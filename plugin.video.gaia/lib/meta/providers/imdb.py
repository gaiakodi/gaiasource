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

# Do not import the Parser here. Check parser() for more info.
#from lib.modules.parser import Parser

from lib.modules.tools import Logger, Converter, Tools, Regex, Media, Audience, Time, Language, Country, Math, System, File, Csv, Settings, Platform, Hardware
from lib.modules.interface import Translation, Format, Dialog
from lib.modules.convert import ConverterDuration, ConverterTime, ConverterSize
from lib.modules.network import Networker
from lib.modules.cache import Cache
from lib.meta.cache import MetaCache
from lib.modules.concurrency import Pool

from lib.modules.account import Imdb as Account

from lib.meta.provider import MetaProvider
from lib.meta.tools import MetaTools
from lib.meta.image import MetaImage

class MetaImdb(MetaProvider):

	# LINK

	# NB: Add the www subdomain.
	# IMDb requests take very long, way longer than Trakt/TMDb/TVDb/Fanart, therefore delaying metadata retrieval.
	# This might be because IMDb website are very large (+-250KB compressed and need 100ms to parse), but probably more because of redirections, Cloudflare, and other checks by IMDb.
	# Requests without the www subdomain take +- 5-6 secs and have 2 HTTP redirects.
	# Requests with the www subdomain take +- 3 secs and have no HTTP redirects.
	# This is most likely caused by IMDb server security checks, the same that drop connections if the rate limit was hit. Probably something like Amazon AWS own "Cloudflare" type of thing using HTTP redirects.
	# Hence, always add the www subdomain to make requests faster.
	Link							= 'https://www.imdb.com'

	LinkTitle						= '/title/{id}'
	LinkSeason						= '/title/{id}/episodes'
	LinkAward						= '/title/{id}/awards'
	LinkList						= '/list/{id}'
	LinkLists						= '/user/{id}/lists'
	LinkListWatch					= '/user/{id}/watchlist'
	LinkListRating					= '/user/{id}/ratings'
	LinkListCheckin					= '/user/{id}/checkins'
	LinkSearchTitle					= '/search/title'
	LinkSearchPerson				= '/search/name'
	LinkFind						= '/find'
	LinkCsv							= '/export'

	# https://developer.imdb.com/non-commercial-datasets/
	# https://datasets.imdbws.com/
	LinkBulk						= 'https://datasets.imdbws.com'
	LinkBulkEpisode					= 'title.episode.tsv.gz' # 50+ MB
	LinkBulkRating					= 'title.ratings.tsv.gz' # 8+ MB

	# PATH

	# Used to identify with type of link it is.
	PathTitle						= '/title/tt'
	PathPerson						= '/name/nm'
	PathSearch						= '/search'
	PathSearchTitle					= '/search/title'
	PathSearchPerson				= '/search/name'
	PathList						= '/list'
	PathUser						= '/user'
	PathListWatch					= '/watchlist'
	PathListRating					= '/ratings'
	PathCsv							= '/export'

	# TYPE
	# IMDb uses different title types for different parts of their website.
	# On https://imdb.com/search/title/ it uses lower case letters with underscores.
	# However, these do not work on lists like https://imdb.com/list/lsXXXXX/ which uses camel case without underscores.
	# The JSON returned by the new search layout also uses camel case without underscores.
	# Using camel case without underscores also seems to work on the search page.
	# Note that all camel cases are required for lists (eg: tvMiniSeries), otherwise they are ignored.

	# https://help.imdb.com/article/imdb/discover-watch/how-do-you-decide-if-a-title-is-a-film-a-tv-movie-or-a-miniseries/GKUQEMEFSM54T2KT?ref_=helpart_nav_23#
	# Most TV Movies and Videos are just normal "movies" on Trakt.
	#	Feature:		680,388
	#	TV Movie:		148,388
	#	Video:			190,965 (has some shorts, porn, etc, but most of them are full movies)
	#	Short:			1,009,487
	#	TV Short:		10,379
	#	TV Special:		48,904
	#	Series:			265,665
	#	Mini-series:	55,841

	TypeMovie						= 'movie'			# Used by lists. Very similar to "feature", but includes titles like tt28814949 (Documentary/Music).
	TypeMovieFeature				= 'feature'			# Used by search. Very similar to "movie", but does not include titles like tt28814949 (Documentary/Music).
	TypeMovieTv						= 'tvMovie'
	TypeShow						= 'tvSeries'
	TypeEpisode						= 'tvEpisode'
	TypeSpecial						= 'tvSpecial'
	TypeMiniseries					= 'tvMiniSeries'
	TypeShort						= 'short'
	TypeShortTv						= 'tvShort'
	TypePodcastShow					= 'podcastSeries'
	TypePodcastEpisode				= 'podcastEpisode'
	TypeGame						= 'videoGame'
	TypeMusic						= 'musicVideo'
	TypeVideo						= 'video'
	TypesAll						= [TypeMovieFeature, TypeMovieTv, TypeShort, TypeShortTv, TypeSpecial, TypeVideo, TypeShow, TypeMiniseries, TypeEpisode]
	TypesFilm						= [TypeMovieFeature, TypeMovie, TypeMovieTv, TypeVideo]
	TypesMovie						= [TypeMovie, TypeMovieTv, TypeVideo] 			# Should only be used by lists. IMDb has updated their list pages, and now also uses "feature" instead of "movie".
	TypesFeature					= [TypeMovieFeature, TypeMovieTv, TypeVideo]	# Should only be used by search. A lot of full movies listed as "Video".
	TypesShort						= [TypeShort, TypeShortTv]
	TypesSpecial					= [TypeSpecial]
	TypesTelevision					= [TypeMovieTv]
	TypesSerie						= [TypeShow, TypeMiniseries, TypeEpisode]
	TypesShow						= [TypeShow, TypeMiniseries]
	TypesMini						= [TypeMiniseries]
	TypesEpisode					= [TypeEpisode]
	TypesSearch						= [TypeMovieFeature, TypeMovieTv, TypeShort, TypeShortTv, TypeSpecial, TypeVideo, TypeShow, TypeMiniseries] # Used to search accross media.
	TypesSearchMovie				= [TypeMovieFeature, TypeMovieTv, TypeVideo, TypeSpecial, TypeShort, TypeShortTv]
	TypesSearchShow					= [TypeShow, TypeMiniseries]

	# STATUS

	StatusAnnounced					= 'announced'
	StatusScript					= 'script'
	StatusPreproduction				= 'pre_production'
	StatusFilming					= 'filming'
	StatusPostproduction			= 'post_production'
	StatusCompleted					= 'completed'
	StatusReleased					= 'released'
	StatusAvailable					= [StatusReleased]
	StatusUnavailable				= [StatusAnnounced, StatusScript, StatusPreproduction, StatusFilming, StatusPostproduction, StatusCompleted]

	Status 							= {
										MetaTools.StatusPlanned			: StatusAnnounced,
										MetaTools.StatusScripted		: StatusScript,
										MetaTools.StatusPreproduction	: StatusPreproduction,
										MetaTools.StatusProduction		: StatusFilming,
										MetaTools.StatusPostproduction	: StatusPostproduction,
										MetaTools.StatusCompleted		: StatusCompleted,
										MetaTools.StatusReleased		: StatusReleased,
									}

	# GENRE
	# Similar to the type, use upper case with dashes, instead of lower case with underscore.
	# Lower-underscore can only be used in Advanced Search, but not on lists.
	# Upper-dash can be used in Advanced Search and lists.
	# An using the actual upper case words, makes it easier to filter lists.
	# NB: Any changes here, should also update indexer.py retrieve().

	GenreAction						= 'Action'
	GenreAdventure					= 'Adventure'
	GenreAnimation					= 'Animation'
	GenreBiography					= 'Biography'
	GenreComedy						= 'Comedy'
	GenreCrime						= 'Crime'
	GenreDocumentary				= 'Documentary'
	GenreDrama						= 'Drama'
	GenreFamily						= 'Family'
	GenreFantasy					= 'Fantasy'
	GenreHistory					= 'History'
	GenreHorror						= 'Horror'
	GenreMusic						= 'Music'
	GenreMusical					= 'Musical'
	GenreMystery					= 'Mystery'
	GenreNoir						= 'Film-Noir'
	GenreRomance					= 'Romance'
	GenreScifi						= 'Sci-Fi'
	GenreThriller					= 'Thriller'
	GenreWar						= 'War'
	GenreWestern					= 'Western'
	GenreNews						= 'News'
	GenreSport						= 'Sport'
	GenreTalk						= 'Talk-Show'
	GenreGame						= 'Game-Show'
	GenreReality					= 'Reality-TV'	# TV must be all upper for Advanced Search.
	GenreShort						= 'Short'
	GenreMini						= 'Mini'		# Not listed as genre, but used for compatibility with TVDb/Trakt.

	Genres							= {
										MetaTools.GenreAction		: GenreAction,
										MetaTools.GenreAdventure	: GenreAdventure,
										MetaTools.GenreAnimation	: GenreAnimation,
										MetaTools.GenreBiography	: GenreBiography,
										MetaTools.GenreComedy		: GenreComedy,
										MetaTools.GenreCrime		: GenreCrime,
										MetaTools.GenreDocumentary	: GenreDocumentary,
										MetaTools.GenreDrama		: GenreDrama,
										MetaTools.GenreFamily		: GenreFamily,
										MetaTools.GenreFantasy		: GenreFantasy,
										MetaTools.GenreHistory		: GenreHistory,
										MetaTools.GenreHorror		: GenreHorror,
										MetaTools.GenreMusic		: GenreMusic,
										MetaTools.GenreMusical		: GenreMusical,
										MetaTools.GenreMystery		: GenreMystery,
										MetaTools.GenreNoir			: GenreNoir,
										MetaTools.GenreRomance		: GenreRomance,
										MetaTools.GenreScifi		: GenreScifi,
										MetaTools.GenreThriller		: GenreThriller,
										MetaTools.GenreWar			: GenreWar,
										MetaTools.GenreWestern		: GenreWestern,
										MetaTools.GenreNews			: GenreNews,
										MetaTools.GenreSport		: GenreSport,
										MetaTools.GenreTalk			: GenreTalk,
										MetaTools.GenreGame			: GenreGame,
										MetaTools.GenreReality		: GenreReality,
										MetaTools.GenreShort		: GenreShort,
									}

	# CERTIFICATE

	CertificateG					= 'G'		# General Audience (All- Age: Any)
	CertificatePg 					= 'PG'		# Parental Guidance Suggested (Kids - Age: 8+)
	CertificatePg13					= 'PG-13'	# Parents Strongly Cautioned (Teens - Age: 13+)
	CertificateR					= 'R'		# Restricted (Teens - Age: 14+)
	CertificateNc17					= 'NC-17'	# Adults Only (Adults - Age: 17+)
	CertificateTvg					= 'TV-G'	# General Audience (All - Age: Any)
	CertificateTvy					= 'TV-Y'	# All Children (Kids - Age: 2+)
	CertificateTvy7					= 'TV-Y7'	# Directed to Older Children (Kids - Age: 7+)
	CertificateTvpg					= 'TV-PG'	# Parental Guidance Suggested (Kids - Age: 8+)
	CertificateTv13					= 'TV-13'	# Parents Strongly Cautioned (Teens - Age: 13+)
	CertificateTv14					= 'TV-14'	# Parents Strongly Cautioned (Teens - Age: 14+)
	CertificateTvma					= 'TV-MA'	# Mature Audiences Only (Adults - Age: 17+)
	CertificateNr					= 'NR'		# Not available. Rather a negation of all other certificates.
	Certificates					= [CertificateG, CertificatePg, CertificatePg13, CertificateR, CertificateNc17, CertificateTvg, CertificateTvy, CertificateTvy7, CertificateTvpg, CertificateTv13, CertificateTv14, CertificateTvma]

	# GROUP
	# Note that with the new layout, some of these are plural, some are singular.

	GroupOscarWinner				= 'oscar_winner'							# Titles + People.
	GroupOscarNominee				= 'oscar_nominee'							# Titles + People.
	GroupOscarPictureWinner			= 'best_picture_winner'						# Titles. Renamed from oscar_best_picture_winner.
	GroupOscarPictureNominee		= 'oscar_best_picture_nominees'				# Titles.
	GroupOscarDirectorWinner		= 'best_director_winner'					# Titles + People. Renamed from oscar_best_director_winner.
	GroupOscarDirectorNominee		= 'oscar_best_director_nominees'			# Titles + People.
	GroupEmmyWinner					= 'emmy_winner'								# Titles + People.
	GroupEmmyNominee				= 'emmy_nominee'							# Titles + People.
	GroupGoldenGlobeWinner			= 'golden_globe_winner'						# Titles.
	GroupGoldenGlobeNominee			= 'golden_globe_nominee'					# Titles.
	GroupRazzieWinner				= 'razzie_winner'							# Titles.
	GroupRazzieNominee				= 'razzie_nominee'							# Titles.
	GroupNationalFilm				= 'national_film_preservation_board_winner'	# Titles.

	GroupTop100						= 'top_100'									# Titles.
	GroupTop250						= 'top_250'									# Titles.
	GroupTop1000					= 'top_1000'								# Titles.
	GroupBottom100					= 'bottom_100'								# Titles.
	GroupBottom250					= 'bottom_250'								# Titles.
	GroupBottom1000					= 'bottom_1000'								# Titles.

	GroupOscarActorWinner			= 'oscar_best_actor_winners'				# People.
	GroupOscarActorNominee			= 'oscar_best_actor_nominees'				# People.
	GroupOscarActressWinner			= 'oscar_best_actress_winners'				# People.
	GroupOscarActressNominee		= 'oscar_best_actress_nominees'				# People.
	GroupOscarSupportorWinner		= 'oscar_best_supporting_actor_winners'		# People.
	GroupOscarSupportorNominee		= 'oscar_best_supporting_actor_nominees'	# People.
	GroupOscarSupportressWinner		= 'oscar_best_supporting_actress_winners'	# People.
	GroupOscarSupportressNominee	= 'oscar_best_supporting_actress_nominees'	# People.
	GroupGoldenGlobeWinning			= 'golden_globe_winning'					# People.
	GroupGoldenGlobeNominated		= 'golden_globe_nominated'					# People.

	GroupNowPlaying					= 'now-playing-us'

	Awards							= {
										MetaTools.AwardAcademyWinner		: GroupOscarWinner,
										MetaTools.AwardAcademyNominee		: GroupOscarNominee,
										MetaTools.AwardEmmyWinner			: GroupEmmyWinner,
										MetaTools.AwardEmmyNominee			: GroupEmmyNominee,
										MetaTools.AwardGlobeWinner			: GroupGoldenGlobeWinner,
										MetaTools.AwardGlobeNominee			: GroupGoldenGlobeNominee,
										MetaTools.AwardRazzieWinner			: GroupRazzieWinner,
										MetaTools.AwardRazzieNominee		: GroupRazzieNominee,
										MetaTools.AwardNationalWinner		: GroupNationalFilm,

										MetaTools.AwardTop100				: GroupTop100,
										MetaTools.AwardTop250				: GroupTop250,
										MetaTools.AwardTop1000				: GroupTop1000,
										MetaTools.AwardBottom100			: GroupBottom100,
										MetaTools.AwardBottom250			: GroupBottom250,
										MetaTools.AwardBottom1000			: GroupBottom1000,

										MetaTools.AwardPictureWinner		: GroupOscarPictureWinner,
										MetaTools.AwardPictureNominee		: GroupOscarPictureNominee,
										MetaTools.AwardDirectorWinner		: GroupOscarDirectorWinner,
										MetaTools.AwardDirectorNominee		: GroupOscarDirectorNominee,
										MetaTools.AwardActorWinner			: GroupOscarActorWinner,
										MetaTools.AwardActorNominee			: GroupOscarActorNominee,
										MetaTools.AwardActressWinner		: GroupOscarActressWinner,
										MetaTools.AwardActressNominee		: GroupOscarActressNominee,
										MetaTools.AwardSupportorWinner		: GroupOscarSupportorWinner,
										MetaTools.AwardSupportorNominee		: GroupOscarSupportorNominee,
										MetaTools.AwardSupportressWinner	: GroupOscarSupportressWinner,
										MetaTools.AwardSupportressNominee	: GroupOscarSupportressNominee,
									}

	# COMPANY

	Companies						= None

	# GENDER

	GenderMale						= 'male'
	GenderFemale					= 'female'
	GenderNonbinary					= 'non-binary'
	GenderOther						= 'other'
	Genders							= {
										MetaTools.GenderMale		: GenderMale,
										MetaTools.GenderFemale		: GenderFemale,
										MetaTools.GenderNonbinary	: GenderNonbinary,
										MetaTools.GenderOther		: GenderOther,
									}

	# WATCH
	# Update (2025-03): The IMDbTV/Freevee option has been removed from the website. Using it causes IMDb requests to fail.

	WatchFree						= 'US/IMDbTV'						# Freevee
	WatchUsRent						= 'US/today/Amazon/subs'
	WatchUsBuy						= 'US/today/Amazon/paid'
	WatchUkRent						= 'GB/today/Amazon/subs'
	WatchUkBuy						= 'GB/today/Amazon/paid'
	WatchDeRent						= 'DE/today/Amazon/subs'
	WatchDeBuy						= 'DE/today/Amazon/paid'
	WatchListRent					= 'has_video_prime_instant_video'	# Used by lists.
	WatchListBuy					= 'has_video_amazon_instant_video'	# Used by lists.
	#Watches						= [WatchFree, WatchUsRent, WatchUsBuy, WatchUkRent, WatchUkBuy, WatchDeRent, WatchDeBuy]
	Watches							= [WatchUsRent, WatchUsBuy, WatchUkRent, WatchUkBuy, WatchDeRent, WatchDeBuy]
	WatchesList						= [WatchListRent, WatchListBuy]
	#WatchesFree					= [WatchFree]
	WatchesFree						= []
	WatchesRent						= [WatchUsRent, WatchUkRent, WatchDeRent]
	WatchesBuy						= [WatchUsBuy, WatchUkBuy, WatchDeBuy]
	#WatchesUs						= [WatchFree, WatchUsRent, WatchUsBuy]
	WatchesUs						= [WatchUsRent, WatchUsBuy]
	WatchesUk						= [WatchUkRent, WatchUkBuy]
	WatchesDe						= [WatchDeRent, WatchDeBuy]

	# THEATER

	TheaterRelease					= 'restrict'				# In theaters near you. Advanced Search and Lists.
	TheaterFavorite					= 'favorite-theaters'		# In favorite theaters. Advanced Search only.
	TheaterOnline					= 'online-ticketing'		# In theaters with online ticketing (US only). Advanced Search only.
	TheaterListFavorite				= 'favorite'				# In favorite theaters. Lists only.

	# SORT

	SortDefault						= 'list_order'
	SortPopularity					= 'popularity'	# SortMovieMeter for movies, SortStarMeter for people.
	SortMovieMeter					= 'moviemeter'
	SortStarMeter					= 'starmeter'
	SortAlphabetic					= 'alpha'
	SortRating						= 'user_rating'
	SortVotes						= 'num_votes'
	SortGross						= 'boxoffice_gross_us'
	SortRuntime						= 'runtime'
	SortYear						= 'year'
	SortDate						= 'release_date'
	SortBirth						= 'birth_date'
	SortDeath						= 'death_date'
	SortUserRating					= 'my_ratings'			# Advanced Search
	SortUserDate					= 'your_rating_date'	# Advanced Search
	SortListRating					= 'your_rating'			# Ratings List
	SortListDate					= 'date_added'			# List and Ratings List

	# ORDER

	OrderAscending					= 'asc'
	OrderDescending					= 'desc'
	OrderDefault					= {
		SortDefault					: OrderAscending,
		SortPopularity				: OrderAscending, # Should be ascending for most to least popular.
		SortMovieMeter				: OrderAscending, # Should be ascending for most to least popular.
		SortStarMeter				: OrderAscending, # Should be ascending for most to least popular.
		SortAlphabetic				: OrderAscending,
		SortRating					: OrderDescending,
		SortVotes					: OrderDescending,
		SortGross					: OrderDescending,
		SortRuntime					: OrderDescending,
		SortYear					: OrderDescending,
		SortDate					: OrderDescending,
		SortBirth					: OrderDescending,
		SortDeath					: OrderDescending,
		SortUserRating				: OrderDescending,
		SortUserDate				: OrderDescending,
		SortListRating				: OrderDescending,
		SortListDate				: OrderDescending,
	}

	# ADULT

	AdultExclude					= None
	AdultInclude					= 'include'

	# VIEW

	ViewDetail						= 'detail'
	ViewSimple						= 'simple'
	ViewGrid						= 'grid'

	# ID

	IdTitle							= 'tt'
	IdList							= 'ls'
	IdCompany						= 'co'
	IdPerson						= 'nm'
	IdUser							= 'ur'
	Ids								= [IdTitle, IdList, IdCompany, IdPerson, IdUser]

	# LIMIT

	LimitDefault					= 50	# The default number of titles returned per page.
	LimitDiscover					= 250	# The maximum number of titles that displayed per page in Advanced Search.
	LimitList						= 100	# The maximum number of titles that displayed per page in Lists. This is fixed and cannot be changed. Update: This is for the old list HTML. The new one does not use this count.

	# CACHE

	CacheMetadata					= Cache.TimeoutDay3
	CacheListId						= Cache.TimeoutMonth1
	CacheNone						= None

	# BULK

	BulkModeExtended			= 'extended'
	BulkModeStandard			= 'standard'
	BulkModeEssential			= 'essential'
	BulkModeDisabled			= 'disabled'
	BulkModes					= (BulkModeDisabled, BulkModeEssential, BulkModeStandard, BulkModeExtended)

	# How often to download the IMDb bulk datasets, process them, and add them to metadata.db.
	# Do not refresh too often, since the download is large (90MB+) and local processing takes long (130secs+).
	# Also avoid putting a strain on IMDb's server if a lot of users retrieve detailed metadata.
	# The only reason to refresh more frequently is to get the numbers and ratings of episodes from the past 2 weeks.
	# The latest ratings are in any case retrieved from HTML, except for episodes SxxE51+ (HTML page only goes until episode 50 per season). All ratings older than 2 weeks are in the dataset.
	# The pack data might also be slightly outdated, but since the IMDb data is not that important for pack generation, it is acceptable.
	# The timeout is also depended on the hardware.
	BulkTimeout						= {
										BulkModeDisabled :	None,
										BulkModeExtended :	Cache.TimeoutWeek2,
										BulkModeStandard :	Cache.TimeoutWeek4,
										BulkModeEssential :	Cache.TimeoutWeek8,

										None :			Cache.TimeoutDay7, # For semi-forced refreshes.
										False :			Cache.TimeoutHour12, # For external metadata generation.
									}

	BulkSizeDownload				= 73400320 # 70MB. Download size of archives.
	BulkSizeStorage					= 419430400 # 400MB. Minimum free disk space for the downloads and extracted data.
	BulkSizeMemory					= {
										# Minimum free RAM to process the data in memory.
										# Bulk generation/refresh requires 2.1-2.5+ GB RAM (64bit systems) and 1.5-1.6+ GB RAM (32bit systems), since Python uses different lengthed data types for different bitness.
										# This is because there are 10 million IMDb entries, and Python has an overhead for variables, due to bitness, auto-garbage-collection, and dynamic types.
										#	64bit systems: 50+ bytes per string and 28-32+ for integers/floats
										#	32bit systems: 30+ bytes per string and 20-23+ for integers/floats
										# Without optimization, such as storing the ID as a string instead of an integer, and reading the entire file in one go, increases RAM to 3.5+ GB.
										# Update: It seems that 64bit systems now also use 1.5-1.6GB.
										Platform.Bits32: 1825361100, # 1.7GB (100MB above what is needed)
										Platform.Bits64: 2791728742, # 2.6GB (100MB above what is needed)
										None: 2362232012, # 2.2GB
									}
	BulkSizeMinimum					= {
										# Minimum total and free memory, otherwise a warning will be shown in the wizard.
										Platform.Bits32: (3006477107, 1610612736), # [2.8GB, 1.5GB]
										Platform.Bits64: (4080218931, 2254857830), # [3.8GB, 2.1GB]
										None: (3435973836, 1932735283), # [3.2GB, 1.8GB]
									}

	BulkDuration					= (
										# Although this typically takes 13-14 minutes on a ARMv7l+eMMC during normal bi-weekly updates, during preloading this can sometimes only take 9-10 minutes.
										(3, 5), 	# Minutes to process on excellent devices. Eg: i7+SSD: 03:50
										(5, 10), 	# Minutes to process on high-end devices.
										(10, 15), 	# Minutes to process on medium-end devices. Eg: ARMv7l+eMMC: 13:50
										(15, 25), 	# Minutes to process on low-end devices.
									)

	BulkIdPrefix					= '99999'
	BulkIdShow						= '-1' # Used as an integer during generation.
	BulkIdLookup					= 'lookup'

	BulkRefreshAutomatic			= 0
	BulkRefreshSelection			= 1

	BulkDialogDisabled				= 0
	BulkDialogBackground			= 1
	BulkDialogForeground			= 2

	BulkActionDisabled				= 0
	BulkActionNotification			= 1
	BulkActionSelection				= 2
	BulkActionRestart				= 3
	BulkActionMemory				= 4

	BulkSettingsSelected			= 'metadata.bulk.selected'
	BulkSettingsRefreshed			= 'metadata.bulk.refreshed'
	BulkSettingsMode				= 'metadata.bulk.mode'
	BulkSettingsRefresh				= 'metadata.bulk.refresh'
	BulkSettingsNotification		= 'metadata.bulk.notification'
	BulkSettingsProgress			= 'metadata.bulk.progress'
	BulkSettingsAction				= 'metadata.bulk.action'

	BulkCanceled					= None

	# USAGE
	# IMDb does not seem to have clear limits.
	# Sometimes if 50 pages are requested in a short time, IMDb will start blocking.
	# Other times you can make 100s of requests without blocking.
	# Probably depends on your IP/VPN and other server conditions.
	UsageAuthenticatedRequest		= 250
	UsageAuthenticatedDuration		= 60
	UsageUnauthenticatedRequest		= 250
	UsageUnauthenticatedDuration	= 60

	UsageMemory						= None
	UsageStorage					= None

	# OTHER

	Special							= 'Unknown'	# The special/unassigned episode parameter. Most specials are added as extra episodes to another season. https://imdb.com/title/tt20674124/episodes/?season=Unknown
	Privacy							= 'privacy'	# User list is private and must be set to public to get the list.
	Primary							= '+'		# Use as the primary language or country.
	Negate							= '!'		# Exclude parameter.
	Debug							= False		# Disable debugging, since many smaller movies have many missing attributes.

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		MetaProvider.__init__(self, account = Account.instance())

	##############################################################################
	# PARSER
	##############################################################################

	@classmethod
	def parser(self, data = None):
		# Importing Parser takes long (100ms).
		# Only import on-demand, otherwise if imdb.py is imported anywhere, it always takes long to just load a directory menu.
		from lib.modules.parser import Parser
		return Parser(data = data, parser = Parser.ParserHtml) # Parser.ParserHtml is faster than Parser.ParserHtml5.

	##############################################################################
	# ID
	##############################################################################

	@classmethod
	def _id(self, id, value):
		if not id or not value: return None
		return id + Tools.stringRemovePrefix(str(value), remove = id)

	@classmethod
	def _idTitle(self, id):
		return self._id(id = MetaImdb.IdTitle, value = id)

	@classmethod
	def _idList(self, id):
		return self._id(id = MetaImdb.IdList, value = id)

	@classmethod
	def _idCompany(self, id):
		return self._id(id = MetaImdb.IdCompany, value = id)

	@classmethod
	def _idPerson(self, id):
		return self._id(id = MetaImdb.IdPerson, value = id)

	@classmethod
	def _idUser(self, id):
		return self._id(id = MetaImdb.IdUser, value = id)

	@classmethod
	def _idPrefix(self, id):
		return id

	@classmethod
	def _idPrefixTitle(self):
		return MetaImdb.IdTitle

	@classmethod
	def _idPrefixList(self):
		return MetaImdb.IdList

	@classmethod
	def _idPrefixCompany(self):
		return MetaImdb.IdCompany

	@classmethod
	def _idPrefixPerson(self):
		return MetaImdb.IdPerson

	@classmethod
	def _idPrefixUser(self):
		return MetaImdb.IdUser

	@classmethod
	def _idExpression(self, id, group = True, suffix = True):
		expression = id + '\d+'
		if group: expression = '(%s)' % expression
		if suffix: expression = '%s(?:$|[^\d])' % expression
		return expression

	@classmethod
	def _idExpressionTitle(self, group = True, suffix = True):
		return self._idExpression(id = MetaImdb.IdTitle, group = group, suffix = suffix)

	@classmethod
	def _idExpressionList(self, group = True, suffix = True):
		return self._idExpression(id = MetaImdb.IdList, group = group, suffix = suffix)

	@classmethod
	def _idExpressionCompany(self, group = True, suffix = True):
		return self._idExpression(id = MetaImdb.IdCompany, group = group, suffix = suffix)

	@classmethod
	def _idExpressionPerson(self, group = True, suffix = True):
		return self._idExpression(id = MetaImdb.IdPerson, group = group, suffix = suffix)

	@classmethod
	def _idExpressionUser(self, group = True, suffix = True):
		return self._idExpression(id = MetaImdb.IdUser, group = group, suffix = suffix)

	@classmethod
	def _idMatch(self, id, data, group = True, prefix = True, suffix = True):
		expression = self._idExpression(id = id, group = group, suffix = suffix)
		if prefix: expression = '\!?' + expression
		return Regex.match(data = data, expression = expression, cache = True)

	@classmethod
	def _idMatchTitle(self, data, group = True, prefix = True, suffix = True):
		return self._idMatch(id = MetaImdb.IdTitle, data = data, group = group, prefix = prefix, suffix = suffix)

	@classmethod
	def _idMatchList(self, data, group = True, prefix = True, suffix = True):
		return self._idMatch(id = MetaImdb.IdList, data = data, group = group, prefix = prefix, suffix = suffix)

	@classmethod
	def _idMatchCompany(self, data, group = True, prefix = True, suffix = True):
		return self._idMatch(id = MetaImdb.IdCompany, data = data, group = group, prefix = prefix, suffix = suffix)

	@classmethod
	def _idMatchPerson(self, data, group = True, prefix = True, suffix = True):
		return self._idMatch(id = MetaImdb.IdPerson, data = data, group = group, prefix = prefix, suffix = suffix)

	@classmethod
	def _idMatchUser(self, data, group = True, prefix = True, suffix = True):
		return self._idMatch(id = MetaImdb.IdUser, data = data, group = group, prefix = prefix, suffix = suffix)

	@classmethod
	def idType(self, value):
		for id in MetaImdb.Ids:
			if value.startswith(id): return id
		return None

	##############################################################################
	# LINK
	##############################################################################

	@classmethod
	def link(self, media = None, id = None, title = None, year = None, season = None, metadata = None, search = False):
		if metadata:
			if not media:
				if 'tvshowtitle' in metadata:
					if 'episode' in metadata: media = Media.Episode
					elif 'season' in metadata: media = Media.Season
					else: media = Media.Show
				else:
					media = Media.Movie
			if id is None and media == Media.Episode:
				try:
					id = metadata['id']['episode']['imdb']
					if id: media = Media.Show # Avoid adding the season number if we directly access the episode ID.
				except: pass
			if id is None:
				try: id = metadata['id']['imdb']
				except: pass
			try: title = metadata['tvshowtitle'] if metadata['tvshowtitle'] else metadata['title']
			except: pass
			try: year = metadata['year']
			except: pass
			try: season = metadata['season']
			except: pass

		link = None
		if id:
			if media == Media.Show: season = None
			link = self._linkTitle(id = id, season = season)
		elif search and title:
			query = title
			if year and media == Media.Movie: query += ' ' + str(year)
			link = Networker.linkCreate(link = Networker.linkJoin(MetaImdb.Link, MetaImdb.LinkFind), parameters = {'q' : query})

		# Remove the www subdomain to make the link more readable and the QR code simpler.
		# Read the comment at the enum for more info on why www was added.
		if link: link = link.replace('https://www.', 'https://')
		return link

	@classmethod
	def linkImage(self, link, size = 780, crop = False):
		if not link: return None
		expression = '((?:_SX|_SY|_UX|_UY|_CR|_AL|_V)(?:\d+|_).+?\.)'

		# Keep the cropped coordinates for people images, otherwise there might be differently sized images in the menu.
		# Eg: https://m.media-amazon.com/images/M/MV5BMzIzMTE4NzcyMl5BMl5BanBnXkFtZTgwODA2NTQyNTM@._V1_UY209_CR87,0,140,209_AL_.jpg
		# Eg: https://m.media-amazon.com/images/M/MV5BYjQ5MDkyMGEtYmI0OS00MmM2LWE0MmEtZmQ2NjA5MzYyYTFjXkEyXkFqcGdeQXVyNjIwMTQzOTU@._V1_UY209_CR37,0,140,209_AL_.jpg
		if crop:
			try:
				pixel = Regex.extract(data = link, expression = '_CR([\d\,]+)')
				if pixel:
					pixel = [int(i) for i in pixel.split(',')]
					if pixel:
						ratio = size / float(pixel[3])
						pixel = [int(i * ratio) for i in pixel]

						# Either scale vertically or horizontally.
						# Use the same scaling as in the original link (some links contain _UX, some _UY).
						# Otherwise some images might have top-bottom or left-right white bars.
						width = pixel[2]
						height = pixel[3]
						if Regex.extract(data = link, expression = '((?:_UX)(?:\d+|_).+?\.)'):
							scaler = '_UX'
							size = width
						else:
							scaler = '_UY'
							size = height

						pixel = [str(i) for i in pixel]
						return Regex.replace(data = link, expression = expression, replacement = '%s%d_CR%s.' % (scaler, size, ','.join(pixel)), group = 1)
			except: Logger.error()

		# Eg: https://m.media-amazon.com/images/M/MV5BNjA3NGExZDktNDlhZC00NjYyLTgwNmUtZWUzMDYwMTZjZWUyXkEyXkFqcGdeQXVyMTU1MDM3NDk0._V1_.jpg
		# Eg: https://m.media-amazon.com/images/M/MV5BMzA4Njc3ODYtMTYwOS00Y2NiLWFkNmEtOThhZmU0MGQxM2Y5XkEyXkFqcGdeQXVyMTYzMDM0NTU@._V1_QL75_UX190_CR0,0,190,281_.jpg
		return Regex.replace(data = link, expression = expression, replacement = '_SX%d.' % size, group = 1)

	@classmethod
	def _linkTitle(self, id, season = None):
		if season: return Networker.linkCreate(link = Networker.linkJoin(MetaImdb.Link, MetaImdb.LinkSeason).format(id = id), parameters = {'season' : season})
		else: return Networker.linkJoin(MetaImdb.Link, MetaImdb.LinkTitle).format(id = id)

	def _linkAward(self, id):
		return Networker.linkJoin(MetaImdb.Link, MetaImdb.LinkAward).format(id = id)

	def _linkLists(self, user, **parameters):
		if not user:
			user = self.accountId()
			if not user: return None
		return self._linkCreate(link = MetaImdb.LinkLists, id = self._idUser(user), **parameters)

	def _linkList(self, id, media = None, status = None, year = None, date = None, rating = None, votes = None, genre = None, language = None, country = None, certificate = None, group = None, gender = None, limit = None, page = None, offset = None, sort = None, order = None, adult = None, view = None, **parameters):
		if not id: return None
		return self._linkCreate(link = MetaImdb.LinkList, id = self._idList(id), media = media, status = status, year = year, date = date, rating = rating, votes = votes, genre = genre, language = language, country = country, certificate = certificate, group = group, gender = gender, limit = limit, page = page, offset = offset, sort = sort, order = order, adult = adult, view = view, **parameters)

	def _linkListWatch(self, user, **parameters):
		if not user:
			user = self.accountId()
			if not user: return None
		return self._linkCreate(link = MetaImdb.LinkListWatch, id = self._idUser(user), **parameters)

	def _linkListRating(self, user, **parameters):
		if not user:
			user = self.accountId()
			if not user: return None
		return self._linkCreate(link = MetaImdb.LinkListRating, id = self._idUser(user), **parameters)

	def _linkListCheckin(self, user, **parameters):
		if not user:
			user = self.accountId()
			if not user: return None
		return self._linkCreate(link = MetaImdb.LinkListCheckin, id = self._idUser(user), **parameters)

	'''
		link:			The link base/path.
						- String:		Specific link base.
		media:			The content media.
						- None:			Any media type, except if 'type' is specified.
						- String:		Specific media.
						- List:			Multiple medias.
		niche:			The content niche.
						- None:			Any niche type.
						- String:		Specific niche.
						- List:			Multiple niches.
		id:				The IMDb title/list/person ID.
						- None:			No ID.
						- String:		Specific ID.
		query:			The IMDb search query for titles or names.
						- None:			No query.
						- String:		Specific query.
						- List:			Specific query.
		keyword			The IMDb search keywords added to titles to provide additional info, such as "anime".
						- None:			No keywords.
						- String:		Specific keywords.
						- List:			Specific keywords.
		type:			The IMDb title type.
						- None:			Automatically determined the type from 'media'.
						- String:		Specific type.
						- List:			Multiple types. Values are ORed, so it makes sense to specify multiple values.
		status:			The IMDb production status. Note that this parameter has been removed in the new Advanced Search layout. Use date range instead.
						- None:			Any status.
						- True:			Only released titles.
						- False:		Only unreleased titles.
						- String:		Specific status.
						- List:			Multiple statuses. Values are ORed, so it makes sense to specify multiple values.
		year:			The IMDb release year.
						- None:			Any year.
						- True:			Released this year or earlier.
						- False:		Released this year or later.
						- Integer:		Released during a specific year.
						- List:			Year range. If the first/second value is None, any year in the lower/higher range.
		date:			The IMDb release date.
						- None:			Any date.
						- True:			Released today or earlier.
						- False:		Released today or later.
						- Integer:		Released on or before the given date. Large values are timestamps. Small positive values are number of days into the past. Small negative values are number of days into the future.
						- String:		Released on or before the given date. Date format YYYY-MM-DD or YYYY-MM.
						- List:			Date range. If the first/second value is None, any date in the lower/higher range. Values can be integers or strings.
		rating:			The IMDb average rating.
						- None:			Any rating.
						- Integer:		Specific minimum rating.
						- Float:		Specific minimum rating.
						- String:		VotingLenient/VotingNormal/VotingModerate/VotingStrict, based on the media type.
						- List:			Rating range. If the first/second value is None, any rating in the lower/higher range. Values can be integers or floats.
		votes:			The IMDb number of votes.
						- None:			Any votes.
						- Integer:		Specific minimum votes.
						- String:		VotingLenient/VotingNormal/VotingModerate/VotingStrict, based on the media type.
						- List:			Vote range. If the first/second value is None, any votes in the lower/higher range.
		genre:			The IMDb genre.
						- None:			Any genres.
						- String:		Specific genre.
						- List:			Multiple genres. Values are ANDed, so it makes little sense to specify multiple values, except for some specific combination (eg: Action-Thriller).
		language:		The IMDb language.
						Note that IMDb uses 2-letter ISO-639-1 codes. However, some less-known languages use a 3-letter code.
						Note that this is the release language, not the language of the returned metadata (which is set in the headers).
						Values with a "-" or "!" prefix will be excluded.
						- None:			Any languages.
						- True:			Excluded "spammy" languages, mostly from India and Turkey.
						- String:		Specific language.
						- List:			Multiple languages. Values are ANDed, so it makes little sense to specify multiple values, except for some specific combination (eg: de-nl).
		country:		The IMDb country.
						Note that IMDb uses 2-letter ISO Alpha-2 codes.
						Values with a "-" or "!" prefix will be excluded.
						- None:			Any countries.
						- True:			Excluded "spammy" countries, mostly India and Turkey.
						- String:		Specific country.
						- List:			Multiple countries. Values are ANDed, so it makes little sense to specify multiple values, except for some specific combination (eg: de-nl).
		certificate:	The IMDb age certificates.
						- None:			Any certificate.
						- String:		Specific certificate.
						- List:			Multiple certificates. Values are ORed, so it makes sense to specify multiple values.
		group:			The IMDb group for titles and people.
						- None:			Any group.
						- True:			Award winners, based on the media type.
						- String:		Specific group.
						- List:			Multiple groups. Values are ANDed, so it makes little sense to specify multiple values, except for some specific combination (eg: won both Oscar and Golden Globe).
		gender:			The IMDb gender for people.
						- None:			Any gender.
						- String:		Specific gender.
						- List:			Multiple genders. Values are ORed, so it makes sense to specify multiple values.
		watch:			The IMDb watch/stream availability.
						- None:			Any (un)availability.
						- True:			Available on any streaming service.
						- String:		Available on a specific streaming service.
						- List:			Available on any streaming service from a list. Values are ORed, so it makes sense to specify multiple values.
		limit:			The maximum number of titles to return.
						Value in [1,250].
						- None:			Use the default limit, typically 50.
						- Integer:		Specific limit.
		page			The current page within the list.
						Value in [1,inf].
						Note that this value is not used directly, but instead calculated from 'limit' and 'offset'.
						- None:			Use the default limit, typically 50.
						- Integer:		Specific page.
		offset			The current offset within the list.
						Value in [1,inf] and should be multiples of 'limit'.
						- None:			Calculate from 'page' and 'limit', or use the default offset of 1 if 'page' was not provided.
						- Integer:		Specific offset. Should be multiples of 'limit' + 1. Eg: with a limit of 50, the first page has an offset of 1 and the second page an offset of 51.
		sort:			The attribute to sort against.
						- None:			Use the default- None:		 sorting of the list.
						- String:		Specific sort attribute.
		order:			The order of sorting.
						- None:			Automatically determined the default order from 'sort'.
						- String:		Specific sort order.
		adult:			Wether or not to include adult/porn titles.
						- None:			Seems to be excluded by default on IMDb.
						- True:			Include adult content.
						- False:		Exclude adult content.
		view:			The HTML layout/view of the list.
						- None:			Use the detailed view with extra metadata.
						- True:			Use the detailed view with extra metadata.
						- False:		Use the simple view without extra metadata.
						- String:		Use a specific view type.
		csv:			Export the list to CSV. Works for all custom lists, user watchlists, and user ratings lists.
						- None:			Do not export to CSV.
						- True:			Export to CSV.
						- False:		Do not export to CSV.
		format:			Any extra parameters that will be string-formatted into the link/path.
						- None:			No string-formatted parameters.
						- Dictionary:	String-formatted parameters, with the key being the format ID and the value the replacement data.
	'''
	def _linkCreate(self, link = None, media = None, niche = None, id = None, query = None, keyword = None, type = None, status = None, release = None, year = None, date = None, duration = None, rating = None, votes = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, group = None, gender = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, adult = None, filter = None, view = None, csv = None, format = None, reduce = None):
		if media == Media.Season: return None # IMDb does not support seasons as separate "objects", only shows and episodes.
		if format is None: format = {}

		if csv:
			parameters = {}
		else:
			parameters = self._parameterInitialize(media = media, niche = niche, link = link, id = id, query = query, keyword = keyword, type = type, status = status, release = release, year = year, date = date, duration = duration, rating = rating, votes = votes, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = group, gender = gender, watch = watch, theater = theater, limit = limit, page = page, offset = offset, sort = sort, order = order, adult = adult, filter = filter, view = view, format = format)
			if parameters is None: return None # Unsupported parameters (eg: unsupported genre).

		# IMDb has introduced a new HTML layout for Advanced Search.
		# Currently, the new and old layout are returned randomly on each request, and it does not seem to be depended only any headers or cookies.
		# IMDb will probably completely remove the old layout in the near future.
		# Lists, watchlist, and rating lists are still shown in the old layout.
		# The new layout uses JS to dynamically load the JSON of the next page, instead of reloading the page with a new GET URL.
		# Hence, the "start" parameter is ignored in the new layout.
		# If the "start" parameter is added, it always returns the first page in the new layout.
		# The new JS uses a complex algorithm to generate a hash that is added to IMDb JSON requests.
		# Without this hash, requests are rejected.
		# The algorithm seems too complex to reverse engineer.
		# The only current option seems to retrieve the maximum number of 250 titles per page with one request.
		# Then we manually split them into 5 pages of 50 titles.
		# If we need more pages, we will probably have to introduce TMDb/Trakt discovery.
		if reduce:
			oldOffset = parameters.get('start', 1) - 1
			oldLimit = parameters.get('count', MetaImdb.LimitDefault)

			newLimit = int(MetaImdb.LimitDiscover / oldLimit)
			newPage = Math.roundDown((oldOffset / oldLimit) / newLimit)

			parameters['start'] = (MetaImdb.LimitDiscover * newPage) + 1
			parameters['count'] = MetaImdb.LimitDiscover

		# ID
		if not id is None and not 'id' in format: format['id'] = id # If the ID is in the link path.

		# Ranges
		for k, v in parameters.items():
			if Tools.isArray(v):
				v = ['' if i is None else str(i) for i in v]
				parameters[k] = ','.join(v)

		# Create
		if not link.startswith(MetaImdb.Link): link = Networker.linkJoin(MetaImdb.Link, link)
		link = Networker.linkClean(link = link, parametersStrip = False, headersStrip = True)
		if csv: link = [link, MetaImdb.LinkCsv]
		link = Networker.linkCreate(link = link, parameters = parameters, duplicates = False)
		if format: link = link.format(**format)
		return link

	##############################################################################
	# COMPANY
	##############################################################################

	@classmethod
	def _companies(self):
		# This structure is too large to add as a global enum.
		# Otherwise importing this class has an initialization overhead.
		# Only create on demand.
		if MetaImdb.Companies is None:
			# Originals are assembled by combining the company’s studios and networks (IDs added to the query as companies=co00000), and then excluding other major competing companies (IDs added to the query as companies=!co00000).
			# The following attributes can be used to create originals. Each of them can be a fixed IMDb ID, or a MetaTools enum containing multiple IDs.
			#	1 fixed: Instead of automatically assembling the company’s studios and networks, provide a fixed list of companies to use. This is useful if one does not want to include all IDs of a company. For instance, only include the networks, but not the studios. Or including a specific ID that only contains originals, like "Hulu Originals".
			#	2. include: Any extra company to include, besides the studios/networks added automatically, or the "fixed" IDs. These IDs are added explicitly to the query (companies=co00000).
			#	3. exclude: Any company to exclude. These IDs are added explicitly to the query (companies=!co00000).
			#	4. allow: Any company to allow without explicitly adding it to the query. These companies are removed from the "exclude" list. This is useful to allow collaborations between two companies without including other titles from the collaborating company.
			#	5. disallow: Any company to disallow without explicitly adding it to the query. These companies are removed from the "include" list.
			#	6. language: Any company to "include" if the user settings contain the language, otherwise they are added to "disallow". This is useful to exclude eg Indian titles that clutter the list (eg: Amazon, Netflix, etc).
			#
			# The "accuracy" of the originals (false positives vs false negatives) are classified at the following levels.
			# We try to exclude as many non-originals, without removing the actual originals (at least the bigger/famous ones). In most cases we rather want to exclude too many than too few, since there are the other network/broadcaster/distributor menus with more titles.
			# Sometimes originals appear on multiple platforms, some of them are co-produced originals, originals created by joint ventures (eg The CW), or originals that changed company after a certain season. Sometimes there are even well-know/big originals that appear on competing platforms (eg an Amazon Original might also appear on Netflix). This makes things very difficult to filter and often requires exclusions of small studios/networks, instead of excluding an entire block (eg Netflix).
			# Note that due to the URL-length limit, only so many exclusions can be added (+-450). If there are too many exclusions, at some point the menu might actually become less accurate, since too many (important) IDs are cut off at the end of the URL.
			#	Level-0 (More menu): No, or just the default, exclusions applied to make them slightly more accurate than the Producers/Broadcasters menus (studios+networks without any exclusions). These definitely need a lot more work in the future.
			#	Level-1 (More menu): Some custom exclusions were added to make them slightly more accurate than level 0, but still too many incorrect titles. These also need a lot more work in the future.
			#	Level-2 (Main or More menu): Many custom exclusions were added. But there are too many other originals on the network and its own originals are on other platforms, making a difficult to filter accurately (eg SyFy). In many cases the exclusions are for individual companies, not batches. In some cases, further refinement might help, but in other cases the menu will never get that much more accurate. This applies to many movie originals that are not actually originals and just less-known movies from smaller studios/networks (eg SyFy, Discovery, etc).
			#	Level-3 (Main menu): Many custom exclusions were added and the menu is close to perfect. Some more refinements might be beneficial, but sometimes adding more exclusions might not improve things help. These originals were gotten into a decent state, without picking out every last minor non-original.
			#	Level-4 (Main menu): Many custom exclusions were added and the menu is essentially perfect, at least as perfect as it can be. More exclusions will not improve anything and this can be left as-is. Although in the future it might have to be updated again, once new titles arrive.

			from lib.meta.company import MetaCompany

			MetaImdb.Companies = {
				MetaCompany.Company20thcentury : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0000756', 'co0056447', 'co0161074', 'co0096253', 'co0010685', 'co0781821', 'co0017497', 'co0103215', 'co0179259', 'co0365818', 'co0822480', 'co0067247', 'co0840157', 'co0049339', 'co1023009', 'co0103726', 'co0423469', 'co1031931', 'co0645300', 'co0530625', 'co0378436', 'co0166475', 'co0103751', 'co0077505', 'co0048444', 'co0039396', 'co0098487', 'co0039745'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0000756', 'co0010224', 'co0053239', 'co0007180', 'co0189783', 'co0280047', 'co0862964', 'co0092296', 'co0150813', 'co0063964', 'co0161074', 'co0159046', 'co0209782', 'co0296943', 'co0297163', 'co0010685', 'co0063989', 'co0937473', 'co0751509', 'co0826899', 'co0605838', 'co0781821', 'co0853216', 'co0421648', 'co0108018', 'co0937474', 'co0643891', 'co0943364', 'co0226330', 'co0952616', 'co0286182', 'co0711817', 'co0794652', 'co0931863', 'co0544968', 'co0788854', 'co0051662', 'co0764128', 'co0197226', 'co0785884', 'co0256824', 'co0581069', 'co0491690', 'co0368892', 'co0241365', 'co0092951', 'co0273176', 'co0012812', 'co0866807', 'co0832095', 'co0863455', 'co0623011', 'co0746852', 'co0148451', 'co0078923', 'co0866288', 'co0665472', 'co0643890', 'co0195278', 'co0947212', 'co0867515', 'co0862965', 'co0707661', 'co0491691', 'co0380710', 'co0346045', 'co0295671', 'co1051152', 'co0918688', 'co0867516', 'co0863456', 'co0814039', 'co0662795', 'co0662791', 'co0662285', 'co0642443', 'co0046053', 'co1040440', 'co1034313', 'co1027357', 'co0941233', 'co0918845', 'co0918844', 'co0883912', 'co0870304', 'co0867519', 'co0867518', 'co0867517', 'co0855510', 'co0723134', 'co0694711', 'co0613528', 'co0560127', 'co0421647', 'co0368843', 'co0368801', 'co0271701', 'co0270675', 'co0246174', 'co0200961', 'co0173400', 'co0160971', 'co0080169', 'co0924784', 'co0893064', 'co0877266', 'co0782188', 'co0611815', 'co0547664', 'co0547663', 'co0451003', 'co0419314', 'co0379362', 'co0379346', 'co0379325', 'co0379300', 'co0368861', 'co0368661', 'co0212696', 'co0197792', 'co0196456', 'co0195082', 'co0118485', 'co0099617', 'co0094759', 'co0030446'],
				},
				MetaCompany.CompanyAbc : {
					# Show (2108): Level-3
					# Movie (2249): Level-2
					# ABC is owned and collaborates with by Disney.
					# A ton of ABC stuff is on Hulu.
					# ABC Signatures and other studios sometimes produce content for other platforms. (eg: Netflix/Marvel original, but produced by ABC tt3322312)
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'fixed' : MetaProvider.CompanyNetwork,
															'exclude' : [
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]}, # tt1466074
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyTbs			: [MetaProvider.CompanyNetwork]}, # Not for tt0086827.
																#{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # Not for tt7587890.
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]}, # tt0066206
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]}, # tt0066206

																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},

																'co0045367', # Oxygen Media (tt0458352)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0209226', 'co0074648', 'co0314763', 'co0033326', 'co0899934', 'co0048955', 'co0021273', 'co0852654', 'co0056365', 'co0061107', 'co0641809', 'co0033054', 'co0755246', 'co0377134', 'co0348603', 'co0181606', 'co0383943', 'co0009307', 'co0129642', 'co0112209', 'co0825786', 'co0671036', 'co0508214', 'co0432287', 'co0385264', 'co0202583', 'co0152669', 'co0044833', 'co0043308', 'co0875139', 'co0869949', 'co0868474', 'co0847123', 'co0794140', 'co0752381', 'co0742232', 'co0728048', 'co0646998', 'co0636045', 'co0401142', 'co0387413', 'co0339897', 'co0299815', 'co0257987', 'co0184398', 'co0171572', 'co0092661', 'co0088355', 'co0055400', 'co0049424', 'co0924094', 'co0875134', 'co0296206', 'co0048784'],
					MetaProvider.CompanyNetwork		: ['co0037052', 'co0050794', 'co0571670', 'co0038002', 'co0033326', 'co0547748', 'co0048955', 'co0072128', 'co0366131', 'co0717722', 'co0113687', 'co0051484', 'co0885117', 'co0815633', 'co0604632', 'co0095158', 'co0093288', 'co0071029', 'co0160591'],
					MetaProvider.CompanyVendor		: ['co0213225', 'co0016203', 'co0212150', 'co0024582', 'co0094898', 'co0427720', 'co0090366', 'co0081188', 'co0739072', 'co0043953', 'co0504198', 'co0399064', 'co0053123', 'co0078518', 'co0795985', 'co0138770', 'co0086850', 'co0776976', 'co0723944', 'co0503538', 'co1027259', 'co0992781', 'co0976554', 'co0923262', 'co0913419', 'co0860670', 'co0825785', 'co0825784', 'co0795983', 'co0793020', 'co0747268', 'co0716481', 'co0712561', 'co0704979', 'co0625846', 'co0598951', 'co0499524', 'co0493121', 'co0465399', 'co0431081', 'co0430836', 'co0391449', 'co0327798', 'co0297296', 'co0287995', 'co0274340', 'co0272294', 'co0269174', 'co0266935', 'co0094890', 'co0009893', 'co1024565', 'co1008959', 'co0980699', 'co0928550', 'co0868243', 'co0859939', 'co0852116', 'co0842694', 'co0813557', 'co0695216', 'co0233792', 'co0224390', 'co0075098', 'co0303200'],
				},
				MetaCompany.CompanyAe : {
					# Show (582): Level-3. Maybe close to Level-4.
					# Movie (476): Level-2
					# A+E Studios produces a lot of titles that are not marked as A+E Originals on IMDb posters for other companies (eg Netflix, BBC, History, Lifetime, etc).
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt2188671, tt3230780, tt1836037, tt9308682.
																#{MetaCompany.CompanyAcorn			: [MetaProvider.CompanyNetwork]}, # Not for tt3581932.
																#{MetaCompany.CompanyBbc				: [MetaProvider.CompanyNetwork]}, # Not for tt3581932, tt3910804, tt0091618, tt0115355.
																#{MetaCompany.CompanyHistory			: [MetaProvider.CompanyNetwork]}, # Not for tt3910804, tt0423652, tt2707792, tt10589968.
																#{MetaCompany.CompanyFox				: [MetaProvider.CompanyNetwork]}, # Not for tt1552112, tt1590961, tt2229907, tt1497563.
																#{MetaCompany.CompanyFx				: [MetaProvider.CompanyNetwork]}, # Not for tt4337944.
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # Not for tt0423652, tt11794642.
																#{MetaCompany.CompanySky				: [MetaProvider.CompanyNetwork]}, # Not for tt0423652, tt2707792, tt2132641.
																#{MetaCompany.CompanyPeacock			: [MetaProvider.CompanyNetwork]}, # Not for tt1785123.
																#{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # Not for tt1785123, tt0424627.
																#{MetaCompany.CompanyHulu				: [MetaProvider.CompanyNetwork]}, # Not for tt8594028, tt8594028.
																#{MetaCompany.CompanyBravo			: [MetaProvider.CompanyNetwork]}, # Not for tt0424627.
																#{MetaCompany.CompanyYoutube			: [MetaProvider.CompanyNetwork]}, # Not for tt15250706.
																#{MetaCompany.CompanyCbs				: [MetaProvider.CompanyNetwork]}, # Not for tt1103973.
																#{MetaCompany.CompanyAmc				: [MetaProvider.CompanyNetwork]}, # Not for tt18552362.
																#{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # Not for tt3868860.
																{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # Not for tt0141842.
																{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # Not for tt0368479, tt9645942.

																#'co0039462', # Public Broadcasting Service (PBS). Not for tt0091618.
																#'co0051618', # Entertainment One. Not for tt0785036, tt1329291.
																#'co0015194', # ITV - Independent Television (tt0118401). Not for tt0094525 (on A+E Originals Wikipedia it says it is an A+E original).
																'co0141215', # Bentley Productions (tt0118401)
																#'co0070627', # CBS (tt0368479). Not for tt1842530 (which was CBS, but now a A+E Original).
																#'co0037052', # American Broadcasting Company (ABC). Not for tt11794642.
																'co0048965', # Chestermead (tt0112130)
																'co0353668', # Gaumont International Television (tt6692188)
																'co0103289', # Granada Television (tt0086661, tt0090509, tt0108855). These seem to be semi A+E originals, together with ITV??
																#'co0058425', # Granada Entertainment (tt0118290). Do not add ABC, since it is Disney. Not for tt0423652.
																'co0113580', # Witzend Productions (tt0090477)
																'co0806514', # Studio S (tt12516712)
																'co0042601', # Travel Channel (tt2012511)
																'co0376843', # Planète Bleue Télévision (tt2189874)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyShowtime			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTnt				: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanySyfy				: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCrunchyroll		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyParamount			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony				: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm				: [MetaProvider.CompanyVendor]},
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0467028', 'co0152564', 'co0883720', 'co0741969', 'co1024705', 'co0624428', 'co1047517', 'co0933418', 'co0995059', 'co0843022', 'co0779123', 'co0778575', 'co0703903', 'co0600239', 'co0587318', 'co0368082', 'co0347017', 'co0778574'],
					MetaProvider.CompanyNetwork		: ['co0056790', 'co0976488', 'co0736175', 'co0452284', 'co0723513', 'co0930307', 'co0624428', 'co0450920', 'co0979954', 'co0783041', 'co0441521', 'co0159554', 'co1048176', 'co1021426', 'co1002360', 'co0889192', 'co0779123', 'co0778575', 'co0580178', 'co0778574'],
					MetaProvider.CompanyVendor		: ['co0023845', 'co0331411', 'co0674785', 'co0625685', 'co1057623'],
				},
				MetaCompany.CompanyAcorn : {
					# Show (176): Level-2
					# Movie (27): Level-2.
					# AcornTV has content from ITV, Channel 4, BBC, All3Media, DRG, and ZDF.
					# Some Acorn Originals do not have any Acorn ID listed under their companies.
					# Other Acorn Originals are released on multiple other platforms.
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																'co0318834', # AMC Studios (tt15428778) (sister/parent channel)
																'co0061958', # ARD Degeto Film (tt4378376)
																'co0618997', # Bad Wolf (tt2177461)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyStudio]},

																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHistory		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},

																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0595504', 'co0524201'],
					MetaProvider.CompanyNetwork		: ['co0463759', 'co0178134', 'co0174662', 'co0098270', 'co0277845'],
					MetaProvider.CompanyVendor		: ['co0489114', 'co0502394', 'co0066950'],
				},
				MetaCompany.CompanyAdultswim : {
					# Show (216): Level-3
					# Movie (28): Level-3
					# Most Adult Swim Originals are released on many other major platforms.
					# Almost none of the Adult Swim Orignals movies have an Adult Swim ID listed under its companies.
					# Difficult to filter between Cartoon Network, Adult Swim, Boomerang, and other Warner companies.
					MetaProvider.CompanyOriginal	: {
														Media.Show	: {
															'exclude' : [
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]}, # tt2560140, tt0388629, tt9335498
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # tt0149460, tt0182576, tt1561755
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]}, # tt0096694

																'co1060195', # Cartoon Network Productions (tt0220880) (sister channel)
																'co0238110', # Cartoon Network Studios (tt0115157, tt1305826) (sister channel)
																'co0127153', # Animax (tt0112159)
																'co0964339', # Animax (tt0373732)
																'co0127153', # Animax (tt5626028)
																'co0500104', # Animax Brazil (tt0877057)
																'co0035005', # AT-X (tt0409591)
																'co0123927', # DC Entertainment (tt14681924, tt1641384)
																'co0453359', # Anime Ltd (tt0213338)
																'co0043107', # British Broadcasting Corporation (BBC) (tt0290978)
																'co0028689', # Manga Entertainment (tt4644488)
																'co0049595', # Shueisha (tt6342474)
																'co0039940', # FUNimation Entertainment (tt3741634)
																'co0257336', # The Anime Network (tt3742982)
																'co0062107', # Toei Animation (tt8433216, tt0103369)
																'co0190623', # TV Setouchi Broadcasting (TSC) (tt1214085)
															],
														},
														Media.Movie	: {
															'fixed' : MetaProvider.CompanyStudio,
														},
													},
					MetaProvider.CompanyStudio		: ['co0008281', 'co0777394', 'co1040172', 'co1040171'],
					MetaProvider.CompanyNetwork		: ['co0153115', 'co1019499', 'co0583876', 'co1003525', 'co0600922'],
					MetaProvider.CompanyVendor		: ['co0546259', 'co0635386'],
				},
				MetaCompany.CompanyAmazon : {
					# Show (1221 of 353+): Level-4. A lot of other originals appear on Amazon, and a few Amazon originals appear on other platforms. Many co-productions.
					# Movie (1492 of 172+): Level-3.
					# Numbers might be far off, since many of the international, smaller, and non-direct Amazon originals are not included.
					# https://en.wikipedia.org/wiki/Category:Amazon_Prime_Video_original_programming
					# https://en.wikipedia.org/wiki/List_of_Amazon_Prime_Video_original_programming
					# https://en.wikipedia.org/wiki/Category:Amazon_Prime_Video_original_films
					# https://press.amazonmgmstudios.com/us/en/all-original-series
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															# Too many Indian titles clutering the menu.
															'language' : [
																{Language.CodeIndian : ['co0939864', 'co0869098', 'co0609198']},
															],
														},
														Media.Show : {
															'allow' : [
																'co0050995', # Sky (tt5932548)
																'co0217380', # Sky Network Television (tt3502248)
																'co0329071', # Sky Atlantic (tt3498622)
																'co0374625', # Sky Atlantic HD (tt3498622)
																'co0537097', # BBC First (tt4374208)
																'co0043107', # BBC (tt5687612, tt11771270)
																'co0234667', # BBC One (tt11646832, tt10405370, tt11771270)
																'co0399177', # BBC Three (tt5687612)
																'co0698073', # BBC Studios (tt1869454, tt11771270)
																'co0706824', # Channel 4 (tt4374208)
																'co0287003', # Epix (tt5932548, tt10405370)
																'co0981653', # Discovery Force Channel (tt6741278)
																'co0981669', # Discovery Toons (tt6741278)
																'co0984883', # Discovery Toons (tt6741278, tt3952746)
																'co1010769', # Discovery Kids (tt3952746)
																'co0614571', # Discovery Kids (tt3952746)
																'co0007546', # Nickelodeon Network (tt3952746)
																'co0202535', # Fox (tt3502248)
																'co0015194', # ITV - Independent Television (tt6964748)
																'co0216142', # NBC Universal International (tt6932244)
																'co0724274', # TNT Series (tt4607112)
																'co0103727', # British Sky Broadcasting (BSkyB) (tt4607112)
																'co0103528', # Channel 4 Television Corporation (too much other content listed here that too many titles might be excluded with CH4 networks).
															],
															'exclude' : [
																# There is currently only 1 show on Hulu from Amazon or MGM (tt28082724).
																# https://en.wikipedia.org/wiki/List_of_Hulu_original_programming
																# There are however many other Hulu shows than can not be excluded with other companies.
																#'co0059995',	# Warner Home Video (tt6474236) - Do not include for tt3498622.
																#'co0508149',	# Legendary Television (tt6474236) - Do not include for tt0489974.
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanySky			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyStarz			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCinemax		: [MetaProvider.CompanyNetwork]},

																'co0684443', # Viu (tt13634792)
																'co0571670', # Freeform (tt11083696)
																'co0006395', # Lifetime (tt3314218)
																'co0362812', # Videoland (tt5603140)
																#'co0611078', # Videoland (tt3996656) - Allow for tt20252368
																'co0335765', # Just Bridge Entertainment (tt3996656)
																'co0715422', # Quibi (tt10580064, tt10726424)
																'co0539690', # Fuji TV (tt8515016)
																'co0890429', # Viaplay Studios (tt23781186) - Not Viaplay co0488702 for tt13315664,
																'co0332053', # tvN (tt26493973)
																'co0028644', # SBS (tt10405370)
																'co0013021', # Walt Disney Television (tt8089592)
																'co0129175', # NBC Universal Television (tt2262456)
																'co0164664', # ARTE (tt0780362) - Do not include co0014456 for tt3498622.
																'co0396455', # Me-TV (tt0126158)
																'co0035005', # AT-X (tt11595706)
																'co0845675', # Tving (tt14166656)
																'co0367880', # DiziMax (tt4789576)
																'co0120210', # Tokyo MX (tt28685470)
																'co0039462', # Public Broadcasting Service (PBS) (tt6889090)
																'co0743251', # Universal Pictures Home Entertainment (tt8463714)
																'co0003716', # History Channel (tt2167393, tt2338096)
																'co0025978', # Norsk Rikskringkasting (NRK) (tt8347410)
																'co0724460', # Tubi TV (tt0096816)
																'co0493506', # iQIYI (tt14518610)
																'co0760183', # START (tt10199718)
																'co0028557', # Canal+ (tt8382834)
																'co0916189', # Maxdome (tt0435995)
																'co0680232', # HBO España (tt8427140)
																'co0077535', # The WB Television Network (tt0259141)
																'co0593772', # Globoplay (tt10343984)
																'co0487058', # Tencent Video (tt13417558)
																'co0275386', # Sentai Filmworks (tt10778040)
																'co0061664', # ABC Video (tt0286342)
																'co0036798', # Court TV (tt0156442)
																#'co0013526', # Yleisradio (YLE) (tt8760304) - Do not use for tt5687612.
																'co0800011', # Leonine Distribution (tt8760304)
																#'co0114002', # Madman Entertainment (tt7551216) - Do not use for tt3503520.
																'co0043688', # Canal+ Polska (tt7551216)
																'co0202446', # YouTube (tt0115228)
																'co0114908', # Mainichi Broadcasting System (MBS) (tt8696458)
																'co0295850', # ServusTV (tt0368730)
																'co0879800', # Google Play (tt0339702)
																'co0172129', # Mill Creek Entertainment (tt0138230)
																'co0025002', # TV Asahi (tt0159182)
																'co0008941', # Breakthrough Entertainment (tt2817476)
																'co0351891', # Signature Entertainment (tt0065322)
														]},
														Media.Movie	: {
															'disallow' : [
																# There are too many India films on Amazon that are not originals.
																# These India titles are all from different companies (producer and distributor).
																# But disallowing "Amazon India" does not solve the full problem, because many Indian titles are added under Amazon Prime Video (co0476953).
																# So for now, still exclude Indian titles manually, by adding IDs to "exclude".
																#'co0939864',	# Amazon India.
															],
															'exclude' : [
																# Do not inlcude Hulu, since some movies on there are produced by Amazon Studios (tt2180339).
																# {MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyStudio]}, # tt10362466, tt13069986, tt12672536
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # tt3322940
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # tt0181689
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]}, # tt14331144
																{MetaCompany.CompanyTubi			: [MetaProvider.CompanyNetwork]}, # tt5883632
																{MetaCompany.CompanyAdultswim		: [MetaProvider.CompanyNetwork]}, # tt14636170
																#{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]}, # tt16426418 - Do not add for tt14948432.

																'co0202446', # YouTube (tt1281966)
																'co0240130', # StudioCanal UK (tt13397574)
																'co0157100', # Koch Media (tt4016934)
																'co0072847', # Splendid Film (tt15744298)
																'co0623930', # Neon (tt9484998)
																'co0014456', # Arte (tt0976051)
																'co0291948', # Kino Lorber (tt17527468)
																'co0152990', # Roadshow Entertainment (tt15334488)
																'co0530363', # Cinemundo (tt16426418) - Do not add Warner, due to tt14948432.
																'co0137851', # Sony Pictures Home Entertainment (tt9848626)
																'co0183709', # Universal Pictures International (UPI) (tt2910904) - do not add all Universal vendors, otherwise there are too many IDs and some important ones are cut off.
																'co0820078', # Universal Pictures International (UPI) (tt4685762)
																'co0023827', # Universal Pictures Home Entertainment (UPHE) (tt1855199)
																'co0776428', # 7flix (tt5814060)
																'co0147162', # Shaw Organisation (tt11127680, tt5989218)
																'co0061229', # Seven Network (tt0409182)
																'co0608555', # Arthaus (tt1212428)
																'co0427244', # Vertical Entertainment (tt26625693)
																'co0412767', # Uncork'd Entertainment (tt4711924)
																'co0351891', # Signature Entertainment (tt13923456)
																#'co0733129', # United Artists Releasing (tt14456350, tt4873118) - Do not add because of tt12262116.
																'co0760183', # START (tt14456350)
																'co0514540', # Movie Cloud (tt4873118)
																'co0220024', # Gravitas Ventures (tt6865630)
																'co0058013', # Samuel Goldwyn Films (tt5895892)
																'co0000689', # Odeon (tt9252488)
																'co0158672', # Golden Screen Cinemas (tt27641085)
																'co0092769', # Screen Media Films (tt11649338)
																'co0014453', # Sony Pictures Classics (tt0048473)
																'co0130438', # AMC Theatres (tt14379088)
																'co0313320', # Film1 (tt10199590)
																'co0003850', # Nippon Television Network (NTV) (tt0923811)
																'co0370614', # Tanweer Alliances (tt5822564)
																'co0879800', # Google Play (tt28103733)
																'co0422781', # Google Play (tt1047102)
																'co0551035', # The Searchers (tt7671064)
																'co0076345', # Metrodome Distribution (tt0424938)
																'co0024325', # Dutch FilmWorks (DFW) (tt8535180)
																'co0122766', # Umbrella Entertainment (tt12982370)
																'co0939736', # Plaion Pictures (tt17595262)
																'co0467911', # GoDigital (tt3176980)
																'co0223766', # Indie Rights (tt7620554)
																'co0466997', # GSC Movies (GSCM) (tt26489336)
																'co0051618', # Entertainment One (tt1656177)
																'co0298063', # Vimeo (tt4064498)
																'co0853115', # Vivamax (tt16452694)
																'co0313190', # NTR (tt8639136)
																'co0011466', # Antenna Entertainment (tt27860430)
																'co0640369', # Ammo Content (tt3737840)
																'co0883080', # Great American Family (tt13273728)
																'co0032922', # Hallmark Channel (tt15829734)
																'co0652345', # Digicine (tt30850554)
																'co0011688', # Bridgestone Multimedia (tt11136662)
																'co0034057', # Indican Pictures (tt4927984)
																'co0894072', # RTL+ (tt17524292)
																'co0309225', # 101 Films (tt13063384)
																'co0079290', # Fremantle (tt13626200)
																'co0005266', # ITN Distribution (tt10078886)
																'co0026841', # United Artists (tt0027869)
																'co0341688', # Buffalo 8 Productions (tt14027672)
																'co0228071', # Interfilm (tt4971408)
																'co0003188', # IPA Asia Pacific (tt5340882)
																'co0535228', # Kinologistika (tt27680383)
																'co0041263', # Salzgeber & Company Medien (tt19800090)
																'co0989452', # NDR (tt9812614)
																'co0057093', # TLA Releasing (tt1266073)
																'co0158822', # IndieFlix (tt1311031)
																'co0005584', # Alliance (tt0118763)
																'co0836187', # Stream Go Media (tt0045609)
																'co0465489', # Elevation Pictures (tt5268348)
																'co0270203', # CD Land (tt4629032)
																'co0061460', # France 3 (tt0037166)
																'co0131785', # NBC Universal Television Distribution (tt0080128)
																'co0395148', # Vinegar Syndrome (tt0125510)
																'co0362667', # Full Moon Features (tt8073604)
																'co0015762', # IFC Films (tt3268340)
																'co0441308', # Rajawali Citra Televisi Indonesia (RCTI) (tt11710090)
																'co0149420', # Suraya Filem (tt25872924)

																# Indian - Listed under the normal "Amazon", not "Amazon India".
																'co0095447', # Annapurna Studios (tt10698680)
																'co0797864', # Aha (tt0116630)
																'co0629395', # Hotstar (tt3863552)
																'co0285709', # Sun TV (tt10189514)
																'co0077190', # Yash Raj Films (tt0420332, tt0112870, tt0441048, tt1182937, tt0118983) This will exclude tt19755170.
																'co0110152', # Yash Raj Films International Ltd. (tt9105014)
																'co0274702', # Zee Studios (tt7098658)
																'co0237670', # Phars Film (tt7838252, tt24517830)
																'co0262079', # AA Films (tt9389998, tt7778680)
																'co1017567', # YouTube (tt5764096)
																'co0089614', # Sri Balaji Video (tt11591306)
																'co0832091', # Dhinchaak (tt6988116)
																'co0548846', # IMGC Global Entertainmet (tt2806788)
																'co0015398', # iDream Productions (tt5918074)
																'co0093603', # Bcineet (tt5918074)
																'co0336601', # Reliance Entertainment (tt0315642)
																'co0277906', # Mind Blowing Films (tt8144834)
																'co0333827', # Star VijayTV (tt8176054, tt6067752)
																'co0026065', # Raajkamal Films International (tt0364647)
																'co0266060', # Fox STAR Studios (tt3709344)
																'co0050176', # Eros Worldwide (tt0222012, tt11460992)
																'co0700204', # Zee Tamil (tt6380520)
																'co0450251', # Night Ed Films (tt22170036)
																'co0723835', # Sun NXT (tt0482389)
																'co0451721', # Jaya TV (tt5611648)
																'co0032513', # B4U Entertainment (tt0101649)
																'co0083916', # Suresh Productions (tt9799984)
																'co0121223', # StarPlus (tt1773015)

																# Indian - Not needed anymore, since we now exclude Amazon India.
																#'co0110172', # Ayngaran International (tt26233598)
																#'co0766492', # Friday Entertainment (tt27459160)
																#'co0808044', # Jio Cinema (tt26655108)
																#'co0124425', # Alive Vertrieb und Marketing (tt12844910)
																#'co0226633', # Bharat Entertainment International (tt0805184)
																#'co0322115', # Zee Cinema (tt15302222) Allow for tt19755170.
																#'co0078798', # Zee TV (tt0106333)
																#'co0582567', # Dimension Pictures (tt0073707)
																#'co0601433', # NH Studioz (tt7700730)
																#'co0637050', # Sakthi Film Factory (tt28857146)
																#'co0166112', # Eros Australia Pty. Ltd. (tt2385104)
																#'co0863532', # KVN Productions (tt11992424)
																#'co1018470', # Avenue Theatre (tt0278291)
																#'co0283500', # Studio Green (tt9688874)
																#'co0325324', # Magic Frames (tt27411198)
																#'co0588636', # Pooja Entertainment & Films (tt7329858)
																#'co0121223', # StarPlus (tt0494290)
																#'co0894909', # Goldmines Telefilms (tt0375066)
																#'co0088739', # Video Sound (tt0242519)
																#'co0546496', # Sony Liv (tt0195231)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0319272', 'co1025982', 'co0888198', 'co0477966'],
					MetaProvider.CompanyNetwork		: ['co0476953', 'co0337718', 'co0939864', 'co0515031', 'co0796766', 'co0931938', 'co0869098', 'co0665882', 'co0946652', 'co0260409', 'co0664543', 'co0609198', 'co0888198', 'co0616693', 'co0409640', 'co0348775', 'co0963571', 'co0994447', 'co1003340', 'co0994448', 'co0981326', 'co0630540', 'co0904701', 'co1028072', 'co1025228', 'co1011011', 'co1000687', 'co0999701', 'co0904703', 'co0904702', 'co0653187', 'co0115743'],
					MetaProvider.CompanyVendor		: ['co0042083', 'co0250772', 'co0249265', 'co0850778', 'co0491850', 'co0389614', 'co0968084', 'co0785664'],
				},

				MetaCompany.CompanyAmc : {
					# Show (246 of 87+): Level-3.
					# Movie (11 of 1?): Level-2. Not really any AMC original films.
					# https://en.wikipedia.org/wiki/Category:AMC_(TV_channel)_original_programming
					# Many AMC Originals are released on other major platforms (Netflix, Amazon, Apple, Fox, Hulu, ITV, BBC, etc).
					# BBC America is also jointly owned by BBC and AMC. Exclude them, because these are not typically AMC Originals.
					# Rather exclude studios.
					MetaProvider.CompanyOriginal	: {
														Media.Show	: {
															'disallow' : [
																# Do not exclude, just disallow, since it is a joint-venture between BBC and AMC.
																'co0118334',	# BBC America (tt0407362, tt0758790, tt14466018, tt1474684, tt0290988, still allow for tt7016936)

																# There are tons of titles from Sundance and IFC that have no AMC company listed under them.
																# Do not include them, since there are too many false positives.
																# Only disallow, not exclude, for those titles that have both Sundance/IFC and AMC companies listed.
																# Still allow eg tt14466446.
																'co0163116',
																'co0109271',
																'co0164785',
																'co0609786',
																'co0007113',
																'co0746323',
																'co0536718',
																'co0319525',
																'co0822328',
																'co0354847',
																'co0816708',
																'co0536717',
																'co1036643',
																'co0888151',
																'co0015762',
																'co0310156',
																'co0046530',
																'co0180145',
																'co0252564',
																'co0013560',
																'co0258945',
																'co0832893',
																'co0340786',
																'co0217619',
																'co0985922',
																'co0848594',
															],
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Do not add for tt0903747, tt6156584.
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Do not add for tt0903747, tt1520211.
																#{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # Do not add for tt1520211.
																#{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # Do not add for tt6156584.
																#{MetaCompany.CompanyApple		: [MetaProvider.CompanyNetwork]}, # Do not add for tt14688458.

																'co0216537',	# FX Productions (tt2802850)
																'co0094955',	# Fox Television Studios (tt1637727)
																'co0048735',	# CBS Productions (tt0313043)
																'co0618997',	# Bad Wold (tt2177461)
																#'co0053559',	# Paramount Television (tt0053479) - Do not use for tt3960394
																'co0241671',	# Danny Thomas Enterprises (tt0053479)
																'co0073081',	# Apatow Productions (tt0193676)
																'co0104730',	# Red Production Company (tt3428912)
																'co0165398',	# Reel World Management (tt21064598)
																'co0073684',	# Fandango (tt2049116)
																'co0072097',	# World Productions (tt15548144)
																'co0963582',	# Kuma Productions (tt23856194)
																'co0337799',	# Bavaria Fiction (tt5830254)
																'co0131884',	# Cinenord (tt7875794)
																'co0382708',	# Zip Works (tt2183404)
																'co0753658',	# PGM TV (tt8571906)
																'co0633628',	# Lingo Pictures (tt8765446)
																'co0242101',	# Universal Cable Productions (tt4820370)
																'co0007127',	# New Regency Productions (tt9062784)
																'co0886612',	# Anton Capital Entertainment (tt7660970)
																'co0559293',	# Boom Cymru (tt6006350)
																'co0075561',	# Hal Roach Studios (tt0278213)
																'co0835564',	# Altitude Television (tt13636038)
																'co0357122',	# FremantleMedia Australia (tt21632956)
																'co0396344',	# Narrativia (tt8080292)
																'co0635718',	# OceanX Media (tt6769208)
																'co0814898',	# NENT Studios U.K. (tt6831266)
																'co0302822',	# Matchbox Pictures (tt1823011)
																'co0353891',	# BYUtv (tt15113594)
																'co0035637',	# FremantleMedia (tt10394886)
																'co0910759',	# OLM (tt21844490)
																'co0709489',	# Forta (tt14989818)
																'co0608240',	# Shanghai GCOO Entertainment (tt10369876)
																'co0103820',	# Company Pictures (tt3495652)
																'co0525512',	# Palladium Fiction (tt2309405)
																'co0843701',	# Boulet Brothers Productions (tt6289132)
																'co0349395',	# Odeon Fiction (tt10625812)
																'co1024602',	# Jarowskij (tt5603186)
																'co0134332',	# Vico Films (tt8409626)
																'co0802736',	# Migu Video (tt9805678)
																'co0765260',	# Nordvision (tt12693148)
																'co0061958',	# ARD Degeto Film (tt5917226)
																'co0634035',	# Atlantia Media (tt14716434)
																'co0586459',	# Dramacorp (tt8290414)
																'co0419528',	# Lincoln TV (tt4999820)
															],
														},
														Media.Movie	: {
															'fixed' : MetaProvider.CompanyStudio,
															'disallow' : [
																# Do not exclude, just disallow, since it is a joint-venture between BBC and AMC.
																'co0118334',	# BBC America
																'co0332012',	# AMC Networks (tt0111161)

																# There are tons of titles from Sundance and IFC that have no AMC company listed under them.
																# Do not include them, since there are too many false positives.
																# Only disallow, not exclude, for those titles that have both Sundance/IFC and AMC companies listed.
																'co0163116',
																'co0109271',
																'co0164785',
																'co0609786',
																'co0007113',
																'co0746323',
																'co0536718',
																'co0319525',
																'co0822328',
																'co0354847',
																'co0816708',
																'co0536717',
																'co1036643',
																'co0888151',
																'co0015762',
																'co0310156',
																'co0046530',
																'co0180145',
																'co0252564',
																'co0013560',
																'co0258945',
																'co0832893',
																'co0340786',
																'co0217619',
																'co0985922',
																'co0848594',
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0118334', 'co0332012', 'co0318834', 'co0163116', 'co0109271', 'co0287744', 'co0164785', 'co0985922', 'co0609786', 'co0992498', 'co0896081', 'co0649866', 'co0329743', 'co0039494'],
					MetaProvider.CompanyNetwork		: ['co0015762', 'co0007113', 'co0602021', 'co0310156', 'co0019701', 'co0046530', 'co0118334', 'co0332012', 'co0815501', 'co0180145', 'co0340786', 'co0848594', 'co0746323', 'co0668189', 'co0217619', 'co0570103', 'co0252564', 'co0536718', 'co0319525', 'co0737214', 'co0251921', 'co0013560', 'co0822328', 'co0354847', 'co0258945', 'co0832893', 'co0816708', 'co0759230', 'co0536717', 'co0822529', 'co0797042', 'co1070323', 'co1036643', 'co0888151'],
					MetaProvider.CompanyVendor		: ['co0379646', 'co0092267', 'co0794271', 'co0442035', 'co0208997', 'co0441631', 'co0163378', 'co0861142', 'co0495248'],
				},

				MetaCompany.CompanyApple : {
					# Show (174 of 144+): Level-4. A few Apple originals appear on other platforms.
					# Movie (57 of 65+): Level-4. Relatively accurate movie originals.
					# https://en.wikipedia.org/wiki/Category:Apple_TV%2B_original_programming
					# https://en.wikipedia.org/wiki/Category:Apple_TV%2B_original_films
					# https://en.wikipedia.org/wiki/List_of_Apple_TV%2B_original_programming
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'allow' : [
																'co0103528', # Channel 4 Television Corporation (too much other content listed here that too many titles might be excluded with CH4 networks).
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},

																{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork]}, # tt0095707. Not the studios for tt18351584, tt21088136.
																{MetaCompany.CompanyBbc			: [MetaProvider.CompanyNetwork]}, # tt0111993
																{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]}, # tt0099698
																{MetaCompany.CompanyYoutube		: [MetaProvider.CompanyNetwork]}, # tt12879180
																{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # tt11112478

																'co0741656', # Twisted Mirror TV (tt6274606)
																'co0093604', # CBS Broadcasting (tt6396082)
																'co0635189', # Seeka TV (tt12205436)
																'co0008949', # Korean Broadcasting System (KBS) (tt14169420)
																'co0583843', # CuriosityStream (tt16122518)
																'co0583843', # CuriosityStream (tt0099698)
															],
														},
														Media.Movie : {
															'allow' : [
																'co0284741', # HBO Entertainment. Do not add for tt19853258 (under Other Companies).
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},

																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # tt15727212
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # tt0106677
																{MetaCompany.CompanyTubi			: [MetaProvider.CompanyNetwork]}, # tt5553210
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]}, # tt0078754
																#{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]}, # tt0059026. Do not add for tt15326988 (under Other Companies).
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]}, # tt0155388
																#{MetaCompany.CompanyParamount	: [MetaProvider.CompanyVendor]}, # tt0387301. Do not add for tt19853258 (under Other Companies).

																'co0037052', # American Broadcasting Company (ABC) (tt0387301)
																'co0059995', # Warner Home Video (tt0059026)
																'co0151501', # Capelight Pictures (tt0106677)
																'co0103538', # Portman Entertainment Group (tt0106422, tt0101462)
																'co0029578', # Portman Global Ltd. (tt0117601)
																'co0128056', # Universal Music Enterprises (tt0393449)
																'co0074573', # Rudolf Steiner Film (tt14682964)
																'co0041509', # World Wide International Television (tt0097352)
																'co0346444', # Ciné+ (tt28075464)
																'co0220024', # Gravitas Ventures (tt27544533)
																'co0314632', # Freestyle Digital Media (tt13646460)
																'co0305404', # Raven Banner Entertainment (tt4632976)
																'co0209560', # Grindstone Entertainment Group (tt22309256)
																#'co0292909', # Lionsgate Home Entertainment (tt22309256) - Do not add for tt9606374.
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0861654', 'co0822606'],
					MetaProvider.CompanyNetwork		: ['co0546168'],
					MetaProvider.CompanyVendor		: ['co0694131', 'co0177409', 'co0854529', 'co0424544', 'co0585513', 'co0804590', 'co0531699', 'co0428931', 'co0931939', 'co0750014', 'co0239755', 'co1033989', 'co0657282', 'co0636343', 'co1021371', 'co0613564', 'co0887931'],
				},

				MetaCompany.CompanyArd : {
					# Show (4161): Level-3
					# Movie (14053): Level-3
					# Difficult to filter, since co-productions and content-sharing with Britain, France, Scandinavia, and most European countries, even a few with US and AU.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# DW (probably mostly news)
																'co0804512',

																# KiKa
																'co0030553', 'co0895262', 'co0937862', 'co1050978',
															],
														},
														Media.Show : {
															'exclude' : [
																# Too many ARD titles on BBC. Only use studios.
																# Too many studios, the smaller ones (eg: BBC Drama Group) will be cut off.
																#{MetaCompany.CompanyBbc			: [MetaProvider.CompanyNetwork]}, # tt0081834, tt0200849, tt14211026, tt0907702, tt0306353
																{MetaCompany.CompanyBbc			: [MetaProvider.CompanyStudio]},

																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt0120949
																{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]}, # tt0106089
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # tt7085256
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]}, # tt1001482
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]}, # tt1436544
																{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]}, # tt2071322
																{MetaCompany.CompanySky			: [MetaProvider.CompanyNetwork]}, # tt6921882
																{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork]}, # tt0078600
																{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # tt1513168
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # tt0118500
																{MetaCompany.CompanyChannel5		: [MetaProvider.CompanyNetwork]}, # tt4689402
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # tt21105638
																{MetaCompany.CompanyAcorn			: [MetaProvider.CompanyNetwork]}, # tt3640276
																{MetaCompany.CompanyAubc			: [MetaProvider.CompanyNetwork]}, # tt0088573
																{MetaCompany.CompanyCbc			: [MetaProvider.CompanyNetwork]}, # tt1875337

																'co0831073', # Gain (tt7920978)
																'co0816435', # ChaiFlicks (tt27195940)
																'co1026942', # Eyeworks (tt1129398)
																'co0039462', # Public Broadcasting Service (PBS) (tt0383795)
																'co0032224', # Titanus (tt0074050)
																'co0028644', # Special Broadcasting Service (SBS) (tt13079194, co0028644)
																'co0005084', # National Geographic (tt13079194)
																'co0396719', # DreamWorks Classics (tt0118380)
																'co0523322', # Stan (tt11385266)
																'co0024027', # The Family Channel (tt0096551)
																'co0189627', # Qubo (tt1728224)
																'co0584275', # Screenbound International Pictures (tt0144729)
																'co0734577', # Multimania TV (tt1073449)
																'co0362268', # WOWOW Prime (tt2377081)
																'co0287296', # AXN Mystery (tt0106042)
																'co0541528', # Gloob (tt6328652)
																'co0405477', # Cyber Group Studios (tt4641870)
																'co0350619', # Dandelooo (tt4641870)
																'co0003716', # History Channel (tt1591535)
																'co0103528', # Channel 4 Television Corporation (tt0377171)
																'co0147982', # Okko Productions (tt0261964)
																'co0103738', # BBC Entertainment (tt0111931)
																'co0197209', # BBC Cymru Wales (tt3159736)
																'co0103536', # BBC Drama Group (tt0259733)
																'co0118334', # BBC America (tt0969007)
																'co0104217', # Rollem Productions (tt3428478)
																'co0563461', # Rede Globo (tt0209555)
																'co0265997', # CBeebies (tt3533604)
																'co0059995', # Warner Home Video (tt0179569)
																'co0007979', # Network Ten (tt2436456)
															],
														},
														Media.Movie : {
															'exclude' : [
																# Too many ARD titles on BBC. Only use studios.
																{MetaCompany.CompanyBbc			: [MetaProvider.CompanyStudio]},

																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanySky			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyChannel5		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAcorn			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAubc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCbc			: [MetaProvider.CompanyNetwork]},

																'co0028644', # Special Broadcasting Service (SBS) (tt13079194, co0028644)
																'co0005084', # National Geographic (tt13079194)
																'co0396719', # DreamWorks Classics (tt0118380)
																'co0523322', # Stan (tt11385266)
																'co0024027', # The Family Channel (tt0096551)
																'co0362268', # WOWOW Prime (tt2377081)
																'co0287296', # AXN Mystery (tt0106042)
																'co0003716', # History Channel (tt1591535)
																'co0103528', # Channel 4 Television Corporation (tt0377171)
																'co0103738', # BBC Entertainment (tt0111931)
																'co0197209', # BBC Cymru Wales (tt3159736)
																'co0103536', # BBC Drama Group (tt0259733)
																'co0118334', # BBC America (tt0969007)
																'co0265997', # CBeebies (tt3533604)
																'co0059995', # Warner Home Video (tt0179569)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0061958', 'co0041492', 'co0114174', 'co0237938', 'co0065221', 'co1069396', 'co0442963', 'co0908647', 'co0174684', 'co0695411', 'co0380454', 'co0128591', 'co0087780', 'co0297730', 'co0323874', 'co0285377', 'co0787553', 'co0319227', 'co0763053', 'co0753522', 'co0378995', 'co0084641', 'co1063921', 'co1045188', 'co1039527', 'co1018274', 'co1017738', 'co0959826', 'co0910946', 'co0888797', 'co0879011', 'co0827406', 'co0805147', 'co0632705', 'co0626833', 'co0622450', 'co0622438', 'co0527723', 'co0291283', 'co0242006', 'co0194454', 'co0011697', 'co0000497'],
					MetaProvider.CompanyNetwork		: ['co0075650', 'co0051615', 'co0024077', 'co0028284', 'co0047104', 'co0099654', 'co0015124', 'co0072480', 'co0840291', 'co0799614', 'co0030553', 'co0217768', 'co0852680', 'co0014369', 'co0203048', 'co0274575', 'co0768255', 'co0452750', 'co0041492', 'co0114174', 'co0248658', 'co0059346', 'co0961937', 'co0895262', 'co0989452', 'co0937862', 'co0003707', 'co0185608', 'co0048844', 'co0181346', 'co0178657', 'co1034271', 'co0001882', 'co0091806', 'co1059146', 'co0918729', 'co1069396', 'co0839861', 'co1050978', 'co0894463', 'co0894460', 'co0860660', 'co0685769', 'co0609268', 'co0064040', 'co0055445', 'co0840146', 'co0208114', 'co0968172', 'co0895263', 'co0227567', 'co0476379', 'co0839856', 'co0971729', 'co0180705', 'co0992810', 'co0223205', 'co1000425', 'co0889776', 'co0982164', 'co0613282', 'co0497336', 'co1035748', 'co1020144', 'co0914202', 'co0905950', 'co0878991', 'co0804512', 'co0577985', 'co0988580', 'co0891048', 'co0489664'],
					MetaProvider.CompanyVendor		: ['co0085892', 'co0833555', 'co0738126', 'co1011585', 'co0760311', 'co0616840', 'co0604266', 'co0549240', 'co0503369', 'co0382269', 'co0328560', 'co0298474', 'co0298180', 'co0264412', 'co0125917', 'co0125915', 'co0125914', 'co0125086', 'co0125085', 'co0114620', 'co0549239', 'co0294660', 'co0212720', 'co0135975', 'co0107837'],
				},

				MetaCompany.CompanyAubc : {
					# Show (871): Level-3 to Level-4
					# Movie (729): Level-3
					# Many collaborations with BBC, and other British and German channels. Generally difficult to filter UK content.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'allow' : [
																# Foxtel (Australia)
																'co0119102',
																'co0039238',
																'co0227681',
																'co0778133',
																'co0174174',
																'co0626569',
																'co0919693',
																'co0974175',

																'co0103528', # ITV Studios Australia
																'co0659811', # BBC Studios (AU)
																'co0752302', # BBC Worldwide ANZ (AU)
																'co0560305', # Sky Business (AU)
																'co0329023', # Sky News Australia (AU)
																'co0295048', # Sky Pictures (AU)
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]}, # tt23845296, tt0185102, tt0103381
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Not for tt4192782, tt4878488, tt7371868, tt1587000.
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Not for tt13315664.
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # tt0273366, tt0138967. Not for tt0454656.
																#{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # tt0092383. Not for tt9214692, tt2699780, tt1401650.
																{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork]}, # tt23576878, tt15548144. Not studios (tt20697956, tt2155043).
																#{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]}, # tt1008108. Not (tt0090521).
																{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]}, # tt10691770
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # tt0387764
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # tt4122068
																{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # tt4644488
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # tt8201186
																{MetaCompany.CompanyBritbox		: [MetaProvider.CompanyNetwork]}, # tt0478942
																{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]}, # tt2141913
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]}, # tt0352085, tt4573608
																{MetaCompany.CompanyCartoonnet	: [MetaProvider.CompanyNetwork]}, # tt7446086
																#{MetaCompany.CompanyAcorn		: [MetaProvider.CompanyNetwork]}, # tt4905554, tt16343844. not for tt2699780.
																#{MetaCompany.CompanyCbc			: [MetaProvider.CompanyNetwork]}, # tt2155025, tt21058104
																#{MetaCompany.CompanySky			: [MetaProvider.CompanyNetwork]}, # tt1610518, tt7005920
																#{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # tt2401525
																#{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]}, # Not for tt7537096

																# Too much other content listed here that too many titles might be excluded with CH4 networks.
																#'co0103528', # Channel 4 Television Corporation (tt0111958, tt0262150, tt3330720). Not for tt0103381.

																'co0008693', # Home Box Office (HBO) (tt0096708, tt0092383)
																'co0039462', # Public Broadcasting Service (PBS) (tt1430509)
																'co0112383', # RTL Entertainment (tt1008108)
																'co0225981', # RTL Crime (tt1701920)
																'co0035005', # AT-X (tt0205410)
																'co0189627', # Qubo (tt0190178)
																'co0601402', # House Productions (tt13994572)
																'co0103660', # Channel X (tt4082744)
																'co0301399', # Alibi (tt9788012)
																'co0131570', # Marvel Comics (tt1441105)
																'co0103628', # Hat Trick Productions (tt0111958)
																'co0039940', # FUNimation Entertainment (tt0816397)
																'co0062107', # Toei Animation (tt3124992)
																'co0028689', # Manga Entertainment (tt0877057)
																'co0527221', # Bandit Television (tt6059460)
																'co0005803', # Muse Entertainment Enterprises (tt1567215)
																'co0103531', # Aardman Animations (tt0983983)
																'co0075163', # Henson Associates (HA) (tt0092383)
																'co0113685', # Novel Entertainment Productions (tt0373533)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0051111', 'co0573602', 'co0691266', 'co0674885', 'co0451084', 'co0805649', 'co0798189', 'co0699016', 'co0691282', 'co0595394', 'co0142606'],
					MetaProvider.CompanyNetwork		: ['co0051111', 'co0638282', 'co0589680', 'co0530354', 'co0385785', 'co0432662', 'co0513317', 'co0061664', 'co0202700', 'co0142963', 'co0395856', 'co0573602', 'co1059801', 'co0396190', 'co0772897', 'co1030092', 'co0892324', 'co0892147', 'co0157128'],
					MetaProvider.CompanyVendor		: ['co0146211', 'co0324755', 'co0300082', 'co0099385', 'co0107728', 'co0167586', 'co0404882', 'co0225761', 'co0225761', 'co1055432', 'co0960276', 'co0805995', 'co0805351', 'co0771493', 'co0752802', 'co0730018', 'co0696457', 'co0690730', 'co0649060', 'co0647385', 'co0610625', 'co0326245', 'co0298327', 'co0220836', 'co0211730'],
				},
				MetaCompany.CompanyBbc : {
					# Show (3510): Level-3. Not sure if this can be improved in any way. A l.ot of other originals (ITV, HBO, etc) that cannot be filtered out.
					# Movie (3035): Level-2
					# Very difficult to exclude anything.
					# BBC has tons of content from US and other countries, but at the same time most BBC Originals appear on US networks, and even on British competitive network.
					# It even goes so far that "originals" change:
					#	The new Doctor Who is now a Disney+ original.
					#	Peaky Blinders is now a Netflix original.
					# And then there are so many cross-border collaborations. Not only BBC America (BBC+AMC), but also co-productions with HBO, Disney, ITV, CH4, AUBC, etc.
					# It is therefore nearly impossible to filter out other content without filtering out real/big BBC originals.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'allow' : [
																'co0203432', # CNBC-e (tt0436992). Listed as vendor under NBC in any case.
															],
															'disallow' : [
																# It seems that (probably) all BBC Originals have another BBC company listed under them.
																# Either a local BBC studio, or one of the channels (BBC 1-3, iPlayer, etc).
																# Many non-BBC Originals typically only have this ID listed.
																# By excluding this ID, the titles drop from 10k to 4k.
																# Not sure if this removes smaller BBC originals that only have this ID listed.
																# But this seems one of the most effective way of filtering out other content.
																'co0043107', # British Broadcasting Corporation (BBC) (GB)

																# Children's BBC
																'co0219933', 'co0265997', 'co0871749', 'co0832669', 'co0410030', 'co0451949', 'co0639136', 'co0639136', 'co0381268', 'co0457128', 'co0324563', 'co0134301', 'co0219545', 'co0104248', 'co0831132',

																# BBC News
																'co0530479', 'co0114729', 'co0460362', 'co0114728', 'co0531653', 'co0405647', 'co0861902', 'co0324701',
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Not for tt2442560, tt28118211, tt4179452, tt1475582, tt0185906.
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Not for tt1869454, tt10405370, tt2442560, tt1888075, tt0056751, tt11646832.
																#{MetaCompany.CompanySky			: [MetaProvider.CompanyNetwork]}, # Not for tt2442560, tt1888075.
																#{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork]}, # Not for tt2396135, tt0056751, tt0808096.
																#{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # Not for tt7671070, tt0436992, tt1475582, tt0185906, tt7016936, tt5607976.
																#{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # Not for tt0436992, tt1475582, tt1888075, tt31433814, tt7016936.
																#{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # Not for tt0436992, tt0056751.
																#{MetaCompany.CompanyPluto		: [MetaProvider.CompanyNetwork]}, # Not for tt1475582.
																#{MetaCompany.CompanyWarner		: [MetaProvider.CompanyNetwork]}, # Not for tt0185906.
																#{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]}, # Not for tt1888075.
																#{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # Not for tt2303687, tt9059760.
																#{MetaCompany.CompanyAcorn		: [MetaProvider.CompanyNetwork]}, # Not for tt2303687, tt2294189, tt0362357.
																#{MetaCompany.CompanyBravo		: [MetaProvider.CompanyNetwork]}, # Not for tt2294189, tt7016936.
																#{MetaCompany.CompanyMgm			: [MetaProvider.CompanyNetwork]}, # Not for tt10405370.
																#{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # Not for tt7016936.
																#{MetaCompany.CompanyStarz		: [MetaProvider.CompanyNetwork]}, # Not for tt7016936.
																#{MetaCompany.CompanyAe			: [MetaProvider.CompanyNetwork]}, # Not for tt0115355.
																#{MetaCompany.CompanyCinemax		: [MetaProvider.CompanyNetwork]}, # Not for tt4276618.
																#{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # Not for tt15557874.
																#{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]}, # tt0758790 (BBC original). Not for tt10661302, tt21822590.
																{MetaCompany.CompanyChannel5		: [MetaProvider.CompanyNetwork]}, # tt10590066. Not sure if there are any co-productions, since CH5 is now owned by Paramount.

																#'co0014456', # ARTE. Not for tt2442560.
																#'co0618997', # Bad Wolf. Both ITV and BBC have a lot of titles produced by them (tt2401256).
																#'co0051111', # Australian Broadcasting Corporation (ABC). Not for tt0436992.
																#'co0045850', # Canadian Broadcasting Corporation (CBC). Not for tt0436992.
																#'co0039462', # Public Broadcasting Service (PBS). Not for tt1475582, tt9179616.

																'co0072315', # National Broadcasting Company (NBC) (tt0386676, tt0098844, tt0098904)
																'co0037052', # American Broadcasting Company (ABC) (tt0053502)
																'co0070627', # CBS (tt0460649, tt11379026)
																'co0170466', # CBS Paramount Domestic Television (tt0092455)
																'co0007821', # CBS Studios (tt18228732)
																'co0159275', # Fox Television Animation (tt0096697, tt0182576)
																'co0056447', # 20th Century Fox Television (tt0212671, tt0106179, tt9174558)
																'co0741733', # Searchlight Television (tt10166622)
																'co0216537', # FX Productions (tt7908628, tt6439752, tt5715524, tt8134186)
																'co0123927', # DC Entertainment (tt11192306)
																'co0578069', # Marvel Entertainment Group (tt0103584)
																'co0047120', # Marvel Entertainment (tt10862280)
																'co0051941', # Marvel Studios (tt0772145)
																'co0028689', # Manga Entertainment (tt0168366)
																'co0045140', # Showcase Television (tt0290988)
																'co0054762', # Alliance Atlantis Communications (tt0288937)
																'co0142434', # Alloy Entertainment (tt13075042)
																'co0053559', # Paramount Television (tt3829868)
																'co0129164', # DreamWorks Animation (tt7745956)
																'co0005051', # Turner Broadcasting System (TBS) (tt7745956)
																'co0067205', # Touchstone Television (tt0756509)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},

																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]}, # tt0935075
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]}, # tt0349683, tt0146882
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyStudio]}, # tt1623205, tt4566758

																'co0072315', # National Broadcasting Company (NBC)
																'co0037052', # American Broadcasting Company (ABC)
																'co0070627', # CBS
																'co0170466', # CBS Paramount Domestic Television
																'co0007821', # CBS Studios
																'co0159275', # Fox Television Animation
																'co0056447', # 20th Century Fox Television
																'co0741733', # Searchlight Television
																'co0216537', # FX Productions
																'co0123927', # DC Entertainment
																'co0578069', # Marvel Entertainment Group
																'co0047120', # Marvel Entertainment
																'co0051941', # Marvel Studios
																'co0028689', # Manga Entertainment
																'co0045140', # Showcase Television
																'co0054762', # Alliance Atlantis Communications
																'co0142434', # Alloy Entertainment
																'co0053559', # Paramount Television
																'co0129164', # DreamWorks Animation
																'co0005051', # Turner Broadcasting System (TBS)
																'co0067205', # Touchstone Television

																'co0024325', # Dutch FilmWorks (DFW) (tt0479528)
																'co0002572', # Millennium Films (tt1210042)
																'co0002219', # Toho (tt0050613)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0103694', 'co0592426', 'co0086182', 'co0219933', 'co0294698', 'co0130080', 'co0103752', 'co0103752', 'co0314450', 'co0125663', 'co0119621', 'co0129827', 'co0197209', 'co0457128', 'co0103738', 'co0698073', 'co0304634', 'co0296207', 'co0303279', 'co0159688', 'co0098758', 'co0740959', 'co0687055', 'co0317480', 'co0659275', 'co0104639', 'co0377983', 'co0098707', 'co0451949', 'co0618243', 'co0545558', 'co0432727', 'co0402393', 'co0402320', 'co0401549', 'co0324563', 'co0242639', 'co0231124', 'co0256436', 'co0134301', 'co0486599', 'co0485419', 'co0417954', 'co0377087', 'co0657045', 'co0752302', 'co0653588', 'co0305383', 'co0277403', 'co0245082', 'co0206538', 'co0855002', 'co0813700', 'co0307892', 'co0130009', 'co0103536', 'co0952028', 'co0501395', 'co0239708', 'co0875442', 'co0775667', 'co0726893', 'co0639136', 'co0606007', 'co0500559', 'co0486601', 'co0466169', 'co0315578', 'co0274311', 'co0178363', 'co0020220', 'co1016646', 'co0576599', 'co0486603', 'co0470945', 'co0403283', 'co0398746', 'co0295789', 'co0283200', 'co0219545', 'co0150936', 'co0131402', 'co0728849', 'co0685213', 'co0545593', 'co0534033', 'co0488378', 'co0486613', 'co0445171', 'co0441937', 'co0381268', 'co0369502', 'co0104248', 'co0078164', 'co1072031', 'co1048403', 'co1011972', 'co1006872', 'co1006871', 'co1000688', 'co0971251', 'co0945424', 'co0921192', 'co0920461', 'co0872432', 'co0853286', 'co0831132', 'co0801365', 'co0768859', 'co0761679', 'co0747089', 'co0692523', 'co0679922', 'co0659811', 'co0658426', 'co0621097', 'co0610967', 'co0608298', 'co0598746', 'co0579133', 'co0572286', 'co0544782', 'co0526172', 'co0516676', 'co0516672', 'co0516659', 'co0491244', 'co0486604', 'co0485699', 'co0463969', 'co0458044', 'co0442163', 'co0437284', 'co0418400', 'co0408144', 'co0370496', 'co0364786', 'co0363467', 'co0360835', 'co0353205', 'co0338843', 'co0299328', 'co0288712', 'co0263467', 'co0262608', 'co0246062', 'co0167164', 'co0146506', 'co0127837', 'co1067108', 'co1050406', 'co0901031', 'co0838768', 'co0717843', 'co0537139', 'co0516725', 'co0491243'],
					MetaProvider.CompanyNetwork		: ['co0043107', 'co0234667', 'co0234496', 'co0086182', 'co0399177', 'co0219933', 'co0265997', 'co0290595', 'co0534118', 'co0118334', 'co0422378', 'co0103544', 'co0537097', 'co0308047', 'co0132809', 'co0246015', 'co0530479', 'co0114729', 'co0453153', 'co0415789', 'co0164585', 'co0104650', 'co0832669', 'co1039429', 'co0531653', 'co0460362', 'co0317480', 'co0114728', 'co0477883', 'co0334989', 'co0142197', 'co0989615', 'co0503643', 'co0315543', 'co0206538', 'co0561347', 'co0405647', 'co0642119', 'co0621988', 'co0473661', 'co0471445', 'co0410030', 'co0726893', 'co0625141', 'co0348803', 'co0321381', 'co0853285', 'co1067868', 'co1045058', 'co0918458', 'co0883449', 'co0883439', 'co0883438', 'co0882716', 'co0871749', 'co0861902', 'co0806831', 'co0803582', 'co0781048', 'co0780894', 'co0482050', 'co0471188', 'co0401989', 'co0401784', 'co0370496', 'co0365373', 'co0324701', 'co0270289', 'co0479331'],
					MetaProvider.CompanyVendor		: ['co0103957', 'co0114992', 'co0137763', 'co0065632', 'co0200731', 'co0104087', 'co0225995', 'co0775667', 'co0649102', 'co0593490', 'co0990657', 'co0874518', 'co0709699', 'co0675085', 'co0294183', 'co0291731', 'co0281995', 'co0858275', 'co0417955', 'co0397748', 'co0344444', 'co0272944', 'co0106311', 'co0105842', 'co1019605', 'co1007584', 'co0990658', 'co0976553', 'co0963204', 'co0960250', 'co0955257', 'co0942671', 'co0912517', 'co0815297', 'co0811069', 'co0795915', 'co0786705', 'co0669375', 'co0660947', 'co0659116', 'co0631186', 'co0628629', 'co0548872', 'co0516755', 'co0516737', 'co0497354', 'co0440119', 'co0426629', 'co0377398', 'co0321397', 'co0261608', 'co0247569', 'co0210507', 'co0131862', 'co0094787', 'co0913252', 'co0870149', 'co0801464', 'co0797002', 'co0780683', 'co0774810', 'co0756060', 'co0492919', 'co0411485', 'co0388502', 'co0178374'],
				},
				MetaCompany.CompanyBoomerang : {
					# Show (83): Level-3. Most exclusions copied from Cartoon Network.
					# Movie (11): Level-3. Most exclusions copied from Cartoon Network.
					# Difficult to filter between Cartoon Network, Adult Swim, Boomerang, and other Warner companies.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# Too much other content.
																'co0444611', # Boomerang Latin America
															],
														},
														Media.Show : {
															'exclude' : [
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]}, # tt1596356 (sister channel)
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyStudio]},

																'co0127153', # Animax (tt9335498)
																'co0964339', # Animax ()
																'co0127153', # Animax ()
																'co0132285', # Aniplex (tt2250192)
																'co0035005', # AT-X (tt0409591)
																'co0453359', # Anime Ltd (tt0213338)
																'co0190623', # TV Setouchi Broadcasting (TSC) (tt1214085)
																'co0039940', # FUNimation Entertainment (tt4644488)
																'co0045850', # Canadian Broadcasting Corporation (CBC) (tt1094229, tt0491603)
																'co0571670', # Freeform (tt1578873)
																'co0058596', # Sesame Workshop (tt0063951)
																'co0001860', # United Paramount Network (UPN) (tt0088631)
																'co0087695', # Southern Star Entertainment (tt0456029)
															],
														},
														Media.Movie	: {
															'exclude' : [
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyStudio]}, # tt15352516
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]}, # tt0085334, tt0308443

																'co0036989', # Pierre Grise Productions (tt0113273)

																'co0127153', # Animax ()
																'co0964339', # Animax ()
																'co0127153', # Animax ()
																'co0132285', # Aniplex ()
																'co0035005', # AT-X ()
																'co0453359', # Anime Ltd ()
																'co0190623', # TV Setouchi Broadcasting (TSC) ()
																'co0039940', # FUNimation Entertainment ()
																'co0062107', # Toei Animation (tt0112513)
																'co0028689', # Manga Entertainment (tt0090248, tt0210234, tt0403703)
																'co0006858', # Manga Entertainment

																'co0031085', # Argentina Video Home (tt0360486)
																'co0152990', # Roadshow Entertainment (tt3104988, tt0109686)
																'co0236298', # Roadshow Entertainment (tt4116284)
																'co0370614', # Tanweer Alliances (tt0451279)
																'co0051618', # Entertainment One (tt9071322, tt1798684)
																'co0007127', # New Regency Productions (tt15083184)
																'co0157100', # Koch Media (tt0357668)
																'co0021661', # Universum Film (UFA) (tt0283139)
																'co0033472', # Morgan Creek Entertainment (tt0844029)
																'co0118514', # Monarch Home Video (tt0207585)
																'co0200212', # ACME (tt7424200)
																'co0068880', # Bridge Entertainment Group (tt0095368)
																'co0227523', # Well Go USA Entertainment (tt10627720)
																'co0482817', # Sunrise (tt0322645, tt0260191)
															],
														},
													},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0211390', 'co0444611', 'co0530659', 'co0124378', 'co0962875', 'co1020840', 'co0491815', 'co0333438', 'co0250141', 'co1012356', 'co0676555', 'co0344625', 'co0919362', 'co0806729', 'co0679000', 'co0505996'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyBravo : {
					# Show (270): Level-3. Difficult to distiguish between NBC (and other sister channels) originals, and other non-originals from smaller studios/networks.
					# Movie (164): Level-3. Difficult to distiguish between general Universal films.
					# Do not exclude Netflix, Peacock, Discovery, Hulu (Japan), NBC, Fubo, Hayu, E4, Sky, TLC, ITVBe/ITV, 7Bravo, Seven Network, Freevee, Lifetime, NOW/WOW.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'allow' : [
																# Amazon Freevee
																'co0796766',
															],
															'disallow' : [
																# 7Bravo
																# Too many non-originals.
																# And it seems that all Bravo Originals have another Bravo comapny listed under them.
																'co0979519', # tt3781836, tt1933854, tt3444938
															],
														},
														Media.Show : {
															'exclude' : [
																# Although USA is a sister channel, there are too many USA Originals if we do not exclude this here.
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # tt1064899, tt4209256. Excludes tt7945720 (on Wikpedia a Bravo Original, on IMDb poister a USA Original.)

																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # tt1578873
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # tt5834204
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # tt0098844
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # tt1358522
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]}, # tt0072562
																{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]}, # tt1632701
																{MetaCompany.CompanyStarz			: [MetaProvider.CompanyNetwork]}, # tt1833285

																'co0005035', # Warner Bros. Television (tt0200276)
																'co0118334', # BBC America (tt7016936)
																'co0508924', # Paramount Channel (tt2294189)
																'co0820851', # SPI International (tt1612716)
																'co0028766', # TF1 (tt0167565, tt6483836)
																'co0381716', # MTVA (tt2303077)
																'co0109042', # Xenon Pictures ()
																'co0053559', # Paramount Television (tt0318390)
																'co0066107', # Paramount Network Television (tt0324865)
																'co0037052', # American Broadcasting Company (ABC) (tt1826805)
																'co0070627', # CBS
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHistory		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyStudio]},

																'co0150452', # The Weinstein Company (tt0375920)
																'co0195144', # Passion River Films (tt1781069)

																'co0037052', # American Broadcasting Company (ABC)
																'co0070627', # CBS
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0076928', 'co0289501', 'co0208168'],
					MetaProvider.CompanyNetwork		: ['co0055388', 'co0979519', 'co0044418', 'co0093310', 'co0051348', 'co0913432', 'co0544037', 'co0321399', 'co0871340', 'co0073234', 'co1005022', 'co0089713'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyBritbox : {
					# Show (100): Level-2
					# Movie (31): Level-2
					# Near impossible to distiguish between BritBox Originals, and (other) originals from BBC, ITV, CH4, CH5.
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # Not for tt9204128, tt15565872
																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # Not for tt0384766, tt15565872
																#{MetaCompany.CompanyMgm				: [MetaProvider.CompanyNetwork]}, # Not for tt15565872
															],
														},
														Media.Movie : {
															'exclude' : [
															],
														},
													},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0685539', 'co0859609', 'co0957541', 'co1063503', 'co1058884'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyCartoonnet : {
					# Show (626): Level-4
					# Movie (109): Level-3
					# Difficult to filter between Cartoon Network, Adult Swim, Boomerang, and other Warner companies.
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]}, # tt0388629
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # tt0096697
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # tt0096657
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]}, # tt0086815
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyStudio]}, # tt2325846

																'co0127153', # Animax (tt9335498)
																'co0964339', # Animax ()
																'co0127153', # Animax ()
																'co0132285', # Aniplex (tt2250192)
																'co0035005', # AT-X (tt0409591)
																'co0453359', # Anime Ltd (tt0213338)
																'co0190623', # TV Setouchi Broadcasting (TSC) (tt1214085)
																'co0039940', # FUNimation Entertainment (tt4644488)
																'co0045850', # Canadian Broadcasting Corporation (CBC) (tt1094229, tt0491603)
																'co0571670', # Freeform (tt1578873)
																'co0058596', # Sesame Workshop (tt0063951)
																'co0001860', # United Paramount Network (UPN) (tt0088631)
																'co0087695', # Southern Star Entertainment (tt0456029)
															],
														},
														Media.Movie	: {
															'exclude' : [
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyStudio]}, # tt15352516
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]}, # tt0085334, tt0308443

																'co0127153', # Animax ()
																'co0964339', # Animax ()
																'co0127153', # Animax ()
																'co0132285', # Aniplex ()
																'co0035005', # AT-X ()
																'co0453359', # Anime Ltd ()
																'co0190623', # TV Setouchi Broadcasting (TSC) ()
																'co0039940', # FUNimation Entertainment ()
																'co0062107', # Toei Animation (tt0112513)
																'co0028689', # Manga Entertainment (tt0090248, tt0210234, tt0403703)
																'co0006858', # Manga Entertainment

																'co0031085', # Argentina Video Home (tt0360486)
																'co0152990', # Roadshow Entertainment (tt3104988, tt0109686)
																'co0236298', # Roadshow Entertainment (tt4116284)
																'co0370614', # Tanweer Alliances (tt0451279)
																'co0051618', # Entertainment One (tt9071322, tt1798684)
																'co0007127', # New Regency Productions (tt15083184)
																'co0157100', # Koch Media (tt0357668)
																'co0021661', # Universum Film (UFA) (tt0283139)
																'co0033472', # Morgan Creek Entertainment (tt0844029)
																'co0118514', # Monarch Home Video (tt0207585)
																'co0200212', # ACME (tt7424200)
																'co0068880', # Bridge Entertainment Group (tt0095368)
																'co0227523', # Well Go USA Entertainment (tt10627720)
																'co0482817', # Sunrise (tt0322645, tt0260191)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0238110', 'co1060195', 'co0674218', 'co0340724', 'co0844092', 'co0764593', 'co0593002', 'co0655772', 'co0592194'],
					MetaProvider.CompanyNetwork		: ['co0005780', 'co1006606', 'co0177449', 'co0445677', 'co1014644', 'co1019493', 'co0967426', 'co1015360', 'co1001745', 'co0967683', 'co0873854', 'co1010748', 'co0323359', 'co0188542', 'co1065573', 'co1006909', 'co0970248', 'co0323319', 'co1008286', 'co0252029', 'co1064907', 'co1039856', 'co1025810', 'co1065574', 'co1060525', 'co1039942', 'co1035369', 'co1030543', 'co0990387', 'co0979463', 'co1059342', 'co1057333', 'co1049124', 'co1048006', 'co1045413', 'co1030544', 'co0868070', 'co0727598'],
					MetaProvider.CompanyVendor		: ['co1048340', 'co1048303', 'co0919200', 'co0642967', 'co0087030'],
				},
				MetaCompany.CompanyCbc : {
					# Show (998): Level-3 to Level-4
					# Movie (1089): Level-3 to Level-4
					# Shares content and co-productions with a lot of US channels.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																'co0732227', 'co0256692', # CBC Kids
																'co0526683', 'co0004543', # CBC News
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt5421602, tt3526078, tt1094229, tt2874692, tt5912064, tt1091909, tt1034007, tt6143796, tt15764684, tt0758790
																#{MetaCompany.CompanyItv				: [MetaProvider.CompanyNetwork]}, # Not for tt3526078, tt6998202, tt0085017
																#{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]}, # Not for tt3526078
																#{MetaCompany.CompanyHulu				: [MetaProvider.CompanyNetwork]}, # Not for tt3526078, tt1091909, tt10193046, tt10267798
																#{MetaCompany.CompanyFox				: [MetaProvider.CompanyNetwork]}, # Not for tt3526078, tt9083140
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # Not for tt0758790, tt1091909, tt1094229, tt5912064, tt1297754
																#{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # Not for tt1094229, tt5912064, tt4919930, tt1699440
																#{MetaCompany.CompanyTubi				: [MetaProvider.CompanyNetwork]}, # Not for tt1094229
																#{MetaCompany.CompanyChannel4			: [MetaProvider.CompanyNetwork]}, # Not for tt1672189, tt0088727, tt1453159, tt1149608
																#{MetaCompany.CompanyChannel5			: [MetaProvider.CompanyNetwork]}, # Not for tt2874692
																#{MetaCompany.CompanyAcorn			: [MetaProvider.CompanyNetwork]}, # Not for tt1091909
																#{MetaCompany.CompanyFox				: [MetaProvider.CompanyNetwork]}, # Not for tt1495950
																#{MetaCompany.CompanyYoutube			: [MetaProvider.CompanyNetwork]}, # Not for tt1495950
																#{MetaCompany.CompanySky				: [MetaProvider.CompanyNetwork]}, # Not for tt7332358, tt8593252, tt1453159, tt15221950
																#{MetaCompany.CompanyCw				: [MetaProvider.CompanyNetwork]}, # Not for tt6987476, tt8593252, tt11187454, tt15310816, tt29780951
																#{MetaCompany.CompanyCineflix			: [MetaProvider.CompanyNetwork]}, # Not for tt8593252
																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # Not for tt0156200, tt1672189, tt0758790, tt1149608, tt0085017, tt15221950
																#{MetaCompany.CompanyStarz			: [MetaProvider.CompanyNetwork]}, # Not for tt1672189, tt1453159
																#{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # Not for tt15437862, tt13250034
																#{MetaCompany.CompanyShowtime			: [MetaProvider.CompanyNetwork]}, # Not for tt0758790
																#{MetaCompany.CompanyTnt				: [MetaProvider.CompanyNetwork]}, # Not for tt0758790
																#{MetaCompany.CompanyBbc				: [MetaProvider.CompanyNetwork]}, # Not for tt0485301, tt0758790, tt7660970, tt1149608, tt10267798
																#{MetaCompany.CompanyCrave			: [MetaProvider.CompanyNetwork]}, # Not for tt1453159
																#{MetaCompany.CompanyAmc				: [MetaProvider.CompanyNetwork]}, # Not for tt7660970
																#{MetaCompany.CompanySyfy				: [MetaProvider.CompanyNetwork]}, # Not for tt3696720, tt0103504
																#{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]}, # Not for tt0085017
																#{MetaCompany.CompanyCartoonnet		: [MetaProvider.CompanyNetwork]}, # Not for tt0085017, tt16154056
																#{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # Not for tt1699440, tt10267798, tt16154056
																#{MetaCompany.CompanyRoku				: [MetaProvider.CompanyNetwork]}, # Not for tt16154056

																{MetaCompany.CompanyMgm				: [MetaProvider.CompanyNetwork]}, # tt9686194
																{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # tt15384074, tt0144701
																{MetaCompany.CompanyBritbox			: [MetaProvider.CompanyNetwork]}, # tt15210882
																{MetaCompany.CompanyPeacock			: [MetaProvider.CompanyNetwork]}, # tt11719808
																{MetaCompany.CompanyNickelodeon		: [MetaProvider.CompanyNetwork]}, # tt10146162

																#'co0118334', # BBC America. Not for tt0758790.
																#'co0234667', # BBC One (tt1475582). Not for tt0758790, tt0115335.
																#'co0234496', # BBC Two. Not for tt0090417
																#'co0399177', # BBC Three (tt0436992)
																'co0103752', # BBC Wales (tt1475582, tt0436992). Not for tt0485301 (but this is in general a BBC original).

																#'co0039462', # Public Broadcasting Service (PBS). Not for tt0088727, tt0090417, tt1699440, tt0199253, tt0115335.
																#'co0070627', # CBS. Not for tt0178145.
																'co0037052', # American Broadcasting Company (ABC) (tt0065272, tt0062595)
																'co0072315', # National Broadcasting Company (NBC) (tt2427220)
																'co0070925', # Fox Network (tt0096697)
																'co0467028', # A+E Studios (tt8270592)
																'co0023514', # Australian Film Finance Corporation (AFFC) (tt0491603)
																'co0103289', # Granada Television (tt0053494)
																'co0776051', # ViacomCBS Global Distribution Group (tt8324422)
																'co0131884', # Cinenord (tt7875794)
																'co0234956', # Screen Australia (tt15233564)
																'co0103396', # Yorkshire Television (YTV) (tt0068069)
																'co0856694', # Keshet 12 (tt23856194)
																'co0103397', # Python (Monty) Pictures (tt0063929)
																'co0353891', # BYUtv (tt11129816)
																'co0123995', # North One Television (tt4719744)
																'co0186351', # DStv (tt10163204)
																'co0415381', # Drama Republic (tt8147076)
																'co0381591', # Iris Group (tt6258718)
																'co0043801', # ShadowMachine (tt12545180)
																'co0027922', # Tezuka Productions (tt0124228)
																'co0687042', # Hulu Originals (tt27302116)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]}, # tt3170832, tt0116483, tt4263482
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]}, # tt0031381
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]}, # tt0172493
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]},

																'co0240399', # MSNBC Films (tt1152758)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0045850', 'co0004543', 'co0986283', 'co0054718', 'co0801639', 'co0809993', 'co0193428', 'co0077499'],
					MetaProvider.CompanyNetwork		: ['co0045850', 'co0737690', 'co0526683', 'co0018033', 'co0732227', 'co0407617', 'co0365169', 'co0145787', 'co0945984', 'co0006230', 'co0256692', 'co0017485', 'co0849552', 'co0684928', 'co0684927', 'co0578570', 'co0274055'],
					MetaProvider.CompanyVendor		: ['co0645943', 'co0384853', 'co0057201', 'co1066695', 'co1065113', 'co1065112', 'co1065111', 'co1065081', 'co1064971', 'co0989392', 'co0989391', 'co0921956', 'co0914225', 'co0849553', 'co0804510', 'co0727824', 'co0725740', 'co0689721', 'co0583459', 'co0579073', 'co0380822', 'co0296164', 'co0294079', 'co0044672', 'co0033534', 'co0031756', 'co0990830', 'co0922467'],
				},
				MetaCompany.CompanyCbs : {
					# Show (1862): Level-3. Impossible to filter out Paramount+ and Showtime Originals.
					# Movie (2706): Level-2
					# Many Showtime and Paramount+ originals are created by CBS Studios and/or broadcast on CBS (eg tt7440726, tt0452046).
					# CBS is producing a lot of content for other platforms, both sibling and competing channels.
					# And CBS originals appear on other platforms (eg HBO, Peacock, etc)
					MetaProvider.CompanyOriginal	: {
														# Do not exclude Netflix, Amazon, Paramount+, HBO, CTV, Comedy Central, TNT, TBS, Warner, The CW (eg tt6226232, tt0898266, tt0397442)
														Media.Show : {
															'fixed' : MetaProvider.CompanyNetwork,
															'exclude' : [
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # tt0159206. Do not add for tt6226232.

																'co0008693', # Home Box Office (HBO) (tt0159206)
																'co0007546', # Nickelodeon Network (tt0972534, tt0417299) (sibling channel)
																'co0078560', # Nickelodeon Studios (tt0105950) (sibling channel)
																'co0013582', # Teletoon (tt0318913)
																#'co0052980', # Showtime Networks (tt0773262) (sibling channel)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]}, # tt0159273
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]}, # tt5090568, tt8589698

																'co0031085', # Argentina Video Home (tt0094898)
																'co0219620', # Universal Pictures Video (tt1399103)
																#'co0024325', # Dutch FilmWorks (DFW) (). Do not add for tt1072748.
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0274041', 'co0007821', 'co0049888', 'co0817261', 'co0047306', 'co0048735', 'co0183875', 'co0090662', 'co0006057', 'co0040329', 'co0422485', 'co0249961', 'co0123634', 'co0356030', 'co0719327', 'co0810398', 'co0796824', 'co0174020', 'co0095142', 'co0839930', 'co0787164', 'co0512488', 'co0379901', 'co0119022', 'co0907180', 'co0885423', 'co0876845', 'co0857109', 'co0822007', 'co0741478', 'co0682166', 'co0635749', 'co0554468', 'co0489623', 'co0406924', 'co0405466', 'co0270636', 'co0112904', 'co0059861', 'co0026997', 'co0009808', 'co0883452', 'co0820546', 'co0635748', 'co0319948'],
					MetaProvider.CompanyNetwork		: ['co0070627', 'co0598660', 'co0453313', 'co0326888', 'co0047863', 'co0313883', 'co0877435', 'co0361334', 'co0972197', 'co0754315'],
					MetaProvider.CompanyVendor		: ['co0042311', 'co0007496', 'co0226201', 'co0274041', 'co0213710', 'co0248464', 'co0106097', 'co0094754', 'co0170466', 'co0212901', 'co0266215', 'co0776051', 'co0172646', 'co0225608', 'co0806725', 'co0244801', 'co0135308', 'co0223570', 'co0266490', 'co0457912', 'co0257036', 'co0445889', 'co0405556', 'co0176590', 'co0794271', 'co0244996', 'co0064922', 'co0361085', 'co0276665', 'co0399026', 'co0030685', 'co1047418', 'co0878295', 'co0124383', 'co0304538', 'co0214398', 'co0791015', 'co0616372', 'co0101612', 'co0877389', 'co0453962', 'co0130300', 'co1032498', 'co0680153', 'co0176456', 'co0147772', 'co0905313', 'co0842403', 'co0700002', 'co0670562', 'co0599875', 'co0587108', 'co0524636', 'co0121770', 'co0032142', 'co0007214', 'co1072706', 'co1067273', 'co1038688', 'co1034107', 'co0992782', 'co0940354', 'co0939093', 'co0840165', 'co0805424', 'co0795987', 'co0761328', 'co0699401', 'co0698066', 'co0679175', 'co0672682', 'co0634761', 'co0622518', 'co0528740', 'co0493419', 'co0489870', 'co0481698', 'co0481487', 'co0479557', 'co0434383', 'co0400863', 'co0309278', 'co0306937', 'co0282920', 'co0276655', 'co0232339', 'co0216642', 'co0181494', 'co0172946', 'co0116822', 'co0093670', 'co0079206', 'co0024107', 'co0017523', 'co1074129', 'co1042083', 'co0953815', 'co0927303', 'co0870263', 'co0868761', 'co0865737', 'co0856617', 'co0855511', 'co0803988', 'co0713727', 'co0710679', 'co0643897', 'co0638970', 'co0635748', 'co0635516', 'co0396072', 'co0276671', 'co0276644', 'co0220929', 'co0214620', 'co0095978'],
				},
				MetaCompany.CompanyChannel4 : {
					# Show (2435): Level-3. Too many co-productions, and content from other networks (and vice versa), to accurately filter this.
					# Movie (2611): Level-3
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'allow' : [
																'co0381648', # Hulu Japan (tt2384811)
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt2085059, tt6257970, tt0487831, tt0377260, tt2384811, tt0280330.
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # tt4374208. Not for tt3922704.
																#{MetaCompany.CompanyBbc				: [MetaProvider.CompanyNetwork]}, # Not for tt0112004, tt1844923, tt3706628
																#{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # Not for tt0112004, tt0487831
																#{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]}, # Not for tt0387764, tt0487831, tt0280330
																#{MetaCompany.CompanyAubc				: [MetaProvider.CompanyNetwork]}, # Not for tt0387764, tt3330720, tt4122068, tt0377260
																#{MetaCompany.CompanyAmc				: [MetaProvider.CompanyNetwork]}, # Not for tt4122068
																#{MetaCompany.CompanyCinemax			: [MetaProvider.CompanyNetwork]}, # Not for tt2085059
																#{MetaCompany.CompanySky				: [MetaProvider.CompanyNetwork]}, # Not for tt2085059
																#{MetaCompany.CompanyPeacock			: [MetaProvider.CompanyNetwork]}, # Not for tt10846104
																#{MetaCompany.CompanyItv				: [MetaProvider.CompanyNetwork]}, # Not for tt0377260, tt3706628
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # tt3228904. Not for tt3922704.

																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # tt0460681, tt0141842. Not for tt0487831, tt1844923, tt11076876, tt1220617.
																{MetaCompany.CompanyCw				: [MetaProvider.CompanyNetwork]}, # tt2661044, tt0368530, tt3566726
																{MetaCompany.CompanyHulu				: [MetaProvider.CompanyNetwork]}, # tt2235759
																{MetaCompany.CompanyParamount			: [MetaProvider.CompanyNetwork]}, # tt5853176
																{MetaCompany.CompanyBravo				: [MetaProvider.CompanyNetwork]}, # tt5665418
																{MetaCompany.CompanyStarz				: [MetaProvider.CompanyNetwork]}, # tt3006802
																{MetaCompany.CompanyShowtime			: [MetaProvider.CompanyNetwork]}, # tt2137109
																{MetaCompany.CompanyTnt				: [MetaProvider.CompanyNetwork]}, # tt1600199
																{MetaCompany.CompanyTbs				: [MetaProvider.CompanyNetwork]}, # tt0086798
																{MetaCompany.CompanyAdultswim			: [MetaProvider.CompanyNetwork]}, # tt12074628

																#'co0039462', # Public Broadcasting Service (PBS) # Not for tt3706628, tt0094576
																#'co0014456', # ARTE # Not for tt3706628

																#'co0754095', # HBO Max (tt0460681, tt0141842). Still excludes tt1220617 (Which is a E4 Original). Not for tt11076876.
																'co0005035', # Warner Bros. Television (tt0460681)
																'co0008693', # Home Box Office (HBO) (tt0141842)

																'co0072315', # National Broadcasting Company (NBC)
																'co0037052', # American Broadcasting Company (ABC) # tt0411008
																'co0070627', # CBS

																'co0056447', # 20th Century Fox Television (tt1561755)
																'co0154766', # Logo (tt1353056)
																'co0667778', # Universal Kids (tt0144701)
																'co0981669', # Discovery Toons (tt0088563)
																'co0123927', # DC Entertainment (tt7658402, tt14681924)
																'co0280047', # 20th Century Fox Home Entertainment (tt3228904)
																'co0086397', # Sony Pictures Television (tt0118480)
																'co0053559', # Paramount Television (tt0244365)
																'co0145449', # CNN International (tt0115147)
																'co0293940', # Greenlight Films (tt4771108)
																'co0272021', # Roast Beef Productions (tt21148288)
																'co0072876', # Warner Bros. Animation (tt0111970)
																'co0106768', # Marvel Productions (tt0108895)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},

																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},

																'co0072315', # National Broadcasting Company (NBC)
																'co0037052', # American Broadcasting Company (ABC)
																'co0070627', # CBS
																'co0170466', # CBS Paramount Domestic Television
																'co0007821', # CBS Studios
																'co0159275', # Fox Television Animation
																'co0056447', # 20th Century Fox Television
																'co0741733', # Searchlight Television
																'co0216537', # FX Productions
																'co0123927', # DC Entertainment
																'co0578069', # Marvel Entertainment Group
																'co0047120', # Marvel Entertainment
																'co0051941', # Marvel Studios
																'co0028689', # Manga Entertainment
																'co0045140', # Showcase Television
																'co0054762', # Alliance Atlantis Communications
																'co0142434', # Alloy Entertainment
																'co0053559', # Paramount Television
																'co0129164', # DreamWorks Animation
																'co0005051', # Turner Broadcasting System (TBS)
																'co0067205', # Touchstone Television
																'co0024325', # Dutch FilmWorks (DFW)

																'co0232782', # Cinéart (tt2278871)
																'co0150452', # The Weinstein Company (tt1045658)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0167631', 'co0290683', 'co0103532', 'co0002948', 'co0000063', 'co0103747', 'co0019406', 'co0940546', 'co0977444', 'co0674378', 'co0993801', 'co0391865'],
					MetaProvider.CompanyNetwork		: ['co0103528', 'co0706824', 'co0167631', 'co0106185', 'co0651210', 'co0163162', 'co0159436', 'co0007824', 'co0523488', 'co0361173', 'co0557933', 'co0691823'],
					MetaProvider.CompanyVendor		: ['co0103528', 'co0044785', 'co0235537', 'co0167590', 'co0106289', 'co0108028', 'co0200324', 'co0792816', 'co0412137'],
				},
				MetaCompany.CompanyChannel5 : {
					# Show (966): Level-3
					# Movie (740): Level-2
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# Too many unrelated titles.
																# And more geared towards Paramount.
																'co0533814', # Spike UK (tt3337194, tt1885102, tt1863526)
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt12004280
																#{MetaCompany.CompanyAcorn			: [MetaProvider.CompanyNetwork]}, # Not for tt13430420
																#{MetaCompany.CompanyCrave			: [MetaProvider.CompanyNetwork]}, # Not for tt13406036
																#{MetaCompany.CompanyBbc				: [MetaProvider.CompanyNetwork]}, # Not for tt10590066
																#{MetaCompany.CompanyItv				: [MetaProvider.CompanyNetwork]}, # Not for tt1905943
																#{MetaCompany.CompanyCbs				: [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork]}, # Not for tt31647174

																{MetaCompany.CompanyNickelodeon		: [MetaProvider.CompanyNetwork]}, # tt3121722, tt0426769 (sister channel)
																{MetaCompany.CompanyAmc				: [MetaProvider.CompanyNetwork]}, # tt0903747, tt1520211
																{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # tt0421030
																{MetaCompany.CompanySyfy				: [MetaProvider.CompanyNetwork]}, # tt4878326, tt2758950
																{MetaCompany.CompanyHistory			: [MetaProvider.CompanyNetwork]}, # tt1985443
																{MetaCompany.CompanyTnt				: [MetaProvider.CompanyNetwork]}, # tt1723760
																{MetaCompany.CompanyUsa				: [MetaProvider.CompanyNetwork]}, # tt8289480, tt0112112
																{MetaCompany.CompanyAe				: [MetaProvider.CompanyNetwork]}, # tt1103968

																# Sister channels
																'co0093767', # Nicktoons Productions (tt0206512)
																'co0070627', # CBS (tt9795876, tt1553656, tt14218674). Probably a bad idea, but CH5 Originals do not seem to be on CBS.
																'co0170466', # CBS Paramount Domestic Television (tt0112178)
																'co0183875', # CBS Paramount Network Television (tt0247082)
																'co0274041', # CBS Television Studios (tt9795876)
																#'co0007821', # CBS Studios (tt14218674). Not for tt31647174
																'co0052980', # Showtime Networks (tt0904208)
																'co0023307', # Music Television (MTV) (tt1051220)

																'co0209226', # ABC Signature (tt0452046, tt4396862, tt0413573)
																'co0072315', # National Broadcasting Company (NBC) (tt0203259)
																'co0129175', # NBC Universal Television (tt0412142)
																'co0056447', # 20th Century Fox Television (tt0455275, tt1844624)
																'co0216537', # FX Productions (tt1124373)
																'co0005035', # Warner Bros. Television (tt1196946, tt1839578)
																'co0077535', # The WB Television Network (tt0158552)
																'co0071026', # MGM Television (tt1567432)
																'co0071430', # Motion Picture Corporation of America (MPCA) (tt2874692)
																'co0881747', # Harp to the Party Productions (tt14218674)
																'co0777583', # Leonine Studios (tt8769360)
																'co0080248', # Mattel (tt0126158)
																'co0022105', # Disney Channel (tt0172049)
																'co0030553', # Kinderkanal (KiKA) (tt0200369)
																'co0129164', # DreamWorks Animation (tt3508674)
																'co0039254', # Women's Entertainment Television (WEtv) (tt0462085)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},

																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},

																'co0072315', # National Broadcasting Company (NBC)
																'co0037052', # American Broadcasting Company (ABC)
																'co0070627', # CBS
																'co0159275', # Fox Television Animation
																'co0056447', # 20th Century Fox Television
																'co0741733', # Searchlight Television
																'co0216537', # FX Productions
																'co0123927', # DC Entertainment
																'co0578069', # Marvel Entertainment Group
																'co0047120', # Marvel Entertainment
																'co0051941', # Marvel Studios
																'co0028689', # Manga Entertainment
																'co0045140', # Showcase Television
																'co0054762', # Alliance Atlantis Communications
																'co0142434', # Alloy Entertainment
																'co0129164', # DreamWorks Animation
																'co0005051', # Turner Broadcasting System (TBS)
																'co0067205', # Touchstone Television
																'co0024325', # Dutch FilmWorks (DFW)
																'co0150452', # The Weinstein Company
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0572210', 'co0419882', 'co0445528'],
					MetaProvider.CompanyNetwork		: ['co0003500', 'co0616900', 'co0174820', 'co0533814', 'co0360612', 'co0773190', 'co0798902', 'co0836811', 'co0340961', 'co0187281', 'co0901456', 'co0187155', 'co0187155', 'co0594710', 'co0237619', 'co1040344', 'co0358510', 'co0106315', 'co1047381', 'co0797466', 'co0732834'],
					MetaProvider.CompanyVendor		: ['co0106195', 'co0242515'],
				},
				MetaCompany.CompanyCineflix : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0064070', 'co0376305', 'co0317170', 'co0658624', 'co0467141', 'co0344403', 'co0765221', 'co0691772', 'co0647273', 'co0645818', 'co0522055'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0182284', 'co0510368', 'co0775253'],
				},
				MetaCompany.CompanyCinemax : {
					# Show (39 of 33+): Level-4.
					# Movie (636 of 5+): Level-2. Not really any Cinemax original films.
					# https://en.wikipedia.org/wiki/Category:Cinemax_original_programming
					# https://en.wikipedia.org/wiki/Category:Cinemax_original_films
					MetaProvider.CompanyOriginal	: {
														Media.Show	: {
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # tt2085059. Do not add for tt5743796.
																{MetaCompany.CompanyStarz			: [MetaProvider.CompanyNetwork]}, # tt0448190
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # tt1279972
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # tt2295953

																'co0005861', # HBO Films (tt0995832)

																'co0508924', # Paramount Channel (tt2294189)
																'co0591004', # Paramount Channel (tt1199099)
																'co0001860', # United Paramount Network (UPN) (tt0227972)

																'co0235537', # Channel 4 DVD (tt2085059)
																'co0288368', # 13th Street (tt0306414)
																'co0716013', # SKY Studios (tt7661390)
																'co0533814', # Spike (tt1885102)
																'co0072315', # National Broadcasting Company (NBC) (tt0081933)
																'co0037052', # American Broadcasting Company (ABC) (tt0092402, tt1760943)
																'co0710530', # CStar (tt1167345)
																'co0024325', # Dutch FilmWorks (DFW) (tt2006374)
																'co0054018', # American Cinema Group (tt1459243)
																'co0014456', # ARTE (tt1831575)
																'co0178817', # AMC Pictures (tt1392307)
																'co0450254', # Multicom Entertainment Group (tt0143044)
																'co0795545', # CCXTV (tt0244901)
																'co0024077', # ARD (tt1504261)
																'co0630596', # BluTV (tt1941928)
																#'co0086474', # Western International Communications Ltd. (tt0085085). Is a Cinemax Original.
																'co0507878', # Disney Channel India (tt6457306)
															],
														},
														Media.Movie	: {
															# These are very inaccurate.
															# Cinemax probably does not have any film Originals, except maybe the occasional Cinemax After Dark (Eroctica).
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # tt0190641

																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]}, # tt0099685
																{MetaCompany.CompanyTubi			: [MetaProvider.CompanyNetwork]}, # tt0756683
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # tt0090190

																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]}, # tt1727824
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]}, # tt0052618

																'co0179392', # Lionsgate UK (tt19637052, tt10366206, tt1320253)
																'co0800011', # Leonine Distribution (tt7160372)
																'co0719901', # Mubi (tt22041854)
																'co0427244', # Vertical Entertainment (tt12519802)
																'co0015762', # IFC Films (tt1872818)
																'co0024325', # Dutch FilmWorks (DFW) (tt0092263, tt1912398, tt0837106)
																'co0820851', # SPI International (tt2622036, tt1612603) # These might be Cinemax After Dark Originals.
																'co0051618', # Entertainment One (tt1640459)
																'co0072847', # Splendid Film (tt1844770)
																'co0232782', # Cinéart (tt1550312)
																'co0151501', # Capelight Pictures (tt1248971)
																'co0178485', # REX Film (tt0471930)
																'co0208383', # Senator Home Entertainment (tt1613062)
																'co0291951', # SF Home Entertainment (tt0950739)
																'co0019532', # Kinowelt Home Entertainment (tt1137436)
																'co0145667', # Icon Film Distribution (tt1198101)
																'co0113335', # A-Film Home Entertainment (tt1846526)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0027725', 'co0005144'],
					MetaProvider.CompanyNetwork		: ['co0042496', 'co0268340', 'co0861398', 'co0123742', 'co0368145', 'co0872473', 'co0778313', 'co0913502', 'co0790278', 'co0625219', 'co0887358', 'co0802222', 'co0011668'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyColumbia : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0050868', 'co0041442', 'co0074221', 'co0103416', 'co0041248', 'co0239725', 'co0032932', 'co0985783', 'co0072216', 'co0624442', 'co0147951', 'co0136288', 'co0001581', 'co0446085', 'co0198276', 'co0142305', 'co0113915', 'co0113868', 'co0075055', 'co0063529', 'co0562672', 'co0562672', 'co0324275', 'co0245365', 'co0142304', 'co0110462', 'co0093452', 'co0008439', 'co0772149', 'co0206582'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0050868', 'co0108852', 'co0001850', 'co0130303', 'co0057923', 'co0282638', 'co0215212', 'co0221123', 'co0128198', 'co0070977', 'co0127120', 'co0003581', 'co0219440', 'co0218288', 'co0214905', 'co0009297', 'co0014351', 'co0189864', 'co0098048', 'co0077851', 'co0213457', 'co0057443', 'co0106070', 'co0110090', 'co0003949', 'co0045926', 'co0108034', 'co0438107', 'co0372744', 'co0005726', 'co0218192', 'co0118308', 'co0095798', 'co0060005', 'co0807814', 'co0075764', 'co0628925', 'co0053539', 'co0768357', 'co0117455', 'co0031545', 'co0774471', 'co0252452', 'co0302174', 'co0170439', 'co0358260', 'co0231770', 'co0006448', 'co0629458', 'co0182605', 'co0176140', 'co0092241', 'co0089682', 'co0237854', 'co0047778', 'co0613324', 'co0218290', 'co0215270', 'co0215257', 'co0035705', 'co0805428', 'co0159180', 'co0108003', 'co0728184', 'co0120631', 'co0139447', 'co0877032', 'co0351835', 'co0539852', 'co0055524', 'co0359121', 'co0225408', 'co0135317', 'co0094232', 'co0287692', 'co0768425', 'co0638112', 'co0114725', 'co0076384', 'co0257569', 'co0037988', 'co0152638', 'co0232238', 'co0015669', 'co0884352', 'co0108012', 'co0051419', 'co0720168', 'co0651764', 'co0176177', 'co0032747', 'co0393411', 'co0135318', 'co0942170', 'co0751613', 'co0039725', 'co0115734', 'co0115429', 'co0045347', 'co0113976', 'co0117466', 'co0815627', 'co0139446', 'co1013825', 'co0942169', 'co0488192', 'co0382315', 'co0163983', 'co0092245', 'co0400389', 'co0211796', 'co0185616', 'co0897405', 'co0325928', 'co0215095', 'co0178866', 'co0162942', 'co0162942', 'co0241443', 'co0057970', 'co0025186', 'co0373110', 'co0700140', 'co0991324', 'co0379792', 'co0954396', 'co0081792', 'co0754056', 'co0982368', 'co0537026', 'co0382360', 'co0008806', 'co1020466', 'co0751516', 'co0379620', 'co1002119', 'co0825783', 'co0778447', 'co0730604', 'co0628924', 'co0371171', 'co0837462', 'co0796316', 'co0728653', 'co0717323', 'co0628032', 'co0613216', 'co0428560', 'co0250208', 'co0185878', 'co0961122', 'co0937939', 'co0826726', 'co0802980', 'co0723390', 'co0229304', 'co0213673', 'co0208202', 'co0118302', 'co0118300', 'co1042290', 'co1041459', 'co1021830', 'co0960788', 'co0960786', 'co0937938', 'co0930442', 'co0919176', 'co0919014', 'co0890192', 'co0793829', 'co0753593', 'co0625795', 'co0455564', 'co0354514', 'co0303509', 'co0301411', 'co0300278', 'co0232073', 'co0200952', 'co0120629', 'co0075055', 'co0073559', 'co0054490', 'co0053661', 'co1061942', 'co1044199', 'co1037590', 'co0996230', 'co0981289', 'co0943399', 'co0924447', 'co0919175', 'co0919019', 'co0919016', 'co0919015', 'co0919013', 'co0913591', 'co0853923', 'co0840651', 'co0835295', 'co0833779', 'co0802979', 'co0797841', 'co0793712', 'co0787177', 'co0544343', 'co0543768', 'co0517926', 'co0492268', 'co0382011', 'co0296648', 'co0289892', 'co0274904', 'co0210948', 'co0040618', 'co0011801', 'co0960785', 'co0960784', 'co0929000', 'co0806647', 'co0793828', 'co0793828', 'co0771804', 'co0770848', 'co0692171', 'co0660474', 'co0659417', 'co0455563', 'co0453812', 'co0337735', 'co0221049', 'co0219416', 'co0215137', 'co0213635', 'co0209928', 'co0206425', 'co0201367', 'co0137852', 'co0004899'],
				},
				MetaCompany.CompanyComedycen : {
					# Show (527): Level-3, maybe close to Level-4
					# Movie (183): Level-3
					# Very difficult to filter, since CC has few originals, but carries a ton of content from many other channels.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'allow' : [
																MetaCompany.CompanyFreevee, # tt0094517
															],

															'disallow' : [
																# Exclude non-US/UK/CA Comedy Central channels, since they mostly have content from other networks.
																# Probably all Comedy Central Originals should be listed on the US/UK/CA channels.
																'co0903459', 'co0886579', 'co0877841', 'co0913861', 'co0947125', 'co0810091', 'co1010895', 'co0903461', 'co0903460', 'co1073642',
																'co0409231', 'co0360149', 'co0226227', 'co0984705', 'co0393953', 'co0476675',
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyCbs				: [MetaProvider.CompanyNetwork]}, # Not for tt0115147, tt0121955, tt0370194, tt0353049, tt1430587, tt0318959, tt0386180
																#{MetaCompany.CompanyChannel4			: [MetaProvider.CompanyNetwork]}, # Not for tt0115147, tt0121955
																#{MetaCompany.CompanyMtv				: [MetaProvider.CompanyNetwork]}, # Not for tt0121955, tt0318959, tt0386180
																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # Not for tt0121955, tt0370194, tt0353049, tt9272514, tt1981558
																#{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # Not for tt0121955, tt1621748
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt0121955, tt0094517, tt0353049
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # Not for tt0094517
																#{MetaCompany.CompanyNickelodeon		: [MetaProvider.CompanyNetwork]}, # Not for tt0121955
																#{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # Not for tt0121955, tt0386180
																#{MetaCompany.CompanyPeacock			: [MetaProvider.CompanyNetwork]}, # Not for tt0094517
																#{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # Not for tt0121955, tt0094517, tt0370194, tt0821375, tt0318959, tt1621748, tt1981558
																#{MetaCompany.CompanyWarner			: [MetaProvider.CompanyNetwork]}, # Not for tt0121955
																#{MetaCompany.CompanySyfy				: [MetaProvider.CompanyNetwork]}, # Not for tt0094517
																#{MetaCompany.CompanyFox				: [MetaProvider.CompanyNetwork]}, # Not for tt0458254, tt2022713
																#{MetaCompany.CompanyRoku				: [MetaProvider.CompanyNetwork]}, # Not for tt0370194
																#{MetaCompany.CompanyMgm				: [MetaProvider.CompanyNetwork]}, # Not for tt0370194, tt0353049
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # Not for tt2022713
																#{MetaCompany.CompanyHulu				: [MetaProvider.CompanyNetwork]}, # Not for tt5648202

																{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # tt6226232, tt0460649. Not for tt11457996
																{MetaCompany.CompanyUsa				: [MetaProvider.CompanyNetwork]}, # tt1632701, tt1442437, tt0491738
																{MetaCompany.CompanyTnt				: [MetaProvider.CompanyNetwork]}, # tt0108778, tt2861424
																{MetaCompany.CompanyTbs				: [MetaProvider.CompanyNetwork]}, # tt1583607, tt1637574, tt1942919
																{MetaCompany.CompanyFx				: [MetaProvider.CompanyNetwork]}, # tt0472954, tt0096697
																{MetaCompany.CompanyShowtime			: [MetaProvider.CompanyNetwork]}, # tt0904208
																{MetaCompany.CompanyAdultswim			: [MetaProvider.CompanyNetwork]}, # tt10826054
																{MetaCompany.CompanyCw				: [MetaProvider.CompanyNetwork]}, # tt0284722, tt0112056 (sister channel)

																#'co0037052', # American Broadcasting Company (ABC). Not for tt0108897.
																#'co0715422', # Quibi. Not for tt0370194.

																'co0048735', # CBS Productions (tt0247144) (sister channel)
																'co0072315', # National Broadcasting Company (NBC) (tt0386676, tt0491738, tt2467372)
																'co0385962', # Disney Media Distribution (DMD) (tt5691552)
																'co0385962', # Disney Media Distribution (DMD) (tt5691552)
																'co0213225', # Disney-ABC Domestic Television (tt1819509, tt1587678)
																'co0209226', # ABC Signature (tt7845644, tt5592146)
																'co0106185', # E4 (tt0280330)
																'co0043801', # ShadowMachine (tt3398228)
																'co0006166', # Imagine Television (tt0367279)
																'co0382999', # ITV Studios Global Entertainment (tt3526078)
																'co0015194', # ITV - Independent Television (tt0115369)
																'co0043107', # British Broadcasting Corporation (BBC) (tt0290978)
																'co0118334', # BBC America (tt0290988)
																'co0306346', # HBO Home Entertainment (tt0387199)
																'co0077623', # Home Box Office Home Video (HBO) (tt0866442)
																'co0057973', # Blackie and Blondie Productions (tt1442464)
																'co0067205', # Touchstone Television (tt0101120)
																'co0135632', # Talkback Thames (tt0487831)
																'co0115168', # Objective Productions (tt0387764)
																'co0020016', # Carsey-Werner Distribution (tt0165598)
																'co0071857', # Garfield Grove Productions (tt1235547)
																#'co0760246', # Mattel Television (tt10826054). Not for tt0105950.
																'co0275279', # Kapital Entertainment (tt4384086)
																'co0077647', # Viacom (tt0174378)
																'co0691491', # 3dot productions (tt7808566)
																'co0004981', # Chuck Lorre Productions (tt11116204)
																'co0072133', # Tokyo Broadcasting System (TBS) (tt0375466)
																'co0268224', # Pointy Bird Productions (tt0802146)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTbs			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},

																'co0024325', # Dutch FilmWorks (DFW) (tt1306980)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0116486', 'co0239378'],
					MetaProvider.CompanyNetwork		: ['co0029768', 'co0076380', 'co0226227', 'co0003869', 'co0811133', 'co0903459', 'co0049249', 'co0409231', 'co0360149', 'co0047312', 'co0886579', 'co0387083', 'co0984705', 'co0877841', 'co0131848', 'co0768658', 'co0393953', 'co0947125', 'co0913861', 'co0476675', 'co1073642', 'co1010895', 'co0903461', 'co0903460', 'co0810091'],
					MetaProvider.CompanyVendor		: ['co0308378', 'co0401415'],
				},
				MetaCompany.CompanyConstantin : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0002257', 'co0117695', 'co0276919', 'co0756918', 'co0401773', 'co0675006', 'co0676507', 'co0368853', 'co0942297', 'co0501831', 'co0886172', 'co0435989', 'co0975833', 'co0866740'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0002257', 'co0080484', 'co0504319', 'co0233657', 'co0179125', 'co1005885', 'co0895098', 'co0244344', 'co1053231', 'co0995200', 'co0962732', 'co0837068', 'co0883893', 'co0877579', 'co0167676', 'co0094921'],
				},
				MetaCompany.CompanyCrave : {
					# Show (48): Level-3
					# Movie (212): Level-2
					# There are not many Crave Originals and most were released under The Movie Network (TMN).
					# It seems that Crave these days receives most of its content from other networks.
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																# HBO, Showtime, Starz provide most of the content to Crave, but these are not Crave Originals.
																# And Crave probably does not shre its originals with HBO, Showtime, and Starz.
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyStarz			: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]}, # Not for tt10738442

																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # tt5171438, tt9184820
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # tt3502248
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # tt0965394
																{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]}, # tt0235137
																{MetaCompany.CompanyHistory		: [MetaProvider.CompanyNetwork]}, # tt3315386
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # tt13406036

																#{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]}, # Not for tt0456778.
																#{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # Not for tt2490030.
																#{MetaCompany.CompanySky			: [MetaProvider.CompanyNetwork]}, # Not for tt2490030.
																#{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # Not for tt4647692.

																'co0071026', # MGM Television (tt0374455)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyVendor]},

																'co0983179', # Tubi Films (tt31499750)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0243465', 'co0734142'],
					MetaProvider.CompanyNetwork		: ['co0043355', 'co0605105', 'co0667174', 'co0758813', 'co0584469'],
					MetaProvider.CompanyVendor		: ['co0611544', 'co0493530', 'co0047549'],
				},
				MetaCompany.CompanyCrunchyroll : {
					# Show (611): Level-2
					# Movie (48): Level-2
					# Has a lot of anime and partnerships with Sony, Animax, Aniplex, AXN, Funimation, Anime Ltd, etc.
					# Difficult to filter between partner content. Crunchyroll Originals are also on Netflix, HBO, etc.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'exclude' : [
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCartoonnet	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # tt12343534
																#{MetaCompany.CompanyAdultswim	: [MetaProvider.CompanyNetwork]}, # Not for tt13042440.
															],
														},
														Media.Show : {
															'exclude' : [
															],
														},
														Media.Movie : {
															'exclude' : [
																'co0072847', # Splendid Film (tt4262980)
																'co0138428', # Happinet (tt7529650)
																'co0061162', # Golden Village Pictures (tt11923304)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0251163', 'co0873834', 'co0997614'],
					MetaProvider.CompanyNetwork		: ['co0251163', 'co0931273', 'co0977033'],
					MetaProvider.CompanyVendor		: ['co0114007', 'co0316684'],
				},
				MetaCompany.CompanyCw : {
					# Show (229 of 173+): Level-4.
					# Movie (91 of 260+): Level-2. Too many titles from smaller studios. Probablby none, or very few, CW original films exist (not even a Wikipedia page).
					# https://en.wikipedia.org/wiki/Category:The_CW_original_programming
					# https://en.wikipedia.org/wiki/List_of_programs_broadcast_by_The_CW
					# The CW purchased a lot of shows from other networks which are now semi-CW Originals (AMC, Netflix, HBO, CTV, Stan, and many more).
					# Many of the titles from AMC, Sky, Hallmark, CTV, eg are now part of CW, but maybe should not always be considered CW Originals.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown	: {
															'disallow' : [
																# Do not add WTCG/WPIX/KTLA, since there are too many other titles.
																# Maybe own that might be considered a CW Original: tt0128886, tt0147746.
																'co0767441',
																'co0000647',
																'co0374263',
																'co0523775',
																'co0007077',
																'co0378383',
															],
														},
														Media.Show	: {
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Do not add for tt21064598, tt2193021.
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Do not add for tt21064598, tt2193021, tt0412253 (because it is also a Hulu Original, although listed on Wikipedia as CW Original for the later season).
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # tt0460637 (purchased show)
																#{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # tt9810248, tt21064598 (Both are purchased or co-productions).
																#{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # tt0808491 (purchased show)
																#{MetaCompany.CompanyRoku			: [MetaProvider.CompanyNetwork]}, # tt10738442. Do not add for tt26452193.

																'co0007893', # Fox Kids Network (tt0214341)
																#'co0080139', # CTV Television Network (tt21064598, tt0115083, tt1592154, tt10738442, tt30487848) (purchased shows). Do not add for tt21064598.
																#'co0032922', # Hallmark Channel (tt21043326, tt0115083) (purchased shows)
																'co0308209', # CCTV-8 (tt1592154)
																'co0605105', # Crave (tt10738442)
																'co0689402', # Bell Media Studios (tt30487848)
																'co0050436', # Sex and the City Productions (tt0159206)
																'co0076338', # CITY-TV (tt0279600). Do not add for tt0955322. Smallville is both a WB and CW original.
																'co0546496', # Sony Liv (tt7950706)
																'co0046592', # Universal Television (tt0112230)
																'co0023827', # Universal Pictures Home Entertainment (UPHE) (tt0098780)
																'co0388514', # Universal Pictures Finland (tt1866570)
																'co0186606', # Universal International Studios (tt19889996)
																'co1013700', # Universal Toons (tt0937403)
																'co0147812', # NBC Telemundo Network (tt1696969)
																'co0037052', # American Broadcasting Company (ABC) (tt0075596)
																'co0180200', # PBS Kids Sprout (tt0063951)
																#'co0004314', # Global (tt11873484). Do not add for tt1225901.
																'co0051618', # Entertainment One (tt11873484)
																'co0056447', # 20th Century Fox Television (tt0077097)
																'co0935669', # FUNimation Productions (tt0249327)
																'co0118334', # BBC America (tt0808096)
																'co0052177', # 4 Kids Entertainment (tt1409055)
																'co0039462', # Public Broadcasting Service (PBS) (tt0142055)
																'co0202446', # YouTube (tt12164342)
																'co0716013', # SKY Studios (tt7939218)
																'co0447329', # Sky Vision (tt8038720)
																'co0534118', # BBC iPlayer (tt10653784)
																'co0800011', # Leonine Distribution (tt6109562)
																#'co0045850', # Canadian Broadcasting Corporation (CBC) (tt15310816). Do not add for tt29780951 (CBS+CW co-production).
																'co0060306', # Lionsgate Films (tt15310816) (only S03 released on CW).
																'co0188462', # Lions Gate Television (tt0790820)
																'co0104833', # Children's Independent Television (CiTV) (tt1140100)
																'co0106283', # Trouble (tt0362404, tt0772137)
																'co0247505', # Citytv (tt0363307, tt1197567)
																'co0015194', # ITV - Independent Television (tt1811179)
																'co0197876', # American Forces Network (tt0270118)
																'co0395984', # AXS TV (tt0272422)
																'co0122766', # Umbrella Entertainment (tt11187454)
																'co0189627', # Qubo (tt0235132)
																'co0051111', # Australian Broadcasting Corporation (ABC) (tt7537096)
																'co0325570', # Off The Fence (tt18028428)
																'co0105874', # LivingTV (tt0437758)
																#'co0450254', # Multicom Entertainment Group (tt1411254). Is a CW original.
																#'co0108903', # Questar Entertainment (tt11427244). Probably is a CW original, since tt3052478, tt13070378, many-more, is made by the same company.
																'co0001524', # China Central Television (CCTV) (tt1832789, tt0853174)
																'co0062107', # Toei Animation (tt1783878)
															],
														},

														Media.Movie	: {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
															],
														},
													},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0174148', 'co0000647', 'co0007077', 'co1024509', 'co0481314', 'co0374263', 'co0378383', 'co0523775', 'co0786540', 'co0371051', 'co0767441', 'co1049674', 'co0664978', 'co0509842', 'co0369245'],
					MetaProvider.CompanyVendor		: ['co0593960', 'co0547811', 'co0469845', 'co0432088', 'co0221492', 'co0964315', 'co0832948', 'co0800524', 'co0793958', 'co0725543', 'co0710892', 'co0672687', 'co0652452', 'co0615111', 'co0402268', 'co0391210', 'co0357335', 'co0217572', 'co0826832', 'co0664164'],
				},
				MetaCompany.CompanyDarkhorse : {
					# Show (12): Level-5
					# Movie (33): Level-5
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
															],
														},
														Media.Movie : {
															'exclude' : [
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0020061', 'co0166969'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0978106'],
				},
				MetaCompany.CompanyDccomics : {
					# Show (79): Level-5. Near perfect out of the box.
					# Movie (95): Level-4. Most of the incorrect titles have DC as "Thank you" or "Additional material".
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
															],
														},
														Media.Movie : {
															'exclude' : [
																'co0084134', # Kemp Company (tt0264464)
																'co0159772', # Heyday Films (tt0480249)
																'co0024560', # Jerry Weintraub Productions (tt1155076)
																'co1041703', # Grabaciones y Doblajes (tt0129167)
																'co0007545', # View Askew Productions (tt0109445)
																'co0204383', # Little Sam Films (tt0862856)
																'co0040322', # Mr. Mudd (tt1967545)
																'co0093859', # Day Care Productions (tt0317303)
																'co0062559', # Madacy Entertainment (tt0313911)
																'co0044439', # BenderSpink (tt1334512)
																'co0114242', # Spring Creek Productions (tt0318155)
																'co0251858', # FilmNation Entertainment (tt2182256)
																'co0060823', # Wife 'n' Kids (tt0109288)
																'co0221271', # David Dobkin Productions (tt0486583)
																'co0063961', # Tribeca Productions (tt0455323)
																'co0198259', # Delirio Films (tt7544820)
																'co0040304', # Van Ness Films (tt0300295)
																'co0228485', # Roger Grant Productions (tt1164732)
																'co0275629', # Tony Watt (tt1470822)
																'co0001727', # Paws (tt0459653)
																'co0194219', # Metaluna Productions (tt8227356)
																'co0942059', # Ally Financial (tt21435030)
																'co0006414', # National Film Board of Canada (NFB) (tt0262367, tt0804477)
																'co0006707', # Don Mischer Productions (tt0368610)
																'co0619494', # King Bert Productions (tt6949018)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0123927', 'co0038332', 'co1064049', 'co1036036', 'co0752503', 'co0748686', 'co0584833'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0697225', 'co1058414', 'co0951237', 'co0755173', 'co0881612'],
				},
				MetaCompany.CompanyDimension : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0019626', 'co0079757'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0210118', 'co0098484'],
				},
				MetaCompany.CompanyDiscovery : {
					# Show (2555 of 328+): Level-3. Most shows from other studios seem to be exclusively on Discovery.
					# Movie (1362 of ?): Level-2. Probably no "true" Discovery original film. Although most movies from other studios seem to be exclusively  on Discovery.
					# https://en.wikipedia.org/wiki/Category:Discovery_Channel_original_programming
					# https://en.wikipedia.org/wiki/Category:Discovery%2B_original_programming
					# https://en.wikipedia.org/wiki/List_of_Discovery_Channel_original_programming
					# https://en.wikipedia.org/wiki/List_of_Discovery%2B_original_programming
					# Discovery seems to produce a lot of low-cost shows, most of them reality, docu, history, nature, day-time-TV, etc.
					# Most Discovery/HBO/Max titles appear on all three networks, so it is difficult to distinguish.
					# Although there are 2500+ titles, they seem to be enlarge Discovery (or at least sister channels) Originals.
					MetaProvider.CompanyOriginal	: {

														Media.Show	: {
															'disallow' : [
																# Too many cluttered titles with Discovery Kids and Discovery Toons.
																# Also exclude Force Channel, since it mostly is only animation, and requires many exclusions of individual companies otherwise.
																'co0981653', 'co0981669', 'co0614571', 'co0984883', 'co0092660', 'co0092660', 'co0981619', 'co0981827', 'co1010769', 'co0598558', 'co1006785', 'co1061317', 'co0275477', 'co0984881', 'co1067092', 'co1006154', 'co0788357', 'co1012797', 'co0525521', 'co0525521', 'co1012796', 'co0981825', 'co0981689', 'co0981643', 'co1070858', 'co1067096', 'co1048738', 'co1048737', 'co1048736', 'co1048735', 'co1006964', 'co1005826',
															],
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # tt5626028, tt0121955. Do not add for tt1628033, tt5618256, tt4686698 (co-production Discovery+Netflix).
																{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyStudio]}, # tt6741278, tt0182576, tt0158552. Do not add network for tt1800864, tt1628033.
																{MetaCompany.CompanyCartoonnet		: [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork]}, # tt1942683, tt0760437, tt27502465. Owned by Warner, but too many (any we already disallow Discovery Toons/Kids).

																{MetaCompany.CompanyCrunchyroll		: [MetaProvider.CompanyNetwork]}, # tt2560140, tt0388629
																{MetaCompany.CompanyFx				: [MetaProvider.CompanyNetwork]}, # tt0472954, tt0149460
																{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # tt0397306, tt1199099
																{MetaCompany.CompanyUsa				: [MetaProvider.CompanyNetwork]}, # tt1064899

																'co0106185', # E4 (tt5969074, tt9615014)
																'co0110208', # Shout! Factory (tt3398228)
																'co0171371', # PBS Kids (tt7006666, tt11992456)
																'co0001860', # United Paramount Network (UPN) (tt0103359)
																'co1013700', # Universal Toons (tt0409591)
																'co0044418', # Bravo Networks (tt1720601)
																'co0076928', # Bravo Cable (tt0437741)
																'co0120663', # American Public Television (tt11950864)
																'co0037052', # American Broadcasting Company (ABC) (tt0348894, tt0313038)
																'co0072315', # National Broadcasting Company (NBC) (tt12752438)
																'co0109033', # Ubisoft (tt14837566)
																'co0108311', # Family Home Entertainment (FHE) (tt0086719)
																'co0186051', # Titmouse (tt2058221)
																'co0276639', # Tiny Pop (tt5607658)
																'co0101987', # Treehouse TV (tt11873224)
																'co0764723', # Hayu (tt4986084)
															],
														},
														Media.Movie	: {
															# Too many movies released/distributed by other (smaller) studios/networks, making it difficult to filter.
															'disallow' : [
																# Too many cluttered titles with Discovery Kids and Discovery Toons.
																# Do not exclude Force Channel, like with shows, since it contains a lot of normal movies.
																'co0981669', 'co0614571', 'co0984883', 'co0092660', 'co0092660', 'co0981619', 'co0981827', 'co1010769', 'co0598558', 'co1006785', 'co1061317', 'co0275477', 'co0984881', 'co1067092', 'co1006154', 'co0788357', 'co1012797', 'co0525521', 'co0525521', 'co1012796', 'co0981825', 'co0981689', 'co0981643', 'co1070858', 'co1067096', 'co1048738', 'co1048737', 'co1048736', 'co1048735', 'co1006964', 'co1005826',
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # tt1649418, tt2463208, tt7991608
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]}, # tt15326988
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # tt4637028
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # tt9695722
																{MetaCompany.CompanyTubi			: [MetaProvider.CompanyNetwork]}, # tt1587807

																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt1517489
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},

																'co0037052', # American Broadcasting Company (ABC) (tt0267913)
																'co1021520', # Sky Original Films (tt15845360)
																'co0024325', # Dutch FilmWorks (DFW) (tt8417168)
																'co0114002', # Madman Entertainment (tt10530838)
																'co0043365', # CJ Entertainment (tt7156436)
																'co0984887', # Nintendo Pictures (tt1123372, tt3229648)
																'co1006606', # Cartoon Network (tt2788526)
																'co0815056', # Rajawali Televisi (RTV) (tt10534312, tt7869818, tt8734872)
																'co0294642', # The Hub (tt3861212)
																'co0000869', # Starz (tt1754915)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0045277', 'co0225421', 'co0092660', 'co0225759', 'co0521172', 'co0021831', 'co0134725', 'co0056361', 'co0265049', 'co0003317', 'co0504839', 'co0132346', 'co0525521', 'co1003986', 'co0763811', 'co0213496', 'co0912981', 'co0634119', 'co0453652', 'co0274735', 'co0271061', 'co0256092', 'co0255454', 'co0241703', 'co0124561', 'co0100704'],
					MetaProvider.CompanyNetwork		: ['co0981669', 'co0834810', 'co0981653', 'co0614571', 'co0225421', 'co0984883', 'co0500808', 'co0726548', 'co0267805', 'co0089706', 'co0210778', 'co0212711', 'co0092660', 'co0045277', 'co0224615', 'co0981619', 'co0981827', 'co0074719', 'co1010769', 'co0030015', 'co1023494', 'co0120666', 'co0598558', 'co0070253', 'co0500448', 'co0188065', 'co0465058', 'co0504369', 'co0885467', 'co0147826', 'co0943778', 'co0457897', 'co0163534', 'co1006785', 'co0274712', 'co1061317', 'co0278859', 'co0102909', 'co0833882', 'co0315118', 'co0253720', 'co0182992', 'co0564243', 'co0409438', 'co0275477', 'co0155054', 'co0131594', 'co0984881', 'co0531164', 'co0271708', 'co0197261', 'co1067092', 'co0979624', 'co0656406', 'co1006154', 'co0927174', 'co0788357', 'co0427466', 'co0243945', 'co0130326', 'co0923071', 'co0896334', 'co0869091', 'co0848923', 'co0405559', 'co0404321', 'co0350346', 'co0225758', 'co0225264', 'co0147813', 'co0064712', 'co0664644', 'co0268270', 'co0106294', 'co1012797', 'co0924477', 'co0894752', 'co0610831', 'co0525521', 'co0511125', 'co0396789', 'co0389407', 'co0195831', 'co1023840', 'co1012796', 'co0981825', 'co0981689', 'co0981643', 'co0933193', 'co0904378', 'co0870258', 'co0746360', 'co0693803', 'co0583138', 'co0534443', 'co0486937', 'co0328002', 'co0166855', 'co1070858', 'co1067096', 'co1048738', 'co1048737', 'co1048736', 'co1048735', 'co1036969', 'co1027849', 'co1027848', 'co1006964', 'co1006908', 'co1005826', 'co0964265', 'co0891875', 'co0828614', 'co0809123', 'co0683600', 'co0654638', 'co0565776', 'co0397571', 'co0314157', 'co0245318', 'co0205109', 'co0168990', 'co1006802', 'co0997619', 'co0965409'],
					MetaProvider.CompanyVendor		: ['co0077924', 'co0863266', 'co0131861', 'co0212079', 'co0521172', 'co0639652', 'co0021831', 'co0601745', 'co0543688', 'co0473690', 'co0298300', 'co0013509', 'co0051998', 'co0003317', 'co0876160', 'co0394091', 'co0625938', 'co0165242', 'co0808524', 'co0453651', 'co1005816', 'co0318256', 'co0924483', 'co0322476', 'co0284818', 'co0108234', 'co1063267', 'co1044762', 'co1037501', 'co1031570', 'co1031569', 'co1031568', 'co1008104', 'co0986413', 'co0930735', 'co0759066', 'co0607065', 'co0574955', 'co0503443', 'co0453652', 'co0211019', 'co0027586', 'co1058424', 'co0877509', 'co0758186', 'co0642760', 'co0583140', 'co0583139'],
				},
				MetaCompany.CompanyDisney : {
					# Show (804 of 357+): Level-4. A lot of other originals appear on Disney+, and many Disney originals appear on other platforms. Many co-productions (Hulu, NatGeo, ABC, etc).
					# Movie (934 of 115+): Level-4. Has many normal Walt Disney titles, that are not necessarily part of Disney+/Disney-Channel originals.
					# https://en.wikipedia.org/wiki/Category:Disney%2B_original_programming
					# https://en.wikipedia.org/wiki/Category:Disney_Channel_original_programming
					# https://en.wikipedia.org/wiki/Category:Disney%2B_original_films
					# https://en.wikipedia.org/wiki/Category:Disney_Channel_original_films
					# https://en.wikipedia.org/wiki/List_of_Disney%2B_original_films
					# https://en.wikipedia.org/wiki/List_of_Disney_Channel_original_films
					# Fox, FX, Star+, Lifetime, A&E, ABC, National Geographic, and History Channel owned by Disney.
					# Disney produces a lot of content for Hulu, and now also 100% owns Hulu.
					# Disney produces a lot of content National Geographic, and vice versa.
					# Most Disney titles appear on Disney+, Star+, Hulu, and occasionally NatGeo.
					# Most "true" Disney originals (Star Trek, Marvel, etc) are only on Disney+, but not Hulu. But there are exceptions (tt13157618, tt24640580, tt26450613, tt27921614).
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'language' : [
																{Language.CodeIndian : ['co0847080', 'co0930616', 'co0930627', 'co1046200', 'co0507878']},
															],
															'disallow' : [
																# There are way too many Disney cartoons and children's programs, cluttering the menu with titles that most people do not want to watch.
																# Excluding these is not always a good idea, since some of the Disney+ titles we want, also appear on Channel/XD/Junior, although not that many.
																# Also, 95% of all Channel/XD/Junior are also listed under the normal Disney+.
																# Disallow them, trying to get rid of at least some titles that are not on Disney+.
																# Reduces shows from 1700 down to 800 titles with "disallow", or 600 titles with "exclude".
																'co0022105', 'co0243675', 'co0311978', 'co0172644', 'co0831766', 'co0410032', 'co0875800', 'co0293280', 'co0326117', 'co0655773', 'co0507878', 'co0363715', 'co0293235', 'co0124426', 'co0497271', 'co0465045', 'co0148907', 'co0269642', 'co0127640', 'co0483030', 'co0092035', 'co0962993', 'co0931913', 'co0472570', 'co0410031', 'co0328976', 'co0586391', 'co0510795', 'co0479835', 'co0067765', 'co0311814', 'co1069365', 'co0067765', 'co0899094', 'co0616595', 'co0475581', 'co0626229', 'co0503291', 'co0492228', 'co0492228', 'co0487401', 'co0479836', 'co0471424', 'co0970093', 'co0854831', 'co0743057', 'co0638820', 'co0503303', 'co0308696', 'co0818715', 'co0693410', 'co0503276', 'co0503273', 'co0460088', 'co0438719', 'co1070494', 'co1031882', 'co0971893', 'co0940491', 'co0864435', 'co0833749', 'co0830701', 'co0716227', 'co0654197', 'co0646640', 'co0545024', 'co0503301', 'co0410034', 'co0410033', 'co0333590', 'co0781340',
															],
														},
														Media.Show : {
															'allow' : [
																'co0103528', # Channel 4 Television Corporation (too much other content listed here that too many titles might be excluded with CH4 networks).
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},

																# Fox, FX, and ABC owned by Disney.
																# But still exclude "FX Productions", since they are inteded for FX/Hulu.
																{MetaCompany.CompanyFx			: [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork]}, # tt2788316, tt14452776, tt5645432, tt11527058
																{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]}, # tt7235466
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]}, # tt11691774, tt1640719, tt17543592. Do not add studio for tt12580982.

																# Although Disney produces a lot of content for Hulu, there are too many Hulu titles.
																# Most "true" Disney originals (Star Trek, Marvel, etc) are only on Disney+, but not Hulu. But there are exceptions (tt13157618, tt24640580, tt26450613, tt27921614).
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyStudio]}, # tt14500082, tt25050236, tt20285780, tt13018148, tt9811316, tt9114512. Do not add network for tt13157618.

																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # tt0452046
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]}, # tt13875494
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]}, # tt1199099
																{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # tt4803766
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # tt12878838
																{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork]}, # tt14531842, tt0086661
																{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]}, # tt27775188
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # tt15669534
																{MetaCompany.CompanyBbc			: [MetaProvider.CompanyNetwork]}, # tt1533435, tt10166622, tt9174558, tt11997646
																{MetaCompany.CompanyStarz			: [MetaProvider.CompanyNetwork]}, # tt8610212

																# NatGeo is owned by Disney, but there are too many titles cluttering the menu.
																# Exclude here. Users can watch them from the NatGeo Originals.
																# Some are incorrectly excluded: tt17921714, tt5673782, tt9165706.
																{MetaCompany.CompanyNationalgeo	: [MetaProvider.CompanyNetwork]}, # tt10370750, tt4838586, tt2964642, tt4131818, tt3110590, tt1020109, tt26351130, tt11170862, tt11003514, tt11003514, tt10115054

																# Although Disney owns Lifetime, exclude them.
																'co0006395', # Lifetime Television (tt1991410)

																'co0070925', # Fox Network (tt7235466, tt0285331)
																'co0198140', # Fox Networks Group (tt9070896)
																'co0039462', # Public Broadcasting Service (PBS) (tt3747572)
																'co0028644', # Special Broadcasting Service (SBS) (tt11899030)
																'co0375381', # Universal Sony Pictures Home Entertainment (tt7678620)
																#'co0234667', # BBC One (tt10166622)
																#'co0234496', # BBC Two (tt9174558)
																#'co0399177', # BBC Three (tt11997646)
																'co0879659', # Sony AXN (tt9113406)
																'co0684443', # Viu (tt7222086)
																'co0077535', # The WB Television Network (tt0134247)
																'co0281995', # BBC DVD (tt0396991)
																'co0072315', # National Broadcasting Company (NBC) (tt0101050)
																'co0301399', # Alibi (tt7242816)
																'co0186281', # AXN (tt0083470)
																'co0217299', # AXN (tt2006421)
																'co0018288', # Seoul Broadcasting System (SBS) (tt6157190)
																'co0306669', # Munhwa Broadcasting Corporation (MBC) (tt21195490)
																'co0367814', # JTBC (tt13304700)
																'co0964826', # WOW (tt0423652)
																'co0003716', # History Channel (tt4680444, tt1596786)
																'co0069685', # Studios USA Television (tt0111964)
																'co0108881', # MGM/UA Television (tt0086744)
																'co0544623', # Movistar+ (tt10883660)
																'co0730454', # Huanyu Entertainment (tt9632208)
																'co0487058', # Tencent Video (tt7817930)
																'co0045850', # Canadian Broadcasting Corporation (CBC) (tt0923293)
																'co0008949', # Korean Broadcasting System (KBS) (tt19851552)
																'co0195232', # OCN (tt8236544, tt3914520)
																'co0169177', # Fox International Channels (tt1020116)
																'co0435933', # CTV (tt11262762)
																'co0325317', # ITV America (tt23161752)
																'co0332053', # tvN (tt3215140)
																'co0662529', # Spectrum Originals (tt14391474)
																'co0610457', # Bilibili (tt19896160)
																'co0025002', # TV Asahi (tt9563806)
																'co0459291', # National Geographic Wild (tt6498784)
																'co0359809', # Fernsehjuwelen (tt10853780)
																'co0040478', # ESPN (Entertainment & Sports Programming Network) (tt13081200)
																'co0003850', # Nippon Television Network (NTV) (tt20518582)

																# Anime
																'co0132285', # Aniplex (tt0988824)
																'co0035005', # AT-X (tt22817632)
																'co0028689', # Manga Entertainment (tt0110426)

															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},

																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]}, # tt0114924, tt0107282
																{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]}, # tt1414382
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyStudio]}, # tt26569323

																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},

																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]}, # tt1821694, tt1714206

																#{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]}, # Now owned by Disney. Exclude the pre-Disney companies below.
																#{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyVendor]}, # Owned by Disney.

																'co0225299', # Summit Distribution (tt0945513)
																'co0292985', # Summit Home Entertainment (tt1673434)
																'co0819893', # Paramount Home Entertainment (tt1109624)
																'co0384006', # Pathé Distribution (tt2358891)
																'co0047476', # StudioCanal (tt2244901)
																'co0151501', # Capelight Pictures (tt7241926)
																'co0042399', # Focus Features (tt0480242)
																'co0022594', # Miramax (tt0918927)
																'co0351891', # Signature Entertainment (tt4486986)
																'co0461959', # Signature Pictures (tt2716382)
																'co0534547', # Anime Limited (tt15242330)

																# Owned by Disney.
																'co0384006', # Hollywood Pictures Home Entertainment (tt0107282)
																'co0028932', # Searchlight Pictures (tt9731534, tt9770150, tt15218000, tt14814040, tt12758486)

																# 20th Century Fox (pre-Disney).
																# There are still a bunch of 20th Century Studios titles left that might not be considered Disney Originals (tt6264654, tt4244994, tt11858890).
																'co0000756', 'co0010224', 'co0053239', 'co0007180', 'co0189783', 'co0280047', 'co0862964', 'co0092296', 'co0150813', 'co0063964', 'co0159046', 'co0209782', 'co0296943', 'co0297163', 'co0010685', 'co0063989', 'co0937473', 'co0751509', 'co0826899', 'co0605838', 'co0853216', 'co0421648', 'co0108018', 'co0937474', 'co0643891',
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0008970', 'co0044374', 'co0098836', 'co0030830', 'co0059516', 'co0074039', 'co0858960', 'co0236496', 'co0007273', 'co0680423', 'co0046531', 'co0092035', 'co0075995', 'co0228775', 'co0647646', 'co0473608', 'co0067765', 'co0487331', 'co0236193', 'co0108298', 'co0911059', 'co0185084', 'co0067765', 'co0587555', 'co0127587', 'co0648616', 'co0330557', 'co0233857', 'co0251003', 'co0218992', 'co0136752', 'co0060743', 'co0057494', 'co0032298', 'co0863227', 'co0861755', 'co0775889', 'co0269268', 'co0081470', 'co1019732', 'co0985230', 'co0876136', 'co0756059', 'co0629374', 'co0577273', 'co0495414', 'co0323370', 'co0060584', 'co0782717', 'co0227227'],
					MetaProvider.CompanyNetwork		: ['co0721120', 'co0022105', 'co0847080', 'co0243675', 'co0311978', 'co0172644', 'co0831766', 'co0410032', 'co0875800', 'co0293280', 'co0326117', 'co0655773', 'co0507878', 'co0363715', 'co0293235', 'co0124426', 'co0497271', 'co0465045', 'co0148907', 'co0269642', 'co0127640', 'co0483030', 'co0962993', 'co0931913', 'co0472570', 'co0838196', 'co0410031', 'co0328976', 'co0930616', 'co0586391', 'co0510795', 'co0479835', 'co0311814', 'co1069365', 'co0899094', 'co0616595', 'co0475581', 'co0626229', 'co0503291', 'co0492228', 'co0492228', 'co0487401', 'co0479836', 'co0471424', 'co0970093', 'co0930627', 'co0854831', 'co0743057', 'co0638820', 'co0503303', 'co0308696', 'co0818715', 'co0693410', 'co0503276', 'co0503273', 'co0460088', 'co0438719', 'co1070494', 'co1046200', 'co1031882', 'co0971893', 'co0940491', 'co0864435', 'co0833749', 'co0830701', 'co0716227', 'co0654197', 'co0646640', 'co0545024', 'co0503301', 'co0410034', 'co0410033', 'co0333590', 'co0781340'],
					MetaProvider.CompanyVendor		: ['co0000779', 'co0226183', 'co0049546', 'co0114699', 'co0013021', 'co0213225', 'co0078478', 'co0039330', 'co0229306', 'co0209825', 'co0033410', 'co0227555', 'co0193692', 'co0811166', 'co0044279', 'co0659852', 'co0351644', 'co0244964', 'co0014626', 'co0292142', 'co0172644', 'co0385962', 'co0121807', 'co0229701', 'co0234296', 'co0248598', 'co0239645', 'co0235043', 'co0087337', 'co0108188', 'co0123419', 'co0565163', 'co0126002', 'co0916747', 'co0882527', 'co0813447', 'co1042820', 'co0824956', 'co0792679', 'co0774695', 'co0133895', 'co0302554', 'co0251885', 'co0170500', 'co0660110', 'co0233849', 'co0916748', 'co0774696', 'co0230605', 'co0606140', 'co0331976', 'co0991889', 'co0916028', 'co0218422', 'co0602039', 'co0514544', 'co0135322', 'co0256585', 'co0595116', 'co0039725', 'co0303939', 'co0077596', 'co0280125', 'co0212150', 'co0119593', 'co0966487', 'co0565114', 'co0269496', 'co0226005', 'co0972210', 'co0127146', 'co0028786', 'co0967209', 'co0256904', 'co0162996', 'co0050977', 'co0497272', 'co0279419', 'co0110121', 'co0011680', 'co0894430', 'co0606141', 'co0238690', 'co0298029', 'co0148456', 'co0958910', 'co0646633', 'co0212721', 'co0094898', 'co0241443', 'co0225392', 'co0188047', 'co0989959', 'co0286221', 'co0183512', 'co0136583', 'co0972527', 'co0956237', 'co0472915', 'co0242391', 'co0979350', 'co0799752', 'co0786439', 'co0586391', 'co0739072', 'co0474398', 'co0360208', 'co0244024', 'co1041397', 'co1009765', 'co0998459', 'co0448448', 'co0380199', 'co0090520', 'co1011371', 'co0918614', 'co0306723', 'co0298883', 'co0298883', 'co0292086', 'co0144563', 'co1033923', 'co1000896', 'co0937874', 'co0850185', 'co0806192', 'co0475581', 'co0406107', 'co0381864', 'co0297226', 'co0167716', 'co0118321', 'co0076708', 'co0918597', 'co0817519', 'co0816614', 'co0777984', 'co0627160', 'co0494199', 'co0479836', 'co0203040', 'co0175122', 'co0039576', 'co1005822', 'co0968316', 'co0968314', 'co0968309', 'co0817786', 'co0806509', 'co0799546', 'co0727433', 'co0671586', 'co0582081', 'co0506477', 'co0497275', 'co0445522', 'co0383487', 'co0366876', 'co0356736', 'co0336503', 'co0228542', 'co0218992', 'co0200835', 'co0122790', 'co0118329', 'co0006618', 'co1052155', 'co1035870', 'co1025506', 'co0968313', 'co0937873', 'co0808425', 'co0770520', 'co0688938', 'co0686598', 'co0654909', 'co0605619', 'co0597852', 'co0595325', 'co0595115', 'co0512778', 'co0503268', 'co0497274', 'co0497273', 'co0482409', 'co0405683', 'co0330522', 'co0310744', 'co0291721', 'co0252715', 'co0242525', 'co0187099', 'co0004375', 'co1071047', 'co1064117', 'co1050629', 'co1037590', 'co1014399', 'co1011345', 'co1011338', 'co1011337', 'co1009793', 'co1009357', 'co0990094', 'co0976075', 'co0968984', 'co0968983', 'co0968982', 'co0968981', 'co0968980', 'co0968315', 'co0968312', 'co0968311', 'co0936067', 'co0927318', 'co0913419', 'co0887985', 'co0874690', 'co0874690', 'co0858033', 'co0836847', 'co0796300', 'co0761450', 'co0752998', 'co0663644', 'co0663602', 'co0646695', 'co0557891', 'co0545133', 'co0506478', 'co0503297', 'co0503269', 'co0480703', 'co0429426', 'co0419912', 'co0419911', 'co0406009', 'co0361752', 'co0356845', 'co0350074', 'co0338893', 'co0338803', 'co0330842', 'co0325880', 'co0305751', 'co0247714', 'co0243626', 'co0228631', 'co0225453', 'co0209424', 'co0189485', 'co0127032', 'co0122778', 'co0120700', 'co0100079', 'co0094890', 'co0044682', 'co0042428', 'co1051278', 'co1051277', 'co1050960', 'co1050659', 'co1050658', 'co1044874', 'co1044115', 'co1044114', 'co1044113', 'co1044112', 'co1038671', 'co0968310', 'co0863768', 'co0782717', 'co0712949', 'co0482408', 'co0348142', 'co0254863', 'co0247742', 'co0144564', 'co0099937', 'co0066549', 'co0058858', 'co0016858'],
				},
				MetaCompany.CompanyDreamworks : {
					# Show (196): Level-4
					# Movie (267): Level-4
					# Produces content for other networks (NBC, Netflix, HBO, TNT, etc)
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
															],
														},
														Media.Movie : {
															'exclude' : [
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0129164', 'co0040938', 'co0819670', 'co0461500', 'co0554810', 'co0003158', 'co0252576', 'co0669071', 'co0527751', 'co0102694'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0027541', 'co0067641', 'co0299243', 'co0396719', 'co0772464', 'co0405898', 'co0289670', 'co0397133', 'co0371886', 'co0961518', 'co0377564', 'co0121773', 'co0751021', 'co0513025', 'co0431502', 'co0882259', 'co0646563', 'co0169654', 'co0253584'],
				},
				MetaCompany.CompanyFacebook : {
					# Show (267): Level-4
					# Movie (24): Level-4
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},

																{MetaCompany.CompanyYoutube		: [MetaProvider.CompanyNetwork]}, # tt15430152
																{MetaCompany.CompanyMtv			: [MetaProvider.CompanyNetwork]}, # tt0103520
																{MetaCompany.CompanyBritbox		: [MetaProvider.CompanyNetwork]}, # tt11347766
															],
														},
														Media.Show : {
															'exclude' : [
																'co0021273', # ABC Entertainment (tt7849864)
																'co0673353', # ShowMax (tt30279071)
															],
														},
														Media.Movie : {
															'exclude' : [
																'co0047476', # StudioCanal (tt10407272)
																'co0644674', # Wings Entertainment (tt2995836)
																'co0136666', # Canal de las Estrellas (tt1484065)
																'co0091046', # NRK-TV International (tt21862900)
															],
														},
													},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0667127', 'co0321654'],
					MetaProvider.CompanyVendor		: ['co0776772', 'co0933562', 'co0872204'],
				},
				MetaCompany.CompanyFox : {
					# Show (870): Level-3 to Level-4
					# Movie (373): Level-3. Since many titles are produced by 20th Century Fox, one cannot really exclude much.
					# The biggest problem is probably not being able to filter out FX (now Disney). Too many true Fox originals are listed under the FX/FXX/FXM networks, and some even under FX Productions.
					# There are also a bunch of titles produced by 20th Centruy Fox and Fox Television, which are NBC or USA originals (tt0460091, tt0810788).
					MetaProvider.CompanyOriginal	: {
														Media.Unknown	: {
															'fixed' : MetaProvider.CompanyNetwork, # 20th Centruy Fox, Fox Television, and other Fox studios produce a lot of content that are originals of other platforms (NBC, USA, Netflix, etc).
															'disallow' : [
																# Fox Kids
																'co0007893', 'co1071109', 'co0054541',

																# Fox Sports
																'co0048418', 'co0545358', 'co0247100', 'co0447568', 'co0198143', 'co0267041', 'co0489335',

																# Fox Business
																'co0210247', 'co0857401',

																# Fox News
																'co0085044',

																# Fox Premium Series (AR)
																'co0710263',

																# Fox Showcase
																'co0736326',

																# Fox from certain countries. Contains too many toher titles. Most Fox Originals are on "Fox Network".
																'co0202535', 'co0440497', 'co0771707', 'co0478980', 'co0877386', 'co0449297',

																# Foxtel
																'co0119102', 'co0039238', 'co0227681', 'co0778133', 'co0174174', 'co0626569', 'co0919693', 'co0974175',
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt0455275, tt4052886, tt0182576, tt1826940, tt2467372, tt0412142
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # Not for tt0455275, tt4052886, tt0182576, tt1119644, tt0412142, tt0460627
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # Not for tt0455275, tt0182576, tt2618986, tt1826940, tt0285331, tt0303461
																#{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # Not for tt0182576, tt0118375, tt1195935, tt0149460, tt1561755
																#{MetaCompany.CompanySky				: [MetaProvider.CompanyNetwork]}, # Not for tt0455275, tt4052886, tt0182576, tt2467372, tt0285331, tt1119644
																#{MetaCompany.CompanyBbc				: [MetaProvider.CompanyNetwork]}, # Not for tt0182576, tt0285331
																#{MetaCompany.CompanyItv				: [MetaProvider.CompanyNetwork]}, # Not for tt0182576, tt0851851, tt1195935, tt5164196, tt1561755
																#{MetaCompany.CompanyChannel4			: [MetaProvider.CompanyNetwork]}, # Not for tt0182576, tt1826940, tt2467372, tt0362359, tt0149460
																#{MetaCompany.CompanyChannel5			: [MetaProvider.CompanyNetwork]}, # Not for tt0204993, tt3749900
																#{MetaCompany.CompanyAdultswim		: [MetaProvider.CompanyNetwork]}, # Not for tt0182576, tt0118375, tt0149460, tt1561755
																#{MetaCompany.CompanyNickelodeon		: [MetaProvider.CompanyNetwork]}, # Not for tt0182576
																#{MetaCompany.CompanyComedycen	: [MetaProvider.CompanyNetwork]}, # Not for tt0182576, tt5691552, tt1195935, tt0165598, tt0149460, tt0096697
																#{MetaCompany.CompanyCartoonnet	: [MetaProvider.CompanyNetwork]}, # Not for tt0182576, tt0096697
																#{MetaCompany.CompanyFx				: [MetaProvider.CompanyNetwork]}, # Not for tt0182576, tt2618986, tt2647544, tt0118375, tt1195935, tt0149460
																#{MetaCompany.CompanySyfy				: [MetaProvider.CompanyNetwork]}, # Not for tt0851851, tt0303461, tt0204993
																#{MetaCompany.CompanyHulu				: [MetaProvider.CompanyNetwork]}, # Not for tt1826940, tt5691552, tt0118375, tt0412142, tt0149460, tt1561755
																#{MetaCompany.CompanyPeacock			: [MetaProvider.CompanyNetwork]}, # Not for tt1826940

																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # tt0944947. Not for tt0362359, tt1119644, tt1615919, tt3749900, tt0165598.
																#{MetaCompany.CompanyUsa				: [MetaProvider.CompanyNetwork]}, # tt1632701, tt0810788. Not for tt7235466.
																{MetaCompany.CompanyTnt				: [MetaProvider.CompanyNetwork]}, # tt0773262
																{MetaCompany.CompanyShowtime			: [MetaProvider.CompanyNetwork]}, # tt0773262
																{MetaCompany.CompanyAmc				: [MetaProvider.CompanyNetwork]}, # tt1520211
																{MetaCompany.CompanyHistory			: [MetaProvider.CompanyNetwork]}, # tt2306299
																{MetaCompany.CompanyCw				: [MetaProvider.CompanyNetwork]}, # tt0397442, tt1405406, tt2661044, tt9471404
																{MetaCompany.CompanyStarz				: [MetaProvider.CompanyNetwork]}, # tt2375692
																{MetaCompany.CompanyAe				: [MetaProvider.CompanyNetwork]}, # tt2188671
																{MetaCompany.CompanyMgm				: [MetaProvider.CompanyNetwork]}, # tt8080122, tt9686194

																{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyStudio]}, # tt3502248 (studios only)

																# We Since we cannot get rid of FX Network, at least remove some (with rights now probably all belong to Disney).
																'co0216537', # FX Productions (tt6439752, tt2788432, tt6439752, tt1486217). Not for tt2618986. Rea-add, since this might only be one title, but excludes a lot of newer FX productions.
																'co0362128', # FX Canada (tt1984119, tt2149175, tt2654620, tt5114356). Removes at least some FX originals.

																#'co0072315', # National Broadcasting Company (NBC) (tt0203259, tt2805096, tt0200276, tt0364828, tt0460091). Not for tt2467372, tt0412142 (only has studio listed).
																#'co0069685', # Studios USA Television (tt0203259). Not for tt0112167.
																#'co0123927', # DC Entertainment. Not for tt4052886.
																#'co0038332', # DC Comics. Not for tt3749900.

																'co0059516', # Walt Disney Studios (tt12324366)
																'co0037052', # American Broadcasting Company (ABC) (tt0411008, tt0413573, tt7587890). tt7235466 is now an ABC Original, but does not have the company listed.
																'co0070627', # CBS (tt0364845, tt0460649)
																'co0062107', # Toei Animation (tt0388629)
																'co0177234', # Dutch Oven (tt1632701)
																'co0077623', # Home Box Office Home Video (HBO) (tt0306414)
																'co0137851', # Sony Pictures Home Entertainment (tt3006802, tt2741602)
																'co0288470', # Jeff Eastin & Warrior George Productions (tt3006802)
																'co0077535', # The WB Television Network (tt0118276)
																'co0422378', # BBC Television (tt1888075)
																'co0019598', # Wolf Films (tt2805096, tt0203259, tt2261391)
																'co0076928', # Bravo Cable (tt0200276)
																#'co0356636', # Universal Channel (tt1830617)
																#'co0440561', # Universal Channel (tt4477976). Not for tt0460627.
																'co0046592', # Universal Television (tt1830617, tt4477976)
																'co0242101', # Universal Cable Productions (tt1319735)
																'co0733397', # NBCUniversal Content Studios (tt8388390)
																'co0071326', # Lucasfilm (tt13622776)
																'co0022762', # NBC Studios (tt0364828)
																'co0820547', # Paramount+ (tt5853176)
																'co0042496', # Cinemax (tt1492179)
																'co0077920', # USA Television Network (tt1064899)
																'co0086397', # Sony Pictures Television (tt4975856)
																'co0183875', # CBS Paramount Network Television (tt0389564)
																'co0209226', # ABC Signature (tt5614844)
																'co0569560', # Levens (tt3696720)
																'co0200179', # Warner Bros. Home Entertainment (tt0103359)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyVendor]},

																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0000756', 'co0056447', 'co0096253', 'co0982337', 'co0010685', 'co0738806', 'co0230438', 'co0017497', 'co0103215', 'co0094955', 'co0179259', 'co0159275', 'co0237611', 'co0044236', 'co0511631', 'co0745899', 'co0153896', 'co0049229', 'co0043064', 'co0119102', 'co0389268', 'co0176225', 'co0540029', 'co0526787', 'co0359883', 'co1000157', 'co0505758', 'co0381995', 'co0241299', 'co0161155', 'co0478329', 'co0111263', 'co0145584', 'co0119101', 'co0036884', 'co0016208', 'co0523978', 'co0481724', 'co0324816', 'co0205994', 'co0089950', 'co0029761', 'co0708085', 'co0564373', 'co0201557', 'co0355206', 'co1031931', 'co0864210', 'co0858861', 'co0837708', 'co0658666', 'co0592896', 'co0494836', 'co0330294', 'co0282311', 'co0219533', 'co0145961', 'co0096046', 'co0077505', 'co0073335', 'co0645300', 'co0568535'],
					MetaProvider.CompanyNetwork		: ['co0070925', 'co0202535', 'co0007893', 'co0440497', 'co0039238', 'co0048418', 'co0054541', 'co0721667', 'co0375871', 'co0202574', 'co0204898', 'co0227681', 'co0545358', 'co0258754', 'co0908997', 'co0247100', 'co0771707', 'co0449463', 'co0202732', 'co0301422', 'co0078297', 'co0051829', 'co0277812', 'co0206943', 'co0710263', 'co0004295', 'co0682531', 'co0447568', 'co0250861', 'co0203823', 'co0751740', 'co0356177', 'co0210247', 'co0542537', 'co0306913', 'co0159248', 'co0778133', 'co0478980', 'co0877386', 'co0736326', 'co0198143', 'co0174174', 'co0085044', 'co0449297', 'co0359063', 'co0267041', 'co0249996', 'co0575133', 'co0558237', 'co0626569', 'co0403745', 'co0355572', 'co0355485', 'co0135313', 'co0804693', 'co0731654', 'co0489335', 'co0448576', 'co0365499', 'co0363535', 'co0355970', 'co0589037', 'co0571347', 'co0540887', 'co0284410', 'co0187655', 'co0919693', 'co0823247', 'co0780552', 'co0540882', 'co0540030', 'co0457833', 'co0367883', 'co0367831', 'co0350472', 'co0341010', 'co0326196', 'co0189391', 'co0107413', 'co1071109', 'co1028671', 'co0974175', 'co0857401', 'co0773182', 'co0764281', 'co0619897', 'co0546196', 'co0540886', 'co0540885', 'co0540884', 'co0540881', 'co0540880', 'co0540879', 'co0540033', 'co0540032', 'co0540031', 'co0520126', 'co0495243', 'co0488293', 'co0375893', 'co0364689', 'co0247220', 'co0231938', 'co0203920', 'co0201790', 'co0974098', 'co0953613', 'co0761770', 'co0417565', 'co0233692'],
					MetaProvider.CompanyVendor		: ['co0000756', 'co0010224', 'co0053239', 'co0028775', 'co0070925', 'co0042311', 'co0007180', 'co0189783', 'co0280047', 'co0862964', 'co0007496', 'co0092296', 'co0017628', 'co0150813', 'co0063964', 'co0125154', 'co0226201', 'co0107998', 'co0159046', 'co0209782', 'co0296277', 'co0296943', 'co0628925', 'co0297163', 'co0768357', 'co0106097', 'co0010685', 'co0063989', 'co0629458', 'co0077922', 'co0937473', 'co0751509', 'co0826899', 'co0266060', 'co0605838', 'co0094754', 'co0212901', 'co0853216', 'co0453999', 'co0421648', 'co0004762', 'co0108018', 'co0266215', 'co0166027', 'co0030121', 'co0937474', 'co0643891', 'co0943364', 'co0226330', 'co0034633', 'co0806725', 'co0244801', 'co0952616', 'co0117449', 'co0565880', 'co0442630', 'co0286182', 'co0223570', 'co0711817', 'co0198140', 'co0873684', 'co0601119', 'co0257036', 'co0794652', 'co0931863', 'co0544968', 'co0445889', 'co0279204', 'co0788854', 'co0051662', 'co0613529', 'co0604098', 'co0169177', 'co0764128', 'co0197226', 'co0819148', 'co0244996', 'co0785884', 'co0025186', 'co0256824', 'co0226875', 'co0037196', 'co0581069', 'co0491690', 'co0389268', 'co0035270', 'co0540029', 'co0368892', 'co0241365', 'co0188813', 'co0186658', 'co0092951', 'co0273176', 'co0044433', 'co0012812', 'co0866807', 'co0832095', 'co0544609', 'co0534355', 'co0526787', 'co0410408', 'co0376922', 'co0124383', 'co0863455', 'co0623011', 'co0350138', 'co0339536', 'co0304538', 'co0775365', 'co0746852', 'co0746833', 'co0653064', 'co0628924', 'co0569543', 'co0496965', 'co0148451', 'co0111795', 'co0078923', 'co0877389', 'co0866288', 'co0665472', 'co0663130', 'co0643890', 'co0373782', 'co0195278', 'co0130300', 'co0947625', 'co0947212', 'co0867515', 'co0862965', 'co0838082', 'co0815746', 'co0794651', 'co0743189', 'co0707661', 'co0680153', 'co0491691', 'co0380710', 'co0346045', 'co0258074', 'co0197094', 'co0009425', 'co1051152', 'co1021830', 'co0918688', 'co0867516', 'co0863456', 'co0817521', 'co0814039', 'co0700002', 'co0670562', 'co0662795', 'co0662791', 'co0662785', 'co0662285', 'co0599875', 'co0590259', 'co0506412', 'co0287474', 'co0279054', 'co0046053', 'co0046053', 'co0039408', 'co1040440', 'co1034313', 'co1027357', 'co0981624', 'co0951793', 'co0939093', 'co0918845', 'co0918844', 'co0883912', 'co0870304', 'co0867519', 'co0867518', 'co0867517', 'co0855510', 'co0771917', 'co0761328', 'co0723388', 'co0698066', 'co0694711', 'co0660503', 'co0613528', 'co0602412', 'co0534310', 'co0481487', 'co0472872', 'co0423932', 'co0421647', 'co0400863', 'co0368843', 'co0368801', 'co0292578', 'co0271701', 'co0270675', 'co0224399', 'co0212875', 'co0209926', 'co0202504', 'co0200961', 'co0173400', 'co0160971', 'co0117468', 'co0080169', 'co0040586', 'co0924784', 'co0855511', 'co0663129', 'co0611815', 'co0547664', 'co0547663', 'co0451003', 'co0443515', 'co0379362', 'co0379346', 'co0379325', 'co0379300', 'co0368861', 'co0368661', 'co0293095', 'co0197792', 'co0196456', 'co0195082', 'co0118485', 'co0099617', 'co0094759', 'co0030446'],
				},
				MetaCompany.CompanyFreevee : {
					# Show (51): Level-3
					# Movie (67): Level-2
					# Freevee Originals created by Amazon Studios and/or also on Amazon Prime.
					# Most Freevee Originals are not on other competing platforms, with a few exceptions (eg: tt11090458, tt13315664)
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# IMDb and IMDb Originals.
																# There are some titles that are Originals (eg tt9154158, tt8589176, etc), but most titles are interviews and other IMDb summaries and shows.
																'co0699104',
																'co0047972',
																'co0890032',
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Not for tt11090458.
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # tt0804503
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # tt1094229, tt0056751
																{MetaCompany.CompanyBravo			: [MetaProvider.CompanyNetwork]}, # tt0765425
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]}, # tt2628232, tt0439100
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # tt0077000
																{MetaCompany.CompanyHistory		: [MetaProvider.CompanyNetwork]}, # tt15766736
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]}, # tt3517016

																'co0014456', # ARTE (tt2442560)
																'co0053559', # Paramount Television (tt9288030)
																'co0046592', # Universal Television (tt2261391)
																'co0242101', # Universal Cable Productions (tt7008682)
																'co0086397', # Sony Pictures Television (tt7462410)
																'co0508149', # Legendary Television (tt10623646)
																'co0194736', # Media Rights Capital (MRC) (tt11743610)
																'co0463308', # Picrow (tt4687880)
																'co0070636', # 3 Arts Entertainment (tt7826376)
																'co0037052', # American Broadcasting Company (ABC) (tt0059968)
																'co0072315', # National Broadcasting Company (NBC) (tt0094574)
																'co0070627', # CBS (tt0054533)
																'co0032922', # Hallmark Channel (tt0879688)
																'co0157100', # Koch Media (tt0075561)
																'co0172129', # Mill Creek Entertainment (tt0126158)
																'co0039940', # FUNimation Entertainment (tt1158671)
																'co0339529', # Tanweer Films (tt1158671)
																'co0575132', # Peppermint Enterprises (tt3922744)
																'co0264223', # Youku (tt11705374)
																'co0245229', # New KSM (tt3969094)
																#'co0045850', # Canadian Broadcasting Corporation (CBC) (tt1094229). Not for tt11090458.
															],
														},
														Media.Movie : {
															'allow' : [
																'co0007143', # Metro-Goldwyn-Mayer (MGM) (tt28182736)
																'co0060306', # Lionsgate Films (tt28182736)
															],
															'exclude' : [
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyBravo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHistory		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},

																'co0735768', # GED Cinema (tt6803046)
																'co0147162', # Shaw Organisation (tt8615822, tt8615822)
																'co0156943', # Tiberius Film (tt13026738)
																'co0339529', # Tanweer Films (tt2027136)
																'co0370614', # Tanweer Alliances (tt13141250)
																'co0267142', # Lumière Home Entertainment (tt1658851)
																'co0939736', # Plaion Pictures (tt18224610)
																'co0281939', # Breaking Glass Pictures (tt5883632)

																'co0024325', # Dutch FilmWorks (DFW)
																'co0037052', # American Broadcasting Company (ABC)
																'co0072315', # National Broadcasting Company (NBC)
																'co0070627', # CBS
															],
														},
													},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0796766', 'co0699104', 'co0047972', 'co0890032'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyFx : {
					# Show (178 of 87+): Level-4.
					# Movie (46 of 11+): Level-4.
					# https://en.wikipedia.org/wiki/Category:FX_Networks_original_programming
					# https://en.wikipedia.org/wiki/Category:FX_Networks_original_films
					MetaProvider.CompanyOriginal	: {
														Media.Show	: {
															'allow' : [
																'co0011881', # Showtime Australia (tt1124373)
															],
															'exclude' : [
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyStudio]}, # tt1520211. Do not add networks for tt2802850.
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Do not add for tt2802850, tt1844624, tt1124373.
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # tt0182576. Do not add for tt2802850, tt1844624.
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # tt9244556
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]}, # tt0364845, tt0098936
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]}, # tt1266020
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # tt1358522
																{MetaCompany.CompanyAdultswim		: [MetaProvider.CompanyNetwork]}, # tt1561755, tt0118375, tt0149460, tt0182576
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]}, # tt4093826
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # tt1132290
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # tt1462059
																{MetaCompany.CompanyStarz			: [MetaProvider.CompanyNetwork]}, # tt2094262
																{MetaCompany.CompanyCinemax		: [MetaProvider.CompanyNetwork]}, # tt4229954
																#{MetaCompany.CompanyComedycen	: [MetaProvider.CompanyNetwork]}, # tt3551096, tt1195935, tt0149460. Do not add for tt0472954.
																{MetaCompany.CompanyTubi			: [MetaProvider.CompanyNetwork]}, # tt1598754. Tubi created after Dinsey purchased FX from Fox.

																'co0878025', # Sky Showcase (tt0096697)
																'co0202446', # YouTube (tt10691770)
																#'co0247505', # Citytv (tt1828327). Do not add for tt1844624.
																'co0077261', # Radio Télévision Luxembourg - Télévision Indépendante (RTL-TVI) (tt1828327)
																'co0365525', # Universal Channel (tt2647544)
																'co0440561', # Universal Channel (tt1986770)
																'co0730731', # TVNOW (tt0460627)
																'co0106185', # E4 (tt1195935)
																#'co0260673', # Sub (tt3551096). Do not add for tt1844624.
																'co0037052', # American Broadcasting Company (ABC) (tt3551096). Both ABC and FX are owned by Disney.
																#'co0080139', # CTV Television Network (tt4396630). Do not add for tt0361217.
																'co0363506', # Orbit Showtime Network (OSN) (tt1641349)
																'co0617296', # Q2 (tt5345490, tt4396630)
																#'co0362268', # WOWOW Prime (tt1821681, tt2476706). Do not add for tt8746478.
																'co0117505', # Perviy Kanal (tt1821681, tt2476706)
																'co0056790', # A+E Networks (tt4337944)
																'co0118559', # Prima TV (tt1567254)
																#'co0363592', # FS Film (tt0446241). Listed as FX Original on Wikipedia.
																'co0014769', # Chum Television (tt0182587)
																'co0110170', # VMM (tt0320882)
																'co0424672', # The Online Network (tt2860376)
																'co0041689', # All American Television (tt0124232)
																'co0089715', # The Health Network (THN) (tt0346201)
															],
														},
														Media.Movie	: {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # tt9466114
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # tt2096673
																{MetaCompany.CompanyStarz			: [MetaProvider.CompanyNetwork]}, # tt0120484

																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt0293662, tt0371746, tt0458339
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]}, # tt1454029, tt0147800
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]}, # tt1099212
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]}, # tt0283111
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]}, # tt2948356, tt0367085
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]}, # tt0482606

																'co0002663', # Warner Bros. (tt1431045, tt0458525)
																'co0324445', # Starz Digital Media (tt1714203)
																'co0221717', # Lighthouse Home Entertainment (tt0240515)
																'co0035496', # Kinowelt Filmverleih (tt0443536)
																'co0051618', # Entertainment One (tt1517489)
																'co0150452', # The Weinstein Company (tt1780798)
																'co0011489', # Turner Classic Movies (TCM) (tt0367085)
																'co0024325', # Dutch FilmWorks (DFW) (tt9779516)
																'co0108000', # Intercontinental Video (tt2281587)
																'co0090512', # Arte France Cinéma (tt0362427)
																'co0016059', # Ascot Elite Home Entertainment (tt0401224)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0216537'],
					MetaProvider.CompanyNetwork		: ['co0060381', 'co0421362', 'co0186186', 'co0362128', 'co0481858', 'co0777254', 'co0197517', 'co0448575', 'co0385924', 'co0157673', 'co1032328', 'co0960667', 'co0902824', 'co0448574', 'co0263771', 'co0746872'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyGaumont : {
					# Show (111): Level-5
					# Movie (1444): Level-2 to Level-3
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
															],
														},
														Media.Movie : {
															'exclude' : [
																'co0967420', # Wild Chickens Productions (tt10640346)
																'co0040943', # The Princess Bride Ltd. (tt0093779)
																'co0044482', # Peninsula Films (tt0309987)
																'co0057311', # Working Title Films (tt0783233)
																'co0033437', # Mandalay Entertainment (tt0119345)
																'co0310456', # Virgin Produced (tt1219289)
																'co0049348', # Touchstone Pictures (tt0105417)
																'co0000858', # Brooksfilms (tt0080678)
																'co0135575', # Bold Films (tt1974419)
																'co0179365', # Don Bluth Productions (tt0096787)
																'co0135149', # Infinitum Nihil (tt0970179)
																'co0016626', # Tokuma Shoten (tt0087544)
																'co0112023', # Melodrama Pictures (tt0978762)
																'co0095134', # Marvel Enterprises (tt0103923)
																'co0106768', # Marvel Productions (tt0092106)
																'co0163343', # Rai 2 (tt0086022)
																'co0092453', # Entertainment 360 (tt1535438)
																'co0089870', # Cineplex Odeon Films (tt0099703)
																'co0013844', # Produzioni Europee Associate (PEA) (tt0074291)
																'co0091376', # Saga Productions Inc. (tt0082783)
																'co0113566', # Winkast Film Productions (tt0092563)
																'co0676288', # CKK (tt0074156)
																'co0039268', # Werner Herzog Filmproduktion (tt0083946)
																'co0093733', # Rankin/Bass Productions (tt0084237)
																'co0755807', # Alligator (tt0080354)
																'co0043612', # Polyphony Digital (tt0087089)
																'co0026096', # LQ/JAF (tt0072730)
																'co0641809', # ABC Motion Pictures (tt0091993)
																'co0066515', # Cargo Films (tt0090563)
																'co0059899', # Bad Movies (tt12959488)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0172053', 'co0059061', 'co0053065', 'co0051263', 'co0059676', 'co0011191', 'co0042098', 'co0285075', 'co0051969', 'co0353668', 'co0455873', 'co0125456', 'co0126294', 'co0197001', 'co0112349', 'co0118687', 'co0844356', 'co0374778', 'co0243598', 'co0054362', 'co0002907', 'co1053226', 'co0277376', 'co0961384', 'co0726353', 'co0341836', 'co0332544', 'co0278881', 'co0135492', 'co0131371', 'co0120389', 'co0099681', 'co0091513', 'co0083850', 'co0056284', 'co0022037', 'co0012779', 'co0778046', 'co0005388'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0172053', 'co0105966', 'co0033410', 'co0108034', 'co0182000', 'co0064278', 'co0026280', 'co0212919', 'co0159180', 'co0036160', 'co0187612', 'co0135317', 'co0186581', 'co0140056', 'co0864902', 'co0008471', 'co0064878', 'co0172122', 'co0028520', 'co0398337', 'co0128844', 'co0080245', 'co0240792', 'co0181164', 'co0699827', 'co0175932', 'co0066838', 'co0217840', 'co0173397', 'co0949530', 'co0772044', 'co0594645', 'co0521315', 'co0516770', 'co0456755', 'co0326260', 'co0308033', 'co0304207', 'co0301531', 'co0274195', 'co0247165', 'co0241665', 'co0100931', 'co0910931', 'co0902798', 'co0859868', 'co0147769', 'co0108027'],
				},
				MetaCompany.CompanyGoogle : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0944862', 'co0729093', 'co0678053', 'co0582980', 'co0507176', 'co0352536', 'co0265703'],
					MetaProvider.CompanyNetwork		: ['co0879800', 'co0422781', 'co1033988', 'co0992738', 'co0642369', 'co0625172', 'co0564081', 'co1021372', 'co0657283', 'co1001116', 'co0623478', 'co0613563', 'co0352536'],
					MetaProvider.CompanyVendor		: ['co0123378', 'co0487508', 'co0552365', 'co0379677', 'co1008843', 'co0821394', 'co0680753', 'co0635012', 'co0628498'],
				},
				MetaCompany.CompanyHayu : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0764723'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyHbo : {
					# Show (969 of 308+): Level-4.
					# Movie (629 of 260+): Level-3. Too many titles from smaller studios.
					# https://en.wikipedia.org/wiki/Category:HBO_original_programming
					# https://en.wikipedia.org/wiki/Category:HBO_Films_films
					# Collaborations with BBC, Cinemax, Showtime, and more.
					MetaProvider.CompanyOriginal	: {
														Media.Show	: {
															'allow' : [
																'co0103528', # Channel 4 Television Corporation (too much other content listed here that too many titles might be excluded with CH4 networks).
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyStudio]}, # Do not add network for tt0844441, and others.
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},

																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]}, # tt1839578
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]}, # tt0200276
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]}, # tt1442464
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # tt1220617
																{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]}, # tt8712204
																{MetaCompany.CompanyAcorn			: [MetaProvider.CompanyNetwork]}, # tt9466596
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]}, # tt0044231
																#{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # tt4276624 - Do not add for tt0944947.
																#{MetaCompany.CompanyComedycen	: [MetaProvider.CompanyNetwork]}, # tt0908454, tt0290978 - Do not add for tt0387199.
																#{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]}, # tt1582457 - Do not add for tt0944947.
																#{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]}, # tt12074628, tt14681924, tt0362359. Do not add for tt0264235.
																#{MetaCompany.CompanyCinemax		: [MetaProvider.CompanyNetwork]}, # tt4276618, tt2017109 (HBO sister company). Do not add for tt0306414, tt1886866.
																#{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # tt0458253. Do not add for tt0944947, tt0844441.

																'co0104481', # Zeppotron (tt2085059)
																#'co0751740', # FOX (tt2861424). Do not add for tt0844441.
																'co0997690', # ToonWorks Detour (tt2861424)
																'co0738806', # Fox Entertainment (tt11188682)
																'co0931273', # Crunchyroll (DE) (tt12057106)
																'co0234667', # BBC One (tt4276618)
																'co0202446', # YouTube (tt14681924)
																'co0037736', # Televisión Federal (Telefe) (tt0362359)
																'co0070756', # VOX (tt0458253)
																'co0131276', # Pop TV (tt1936532)
																'co0214175', # truTV (tt8026448)
																'co0001860', # United Paramount Network (UPN) (tt0105946)
																'co0088248', # TNT Originals (tt1462059)
																'co0044350', # Gativideo (tt0760437)
																'co0029473', # Albatros Film (tt0220880)
																'co0611078', # Videoland (tt7529770)
																'co0810364', # CTV Sci-Fi Channel (tt14923244)
																'co0058689', # YTV (tt0343314)
																'co0052980', # Showtime Networks (tt1582457)
																'co0844260', # Ertflix (tt0290978)
																'co0437769', # Kix (tt0398417)
																'co0052417', # NHK (tt5491994)
																'co0118346', # Epix Media (tt0237123)
																'co0157100', # Koch Media (tt1186356)
																'co0291780', # Koch Media (tt4718304)
																'co0124425', # Alive Vertrieb und Marketing (tt0417373)
																'co0039462', # Public Broadcasting Service (PBS) (tt1178618)
																#'co0335765', # Just Bridge Entertainment (tt1843678) - Do not add for tt1492179.
																'co0230162', # Reel DVD (tt1843678)
																'co0051891', # Paramount Home Entertainment (tt0297494)
																'co0032009', # CanWest Global Communications (tt0115378)
																'co0488702', # Viaplay (tt8290362)
																'co0815501', # AMC+ (tt9062784)
																'co0104833', # Children's Independent Television (CiTV) (tt4847134)
																'co0453279', # Kazé Germany (tt4731072)
																'co0165168', # Cable News Network (CNN) (tt2845786)
																'co0024325', # Dutch FilmWorks (DFW) (tt1885102)
																'co0013582', # Teletoon (tt0292800)
																'co0000869', # Starz (tt1832045)
																'co0089212', # Super RTL (tt0419326)
																'co0895262', # Kika (tt0352068)
																'co0491867', # Junior (tt0236893)
																'co0014957', # USA Network (tt3974304, tt0206500)
																'co0359809', # Fernsehjuwelen (tt0166035)
																'co0103999', # ATV Network (tt0080935)
																'co0027404', # Tango Entertainment (tt0086660)
																'co0006451', # Roadshow Home Video (tt0236909)
																'co0001093', # Trinity Broadcasting Network (TBN) (tt2515514)
																'co0122766', # Umbrella Entertainment (tt0089645)
																'co0098048', # Columbia TriStar Home Entertainment (tt0092383)
																'co0033381', # Independent Film Channel (IFC) (tt0103466)
																'co0004902', # Ketnet (tt0862620)

																'co0539690', # Fuji TV (tt0437745)
																'co0006066', # Anime Works (tt0318871)
																'co0120210', # Tokyo MX (tt28279848)
																'co0028689', # Manga Entertainment (tt0278238)
															],
														},
														# A few HBO Original Films are not listed under an HBO studio, but just the HBO channel.
														# But do not include the networks, otherwise there are too many false positives.
														Media.Movie	: {
															'fixed' : MetaProvider.CompanyStudio,
															'exclude' : [
																{MetaCompany.CompanyNetflix	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyParamount	: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyAmazon	: [MetaProvider.CompanyNetwork]}, # tt12361974

																'co0292142', # Walt Disney Studios Home Entertainment (tt1705786)
																'co0357132', # Wildcard Distribution (tt5664196)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0139821', 'co0005861', 'co0199013', 'co0391378', 'co0281949', 'co0229386', 'co0074198', 'co0490785', 'co0284741', 'co0561930', 'co0002401', 'co0625707', 'co0036039', 'co0440095', 'co0095169', 'co0320834', 'co0784743', 'co0149507', 'co0193395', 'co0080413', 'co0112313', 'co0095172', 'co0768628', 'co0478999', 'co0273255', 'co0068811', 'co0363290', 'co0051804', 'co0728364', 'co0179190'],
					MetaProvider.CompanyNetwork		: ['co0754095', 'co0008693', 'co0095413', 'co0167627', 'co0006163', 'co0909975', 'co0869157', 'co0777335', 'co0123742', 'co0913428', 'co0140098', 'co0644177', 'co0368145', 'co0092268', 'co1010749', 'co1020089', 'co1010750', 'co0915296', 'co0312842'],
					MetaProvider.CompanyVendor		: ['co0077623', 'co0101990', 'co0113668', 'co0840644', 'co0112024', 'co0680232', 'co0248784', 'co0114708', 'co0033562', 'co0037614', 'co0031966', 'co0289307', 'co0229386', 'co0306346', 'co0178216', 'co0450274', 'co0622841', 'co0625624', 'co0703486', 'co0638197', 'co0625625', 'co0736914', 'co0638196', 'co0487453', 'co0638200', 'co0638198', 'co0638201', 'co0638199', 'co0891644', 'co0450282', 'co0035311', 'co0799745', 'co0720309', 'co0638203', 'co0620979', 'co0484616', 'co0207690', 'co0148466', 'co0721140', 'co0640662'],
				},
				MetaCompany.CompanyHistory : {
					# Show (576): Level-4
					# Movie (698): Level-4
					# Most content provided or shared with A&E and Disney.
					# History is relatively accurate from the start, without too many exclusions.
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Do not add for tt2306299.
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # Do not add for tt2306299, tt11947238.
																#{MetaCompany.CompanySky				: [MetaProvider.CompanyNetwork]}, # Do not add for tt2306299.
																#{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # Do not add for tt4803766.
																#{MetaCompany.CompanyBbc				: [MetaProvider.CompanyNetwork]}, # Do not add for tt3910804.

																{MetaCompany.CompanyTrutv				: [MetaProvider.CompanyNetwork]}, # tt1674417
																{MetaCompany.CompanyParamount			: [MetaProvider.CompanyVendor]}, # tt0075520
																#{MetaCompany.Company20thcentury		: [MetaProvider.CompanyVendor]}, # tt2245988. Not for tt2306299.
																#{MetaCompany.CompanyWarner'			: [MetaProvider.CompanyVendor]}, # Not for tt2306299.
																{MetaCompany.CompanyUniversal			: [MetaProvider.CompanyVendor]}, # tt1567215

																#'co0072315', # National Broadcasting Company (NBC) (tt2400631). Not for tt1248967.
																'co0003079', # Concorde Home Entertainment (tt2400631)
																'co0046592', # Universal Television (tt0074007)
																'co0058425', # Granada Entertainment (tt0423652)
																'co0388495', # One Three Media (tt2245988)
																'co0827330', # Cornelia Street Productions (tt9179882)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyCartoonnet	: [MetaProvider.CompanyNetwork]}, # tt1075417

																{MetaCompany.CompanyParamount			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony				: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm				: [MetaProvider.CompanyVendor]},
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0003716', 'co0262451', 'co0579401', 'co0118166'],
					MetaProvider.CompanyNetwork		: ['co0003716', 'co0342233', 'co0889133', 'co0308904', 'co0379713', 'co0625848', 'co0995097', 'co0665299', 'co0626674', 'co0524434', 'co0473691', 'co0262373', 'co0880224', 'co0733710', 'co0688432', 'co1057532', 'co1048877', 'co1039714', 'co0904694', 'co0672898', 'co0655111', 'co0510420', 'co0500387', 'co0522483'],
					MetaProvider.CompanyVendor		: ['co0376124'],
				},
				MetaCompany.CompanyHulu : {
					# Show (515 of 147+): Level-4.
					# Movie (225 of 71+): Level-4.
					# https://en.wikipedia.org/wiki/Category:Hulu_original_programming
					# https://en.wikipedia.org/wiki/Category:Hulu_original_films
					# Hulu gets content from most major platforms owned by Disney (Disney, Fx, Star, etc).
					# Sometimes Hulu Originals also appear on other platforms like Netflix, Amazon, and Apple (eg: tt1844624, tt5834204).
					# There are also Hulu Originals (which became originals with later seasons) that are also on Netflix.
					# Most Hulu Originals are not listed under "Hulu Originals" (co0687042).
					MetaProvider.CompanyOriginal	: {
														Media.Show	: {
															'disallow' : [
																'co0381648', # Hulu Japan
															],
															'exclude' : [
																'co0055529', # Fuji Television Network (tt0388629)
																'co0035005', # AT-X (tt2560140)
																'co0120210', # Tokyo MX (tt28279848)
																'co0080694', # Yomiuri Telecasting Corporation (YTV) (tt0159175)
																'co0025002', # TV Asahi (tt0103369)
																'co0271936', # Proware Multimedia International (tt0318898)
																'co0203559', # Anime Virtual (tt3816198)
																'co0127153', # Animax (tt7441658)
																'co0217506', # Media Factory (tt0168366)
																'co0302457', # YOYO TV (tt1751105)
																'co0003850', # Nippon Television Network (NTV) (tt28329410)
																'co0114908', # Mainichi Broadcasting System (MBS) (tt21927720)

																'co0049524', # RTL (tt0088526)
																'co0317731', # Plug RTL (tt11640018)
																'co0878026', # Sky Max (tt9174582)
																'co0054806', # Nederlandse Christelijke Radio-Vereniging (NCRV) (tt0083483)
																'co0208462', # Antena 4 - Euforia Lifestyle Tv (tt0090493)
																'co0003601', # Sat.1 (tt0098929)
																'co0083928', # Witt/Thomas/Harris Productions (tt0103426)
																'co0039462', # Public Broadcasting Service (PBS) (tt12749392)
																'co0437769', # Kix (tt0247827)
																'co0031085', # Argentina Video Home (tt0259153)
																'co0014769', # Chum Television (tt0313038)
																'co0445068', # Frisbee (tt0300865)
																'co0867829', # Fubo TV (tt0463398)
																'co0151333', # Star World (tt1826940)
																'co0420074', # Gerth Medien (tt9471404)
																'co0360503', # Yahoo (tt1439629)
																'co0725641', # CJ ENM Co. (tt1486217)
																'co0174662', # Acorn Media (tt2303687)
																'co0463759', # Acorn TV (tt15233564)
																'co0203932', # Time Life Music (tt0094582)
																'co0231124', # BBC Drama Productions (tt2733252)
																'co0000869', # Starz (tt4189022)
																'co0118313', # Fabulous Films (tt2211129)
																'co0099385', # ABC International (tt7242816)
																'co0494442', # KRO-NCRV (tt5830254)
																'co0685539', # BritBox (tt12369754)
																'co0715422', # Quibi (tt10681780)
																'co0511943', # Proximus (tt23458434)
																'co0245229', # New KSM (tt5583512)
																'co0229287', # OWN: The Oprah Winfrey Network (tt4419214)
																'co0119714', # Rooster Teeth Productions (tt3066242)
																'co0359809', # Fernsehjuwelen (tt8983318)
																'co0196912', # Veranda Entertainment (tt1554369)
																'co0038987', # ZDF Enterprises (tt7150060)
																'co0226227', # Comedy Central Deutschland (tt5648202)
																'co0353891', # BYUtv (tt8602408)
																'co0890276', # Vergina TV (tt3232262)

																#'co0013526', # Yleisradio (YLE) (tt9174582) - Do not add for tt5834204.
															],
														},
														Media.Movie	: {
															'disallow' : [
																'co0381648', # Hulu Japan
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},

																'co0198457', # Universal Pictures International (UPI) (tt18925334)
																'co0484138', # NOS Audiovisuais (tt11389872)
																'co0271257', # Feelgood Entertainment (tt9764362)
																'co0000689', # Odeon (tt0133152)
																'co0314034', # Forum Hungary (tt9100018)
																'co0060306', # Lionsgate Films (tt0348333)
																'co0232782', # Cinéart (tt8613070)
																'co0047778', # Columbia TriStar Film Distributors (tt0181852)
																'co0213829', # Nordisk Film Distribution (tt10288566)
																'co0064766', # C.B. Films S.A. (tt0104868)
																'co0427244', # Vertical Entertainment (tt21222462)
																#'co0041517', # Touchstone Home Video (tt0146882). Part of Disney.
																'co0087338', # Kinepolis Film Distribution (KFD) (tt0116778)
																'co0059995', # Warner Home Vídeo (tt0121164)
																'co0027719', # Filmax (tt10399608)
																'co0011489', # Turner Classic Movies (TCM) (tt0103596)
																'co0079450', # New Line Home Video (tt0060386)
																'co0089127', # Magnetic Video (tt0065462)
																'co0057299', # Abril Vídeo (tt0067065)
																'co0015327', # Kommunenes Filmcentral (KF) (tt0105812)
																'co0292909', # Lionsgate Home Entertainment (tt0107387)
																'co0006451', # Roadshow Home Video (tt0102307)
																'co0001850', # Columbia TriStar Home Video (tt0281322)
																'co0024325', # Dutch FilmWorks (DFW) (tt0970472)
																'co0077442', # MTI Home Video (tt0861772)
																'co0167266', # Magnolia Home Entertainment (tt1185418)
																'co0158822', # IndieFlix (tt1311031)
																'co0296083', # Green Apple Entertainment (tt1415256)
																'co0041475', # EuroVideo (tt2149360)
																'co0000125', # Sunfilm Entertainment (tt1934458)
																'co0137851', # Sony Pictures Home Entertainment (tt1311071)
																'co0124425', # Alive Vertrieb und Marketing (tt2298224)
																'co0221717', # Lighthouse Home Entertainment (tt1810710)
																'co0166963', # Oscilloscope (tt3297554)
																'co0279341', # Redbox Automated Retail (tt3957254)
																'co0183709', # Universal Pictures International (UPI) (tt8522006)
																'co0590410', # Koch Films (tt6931658)
																'co0132923', # Dogwoof (tt25470468)
																'co0733129', # United Artists Releasing (tt11160650)
																'co0381958', # Busch Media Group (tt12982370)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0687042'],
					MetaProvider.CompanyNetwork		: ['co0218858', 'co0381648', 'co0687042', 'co0630515', 'co0588218'],
					MetaProvider.CompanyVendor		: ['co0857173'],
				},
				MetaCompany.CompanyItv : {
					# Show (3752): Level-3
					# Movie (1600): Level-3
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# ITVX Kids and CITV
																'co0984960', 'co0104833', 'co0832781', 'co0600871', 'co0662116',
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt0096657, tt1606375, tt2249364
																#{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # Not for tt0096657, tt0084987, tt0118401
																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # Not for tt0096657, tt15565872
																#{MetaCompany.CompanyFox				: [MetaProvider.CompanyNetwork]}, # Not for tt0096657, tt13589004, tt1000734
																#{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]}, # Not for tt0096657
																#{MetaCompany.CompanyCartoonnet		: [MetaProvider.CompanyNetwork]}, # Not for tt0096657
																#{MetaCompany.CompanyAcorn			: [MetaProvider.CompanyNetwork]}, # Not for tt1734537, tt2249364, tt0310455, tt7801964
																#{MetaCompany.CompanySky				: [MetaProvider.CompanyNetwork]}, # Not for tt1734537
																#{MetaCompany.CompanyBbc				: [MetaProvider.CompanyNetwork]}, # Not for tt2249364, tt6131920, tt4192812, tt2396135
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # Not for tt2249364, tt3747572
																#{MetaCompany.CompanyStarz			: [MetaProvider.CompanyNetwork]}, # Not for tt11656892
																#{MetaCompany.CompanyCinemax			: [MetaProvider.CompanyNetwork]}, # Not for tt1831575, tt0105977
																#{MetaCompany.CompanyShowtime			: [MetaProvider.CompanyNetwork]}, # Not for tt1000734
																#{MetaCompany.CompanyMgm				: [MetaProvider.CompanyNetwork]}, # Not for tt9642982, tt11716756, tt15565872
																#{MetaCompany.CompanyPeacock			: [MetaProvider.CompanyNetwork]}, # tt1266020. Not for tt1606375
																#{MetaCompany.CompanyAe				: [MetaProvider.CompanyNetwork]}, # tt0063869. Not for tt0118401, tt0094525
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # tt1266020, tt2149175. Not studios for tt4938084. Not for tt0118401, tt2396135, tt6964748, tt15565872.

																# Not sure if these should be added, since they are produced by ITV/STV, but Apple+ Originals.
																{MetaCompany.CompanyApple				: [MetaProvider.CompanyNetwork]}, # tt21088136, tt18351584

																{MetaCompany.CompanyCw				: [MetaProvider.CompanyNetwork]}, # tt0460681, tt0397442
																{MetaCompany.CompanyAmc				: [MetaProvider.CompanyNetwork]}, # tt6156584
																{MetaCompany.CompanyUsa				: [MetaProvider.CompanyNetwork]}, # tt4158110
																{MetaCompany.CompanyFx				: [MetaProvider.CompanyNetwork]}, # tt1266020, tt2149175
																{MetaCompany.CompanyNickelodeon		: [MetaProvider.CompanyNetwork]}, # tt0206512
																{MetaCompany.CompanyBravo				: [MetaProvider.CompanyNetwork]}, # tt1411598
																{MetaCompany.CompanySyfy				: [MetaProvider.CompanyNetwork]}, # tt3148266
																{MetaCompany.CompanyHulu				: [MetaProvider.CompanyNetwork]}, # tt14531842
																{MetaCompany.CompanyAdultswim			: [MetaProvider.CompanyNetwork]}, # tt0213338

																# ITV has done co-productions with these, but there are too many non-originals.
																'co0072315', # National Broadcasting Company (NBC) (tt0934814, tt4477976, tt2243973, tt0813715, tt0758745)
																'co0070627', # CBS (tt2660806). Excludes valid ones (tt8819906).

																'co0095413', # Max (tt14586350)
																'co0754095', # HBO Max (tt11212276, tt0387199). This will incorrectly exclude tt15565872.
																'co0097248', # HD Vision Studios (tt0384766)

																'co0037052', # American Broadcasting Company (ABC) (tt0075529, tt0115369)
																'co0159275', # Fox Television Animation (tt0182576)
																'co0822480', # 20th Television Animation (tt0397306)
																'co0056447', # 20th Century Fox Television (tt0059968)
																#'co0039462', # Public Broadcasting Service (PBS). Not for tt0096657, tt1606375, tt0310455, tt4192812, tt0094525
																#'co0014456', # ARTE. Not for tt0096657, tt1831575.
																'co0038332', # DC Comics (tt3749900)
																'co0123927', # DC Entertainment (tt2771780)
																'co0005035', # Warner Bros. Television (tt5164196)
																'co0129164', # DreamWorks Animation (tt10436228)
																'co0077647', # Viacom (tt0094559)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt15353964

																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},

																'co0072315', # National Broadcasting Company (NBC)
																'co0037052', # American Broadcasting Company (ABC)
																'co0070627', # CBS
																'co0159275', # Fox Television Animation
																'co0056447', # 20th Century Fox Television
																'co0741733', # Searchlight Television
																'co0216537', # FX Productions
																'co0123927', # DC Entertainment
																'co0578069', # Marvel Entertainment Group
																'co0047120', # Marvel Entertainment
																'co0051941', # Marvel Studios
																'co0028689', # Manga Entertainment
																'co0045140', # Showcase Television
																'co0054762', # Alliance Atlantis Communications
																'co0142434', # Alloy Entertainment
																'co0129164', # DreamWorks Animation
																'co0005051', # Turner Broadcasting System (TBS)
																'co0067205', # Touchstone Television
																'co0024325', # Dutch FilmWorks (DFW)
																'co0150452', # The Weinstein Company

																'co0084832', # Cinéart (tt2278871)
																'co0072847', # Splendid Film (tt5700672)
																'co0151501', # Capelight Pictures (tt4034354, tt1470827)
																'co0138168', # Asahi Broadcasting Corporation (ABC) (tt1436045)
																'co0098537', # American Cinema Releasing (tt0080180)
																'co0339529', # Tanweer Films (tt1389127)
																'co0114002', # Madman Entertainment (tt1703148)
																'co0103694', # BBC Film (tt1227183)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0269801', 'co0103328', 'co0178626', 'co0325317', 'co0103509', 'co0271278', 'co0367108', 'co0062263', 'co0323983', 'co0551019', 'co0444635', 'co0104311', 'co0592609', 'co0824500', 'co0499176', 'co0512531', 'co0899320', 'co0693477', 'co0508070', 'co0444747', 'co0644045', 'co0518213', 'co0370371', 'co0102232', 'co0659706', 'co0836810', 'co0667771', 'co0579802', 'co0572222', 'co1060623', 'co1006968', 'co0974673', 'co0939606', 'co0898028', 'co0795301', 'co0718789', 'co0595686', 'co0435936', 'co0339733', 'co0121698', 'co0046794', 'co0423164', 'co0248792'],
					MetaProvider.CompanyNetwork		: ['co0015194', 'co0911004', 'co0356585', 'co0104833', 'co0688964', 'co0940556', 'co0165745', 'co0832896', 'co0260257', 'co0984960', 'co0832781', 'co0832898', 'co0228738', 'co0600871', 'co0533816', 'co0139023', 'co0777792', 'co0262036', 'co0225802', 'co0234812', 'co0209174', 'co0177163', 'co0122767', 'co0786320', 'co0662116', 'co0862078', 'co0836774', 'co0743872', 'co0047173', 'co0038954', 'co0661472', 'co0617637', 'co0265624', 'co0986030', 'co0916015', 'co0862080', 'co0836808', 'co0749906', 'co0732240', 'co0701469'],
					MetaProvider.CompanyVendor		: ['co0382999', 'co0195491', 'co0312028', 'co0260221', 'co0980080', 'co0276713', 'co0169176', 'co1019849', 'co0987704', 'co0945425', 'co0840012', 'co0658525', 'co0596155', 'co0592953', 'co0589309', 'co0496248', 'co0158907', 'co1066271', 'co0975815', 'co0951620', 'co0913255', 'co0735462', 'co0473492'],
				},
				MetaCompany.CompanyLionsgate : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0060306', 'co0026995', 'co0086772', 'co0006881', 'co0188462', 'co0306113', 'co0592395', 'co0857626', 'co0150906', 'co1042265', 'co1064776', 'co0888885', 'co0757364', 'co0331257'],
					MetaProvider.CompanyNetwork		: ['co0060306', 'co0179392', 'co0530439', 'co0086772', 'co0129819', 'co0807819', 'co0811073', 'co0199862', 'co0850058', 'co0165815', 'co0183764', 'co0580785', 'co0983801', 'co0732499'],
					MetaProvider.CompanyVendor		: ['co0292909', 'co0082557', 'co0292919', 'co0301387', 'co1021057', 'co1020766', 'co0292916', 'co1013271', 'co0363154', 'co1042082'],
				},
				MetaCompany.CompanyLucasfilm : {
					# Show (52): Level-5
					# Movie (75): Level-4. Most of the incorrect titles have Lucasfilm as "Thank you" or "Additional material".
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																'co0045189', # VH1 Television (tt0435578)
																'co0049595', # Shueisha (tt6532184)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyMarvel	: [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork]}, # tt3385516, tt10872600

																'co0420822', # TSG Entertainment (tt6264654)
																'co0059609', # Happy Madison Productions (tt2191701)
																'co0093810', # Marc Platt Productions (tt10640346)
																'co0739708', # Perfect World Pictures (tt8041270)
																'co0047265', # Blue Sky Studios (tt0358082)
																#'co0017902', # Pixar Animation Studios (tt0317705). Not for tt0416716, tt0427263.
																#'co0017902', # Pixar Animation Studios (tt1979376). Not for tt0416716, tt0427263.
																'co0593882', # Pixarvision (tt0317705)
																'co0080248', # Mattel (tt1979376)
																'co0073081', # Apatow Productions (tt0838283)
																'co0142678', # Relativity Media (tt1156398)
																'co0035894', # Zoetrope Studios (tt0099674)
																'co0479739', # LStar Capital (tt2120120)
																'co0194736', # Media Rights Capital (MRC) (tt1637725)
																'co0480572', # Krazy Glue (tt1490017)
																'co0163665', # Offspring Entertainment (tt0974661)
																'co0525323', # Green Hummingbird Entertainment (tt4996328)
																#'co0049348', # Touchstone Pictures (tt0371724). Not for tt4191054.
																'co0136709', # Everyman Pictures (tt0371724)
																'co0152165', # Roger Birnbaum Productions (tt0293564)
																'co0390816', # A24 (tt7014006)
																'co0210013', # Atomic Monkey (tt0371606)
																'co0127668', # Kerner Entertainment Company (tt0472181)
																'co0165439', # Neal Street Productions (tt14402146)
																'co0048322', # Jane Startz Productions (tt0113419)
																'co0093869', # Mayhem Pictures (tt10649016)
																'co0309252', # BRON Studios (tt5206260)
																'co0049006', # Learning in Focus (tt0091920)
																'co0206391', # Golan-Globus Productions (tt0095895)
																'co0652942', # Pentimento Productions (tt7133092)
																'co0188417', # Leslie Iwerks Productions (tt1059955)
																'co0090913', # Pollock Trust Fund (tt0350044)
																'co0273554', # Fury Productions (tt1623757)
																'co0088431', # World of Wonder Productions (tt1705977)
																'co0097671', # Company Films (tt2014338)
																'co0058650', # Constant Communication (tt0342275)
																'co0005002', # Barry Jossen Productions (tt0112776)
																'co0064364', # Sarabande Productions (tt0092998)
																'co0043232', # Ely Lake Films (tt0088404)
																'co0099734', # Huayi Brothers Media (tt3429014)
																'co0072275', # Arnold Leibovit Entertainment (tt0089127)
																'co0067197', # Yellow Hat Productions (tt0800191)
																'co0070117', # DPI Productions Limited (tt0278473)
																'co0022995', # 68 Limited (tt0094587)
																'co0679922', # British Broadcasting Corporation (BBC East) (tt7809982)
																'co0118163', # Optomen Television (tt1086391)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0071326', 'co0196838', 'co0243324', 'co0396757', 'co0034535', 'co0634381'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0135295', 'co0134604'],
				},
				MetaCompany.CompanyMarvel : {
					# Show (173): Level-5. Near perfect out of the box. The young kids animation that seem out of place are produced by Marvel.
					# Movie (120): Level-4. Most of the incorrect titles have Marvel as "Thank you" or "Additional material".
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																#'co0058596', # Sesame Workshop (tt0066651). Not for tt0800080.
																'co0032648', # Potterton Productions (tt0066651)
															],
														},
														Media.Movie : {
															'exclude' : [
																'co0141156', # Star Partners (tt0093693)
																'co0008429', # Loop Troop (tt2245084)
																'co0017692', # Ontario Film Development Corporation (tt2245084)
																'co0567243', # Amblin Partners (tt3581652)
																'co0323215', # Annapurna Pictures (tt6266538)
																'co0051876', # Largo International N.V. (tt0104797)
																'co0116500', # Denver and Delilah Productions (tt2139881)
																'co0215519', # Indian Paintbrush (tt1967545)
																'co0184077', # World Film Services (tt0088979)
																'co0228078', # Amblimation (tt0108526)
																'co0014288', # Stonebridge Entertainment (tt0105211)
																'co0073417', # Icon Productions (tt0107501)
																'co0021095', # Jinks/Cohen Company (tt0309530)
																'co0048806', # Academy of Television Arts and Sciences (ATAS) (tt0154129)
																'co0397226', # CNN Films (tt7689964)
																'co0208372', # Hollywood Animals (tt0101455)
																'co0078090', # Trilogy Entertainment Group (tt0109912)
																'co0012575', # Paragon Entertainment Corporation (tt0271124)
																'co0673208', # Stuntwomen (tt7018574)
																'co0259788', # Dandi Productions (tt1358484)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0047120', 'co0051941', 'co0106768', 'co0095134', 'co0249290', 'co0377521', 'co0578069', 'co0741611', 'co0761154', 'co0255123', 'co0014418', 'co0312886'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0131570', 'co0133841', 'co0013122', 'co0782734', 'co0672091', 'co0501997', 'co0310115', 'co0769644', 'co0597450', 'co0390765', 'co0345534', 'co0276246'],
				},
				MetaCompany.CompanyMgm : {
					# Show (99): Level-3, close to Level-4
					# Movie (165): Level-3
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'fixed' : [
																# Only MGM+ and Epix.
																# MGM Amazon are mostly Amazon Originals.
																# Other MGM studios/networks mostly have originals of other channels.
																'co1041306',
																'co0137531',
																'co0351819',
																'co0963655',
																'co0287003',
																'co0757549',
																'co0500325',

																# Also include MGM Television and MGM/UA Television.
																# Many of these started as MGM Originals, but are now part of other networks.
																# And they produce MGM Originals, before Epix/MGM+ became a thing.
																'co0071026',
																'co0108881',
															],
														},
														Media.Show : {
															'exclude' : [
																'co0070925', # Fox Network (tt0212671, tt4785472)
																'co0070627', # CBS (tt0052520) (previous sister channel)
																'co0598660', # CBS All Access (tt0370194, tt0353049) (previous sister channel)
																'co0072315', # National Broadcasting Company (NBC) (tt0075488, tt0057765, tt0083412)
																'co0183230', # Warner Horizon Television (tt8425532)
																'co0052980', # Showtime Networks (tt0439100)
																#'co0721120', # Disney+ (tt14263564, tt10278918). Not for tt8080122.
																'co0280908', # Timberman-Beverly Productions (tt14263564)
																'co0071326', # Lucasfilm (tt10278918)
																'co0037052', # American Broadcasting Company (ABC) (tt0092492, tt0056777, tt0057729)
																'co0981669', # Discovery Toons (tt6714408)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]}, # tt0848228
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]}, # tt0903624
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # tt8521778 (sister channel)

																'co0037052', # American Broadcasting Company (ABC) (tt1392170)
																'co0005073', # Universal Pictures (tt0111282)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0007143', 'co0071026', 'co1025982', 'co0071784', 'co0108881', 'co0351819', 'co0094507', 'co0133275', 'co1002105', 'co0033274', 'co1041306', 'co0637869', 'co0756630', 'co0137531', 'co0129775', 'co0118337', 'co0072132', 'co0014753', 'co0784982', 'co0390374', 'co0217741', 'co0054424'],
					MetaProvider.CompanyNetwork		: ['co0287003', 'co0963655', 'co0989613', 'co0757549', 'co0500325', 'co0372220', 'co0857173'],
					MetaProvider.CompanyVendor		: ['co0007143', 'co0007143', 'co0015461', 'co0001770', 'co0811496', 'co0629989', 'co0774691', 'co0241239', 'co0819129', 'co0854778', 'co0811498', 'co0812330', 'co0106028', 'co0110106', 'co0795735', 'co0847176', 'co0108601', 'co0842411', 'co0812376', 'co0071194', 'co0045081', 'co0172646', 'co0838580', 'co0815526', 'co0218708', 'co0028432', 'co0615541', 'co0373148', 'co0824157', 'co0296819', 'co0017533', 'co0834362', 'co0267112', 'co0223702', 'co0831915', 'co0813670', 'co0312972', 'co0976477', 'co0901928', 'co0892556', 'co1020459', 'co0956201', 'co0903518', 'co0431795', 'co0897318', 'co0308798', 'co0182522', 'co0877383', 'co0890175', 'co0057424', 'co0980207', 'co0864701', 'co0342528', 'co0002778', 'co0884625', 'co0842533', 'co0093679', 'co0061822', 'co0379710', 'co1002361', 'co0980535', 'co0940671', 'co0752365', 'co0713989', 'co0541388', 'co0423099', 'co1021676', 'co1011157', 'co0972214', 'co0879364', 'co0870314', 'co0845802', 'co0834722', 'co0544449', 'co0398306', 'co0373431', 'co0364999', 'co0228545', 'co0119613', 'co0959574', 'co0902145', 'co0868221', 'co0867990', 'co0867937', 'co0867936', 'co0867935', 'co0867934', 'co0867933', 'co0867931', 'co0867930', 'co0865133', 'co0865132', 'co0865131', 'co0865130', 'co0865129', 'co0864454', 'co0864453', 'co0864452', 'co0864451', 'co0811497', 'co0757306', 'co0719194', 'co0716032', 'co0663644', 'co0630394', 'co0541390', 'co0522682', 'co0399951', 'co0393210', 'co0389002', 'co0268150', 'co0259336', 'co0259336', 'co0219076', 'co0194242', 'co0099361', 'co0089126', 'co0088925', 'co0077433', 'co0049562', 'co0036731', 'co0007839'],
				},
				MetaCompany.CompanyMiramax : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0022594', 'co0761033'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0564364', 'co0567610', 'co0995068', 'co0681704', 'co0777547', 'co0990661'],
				},
				MetaCompany.CompanyMtv : {
					# Show (921): Level-4
					# Movie (618): Level-3. MTV Entertainment Studios produces some high-quality movies with other studios (Paramount, MGM, etc). But most of these are not released on MTV at all, so actually not an original.
					# Very difficult to filter, since MTV has few originals, but carries a ton of content from many other channels.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'allow' : [
																MetaCompany.CompanyFreevee, # tt0094517
															],
															'disallow' : [
																# Exclude non-US/UK/CA MTV channels, since they mostly have content from other networks.
																# Probably all MTV Originals should be listed on the US/UK/CA channels.
																'co0079817', 'co0826001', 'co0008784', 'co0007798', 'co0196833', 'co0732848', 'co0895958', 'co0164271', 'co0168324', 'co0649578', 'co0067273', 'co0544112', 'co1021416', 'co0169031',
																'co0804934', 'co0170931', 'co0963160', 'co0120556', 'co0484806', 'co0782074', 'co0893707', 'co1048003',
																'co0185136', 'co0120656', 'co0079817', 'co0110193', 'co0164112', 'co0312264', 'co0215384', 'co0476397', 'co0338315', 'co0329982',
																'co0147811', 'co0357453', 'co0288173', 'co0367666', 'co0593261', 'co0403913', 'co0092945', 'co0595428', 'co0934596', 'co0169536', 'co0939005',
																'co0142523', 'co0193440', 'co0254798', 'co0238894', 'co0895958', 'co0482778', 'co0256098', 'co0199873', 'co0142524', 'co1049500', 'co0015808', 'co0190708',
																'co0233926', 'co0398445', 'co0188755', 'co0499551', 'co0188430', 'co0938465', 'co0781615',
																'co0526986', 'co0963395', 'co0478015', 'co0514535',
																'co0189546',
															],
														},
														Media.Show : {
															Media.Unknown : {
																'disallow' : [
																	# Do not include this, since it produces a lot of content for Paramount+ and Showtime, not MTV originals, and not even broadcasted on MTV.
																	'co0849655', # MTV Entertainment Studios
																],
															},
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt3921180, tt3484274, tt0176095, tt0489598, tt0426738, tt1567432, tt0176095, tt1051220
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # Not for tt0290983, tt1051220
																#{MetaCompany.CompanyCbs				: [MetaProvider.CompanyNetwork]}, # Not for tt0176095, tt1820166, tt7686456, tt1563069, tt0305011
																#{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]}, # Not for tt1820166, tt0292861
																#{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # Not for tt3484274, tt1567432, tt1051220
																#{MetaCompany.CompanyCartoonnet		: [MetaProvider.CompanyNetwork]}, # Not for tt0465344, tt1145872
																#{MetaCompany.CompanyNickelodeon		: [MetaProvider.CompanyNetwork]}, # Not for tt0118298
																#{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # Not for tt0361227, tt1820166, tt1344970, tt0264263, tt1563069
																#{MetaCompany.CompanyChannel4			: [MetaProvider.CompanyNetwork]}, # Not for tt0306370
																#{MetaCompany.CompanyChannel5			: [MetaProvider.CompanyNetwork]}, # Not for tt0395891, tt3186162, tt1567432, tt1051220
																#{MetaCompany.CompanyHayu				: [MetaProvider.CompanyNetwork]}, # Not for tt1563069
																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # Not for tt0305011
																#{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # Not for tt0305011, tt0111873, tt0292861, tt0208616
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # Not for tt3186138, tt0290983, tt3186138
																#{MetaCompany.CompanyFacebook			: [MetaProvider.CompanyNetwork]}, # Not for tt0103520
																#{MetaCompany.CompanyItv				: [MetaProvider.CompanyNetwork]}, # Not for tt1292967
																#{MetaCompany.CompanySky				: [MetaProvider.CompanyNetwork]}, # Not for tt1051220
																#{MetaCompany.CompanyMgm				: [MetaProvider.CompanyNetwork]}, # Not for tt1567432

																{MetaCompany.CompanyCw				: [MetaProvider.CompanyNetwork]}, # tt0397442
																#{MetaCompany.CompanySyfy				: [MetaProvider.CompanyNetwork]}, # tt0118276. Not for tt1051220.

																#'co0077647', # Viacom. Not for tt0208614, tt0111873, tt0101134, tt0112065.
																#'co0053846', # Spike. Not for tt1051220.
																'co0901457', # SkyShowtime (tt16358384, tt11712058) (sister channel)

																'co0037052', # American Broadcasting Company (ABC) (tt0285403, tt1441109, tt0053502)
																'co0072315', # National Broadcasting Company (NBC) (tt0285403, tt0094574, tt0060010)

																'co0020963', # Darren Star Productions (tt8962124)
																'co0215791', # Varsity Pictures (tt1344204)
																'co0039940', # FUNimation Entertainment (tt0213338, tt0138919)
																'co1000699', # Peppa Pig (tt0426769)
																'co0044395', # Nickelodeon Animation Studios (tt0101178)
																'co0541819', # Studio MDHR (tt0386180)
																'co0077535', # The WB Television Network (tt0118276)
																'co0077924', # Discovery Communications (tt1885560)
															],
														},
														Media.Movie : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTbs			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																#{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]}, # tt15486810
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},

																'co0024325', # Dutch FilmWorks (DFW) (tt1306980)
																'co0158853', # 21 Laps Entertainment (tt2222042)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0066916', 'co0849655', 'co0034438', 'co0149533', 'co0001660', 'co0079817', 'co0008784', 'co0174093', 'co0086778', 'co0054176', 'co0753138', 'co0268131', 'co0007798', 'co0032412', 'co0452480', 'co0509399', 'co0461358', 'co0174753', 'co0649578', 'co0544112', 'co0164271', 'co0895958', 'co0269523', 'co1021416', 'co0943653', 'co0924598', 'co0826001', 'co0732848', 'co0359673', 'co0348760', 'co0338192', 'co0226989', 'co0196833', 'co0169031', 'co0168324', 'co0158087', 'co0108413', 'co0067273'],
					MetaProvider.CompanyNetwork		: ['co0023307', 'co0066916', 'co0185136', 'co0120656', 'co0170931', 'co0149533', 'co0079817', 'co0074952', 'co0005971', 'co0142523', 'co0753138', 'co0963160', 'co0499552', 'co0164112', 'co0110193', 'co0312264', 'co0215384', 'co0197096', 'co0193440', 'co0149831', 'co0833608', 'co0189216', 'co0120556', 'co0476397', 'co0254798', 'co0210232', 'co0749671', 'co0338315', 'co0329982', 'co0526986', 'co0963395', 'co0357453', 'co0147811', 'co0557951', 'co0288173', 'co0283024', 'co0238894', 'co0233926', 'co0895958', 'co0887610', 'co0804934', 'co0790620', 'co0482778', 'co0367666', 'co0256098', 'co1048003', 'co1021416', 'co0939005', 'co0934596', 'co0893707', 'co0782074', 'co0692922', 'co0595428', 'co0593261', 'co0514535', 'co0499551', 'co0484806', 'co0478015', 'co0403913', 'co0398445', 'co0375670', 'co0338237', 'co0268026', 'co0264230', 'co0199873', 'co0190708', 'co0189546', 'co0189533', 'co0188755', 'co0188430', 'co0169536', 'co0142524', 'co0092945', 'co0015808', 'co1049500', 'co0938465', 'co0781615', 'co0628441', 'co0531814'],
					MetaProvider.CompanyVendor		: ['co0295362', 'co0878591', 'co0872843', 'co0606143', 'co0122521', 'co0873365', 'co0817756', 'co0817583', 'co0625916', 'co0502802', 'co0350566', 'co0252808', 'co0046412', 'co0171600'],
				},
				MetaCompany.CompanyNationalgeo : {
					# Show (845): Level-4
					# Movie (1109): Level-4
					# NatGeo is relatively accurate from the start, without too many exclusions.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# Nat Geo Toons (tt6710836, tt6348126, tt1447487, tt18554728)
																'co1004777',
																'co1044140',
																'co1020472',
																'co1020838',
																'co1020525',
																'co1020527',

																# Nat Geo Kids (tt4346362, tt5200330)
																'co0184091',
																'co0781136',
																'co0713969',
															],
														},
														Media.Show : {
															'exclude' : [
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # tt0386950
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]}, # tt6840134

																'co0039462', # Public Broadcasting Service (PBS) (tt0106172, tt0083452)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # tt27837467
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # tt12262116
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]}, # tt0333766
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]}, # tt0420223
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]}, # tt0120901
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]}, # tt0120901
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyStudio]},

																'co0039462', # Public Broadcasting Service (PBS) ()
																'co0026841', # United Artists (tt0310793)
																'co0022594', # Miramax (tt0145547)
																'co0060306', # Lionsgate Films (tt0258273)
																'co0047947', # Kino International (tt1124052)
																'co0002318', # First Run Features (tt2467442)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0005084', 'co0056555', 'co0624013', 'co0203553', 'co0459291', 'co0512191', 'co0145734', 'co0649860', 'co0272910', 'co0184091', 'co0965804', 'co0925467', 'co0863016', 'co0335470', 'co0176729', 'co1001450', 'co0916743', 'co0871114', 'co0846485', 'co0647865', 'co0282842', 'co0235837', 'co0213988', 'co0204659', 'co0943055', 'co0748068'],
					MetaProvider.CompanyNetwork		: ['co0139461', 'co0005084', 'co0056555', 'co0286617', 'co1004777', 'co0170411', 'co0376245', 'co0282022', 'co0279494', 'co0040897', 'co0781136', 'co0459291', 'co0130013', 'co0303924', 'co0097694', 'co0645043', 'co0410009', 'co0875566', 'co0649860', 'co0638684', 'co0381565', 'co1044140', 'co0468870', 'co0223788', 'co0217749', 'co0139462', 'co0530592', 'co0965804', 'co0782472', 'co0606234', 'co0243269', 'co0886585', 'co0882848', 'co0863016', 'co0735946', 'co0713969', 'co0369810', 'co0224810', 'co1058738', 'co1020838', 'co1020527', 'co1020525', 'co1020472', 'co1001450', 'co0983810', 'co0965465', 'co0930019', 'co0916743', 'co0879628', 'co0846485', 'co0792207', 'co0546833', 'co0474480', 'co0204659', 'co0195887', 'co0965214', 'co0943055', 'co0748068', 'co0648039'],
					MetaProvider.CompanyVendor		: ['co0223903', 'co0479685', 'co0273006', 'co0195888', 'co0088666', 'co0975541', 'co0874431', 'co0815045', 'co0814599', 'co0694343', 'co0544568', 'co0453441', 'co0421612', 'co0347855', 'co0334531', 'co0300041', 'co0272951', 'co0824877', 'co0694600', 'co0687580', 'co0290280', 'co0272982', 'co0272950'],
				},
				MetaCompany.CompanyNbc : {
					# Show (2396): Level-3
					# Movie (2707): Level-2
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'fixed' : MetaProvider.CompanyNetwork,
															'exclude' : [
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # do not add for tt0203259.
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},

																'co0580785', # Lions Gate Entertainment (tt6394270)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0072315', 'co0129175', 'co0022762', 'co0195910', 'co0095173', 'co0065874', 'co0048970', 'co0009465', 'co0242700', 'co0851289', 'co0216142', 'co0066042', 'co0857626', 'co0733397', 'co0059726', 'co0284326', 'co0187587', 'co0608727', 'co0485242', 'co0242277', 'co0114840', 'co0112163', 'co0111876', 'co0947572', 'co0865080', 'co0809813', 'co0756108', 'co0738026', 'co0726999', 'co0649559', 'co0574746', 'co0518674', 'co0376914', 'co0368618', 'co0147867', 'co0147866', 'co0046728', 'co1048379'],
					MetaProvider.CompanyNetwork		: ['co0072315', 'co0135684', 'co0147812', 'co0588377', 'co0196211', 'co0216142', 'co0046828', 'co0071577', 'co0854498', 'co0622734', 'co0261403', 'co0197667', 'co0015493', 'co0003209', 'co0816726', 'co0704497', 'co0758126', 'co0893655', 'co0889394', 'co0637717', 'co0616374', 'co0213416', 'co0093506', 'co0814736', 'co0260407', 'co0054488'],
					MetaProvider.CompanyVendor		: ['co0131785', 'co0203432', 'co0108351', 'co0014503', 'co0474968', 'co0672698', 'co0459508', 'co0373481', 'co0800079', 'co0068602', 'co0240399', 'co0203354', 'co0211414', 'co0945036', 'co0345290', 'co0198120', 'co0196214', 'co0839122', 'co0722053', 'co0443630', 'co0387785', 'co0302702', 'co0256170', 'co0775963', 'co0763972', 'co0537229', 'co0468247', 'co0384687', 'co0315124', 'co0306219', 'co0219279', 'co0051472', 'co0879192', 'co0852261', 'co0763971', 'co0728905', 'co0610705', 'co0514291', 'co0354562', 'co0219254', 'co0219220', 'co0154456', 'co1067279', 'co1021678', 'co0992783', 'co0976901', 'co0958317', 'co0926779', 'co0926776', 'co0925618', 'co0922214', 'co0918373', 'co0879183', 'co0871957', 'co0857116', 'co0731677', 'co0672689', 'co0655265', 'co0610076', 'co0608727', 'co0607404', 'co0537945', 'co0537942', 'co0517613', 'co0508202', 'co0488771', 'co0452922', 'co0435778', 'co0416933', 'co0416000', 'co0384730', 'co0338179', 'co0233867', 'co0127161', 'co0123321', 'co0101920', 'co0099445', 'co0093287', 'co0075133', 'co1042083', 'co1042082', 'co0993178', 'co0916077', 'co0868952', 'co0793937', 'co0793935', 'co0638541', 'co0557651', 'co0403386', 'co0271452', 'co0229385', 'co0215788'],
				},
				MetaCompany.CompanyNetflix : {
					# Show (2805 of 913+): Level-4. A lot of other originals appear on Netflix, and a few Netflix originals appear on other platforms.
					# Movie (3508 of 600+): Level-4. Relatively accurate movie originals.
					# Numbers might be far off, since many of the international, smaller, and non-direct Netflix originals are not included.
					# https://en.wikipedia.org/wiki/Category:Netflix_original_programming
					# https://en.wikipedia.org/wiki/Lists_of_Netflix_original_films
					# https://en.wikipedia.org/wiki/List_of_Netflix_original_programming
					# https://en.wikipedia.org/wiki/List_of_Netflix_exclusive_international_distribution_TV_shows
					# https://en.wikipedia.org/wiki/List_of_Netflix_exclusive_international_distribution_films
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'language' : [
																{Language.CodeIndian : ['co0944055']},
															],
														},
														Media.Show : {
															'allow' : [
																'co0052980', # Showtime Networks (tt11016042)
																'co0374625', # Sky Atlantic HD (tt1856010)
																'co0103528', # Channel 4 Television Corporation (too much other content listed here that too many titles might be excluded with CH4 networks).
															],
															'exclude' : [
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]}, # Excludes tt6156584 which is a Netflix Original.
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]}, # Excludes tt6156584 which is a Netflix Original.
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt9055008 is a Paramount+ original, but also on Netflix.
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # tt11650492 is a Netflix Original, but also on Peacock.
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # Excludes tt6156584 which is a Netflix Original.
																{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanySky			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyMtv			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAubc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyAcorn			: [MetaProvider.CompanyNetwork]}, # tt0106148
																#{MetaCompany.CompanyBbc			: [MetaProvider.CompanyNetwork]}, # Do not add for tt28118211.
																#{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]}, # tt1548850. Do not add for tt6257970, a Netflix Original, but also on Channel 4.
																#{MetaCompany.CompanyPluto		: [MetaProvider.CompanyNetwork]}, # Do not add for tt2707408.
																#{MetaCompany.CompanyUniversal	: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},

																'co0684443', # Viu
																#'co0332053', # tvN - Do not add for tt27668559.
																#'co0120210', # Tokyo MX - Do not add for tt21621494.
																'co0035005', # AT-X
																'co0052417', # NHK
																'co0003850', # Nippon Television Network (NTV)
																#'co0493506', # iQIYI (CN) - Do not add for tt3520702.
																'co0032922', # Hallmark Channel (US)
																'co0096347', # DirecTV (US)

																'co0023845', # A&E Home Video (tt0202477)
																'co0077046', # Viz Video (tt0482107)
																'co0024325', # Dutch FilmWorks (DFW) (tt2234222)
																'co0844260', # Ertflix (tt2294189)
																'co0016164', # Channel 3 (tt30176429)
																'co0033381', # Mega Channel (tt16447750)
																'co0018288', # Seoul Broadcasting System (SBS) (tt14819828)
																'co0061335', # Super Channel (tt4667888)
																'co0201022', # Ovation (tt3830558)
																'co0686547', # TRT 1 (tt4320258)
																'co0845675', # Tving (tt26693803, tt14596486)
																'co0039462', # Public Broadcasting Service (PBS) (tt8001092)
																'co0321187', # Yesterday (tt0072500)
																'co0159433', # ATV (tt1534360, tt3565486)
																'co0963208', # Universum Film Home Entertainment (tt0108800)
																'co0633150', # Peppermint Anime (tt3742982)
																'co0229287', # OWN: The Oprah Winfrey Network (tt4971144)
																'co0230162', # Reel DVD (tt2309295)
																'co0046530', # Independent Film Channel (IFC) (tt1780441)
																'co0055529', # Fuji Television Network (tt2379308)
																'co0012955', # Edel Media & Entertainment (tt4277922)
																'co0040657', # Canal J (tt26692417)
																'co0356404', # Showcase Australia (tt4976512)
																'co0137851', # Sony Pictures Home Entertainment (tt1548850)
															],
														},
														Media.Movie : {
															'allow' : [
																'co0002663', # tt13274016
																'co0005073', # tt2737304
																'co0054597', # tt8106534
																'co0072831', # tt8106534
																'co0847351', # tt3447590
																'co0026545', # tt3447590
																'co0086397', # tt9243946
																'co0332012', # tt9243946
																'co0769046', # tt9243946
																'co0000756', # tt12823454
															],
															'exclude' : [
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # tt26744289, tt0156887
																{MetaCompany.CompanyTubi			: [MetaProvider.CompanyNetwork]}, # tt1670345
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # tt5913798
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # tt1139592
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]}, # tt8367814
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]}, # tt1706620, tt2404233, tt1649419
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]}, # tt3460252
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]}, # tt4857264
																#{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]}, # tt11057302, tt12593682, tt0087538 - Do not add, since there are too many Sony music/production companies under vendors (tt7979580, co0086397, co0026545).

																'co0137851', # Sony Pictures Home Entertainment (tt11057302, tt12593682, tt0087538) Will still exclude tt7979580.
																'co0208736', # Sony Pictures Worldwide Acquisitions (SPWA) (tt7014006)
																'co0137851', # Sony Pictures Home Entertainment (tt11057302, tt12593682, tt0087538)
																'co0873390', # Sony Pictures Releasing (tt14668630)
																'co0575132', # Peppermint Enterprises (tt23289160)
																'co0427244', # Vertical Entertainment (tt9271850)
																'co0156943', # Tiberius Film (tt4281724)
																'co0391285', # StudioCanal Germany (tt8310486)
																'co0015762', # IFC Films (tt1467304)
																#'co0102291', # Ascot Elite Entertainment Group (tt9243804) - Do not add for tt1649418.
																#'co0238173', # Front Row Filmed Entertainment (tt9243804) - Do not add for tt13651794.
																'co0006290', # Telepool (tt9243804)
																'co0749314', # Acemaker Movieworks (tt31254554)
																'co0005849', # The Klockworx (tt8228288)
																'co0021661', # Universum Film (UFA) (tt5073620, tt4975722, tt3522806, tt1772264)
																'co0249327', # SF Studios (tt22016156)
																'co0246047', # Viacom18 (tt13818368)
																'co0603957', # GEM Entertainment (tt8633478)
																#'co0000689', # Odeon (tt0156887) - Do not add for tt1649418.
																'co0122766', # Umbrella Entertainment (tt8368406)
																'co0079450', # New Line Home Video (tt0427327)
																'co0124425', # Alive Vertrieb und Marketing (tt8359848)
																#'co0022869', # Pathé (tt20221436) - Do not add for tt8337264.
																'co0742621', # Vyre Network (tt7057496)
																#'co0132285', # Aniplex (tt11032374) - Do not add for tt6660498.
																#'co0002219', # Toho (tt11032374) - Do not add for tt16369708.+
																'co0834114', # Vidio (tt11032374)
																'co0906551', # Paramount Global (tt25869142)
																'co0453070', # FilmRise (tt4129870)
																'co0024325', # Dutch FilmWorks (DFW) (tt1139328)
																'co0809670', # Great Movies Distribution (tt10431500)
																'co0298561', # Nordisk Film Distribution (tt13109952)
																'co0016059', # Ascot Elite Home Entertainment (tt0440803)
																'co0192258', # Paradiso Entertainment (tt14308636)
																'co0002171', # Evangelische Omroep (EO) (tt10521092)
																'co0011466', # Antenna Entertainment (tt28454007)

																# Not needed anymore, since we now do not include "NetFlix India" anymore.
																# Some are only listed under the normal "Netflix", but a few Hindi titles is not the end.
																'co0237670', # Phars Film (tt13927994, tt26548265)
																'co0149420', # Suraya Filem (tt27744786)
																'co0766492', # Friday Entertainment (tt21383812, tt18072316)
																#'co0077190', # Yash Raj Films (tt18072316). Do not add for tt4501268.
																#'co0450251', # Night Ed Films (tt13751694)
																#'co0692549', # Zee5 (tt15181064)
																#'co0130302', # Filmfreak Distributie (tt1954470)
																#'co0328195', # Viacom18 Motion Pictures (tt8108198)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0650527', 'co0743375', 'co0933900', 'co0825975'],
					MetaProvider.CompanyNetwork		: ['co0144901', 'co0944055'],
					MetaProvider.CompanyVendor		: ['co0144901', 'co0944055', 'co0805756', 'co0950660', 'co1048172', 'co0803020'],
				},
				MetaCompany.CompanyNewline : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0046718', 'co0043853', 'co0001803', 'co0002753', 'co0765072', 'co0421859'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0079450', 'co0228937', 'co0098273', 'co0042275', 'co0225343', 'co0497163', 'co0346875'],
				},
				MetaCompany.CompanyNickelodeon : {
					# Show (950): Level-3
					# Movie (248): Level-3
					# Do not exclude Paramount+, Netflix, Discovery Toons, MTV, Stan, Shout! Factory, CBS (Do excldue CBS, even as a sister channel, otherwise too many false positives)
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# Nick at Night. Too many adult stuff, NBC re-runs, and other false positives (tt0069632, tt0090444).
																'co0154874', 'co0184885', 'co1053065',
															],
															'exclude' : [
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyStudio]}, # tt0088580

																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Not for tt9018736.
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCartoonnet	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAdultswim		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]}, # tt0121955

																'co0086397', # Sony Pictures Television (tt0098904, tt0118300)
																'co0059995', # Warner Home Video (tt6226232)
																'co0072315', # National Broadcasting Company (NBC) (tt0098904, tt0083399, tt0083413, tt0047708)
																'co0037052', # American Broadcasting Company (ABC) (tt0411024)
																'co0077535', # The WB Television Network (tt0075596)
																'co0041442', # Columbia Pictures Television (tt0090418)
																'co0070627', # CBS (tt0054533, tt0053525, tt0065314)
																'co0213225', # Disney-ABC Domestic Television (tt0108949)
															],
														},
														Media.Show : {
															'exclude' : [
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]}, # tt12412888
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyStudio]}, # tt1055369

																#'co0023400', # Paramount Pictures (tt14001894) (parent company). Not for tt25289836.
																'co0026281', # Jerry Bruckheimer Films (tt14001894)
																'co0307036', # Sony Pictures Releasing International (SPRI) (tt11762114)
																'co0814477', # Universal Pictures Home Entertainment (tt0790724)
																'co0024325', # Dutch FilmWorks (DFW) (tt0200465)
																#'co0122766', # Umbrella Entertainment (tt7392014). Not for tt0206512.
																'co0015762', # IFC Films (tt7392014)
																'co0000689', # Odeon (tt6199572)
																'co0019532', # Kinowelt Home Entertainment (tt0110598)
																'co0058792', # Roadshow Films (tt1648186)
																'co0152990', # Roadshow Entertainment (tt0039152)
																'co0072847', # Splendid Film (tt1456941)
																'co0031085', # Argentina Video Home (tt0273923)
																'co0380492', # Good Universe (tt7374948)
																'co0113964', # Reel Media International (tt0034928, tt0039698, tt0040626)
																'co0103510', # British Lion Films (tt0050456)
																'co0062107', # Toei Animation (tt0142243, tt0142247)
																'co0063490', # World Northal (tt0078324)
																'co0993734', # Renaissance Content Group (tt0191774)
																'co0069337', # Filmways Australasian Distributors (tt0086591)
																'co0017254', # Alpha Video Distributors (tt0024768)
																'co0241677', # Schröder Media (tt0079532)
																'co0002219', # Toho (tt1344095)
																'co0026841', # United Artists (tt0031535, tt0229797, tt0028872)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0044395', 'co0011615', 'co0004265', 'co0078560', 'co0652791', 'co0093767', 'co0130123', 'co0090721', 'co0888450', 'co0858405', 'co0298878', 'co0516455'],
					MetaProvider.CompanyNetwork		: ['co0007546', 'co0031641', 'co0106182', 'co0167426', 'co0301237', 'co0465477', 'co0154874', 'co0467568', 'co0698648', 'co0164662', 'co0893565', 'co0249384', 'co0040603', 'co0492047', 'co0184885', 'co0492991', 'co0295362', 'co0469424', 'co1073978', 'co1028177', 'co1017467', 'co0851270', 'co0385703', 'co0990497', 'co0513608', 'co0397805', 'co0421170', 'co0328444', 'co0300565', 'co1070844', 'co1040835', 'co0981291', 'co0874875', 'co0577889', 'co1072030', 'co1070495', 'co1053067', 'co1053065', 'co1053063', 'co0874876', 'co0479262', 'co1074587', 'co0912620', 'co0847982', 'co0843315', 'co0672931', 'co0539580', 'co0329703', 'co0296940'],
					MetaProvider.CompanyVendor		: ['co0741051', 'co0216996', 'co1049678', 'co0896623', 'co0619583', 'co0472950', 'co0280606'],
				},
				MetaCompany.CompanyParamount : {
					# Show (227 of 121+): Level-4. A lot of other originals appear on Paramount+, and many Paramount originals appear on other platforms. Many shared content.
					# Movie (121 of 43+): Level-4.
					# https://en.wikipedia.org/wiki/Category:Paramount%2B_original_programming
					# https://en.wikipedia.org/wiki/Category:Paramount%2B_original_films
					# Many Paramount+ Originals also get released on Netflix, Amazon, Apple, Disney, etc.
					# Hence, excluding any of these competitors will remove too many titles.
					# Also do not include studios, since some, like Paramount Television, produce some titles that are not even released on Paramount+.
					# Try to exclude as many CBS and Nickelodeon titles as possible (both owned by Paramount).
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'fixed' : MetaProvider.CompanyNetwork,
															'disallow' : [
																# Do not add TNN and Spike TV, since they contain way too many titles that are not Paramount Originals.
																# Do not exclude, since some Paramount Originals are on Spike as well (eg tt0092455).
																'co0465238',
																'co0046264',
																'co0027042',
																'co0985255',
																'co0053846',
																'co0533814',
																'co0099482',
																'co0926308',
																'co0673785',
																'co0456008',
																'co0465238',
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Do not add for tt9055008.
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Do not add for tt13991232.
																#{MetaCompany.CompanyApple		: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # Do not add for tt0452046 produced by ABC.
																#{MetaCompany.CompanySky			: [MetaProvider.CompanyNetwork]}, # Do not add for tt11712058, tt16358384.

																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyStudio]},
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyStudio]}, # tt8819906. Do not add for tt8806524.
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyStudio]},

																#{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # tt8819906. Do not add for tt4236770.
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]}, # tt0098936
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]}, # tt0106004
																#{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]}, # tt0286486. Do not add for tt0364845.
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt0115167

																# Owned by Paramount, but too many Nickelodeon titles clutter the menu.
																#{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyStudio]}, # tt1877889, tt2712516. Do not add for tt13657062, tt9795876.

																'co0011615', # Nickelodeon Productions (tt2712516)
																'co0577889', # Nickelodeon Games and Sports for Kids (tt0101190)
																'co0652791', # Nick Jr. Productions (tt9000424)
																'co0093767', # Nicktoons Productions (tt0235916)
																'co0301237', # Nick Jr. (tt10558660)
																'co0249384', # Nick Jr. (tt9433014)
																'co0467568', # TeenNick (tt2545498)

																'co0137851', # Sony Pictures Home Entertainment (tt0903747, tt0286486)
																'co0769046', # Sony Pictures Home Entertainment (tt0428167)
																'co0019701', # American Movie Classics (AMC) (tt1520211)
																'co0815501', # AMC+ (tt13062500)
																'co0195106', # AXN (tt0773262)
																'co0143765', # AXN (tt14218674)
																'co0186281', # AXN (tt4280606)
																'co0316481', # 13th Street Universal (tt0773262).
																'co0066335', # 13th Street (tt5827228, tt14449470).
																'co0963655', # MGM+ (tt9813792)
																'co0010224', # 20th Century Fox Home Entertainment (tt0106179, tt1124373)
																'co0077535', # The WB Television Network (tt0158552)
																'co0981669', # Discovery Toons (tt0417299)
																'co0151501', # Capelight Pictures (tt1567432)
																'co0018439', # Vrijzinnig Protestantse Radio Omroep (VPRO) (tt14164730)
																'co0305757', # Universal Channel (tt1595859)
																'co0227561', # Universal Channel (tt1442462)
																'co0440561', # Universal Channel (tt9252156)
																'co0051618', # Entertainment One (tt11041332)
																'co0013585', # Image Entertainment (tt0052520)
																'co0009512', # TNT (tt7491982)
																'co0909338', # Warner TV Serie (tt1378167)
																'co0136706', # Canvas (tt14586544)
																'co0803818', # Binge (tt18228732)
																'co0203432', # CNBC-e (tt0972534, tt0851851)
																'co0123437', # Viasat3 (tt3560084)
																#'co0037417', # M6 (tt14218674). Do not add for tt9054904.
																'co0061229', # Seven Network (tt7949212)
																'co0200391', # ION Television (tt1399045)
																#'co0005073', # Universal Pictures (tt1604099). Do not add for tt5853176.
																'co0104833', # Children's Independent Television (CiTV) (tt1604099)
																'co0395016', # VIER (tt3514324)
																'co0002402', # United American Video (tt0053479)
																'co0082557', # Lions Gate Films Home Entertainment (tt1344204)
																'co0024077', # ARD (tt0060009)
																#'co0894072', # RTL+ (tt12887536). Do not add for tt0092455.
																'co0488702', # Viaplay (tt12887536)
																'co0592609', # ITV Entertainment (tt8819906)
																'co0087314', # Warner Home Video (tt1051220)
																'co0376245', # National Geographic Channel (NGC) (tt0386950)
																'co0001861', # Viva (tt1877889)
																'co0259754', # Gulli (tt4859164)
																'co0255518', # Magic Rock Productions (tt5639976)
																'co0005035', # Warner Bros. Television (tt10329024). Also excludes tt6226232.
																#'co0879800', # Google Play (tt7187044). Do not add for tt13991232.
																'co0951662', # Fifth Season (tt7187044).
																'co0039940', # FUNimation Entertainment (tt0318913).
																'co0161074', # 20th Television (tt7380366). Also excludes tt13875494.
																'co0597706', # Kidz TV (tt0415463)
																#'co0605105', # Crave (tt11173006). Do not add for tt5171438.
																'co0014490', # WWOR (tt0185103)
																'co0171371', # PBS Kids (tt0163929)
																'co0362268', # WOWOW Prime (tt7712598)
																'co0909710', # TOGGO (tt4458594)
																'co0101989', # W Network (tt9755726)
																'co0850678', # The Roku Channel (tt18970320)
																'co0937862', # ARD / ZDF Kinderkanal (KIKA) (tt0329829)
																'co0030553', # Kinderkanal (KiKA) (tt14670820)
																'co0090662', # CBS News Productions (tt0123338)
																'co0011682', # CBS News (tt2163227)
																'co0695125', # ESPN+ (tt0445912)
																'co0060012', # Sony Wonder (tt0101084)
																'co0824956', # Disney Media & Entertainment Distribution (tt5210146)
																'co0015560', # Nelvana (tt0965404)
																'co0391285', # StudioCanal Germany (tt7772600)
																'co0015461', # MGM Home Entertainment (tt0129695)
																'co0269801', # ITV Studios (tt21942560)
																'co0358927', # Rovio Entertainment (tt14118188)
																'co0106229', # Challenge TV (tt0364843)
																'co0193692', # Buena Vista Home Video (tt0222518)
																'co0120568', # Six Point Harness (tt0805837)
																'co0863266', # Warner Bros. Discovery (tt21072822)
																'co0981653', # Discovery Force Channel (tt1442553)
																'co0003079', # Concorde Home Entertainment (tt3681794)
																#'co0028644', # Special Broadcasting Service (SBS) (tt13045814). Do not add for tt5853176.
																'co0107314', # Polyband (tt13045814)
																'co0005780', # Cartoon Network (tt14556544)
																'co0341953', # World Wrestling Federation (WWF) (tt0261495)
																'co0176403', # My Network TV (tt1128727)
																'co0074079', # THQ (tt0853078)
																'co0304322', # Sixx (tt2209649)

																'co0204971', # Magnet Pictures (tt0177444)
																'co0049961', # Mirage Studios (tt6601082)
																'co1010899', # WOW Presents Plus (tt21650372)
																'co0881337', # Stack TV (tt11055882)
																'co0798745', # QUBO. (tt0078714)
																'co0006294', # In Demand (tt0818464)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # tt10399608
																{MetaCompany.CompanyRoku			: [MetaProvider.CompanyNetwork]}, # tt17076046
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]}, # tt0063518
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt0065597
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt9603212, tt1745960

																'co0011615', # Nickelodeon Productions (tt2712516, tt32223312)
																'co0816712', # Warner Bros. Pictures (GB) (tt13097932)
																'co0795863', # Sony Pictures Home Entertainment (tt11285280)
																'co0208736', # Sony Pictures Worldwide Acquisitions (SPWA) (tt7557108)
																'co0820078', # Universal Pictures International (UPI) (tt1399103, tt0462200)
																'co0024325', # Dutch FilmWorks (DFW) (tt11540468)
																'co0351891', # Signature Entertainment (tt15771916)
																'co0190332', # RCV Film Distribution (tt0482546)
																'co0113335', # A-Film Home Entertainment (tt0896872)
																'co0049085', # Momentum Pictures (tt1519461)
																'co0314632', # Freestyle Digital Media (tt7014356)
																'co0106012', # Warner-Pathé Distributors (tt0057128)
																'co0156943', # Tiberius Film (tt11737466)
																'co0152990', # Roadshow Entertainment (tt2312862)
																'co0309225', # 101 Films (tt15304502)
																'co0275579', # Smithsonian Channel (tt2946948)
																'co0511336', # UPtv (tt5952626)
																'co0148076', # Swen Group (tt9809230)
																'co0106328', # BFI Video (tt0033406)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0023400', 'co0053559', 'co0094501', 'co0390995', 'co0179341', 'co0183875', 'co0663819', 'co0066107', 'co0781350', 'co0226970', 'co0858764', 'co0187272', 'co0641896', 'co0069040', 'co0028548', 'co0076598', 'co0942448', 'co0754886', 'co0665829', 'co0465238', 'co0245466', 'co0969494', 'co0614985', 'co0447745', 'co0445608', 'co0336713', 'co0031170', 'co0019613', 'co1027703', 'co0969496', 'co0876322', 'co0501627', 'co0499895', 'co0405466', 'co0101044', 'co0075668', 'co0834862', 'co0750721', 'co0509323', 'co0428828', 'co0334177', 'co0319948', 'co0227227', 'co0012106'],
					MetaProvider.CompanyNetwork		: ['co0820547', 'co0099482', 'co0533814', 'co0632516', 'co0046264', 'co0027042', 'co0778495', 'co0053846', 'co0777243', 'co0913243', 'co0979606', 'co0947664', 'co0985255', 'co0926308', 'co0673785', 'co0456008', 'co0865737'],
					MetaProvider.CompanyVendor		: ['co0023400', 'co0023400', 'co0051891', 'co0074341', 'co0220414', 'co0316662', 'co0754555', 'co0796240', 'co0001860', 'co0318358', 'co0094762', 'co0184442', 'co0803844', 'co0316507', 'co1022855', 'co0131790', 'co0834860', 'co0591004', 'co0011257', 'co0850646', 'co0160099', 'co0021163', 'co0034406', 'co0170466', 'co0087315', 'co0317706', 'co0819892', 'co0453999', 'co0033409', 'co0957308', 'co0822247', 'co0817261', 'co0866247', 'co0309607', 'co0086041', 'co0160703', 'co0819893', 'co0029291', 'co0198704', 'co0808354', 'co0919972', 'co0231973', 'co0135308', 'co0048343', 'co0638721', 'co0001917', 'co0097692', 'co0068790', 'co0565880', 'co0051884', 'co0573273', 'co0244783', 'co0822249', 'co0601119', 'co0817224', 'co0906551', 'co0858764', 'co0834967', 'co1044155', 'co0604098', 'co0349683', 'co0349864', 'co0349935', 'co0204503', 'co0483087', 'co0226970', 'co1061662', 'co0375685', 'co0246986', 'co0999387', 'co0793559', 'co0986034', 'co0277788', 'co0599662', 'co0521586', 'co0090065', 'co0940470', 'co0796824', 'co0739819', 'co0611782', 'co0521548', 'co1019841', 'co0749795', 'co0508924', 'co0440806', 'co0235370', 'co0052142', 'co0048308', 'co1071435', 'co1042408', 'co0943142', 'co0867803', 'co0651759', 'co0583146', 'co0349601', 'co0327798', 'co0327534', 'co0296075', 'co0254086', 'co0242103', 'co0221920', 'co0204462', 'co0138659', 'co0124108', 'co0107991', 'co0043519', 'co0039958', 'co0039221', 'co0037676', 'co0985535', 'co0963678', 'co0962134', 'co0896806', 'co0878210', 'co0877199', 'co0870433', 'co0868203', 'co0868045', 'co0848844', 'co0847151', 'co0847150', 'co0847149', 'co0834861', 'co0820546', 'co0817225', 'co0809207', 'co0807232', 'co0774810', 'co0750721', 'co0695983', 'co0689776', 'co0666792', 'co0662236', 'co0662231', 'co0662229', 'co0630473', 'co0626466', 'co0499762', 'co0334177', 'co0316667', 'co0316628', 'co0297121', 'co0267721', 'co0253584', 'co0245428', 'co0219746', 'co0210910', 'co0202723', 'co0198680', 'co0194150', 'co0151286', 'co0142091', 'co0128329', 'co0111166', 'co0076191', 'co0049835', 'co0038360', 'co0031167', 'co0028920', 'co0012106', 'co0005212', 'co0003407'],
				},
				MetaCompany.CompanyPeacock : {
					# Show (272 of 91+): Level-4.
					# Movie (165 of 18+): Level-3.
					# https://en.wikipedia.org/wiki/Category:Peacock_(streaming_service)_original_programming
					# https://en.wikipedia.org/wiki/Category:Peacock_(streaming_service)_original_films
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'allow' : [
																'co0103528', # Channel 4 Television Corporation (too much other content listed here that too many titles might be excluded with CH4 networks).
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]}, # tt10147894
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]}, # tt10474134

																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]}, # tt0050032
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]}, # tt0460637
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # tt0103396
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]}, # tt0096694
																{MetaCompany.CompanyChannel5		: [MetaProvider.CompanyNetwork]}, # tt0496424
																#{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # tt0491738. Part of NBCUniversal
																#{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork]}, # tt0759364. Do not add for tt9814116.
																#{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]}, # tt7939800. Do not add for tt10846104.
																#{MetaCompany.CompanyBbc			: [MetaProvider.CompanyNetwork]}, # tt23743442. Do not add for tt15557874.
																#{MetaCompany.CompanySky			: [MetaProvider.CompanyNetwork]}, # tt9849186, tt9454736, tt31029686. Do not add for tt9022422, tt9041792.
																#{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # Do not add for tt17371078.

																'co0203910', # AXN (tt0364828)
																'co0137851', # Sony Pictures Home Entertainment (tt0092400)
																'co0070756', # VOX (tt0106028)
																'co0112383', # RTL Entertainment (tt0058796)
																'co0080139', # CTV Television Network (tt3444938)
																'co0247505', # Citytv (tt14852960)
																'co0039462', # Public Broadcasting Service (PBS) (tt0383795)
																'co0095173', # NBC News (tt0044298)
																'co0009297', # Columbia TriStar Domestic Television (tt0086787)
																'co0292919', # Lionsgate Home Entertainment (tt2216314)
																'co0997348', # Telemundo Global Studios (tt29100757)
																'co0083950', # LBS Communications (tt0169477)
																'co0663330', # Olympic Channel (tt12747694)
																'co0030553', # Kinderkanal (KiKA) (tt0939006)
																'co0145927', # Angel Studios (tt7301292)
																'co0284996', # Life Network (tt1101009)
																'co0265997', # CBeebies (tt2021826)
																'co0179636', # Pop TV (tt15537894)
																'co0841978', # Ketchup TV (tt1423559)
																'co0938989', # NFL+ (tt0905590)
																'co0000647', # WPIX (tt21216178)
																'co0267421', # First National Pictures (II) (tt0338579)
																'co0062768', # BKN International (tt1380835)
																'co0029268', # HIT Entertainment (tt1313065)
																#'co0103644', # Tiger Aspect Productions (tt9849186). Do not add for tt9041792.
																'co0684153', # Moonage Pictures (tt9849186)
																'co0772897', # ABC Comedy (tt9454736)
																'co0611078', # Videoland (tt23743442)
																'co0487058', # Tencent Video (tt14016298)
																'co0001524', # China Central Television (CCTV) (tt16970040)
																'co0202446', # YouTube (tt20243990)
																'co0031085', # Argentina Video Home (tt0491738)
															],
														},
														Media.Movie : {
															'allow' : [
																'co0026545', # tt24429218
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]}, # tt10147894
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]}, # tt0190590
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]}, # tt10474134
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # tt26541686
																{MetaCompany.CompanyTubi			: [MetaProvider.CompanyNetwork]}, # tt0111301
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]}, # tt1679335
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]}, # tt0125664
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]}, # tt4104022
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]}, # tt0160236
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]}, # tt2062622
																#{MetaCompany.CompanySky			: [MetaProvider.CompanyVendor]}, # Do not add for tt31122323, tt24429218.
																#{MetaCompany.CompanyUniversal	: [MetaProvider.CompanyVendor]}, # tt10954984, tt21692408, tt14849194. Do not add for tt1121948. And its part of NBCUniversal.

																'co0058792', # Roadshow Films (tt4978420)
																'co0720464', # Warner Bros. Home Entertainment (tt10954984, tt21692408)
																'co0280680', # Kino Films (tt11378946)
																'co0042399', # Focus Features (tt14849194)
																'co0031085', # Argentina Video Home (tt0088847)
																'co0045926', # Columbia TriStar Home Video (tt0118715)
																'co0001850', # Columbia TriStar Home Video (tt0096256)
																'co0854530', # Studio Distribution Services (SDS) (tt0021814, tt5113044)
																'co0307036', # Sony Pictures Releasing International (SPRI) (tt6495056)
																'co0370614', # Tanweer Alliances (tt3470600, tt11358390)
																'co0044076', # The Criterion Collection (tt0120669)
																'co0024325', # Dutch FilmWorks (DFW) (tt15799866)
																'co0588627', # STAR India (tt0452594)
																'co0245399', # good movies! (tt9731598)
																'co0252368', # Huaxia Film Distribution (tt6324278)
																'co0427244', # Vertical Entertainment (tt14850544)
																'co0061607', # Videosonic (tt0027545)
																'co0268731', # Cinedigm Entertainment Group (tt2948840)
																'co0142678', # Relativity Media (tt3416670)
																'co0170439', # Columbia TriStar Home Entertainment (tt0160236)
																'co0068880', # Bridge Entertainment Group (tt0425395)
																'co0309725', # ACE Entertainment (tt6821198)
																'co0292919', # Lionsgate Home Entertainment (tt2062622)
																'co0013585', # Image Entertainment (tt1893218)
																'co0559656', # Reel One International (tt29380647, tt19850052)
																'co0467911', # GoDigital (tt2113683)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0011738', 'co0848470', 'co0848665'],
					MetaProvider.CompanyNetwork		: ['co0764707', 'co0893462', 'co0859748'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyPhilo : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0035988'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyPixar : {
					# Show (15): Level-4
					# Movie (48): Level-4. Most of the incorrect titles have Pixar as "Thank you", "Additional material", or "Studio facilities".
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																'co0331205', # Apple & Eve (tt0063951)
															],
														},
														Media.Movie : {
															'exclude' : [
																'co0016626', # Tokuma Shoten (tt0245429, tt0347149)
																'co0057311', # Working Title Films (tt3890160)
																'co0046203', # WingNut Films (tt0360717)
																'co0140271', # Christien Tinsley's Transfers Inc. (tt0401729)
																'co0091875', # Amarillo Film Office (tt0097576)
																'co0133018', # Silver Screen Partners IV (tt0101414)
																'co0985122', # Annapurna Animation (tt19500164)
																'co0010750', # Saturn Films (tt0963966)
																'co0041499', # Gentle Jungle (tt0120844)
																'co0108859', # Sean S. Cunningham Films (tt0211443)
																'co0134409', # Riff Raff Entertainment (tt0346156)
																'co0019575', # Fenton-Feinberg Casting (tt0090357)
																'co0949735', # Final Cut Partners (tt20274588)
																'co0049689', # Why Not Productions (tt3110960)
																'co0367145', # Mankiller Project (tt2182159)
																'co0489736', # Ain't Heard Nothin' Yet Corp. (tt3856408)
																'co0204251', # Salient Media (tt0949815)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0017902'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0348691', 'co0593882', 'co1070967', 'co1042473', 'co0894998', 'co0791909', 'co0087268', 'co0754045'],
				},
				MetaCompany.CompanyPluto : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0545791'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyRegency : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0007127', 'co0867908', 'co0066289', 'co0023875', 'co1007086', 'co0057227', 'co0172093'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0169144', 'co0802353'],
				},
				MetaCompany.CompanyRko : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0041421', 'co0055570', 'co1012051', 'co0103147', 'co0570527', 'co0434677', 'co0181377', 'co0063400', 'co0041353', 'co0032881', 'co0030174', 'co0015766', 'co0181770', 'co0142236'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0041421', 'co0119009', 'co0786380', 'co0786630', 'co0413144', 'co0010029', 'co0227201', 'co0134686', 'co0536351', 'co0052638', 'co0227091', 'co0232178', 'co0237410', 'co0686069', 'co0553775', 'co0217289', 'co0179449', 'co0231823', 'co0216147', 'co0187385', 'co0647480', 'co0644319', 'co0053128', 'co0787886', 'co0228093', 'co0422029', 'co0092195', 'co0786409', 'co0056735', 'co0185060', 'co0226417', 'co0800706', 'co0070644', 'co0298865', 'co0980884', 'co0878304', 'co0944451', 'co0885328', 'co0577797', 'co0530337', 'co0363180', 'co0294557', 'co0273555', 'co0228654', 'co0228057', 'co0158195', 'co0088033', 'co0937233', 'co0867874', 'co0864136', 'co0863849', 'co0863848', 'co0781567', 'co0781566', 'co0730403', 'co0727706', 'co0727473', 'co0674253', 'co0673681', 'co0671570', 'co0659060', 'co0658762', 'co0658761', 'co0522672', 'co0477404', 'co0462005', 'co0444348', 'co0413143', 'co0380711', 'co0244861', 'co0232138', 'co0231046', 'co0229874', 'co0229869', 'co0228795', 'co0228777', 'co0228660', 'co0228656', 'co0227694', 'co0227165', 'co0227029', 'co0226998', 'co0220630', 'co0218291', 'co0187074', 'co0181770', 'co0067639', 'co0047507', 'co0044939', 'co0035000'],
				},
				MetaCompany.CompanyRoku : {
					# Show (192): Level-3. There are many titles from Quibi (now Roku) and other smaller channels that might be considered Roku Originals, because the other networks are too small and unknown.
					# Movie (33): Level-3. Not many Roku Original movies exist.
					#	https://en.wikipedia.org/wiki/Category:Roku_original_programming
					#	https://en.wikipedia.org/wiki/List_of_The_Roku_Channel_original_programming
					# Only some are listed under "Roku Originals".
					# Some are not listed as Roku Originals, although Wikipedia says so (tt10726424, tt27669794, tt31945450, tt26689543).
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # tt0397442
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # tt0370194
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # tt15552018, tt0131183
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # tt14989818

																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Not for tt10580064, tt10726424.
																#{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]}, # Not for tt11460580.
																#{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]}, # Not for tt26452193.
																#{MetaCompany.CompanyTbs			: [MetaProvider.CompanyNetwork]}, # Not for tt10338160.
																#{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # Not for tt27669794.
																#{MetaCompany.CompanyParamount	: [MetaProvider.CompanyNetwork]}, # Not for tt18970320, tt2140663.
																#{MetaCompany.CompanyDiscovery	: [MetaProvider.CompanyNetwork]}, # Not for tt17163920.
																#{MetaCompany.CompanyYoutube		: [MetaProvider.CompanyNetwork]}, # Not for tt5535270.

																#{MetaCompany.CompanyParamount	: [MetaProvider.CompanyStudio]}, # Not for tt16026032, tt2140663.
																#{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyStudio]}, # Not for tt16026032.
																#{MetaCompany.Company20thcentury	: [MetaProvider.CompanyStudio]}, # Not for tt16026032.
																#{MetaCompany.CompanyWarner		: [MetaProvider.CompanyStudio]}, # Not for tt10623550.
																#{MetaCompany.CompanyCbs			: [MetaProvider.CompanyStudio]}, # Not for tt29732006.

																#'co0159111', # Quibi (tt9104072, tt10122474). Not for tt10620606, tt11803720. Now owned by Roku.
																'co0903231', # Rakuten Viki (tt20234568)
																'co0080139', # CTV Television Network (tt10738442)
																'co0014456', # ARTE (tt13925142)
																'co0649451', # Brat TV (tt7356206)
																'co0039462', # Public Broadcasting Service (PBS) (tt0078701, tt0369081)
																'co1068273', # PBS Me (tt16154056)
																'co0072315', # National Broadcasting Company (NBC) (tt0101158)
																'co0135684', # NBC Sports (tt5440768)
																'co0148907', # Playhouse Disney (tt32370092)
																'co0280472', # Manhattan Neighborhood Network (tt8050360)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # tt5177120
																#{MetaCompany.CompanyParamount	: [MetaProvider.CompanyNetwork]}, # Not for tt17076046.
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # tt15799866
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
															],
														},
													},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0364962', 'co0850678', 'co0566316', 'co0952202', 'co1031799', 'co0699790', 'co0864985', 'co0495245', 'co0577538'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyScreengems : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0010568', 'co0033007', 'co0145747', 'co0148620', 'co0075450', 'co0675845', 'co0240976', 'co0011282', 'co0830233'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0010568', 'co0033007', 'co0964193'],
				},
				MetaCompany.CompanyShowtime : {
					# Show (310 of 194+): Level-4.
					# Movie (109 of 102+): Level-3.
					# https://en.wikipedia.org/wiki/Category:Showtime_(TV_network)_original_programming
					# https://en.wikipedia.org/wiki/Category:Showtime_(TV_network)_films
					# https://en.wikipedia.org/wiki/List_of_Showtime_original_programming
					# Many collaborations and content provided to HBO, Cinemax, Netflix, Apple, Amazon, Hulu, Roku, Paramount, Playstation Vue, ITV, and more.
					# It seems the best way is to only use "Showtime Networks". Can't find any Showtime Originals that are not under this company.
					# Only SkyShowtime Originals (tt24022296, tt13263302, tt10371088) are not listed under "Showtime Networks", and most shows under SkyShowtime are Paramount+ Originals.
					# Many titles that seem to not be Showtime Originals, actually are.
					MetaProvider.CompanyOriginal	: {

														Media.Show	: {
															'fixed' : [
																'co0052980', # Showtime Networks
															],
															'exclude' : [
																#{MetaCompany.CompanyNetflix	: [MetaProvider.CompanyNetwork]}, # Do not add for tt0773262, tt1586680.
																#{MetaCompany.CompanyAmazon	: [MetaProvider.CompanyNetwork]}, # Do not add for tt0773262, tt1586680.
																#{MetaCompany.CompanyHbo		: [MetaProvider.CompanyNetwork]}, # tt0944947, tt2356777. Do not add for tt1586680, tt7440726.
																{MetaCompany.CompanyStarz		: [MetaProvider.CompanyNetwork]}, # tt10732048

																'co0098270', # AcornMedia (tt0115243)
																'co0022105', # Disney Channel (tt0106110)
																'co0003833', # Scanbox Entertainment (tt0290854)
																'co0877020', # Showtime Championship Boxing (tt1087760)
															],
														},
														Media.Movie	: {
															# At some point A24 released exclusivly on Showtime, although we try to exclude them via other companies.
															# It seems there is no good way of getting original films.
															# The best is to only use "Showtime Entertainment", which gets about 70% of the originals (except asome, eg tt0112727, tt0150363, tt0118528).
															'fixed' : MetaProvider.CompanyStudio,
															'disallow' : [
																'co0052980', # Showtime Networks
															],
															'exclude' : [

															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0052980', 'co0048667', 'co0628396', 'co0161345', 'co0048307', 'co0074825', 'co0045143', 'co1021008', 'co0877020', 'co0866626', 'co0458723', 'co0166446', 'co0065559', 'co0049409', 'co0047886'],
					MetaProvider.CompanyNetwork		: ['co0052980', 'co0011881', 'co0913372', 'co0901457', 'co0903913', 'co0212571', 'co0553743', 'co0944921', 'co0329011', 'co1036849', 'co0979606', 'co0927319', 'co0984498', 'co0652000', 'co0067309', 'co0014147'],
					MetaProvider.CompanyVendor		: ['co0087627', 'co0363506', 'co0121751', 'co0362187', 'co0316643', 'co0630026', 'co0698040', 'co0329014', 'co0142105', 'co0029265', 'co0872067', 'co0377252', 'co0125959', 'co0081812'],
				},
				MetaCompany.CompanySky : {
					# Show (1026): Level-2 to Level-3. Essentailly impossible to filter out HBO, Peacock, NBC, and other titles, due to content sharing and co-productions.
					# Movie (701): Level-2
					# A lot of co-productions with HBO (a shit ton), Showtime, Cinemax, and AMC.
					# Essentially impossible to filter out HBO content. Most HBO Originals are exclusively released on Sky in the UK, and Sky Originals mostly exclusively on HBO in the US. And this cannot be distiguished on IMDb.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown	: {
															# Too many IDs. Only use some.
															'fixed' : [
																# Sky Studios
																'co0542151', 'co1021520', 'co1025909', 'co0716013', 'co0445144', 'co0545188', 'co1069222', 'co0857784', 'co0103904', 'co0295048', 'co0612777',

																# Sky Networks
																'co0050995', 'co0169165', 'co0701341', 'co1005815', 'co0943021', 'co0951621', 'co1062041', 'co0614200', # Sky
																'co0277926', 'co0979860', 'co0979861', 'co1017869', 'co0774567', # Sky Europe
																'co0104193', 'co0615219', 'co0995552', 'co0894261', 'co0187094', 'co0323771', 'co0488036', # Sky One
																'co0103971', # Sky TV
																'co0825565', 'co0248896', 'co0547057', # Sky Channel
																'co0169100', 'co0301439', # Sky Movies
																'co0374625', 'co0329071', 'co0472197', 'co0989607', # Sky Atlantic
																'co0447329', 'co0401180', # Sky Vision
																'co0893022', 'co0663240', # Sky Go
																'co0967014', 'co0878025', # Sky Showcase
																'co0840513', 'co0788771', 'co0965885', # Sky Crime
																'co0285888', 'co0787982', # Sky Comedy
																'co0803868', 'co0885421', # Sky Documentaries
																'co0804062', 'co0966569', # Sky Nature
																'co0228643', 'co0411058', 'co0305913', 'co0211903', 'co0573344', # Sky Arts
																'co0901457', 'co0944921', 'co1036849', 'co0984498', # SkyShowtime
																'co0103727', # British Sky Broadcasting (BSkyB)
																'co0878026', 'co0497417', # Sky Max
																'co0778032', 'co1003057', 'co1034749', 'co1062045', 'co1062043', # Now
																'co0964826', # Wow
															],
														},
														Media.Show : {
															'exclude' : [
																# tt2628232 is a Sky Showtime original, but has not Sky company listed under it. If added int he future, check the other networks to exclude.

																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Not for tt2049116
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Not for tt5650650, tt7604446, tt4607112, tt3498622, tt7604446
																#{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # Not for tt10482370, tt10234362, tt3655448, tt7157248, tt7938588, tt3498622, tt4378376, tt1492179
																#{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]}, # Not for tt9055250, tt6586318
																#{MetaCompany.CompanyCinemax		: [MetaProvider.CompanyNetwork]}, # tt8594276. Not for tt1492179, tt7661390
																#{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]}, # Not for tt8038720
																#{MetaCompany.CompanyCrave		: [MetaProvider.CompanyNetwork]}, # Not for tt6586318
																#{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # Not for tt2711738, tt5830254, tt9174582
																#{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # Not for tt7661390, tt5830254, tt4075386, tt5936448, tt2049116, tt2647420
																#{MetaCompany.CompanyAubc			: [MetaProvider.CompanyNetwork]}, # Not for tt7604446, tt7604446
																#{MetaCompany.CompanyBbc			: [MetaProvider.CompanyNetwork]}, # Not for tt7604446, tt4607112, tt3502470, tt2164430, tt2647420, tt8129450, tt7604446
																#{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # Not for tt14190592, tt4607112
																#{MetaCompany.CompanyStarz		: [MetaProvider.CompanyNetwork]}, # Not for tt5830254
																#{MetaCompany.CompanyMgm			: [MetaProvider.CompanyNetwork]}, # Not for tt11694186, tt5932548
																#{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]}, # Not for tt1492179, tt10234362, tt9454736
																#{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # Not for tt8129450
																#{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # Not for tt9022422, tt9169784, tt9041792, tt9454736

																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # tt0452046, tt0773262
																{MetaCompany.CompanyHistory		: [MetaProvider.CompanyNetwork]}, # tt2306299
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # tt8690918
																{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]}, # tt2654620. Not for tt8129450 (not really a Sky Original)
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # tt11846996
																{MetaCompany.CompanyBravo			: [MetaProvider.CompanyNetwork]}, # tt5665418

																# Sister channels
																'co0129175', # NBC Universal Television (tt0386676)
																'co0046592', # Universal Television (tt11639952)

																# Collaborators
																'co0077623', # Home Box Office Home Video (HBO) (tt0141842)
																'co0306346', # HBO Home Entertainment (tt2356777)
																'co0284741', # HBO Entertainment (tt8550800)
																'co0005035', # Warner Bros. Television (tt0108778)
																'co0200179', # Warner Bros. Home Entertainment (tt0108757)
																'co0059995', # Warner Home Video (tt2649356)
																'co0072876', # Warner Bros. Animation (tt1213218)
																'co0077535', # The WB Television Network (tt0460681)
																'co0534118', # BBC iPlayer (tt2442560)
																'co0989615', # BBC Player (tt7526498)
																'co0304634', # BBC Worldwide Productions (tt2401256)

																#'co0014456', # ARTE. Not for tt3498622, tt2049116
																'co0037052', # American Broadcasting Company (ABC) (tt7587890, tt0411008, tt0413573)
																'co0070627', # CBS (tt6226232)
																'co0274041', # CBS Television Studios (tt7440726)
																'co0170466', # CBS Paramount Domestic Television (tt0112178)
																'co0070925', # Fox Network (tt0455275)
																'co0318834', # AMC Studios (tt1520211)
																'co0335036', # Television 360 (tt0944947)
																'co0777554', # 1:26 Pictures (tt11198330)
																'co0135004', # Naughty Dog (tt3581920)
																'co0751584', # Little Lamb (tt8772296)
																'co0137851', # Sony Pictures Home Entertainment (tt2741602)
																'co0000869', # Starz (tt1442449)
																'co0014380', # Dino De Laurentiis Company (tt2243973)
																'co0051891', # Paramount Home Entertainment (tt4270492)
																'co0053559', # Paramount Television (tt8324422)
																'co0291982', # Rough House Pictures (tt8634332)
																'co0068775', # Rai Fiction (tt7278862)
																'co0088248', # TNT Originals (tt2402207)
																'co0005051', # Turner Broadcasting System (TBS) (tt7529770)
																'co0103528', # Channel 4 Television Corporation (tt2384811)
																'co0371218', # Zodiak Rights (tt3830558)
																'co0015461', # MGM Home Entertainment (tt0348913)
																'co0804072', # Animal Pictures (tt14269590)
																'co0114965', # Rogers Media (tt9111220)
																'co0616900', # My5 (tt10590066)
																'co0695001', # Box to Box Films (tt8289930)
																'co0018794', # Ríkisútvarpið-Sjónvarp (RÚV) (tt3561180)
																'co0051618', # Entertainment One (tt8765446)
																'co0004762', # Fox Television (tt3435532)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},

																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyVendor]},

																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0196688', 'co0716013', 'co0415969', 'co0979861', 'co0542151', 'co0103904', 'co0151983', 'co0703862', 'co0445144', 'co1021520', 'co0612777', 'co0104200', 'co0726023', 'co0545188', 'co0466362', 'co1069222', 'co1025909', 'co0984914', 'co0950126', 'co0857784', 'co0854725', 'co0798268', 'co0654428', 'co0490861', 'co0397479', 'co0299588', 'co0295048', 'co0253854', 'co0226867', 'co0190730', 'co0023737', 'co0398019', 'co0155760'],
					MetaProvider.CompanyNetwork		: ['co0050995', 'co0985386', 'co0103727', 'co0104193', 'co0893022', 'co0964826', 'co0276736', 'co0374625', 'co0169165', 'co0885190', 'co0277926', 'co0873210', 'co0329023', 'co0952255', 'co0254125', 'co0106276', 'co0228643', 'co0103971', 'co0919122', 'co0803868', 'co0985385', 'co0971524', 'co0447329', 'co0137267', 'co0971525', 'co0919121', 'co0329071', 'co0217380', 'co0967014', 'co0615219', 'co0952256', 'co0985310', 'co0985309', 'co0840513', 'co0970200', 'co0899218', 'co0285888', 'co0804062', 'co0985311', 'co0778032', 'co0352403', 'co1056655', 'co0411058', 'co0901569', 'co0825565', 'co0787982', 'co0379754', 'co0905512', 'co0702154', 'co0919123', 'co0169100', 'co0885421', 'co0878026', 'co0472197', 'co0986206', 'co0905511', 'co0788771', 'co0901457', 'co1061120', 'co1003875', 'co0965885', 'co0986610', 'co0905510', 'co0995552', 'co0248896', 'co0979861', 'co0979860', 'co0966569', 'co0701341', 'co1056656', 'co0894261', 'co0391299', 'co1003057', 'co0995452', 'co0878025', 'co0481199', 'co0187094', 'co1026404', 'co1005815', 'co0547057', 'co0401180', 'co0323771', 'co1067888', 'co0944921', 'co0943021', 'co0932376', 'co0894054', 'co0488036', 'co0305913', 'co0088784', 'co0985384', 'co0951621', 'co0887040', 'co0228496', 'co0217851', 'co0188660', 'co0187356', 'co0136570', 'co1036849', 'co1034749', 'co1017869', 'co0989607', 'co0811948', 'co0663240', 'co0577710', 'co0569926', 'co0376754', 'co0315254', 'co0301439', 'co1073520', 'co1062046', 'co1062045', 'co1062044', 'co1062043', 'co1062041', 'co1058027', 'co0984498', 'co0980132', 'co0931305', 'co0774567', 'co0693280', 'co0614200', 'co0573344', 'co0560305', 'co0497417', 'co0297571', 'co0228600', 'co0211903', 'co0060930', 'co1020952', 'co0909121', 'co0703068'],
					MetaProvider.CompanyVendor		: ['co0122767', 'co1058414', 'co0712274', 'co0249192', 'co0944551', 'co0924398', 'co0814668', 'co0751407', 'co0714728', 'co0429154', 'co0334986', 'co0972316', 'co0958729', 'co0816028', 'co0293012', 'co0253892', 'co0253846', 'co0975175', 'co0924399', 'co0909123', 'co0909049', 'co0849558', 'co0790669', 'co0790533', 'co0734975', 'co0703461', 'co0577711', 'co0577709', 'co0540454', 'co0535961', 'co0454785', 'co0449873', 'co0256832', 'co0232548', 'co0978844', 'co0924319', 'co0469192'],
				},
				MetaCompany.CompanySony : {
					# Show (233): Level-3
					# Movie (198): Level-3
					# Sony produces a lot of US/English shows and movies, but these are almost always produced for other networks.
					# Only the Indian Sony branches (Sony Liv and Sony Entertainment Television) produce true Sony Originals.
					# Not even Sony Japan is really into Originals. Sony mostly owns other big japanese studios/networks that produce their local "originals".
					# If the user wants to get all the US/English titles produces by Sony (and there are a lot), they can be found under the Studios/Producers menus.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'fixed' : [
																'co0628249', # Sony Pictures Television Original Production CEE
																'co0546496', 'co0777877', 'co0806273', # Sony Liv
																'co0246050', 'co0081728', 'co0896022', # Sony Entertainment Television
																'co0544611', 'co0547466', 'co0725762', 'co0657603', 'co0431737', 'co0460639', 'co0822760', 'co0546494', 'co1037981', # Other Sony
															],
														},
														Media.Show : {
															'exclude' : [
																'co0963655', # MGM+ (tt15565872)
															],
														},
														Media.Movie : {
															'exclude' : [
																'co0159111', # Legendary Entertainment (tt3731562)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0086397', 'co0095398', 'co0013638', 'co0042679', 'co0121181', 'co0660299', 'co0053000', 'co0181130', 'co0171368', 'co0628249', 'co0128891', 'co0780213', 'co0622733', 'co0898832', 'co0660268', 'co0164272', 'co0013837', 'co0881672', 'co0450028', 'co0147952', 'co0312488', 'co0074006', 'co1002159', 'co0520898', 'co0304476', 'co0221897', 'co0151953', 'co0107503', 'co0611794', 'co0443771', 'co1006768', 'co0905480', 'co0546495', 'co0460527', 'co0310744', 'co0209115', 'co0208409', 'co1051393', 'co0843409', 'co0782033', 'co0703484', 'co0504899', 'co0357755', 'co0282519', 'co0268017', 'co0251998', 'co0199078', 'co0101361', 'co0044974', 'co0198299', 'co0107410'],
					MetaProvider.CompanyNetwork		: ['co0546496', 'co0246050', 'co0544611', 'co0081728', 'co0372942', 'co0725671', 'co0547466', 'co0434265', 'co0725762', 'co0315317', 'co0777877', 'co0295187', 'co0879659', 'co0186035', 'co0361294', 'co0367891', 'co0629936', 'co0896022', 'co0657603', 'co0888494', 'co0806273', 'co0431737', 'co0367866', 'co0822760', 'co0460639', 'co0415756', 'co0373830', 'co0351299', 'co0482699', 'co0468659', 'co0415760', 'co0415758', 'co0415757', 'co0367949', 'co0367927', 'co1037981', 'co0777056', 'co0629937', 'co0624286', 'co0546494', 'co0493700', 'co0479937', 'co0420621', 'co0415753', 'co0364235'],
					MetaProvider.CompanyVendor		: ['co0137851', 'co0026545', 'co0110101', 'co0052145', 'co0014453', 'co0375381', 'co0145664', 'co0209825', 'co0095398', 'co0769046', 'co0533783', 'co0402495', 'co0185481', 'co0811162', 'co0072831', 'co0163321', 'co0001799', 'co0795863', 'co0584895', 'co0121331', 'co0873390', 'co0655055', 'co0775797', 'co0600878', 'co0307036', 'co0087306', 'co0188620', 'co0565929', 'co0080433', 'co0852957', 'co0144567', 'co0765733', 'co0802090', 'co0243381', 'co0881365', 'co0847351', 'co0060012', 'co0770268', 'co0565928', 'co0151916', 'co0789116', 'co0071829', 'co0865164', 'co0653605', 'co0810034', 'co0802089', 'co0215255', 'co0802091', 'co0256964', 'co0215082', 'co0064922', 'co0880495', 'co0850664', 'co0732568', 'co0080266', 'co0815089', 'co0767764', 'co0305812', 'co0510488', 'co1003784', 'co0472728', 'co0208861', 'co0143764', 'co0104245', 'co0898832', 'co0514017', 'co0281373', 'co0211045', 'co0099317', 'co0009479', 'co0902939', 'co0651690', 'co0384875', 'co0341744', 'co0065232', 'co0043827', 'co0410527', 'co0309356', 'co0179937', 'co0172249', 'co0101612', 'co0088857', 'co0835413', 'co0475310', 'co0393339', 'co0219581', 'co0165909', 'co0033361', 'co1034913', 'co0935482', 'co0832871', 'co0665131', 'co0618335', 'co0617378', 'co0613276', 'co0405210', 'co0280381', 'co0270513', 'co0246535', 'co0132903', 'co0071392', 'co0045940', 'co0980862', 'co0796214', 'co0462171', 'co0457297', 'co0349334', 'co0328292', 'co0310744', 'co0291223', 'co0259638', 'co0057635', 'co0951251', 'co0909503', 'co0828650', 'co0825216', 'co0577179', 'co0558021', 'co0547312', 'co0488996', 'co0469521', 'co0424487', 'co0378943', 'co0309278', 'co0253404', 'co0226000', 'co0213247', 'co0139175', 'co0122709', 'co0032740', 'co0927303', 'co0369424', 'co0254863', 'co0211298', 'co0157130', 'co0131639', 'co0127139', 'co0064651', 'co0028920', 'co0859939', 'co0868243', 'co0842694'],
				},
				MetaCompany.CompanyStarz : {
					# Show (107): Level-3, close to Level-4
					# Movie (231): Level-3
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# Starz Kids and Family
																'co0238789',
																'co1042752',
																'co1042751',
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Not for tt3006802, tt1442449, tt2375692.
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Not for tt3006802, tt2375692.
																#{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # Not for tt3006802, tt2375692.
																#{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # Not for tt3006802, tt1442449, tt2375692.
																#{MetaCompany.CompanyParamount	: [MetaProvider.CompanyNetwork]}, # Not for tt2375692 (at least for Paramount Channel).
																#{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # tt9140342. Not for tt2094262.
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # tt9179552, tt8201186
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # tt4820370
																{MetaCompany.CompanyBravo			: [MetaProvider.CompanyNetwork]}, # tt0448190
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]}, # tt0762067

																'co0118334', # BBC America (tt7016936)
																'co0081852', # Thruline Entertainment (tt2235759)
																'co0951662', # Fifth Season (tt2887954)
																'co0781350', # Paramount Television Studios (tt10574236)
																'co0274041', # CBS Television Studios (tt1831804)
																'co0593772', # Globoplay (tt3846642)
																'co0038332', # DC Comics (tt8425532)
																'co0136768', # All3Media (tt9140342)
																'co0233013', # All3Media International (tt11656892)
																'co0277926', # Sky Deutschland (tt5830254)
																'co0039940', # FUNimation Entertainment (tt0495212)
																'co0783825', # The MediaPro Studio (tt8290362)
																'co0307892', # BBC Two Films (tt8049666)
																'co0049815', # TVNZ (tt8075008)
																'co0014456', # ARTE (tt8335218)
																'co0046592', # Universal Television (tt7587362)
																'co0031829', # Canada Television and Cable Production Fund License Program (CTCPF) (tt0179061)
																'co0837212', # Fremantle (tt9848536)
																'co0712319', # Nordic Entertainment Group (tt7683762)
																'co0287003', # Epix (I) (tt8912384)
																'co0039462', # Public Broadcasting Service (PBS) (tt0337550)
																'co0017229', # Australian Children's Television Foundation (tt0495020)
																'co0211390', # Boomerang (tt1016126)
																#'co0045850', # Canadian Broadcasting Corporation (CBC) (tt1695366). Not for tt1453159.
																'co0257711', # TNT Serie (tt1695366)
																'co0072315', # National Broadcasting Company (NBC) (tt0098762)
																'co0070627', # CBS (tt0212679)
																'co0279237', # MBC Group (tt10198930)
																'co0202446', # YouTube (tt2061165)
																'co0025978', # Norsk Rikskringkasting (NRK) (tt5157290)
																#'co0028557', # Canal+ (tt22189180). Not for tt1453159.
																'co0616357', # German Motion Picture Fund (tt22189180)
																'co0136980', # IDT Entertainment (tt0822601)
																'co0104833', # Children's Independent Television (CiTV) (tt0341973)
																'co0086099', # Fremantle Media International (tt11694076)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # tt5177120

																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]}, # tt0120484
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},

																'co0028689', # Manga Entertainment (tt0156887)
																'co0835320', # Universal Home Entertainment (tt1262416)
																'co0150452', # The Weinstein Company (tt0462322)
																'co0024325', # Dutch FilmWorks (DFW) (tt15325794, tt18083578)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0280576', 'co0482786', 'co0067269'],
					MetaProvider.CompanyNetwork		: ['co0000869', 'co0002342', 'co0324445', 'co0316607', 'co0746532', 'co0238789', 'co0740154', 'co0010826', 'co0746531', 'co0809057', 'co0530112', 'co1042752', 'co0186042', 'co1069971', 'co1018571', 'co0793760', 'co0786037', 'co0002075', 'co1042751', 'co0635080'],
					MetaProvider.CompanyVendor		: ['co0198595', 'co0209315', 'co0224655'],
				},
				MetaCompany.CompanySyfy : {
					# Show (203 of 139+): Level-3.
					# Movie (454 of 259+): Level-2.
					# https://en.wikipedia.org/wiki/Category:Syfy_original_programming
					# https://en.wikipedia.org/wiki/Category:Syfy_original_films
					# Difficult to filter, since many Syfy Originals appear on other platforms, and vice versa, most of them from small studios/distributors.
					MetaProvider.CompanyOriginal	: {

														Media.Show	: {
															'allow' : [
																'co0118334', # BBC America (tt0407362)
																'co0602021', # Shudder (tt4820370)
															],
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # tt1910645. Do not add for tt3148266, tt3230854.
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Do not add for tt3230854, tt4254242.
																#{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # tt0944947, tt0436992. Do not add for tt0094517, tt4276624.

																{MetaCompany.CompanyCw			: [MetaProvider.CompanyNetwork]}, # tt2661044, tt2632424
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # tt10016724
																#{MetaCompany.CompanyPluto		: [MetaProvider.CompanyNetwork]}, # tt0056751. Do not add for tt0118480.
																{MetaCompany.CompanyBritbox		: [MetaProvider.CompanyNetwork]}, # tt0056751
																{MetaCompany.CompanyCartoonnet	: [MetaProvider.CompanyNetwork]}, # tt0112159, tt0088595
																#{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # tt3663490. Do not add for tt4820370.
																{MetaCompany.CompanyHistory		: [MetaProvider.CompanyNetwork]}, # tt6632666
																#{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]}, # tt0115243. Do not add for tt0112111.
																#{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # tt6110648 (USA is a sibling network to Syfy). Do not add for tt8690918.
																#{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]}, # Do not add for tt1132290.
																#{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]}, # Tons also appear on various Fox networks.
																#{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]}, # tt0436992, tt0106179, tt0118276, tt3322312, tt0103584, tt0162065, tt1199099. Do not add for tt8388390, tt8388390.

																'co0808044', # Jio Cinema (tt0944947)
																'co0052417', # NHK (tt0436992)
																'co0820547', # Paramount+ (tt0092455, tt9795876) Do not add all Paramount networks, since Syfy was previously partially owned by Paramount.
																'co0022869', # Pathé (tt0112230)
																'co0047120', # Marvel Entertainment (tt3322312)
																'co0578069', # Marvel Entertainment Group (tt0103584)
																#'co0032009', # CanWest Global Communications (tt0303461, tt0813715). Do not add for tt1519931.
																#'co0186110', # CanWest Global Television Network (tt0204993). Do not add for tt0118480.
																'co0028775', # Fox Film Corporation (tt0303461)
																'co0003850', # Nippon Television Network (NTV) (tt0434706, tt0813715)
																'co0199370', # FremantleMedia Enterprises (tt1199099)
																'co0037052', # American Broadcasting Company (ABC) (tt1307824)
																'co0209226', # ABC Signature (tt0844653)
																'co0113687', # ABC Family Worldwide (tt0838800)
																'co0530354', # ABC for Kids (tt0230804)
																#'co0680232', # HBO España (tt5615700). Do not add for tt5924572.
																'co0366131', # ABC Spark (tt5615700)
																#'co0048760', # Home Video Hellas (HVH) (tt0096684). Do not add for tt0112167.
																'co0322088', # KSM (tt0096684)
																#'co0172894', # Reunion Pictures (tt1954347). Do not add for tt0910812.
																#'co0533814', # Spike (tt0106179). Do not add for tt4878326.
																#'co0053846', # Spike (tt1051220)
																#'co0099482', # Spike TV (tt0823333)
																'co0023307', # Music Television (MTV) (tt1051220)
																'co0024325', # Dutch FilmWorks (DFW) (tt0823333)
																'co0185136', # MTV Italia (tt0201391)
																'co0180560', # Prodigy Pictures (tt1429449, tt1332653)
																'co0132285', # Aniplex (tt0948103)
																#'co0051618', # Entertainment One (tt2365946). Do not add for tt3843168, tt1519931, tt0965394.
																'co0368981', # Studio Hamburg Enterprises (tt2365946)
																'co0834810', # Discovery+ (tt0426697)
																'co0080139', # CTV Television Network (tt0123816)
																'co0269801', # ITV Studios (tt4520906)
																'co0003500', # Channel 5 Television (tt3556944, tt0204993, tt0106179)
																'co0141575', # ATM Grupa S.A. (tt1910645)
																'co0105874', # LivingTV (tt0808013)
																#'co0122766', # Umbrella Entertainment (tt1752076). Do not add for tt0287839.
																'co0076716', # South Pacific Pictures (tt1752076)
																#'co0098315', # Blumhouse Productions (tt6110648). Do not add for tt3696720.
																'co0071240', # Platinum Dunes (tt6110648)
																'co0098270', # AcornMedia (tt0115243)
																'co0158976', # Cuatro (tt1135300)
																'co0024077', # ARD (tt0078579)
																'co0053559', # Paramount Television (tt0281432)
																'co0066107', # Paramount Network Television (tt0389564)
																'co0009512', # TNT (tt3663490)
																'co0287003', # Epix (I) (tt11525188)
																#'co0045850', # Canadian Broadcasting Corporation (CBC) (tt0103504). Do not add for tt3696720.
																'co0061460', # France 3 (tt0103504)
																'co0225995', # BBC Warner (tt0485301)
																#'co0124425', # Alive Vertrieb und Marketing (tt0120570). Do not add for tt0187636.
																'co0151501', # Capelight Pictures (tt0120570)
																'co0221369', # E! Channel (tt0880557)
																'co0041475', # EuroVideo (tt2262308)
																'co0251163', # Crunchyroll (tt0091211)
																#'co0013824', # RHI Entertainment (tt1461312, tt0959086). Do not add for tt1720619.
																'co0163158', # Thunderbird Entertainment (tt1461312)
																'co0011066', # Video Audio Project (VAP) (tt0959086)
																'co0114908', # Mainichi Broadcasting System (MBS) (tt0078692, tt1134000)
																'co0070627', # CBS (tt0460686)
																'co0086191', # Modern Entertainment (tt0292858)
																'co0174148', # The CW Network (The CW) (tt10207090)
																'co0272333', # Spacetoon (tt0092329)
																#'co0003079', # Concorde Home Entertainment (tt1820723). Do not add for tt1595680
																'co0313320', # Film1 (tt1820723)
																'co0248345', # Watch (tt2295953)
																'co0028689', # Manga Entertainment (tt0158591, tt1186591, tt0421480, tt1177191, tt0368197, tt1141604)
																'co0148588', # Star TV (tt1979918)
																'co0190039', # ReelzChannel (tt2336630)
																'co0097219', # Anime International Company (AIC) (tt0318898, tt0158644)
																'co0034415', # Palm Pictures (tt0169501)
																'co0055142', # AB Distribution (tt0159933)
																'co0013582', # Teletoon (tt0190198)
																'co0127196', # Chiba TV (tt0872308)
																'co0437769', # Kix (tt0211867)
																'co0212402', # Dynit (tt0115263)
																'co0062107', # Toei Animation (tt0122336)
																'co1017492', # Ani-Monday (tt0377290)
																'co0006066', # Anime Works (tt0107228)
																'co0293280', # Disney XD (tt1102732)
																'co0376640', # Sonar Entertainment (II) (tt2315850)
																'co0106229', # Challenge TV (tt0193677)
															],
														},
														Media.Movie	: {
															'exclude' : [
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyVendor]}, # tt0304669
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]}, # tt0464154, tt0113497
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]}, # tt0113497
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]}, # tt5834426, tt1259521

																{MetaCompany.CompanyTubi			: [MetaProvider.CompanyNetwork]}, # tt0338526

																'co0097402', # United International Pictures (UIP) (tt6772950)
																'co0292985', # Summit Home Entertainment (tt1245526)
																'co0002257', # Constantin Film (tt0795461)
																'co0024325', # Dutch FilmWorks (DFW) (tt3522806, tt1411250)
																'co0028689', # Manga Entertainment (tt0156887)
																'co0005726', # Columbia TriStar Films AB (tt0133751)
																'co0124425', # Alive Vertrieb und Marketing (tt2321549)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0321669', 'co0169785', 'co0242100'],
					MetaProvider.CompanyNetwork		: ['co0282285', 'co0024368', 'co0876404', 'co0298911', 'co0002937', 'co0308282', 'co0470060', 'co0234798', 'co0289068', 'co0951622', 'co0288390', 'co0188604', 'co0810364', 'co0370054', 'co0306623', 'co0174586', 'co0449313', 'co1056650', 'co1041024', 'co0951623', 'co0370118', 'co0307546', 'co0229476', 'co1049885', 'co0951626', 'co0951625', 'co0951624', 'co0619890', 'co0619887', 'co0619878', 'co0619866', 'co0619861', 'co0619860', 'co0561779', 'co0369798', 'co0311751', 'co0293780', 'co0220940', 'co0311104'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyTbs : {
					# Show (251): Level-4 to Level-5
					# Movie (212): Level-3
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																'co0688123', # TBS (AR). Not real TBS and a Japanese title that is mislabled.
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyTnt				: [MetaProvider.CompanyNetwork]}, # Not for tt4903242, tt7529770, tt1600199, tt10691888, tt6396094, tt6317068
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt6317068
																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # Not for tt1637574, tt5323988, tt4168956, tt5460226, tt7529770, tt0926732, tt5323988
																#{MetaCompany.CompanyTrutv			: [MetaProvider.CompanyNetwork]}, # Not for tt1637574
																#{MetaCompany.CompanyComedycen		: [MetaProvider.CompanyNetwork]}, # Not for tt1637574, tt0397306, tt1942919
																#{MetaCompany.CompanyAdultswim		: [MetaProvider.CompanyNetwork]}, # Not for tt0397306, tt6317068
																#{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]}, # Not for tt0397306
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # Not for tt0397306, tt1441109
																#{MetaCompany.CompanyFox				: [MetaProvider.CompanyNetwork]}, # Not for tt0397306, tt1441109
																#{MetaCompany.CompanyBbc				: [MetaProvider.CompanyNetwork]}, # Not for tt0397306, tt5460226
																#{MetaCompany.CompanyItv				: [MetaProvider.CompanyNetwork]}, # Not for tt0397306
																#{MetaCompany.CompanyChannel4			: [MetaProvider.CompanyNetwork]}, # Not for tt3597790, tt1600199, tt3597790
																#{MetaCompany.CompanySky				: [MetaProvider.CompanyNetwork]}, # Not for tt7529770
																#{MetaCompany.CompanyMtv				: [MetaProvider.CompanyNetwork]}, # Not for tt1441109
																#{MetaCompany.CompanyRoku				: [MetaProvider.CompanyNetwork]}, # Not for tt10338160
																#{MetaCompany.CompanyCrunchyroll		: [MetaProvider.CompanyNetwork]}, # Not for tt25531288 (This was probably mislabled for the unrelated TBS Japan)

																# Too many TBS animated originals also on CN.
																#{MetaCompany.CompanyCartoonnet	: [MetaProvider.CompanyNetwork]}, # tt0115157, tt0088631, tt0118289, tt0419315, tt0083475. Not for tt0098763, tt0101169, tt0126173.
																'co0238110', # Cartoon Network Studios (tt0115157, tt0419315)
																'co1060195', # Cartoon Network Productions (tt0118289)
																#'co0024579', # Hanna-Barbera Productions (tt0083475). Not for tt0098763, tt0101169, tt0126173.
																#'co1063128', # Hanna-Barbera Cartoons. Not for tt0105928
																'co0180605', # Luxanimation (tt0482870)

																# tt1441109 was an ABC original, but moved to TBS.
																# However, still exclude, since there are too many other ABC Originals which are difficult or even impossible to exclude otherwise.
																'co0037052', # American Broadcasting Company (ABC) (tt0285351, tt0086827, tt0083475)
																#'co0209226', # ABC Signature. Not for tt1441109 (ABC original moved to TBS).

																'co0072315', # National Broadcasting Company (NBC) (tt0386676)
																'co0070627', # CBS (tt6226232)
																'co0598660', # CBS All Access (tt1583607)
																#'co0274041', # CBS Television Studios. Not for tt5990096.
																'co0074685', # Bright/Kauffman/Crane Productions (tt0108778)
																'co0008281', # Williams Street (tt2861424)
																'co0077623', # Home Box Office Home Video (HBO) (tt0844441)
																'co0098048', # Columbia TriStar Home Entertainment (tt0086827)
																'co0409029', # Feigco Entertainment (tt10380768)
																'co0022105', # Disney Channel (tt0088616)
																'co0047269', # South African Broadcasting Corporation (SABC) (tt0086798)
																'co0232851', # Meetinghouse Productions (tt1198300)
																'co0062107', # Toei Animation (tt6114326)
																'co0006071', # Tokuma Japan Communications (tt0426383)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNetflix	: [MetaProvider.CompanyNetwork]}, # tt5164214, tt0457939
																{MetaCompany.CompanyAmazon	: [MetaProvider.CompanyNetwork]}, # tt1375666
																{MetaCompany.CompanyAmc		: [MetaProvider.CompanyNetwork]}, # tt0111161
																{MetaCompany.CompanyParamount	: [MetaProvider.CompanyNetwork]}, # tt0088247, tt0196229
																{MetaCompany.CompanyTubi		: [MetaProvider.CompanyNetwork]}, # tt0149261, tt1690953
																{MetaCompany.CompanyPeacock	: [MetaProvider.CompanyNetwork]}, # tt2293640
																{MetaCompany.CompanyDisney	: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt1323594, tt0119174

																'co0228937', # New Line Home Entertainment (tt0359013)
																'co0070627', # CBS (tt0083929)
																'co0591004', # Paramount Channel (tt0196229)
																'co0796240', # Paramount Channel (tt0093389)
																'co0629395', # Hotstar (tt2361509)
																'co0063964', # 20th Century Fox Home Entertainment (tt0116282)
																'co0015461', # MGM Home Entertainment (tt0094012)
																'co0297627', # Universal Pictures Home Entertainment (tt0093300)
																'co0370614', # Tanweer Alliances (tt6182908)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0100472', 'co0573042', 'co0334947', 'co1037480', 'co0683031'],
					MetaProvider.CompanyNetwork		: ['co0005051', 'co0183474', 'co0057274', 'co0418169', 'co0396917', 'co0756309', 'co0528223', 'co0688123', 'co0505494', 'co0569273', 'co1037480', 'co0867778', 'co1000321', 'co0541624'],
					MetaProvider.CompanyVendor		: ['co0972823', 'co0568014', 'co0012522'],
				},
				MetaCompany.CompanyTnt : {
					# Show (234 of 90+): Level-4.
					# Movie (337 of 98+): Level-3.
					# https://en.wikipedia.org/wiki/Category:TNT_(American_TV_network)_original_programming
					# https://en.wikipedia.org/wiki/Category:TNT_(American_TV_network)_original_films
					MetaProvider.CompanyOriginal	: {
														Media.Show	: {
															'exclude' : [
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # tt1958961. Do not add for tt4604612.
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # tt4607112. Do not add for tt2402207, tt1196946.
																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # tt0944947 (Both owned by Warner). Do not add for tt8129610, tt0458253, tt1462059, tt4604612, tt1196946.
																{MetaCompany.CompanyCw				: [MetaProvider.CompanyNetwork]}, # tt0944947 (Both owned by Warner)
																{MetaCompany.CompanyAdultswim			: [MetaProvider.CompanyNetwork]}, # tt1783495, tt0795065 (Both owned by Warner)
																{MetaCompany.CompanyCartoonnet		: [MetaProvider.CompanyNetwork]}, # tt1480669 (Both owned by Warner)
																{MetaCompany.CompanyDiscovery			: [MetaProvider.CompanyNetwork]}, # tt17676766 (Both owned by Warner)
																{MetaCompany.CompanyShowtime			: [MetaProvider.CompanyNetwork]}, # tt1586680
																#{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # tt6226232. Do not add for tt4604612.
																{MetaCompany.CompanyAmc				: [MetaProvider.CompanyNetwork]}, # tt6156584
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # tt0108778. Do not add for tt1714204.
																#{MetaCompany.CompanyNbc				: [MetaProvider.CompanyNetwork]}, # tt0098844, tt0098904. Do not add for tt2402207.
																#{MetaCompany.CompanyCbs				: [MetaProvider.CompanyNetwork]}, # tt0369179. Do not add for tt1196946.
																#{MetaCompany.CompanySky				: [MetaProvider.CompanyNetwork]}, # tt14190592. Do not add for tt2402207.
																#{MetaCompany.CompanyFox				: [MetaProvider.CompanyNetwork]}, # tt2071645, tt1728102. Do not add for tt1462059.
																#{MetaCompany.CompanyFx				: [MetaProvider.CompanyNetwork]}, # tt4189492. Do not add for tt1462059.
																{MetaCompany.CompanyStarz				: [MetaProvider.CompanyNetwork]}, # tt4643084
																#{MetaCompany.CompanySyfy				: [MetaProvider.CompanyNetwork]}, # tt0799862, tt0944947. Do not add for tt3663490.
																{MetaCompany.CompanyUsa				: [MetaProvider.CompanyNetwork]}, # tt1127107

																'co0077535', # The WB Television Network (tt0460653) (sister channel)
																'co0100472', # TBS Productions Inc. (tt4903242) (sister channel)
																#'co0005051', # Turner Broadcasting System (TBS) (tt0289016, tt6902652, tt7529770) (sister channel). Do not add for tt1600199.
																'co0306346', # HBO Home Entertainment (tt1723816, tt0944947) (sister channel)
																'co0077623', # Home Box Office Home Video (HBO) (tt0809497) (sister channel)
																'co0909975', # HBO 3 (tt9170108) (sister channel)

																'co0037052', # American Broadcasting Company (ABC) (tt7587890, tt0411008)
																'co0050794', # ABC Family (tt0976014)
																'co0072315', # National Broadcasting Company (NBC) (tt0098844, tt0098904)
																'co0537097', # BBC First (tt4607112)
																'co0050995', # Sky (tt14190592)
																'co0029768', # Comedy Central (tt6226232)
																'co0051884', # Paramount Comedy Channel (tt0369179)
																'co0056447', # 20th Century Fox Television (tt0106179)
																'co0183875', # CBS Paramount Network Television (tt0247082)
																'co0086397', # Sony Pictures Television (tt0381798)
																#'co0440561', # Universal Channel (tt0412142). Do not add for tt3663490.
																'co0023827', # Universal Pictures Home Entertainment (UPHE) (tt0799862)
																'co0129175', # NBC Universal Television (tt0412142)
																'co0046592', # Universal Television (tt0079783 - released on KNBC)
																#'co0070627', # CBS (tt6226232). Do not add for tt1196946.
																'co0820547', # Paramount+ (tt3288518)
																'co0216537', # FX Productions (tt4189492)
																'co0247505', # Citytv (tt9111220)
																'co0367891', # Sony Entertainment Television (tt0108778)
																'co0292909', # Lionsgate Home Entertainment (tt0108958)
																'co0001860', # United Paramount Network (UPN) (tt0103460)
																'co0001093', # Trinity Broadcasting Network (TBN) (tt0113483)
																#'co0108651', # Oxygen Channel (tt2402569). A TNT original.
																#'co0080139', # CTV Television Network (tt0208629 - a TNT original). Do not add for tt1196946.
																'co0045850', # Canadian Broadcasting Corporation (CBC) (tt1695366)
																'co0234496', # BBC Two (tt0105957)
																'co0159433', # ATV (tt1018501, tt5610466)
																'co0084025', # Reshet TV (tt4354042)
																'co0436383', # El Rey Network (tt4171176)
																'co0196214', # NBC Universal Digital Distribution (tt1261559)
																'co0233817', # MaggieVision (tt1809362)
																'co0006395', # Lifetime Television (tt1196953)
																'co0369614', # El Trece (tt8516554, tt10631536)
																'co0071026', # MGM Television (tt0112037)
																'co0095398', # Sony Pictures Television International (tt1222663)
																#'co0047476', # StudioCanal (tt1958961). Do not add for tt2217759.
																'co0051229', # Rubicon TV AS (tt1958961)
																'co0123927', # DC Universe (tt1043813)
																'co0290683', # Channel 4 Television (tt2647258)
																'co0706824', # Channel 4 (tt0111924)
																'co0094448', # Lorimar Television (tt0077000)
																'co0005803', # Muse Entertainment Enterprises (tt3950230)
																'co0039979', # Jerry Bruckheimer Television (tt4946972)
																'co0702579', # Flow (tt32495809)
																'co0363411', # SoHo (tt1578887)
																'co0165168', # Cable News Network (CNN) (tt10468676)
																'co0469937', # Kanopy (tt8819192)
																'co0473201', # Telemundo Internacional (tt7084640)
																'co0078814', # Zweites Deutsches Fernsehen (ZDF) (tt10095376)
																'co0760183', # START (tt10515972)
																'co0037736', # Televisión Federal (Telefe) (tt10515972)
															],
														},
														Media.Movie	: {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]}, # tt0098084
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt0106233

																#{MetaCompany.CompanyParamount	: [MetaProvider.CompanyVendor]}, # Do not add for tt0435591, tt0329390.
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]}, # tt0062622, tt0903624
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]}, # tt0088323

																'co0008693', # Home Box Office (HBO) (tt1933667) (sister channel)
																'co0228937', # New Line Home Entertainment (tt0109686)
																'co0152990', # Roadshow Entertainment (tt0133093)
																'co0236298', # Roadshow Entertainment (tt2140479, tt0451279)
																'co0031085', # Argentina Video Home (tt0118971)
																'co0370614', # Tanweer Alliances (tt2179136, tt7126948, tt7959026)
																'co0037052', # American Broadcasting Company (ABC) (tt0086393)
																'co0024325', # Dutch FilmWorks (DFW) (tt0362478)
																'co0124425', # Alive Vertrieb und Marketing (tt8974964)
																#'co0122766', # Umbrella Entertainment (tt0079917). Do not add for tt0238768.
																'co0613807', # Powerhouse Films (tt0079917)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0224166', 'co0212433', 'co0088248', 'co0447313', 'co0499377', 'co0447226', 'co0873052', 'co0617058', 'co0480705', 'co0474332', 'co0407107', 'co0375990', 'co0344872', 'co0617059', 'co0465048', 'co0366683', 'co0259875'],
					MetaProvider.CompanyNetwork		: ['co0009512', 'co0011489', 'co0257711', 'co0350722', 'co0505495', 'co0607678', 'co0724274', 'co0771916', 'co0224166', 'co0561952', 'co0418278', 'co0835799', 'co0024749', 'co1010896', 'co0449308', 'co0887203', 'co0852643', 'co0675903', 'co0241737', 'co0893018', 'co0037608', 'co1064922', 'co1029550', 'co0988991', 'co0617058', 'co0239363', 'co1068047', 'co1059526', 'co0868070', 'co0617059'],
					MetaProvider.CompanyVendor		: ['co0448330', 'co0407107', 'co0375990', 'co0361258', 'co0671664'],
				},
				MetaCompany.CompanyTouchstone : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0049348', 'co0067205', 'co0925713', 'co0110398', 'co0759606', 'co0426272', 'co1066685', 'co0747847'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0041517', 'co0659855', 'co0226864', 'co0477440', 'co0300570', 'co0233977', 'co0886556', 'co0750134', 'co0883363', 'co0194602', 'co0387386', 'co1002359', 'co0735841', 'co0539616', 'co0662162', 'co0501762', 'co0241748', 'co0501763', 'co0229151'],
				},
				MetaCompany.CompanyTristar : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0005883', 'co0074221', 'co0051191', 'co0440338', 'co0032932', 'co0624442', 'co0147951', 'co0015605', 'co0001581', 'co0250475', 'co0142305', 'co0113915', 'co0113868', 'co0773877', 'co0355277', 'co0348512', 'co0245365', 'co0168261', 'co0142304', 'co0093452', 'co0008439'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0001850', 'co0127120', 'co0003581', 'co0009297', 'co0005883', 'co0189864', 'co0098048', 'co0077851', 'co0213457', 'co0057443', 'co0003949', 'co0045926', 'co0108034', 'co0005726', 'co0060005', 'co0075764', 'co0628925', 'co0768357', 'co0774471', 'co0170439', 'co0006448', 'co0182605', 'co0047778', 'co0613324', 'co0035705', 'co0728184', 'co0539852', 'co0225408', 'co0135317', 'co0094232', 'co0287692', 'co0768425', 'co0638112', 'co0114725', 'co0037988', 'co0152638', 'co0015669', 'co0884352', 'co0720168', 'co0393411', 'co0135318', 'co0942170', 'co0751613', 'co0039725', 'co0115429', 'co0045347', 'co0815627', 'co0942169', 'co0382315', 'co0163983', 'co0241443', 'co0057970', 'co0373110', 'co0700140', 'co0379792', 'co0954396', 'co0754056', 'co0982368', 'co0382360', 'co1020466', 'co0379620', 'co1002119', 'co0628032', 'co0613216', 'co0428560', 'co0961122', 'co0826726', 'co0802980', 'co0723390', 'co1042290', 'co1021830', 'co0960788', 'co0960786', 'co0919176', 'co0919014', 'co0890192', 'co0753593', 'co0625795', 'co0294950', 'co0120629', 'co1055336', 'co1037590', 'co0981289', 'co0976563', 'co0943399', 'co0919175', 'co0919019', 'co0919016', 'co0919015', 'co0919013', 'co0853923', 'co0833779', 'co0802979', 'co0793712', 'co0670235', 'co0382011', 'co0367774', 'co0284253', 'co0232258', 'co0210948', 'co0189829', 'co1062404', 'co0960785', 'co0960784', 'co0820799', 'co0820798', 'co0774102', 'co0337735', 'co0313694', 'co0217342', 'co0209928', 'co0201367', 'co0137852', 'co0004899'],
				},
				MetaCompany.CompanyTrutv : {
					# Show (194): Level-4. Pretty accurate out of the box.
					# Movie (78): Level-4
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # Not for tt2100976
																#{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # Not for tt2100976, tt8026448, tt3559912, tt5034326, tt7552590, tt1674417, tt4264096
																#{MetaCompany.CompanyTbs			: [MetaProvider.CompanyNetwork]}, # Not for tt1198300
																#{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]}, # Not for tt4661598
																#{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]}, # Not for tt0434702
																#{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # Not for tt0247882
																#{MetaCompany.CompanyPluto		: [MetaProvider.CompanyNetwork]}, # Not for tt0247882
																#{MetaCompany.CompanyTubi			: [MetaProvider.CompanyNetwork]}, # Not for tt0247882
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Not for tt0247882
																#{MetaCompany.CompanyHistory		: [MetaProvider.CompanyNetwork]}, # Not for tt1674417

																{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]}, # tt0106079

																'co0072315', # National Broadcasting Company (NBC) (tt0278191, tt0406429)
																'co0011242', # Conaco (tt1637574)
																'co0070925', # Fox Network (tt0320000)
																'co0220736', # Da Vinci Productions (tt0156442)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt0109127, tt0119137, tt5275892
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]}, # tt0356634
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]}, # tt0100419
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]}, # tt0458364
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0213659'],
					MetaProvider.CompanyNetwork		: ['co0214175', 'co0036798', 'co0494156', 'co0670573', 'co0200080'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyTubi : {
					# Show (43): Level-3. Some difficult to filter through Fox and Amazon.
					# Movie (959): Level-2. Contains a bunch of Tubi Originals, but there are too many low-budget films from various studios/distributors to filter them properley.
					# Has a lot of content on Amazon.
					MetaProvider.CompanyOriginal	: {
														Media.Show : {
															'allow' : [
																'co0103528', # Channel 4 Television Corporation (too much other content listed here that too many titles might be excluded with CH4 networks).
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]}, # tt0247882
																{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]}, # tt26765082
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # tt3079768
																{MetaCompany.CompanyYoutube		: [MetaProvider.CompanyNetwork]}, # tt10589896, tt7356206, tt13664658
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # tt6917254
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]}, # tt1355237, co0007546
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]}, # tt6459140
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]}, # Not for tt29964473, tt6599010.
																#{MetaCompany.CompanyDiscovery	: [MetaProvider.CompanyNetwork]}, # Not for tt10627334.
																#{MetaCompany.CompanyBbc			: [MetaProvider.CompanyNetwork]}, # Not for tt21438656.

																'co0037052', # American Broadcasting Company (ABC) (tt0057733, tt0059968, tt0073972)
																'co0072315', # National Broadcasting Company (NBC) (tt1568769)
																'co0006166', # Imagine Television (tt1598754)
																'co0143473', # Galileo Medien (tt0138956)
																'co0803061', # Multichoice Studios (tt22009132)
																'co0070627', # CBS (tt0051327)
																'co0339529', # Tanweer Films (tt1697033)
																'co0867829', # Fubo TV (tt22003362)
																'co0335765', # Just Bridge Entertainment (tt1069207)
																'co0028689', # Manga Entertainment (tt0096816)
																'co0493506', # iQIYI (tt10048660)
																'co0856769', # Plex (tt25030226)
																'co0585065', # Viceland (tt5866048, tt5868744)
																'co0013582', # Teletoon (tt13183442)
																'co0609886', # Dekkoo (tt4882470)
																'co0725481', # DAZN (tt9427758)
																'co0264223', # Youku (tt11705374)
																'co0741784', # Dust (tt13097906)
																'co0077924', # Discovery Communications (tt0386175)
																'co0033658', # New Dominion Pictures (tt0358809)
																'co0183230', # Warner Horizon Television (tt8888210)
																'co0003850', # Nippon Television Network (NTV) (tt1499872)
																'co0341688', # Buffalo 8 Productions (tt5612996)
																'co0620095', # FOX 10 Phoenix (tt6341364)
																'co0438288', # PAC-12 Network (tt6341364)
															],
														},
														Media.Movie : {
															'allow' : [
																'co0103528', # Channel 4 Television Corporation (too much other content listed here that too many titles might be excluded with CH4 networks).
															],
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyChannel4		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyYoutube		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPluto			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},

																'co0335765', # Just Bridge Entertainment (tt1242432)
																'co0339529', # Tanweer Films (tt1560747)
																'co0067793', # Anchor Bay Entertainment (tt0756683)
																'co0003079', # Concorde Home Entertainment (tt3410834)
																'co0172129', # Mill Creek Entertainment (tt0083976)
																'co0268731', # Cinedigm Entertainment Group (tt3294200)
																'co0006126', # Audio Visual Enterprises (tt0092860)

																'co0024325', # Dutch FilmWorks (DFW)
																'co0037052', # American Broadcasting Company (ABC)
																'co0072315', # National Broadcasting Company (NBC)
																'co0070627', # CBS
															],
														},
													},
					MetaProvider.CompanyStudio		: [],
					MetaProvider.CompanyNetwork		: ['co0724460', 'co0866625', 'co0983179'],
					MetaProvider.CompanyVendor		: [],
				},
				MetaCompany.CompanyTurner : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0045447', 'co0099229', 'co0046564', 'co0064735', 'co0040732', 'co0458361', 'co0150930', 'co0781641', 'co0079227', 'co0728074', 'co0159949', 'co0981578', 'co0971288', 'co0900992', 'co0748955', 'co0662531', 'co0471992', 'co0453802', 'co0446580', 'co0198473', 'co0142333', 'co0098174', 'co0038957', 'co0007241'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0183824', 'co0093282', 'co0084770', 'co0134695', 'co0386603', 'co0009902', 'co0134697', 'co0000078', 'co0147819', 'co0337017', 'co0213389', 'co0381252', 'co0228203', 'co1005738', 'co0974338', 'co0840781', 'co0507520', 'co0397542', 'co0379858', 'co0342533', 'co0206108', 'co0147789', 'co0969989', 'co0917898', 'co0850163', 'co0808042', 'co0639907', 'co0606930', 'co0580410', 'co0386061', 'co0310903', 'co0219076', 'co0199827'],
				},
				MetaCompany.CompanyUniversal : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0005073', 'co0046592', 'co0021358', 'co0129175', 'co0195910', 'co0242101', 'co0769928', 'co0202966', 'co0196576', 'co0359888', 'co0598523', 'co0186420', 'co0186606', 'co0770762', 'co0080319', 'co0040731', 'co0443986', 'co0242700', 'co0216142', 'co0066651', 'co0882993', 'co0453011', 'co0751260', 'co0302927', 'co0733397', 'co0438125', 'co0514005', 'co0163456', 'co0118092', 'co0818184', 'co0313476', 'co0284326', 'co0272828', 'co0064407', 'co0608727', 'co0486437', 'co0485242', 'co0263504', 'co0242277', 'co0175276', 'co0048374', 'co0029904', 'co0574746', 'co0338344', 'co0086865', 'co0075806', 'co1048379', 'co0451692', 'co0035434', 'co0018727', 'co0017927'],
					MetaProvider.CompanyNetwork		: ['co0046592', 'co1013700', 'co0667778', 'co0227561', 'co0440561', 'co0305757', 'co0365525', 'co0770762', 'co0603572', 'co0356636', 'co0395977', 'co0464716', 'co0420019', 'co0326139', 'co0465167', 'co0420018', 'co1006786', 'co0878217', 'co0470442', 'co0464717', 'co0406983', 'co0406980', 'co0323517'],
					MetaProvider.CompanyVendor		: ['co0005073', 'co0023827', 'co0026044', 'co0251089', 'co0060214', 'co0219586', 'co0048238', 'co0297627', 'co0183709', 'co0388514', 'co0105063', 'co0131785', 'co0215138', 'co0198457', 'co0021358', 'co0219620', 'co0375381', 'co0021294', 'co0215174', 'co0219608', 'co0666801', 'co0215230', 'co0067464', 'co0110681', 'co0820078', 'co1003954', 'co0035519', 'co0814477', 'co0533783', 'co0117467', 'co0000534', 'co0129175', 'co0215234', 'co0824421', 'co0794561', 'co0768338', 'co0816494', 'co0241799', 'co0295614', 'co0236977', 'co0215157', 'co0215102', 'co0474968', 'co0854301', 'co0233831', 'co0824424', 'co0030491', 'co0055622', 'co0770680', 'co0195910', 'co0743251', 'co0811906', 'co0812374', 'co0656151', 'co0600878', 'co0137262', 'co0752505', 'co0141128', 'co0429910', 'co0305143', 'co0811907', 'co0565929', 'co0055043', 'co0813571', 'co0840675', 'co0063715', 'co0320855', 'co0056049', 'co0459508', 'co0820080', 'co0180647', 'co0028565', 'co0842674', 'co0151315', 'co0304386', 'co0565928', 'co0710991', 'co0824425', 'co0353649', 'co0752504', 'co0809355', 'co0800079', 'co0872541', 'co0251706', 'co0199066', 'co0184745', 'co0108183', 'co0762550', 'co0121774', 'co0844550', 'co0234421', 'co0824435', 'co0196211', 'co0345290', 'co0688663', 'co0202418', 'co0047319', 'co0820079', 'co0813065', 'co0651230', 'co0443270', 'co0420666', 'co0388893', 'co0205372', 'co0198120', 'co0046866', 'co0379771', 'co0246106', 'co0233644', 'co0196530', 'co0066651', 'co0524308', 'co0292422', 'co0823296', 'co0410007', 'co0240556', 'co0117469', 'co0899185', 'co0838692', 'co0408923', 'co0215112', 'co0548735', 'co0523203', 'co0487454', 'co0380632', 'co0196214', 'co0839122', 'co0835320', 'co0824436', 'co0722053', 'co0682067', 'co0592768', 'co0261403', 'co0223327', 'co0197667', 'co0030676', 'co0751668', 'co0704497', 'co0643665', 'co0256170', 'co0235121', 'co0226568', 'co0213976', 'co0076154', 'co0074924', 'co0053942', 'co0824611', 'co0824439', 'co0775963', 'co0573772', 'co0570325', 'co0542755', 'co0497044', 'co0468247', 'co0458146', 'co0315124', 'co0291326', 'co0215160', 'co0093119', 'co0018085', 'co0983635', 'co0879192', 'co0852261', 'co0797158', 'co0758126', 'co0728905', 'co0514291', 'co0497968', 'co0215092', 'co0140049', 'co0049911', 'co0034656', 'co0023945', 'co0021866', 'co1060162', 'co1021678', 'co0981888', 'co0919416', 'co0879183', 'co0867345', 'co0859748', 'co0843089', 'co0824438', 'co0725110', 'co0691059', 'co0679150', 'co0648656', 'co0648655', 'co0647543', 'co0616374', 'co0572760', 'co0570326', 'co0555207', 'co0517613', 'co0454780', 'co0454779', 'co0416933', 'co0412392', 'co0385643', 'co0361097', 'co0340231', 'co0309423', 'co0233867', 'co0232391', 'co0215218', 'co0215215', 'co0215193', 'co0213416', 'co0193613', 'co0189485', 'co0030062', 'co0967328', 'co0896256', 'co0804920', 'co0800639', 'co0784876', 'co0784875', 'co0773033', 'co0726722', 'co0722000', 'co0721999', 'co0721998', 'co0721997', 'co0715061', 'co0715059', 'co0694362', 'co0679102', 'co0658490', 'co0648654', 'co0636388', 'co0632635', 'co0405240', 'co0353338', 'co0330119', 'co0318230', 'co0305123', 'co0260407', 'co0244009', 'co0243802', 'co0220548', 'co0215283', 'co0215282', 'co0215271', 'co0215243', 'co0215185', 'co0162928', 'co0140051', 'co0125927', 'co0125160', 'co0063145', 'co0042035', 'co0006624'],
				},
				MetaCompany.CompanyUsa : {
					# Show (283): Level-3 or Level 4. Quite a lot of NBC Originals that cannot be filtered out.
					# Movie (247): Level-2.
					# USA content appear not only on NBC and other Universal channels, but also Netflix and Amazon.
					# Contains a lot of syndication television (rights leased out to multiple channels at the same time), like Xena, Highlander, and Hercules.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# Studios USA
																# Too many titles that are actually NBC, CBS, or ABC originals.
																# Most (close to all) USA Originals are also listed under another USA company, with a few exceptions (tt0098844).
																'co0082039', 'co0069685', 'co0082039', 'co0046901', 'co0027352',
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]}, # Not for tt6110648, tt0098844.
																#{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]}, # Not for tt6048596, tt4209256, tt6233618.
																#{MetaCompany.CompanyFox				: [MetaProvider.CompanyNetwork]}, # Not for tt0810788, tt4209256, tt2393813.
																#{MetaCompany.CompanyFx				: [MetaProvider.CompanyNetwork]}, # Not for tt0810788.
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # Not for tt0810788, tt1442437, tt7235466.
																#{MetaCompany.CompanyPeacock			: [MetaProvider.CompanyNetwork]}, # Not for tt14129378.
																#{MetaCompany.CompanySyfy				: [MetaProvider.CompanyNetwork]}, # Not for tt8388390, tt0314979, tt0220238.
																#{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]}, # Not for tt0389564.
																#{MetaCompany.CompanyHbo				: [MetaProvider.CompanyNetwork]}, # tt0103488. Not for tt0389564.
																#{MetaCompany.CompanyHulu				: [MetaProvider.CompanyNetwork]}, # Not for tt3205236
																{MetaCompany.CompanyCartoonnet		: [MetaProvider.CompanyNetwork]}, # tt0084972, tt0086824, tt0115226.

																#'co0037052', # American Broadcasting Company (ABC) (tt1442437)
																#'co0209226', # ABC Signature. Not for tt0312172.
																# 'co0721120', # Disney+ (tt1442437, tt7235466). Not for tt1358522.
																#'co0013021', # Walt Disney Television (tt7235466). Not for tt0312172.

																'co0037052', # American Broadcasting Company (ABC) (tt1442437)
																'co0276440', # Reamworks (tt7235466)
																'co0070627', # CBS (tt0086765, tt0112022, tt0098878, tt1378167)
																'co0276665', # CBS Studios International (tt0098948)
																'co0041673', # The Baywatch Company (tt0096542)
																'co0014456', # ARTE (tt11846996)
																'co0011191', # Gaumont Television (tt0103442)
																#'co0053559', # Paramount Television (tt0106123). Too many originals that are produced or broadcast by Paramount as well (eg tt0389564).
																'co0030480', # Rysher Entertainment (tt0106123). Seems to be synidcation TV, so correctly excludes other synidcation titles (tt0103442).
																'co0050878', # Black Entertainment Television (BET) (tt0103488)
																'co0727603', # Syndication (tt0120974)
																'co0200336', # 25/7 Productions (tt0429318)
																'co0111263', # Fox World (tt0273025)
																'co0065384', # BKN (tt0140749, tt0211867)
															],
														},
														Media.Movie : {
															'exclude' : [
																#{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # tt0405422
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]}, # tt0099938
																{MetaCompany.CompanyTnt			: [MetaProvider.CompanyNetwork]},
																#{MetaCompany.CompanySyfy			: [MetaProvider.CompanyNetwork]}, # Not for tt0991178.
																{MetaCompany.CompanyCrunchyroll	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyStudio]},

																'co0031085', # Argentina Video Home (tt0106677)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0014957', 'co0043969', 'co0082039', 'co0107062', 'co0044731', 'co0055632', 'co0055632'],
					MetaProvider.CompanyNetwork		: ['co0014957', 'co0069685', 'co0043969', 'co0019361', 'co0006634', 'co0082039', 'co0077920', 'co0107062', 'co0094214', 'co0058588', 'co0005674', 'co0724032', 'co0055632', 'co0046901', 'co0027352'],
					MetaProvider.CompanyVendor		: ['co0429394', 'co0198469', 'co0419861'],
				},
				MetaCompany.CompanyWarner : {
					# Show (114): Level-3
					# Movie (59): Level-3
					# The WB is now disfunct. Most of its content is now on The CW and HBO, but also a lot on other competing channels (Disney, ABC, etc).
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'fixed' : [
																# The WB only, since other Warner channels have too much other content.
																'co0077535',
																'co0569058',
															],
														},
														Media.Show : {
															'allow' : [
																'co0001860', # United Paramount Network (UPN) (tt0118276, tt0201391)
															],
															'exclude' : [
																{MetaCompany.CompanyParamount			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]}, # tt0121955, tt0159206, tt0060028, tt0115341
																#{MetaCompany.CompanyCartoonnet	: [MetaProvider.CompanyNetwork]}, # tt0168366. Not for tt0238784.
																{MetaCompany.CompanyUniversal			: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]}, # tt0112230.
																#{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork]}, # tt0426371. Not for tt0238784, tt0118276.

																'co0005861', # HBO Films (tt0185906)
																'co0028689', # Manga Entertainment (tt0168366)
																'co0037052', # American Broadcasting Company (ABC) (tt0312081)
																'co0039462', # Public Broadcasting Service (PBS) (tt0063951)
																#'co0070925', # Fox Network (tt0255734). Not for tt0162065.
																'co0172644', # Toon Disney (tt0426371)
																'co0213225', # Disney-ABC Domestic Television (tt0118466)
																#'co0050794', # ABC Family (tt0255734). Not for tt0318883.
																'co1013700', # Universal Toons (tt0259141)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNetflix			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyPeacock			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyParamount			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDisney			: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal			: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury		: [MetaProvider.CompanyVendor]},

																'co0037052', # American Broadcasting Company (ABC) (tt0088206)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0002663', 'co0005035', 'co0072876', 'co0863266', 'co0137898', 'co0183230', 'co0314266', 'co0064773', 'co0725649', 'co0106448', 'co0468593', 'co0546827', 'co0968965', 'co0623967', 'co0205800', 'co0050690', 'co0768835', 'co0646652', 'co0579299', 'co0041822', 'co0689167', 'co0542039', 'co0057786', 'co0784743', 'co0612253', 'co0879145', 'co0565728', 'co0253255', 'co0812623', 'co0662241', 'co0391813', 'co0661753', 'co0059798', 'co0003381', 'co0274647', 'co0256403', 'co0110958', 'co0065023', 'co0012442', 'co0907088', 'co0837070', 'co0733785', 'co0652719', 'co0604772', 'co0216236', 'co0212511', 'co0893584', 'co0636018', 'co0614052', 'co0371351', 'co0304934', 'co0279994', 'co0152143', 'co1063267', 'co1044762', 'co1008104', 'co0913697', 'co0858861', 'co0823881', 'co0823040', 'co0809022', 'co0806515', 'co0747991', 'co0675376', 'co0658156', 'co0631770', 'co0612161', 'co0591733', 'co0507517', 'co0378906', 'co0216628', 'co0211276', 'co0129483', 'co0121034', 'co0070192', 'co0063400', 'co0198927', 'co0189247'],
					MetaProvider.CompanyNetwork		: ['co0077535', 'co0068578', 'co0108606', 'co0204431', 'co0919124', 'co0909338', 'co0545732', 'co1064788', 'co0740777', 'co0301671', 'co1014492', 'co0569058', 'co1010891', 'co0893585', 'co0065120', 'co1063231', 'co0908564', 'co0983586', 'co0909047'],
					MetaProvider.CompanyVendor		: ['co0059995', 'co0002663', 'co0189793', 'co0089683', 'co0812621', 'co0270424', 'co0342489', 'co0200179', 'co0006383', 'co0214905', 'co0142160', 'co0498895', 'co0087314', 'co0535067', 'co0135321', 'co0106012', 'co0125154', 'co0101941', 'co0106070', 'co0110090', 'co0011555', 'co0438107', 'co0372744', 'co0692919', 'co0118308', 'co0256390', 'co0134706', 'co0056265', 'co0302997', 'co0077674', 'co0075764', 'co0158349', 'co0519888', 'co0053539', 'co0006819', 'co0863266', 'co0307857', 'co0350543', 'co0094757', 'co0176140', 'co0705983', 'co0816712', 'co0720464', 'co0782945', 'co0040785', 'co0770152', 'co0094779', 'co0504146', 'co0032440', 'co0705982', 'co0183230', 'co0350637', 'co0214931', 'co0858195', 'co0081227', 'co0565132', 'co0076018', 'co0239855', 'co0758947', 'co0456097', 'co0421999', 'co0120631', 'co0301198', 'co0187668', 'co0934836', 'co0826866', 'co0626392', 'co0220585', 'co0764931', 'co0870245', 'co0940463', 'co0918687', 'co0064773', 'co0725649', 'co0633129', 'co0108012', 'co0850083', 'co0810652', 'co0209324', 'co0218220', 'co0535056', 'co0128866', 'co0106448', 'co0804751', 'co0287772', 'co0009906', 'co0870244', 'co0512860', 'co0002939', 'co0029726', 'co0237555', 'co0619970', 'co0123357', 'co0215074', 'co0185616', 'co0505091', 'co0402893', 'co0225995', 'co0796988', 'co0304370', 'co0286417', 'co0185428', 'co0162942', 'co0162942', 'co0362429', 'co0046746', 'co0038141', 'co0179187', 'co0072019', 'co0920944', 'co0563079', 'co0290255', 'co0245917', 'co0101954', 'co0094755', 'co0078954', 'co0991324', 'co0364444', 'co0497928', 'co0495055', 'co0227665', 'co0221830', 'co0007935', 'co0959586', 'co0812966', 'co0537026', 'co0297444', 'co0258778', 'co0197868', 'co0152618', 'co0030066', 'co0028883', 'co0882558', 'co0830537', 'co0679446', 'co0516429', 'co0237970', 'co0179125', 'co0051678', 'co0013187', 'co1017479', 'co0825783', 'co0730604', 'co0724683', 'co0664213', 'co0649990', 'co0427039', 'co0154279', 'co0118328', 'co0108205', 'co0075148', 'co1022038', 'co0819108', 'co0570824', 'co0504952', 'co0491625', 'co0445543', 'co0423665', 'co0416202', 'co0166128', 'co0139177', 'co0108370', 'co0039510', 'co1009463', 'co1005816', 'co0904295', 'co0823159', 'co0822856', 'co0815746', 'co0780034', 'co0738220', 'co0725007', 'co0724684', 'co0705919', 'co0654365', 'co0609695', 'co0416473', 'co0335868', 'co0219725', 'co0113272', 'co0106320', 'co0030701', 'co0836843', 'co0813815', 'co0775557', 'co0748065', 'co0701804', 'co0620395', 'co0505090', 'co0453813', 'co0403730', 'co0399929', 'co0352118', 'co0256160', 'co0252812', 'co0245148', 'co0244887', 'co0225757', 'co0206213', 'co0191174', 'co0177654', 'co0131854', 'co0131608', 'co0077865', 'co0070086', 'co0052955', 'co0043200', 'co0031809', 'co0025297', 'co0017870', 'co1063179', 'co1051569', 'co1031570', 'co1031569', 'co1031568', 'co0932647', 'co0840651', 'co0817266', 'co0805127', 'co0769869', 'co0764429', 'co0764375', 'co0747433', 'co0745167', 'co0738052', 'co0725008', 'co0676595', 'co0626379', 'co0544343', 'co0543922', 'co0524188', 'co0502853', 'co0497383', 'co0497257', 'co0491626', 'co0427898', 'co0410678', 'co0382216', 'co0357957', 'co0312698', 'co0298415', 'co0227481', 'co0224399', 'co0146101', 'co0125165', 'co0117476', 'co0112558', 'co0104518', 'co0077784', 'co0060316', 'co0056681', 'co0031565', 'co0004441', 'co1058424', 'co1040646', 'co0981172', 'co0937798', 'co0856617', 'co0793828', 'co0793828', 'co0670752', 'co0662755', 'co0635467', 'co0502722', 'co0498720', 'co0453812', 'co0395391', 'co0352634', 'co0339073', 'co0333669', 'co0308496', 'co0240701', 'co0218114', 'co0194242', 'co0183782', 'co0173783', 'co0150853', 'co0108196', 'co0011676'],
				},
				MetaCompany.CompanyWeinstein : {
					MetaProvider.CompanyOriginal	: {},
					MetaProvider.CompanyStudio		: ['co0150452'],
					MetaProvider.CompanyNetwork		: [],
					MetaProvider.CompanyVendor		: ['co0368345', 'co0446953', 'co0210128', 'co0349607'],
				},
				MetaCompany.CompanyYoutube : {
					# Show (176): Level-4
					# Movie (54): Level-4
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'disallow' : [
																# YouTube
																'co0202446', 'co1017567', 'co0925788', 'co1020655', 'co1009431', 'co1038049', 'co1025883',
																'co1055457', # tt0090440, tt7887026, tt2795864
																'co0883766', # tt6145566, tt26674106, tt27446268
															],
														},
														Media.Show : {
															'exclude' : [
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyApple			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmazon		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyDreamworks	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyConstantin	: [MetaProvider.CompanyVendor]},

																'co0449307', # Weltkino Filmverleih (tt4420704)
																'co0814477', # Universal Pictures Home Entertainment (tt7069740)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0715084', 'co0722763'],
					MetaProvider.CompanyNetwork		: ['co0202446', 'co1055457', 'co0715084', 'co1017567', 'co0574035', 'co0847367', 'co0883766', 'co0925788', 'co1020655', 'co0722763', 'co0687834', 'co0494570', 'co1045018', 'co1009431', 'co0701624', 'co1038049', 'co1025883'],
					MetaProvider.CompanyVendor		: ['co0506705', 'co0457964', 'co0932994', 'co0711702', 'co0702332', 'co0506486', 'co0957563'],
				},
				MetaCompany.CompanyZdf : {
					# Show (2161): Level-2 to Level-3
					# Movie (6858): Level-1 to Level-2
					# Has tons of non-original content from US, UK, and other countries. Very difficult to filter, especailly the BBC content.
					# In the future, we should try to exclude all the co-productions (France, Denmark, Sweden, etc), maybe by excluding networtks for those countries.
					MetaProvider.CompanyOriginal	: {
														Media.Unknown : {
															'allow' : [
																'co0043107', # British Broadcasting Corporation (BBC)
															],
															'disallow' : [
																# It seems that most ZDF Originals are listed under Zweites Deutsches Fernsehen (ZDF) (co0078814).
																# US and other non-original content is typically on ZDFneo, ZDF Mediathek, etc.
																'co0364332', # ZDF Mediathek
																'co0284784', # ZDFneo
																'co0174795', # ZDF/Arte (too much French content)

																# KiKa
																'co0196399', 'co0030553', 'co0895262', 'co0937862', 'co1050978',
															],
														},
														Media.Show : {
															'exclude' : [
																#{MetaCompany.CompanyNetflix		: [MetaProvider.CompanyNetwork]}, # tt2294189, tt13925166, tt7263154. Not for tt8879894, tt6811236.
																{MetaCompany.CompanyHbo			: [MetaProvider.CompanyNetwork]}, # tt0141842, tt11847842
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyCbs			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAbc			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyFox			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyFx			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyShowtime		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyNickelodeon	: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDiscovery		: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyUsa			: [MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyAmc			: [MetaProvider.CompanyNetwork]}, # tt3032476, tt1399664
																{MetaCompany.CompanyHulu			: [MetaProvider.CompanyNetwork]}, # tt0412253
																{MetaCompany.CompanyHistory		: [MetaProvider.CompanyNetwork]}, # tt1542981, tt4316650
																#{MetaCompany.CompanyAe			: [MetaProvider.CompanyNetwork]}, # tt0112130. Not for tt0253839.

																# There might be legitimit co-productions here, but there are too many UK titles cluttering the menu.
																{MetaCompany.CompanyBbc			: [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork]}, # tt2294189, tt11847842
																{MetaCompany.CompanyItv			: [MetaProvider.CompanyNetwork]}, # tt0118401

																'co0062107', # Toei Animation (tt0122336)
																'co0103544', # BBC Northern Ireland (tt2294189)
																'co0129827', # BBC Birmingham (tt7526498)
																'co0293180', # Werner Film Productions (tt13925166)
																'co0785317', # De Mensen (tt7263154)
																'co0103820', # Company Pictures (tt1430509)
																'co0421199', # Monster Scripted AS (tt11204154)
																'co0290683', # Channel 4 Television (tt13125694)
																'co0338519', # Yellow Film & TV (tt6800294)
																'co0048965', # Chestermead (tt0112130)
																'co0042496', # Cinemax (tt9074360)
																'co0545989', # Belga Productions (tt13079194)
															],
														},
														Media.Movie : {
															'exclude' : [
																{MetaCompany.CompanyBbc			: [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork]},
																{MetaCompany.CompanyDisney		: [MetaProvider.CompanyStudio, MetaProvider.CompanyVendor]},

																{MetaCompany.CompanySony			: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyWarner		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyUniversal		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyColumbia		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyMgm			: [MetaProvider.CompanyVendor]},
																{MetaCompany.Company20thcentury	: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyParamount		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyLionsgate		: [MetaProvider.CompanyVendor]},
																{MetaCompany.CompanyTouchstone	: [MetaProvider.CompanyVendor]},

																'co0150452', # The Weinstein Company (tt1126590)
															],
														},
													},
					MetaProvider.CompanyStudio		: ['co0174795', 'co0038987', 'co0222794', 'co0908556', 'co0075883', 'co0196399', 'co0297730', 'co0678159', 'co1040317', 'co0622438', 'co0576396'],
					MetaProvider.CompanyNetwork		: ['co0078814', 'co0364332', 'co0030553', 'co0284784', 'co0895262', 'co0937862', 'co0269033', 'co0178657', 'co0337126', 'co1069160', 'co0989446', 'co0126641', 'co1050978', 'co0187579', 'co0993663', 'co0993978', 'co1035686', 'co0866170', 'co0949312', 'co0473935'],
					MetaProvider.CompanyVendor		: ['co0572131', 'co0236711'],
				},
			}
		return MetaImdb.Companies

	##############################################################################
	# CONVERT
	##############################################################################

	@classmethod
	def _convertCompanies(self, media = None, niche = None, company = None, studio = None, network = None, inverse = False, default = None):
		company = self.company(niche = niche, company = company, studio = studio, network = network)
		if not company: return None

		setting = Language.settingsCode(code = Language.CodePrimary)
		original = {}
		data = {
			None							: [],
			MetaProvider.CompanyStudio		: [],
			MetaProvider.CompanyNetwork		: [],
			MetaProvider.CompanyVendor		: [],
		}
		for k, v in company.items():
			values = []
			disallow = []
			for j in v if Tools.isList(v) else [v]:
				if j == MetaProvider.CompanyProducer: j = [MetaProvider.CompanyStudio]
				elif j == MetaProvider.CompanyBroadcaster: j = [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork]
				elif j == MetaProvider.CompanyDistributor: j = [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]
				elif j == MetaProvider.CompanyOriginal:
					value = self._convertCompany(company = [k, j])
					if value:
						value1 = value.get(Media.Unknown) or {}
						if Media.isMovie(media): value2 = value.get(Media.Movie) or {}
						elif Media.isShow(media): value2 = value.get(Media.Show) or {}
						else: value2 = {}

						original[k] = {}
						for n in ['fixed', 'include', 'exclude', 'allow', 'disallow', 'language']:
							origin = Tools.listFlatten([[m] if Tools.isString(m) else m for m in [value1.get(n), value2.get(n)] if m])
							if n == 'language' and setting:
								for m in origin:
									language = next(iter(m.keys()))
									if not Tools.isArray(language): language = (language,)
									if any(m in language for m in setting): n = 'include'
									else: n = 'disallow'

									origin = next(iter(m.values()))
									if not original[k].get(n): original[k][n] = []
									original[k][n].extend(origin)
									if n == 'disallow': disallow.extend(origin)
							else:
								if not original[k].get(n): original[k][n] = []
								original[k][n].extend(origin)
								if n == 'disallow': disallow.extend(origin)

					if original.get(k, {}).get('fixed'): j = None
					else: j = [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork]
				else: j = [j]
				if j: values.extend(j)

			if values:
				values = Tools.listUnique(values)
				for j in values:
					if self._idMatchCompany(k, prefix = True):
						data.get(j, data[None]).append([k])
					else:
						value = self._convertCompany(company = [k, j])
						if value: data.get(j, data[None]).append([n for n in value if not n in disallow] if disallow else value)

		companies = []
		for i in [None, MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]: # Order is important, since we want to eg place studios before vendors, in case the URL gets cut off.
			value = data[i]
			if value:
				value = Tools.listInterleave(*value) # Interleave, so if there are multiple companies, the IDs with the most titles for each are added to the front of the list.
				if value: companies.extend(value)

		if original:
			all = MetaImdb.Companies
			data = {
				None							: [],
				MetaProvider.CompanyStudio		: [],
				MetaProvider.CompanyNetwork		: [],
				MetaProvider.CompanyVendor		: [],
			}
			for k, v in original.items():
				if v:
					allow = v.get('allow') or []
					disallow = v.get('disallow') or []
					for i in ['fixed', 'include', 'exclude']:
						value = v.get(i)
						if value:
							if Tools.isString(value): value = [value]
							for j in value:
								if Tools.isString(j) and self._idMatchCompany(j, prefix = True):
									if i == 'include' or i == 'fixed':
										if j in disallow: continue
									elif i == 'exclude':
										j = j.lstrip(MetaImdb.Negate)
										if j in allow: continue
										j = MetaImdb.Negate + j
									data[None].append([j])
								else:
									if i == 'fixed' and Tools.isString(j): j = {k : j}
									else: type = [MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor]
									if Tools.isDictionary(j):
										type = next(iter(j.values()))
										if Tools.isString(type): type = [type]
										j = next(iter(j.keys()))
									value2 = all.get(j)
									if value2:
										for m in type:
											value3 = value2.get(m)
											if value3:
												if i == 'include' or i == 'fixed': value3 = [n for n in value3 if not n in disallow]
												elif i == 'exclude': value3 = [(MetaImdb.Negate + n.lstrip(MetaImdb.Negate)) for n in value3 if not n.lstrip(MetaImdb.Negate) in allow]
												data[m].append(value3)

			# Interleave, so if there are multiple companies, the IDs with the most titles for each are added to the front of the list.
			# There might be so many IDs dropped, that we have to get the most important to the front.
			# Eg: [all-custom, first-10-networks, first-3-studios, first-5-vendors, next-10-networks, next-3-studios, next-10-vendors, remaining-networks, remaining-studios, remaining-vendors]
			competitors = [[], [], []]
			other = []
			for i in [[None, None], [MetaProvider.CompanyNetwork, 10, 10], [MetaProvider.CompanyStudio, 3, 3], [MetaProvider.CompanyVendor, 5, 10]]: # Network mostly more important here than studio.
				value = data[i[0]]
				if value:
					limit1 = i[1]
					if limit1 is None:
						competitors[0].extend(Tools.listInterleave(value))
					else:
						limit2 = i[2]
						competitors[0].extend(Tools.listInterleave([j[:limit1] for j in value]))
						competitors[1].extend(Tools.listInterleave([j[limit1:limit2] for j in value]))
						competitors[2].extend(Tools.listInterleave([j[limit2:] for j in value]))
			companies.extend(Tools.listFlatten(competitors))

		if companies:
			companies = Tools.listUnique(companies)
			include = []
			exclude = []

			for i in companies:
				if i.startswith(MetaImdb.Negate): exclude.append(i)
				else: include.append(i)

			for i in include:
				try: exclude.remove(MetaImdb.Negate + i)
				except: pass

			# IMDb has a maximum URL length, which throws an error when exceeded.
			#	414 Request-URI Too Large
			# When shortening the URL, this error is gone, but a new error arrises (probably because the server cannot handle that many IDs).
			#	HTTP ERROR 431
			# It seems that the max length is about 7190 (through trial and error).
			limit = 6700 # Allow some extra length for the remainder of the URL (190) and some more length (300) for other parameters in the niche menus (eg: Netflix Action originals.).
			string = 0
			result = []
			for i in (include + exclude): # Place excludes last, in case the URL gets too long and companies later in the string are ignored.
				string += len(i) + 3 + (2 if i.startswith(MetaImdb.Negate) else 0) # +3 because of URL-encoded comma, and +2 for exlusions (with the ! already taking up a character).
				if string >= limit: break
				result.append(i)

			if result: return result

		return None

	##############################################################################
	# PARAMETER
	##############################################################################

	def _parameterInitialize(self, link = None, media = None, niche = None, id = None, query = None, keyword = None, type = None, status = None, release = None, year = None, date = None, duration = None, rating = None, votes = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, group = None, gender = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, adult = None, filter = None, view = None, **parameters):
		result = {}

		if filter is None:
			# Many of the Explore menus have a lot of Hindi content, sometimes 50%+.
			# Another 10-20% is Turkish and Russian.
			# Check out the Comedy menu with "Best Rated" and "New Releases".
			# The same for the niche Enterprises menus.
			if Media.isExplore(niche) or Media.isEnterprise(niche): filter = MetaProvider.FilterStrict
			elif niche: filter = MetaProvider.FilterLenient
			else: filter = MetaProvider.FilterNone

		languageExclude = False
		if language is True:
			languageExclude = True
			language = None

		countryExclude = False
		if country is True:
			countryExclude = True
			country = None

		if genre is None: genre = []
		elif genre and not genre is True and not Tools.isArray(genre): genre = [genre]
		if language is None: language = []
		elif language and not language is True and not Tools.isArray(language): language = [language]
		if country is None: country = []
		elif country and not country is True and not Tools.isArray(country): country = [country]
		if certificate is None: certificate = []
		elif certificate and not certificate is True and not Tools.isArray(certificate): certificate = [certificate]

		isTitle = False
		isPerson = False
		isList = False
		isUser = False
		isRating = False

		isMovie = False
		isFeature = False
		isShort = False
		isSpecial = False
		isShow = False
		isMini = False
		isEpisode = False
		isDocu = False
		isAnime = False
		isDonghua = False
		isTelevision = False

		if link:
			isTitle = MetaImdb.PathSearchTitle in link
			isPerson = MetaImdb.PathSearchPerson in link
			isList = MetaImdb.PathList in link
			isUser = MetaImdb.PathUser in link
			isRating = MetaImdb.PathListRating in link

		if Media.isMovie(media):
			isMovie = True
			if Media.isFeature(niche): isFeature = True
			elif Media.isShort(niche): isShort = True
			elif Media.isSpecial(niche): isSpecial = True
		elif Media.isSerie(media):
			if Media.isShow(media): isShow = True
			elif Media.isEpisode(media): isEpisode = True
			if Media.isMini(niche): isMini = True
			if Media.isShort(niche): isShort = True

		if Media.isShort(niche) or MetaTools.GenreShort in genre or type in MetaImdb.TypesShort: isShort = True
		if Media.isMini(niche) or MetaTools.GenreMini in genre or type in MetaImdb.TypesMini: isMini = True
		if Media.isDocu(niche) or MetaTools.GenreDocumentary in genre: isDocu = True
		if Media.isAnime(niche) or MetaTools.GenreAnime in genre: isAnime = True
		if Media.isDonghua(niche) or MetaTools.GenreDonghua in genre: isDonghua = True
		if Media.isTelevision(niche) or MetaTools.GenreTelevision in genre: isTelevision = True

		# Short
		if isShort and isShow: genre.append(MetaTools.GenreShort)

		# Topic
		# Its possible to search for "anime" or "donghua" keywords.
		# But they return considerably less titles than searching by genre and language.
		if isAnime:
			genre.append(MetaImdb.GenreAnimation)
			language.append(MetaImdb.Primary + 'ja')
		elif isDonghua:
			genre.append(MetaImdb.GenreAnimation)
			language.append(MetaImdb.Primary + 'zh')
		elif Media.isTopic(niche):
			topic = self.mMetatools.nicheTopic(niche = niche, strict = True)
			if topic:
				topic = self._convertGenre(genre = topic) # Remove unsupported genres.
				if topic: genre.append(topic[0]) # Only add the first genre, since genres are ANDed instead of ORed.
				else: return None # Unsupported topic (eg: Soap).

		# Mood
		if Media.isMood(niche):
			mood = self.mMetatools.nicheMood(niche = niche)
			if mood:
				mood = self._convertGenre(genre = mood) # Remove unsupported genres.
				if mood: genre.append(mood[0]) # Only add the first genre, since genres are ANDed instead of ORed.
				else: return None # Unsupported mood.

		# Age
		if Media.isAge(niche):
			age = self.mMetatools.nicheAge(niche = niche, format = True)
			if age: date = age

		# Quality
		if Media.isQuality(niche):
			quality = self.mMetatools.nicheQuality(niche = niche, media = media)
			if quality:
				rating = quality
				if not votes and not Media.isPoor(niche) and not Media.isBad(niche):
					if Media.isSerie(niche): votes = 500
					elif Media.isShort(niche) or Media.isSpecial(niche): votes = 100
					elif Media.isTopic(niche): votes = 100
					else: votes = 1000
					votes = [votes, None]

		# Region
		if Media.isRegion(niche):
			region = self.mMetatools.nicheRegion(niche = niche)
			if region:
				if region.get('language'):
					language.extend([MetaImdb.Primary + i for i in region.get('language')]) # Primary languages are ORed, not ANDed.
					language = Tools.listUnique(language)
				if region.get('country'):
					country.extend([MetaImdb.Primary + i for i in region.get('country')]) # Primary countries are ORed, not ANDed.
					country = Tools.listUnique(country)

		# Audience
		if Media.isAudience(niche):
			age = Audience.TypeKid if Media.isKid(niche) else Audience.TypeTeen if Media.isTeen(niche) else Audience.TypeAdult
			certificates = self.mMetatools.nicheCertificate(age = age, media = media, unrated = False, format = False)
			if certificates:
				certificate.extend(certificates)
				certificate = Tools.listUnique(certificate)

		# Pleasure
		if Media.isPleasure(niche):
			pleasure = self._convertPleasure(pleasure = niche)
			if pleasure:
				if not keyword: keyword = []
				elif not Tools.isArray(keyword): keyword = [keyword]
				keyword.extend(pleasure)

		if genre:
			if isAnime:
				try: genre.remove(MetaTools.GenreAnime)
				except: pass
			if isDonghua:
				try: genre.remove(MetaTools.GenreDonghua)
				except: pass
			if isMini:
				try: genre.remove(MetaTools.GenreMini)
				except: pass
			if isTelevision:
				try: genre.remove(MetaTools.GenreTelevision)
				except: pass
			if isShort and not isShow:
				try: genre.remove(MetaTools.GenreShort)
				except: pass

			genreCount = len(genre)
			if filter >= MetaProvider.FilterLenient: genre = self._parameterGenre(genre = genre, niche = niche)
			genre = self._convertGenre(genre = genre, default = True)

			# Filter out unsupported genres, like "amime".
			# Unsupported genres can be returned, since we use "default = True" above, which allows us to pass MetaTools and MetaImdb genres into these functions.
			# Unlike other parameters, IMDb does not remove unknown genres like "anime" and will return no results.
			# Update: We now remove certain genres above.
			if genre: genre = [i for i in genre if not i.islower()]

			if not genre and genreCount: return None # Genre not supported for the genre menus.

		# ID
		if not id is None:
			if isTitle: result['role'] = id

		# Query
		if not query is None:
			if Tools.isArray(query): query = ' '.join(query)
			if isTitle: result['title'] = query
			elif isPerson: result['name'] = query

		# Keyword
		if not keyword is None:
			if Tools.isArray(keyword): keyword = ' '.join(keyword)
			if isTitle: result['keywords'] = keyword

		# Type
		if type is None:
			if isSpecial:
				type = MetaImdb.TypesSpecial
			elif isEpisode:
				type = MetaImdb.TypesEpisode
			elif isMini:
				type = MetaImdb.TypesMini
			elif isShow:
				if query: type = MetaImdb.TypesSearchShow
				else: type = MetaImdb.TypesShow
			elif isShort and not isShow:
				type = MetaImdb.TypesShort
			elif isTelevision:
				type = MetaImdb.TypesTelevision
			elif isMovie:
				# IMDb has updated their lists. Now also uses "feature" instead of "movie"
				#if isList or isUser: type = MetaImdb.TypesMovie # Lists use "movie" instead of "feature".
				#else: type = MetaImdb.TypesFeature # Do not add "movie" to searches, since it might return a few non-featured movies (eg: Documentary/Music).
				if query: type = MetaImdb.TypesSearchMovie
				else: type = MetaImdb.TypesFeature
			elif media is None:
				if query: type = MetaImdb.TypesSearch # Search accross media types.
				else:
					type = MetaImdb.TypesAll # Exclude video games, etc.
					if isList or isUser:
						type = Tools.copy(type)
						try: type.remove(MetaImdb.TypeMovieFeature)
						except: pass
						type.append(MetaImdb.TypeMovie)
		if not type is None: result['title_type'] = Tools.listUnique(self._parameterExclude(type))

		yeared = year[0] if (year and Tools.isArray(year)) else year
		past = not date and yeared and yeared <= Time.year() # Check before date is changed below.

		# Company
		# Place before date.
		company = self._convertCompanies(media = media, niche = niche, company = company, studio = studio, network = network)
		if company:
			result['companies'] = company
			if not date: date = True # Otherwise too many unreleased/upcoming titles are returned.

		# Status
		if not status is None:
			if status is True: status = MetaImdb.StatusAvailable
			elif status is False: status = MetaImdb.StatusUnavailable
			else: status = self._convertStatus(status = status)
			result['production_status'] = self._parameterExclude(status)

		# Release
		if not release is None:
			if sort is None:
				sort = MetaImdb.SortDate
				if order is None: order = MetaImdb.OrderDescending
			if release == MetaImdb.ReleaseNew:
				if date is None: date = [None if sort == MetaImdb.SortDate else Time.past(days = 365, format = Time.FormatTimestamp), Time.timestamp()]
			elif release == MetaImdb.ReleaseHome:
				if date is None: date = [None if sort == MetaImdb.SortDate else Time.past(days = 365, format = Time.FormatTimestamp), Time.timestamp()]
				if watch is None: watch = MetaImdb.Watches
			elif release == MetaImdb.ReleaseFuture:
				if date is None: date = [Time.future(days = 1, format = Time.FormatTimestamp), None]

		# Year
		if not year is None:
			if year is True: year = [None, Time.year()]
			elif year is False: year = [Time.year(), None]
			elif not Tools.isArray(year): year = [year, year]
			result['year'] = result['release_date'] = year # The new search does not have a year parameter, but the year can be passed as the date.

		# Date
		# Check the status, since sometimes production_status does not work.
		# Eg: If we retrieve the filmography/history of a person (sorted by release date), there are often a few unreleased titles listed.
		# Always add the date to make sure only released titles are returned.
		# Only do this if the year was not added, otherwise the old year parameter might not match the release date current timestamp.
		future = False
		if not date is None or (status == MetaImdb.StatusReleased and not result.get('year')):
			currentDate = Time.timestamp()

			if date is True or date is None: date = [None, currentDate]
			elif date is False: date = [currentDate, None]
			elif not Tools.isArray(date): date = [None, date]
			timestamp = any(Tools.isInteger(i) and i > 10000 for i in date) # Early timestamps can be small. Only assume timestamp at least one value is big.
			temp = []
			for i in date:
				if Tools.isInteger(i):
					if timestamp: i = Time.format(timestamp = i, format = Time.FormatDate)
					elif i < 0: i = Time.future(days = abs(int(i)), format = Time.FormatDate)
					else: i = Time.past(days = int(i), format = Time.FormatDate)
				temp.append(i)

			date = [Time.timestamp(fixedTime = i, format = Time.FormatDate, utc = True) for i in temp] # Timestamps used below for the Explore parameters and future calculation.
			result['release_date'] = temp

			futureDate = Time.timestamp(fixedTime = Time.future(days = 1, timestamp = currentDate, format = Time.FormatDate), format = Time.FormatDate, utc = True)
			future = any(not i is None and i > futureDate for i in date)

		# Duration
		if not duration is None:
			if Tools.isNumber(duration): duration = [int(duration / 60.0), None] # IMDb uses minutes.
			elif Tools.isArray(duration): duration = [int(i / 60.0) if i else None for i in duration]
			result['runtime'] = duration

		# Explore
		# Must be AFTER date section above, but BEFORE rating/votes section below.
		niched = [niche] if Tools.isString(niche) else Tools.copy(niche) if Tools.isArray(niche) else []
		if isAnime: niched.append(Media.Anime)
		if isDonghua: niched.append(Media.Donghua)
		rating, votes = self._voting(media = media, niche = niched, release = release, year = year, date = date, past = past, genre = genre, language = language, country = country, certificate = certificate, company = company, status = status, rating = rating, votes = votes, sort = True, active = True) # active=True: many users vote on IMDb.
		if Media.isExplore(niche):
			if Media.isAll(niche):
				pass
			elif Media.isNew(niche):
				if sort is None: sort = MetaImdb.SortDate
			elif Media.isHome(niche):
				if watch is None: watch = MetaImdb.Watches
				if sort is None: sort = MetaImdb.SortDate
			elif Media.isBest(niche):
				if sort is None: sort = MetaImdb.SortRating
			elif Media.isWorst(niche):
				if sort is None:
					sort = MetaImdb.SortRating
					order = MetaImdb.OrderAscending
			elif Media.isPrestige(niche):
				pass
			elif Media.isPopular(niche):
				if sort is None: sort = MetaImdb.SortVotes
			elif Media.isUnpopular(niche):
				if sort is None:
					sort = MetaImdb.SortVotes
					order = MetaImdb.OrderAscending
			elif Media.isViewed(niche):
				pass
			elif Media.isGross(niche):
				if sort is None: sort = MetaImdb.SortGross
			elif Media.isAward(niche):
				if group is None: group = MetaImdb.GroupEmmyWinner if Media.isSerie(media) else MetaImdb.GroupOscarWinner # Groups are ANDed, not ORed.
			elif Media.isTrend(niche):
				if sort is None: sort = MetaImdb.SortPopularity

			# Do not apply any voting restrictions on award menus.
			if group and not Media.isPrestige(niche) and not Media.isViewed(niche):
				rating = None
				votes = None

		if group and sort is None:
			sort = MetaImdb.SortRating
			if any(i in group or self._convertAward(award = i, inverse = True) in group for i in [MetaImdb.GroupBottom100, MetaImdb.GroupBottom250, MetaImdb.GroupBottom1000]): order = MetaImdb.OrderAscending
			else: order = MetaImdb.OrderDescending

		if Media.isExplore(niche):
			if date is None and not Tools.isArray(year): date = Time.timestamp() # Do not set for Decades menu.
			if sort is None: sort = MetaImdb.SortPopularity

		# Rating
		if not rating is None:
			if Tools.isString(rating):
				if rating == MetaProvider.VotingMinimal: rating = 0.0
				elif rating == MetaProvider.VotingLenient: rating = 1.0
				elif rating == MetaProvider.VotingNormal: rating = 3.0
				elif rating == MetaProvider.VotingModerate: rating = 5.0
				elif rating == MetaProvider.VotingStrict: rating = 7.5
				elif rating == MetaProvider.VotingExtreme: rating = 8.0
				else: rating = 4.0
			if not Tools.isArray(rating): rating = [rating, None]
			result['user_rating'] = rating

		# Votes
		if not votes is None:
			if Tools.isString(votes):
				if votes == MetaProvider.VotingMinimal: votes = 1
				elif votes == MetaProvider.VotingLenient: votes = 20
				elif votes == MetaProvider.VotingNormal: votes = 1000
				elif votes == MetaProvider.VotingModerate: votes = 5000
				elif votes == MetaProvider.VotingStrict: votes = 20000
				elif votes == MetaProvider.VotingExtreme: votes = 50000
				else: votes = 2000

				if Media.isSerie(media):
					votes = votes / 2.0
					if Media.isEpisode(media): votes = votes / 10.0
					elif Media.isSeason(media): votes = votes / 20.0
				elif Media.isSet(media) or Media.isList(media):
					votes = votes / 20.0

				if isDocu: votes = votes / 5.0
				elif isDonghua: votes = votes / 20.0
				elif isAnime or Media.isTopic(niche): votes = votes / 10.0

				if isShort: votes = votes / 20.0
				elif isTelevision: votes = votes / 10.0
				elif isSpecial: votes = votes / 25.0
				elif Media.isRegion(niche): votes = votes / 3.0

				if (Media.isKid(niche) or Media.isTeen(niche)) and votes: votes = int(votes * 0.75) # Reduce votes for kids.
				votes = Math.roundUp(votes)

			if not Tools.isArray(votes): votes = [votes, None]
			result['num_votes'] = votes

		# Genre
		if genre: result['genres'] = self._parameterExclude(genre)

		# Still allow these languages/countries for the region and award submenus.
		include = Media.isRegion(niche) or Media.isAward(niche)

		# Language
		if not language is None:
			primary = None

			# Mostly Indian and Turkish titles spamming some lists with titles not of interest to most users.
			if (languageExclude or filter >= MetaProvider.FilterStrict) and not country and not include:
				contains = [self._parameterClean(i) for i in language] if Tools.isArray(language) else []
				setting = Language.settingsCode(code = Language.CodePrimary)
				exclude = []
				excludes = [Language.CodeIndian, [Language.CodeTurkish]]

				for i in excludes:
					if not any(j in i for j in setting):
						if not Tools.isArray(language) or not any(j in contains for j in i):
							exclude.extend([MetaImdb.Primary + j for j in i])

				if exclude and not company: # Do not exclude for studios/networks, since enough are already excluded.
					primary, secondary = self._parameterPrimary(exclude)
					primary = self._parameterNegate(primary)
					secondary = self._parameterNegate(secondary)
					if secondary: language = secondary if (languageExclude or not language) else (language + secondary)
				elif languageExclude:
					language = None # Do not exclude if the user has selected a language setting.

			if language or primary:
				language = self._parameterExclude(language)
				primary2, secondary = self._parameterPrimary(language)
				primary = (primary or []) + (primary2 or [])
				if primary: result['primary_language'] = primary
				elif secondary: result['languages'] = secondary

		# Country
		if not country is None:
			primary = None

			# Mostly Indian and Turkish titles spamming some lists with titles not of interest to most users.
			if (countryExclude or filter >= MetaProvider.FilterStrict) and not language and not include:
				contains = [self._parameterClean(i) for i in country] if Tools.isArray(country) else []
				setting = Language.settingsCountry()
				exclude = []
				excludes = [['in'], ['tr']]

				# Currently do not do this. It seems the language filtering above removes the necessary India/Turkish titles.
				'''for i in excludes:
					if not any(j in i for j in setting):
						if not Tools.isArray(country) or not any(j in contains for j in i):
							exclude.extend([MetaImdb.Primary + j for j in i])'''

				if exclude and not company: # Do not exclude for studios/networks, since enough are already excluded.
					primary, secondary = self._parameterPrimary(exclude)
					primary = self._parameterNegate(primary)
					secondary = self._parameterNegate(secondary)
					if secondary: country = secondary if (countryExclude or not country) else (country + secondary)
				elif country is True:
					country = None # Do not exclude if the user has selected a language setting for that country.
			if country or primary:
				country = self._parameterExclude(country)
				country = [((MetaImdb.Negate if i.startswith(MetaImdb.Negate) else '') + 'gb') if i.lower().endswith('uk') else i for i in country] # IMDb uses "GB".
				primary2, secondary = self._parameterPrimary(country)
				primary = (primary or []) + (primary2 or [])
				if primary: result['country_of_origin'] = primary
				elif secondary: result['countries'] = secondary

		# Certificate
		if certificate:
			if len(certificate) == 1 and MetaImdb.CertificateNr in certificate: certificate = self._parameterNegate(MetaImdb.Certificates)
			for i in range(len(certificate)):
				if certificate[i] == Audience.CertificateNr: value = 'Unrated'
				else: value = Audience.format(certificate[i]) # Must be upper case.
				negate = value.startswith('-') or value.startswith('!')
				if negate: value = value.strip('-').strip('!')
				if not ':' in value: value = 'US:' + value
				if negate: value = MetaImdb.Negate + value
				certificate[i] = value
			result['certificates'] = self._parameterExclude(certificate)

		# Group
		if not group is None:
			if group is True:
				# Most IMDb parameters, except for title_type, use AND for a comma-separated list, not "OR"
				# Hence, specifying multiple groups requires a title to match ALL groups, not ANY group.
				# https://community-imdb.sprinklr.com/conversations/imdbcom/ats-support-for-or-searches-in-genres-countries-and-other-fields/5f4a79d48815453dba8c71d8
				if isMovie: group = MetaImdb.GroupOscarWinner
				elif isShow: group = MetaImdb.GroupEmmyWinner
			if not Tools.isArray(group): group = [group]

			# IMDb has changed there groups multiple times over the past weeks.
			# There is no consistency, sometimes using singular, other times plural.
			if isPerson:
				for i in range(len(group)):
					value = group[i]
					if value == MetaImdb.GroupGoldenGlobeWinner: group[i] = MetaImdb.GroupGoldenGlobeWinning
					elif value == MetaImdb.GroupGoldenGlobeNominee: group[i] = MetaImdb.GroupGoldenGlobeNominated
			group = self._convertAward(award = group, default = True)
			result['groups'] = self._parameterExclude(group)

		# Gender
		if (gender is None and isPerson) or gender is True: gender = list(MetaImdb.Genders.values()) # If not provided, IMDb does not return anything.
		if not gender is None:
			gender = self._convertGender(gender = gender, default = True)
			result['gender'] = self._parameterExclude(gender)

		# Watch
		if not watch is None:
			if not Tools.isArray(watch): watch = [watch]
			for i in range(len(watch)):
				value = watch[i]
				if value is True: value = MetaImdb.WatchesList if isList else MetaImdb.Watches
				elif value is False: value = self._parameterNegate(MetaImdb.WatchesList if isList else MetaImdb.Watches)
				watch[i] = value
			if watch:
				watch = Tools.listUnique(Tools.listFlatten(watch))
				if watch: result['watch_option' if isList else 'online_availability'] = self._parameterExclude(watch)

		# Theater
		if not theater is None:
			if not Tools.isArray(theater): theater = [theater]
			for i in range(len(theater)):
				value = theater[i]
				if value is True: value = MetaImdb.TheaterRelease
				elif isList and value == MetaImdb.TheaterFavorite: value = MetaImdb.TheaterListFavorite
				theater[i] = value
			if theater:
				theater = Tools.listUnique(Tools.listFlatten(theater))
				result['now_playing'] = self._parameterExclude(theater)

		# Limit
		if isList:
			if limit is None: limit = MetaImdb.LimitList
			limit = max(1, min(MetaImdb.LimitList, limit)) # 100 fixed page limit for old layout.
			if not limit is None: result['count'] = limit # This value is ignored.
			if not page is None: result['page'] = page # Uses different parameters to Advanced Search.
		else:
			if limit is None: limit = MetaImdb.LimitDefault
			limit = max(1, min(MetaImdb.LimitDiscover, limit)) # 250 maximum page limit. Higher values default to 50.
			if offset is None:
				offset = 1
				if page: offset += (page - 1) * limit
			if not limit is None: result['count'] = limit
			if not offset is None: result['start'] = offset

		# Sort
		if not sort is None:
			if sort == MetaImdb.SortPopularity:
				if isTitle: sort = MetaImdb.SortMovieMeter
				elif isPerson: sort = MetaImdb.SortStarMeter
				else: sort = None
			if not sort is None:
				if isRating: # Rating lists have different sorting parameters.
					if sort == MetaImdb.SortUserRating: sort = MetaImdb.SortListRating
					elif sort == MetaImdb.SortUserDate: sort = MetaImdb.SortListDate
				if order is None: order = MetaImdb.OrderDefault.get(sort)
				result['sort'] = [sort, order]

		# Adult
		if not adult is None:
			if adult is True: adult = MetaImdb.AdultInclude
			elif adult is False: adult = MetaImdb.AdultExclude
			if not adult is None: result['adult'] = adult

		# View
		if view is True or view is None: view = MetaImdb.ViewDetail
		elif view is False: view = MetaImdb.ViewSimple
		result['view'] = view
		result['mode'] = view # Depending on the list, might have both "view" and "mode" parameters.

		return result

	def _parameterExclude(self, value):
		if not Tools.isArray(value): value = [value]
		return [(MetaImdb.Negate + i.strip('-')) if i.startswith('-') else i for i in value]

	def _parameterPrimary(self, value):
		# Many English movies made in Hollywood are categorized under a European country (eg: John Wick 4 or Fight Club).
		# The new layout has an additional parameter "country_of_origin" that seems to only return primary countries, which is slightly better.
		# Instead of adding a new parameter for all functions, we just use the origin parameter if only one country was specified (eg: the Country menu).
		if not value: return None, None
		elif Tools.isString(value): value = [value]
		if len(value) == 1: value[0] = MetaImdb.Primary + value[0]
		return [i.replace(MetaImdb.Primary, '') for i in value if MetaImdb.Primary in i], [i for i in value if not MetaImdb.Primary in i]

	def _parameterNegate(self, value):
		return [MetaImdb.Negate + self._parameterClean(i) for i in value]

	def _parameterClean(self, value):
		return value.strip('-').strip(MetaImdb.Negate).strip(MetaImdb.Primary) if value else value

	def _parameterList(self, values):
		if Tools.isArray(values): values = ','.join([str(i) for i in values])
		return str(values)

	def _parameterGenre(self, genre, niche = None, include = None, exclude = None):
		if not genre: genre = []
		elif not Tools.isArray(genre): genre = [genre]

		if include is None: include = []
		elif not Tools.isArray(include): include = [include]

		if exclude is None: exclude = []
		elif not Tools.isArray(exclude): exclude = [exclude]

		if niche:
			check = []

			# Group Documentaries and Shorts together.
			# Since many docus are shorts and some short also docus.
			isDocu = Media.isDocu(niche) or MetaTools.GenreDocumentary in genre
			isShort = Media.isShort(niche) or MetaTools.GenreShort in genre
			if not isDocu and not isShort: check.extend([MetaImdb.GenreDocumentary, MetaImdb.GenreShort])

			for i in check:
				if not i in genre and not i in include: exclude.append(i)

		if include:
			genre.extend(include)

		if exclude:
			genre = [i for i in genre if not i in exclude]
			genre.extend(self._parameterNegate(exclude))

		return genre

	##############################################################################
	# LOG
	##############################################################################

	def _logFatal(self, id = None, code = None, update = None, missing = None):
		# Increase the IMDb error counter.
		# These errors should generally be seen as temporary errors, since it is mostly caused by temporary blocks after too many requests were made in a short period of time.
		if update: self._errorUpdate()

		details = ''
		if id and code: details = ' [%s - %s]' % (id, code)
		elif id: details = ' [%s]' % id
		elif code: details = ' [%s]' % code

		if missing: missing = 'This could also be due to missing data on IMDb, especially if it is very recent or future release.'
		else: missing = ''

		self._log(details, 'The IMDb data cannot be processed. This might be because too many requests where made in a short period of time and IMDb is temporarily blocking requests from your IP.' + missing, type = Logger.TypeFatal)
		return None

	def _logError(self, id = None, message = None, attribute = None):
		if MetaImdb.Debug and System.developerVersion():
			if id: id = ' [%s]' % id
			if not message: message = ''
			if attribute: message += (' ' if message else '') + ('The "%s" attribute cannot be extracted.' % str(attribute))
			self._log(id, message)
		return None

	##############################################################################
	# REQUEST
	##############################################################################

	def _retrieve(self, link, media = None, niche = None, lock = True, cache = None, **data):
		results = None
		try:
			result, link = self._request(method = Networker.MethodGet, link = link, media = media, niche = niche, lock = lock, cache = cache, internal = True, **data) # Formatted link is used for CSV lists.
			if result:
				if result == MetaImdb.Privacy: return result
				results = self._extractItems(data = result, link = link, media = media, niche = niche, genre = data.get('genre'), language = data.get('language'), country = data.get('country'), certificate = data.get('certificate'))
		except: Logger.error()
		return results

	# NB: timeout = CacheNone: do not cache the data by default, since IMDb pages can be 1MB+ (+-200KB GZIP) in size and quickly fill up disk space.
	# Therefore, do not cache, except if specifically requested, and let the extracted/summarized data be cached by MetaCache.
	# Use language_/country_ with an underscore to distinguish between the HTTP header attributes, and the IMDb GET parameters of the same name.
	def _request(self, link, media = None, niche = None, language_ = None, country_ = None, method = None, lock = True, cache = None, failsafe = True, full = False, internal = False, timeout = None, **data):
		try:
			if not MetaImdb.PathTitle in link and not MetaImdb.PathPerson in link: link = self._linkCreate(link = link, media = media, niche = niche, **data)
			if not link: return (None, link) if internal else None

			if lock: self._lock(limit = lock)
			if cache is MetaImdb.CacheNone:
				result = self._requestData(link = link, language = language_, country = country_, method = method, full = full, timeout_ = timeout)
			else:
				result = self._cache(timeout = cache, function = self._requestData, link = link, language = language_, country = country_, method = method, timeout_ = timeout)
				if (failsafe and result is False) or result == MetaImdb.Privacy: self._cacheDelete(function = self._requestData, link = link, language = language_, country = country_, method = method, timeout_ = timeout)
			return (result, link) if internal else result
		except:
			self._logError()
		finally:
			if lock: self._unlock(limit = lock)
		return (None, link) if internal else None

	def _requestData(self, link, data = None, language = None, country = None, method = None, full = False, timeout_ = None):
		if not data: data = {}
		if method is None: method = Networker.MethodGet

		self._usageUpdate()

		# Use a random user agent.
		# If too many requests are made within a short period of time, IMDb does not return the webpage, and Gaia throws this error:
		#	The IMDb data cannot be processed. This might be because too many requests where made in a short period of time and IMDb is temporarily blocking requests from your IP. Please contact the Gaia developer if you see this message.
		# Sometimes this already happens after 50-100 requests.
		# Not entirley certain if this actually works, but with a random agent these errors seem to be less frequent than with a fixed user agent.
		networker = Networker()
		result = networker.requestText(method = method, link = link, data = data, headers = self._requestHeaders(language = language, country = country), agent = Networker.AgentDesktopRandom, timeout = timeout_)

		error = networker.responseErrorType()
		if error and error in Networker.ErrorServer: self._errorUpdate()

		# Private watchlists (which is just a normal list) returns 404.
		# Private ratings lists returns 403.
		# If parameters are added to the request, IMDb returns an HTML page with: This list is not public. The creator of this list has not enabled public viewing.
		if MetaImdb.PathUser in link or MetaImdb.PathList in link:
			if networker.responseErrorCode() in [403, 404] or (result and 'This list is not public' in result):
				result = MetaImdb.Privacy
				Logger.log('The IMDb list is private and can only be retrieved if made public: ' + link, type = Logger.TypeError)
			elif networker.responseErrorNetwork():
				result = False

		return networker if full else result

	def _requestHeaders(self, language = None, country = None):
		# IMDb returns the website in the language specified in the headers (if supported).
		# In order to get (some) metadata and the poster in a specific language, set the Accept-Language header.
		headers = self.mMetatools.headerLanguage(language = language, country = country)

		# A raw IMDb page is arround 1MB+ in size (eg: "Accept-Encoding: identity").
		# A GZIP-ped IMDb page is under 200KB in size.
		# The data returned by Python's Requests will always have the text data size at +-1MB, because Requests already decompresses the data for us.
		# To get the actual uncompressed size, use:
		#	session.request(stream = True, method = 'GET', ...)
		#	size = len(response.raw.read()))
		# It seems that by default IMDb are returned with GZIP. Not sure if Requests does this, or if IMDb pages are always returned with GZIP by default (if no other Accept-Encoding header was set).
		# Just force the Accept-Encoding header to GZIP to  make sure we get lower-sized data.
		headers[Networker.HeaderAcceptEncoding] = 'gzip, deflate, br'

		return headers

	##############################################################################
	# CLEAN
	##############################################################################

	@classmethod
	def cleanTitle(self, data):
		return self._extractTitle(data = data)

	##############################################################################
	# EXTRACT
	##############################################################################

	def _extract(self, data, keys = None, result = None, attribute = None, function = None, id = None, log = True):
		if Tools.isDictionary(data): data = [data]
		for i in data:
			try:
				value = i if keys is None else Tools.dictionaryGet(dictionary = i, keys = keys)
				if not value is None:
					if function:
						if Tools.isList(function):
							for f in function:
								value = f(value)
						else:
							value = function(value)

					if not result is None and not value is None:
						if Tools.isArray(attribute):
							object = result
							for a in attribute[:-1]:
								if not a in object: object[a] = {}
								object = object[a]
							object[attribute[-1]] = value
						else:
							result[attribute] = value
					return value
			except: pass
		if log: self._logError(id = id, attribute = attribute)
		return None

	def _extractJson(self, data, full = True):
		try:
			# IMDb has JSON data stored inside the HTML.
			# There is a JSON object at the start of the HTML with only basic metadata.
			# But somewhere in the middle of the HTML there is a full JSON metadata object.
			# It is easier and more reliable to use the JSON data instead of extracting values from HTML.

			datas = self.parser(data = data).find_all('script', {'type' : 'application/json'})

			data = None
			for i in datas:
				try:
					i = Converter.jsonFrom(i.string)
					if 'props' in i:
						data = i
						break
				except: pass

			if full:
				try: data = data['props']['pageProps']
				except: data = None
		except: Logger.error()
		return data

	def _extractIdList(self, data):
		try:
			if data: return [item['id'] for item in data]
		except: Logger.error()
		return None

	def _extractIdListLower(self, data):
		try:
			if data: return [item['id'].lower() for item in data]
		except: Logger.error()
		return None

	def _extractMedia(self, data):
		try:
			if data in MetaImdb.TypesFilm or data in MetaImdb.TypesSpecial or data in MetaImdb.TypesShort: return Media.Movie
			elif data in MetaImdb.TypesEpisode: return Media.Episode
			elif data in MetaImdb.TypesSerie: return Media.Show
		except: Logger.error()
		return None

	def _extractNiche(self, data, item = None):
		try:
			niche = []
			if data == MetaImdb.TypeMovie or data == MetaImdb.TypeMovieFeature: niche.append(Media.Feature)
			if data == MetaImdb.TypeMovieTv or data == MetaImdb.TypeShortTv: niche.append(Media.Television)
			if data == MetaImdb.TypeShort or data == MetaImdb.TypeShortTv: niche.append(Media.Short)
			if data == MetaImdb.TypeSpecial: niche.append(Media.Special)

			if data == MetaImdb.TypeMiniseries:
				# Sometimes IMDb marks a show as mini-series, but there are more than one seasons.
				# Maybe a mistake on IMDb. The show was originally intended as a mini-series, but later they decide to add new seasons.
				# Eg: tt20234568 (mini-series type, but 2 seasons).
				multi = False
				if item:
					seasons = self._extract(data = item, keys = ['episodes', 'seasons'])
					if seasons:
						for season in seasons:
							season = season.get('number')
							if season and season > 1:
								multi = True
								break

				if multi: niche.append(Media.Multi)
				else: niche.append(Media.Mini)
			elif data == MetaImdb.TypeShow:
				niche.append(Media.Multi)

			if niche: return niche
		except: Logger.error()
		return None

	# Static, since it is called from cleanTitle().
	@classmethod
	def _extractTitle(self, data):
		try:
			if data:
				# Titles that are a pure number (eg: "1984") will be interpreted as an integer in CSVs. Cast to string.
				data = str(data)

				# Future/unreleased episodes use this format:
				#	Episode #4.1
				# Clean it to be consistent with other providers:
				#	Episode 1
				temp = Regex.extract(data = data, expression = '([a-z]+\s)\s*#(?:\d+\.)?(\d+)', group = None)
				if temp: data = temp[0] + temp[1]

				# Titles ending in a slash.
				# Eg: Nate Bargatze/Jessica Williams/Nicole Avant/Darlene Love/
				# Eg: Ray Romano/Rose/
				data = data.rstrip('/')

				return data
		except: Logger.error()
		return None

	def _extractList(self, data):
		try:
			if data:
				if ',' in data: data = data.split(',')
				elif not Tools.isArray(data): data = [data]
				return [i.strip() for i in data if i]
		except: Logger.error()
		return None

	def _extractRating(self, data):
		try:
			if data == 0: return None # Rating at 0.0.
			return float(data)
		except: Logger.error()
		return None

	def _extractVotes(self, data):
		try:
			if data == 0: return None # No votes cast.
			return int(data)
		except: Logger.error()
		return None

	def _extractImage(self, data):
		try:
			images = {i : [] for i in (None, MetaImage.TypePoster, MetaImage.TypeFanart, MetaImage.TypeThumb)}

			for i in data:
				try:
					i = i['node']
					link = self.linkImage(link = i['url'])
					if link:
						width = i.get('width') or 1
						height = i.get('height') or 1
						aspect = width / height

						# Eg: https://www.imdb.com/title/tt29425792/
						if aspect > 1: # Landscape
							item = {'link' : link, 'quality' : width}
							if width >= 800: images[MetaImage.TypeFanart].append(item)
							images[MetaImage.TypeThumb].append(item)
						else: # Potrait
							item = {'link' : link, 'quality' : height}
							# Sometimes the image is slightly potrait, but is not a poster, but rather some character.
							# https://m.media-amazon.com/images/M/MV5BYWFmNzRhYTUtY2M1ZS00OTM4LTljYzgtYmFjZjAxZmIxMTMxXkEyXkFqcGc@._V1_.jpg
							if aspect > 0.85: images[None].append(item)
							else: images[MetaImage.TypePoster].append(item)
				except: Logger.error()

			# Add the slightly portrait images as fanart/thumbnails if there are not any of those types.
			# Since those portrait images still look better as background than the poster.
			if images[None]:
				for i in (MetaImage.TypeFanart, MetaImage.TypeThumb):
					if not images[i]: images[i] = images[None]

			# Sort by highest resolution.
			result = {}
			for type, image in images.items():
				if type and image:
					image = Tools.listSort(data = image, key = lambda i : i['quality'], reverse = True)
					result[type] = [i['link'] for i in image]

			return result
		except: Logger.error()
		return None

	def _extractTime(self, data):
		try:
			if data: return Time.timestamp(data, format = '%Y-%m-%dT%H:%M:%SZ', utc = True)
		except: Logger.error()
		return None

	def _extractPremiered(self, data):
		try:
			year = None
			month = None
			day = None

			date = data.get('releaseDate')
			if date:
				if Tools.isDictionary(date):
					year = date.get('year')
					month = date.get('month')
					day = date.get('day')

					# Sometimes the date only has a year or a year+month for as few less-known titles.
					# If there is a year and month, assume it is the last day of the month
					if year and month and not day: day = 28 if month == 2 else 30
				elif Tools.isString(date) and '-' in date:
					return date

			# Sometimes the release date is wrong.
			# Eg: The Office (UK) tt0290978: Release date 2023-01-23 | Release year: 2001-2003.
			date = data.get('releaseYear')
			if date:
				if Tools.isDictionary(date):
					year2 = date.get('year')
					if not year or (year2 and year2 < year): year = year2
				else:
					if not year: year = date

			if year and month and day: return '%d-%02d-%02d' % (year, month, day)
		except: Logger.error()
		return None

	def _extractStatus(self, data):
		try:
			if data:
				return self._convertStatus(status = data.lower(), inverse = True, default = True)
		except: Logger.error()
		return None

	def _extractGenre(self, data):
		try:
			if data:
				if Tools.isString(data): data = [data]

				genre = []
				for i in data:
					if Tools.isDictionary(i): i = i.get('genre', {}).get('text') # New list data.
					if i:
						# Filter out REQUEST parameters that are negated.
						# Otherwise negated genres get copied over to the results, and end up in the detailed metadata.
						# Important for Arrivals menu, which negates a bunch of genres.
						if not i.startswith(MetaImdb.Negate) and not i.startswith(MetaImdb.Primary) and not i.startswith('-'): genre.append(i.lower())

				return self._convertGenre(genre = genre, inverse = True, default = True)
		except: Logger.error()
		return None

	def _extractStudio(self, data):
		try:
			if data:
				result = []
				for item in data:
					try: result.append(item['node']['company']['companyText']['text'])
					except: Logger.error()
				if result: return result
		except: Logger.error()
		return None

	def _extractCountry(self, data):
		try:
			if data: return Country.codes([i.lower() for i in data] if Tools.isArray(data) else data.lower())
		except: Logger.error()
		return None

	def _extractLanguage(self, data):
		try:
			if data: return Language.codes([i.lower() for i in data] if Tools.isArray(data) else data.lower())
		except: Logger.error()
		return None

	def _extractCertificate(self, data, media = None):
		try:
			if data:
				if data.lower() == 'x': return Audience.CertificateTvma if Media.isSerie(media) else Audience.CertificateNc17 # IMDb has an old "X" rating for old movies which was replaced by NC-17.
				elif Regex.match(data = data, expression = '(?:ur|(?:un|not)?.*?rated)', cache = True): return Audience.CertificateNr
				elif len(data) > 5 and not '-' in data: return None # Sometimes IMDb returns "approved" or "passed".
				else: return self._convertCertificate(certificate = data, inverse = True, default = True)
		except: Logger.error()
		return None

	def _extractHomepage(self, data):
		try:
			if data:
				result = []
				for item in data:
					rank = 2
					type = item['node']['label'].lower()
					if 'official site' in type: rank = 0
					elif 'official' in type: rank = 1
					result.append((rank, item['node']['url']))
				if result: return sorted(result, key = lambda i : i[0])[0][1]
		except: Logger.error()
		return None

	def _extractCredit(self, data, type):
		try:
			if Tools.isArray(data):
				result = []
				order = 0
				for i in data:
					if i.get('category', {}).get('id') == type:
						credits = i.get('credits')
						if credits:
							for j in credits:
								cast = {}
								try: cast['name'] = j['name']['nameText']['text']
								except: pass
								try: cast['thumbnail'] = self.linkImage(link = j['name']['primaryImage']['url'])
								except: pass
								try: cast['role'] = ' / '.join([k['name'] for k in j['characters']])
								except: pass
								if cast:
									cast['order'] = order
									result.append(cast)
									order += 1
				if result:
					if not type == 'cast': result= Tools.listUnique([i['name'] for i in result])
					return result
		except: Logger.error()
		return None

	def _extractCast(self, data):
		try:
			if data:
				result = []
				order = 0
				for item in data:
					cast = {}
					try: cast['name'] = item['node']['name']['nameText']['text']
					except: Logger.error()
					try: cast['thumbnail'] = self.linkImage(link = item['node']['name']['primaryImage']['url'])
					except: pass
					try: cast['role'] = ' / '.join([i['name'] for i in item['node']['characters']])
					except: pass
					if cast:
						cast['order'] = order
						result.append(cast)
						order += 1
				if result: return result
		except: Logger.error()
		return None

	def _extractCrew(self, data):
		try:
			if data:
				result = []
				for item in data:
					try:
						if item['credits']: result.append(item['credits'][0]['name']['nameText']['text'])
					except: Logger.error()
				if result: return result
		except: Logger.error()
		return None

	def _extractAward(self, data):
		try:
			if data:
				award = {}
				try: award['id'] = Tools.replaceNotAlphaNumeric(data['award']['text'].lower())
				except: Logger.error()
				try: award['name'] = data['award']['text']
				except: Logger.error()
				try: award['wins'] = data['wins']
				except: pass
				try: award['nominations'] = data['nominations']
				except: pass
				if award: return [award]
		except: Logger.error()
		return None

	def _extractCount(self, data):
		try:
			if data:
				episode = None
				season = None
				unknown = None

				try: episode = data['episodes']['total']
				except: Logger.error()

				try: unknown = data['unknownSeasonEpisodes']['total']
				except: Logger.error()

				try:
					seasons = [i['number'] for i in data['seasons']]
					if seasons: season = max(seasons)
				except: Logger.error()

				count = {}
				if not episode is None:
					if not 'episode' in count: count['episode'] = {}
					count['episode']['total'] = episode
				if not unknown is None:
					if not 'episode' in count: count['episode'] = {}
					count['episode']['unknown'] = unknown
				if not season is None:
					if not 'season' in count: count['season'] = {}
					count['season']['total'] = season
				if count: return count
		except: Logger.error()
		return None

	def _extractMetacritic(self, data):
		try:
			if data: return data / 10.0
		except: Logger.error()
		return None

	def _extractProfession(self, data):
		try:
			if data:
				results = []

				if Tools.isList(data): # New person list structure.
					for i in data:
						result = i.get('category', {}).get('text')
						if result: results.append(result)

				if results: return results
		except: Logger.error()
		return None

	def _extractFilmography(self, data):
		try:
			if data:
				results = []

				if Tools.isList(data): # New person list structure.
					for i in data:
						i = i.get('node', {})
						id = i.get('title', {}).get('id')
						if id:
							result = {}
							result['id'] = {'imdb' : id}
							result['imdb'] = id

							title = i.get('title', {}).get('titleText', {}).get('text')
							if title: result['title'] = title

							title = i.get('title', {}).get('originalTitleText', {}).get('text')
							if title: result['originaltitle'] = title

							year = i.get('summary', {}).get('yearRange')
							if year:
								if Tools.isDictionary(year): year = year.get('year')
								elif Tools.isArray(year): year = year[0]
								if year and Tools.isInteger(year): result['year'] = year

							if result: results.append(result)
				else:
					id = data.get('titleId')
					if id:
						result = {}
						result['id'] = {'imdb' : id}
						result['imdb'] = id

						title = data.get('titleText')
						if title: result['title'] = title

						title = data.get('originalTitleText')
						if title: result['originaltitle'] = title

						year = data.get('yearRange')
						if year:
							if Tools.isDictionary(year): year = year.get('year')
							elif Tools.isArray(year): year = year[0]
							if year and Tools.isInteger(year): result['year'] = year

						if result: results.append(result)

				if results: return results
		except: Logger.error()
		return None

	def _extractDescription(self, description):
		# Some IMDb titles do not have a plot, and instead something like:
		#	Add a plot
		#	Add a plot in your language
		if description:
			if Regex.match(data = description, expression = 'add\s+a\s+(?:plot|bio|description)', cache = True):
				description = None
			else:
				# Eg: The definitive documentary, ...  See full summary</a> »
				# Use "?:<a[^<]*?)" instead of "?:<a.*?)", since it is a lot faster for people's bio.
				description = Regex.remove(data = description, expression = '(\s*(?:<a[^<]*?)?\s*see\s*full\s*summary\s*(?:<\/a>)?\s*).{0,3}$', cache = True)

				# Remove BBcode tags.
				if '[' in description:
					decoded = Regex.remove(data = description, expression = '(\[.*?])', group = 1, all = True, cache = True)
					if decoded: description = decoded

				# Remove HTML tags.
				# Some decriptions, like a person's bio, can sometimes have large chunks of HTML.
				if '<' in description:
					decoded = self.parser(data = description).text
					if decoded: description = decoded

				# Some contain HTML entities that are not decoded: "&#39;"
				# Eg: Downton Abbey S06E09 (plot: ... while Edith&#39;s secret ...).
				description = Networker.htmlDecode(description)

				# Some have internal newlines: "... an\nexcellent ..."
				# Some might still have HTML breaks, if the parser above was not executed.
				description = description.replace('<br/>', ' ').replace('<br>', ' ').replace('\n', ' ')

				# Might look like a space, but is a different UTF character (U+00A0 or U+200B).
				description = description.replace(' ', ' ').replace('​', ' ')

				description = description.replace('--', ' - ').replace('  ', ' ').replace('  ', ' ').strip()
		return description

	def _extractItems(self, data, link, media = None, niche = None, genre = None, language = None, country = None, certificate = None):
		try:
			if data:
				filterRating = link and MetaImdb.PathListRating in link
				filterUser = link and MetaImdb.PathUser in link # Is a list is from the current user, and not a list from some other random user.

				filterMovie = Media.isMovie(media)
				filterShow = Media.isSerie(media)
				filterDocu = Media.isDocu(niche) or (genre and MetaTools.GenreDocumentary in genre)
				filterShort = Media.isShort(niche) or (genre and MetaTools.GenreShort in genre)
				filterSpecial = Media.isSpecial(niche)

				if language is True or language is False: language = None
				if country is True or country is False: country = None

				if genre:
					genre = self._extractGenre(genre)
					if genre and not Tools.isArray(genre): genre = [genre]
				if language and not Tools.isArray(language): language = [language]
				if country and not Tools.isArray(country): country = [country]

				if MetaImdb.PathCsv in link:
					function = self._extractCsv
				else:
					new = 'ipc-metadata-list' in data
					if MetaImdb.PathSearchPerson in link: function = self._extractPersonNew if new else self._extractPersonOld
					elif '/user/' in link and '/lists' in link: function = self._extractLists
					elif '"nameListItemSearch"' in data: function = self._extractListPersonNew if new else self._extractListPersonOld
					elif '"titleListItemSearch"' in data or '"advancedTitleSearch"' in data: function = self._extractListNew if new else self._extractListOld
					else: function = self._extractTitleNew if new else self._extractTitleOld # Can be title/person advanced search, or old title/person lists.
				items = function(data = data, media = media, niche = niche, filterMovie = filterMovie, filterDocu = filterDocu, filterShort = filterShort, filterSpecial = filterSpecial, filterShow = filterShow, filterRating = filterRating, filterUser = filterUser)

				if items:
					# Some lists can contain duplicates.
					items = self.mMetatools.filterDuplicate(items = items)

					# Extract media, in case different medias are returned (eg: global search returning movies and shows together).
					for item in items:
						self._dataSet(item = item, key = 'media', value = self.mMetatools.media(metadata = item, media = media))

						self._dataSet(item = item, key = 'niche', value = self.mMetatools.niche(metadata = item, media = media, niche = niche))

						# IMDb often only returns partial metadata.
						# For instance, during discovery (advanced search) the returned JSON only contains up to 3 genres, although there might be more.
						# The title page retrieved by metadata() has more metadata than the lists, but for certain attributes it might still require thew retrieval of a subpage to get the full details.
						# If we for instance discover the History genre, IMDb retruns a bunch of titles where the genre is listed as 4th or 5th genre.
						# Hence, the History genre is not added to the metadata and some titles might later be filtered out locally.
						# Add the search parameter to the metadata to avoid this.

						if genre: self._dataSet(item = item, key = 'genre', value = genre)
						if language: self._dataSet(item = item, key = 'language', value = language)
						if country: self._dataSet(item = item, key = 'country', value = country)
						if certificate:
							value = self._data(item = item, key = 'mpaa')
							if not value or value == Audience.CertificateNr: self._dataSet(item = item, key = 'certificate', value = certificate)
				return items
		except: Logger.error()
		return None

	def _extractTitleNew(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		try:
			items = self._extractJson(data = data, full = True)
			if items:
				items = items['searchResults']['titleResults']['titleListItems']
				if items:
					results = []
					for item in items:
						try:
							result = {}
							resultImdb = {}
							resultMetacritic = {}

							filterType = None
							type = self._extract(data = item, keys = ['titleType', 'id'])
							if filterShort and not Media.isSerie(media): filterType = MetaImdb.TypesShort
							elif filterSpecial: filterType = MetaImdb.TypesSpecial
							elif filterMovie: filterType = MetaImdb.TypesFilm
							elif filterShow: filterType = MetaImdb.TypesSerie
							if filterType and not type in filterType: continue

							self._extract(result = result, data = item, attribute = 'media', keys = ['titleType', 'id'], function = self._extractMedia)
							self._extract(result = result, data = item, attribute = 'niche', keys = ['titleType', 'id'], function = lambda x : self._extractNiche(x, item = item))

							if Media.isEpisode(result.get('media')):
								self._extract(result = result, data = item, attribute = ['imdb'], keys = ['series', 'id'])
								self._extract(result = result, data = item, attribute = ['id', 'episode', 'imdb'], keys = ['titleId'])
								self._extract(result = result, data = item, attribute = 'tvshowtitle', keys = ['series', 'titleText'])
							else:
								self._extract(result = result, data = item, attribute = 'imdb', keys = ['titleId'])

							if 'imdb' in result:
								if 'id' in result: result['id']['imdb'] = result['imdb']
								else: result['id'] = {'imdb' : result['imdb']}
							else: continue

							self._extract(result = result, data = item, attribute = 'title', keys = ['titleText'], function = self._extractTitle)
							self._extract(result = result, data = item, attribute = 'originaltitle', keys = ['originalTitleText'], function = self._extractTitle)
							self._extract(result = result, data = item, attribute = 'plot', keys = ['plot'], function = self._extractDescription)
							self._extract(result = result, data = item, attribute = 'year', keys = ['releaseYear'])
							self._extract(result = result, data = item, attribute = 'premiered', function = self._extractPremiered)
							self._extract(result = result, data = item, attribute = 'mpaa', keys = ['certificate'], function = lambda x : self._extractCertificate(x, media = media))
							self._extract(result = result, data = item, attribute = 'duration', keys = ['runtime'])
							self._extract(result = result, data = item, attribute = 'genre', keys = ['genres'], function = self._extractGenre)

							self._extract(result = result, data = item, attribute = 'cast', keys = ['topCast'], function = self._extractCast)
							self._extract(result = result, data = item, attribute = 'director', keys = ['directors'], function = self._extractCrew)
							self._extract(result = result, data = item, attribute = 'writer', keys = ['writers'], function = self._extractCrew)

							self._extract(result = resultImdb, data = item, attribute = ['image', 'poster'], keys = ['primaryImage', 'url'], function = self.linkImage)
							self._extract(result = resultImdb, data = item, attribute = ['voting', 'rating'], keys = ['ratingSummary', 'aggregateRating'], function = self._extractRating)
							self._extract(result = resultImdb, data = item, attribute = ['voting', 'votes'], keys = ['ratingSummary', 'voteCount'], function = self._extractVotes)
							self._extract(result = resultMetacritic, data = item, attribute = ['voting', 'rating'], keys = ['metascore'], function = self._extractMetacritic, log = False)

							result['rating'] = self._data(resultImdb, ['voting', 'rating'])
							result['votes'] = self._data(resultImdb, ['voting', 'votes'])

							premiered = result.get('premiered')
							if premiered:
								if not result.get('time'): result['time'] = {}
								result['time'][MetaTools.TimePremiere] = ConverterTime(premiered, format = ConverterTime.FormatDate, utc = True).timestamp()

							result['temp'] = {'imdb' : {}} # Always add the IMDb temp, since we check if the this item is from an IMDb list in metadataImdb().
							if resultImdb: result['temp']['imdb'] = resultImdb
							if resultMetacritic: result['temp']['metacritic'] = resultMetacritic

							# Some movie lists contain shows, and some show lists contain movies.
							title = result.get('title')
							if title:
								if filterMovie and title.startswith('Episode:'): continue
								elif filterShow and title.startswith('Movie:'): continue

							# Rating list cannot be filtered according to type using GET parameters.
							if filterRating:
								genre = result.get('genre')
								if genre:
									if filterDocu and not MetaTools.GenreDocumentary in genre: continue
									if filterShort and not MetaTools.GenreShort in genre: continue

							# Some shows are indistinguishable from movies, since they do not contain any info on being a show.
							# Ignore items that have a runtime of more than 5 hours.
							# Shows that have ended, use the total duration of all episodes. Shows that are still running, use the duration of a single episode.
							duration = result.get('duration')
							if filterRating and duration:
									if filterMovie and duration > 20000: continue
									elif filterShow and duration < 18000 and not bool(item.get('endYear')): continue

							if filterShow and duration and duration > 18000: del result['duration'] # The total duration of all episodes in the show.

							if result: results.append(result)
						except: Logger.error()
					return results
		except: Logger.error()
		return None

	def _extractTitleOld(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		try:
			parser = self.parser(data = data)
			items = parser.find_all('div', {'class' : ['lister-item', 'list_item']})
			if items:
				try: filterPerson = Regex.match(data = items[0].find('a')['href'], expression = self._idExpressionPerson(), cache = True)
				except: filterPerson = False
				results = []
				for item in items:
					try:
						result = {}
						resultList = {}
						resultImdb = {}
						resultMetacritic = {}
						itemData = str(item)

						if filterPerson:
							id = item.find('a')['href']
							id = Regex.extract(data = id, expression = self._idExpressionPerson(), group = 1, cache = True)
							if id:
								result['id'] = id
							else: continue

							try:
								name = item.find_all('a')[1].text.strip()
								if name: result['name'] = name
							except: pass

							try:
								description = item.find('p', {'class' : ''}).text
								if description: result['description'] = self._extractDescription(description = description)
							except: pass

							try:
								description = item.find('div', {'class' : 'list-description'}).text
								if description: resultList['description'] = self._extractDescription(description = description)
							except: pass

							try:
								profession = item.find('p', {'class' : 'text-muted'}).text
								profession = Regex.extract(data = profession, expression = '(.+?)(?:\||<\/?div|<\/?span)', group = 1, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines, cache = True)
								profession = [i.strip() for i in profession.split(',')]
								if profession: result['profession'] = profession
							except: pass

							try:
								filmography = []
								for i in item.find_all('a'):
									id = Regex.extract(data = i['href'], expression = self._idExpressionTitle(), group = 1, cache = True)
									if id:
										filmography.append({
											'id' : {'imdb' : id},
											'imdb' : id,
											'title' : i.text.strip(),
										})
								if filmography: result['filmography'] = filmography
							except: pass

							try:
								image = item.find('div', {'class' : 'lister-item-image'}).find('img')['src']
								if image and not '/nopicture/' in image: result['image'] = self.linkImage(image)
							except: pass
						else:
							if filterShow: id = item.find('div', {'class' : 'lister-item-content'}).find('a')['href']
							else: id = item.find('a')['href']
							id = Regex.extract(data = id, expression = self._idExpressionTitle(), group = 1, cache = True)
							if id:
								result['id'] = {'imdb' : id}
								result['imdb'] = id
							else: continue

							try:
								title = item.find_all('a')[1].text.strip()
								if title:
									if filterMovie and Regex.match(data = title, expression = '^\s*episode:', cache = True): continue # Some movie lists contain shows.
									elif filterShow and Regex.match(data = title, expression = '^\s*movie:', cache = True): continue # Some show lists contain movies.

									title = self._extractTitle(title)
									result['title'] = title
									result['originaltitle'] = title
							except: pass

							years = False
							try:
								# Years that contain extra parts, like "Video Game" or "2019-" or "2011-2018".
								year = item.find('span', {'class' : ['lister-item-year', 'year_type']}).text

								if Regex.match(data = year, expression = 'game', cache = True): # (2018 Video Game)
									continue
								elif filterMovie and not Regex.match(data = year, expression = '\(\d{4}[a-z\d\s]*\)', cache = True): # For movies, allow (2014 TV Movie), but disallow (2016 - 2018)
									continue
								elif Regex.match(data = year, expression = '\(\d{4}.*\d{4}\)', cache = True):
									years = True
									if filterMovie: continue

								year = int(Regex.extract(data = year, expression = '(\d{4})', group = 1, cache = True))
								if year: result['year'] = year
							except: pass

							plot = None
							try:
								plot = item.find_all('p', {'class' : 'text-muted'})[-1].text
								if Regex.match(data = plot, expression = 'votes:', cache = True): plot = item.find_all('p', {'class' : ''})[-1].text # User rating lists has the votes in "text-muted".
							except: pass
							if not plot:
								try: plot = item.find('div', {'class' : 'item_description'}).text
								except: pass
							if plot: result['plot'] = self._extractDescription(description = plot)

							try:
								poster = item.find('img')['loadlate']
								if poster and not '/nopicture/' in poster: resultImdb['image'] = {'poster' : self.linkImage(poster)}
							except: pass

							genres = []
							try:
								genre = item.find('span', {'class' : 'genre'}).text
								genre = [i.strip() for i in genre.split(',')]
								genre = self._extractGenre(genre)
								if genre: result['genre'] = genres = genre
							except: pass

							if filterRating: # Rating list cannot be filtered according to type using GET parameters.
								if filterDocu and not MetaTools.GenreDocumentary in genres: continue
								if filterShort and not MetaTools.GenreShort in genres: continue

							# Some featured lists return documentaries as well (eg home releases).
							# Only exclude if it is ONLY documentary. Allow multiple genres (eg: Jackass Forever 2022 - Documentary, Action, Comedy).
							if filterMovie and not filterDocu and genres and len(genres) == 1 and MetaTools.GenreDocumentary in genres: continue

							try:
								mpaa = item.find('span', {'class' : 'certificate'}).text
								if mpaa:
									mpaa = self._extractCertificate(mpaa, media = media)
									if mpaa: result['mpaa'] = mpaa
							except: pass

							try:
								duration = item.find('span', {'class' : 'runtime'}).text
								if not duration: duration = Regex.extract(data = itemData, expression = '((\d+\shr?\s)?\d+\sm(?:in)?)', group = 1, cache = True)
								duration = ConverterDuration(value = duration.replace(',', '')).value(ConverterDuration.UnitSecond) # Eg: 5,702 min
								if duration and (not filterShow or duration < 18000): result['duration'] = duration # The total duration of all episodes in the show.
							except: pass

							# Some shows are indistinguishable from movies, since they do not contain any info on being a show.
							# Ignore items that have a runtime of more than 5 hours.
							if filterRating and duration:
								if filterMovie and duration > 20000: continue
								elif filterShow and duration < 18000 and not years: continue # Do not make this too small. Titanic is 3 hr 14 min (11640 secs).

							rating = None
							try: rating = item.find(True, {'class' : ['ratings-imdb-rating', 'ipl-rating-star__rating']}).text # First ID is a div, second ID is a span.
							except: pass
							if not rating:
								try: rating = item.find('span', {'class' : 'rating-rating'}).find('span', {'class' : 'value'}).text
								except: pass
							if rating:
								rating = rating.strip()
								if rating and not rating == '' and not rating == '-':
									if not 'voting' in resultImdb: resultImdb['voting'] = {}
									try: resultImdb['voting']['rating'] = float(rating)
									except: pass

							# Do not do this for other lists, since the alternative rating might be from a different user (creator of the list) and will incorrectly overwrite the current user's rating.
							# Also ingore individual episodes, since the season and episode numbers are unknown.
							ratingUser = None
							if filterUser and (not filterShow or not filterRating or not Regex.match(data = title, expression = '^\s*episode:', cache = True)):
								try: ratingUser = item.find('span', {'class' : 'userRatingValue'}).text
								except: pass
								if not ratingUser:
									try: ratingUser = item.find('div', {'class' : 'ipl-rating-star--other-user'}).find('span', {'class' : 'ipl-rating-star__rating'}).text
									except: pass
								if ratingUser:
									ratingUser = ratingUser.strip()
									if ratingUser and not ratingUser == '' and not ratingUser == '-':
										if not 'voting' in resultImdb: resultImdb['voting'] = {}
										try: resultImdb['voting']['user'] = float(ratingUser)
										except: pass

							try:
								ratingTime = ConverterTime(Regex.extract(data = itemData, expression = 'rated\s*on\s*(.*?)<', group = 1, cache = True, utc = True), format = ConverterTime.FormatDateShort).timestamp()
								if ratingTime:
									if not 'voting' in resultImdb: resultImdb['voting'] = {}
									resultImdb['voting']['time'] = ratingTime
							except: pass

							try:
								ratingMetacritic = item.find('span', {'class' : 'metascore'}).text
								if ratingMetacritic:
									ratingMetacritic = ratingMetacritic.strip()
									if ratingMetacritic and not ratingMetacritic == '' and not ratingMetacritic == '-':
										try: resultMetacritic['voting'] = {'rating' : float(ratingMetacritic) / 10.0} # Out of 100 and not out of 10.
										except: pass
							except: pass

							votes = None
							try: votes = item.find('span', {'name' : 'nv'}).text
							except: pass
							if not votes:
								try: votes = Regex.extract(data = item.find('div', {'class' : 'rating-list'})['title'], expression = '\((.+?)\svotes?\)', cache = True)
								except: pass
							if votes:
								votes = votes.strip()
								if votes and not votes == '' and not votes == '-':
									if not 'voting' in resultImdb: resultImdb['voting'] = {}
									try: resultImdb['voting']['votes'] = int(votes.replace(',', ''))
									except: pass

							try:
								director = Regex.extract(data = itemData, expression = 'directors?:(.+?)(?:\||<\/?div|<\/?span)', group = 1, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines, cache = True)
								director = self.parser(data = director).find_all('a')
								director = [i.text for i in director]
								if director: result['director'] = director
							except: pass

							try:
								cast = Regex.extract(data = itemData, expression = 'stars?:(.+?)(?:\||<\/?div|<\/?span)', group = 1, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines, cache = True)
								cast = self.parser(data = cast).find_all('a')
								cast = [i.text for i in cast]
								if cast: result['cast'] = cast
							except: pass

						try:
							position = int(item.find('span', {'class' : 'lister-item-index'}).text.replace('.', '').strip())
							if position: resultList['position'] = position
						except: pass

						result['temp'] = {'imdb' : {}} # Always add the IMDb temp, since we check if the this item is from an IMDb list in metadataImdb().
						if resultImdb: result['temp']['imdb'] = resultImdb
						if resultList: result['temp']['imdb']['list'] = resultList
						if resultMetacritic: result['temp']['metacritic'] = resultMetacritic

						if result: results.append(result)
					except: Logger.error()

				return results
		except: Logger.error()
		return None

	def _extractLists(self, data, **parameters):
		try:
			items = self._extractJson(data = data, full = True)
			if items:
				# Check custom lists vs user lists (rating list or watchlist).
				items = items.get('mainColumnData') or {}
				items = items.get('userListSearch') or {}
				items = items.get('edges')
				if items:
					results = []
					for item in items:
						try:
							if 'node' in item: item = item.get('node')

							result = {'media' : Media.List}
							resultImdb = {'time' : {}, 'count' : {}, 'list' : {'type' : 'personal'}}

							self._extract(result = result, data = item, attribute = 'imdb', keys = ['id'])
							if 'imdb' in result: result['id'] = {'imdb' : result['imdb']}
							else: continue

							self._extract(result = result, data = item, attribute = ['id', 'user'], keys = ['author', 'userId'])
							result['user'] = result.get('id').get('user')

							self._extract(result = result, data = item, attribute = 'title', keys = ['name', 'originalText'], function = self._extractTitle)
							self._extract(result = result, data = item, attribute = 'plot', keys = ['description', 'originalText', 'plainText'], function = self._extractDescription)

							self._extract(result = result, data = item, attribute = ['time', 'added'], keys = ['createdDate'], function = self._extractTime)
							self._extract(result = result, data = item, attribute = ['time', 'updated'], keys = ['lastModifiedDate'], function = self._extractTime)
							time = result.get('time')
							if time:
								resultImdb['time']['added'] = time.get('added')
								resultImdb['time']['updated'] = time.get('updated')

							self._extract(result = resultImdb, data = item, attribute = ['count', 'items'], keys = ['items', 'total'])
							self._extract(result = resultImdb, data = item, attribute = ['list', 'user'], keys = ['author', 'nickName'])
							self._extract(result = resultImdb, data = item, attribute = ['list', 'privacy'], keys = ['visibility', 'id'], function = lambda x : x.lower() if x and Tools.isString(x) else None)

							result['temp'] = {'imdb' : {}}
							if resultImdb: result['temp']['imdb'] = resultImdb

							if result: results.append(result)
						except: Logger.error()
					return results
		except: Logger.error()
		return None

	def _extractListNew(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		try:
			items = self._extractJson(data = data, full = True)
			if items:
				# Check custom lists vs user lists (rating list or watchlist).
				items = items.get('mainColumnData')
				if 'list' in items: items = items.get('list')
				elif 'predefinedList' in items: items = items.get('predefinedList') # User watchlist.
				items = items.get('titleListItemSearch') or items.get('advancedTitleSearch')
				items = items.get('edges')
				if items:
					results = []
					for item in items:
						try:
							if 'listItem' in item:
								item = item.get('listItem')
							elif 'node' in item:
								item = item.get('node')
								if 'title' in item and Tools.isDictionary(item['title']): item = item['title']

							result = {}
							resultImdb = {}
							resultMetacritic = {}

							filterType = None
							type = self._extract(data = item, keys = ['titleType', 'id'])
							if filterShort and not Media.isSerie(media): filterType = MetaImdb.TypesShort
							elif filterSpecial: filterType = MetaImdb.TypesSpecial
							elif filterMovie: filterType = MetaImdb.TypesFilm
							elif filterShow: filterType = MetaImdb.TypesSerie
							if filterType and not type in filterType: continue

							self._extract(result = result, data = item, attribute = 'media', keys = ['titleType', 'id'], function = self._extractMedia)
							self._extract(result = result, data = item, attribute = 'niche', keys = ['titleType', 'id'], function = lambda x : self._extractNiche(x, item = item))

							# Get the show ID, not the episode ID, when episodes are added to lists.
							# This data does not seem to have the season and episode numbers, only the episode ID.
							# Hence, we cannot return episodes from the watchlist (like Trakt), but only the show the episodes belongs to.
							self._extract(result = result, data = item, attribute = 'imdb', keys = ['series', 'series', 'id'])
							if not result.get('imdb'): self._extract(result = result, data = item, attribute = 'imdb', keys = ['id'])
							if 'imdb' in result: result['id'] = {'imdb' : result['imdb']}
							else: continue

							self._extract(result = result, data = item, attribute = 'title', keys = ['titleText', 'text'], function = self._extractTitle)
							self._extract(result = result, data = item, attribute = 'originaltitle', keys = ['originalTitleText', 'text'], function = self._extractTitle)
							self._extract(result = result, data = item, attribute = 'plot', keys = ['plot', 'plotText', 'plainText'], function = self._extractDescription)
							self._extract(result = result, data = item, attribute = 'year', keys = ['releaseYear', 'year'])
							self._extract(result = result, data = item, attribute = 'premiered', function = self._extractPremiered)
							self._extract(result = result, data = item, attribute = 'mpaa', keys = ['certificate', 'rating'], function = lambda x : self._extractCertificate(x, media = media))
							self._extract(result = result, data = item, attribute = 'duration', keys = ['runtime', 'seconds'])
							self._extract(result = result, data = item, attribute = 'genre', keys = ['titleGenres', 'genres'], function = self._extractGenre)

							self._extract(result = result, data = item, attribute = 'cast', keys = ['principalCredits'], function = lambda x : self._extractCredit(x, type = 'cast'))
							self._extract(result = result, data = item, attribute = 'director', keys = ['principalCredits'], function = lambda x : self._extractCredit(x, type = 'director'))
							self._extract(result = result, data = item, attribute = 'writer', keys = ['principalCredits'], function = lambda x : self._extractCredit(x, type = 'writer'))
							self._extract(result = result, data = item, attribute = 'creator', keys = ['principalCredits'], function = lambda x : self._extractCredit(x, type = 'creator'))

							self._extract(result = resultImdb, data = item, attribute = ['image', 'poster'], keys = ['primaryImage', 'url'], function = self.linkImage)
							self._extract(result = resultImdb, data = item, attribute = ['voting', 'rating'], keys = ['ratingsSummary', 'aggregateRating'], function = self._extractRating)
							self._extract(result = resultImdb, data = item, attribute = ['voting', 'votes'], keys = ['ratingsSummary', 'voteCount'], function = self._extractVotes)
							self._extract(result = resultMetacritic, data = item, attribute = ['voting', 'rating'], keys = ['metacritic', 'metascore', 'score'], function = self._extractMetacritic, log = False)

							result['rating'] = self._data(resultImdb, ['voting', 'rating'])
							result['votes'] = self._data(resultImdb, ['voting', 'votes'])

							premiered = result.get('premiered')
							if premiered:
								if not result.get('time'): result['time'] = {}
								result['time'][MetaTools.TimePremiere] = ConverterTime(premiered, format = ConverterTime.FormatDate, utc = True).timestamp()

							result['temp'] = {'imdb' : {}} # Always add the IMDb temp, since we check if the this item is from an IMDb list in metadataImdb().
							if resultImdb: result['temp']['imdb'] = resultImdb
							if resultMetacritic: result['temp']['metacritic'] = resultMetacritic

							# Some movie lists contain shows, and some show lists contain movies.
							title = result.get('title')
							if title:
								if filterMovie and title.startswith('Episode:'): continue
								elif filterShow and title.startswith('Movie:'): continue

							# Rating list cannot be filtered according to type using GET parameters.
							if filterRating:
								genre = result.get('genre')
								if genre:
									if filterDocu and not MetaTools.GenreDocumentary in genre: continue
									if filterShort and not MetaTools.GenreShort in genre: continue

							# Some shows are indistinguishable from movies, since they do not contain any info on being a show.
							# Ignore items that have a runtime of more than 5 hours.
							# Shows that have ended, use the total duration of all episodes. Shows that are still running, use the duration of a single episode.
							duration = result.get('duration')
							if filterRating and duration:
									if filterMovie and duration > 20000: continue
									elif filterShow and duration < 18000 and not bool(item.get('releaseYear', {}).get('endYear')): continue

							if filterShow and duration and duration > 18000: del result['duration'] # The total duration of all episodes in the show.

							if result: results.append(result)
						except: Logger.error()
					return results
		except: Logger.error()
		return None

	def _extractListOld(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		return self._extractTitleOld(data = data, media = media, niche = niche, filterMovie = filterMovie, filterDocu = filterDocu, filterShort = filterShort, filterSpecial = filterSpecial, filterShow = filterShow, filterRating = filterRating, filterUser = filterUser)

	def _extractListPersonNew(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		try:
			items = self._extractJson(data = data, full = True)
			if items:
				items = items['mainColumnData']['list']['nameListItemSearch']['edges']
				if items:
					results = []
					for item in items:
						try:
							if 'listItem' in item:
								item = item.get('listItem')
							elif 'node' in item:
								item = item.get('node')
								if 'title' in item and Tools.isDictionary(item['title']): item = item['title']

							result = {}

							self._extract(result = result, data = item, attribute = 'imdb', keys = ['id'])
							if 'imdb' in result: result['id'] = {'imdb' : result['imdb']}
							else: continue

							self._extract(result = result, data = item, attribute = 'name', keys = ['nameText', 'text'])
							self._extract(result = result, data = item, attribute = 'description', keys = ['bio', 'displayableArticle', 'body', 'plaidHtml'], function = self._extractDescription)
							self._extract(result = result, data = item, attribute = 'profession', keys = ['primaryProfessions'], function = self._extractProfession)
							self._extract(result = result, data = item, attribute = 'filmography', keys = ['knownFor', 'edges'], function = self._extractFilmography)
							self._extract(result = result, data = item, attribute = 'image', keys = ['primaryImage', 'url'], function = self.linkImage)

							if result: results.append(result)
						except: Logger.error()
					return results
		except: Logger.error()
		return None

	def _extractListPersonOld(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		return self._extractTitleOld(data = data, media = media, niche = niche, filterMovie = filterMovie, filterDocu = filterDocu, filterShort = filterShort, filterSpecial = filterSpecial, filterShow = filterShow, filterRating = filterRating, filterUser = filterUser)

	def _extractPersonNew(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		try:
			items = self._extractJson(data = data, full = True)
			if items:
				items = items['searchResults']['nameResults']['nameListItems']
				if items:
					results = []
					for item in items:
						try:
							result = {}

							self._extract(result = result, data = item, attribute = 'imdb', keys = ['nameId'])
							if 'imdb' in result: result['id'] = {'imdb' : result['imdb']}
							else: continue

							self._extract(result = result, data = item, attribute = 'name', keys = ['nameText'])
							self._extract(result = result, data = item, attribute = 'description', keys = ['bio'], function = self._extractDescription)
							self._extract(result = result, data = item, attribute = 'profession', keys = ['primaryProfessions'])
							self._extract(result = result, data = item, attribute = 'filmography', keys = ['knownFor'], function = self._extractFilmography)
							self._extract(result = result, data = item, attribute = 'image', keys = ['primaryImage', 'url'], function = self.linkImage)

							if result: results.append(result)
						except: Logger.error()
					return results
		except: Logger.error()
		return None

	def _extractPersonOld(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		try:
			parser = self.parser(data = data)
			items = parser.find_all('div', {'class' : ['lister-item', 'list_item']})
			if items:
				results = []
				for item in items:
					try:
						result = {}

						tag1 = item.find_all('a')[1]
						tag2 = item.find('p', {'class' : 'text-muted'})

						id = tag1['href']
						id = Regex.extract(data = id, expression = self._idExpressionPerson(), group = 1, cache = True)
						if id:
							result['imdb'] = id
							result['id'] = {'imdb' : id}
						else: continue

						name = tag1.text.strip()
						if name: result['name'] = name

						try:
							description = self._extractDescription(item.find_all('p')[1].text)
							if description: result['description'] = description
						except: pass

						try:
							profession = Regex.extract(data = str(tag2), expression = '>(.+?)(?:\||<\/?div|<\/?span)', group = 1, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines, cache = True)
							if profession: result['profession'] = [i.strip() for i in profession.split(',')]
						except: pass

						try:
							films = Regex.extract(data = str(tag2), expression = '(?:<\/div>|<\/span>)\s*(.+?)\s*<\/p', group = 1, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines, cache = True)
							if films:
								films = self.parser(data = films).find_all('a')
								if films:
									filmography = []
									for i in films:
										try:
											filmId = Regex.extract(data = i['href'], expression = self._idExpressionTitle(), group = 1, cache = True)
											if filmId:
												film = {
													'id' : {'imdb' : filmId},
													'imdb' : filmId,
												}
												filmTitle = i.text.strip()
												if filmTitle: film['title'] = filmTitle
												filmography.append(film)
										except: pass
									if filmography: result['filmography'] = filmography
						except: pass

						try:
							image = item.find('img')['src']
							if image: result['image'] = self.linkImage(image, crop = True) # Crop to keep the aspect ratio.
						except: pass

						if result: results.append(result)
					except: Logger.error()
				return results
		except: Logger.error()
		return None

	def _extractCsv(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		try:
			result = []
			items = Csv.decode(data = data, header = True, structured = True, convertList = False) # Do not convert lists, since the Title column might be split into a list if it contains a comma.

			if items:
				function = None
				if self.idType(items[0].get('Const')) == MetaImdb.IdPerson or items[0].get('Name'):
					# https://imdb.com/list/ls000005319/export
					function = self._extractCsvPerson
				else:
					# User watchlist, rating list, custom lists, or other lists.
					# https://imdb.com/list/ls521170945/export
					# https://imdb.com/list/ls029528149/export
					# https://imdb.com/list/ls566661486/export
					# https://imdb.com/list/ls093350982/export  (NB: Test this one, since it has plots with quotes).
					function = self._extractCsvTitle

				for item in items:
					item = function(data = item, media = media, niche = niche, filterMovie = filterMovie, filterDocu = filterDocu, filterShort = filterShort, filterShow = filterShow, filterRating = filterRating, filterUser = filterUser)
					if item: result.append(item)

			return result
		except: Logger.error()
		return None

	def _extractCsvTitle(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		try:
			basic = False
			id = data.get('Const')
			more = data.get('Description')

			# For some lists this is the IMDb ID for the item.
			# Other lists have some "rm" ID and the actual IMDb ID should be extracted from the description.
			# https://imdb.com/list/ls566661486
			if not id or not self.idType(id) in [MetaImdb.IdTitle, MetaImdb.IdPerson] and more:
				basic = True
				id = Regex.extract(data = more, expression = '\[link.*?\/' + self._idExpressionTitle(), cache = True)

			if id and self.idType(id) in [MetaImdb.IdTitle, MetaImdb.IdPerson]:
				type = data.get('Title Type')
				if type:
					if filterDocu and not type in MetaImdb.TypesFilm and not type.lower() == MetaTools.GenreDocumentary: return None # 'documentary' is not one of the listed types in the JSON, only a genre.
					elif filterShort and not Media.isSerie(media) and not type in MetaImdb.TypesShort: return None
					elif filterSpecial and not type in MetaImdb.TypesSpecial: return None
					elif filterMovie and not type in MetaImdb.TypesFilm: return None
					elif filterShow and not type in MetaImdb.TypesSerie: return None

				result = {}
				resultList = {}
				resultImdb = {}

				if type in MetaImdb.TypesEpisode:
					result['media'] = Media.Episode
				elif type in MetaImdb.TypesMini:
					result['media'] = Media.Show
					result['niche'] = [Media.Mini]
				elif type in MetaImdb.TypesSerie:
					result['media'] = Media.Show
				elif type in MetaImdb.TypesSpecial:
					result['media'] = Media.Movie
					result['niche'] = [Media.Special]
				elif type in MetaImdb.TypesShort:
					result['media'] = Media.Movie
					result['niche'] = [Media.Short]
					if type == MetaImdb.TypeShortTv: result['niche'].append(Media.Television)
				elif type in MetaImdb.TypesFilm:
					result['media'] = Media.Movie
					if type == MetaImdb.TypeMovieTv: result['niche'] = [Media.Television]

				result['id'] = {'imdb' : id}
				result['imdb'] = id

				try:
					position = int(data['Position'])
					if position: resultList['position'] = position
				except: pass

				try:
					added = ConverterTime(data['Created'], format = ConverterTime.FormatDate, utc = True).timestamp()
					if added: resultList['added'] = added
				except: pass

				try:
					updated = ConverterTime(data['Modified'], format = ConverterTime.FormatDate, utc = True).timestamp()
					if updated: resultList['updated'] = updated
				except: pass

				try:
					title = data.get('Title')
					if title: result['title'] = result['originaltitle'] = self._extractTitle(title)
				except: pass

				try:
					description = self._extractDescription(data)
					if description: resultList['description'] = description
				except: pass

				try:
					year = int(data.get('Year'))
					if year: result['year'] = year
				except: pass

				try:
					premiered = data.get('Release Date')
					if premiered: result['premiered'] = premiered
				except: pass

				try:
					duration = int(data.get('Runtime (mins)')) * 60
					if duration: result['duration'] = duration
				except: pass

				try:
					genre = data.get('Genres')
					if genre:
						genre = self._extractGenre(self._extractList(genre))
						if genre: result['genre'] = genre
				except: pass

				try:
					director = data.get('Directors')
					if director:
						director = self._extractList(director)
						if director: result['director'] = director
				except: pass

				try:
					rating = float(data.get('IMDb Rating'))
					if rating:
						if not 'voting' in resultImdb: resultImdb['voting'] = {}
						resultImdb['rating'] = rating
				except: pass

				try:
					votes = int(data.get('Num Votes'))
					if votes:
						if not 'voting' in resultImdb: resultImdb['voting'] = {}
						resultImdb['voting']['votes'] = votes
				except: pass

				try:
					ratingUser = float(data.get('Your Rating'))
					if ratingUser:
						if not 'voting' in resultImdb: resultImdb['voting'] = {}
						resultImdb['voting']['user'] = ratingUser
				except: pass

				try:
					ratingTime = ConverterTime(data.get('Date Rated'), format = ConverterTime.FormatDate, utc = True).timestamp()
					if ratingTime:
						if not 'voting' in resultImdb: resultImdb['voting'] = {}
						resultImdb['voting']['time'] = ratingTime
				except: pass

				# Basic lists without all the attributes.
				# https://imdb.com/list/ls566661486
				if basic:
					if not 'title' in result:
						title = Regex.extract(data = more, expression = '\[link.*?\](.*?)\[\/', cache = True)
						if title: result['title'] = result['originaltitle'] = title

					if not 'year' in result or not 'premiered' in result:
						date = Regex.extract(data = more, expression = '.*?\s([a-z]{3,}\.?\s\d{1,2}(?:,?\s\d{4})?)(?!\[\/link)', cache = True)
						if date:
							month = Regex.extract(data = date, expression = '([a-z]{3}[a-z]*\.?)', cache = True)
							date = date.replace(month, month[:3])
							if date:
								if not 'year' in result:
									year = Regex.extract(data = date, expression = '(\d{4})', cache = True)
									if year: result['year'] = int(year)

								if not 'premiered' in result:
									try:
										for format in [ConverterTime.FormatDateAmerican, ConverterTime.FormatDateAmericanShort, ConverterTime.FormatDateAmerican.replace(',', ''), ConverterTime.FormatDateAmericanShort.replace(',', '')]:
											premiered = ConverterTime(date, format = format, utc = True).string(format = ConverterTime.FormatDate)
											if not premiered and '.' in date: premiered = ConverterTime(date.replace('.', ''), format = format, utc = True).string(format = ConverterTime.FormatDate)
											if premiered:
												result['premiered'] = premiered
												break
									except: pass

				if result:
					result['temp'] = {'imdb' : {}} # Always add the IMDb temp, since we check if the this item is from an IMDb list in metadataImdb().
					if resultImdb: result['temp']['imdb'] = resultImdb
					if resultList: result['temp']['imdb']['list'] = resultList
					return result
		except: Logger.error()
		return None

	def _extractCsvPerson(self, data, media = None, niche = None, filterMovie = None, filterDocu = None, filterShort = None, filterSpecial = None, filterShow = None, filterRating = None, filterUser = None):
		try:
			id = data['Const']
			if id and self.idType(id) == MetaImdb.IdPerson:
				result = {}
				resultList = {}
				resultImdb = {}

				result['id'] = {'imdb' : id}
				result['imdb'] = id

				try:
					position = int(data['Position'])
					if position: resultList['position'] = position
				except: pass

				try:
					added = ConverterTime(data['Created'], format = ConverterTime.FormatDate, utc = True).timestamp()
					if added: resultList['added'] = added
				except: pass

				try:
					updated = ConverterTime(data['Modified'], format = ConverterTime.FormatDate, utc = True).timestamp()
					if updated: resultList['updated'] = updated
				except: pass

				try:
					name = data['Name']
					if name: result['name'] = name
				except: pass

				try:
					description = self._extractDescription(data['Description'])
					if description: result['description'] = description
				except: pass

				try:
					filmography = data['Known For']
					if filmography: result['filmography'] = [{'title' : filmography}]
				except: pass

				try:
					birth = data['Birth Date']
					if birth: result['birth'] = birth
				except: pass

				if result:
					result['temp'] = {'imdb' : {}} # Always add the IMDb temp, since we check if the this item is from an IMDb list in metadataImdb().
					if resultImdb: result['temp']['imdb'] = resultImdb
					if resultList: result['temp']['imdb']['list'] = resultList
					return result
		except: Logger.error()
		return None

	##############################################################################
	# FILTER
	##############################################################################

	@classmethod
	def _filter(self, items, year = None, date = None, rating = None, votes = None, genre = None):
		try:
			# Eg: Privacy
			if not items or Tools.isString(items): return items

			# Year
			try:
				if not year is None:
					if not Tools.isArray(year): year = [year, year]
					temp = []
					for item in items:
						value = item.get('year')
						if value is None or ((year[0] is None or value >= year[0]) and (year[1] is None or value <= year[1])):
							temp.append(item)
					items = temp
			except: Logger.error()

			# Date
			try:
				if not date is None:
					if not Tools.isArray(date): date = [date, date]
					date = [Time.timestamp(fixedTime = i, format = Time.FormatDate, utc = True) if Tools.isString(i) else i for i in date]
					temp = []
					for item in items:
						value = item.get('premiered')
						if value is None:
							temp.append(item)
						else:
							value = Time.timestamp(fixedTime = value, format = Time.FormatDate, utc = True)
							if (date[0] is None or value >= date[0]) and (date[1] is None or value <= date[1]):
								temp.append(item)
					items = temp
			except: Logger.error()

			# Rating
			try:
				if not rating is None:
					if not Tools.isArray(rating): rating = [rating, None]
					temp = []
					for item in items:
						value = item.get('rating') or item.get('temp', {}).get('imdb', {}).get('voting', {}).get('rating')
						if value is None or ((rating[0] is None or value >= rating[0]) and (rating[1] is None or value <= rating[1])):
							temp.append(item)
					items = temp
			except: Logger.error()

			# Votes
			try:
				if not votes is None:
					if not Tools.isArray(votes): votes = [votes, None]
					temp = []
					for item in items:
						value = item.get('votes') or item.get('temp', {}).get('imdb', {}).get('voting', {}).get('votes')
						if value is None or ((votes[0] is None or value >= votes[0]) and (votes[1] is None or value <= votes[1])):
							temp.append(item)
					items = temp
			except: Logger.error()

			# Genre
			try:
				if not genre is None:
					genre = self._convertGenre(genre = genre, inverse = True, default = True)
					if genre:
						temp = []
						for item in items:
							value = item.get('genre')
							if value is None: temp.append(item)
							elif any(i in genre for i in value): temp.append(item)
						items = temp
			except: Logger.error()
		except: Logger.error()
		return items

	##############################################################################
	# DISCOVER
	##############################################################################

	def discover(self, media = None, niche = None, id = None, query = None, keyword = None, status = None, release = None, year = None, date = None, duration = None, rating = None, votes = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, group = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, filter = None, cache = None):
		try: return self._retrieve(reduce = True, link = MetaImdb.LinkSearchTitle, media = media, niche = niche, id = id, query = query, keyword = keyword, status = status, release = release, year = year, date = date, duration = duration, rating = rating, votes = votes, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = group, watch = watch, theater = theater, limit = limit, page = page, offset = offset, sort = sort, order = order, filter = filter, cache = cache)
		except: Logger.error()
		return None

	def discoverMovie(self, niche = None, id = None, query = None, keyword = None, status = None, release = None, year = None, date = None, duration = None, rating = None, votes = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, group = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, filter = None, cache = None):
		return self.discover(media = Media.Movie, niche = niche, id = id, query = query, keyword = keyword, status = status, release = release, year = year, date = date, duration = duration, rating = rating, votes = votes, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = group, watch = watch, theater = theater, limit = limit, page = page, offset = offset, sort = sort, order = order, filter = filter, cache = cache)

	def discoverShow(self, niche = None, id = None, query = None, keyword = None, status = None, release = None, year = None, date = None, duration = None, rating = None, votes = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, group = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, filter = None, cache = None):
		return self.discover(media = Media.Show, niche = niche, id = id, query = query, keyword = keyword, status = status, release = release, year = year, date = date, duration = duration, rating = rating, votes = votes, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = group, watch = watch, theater = theater, limit = limit, page = page, offset = offset, sort = sort, order = order, filter = filter, cache = cache)

	def discoverPerson(self, query = None, group = None, gender = None, limit = None, page = None, offset = None, sort = None, order = None, filter = None, cache = None):
		try: return self._retrieve(reduce = True, link = MetaImdb.LinkSearchPerson, query = query, group = group, gender = gender, limit = limit, page = page, offset = offset, sort = sort, order = order, filter = filter, cache = cache)
		except: Logger.error()
		return None

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media = None, niche = None, query = None, keyword = None, status = None, year = None, date = None, duration = None, rating = None, votes = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, group = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, filter = None, cache = None):
		if filter is None: filter = MetaProvider.FilterNone # Do not filter when searching.
		return self.discover(media = media, niche = niche, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, rating = rating, votes = votes, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = group, watch = watch, theater = theater, limit = limit, page = page, offset = offset, sort = sort, order = order, filter = filter, cache = cache)

	def searchMovie(self, niche = None, query = None, keyword = None, status = None, year = None, date = None, duration = None, rating = None, votes = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, group = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, filter = None, cache = None):
		return self.search(media = Media.Movie, niche = niche, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, rating = rating, votes = votes, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = group, watch = watch, theater = theater, limit = limit, page = page, offset = offset, sort = sort, order = order, filter = filter, cache = cache)

	def searchShow(self, media = None, niche = None, query = None, keyword = None, status = None, year = None, date = None, duration = None, rating = None, votes = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, group = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, filter = None, cache = None):
		return self.search(media = Media.Show, niche = niche, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, rating = rating, votes = votes, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = group, watch = watch, theater = theater, limit = limit, page = page, offset = offset, sort = sort, order = order, filter = filter, cache = cache)

	def searchPerson(self, query = None, group = None, gender = None, limit = None, page = None, offset = None, sort = None, order = None, filter = None, cache = None):
		return self.discoverPerson(query = query, group = group, gender = gender, limit = limit, page = page, offset = offset, sort = sort, order = order, filter = filter, cache = cache)

	##############################################################################
	# LIST
	##############################################################################

	# Get the IMDb ID of a list.
	# Works for a user's watchlist, but not for a user's rating list.
	def listId(self, link, cache = True):
		try:
			def _listId(link):
				try:
					data = self._request(link = link)

					if data == MetaImdb.Privacy: return data

					# New list structure.
					json = self._extractJson(data = data, full = True)
					if json:
						id = json.get('aboveTheFoldData', {}).get('listId')
						if id: return id

					# Old list structure.
					parser = self.parser(data = data)
					id = parser.find('meta', {'property': 'pageId'})['content']
					if Regex.extract(data = id, expression = self._idExpressionList()): return id
				except: pass
				return None

			result = Cache.instance().cacheSeconds(timeout = MetaImdb.CacheListId, function = _listId, link = link)

			# Delete the cache entry if it fails.
			if not result or result == MetaImdb.Privacy: Cache.instance().cacheDelete(function = _listId, link = link)

			return result
		except: pass
		return None

	def lists(self, user = None, cache = None):
		try:
			items = self._retrieve(link = self._linkLists(user = user), media = Media.List, cache = cache)
			if items: return items
		except: Logger.error()
		return None

	# Lists can be retrieve in one of the following ways:
	#	1. HTML: Limited filtering available in pre-request. Paging and sorting available in pre-request. Should be used in menus if paging/filtering/sorting is used.
	#	2. CSV: Limited filtering available in post-request. No sorting available. No images available. All items retrieved at once, therefore no paging. Should be used for non-menu where paging is not needed and/or all items are required at once.
	# UPDATE: IMDb has now also changed the old page HTML. It now works similar to the Advanced Search and can return a maximum of 100 items. Use CSV by default.
	# UPDATE (2024-11-11): IMDb has changed the CSV export again. Not it creates an export on AWS which takes some time to generate. But the only way to get the URL to the export is to be logged in, which is impossible via code.
	def list(self, id = None, media = None, year = None, date = None, rating = None, votes = None, genre = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, csv = False, cache = None):
		try:
			id = self._idList(id)
			if csv:
				items = self._retrieve(link = MetaImdb.LinkList, id = id, media = media, cache = cache, csv = True)
				return self._filter(items = items, year = year, date = date, rating = rating, votes = votes, genre = genre)
			else:
				return self._retrieve(link = MetaImdb.LinkList, id = id, media = media, year = year, date = date, rating = rating, votes = votes, genre = genre, watch = watch, theater = theater, limit = limit, page = page, offset = offset, sort = sort, order = order, cache = cache)
		except: Logger.error()
		return None

	# Do not retrieve the person lists using CSV, since it does not contain images.
	def listPerson(self, id = None, limit = None, page = None, offset = None, sort = None, order = None, csv = False, cache = None):
		return self.list(id = id, limit = limit, page = page, offset = offset, sort = sort, order = order, csv = csv, cache = cache)

	# Lists can be retrieve in one of the following ways:
	#	1. HTML: Limited filtering available in pre-request. Paging and sorting available in pre-request. Should be used in menus if paging/filtering/sorting is used.
	#	2. CSV: Limited filtering available in post-request. No sorting available. All items retrieved at once, therefore no paging. Should be used for non-menu where paging is not needed and/or all items are required at once.
	def listWatch(self, user = None, id = None, media = None, year = None, date = None, rating = None, votes = None, genre = None, watch = None, theater = None, limit = None, page = None, offset = None, sort = None, order = None, csv = False, cache = None):
		try:
			# Note that this does not return the user's ratings.
			# Ratings are only added to the CSV if the user is logged in (aka session cookies are added to the request).
			if not id:
				id = self.listId(link = self._linkListWatch(user = user))
				if id == MetaImdb.Privacy: return id
			if id: return self.list(id = id, media = media, year = year, date = date, rating = rating, votes = votes, genre = genre, watch = watch, theater = theater, limit = limit, page = page, offset = offset, sort = sort, order = order, csv = csv, cache = cache)
		except: Logger.error()
		return None

	# Ratings lists can be retrieve in one of the following ways:
	#	1. HTML: Limited filtering available in post-request. Paging and limited sorting available in pre-request.
	# UPDATE (2024-11-11): GET parameters do not work with the ratings list anymore. They are still set when using the JS dialog on the website, but the actual call goes through their API.
	def listRating(self, user = None, media = None, year = None, date = None, rating = None, votes = None, genre = None, limit = None, page = None, offset = None, sort = None, order = None, cache = None):
		try:
			# Exporting the ratings list to CSV is only possible if the user is logged in (aka session cookies are added to the request).
			# The only way to get this is through HTML.
			# The HTML page does not have any filter options, only a few sorting and paging options.
			link = self._linkListRating(user = user, media = media, limit = limit, page = page, offset = offset, sort = sort, order = order)
			if link:
				items = self._retrieve(link = link, media = media, cache = cache)
				return self._filter(items = items, year = year, date = date, rating = rating, votes = votes, genre = genre)
		except: Logger.error()
		return None

	def listCheckin(self, user = None, media = None, year = None, date = None, rating = None, votes = None, genre = None, limit = None, page = None, offset = None, sort = None, order = None, cache = None):
		try:
			link = self._linkListCheckin(user = user, media = media, limit = limit, page = page, offset = offset, sort = sort, order = order)
			if link:
				items = self._retrieve(link = link, media = media, cache = cache)
				return self._filter(items = items, year = year, date = date, rating = rating, votes = votes, genre = genre)
		except: Logger.error()
		return None

	##############################################################################
	# METADATA
	##############################################################################

	# NB: cache = False: do not cache the data by default. Read the comment at _request().
	def metadata(self, id, language = None, country = None, cache = False, retry = 1):
		if not id: return None
		id = self._idTitle(id)

		raw = self._request(link = self._linkTitle(id = id), language_ = language, country_ = country, cache = MetaImdb.CacheMetadata if cache is True else cache if cache else MetaImdb.CacheNone, lock = self._metadataLock(), timeout = self._metadataTimeout(retry = retry))
		if not raw: return None

		data = self._extractJson(data = raw, full = False)
		try: datas = data['props']['pageProps']
		except:
			# If too many requests are made to IMDb within a short period of time, IMDb starts returning error pages (probably some DDoS protection ot just webserver connection limits), which will cause it to fail here.
			# Try again a few times, otherwise give up.
			# Update: Even with 3 retries, there are still sometimes a bunch of titles for which this does not work, especially if many titles are retrieved in batch. Even waiting minutes still returns this page.
			# Update: Only when changing VPN, do these pages load again. IMDb probably detects too many incoming connections in a short period of time and then blocks that IP. So retrying will not help in this case.
			# Update: Keep the number of retries and the sleep time low, in order to not hold up a foreground metadata retrieval process. If it fails, another attempt will be madeto get the IMDb metadata later when the list is reloaded.
			#	<div class="error-page-message">
            #	    <span>Something went wrong. Please reload the page and try again.<!-- -->&nbsp;</span>
            #	    <a href="/" tabindex="0" class="ipc-link ipc-link--base">Go to the homepage</a>
            #	</div>
            #	<div class="error-page-quote-bubble">
            #	    <div class="error-page-quote-bubble-inner">
            #	        <div class="error-page-quote-bubble-text">
            #	            <h1>Error</h1>
            #	            "Houston, we have a problem."
            #	        </div>
            #	    </div>
            #	    <div class="error-page-quote-bubble-tail"></div>
            #	</div>
			if retry and raw and id and ('Please reload the page and try again' in raw or 'Houston, we have a problem' in raw):
				self._logError(id = id, message = 'Temporary IMDb connection problems. Retrying in a few seconds.')
				Time.sleepRandom(0.5, 2.0)
				return self.metadata(id = id, language = language, country = country, cache = MetaImdb.CacheNone, retry = int(retry) - 1)
			else:
				return self._logFatal(id = id, code = 'metadata-a', update = True)

		data = []
		try: data.append(datas['mainColumnData'])
		except: pass
		try: data.append(datas['aboveTheFoldData'])
		except: pass
		if not data: return self._logFatal(id = id, code = 'metadata-b', update = True)

		result = {}
		finance = {}
		tempImdb = {}
		tempMetacritic = {}

		self._extract(id = id, result = result, data = data, attribute = 'imdb', keys = ['id'])
		if 'imdb' in result:
			id = result['imdb']
			result['id'] = {'imdb' : result['imdb']}
		else: return self._logFatal(id = id, code = 'metadata-c')

		self._extract(id = id, result = result, data = data, attribute = 'niche', keys = ['titleType', 'id'], function = lambda x : self._extractNiche(x, item = data)) # Get mini-series niche.

		self._extract(id = id, result = result, data = data, attribute = 'title', keys = ['titleText', 'text'], function = self._extractTitle)
		self._extract(id = id, result = result, data = data, attribute = 'originaltitle', keys = ['originalTitleText', 'text'], function = self._extractTitle)
		self._extract(id = id, result = result, data = data, attribute = 'plot', keys = ['plot', 'plotText', 'plainText'], function = self._extractDescription)
		self._extract(id = id, result = result, data = data, attribute = 'year', keys = ['releaseYear', 'year'])
		self._extract(id = id, result = result, data = data, attribute = 'premiered', function = self._extractPremiered)
		self._extract(id = id, result = result, data = data, attribute = 'genre', keys = ['genres', 'genres'], function = [self._extractIdList, self._extractGenre])
		self._extract(id = id, result = result, data = data, attribute = 'mpaa', keys = ['certificate', 'rating'], function = lambda x : self._extractCertificate(x, media = media))
		self._extract(id = id, result = result, data = data, attribute = 'duration', keys = ['runtime', 'seconds'])
		self._extract(id = id, result = result, data = data, attribute = 'status', keys = ['productionStatus', 'currentProductionStage', 'text'], function = self._extractStatus)
		self._extract(id = id, result = result, data = data, attribute = 'studio', keys = ['production', 'edges'], function = self._extractStudio)
		self._extract(id = id, result = result, data = data, attribute = 'country', keys = ['countriesOfOrigin', 'countries'], function = [self._extractIdListLower, self._extractCountry])
		self._extract(id = id, result = result, data = data, attribute = 'language', keys = ['spokenLanguages', 'spokenLanguages'], function = [self._extractIdListLower, self._extractLanguage])
		self._extract(id = id, result = result, data = data, attribute = 'homepage', keys = ['detailsExternalLinks', 'edges'], function = self._extractHomepage)

		self._extract(id = id, result = result, data = data, attribute = 'cast', keys = ['cast', 'edges'], function = self._extractCast)
		self._extract(id = id, result = result, data = data, attribute = 'director', keys = ['directors'], function = self._extractCrew)
		self._extract(id = id, result = result, data = data, attribute = 'writer', keys = ['writers'], function = self._extractCrew)

		self._extract(id = id, result = result, data = data, attribute = 'award', keys = ['prestigiousAwardSummary'], function = self._extractAward)

		self._extract(id = id, result = result, data = data, attribute = 'count', keys = ['episodes'], function = self._extractCount)

		self._extract(id = id, result = finance, data = data, attribute = 'budget', keys = ['productionBudget', 'budget', 'amount'])
		self._extract(id = id, result = finance, data = data, attribute = 'revenue', keys = ['worldwideGross', 'total', 'amount'])
		self._extract(id = id, result = finance, data = data, attribute = 'opening', keys = ['openingWeekendGross', 'gross', 'total', 'amount'])
		if finance:
			try: finance['profit'] = finance['revenue'] - finance['budget']
			except: pass
			result['finance'] = finance

		self._extract(id = id, result = tempImdb, data = data, attribute = ['voting', 'rating'], keys = ['ratingsSummary', 'aggregateRating'], function = self._extractRating)
		self._extract(id = id, result = tempImdb, data = data, attribute = ['voting', 'votes'], keys = ['ratingsSummary', 'voteCount'], function = self._extractVotes)
		self._extract(id = id, result = tempMetacritic, data = data, attribute = ['voting', 'rating'], keys = ['metacritic', 'metascore', 'score'], function = self._extractMetacritic, log = False)

		result['rating'] = self._data(tempImdb, ['voting', 'rating'])
		result['votes'] = self._data(tempImdb, ['voting', 'votes'])

		premiered = result.get('premiered')
		if premiered:
			if not result.get('time'): result['time'] = {}
			result['time'][MetaTools.TimePremiere] = ConverterTime(premiered, format = ConverterTime.FormatDate, utc = True).timestamp()

		# Add the images listed under "Photos" on the IMDb page.
		# Some titles are only on IMDb, but not on Trakt/TMDb.
		# Or they are on Trakt/TMDb, but Trakt/TMDb do not have images, especially for newer releases.
		# Use the IMDb photos as fanart in this case, since it looks better than using the psoter as fanart fallback.
		# Eg (new release, not images on Trakt/TMDb yet): tt32400680
		self._extract(id = id, result = tempImdb, data = data, attribute = [MetaImage.Attribute], keys = ['titleMainImages', 'edges'], function = self._extractImage)

		poster = self._extract(id = id, data = data, keys = ['primaryImage', 'url'], function = self.linkImage)
		if poster:
			if not tempImdb.get(MetaImage.Attribute): tempImdb[MetaImage.Attribute] = {}
			if not tempImdb.get( MetaImage.Attribute).get( MetaImage.TypePoster): tempImdb[MetaImage.Attribute][MetaImage.TypePoster] = []
			tempImdb[MetaImage.Attribute][MetaImage.TypePoster].insert(0, poster)

		result[MetaImage.Attribute] = {}
		for type, images in (tempImdb.get(MetaImage.Attribute) or {}).items():
			if images:
				if not result[MetaImage.Attribute].get(type): result[MetaImage.Attribute][type] = []
				if not Tools.isArray(images): images = [images]
				for image in images:
					if image:
						image = MetaImage.create(link = image, provider = self.id(), sort = {MetaImage.SortIndex : 0, MetaImage.SortVote : 0})
						if image: result[MetaImage.Attribute][type].append(image)

		result['temp'] = {}

		# Always add the temp IMDb structure, even if it is an empty dict.
		# This is important for MetaManager if a title only exists on IMDb, but not on other providers (eg tt23624830).
		# Do not "if tempImdb", because the dict can be empty if there are no votes and images for the title on IMDb.
		# if tempImdb: result['temp']['imdb'] = tempImdb
		result['temp']['imdb'] = tempImdb

		if tempMetacritic: result['temp']['metacritic'] = tempMetacritic

		return result

	def metadataMovie(self, id, language = None, country = None, cache = False, retry = 1):
		return self.metadata(id = id, language = language, country = country, cache = cache, retry = retry)

	def metadataShow(self, id, language = None, country = None, cache = False, retry = 1):
		return self.metadata(id = id, language = language, country = country, cache = cache, retry = retry)

	def metadataSeason(self, id, season = None, limit = None, language = None, country = None, cache = False, threaded = None):
		try:
			if id:
				if season is None or season is True or season is False: season = [i for i in range(1, (limit or 2) + 1)]
				if not Tools.isArray(season): season = [season]

				if Tools.isArray(season):
					requests = [{'id' : i, 'function' : self.metadataEpisode, 'parameters' : {'id' : id, 'language' : language, 'country' : country, 'season' : i, 'cache' : cache}} for i in season]
					data = self._execute(requests = requests, threaded = threaded)

					if data:
						results = []
						for k, v in data.items():
							result = {'media' : Media.Season, 'season' : k, 'year' : None, 'premiered' : None, 'aired' : None, 'episodes' : [], 'temp' : {'imdb' : {'voting' : {}, 'count' : None}}}
							if v: result.update(v)
							else: continue

							voting = []
							episodes = result.get('episodes')
							if episodes:
								first = None

								for episode in episodes:
									if episode:
										if episode.get('episode') == 1: first = episode
										ratingEpisode = episode.get('rating')
										votesEpisode = episode.get('votes')
										if ratingEpisode and not votesEpisode is None: voting.append({'rating' : ratingEpisode, 'votes' : votesEpisode}) # NB: Do not include 0.0 ratings, which are typical for unaired episodes.

								# The first episode can be a special or unaired pilot without a date.
								# Eg: GoT S01
								if not first: first = episodes[0]
								if first:
									result['year'] = first.get('year')
									result['premiered'] = result['aired'] = first.get('premiered')

							try:
								if voting:
									voting = self.mMetatools.votingAverageWeighted(metadata = voting, maximum = True) # maximum: Do not return the total vote count.

									# The bulk metadata contains all episodes and is therefore more accurate.
									# Use the bulk ratings if there are more votes, since the bulk data can sometimes be outdated by a few days.
									votingBulk = self.bulk(id = id, season = k)
									if not voting or (votingBulk and votingBulk.get('votes', 0) > voting.get('votes', 0)): voting = votingBulk

									if voting:
										result['rating'] = result['temp']['imdb']['voting']['rating'] = voting['rating']
										result['votes'] = result['temp']['imdb']['voting']['votes'] = voting['votes']
							except: Logger.error()

							try:
								bulk = self.bulk(id = id, season = k, data = True)
								result['temp']['imdb']['count'] = max(len(episodes) if episodes else 0, len(bulk.get('episodes') or []) if bulk else 0)
							except: Logger.error()

							try: del result['episodes']
							except: pass
							results.append(result)

						return results or None
		except: Logger.error()
		return None

	# The new page can return a maximum of 50 episodes, due to similar paging restrictions as Advanced Search.
	# There currently does not seem any way of paging, or adding a GET parameter to return more episodes.
	# We could do an advanced search: https://imdb.com/search/title/?series=ttxxxxxxx
	# However, we cannot filter by season, and the JSON data does not contain the season/episode numbers.
	# NB: cache = False: do not cache the data by default. Read the comment at request().
	def metadataEpisode(self, id, season, language = None, country = None, cache = False, threaded = None):
		try:
			if not id: return None

			data = self._request(link = self._linkTitle(id = id, season = MetaImdb.Special if season == 0 else season), language_ = language, country_ = country, cache = MetaImdb.CacheMetadata if cache is True else cache if cache else MetaImdb.CacheNone, lock = self._metadataLock(), timeout = self._metadataTimeout())
			if not data: return None

			# IMDb only sometimes returns the page with JSON. Other times it just returns the pure already formatted HTML.
			# Especially if many IMDb pages are requested in a short period of time, IMDb more often returns pure HTML than JSON.
			# When it returns JSON, it is the new styled IMDb episode page.
			# When it does not return JSON, it is the old styled IMDb episode page.
			parser = self.parser(data = data)

			result = self._metadataEpisodeNew(id = id, season = season, parser = parser)
			if not result: result = self._metadataEpisodeOld(id = id, season = season, parser = parser)
			return result
		except:
			Logger.error()
			return self._logFatal(id = id, code = 'metadata-episode-z')

	def _metadataEpisodeOld(self, id, season, parser):
		try:
			months = {'Jan' : '01', 'Feb' : '02', 'Mar' : '03', 'Apr' : '04', 'May' : '05', 'Jun' : '06', 'Jul' : '07', 'Aug' : '8', 'Sep' : '09', 'Oct' : '10', 'Nov' : '11', 'Dec' : '12'}

			episodes = parser.find('div', {'class' : 'eplist'})

			# Some shows have no listed episodes.
			# Eg: https://www.imdb.com/title/tt21871318/
			if not episodes: return None

			episodes = episodes.find_all('div', {'class' : 'list_item'})
			if not episodes: return self._logFatal(id = id, code = 'metadata-episode-old-a', update = True)

			expressionId = self._idExpressionTitle()
			try:
				show = parser.find('div', {'class' : 'subpage_title_block'}).find('a', {'itemprop' : 'url'})
				showId = Regex.extract(data = show['href'], expression = expressionId)
				showTitle = show.text
			except:
				showId = None
				showTitle = None

			result = []
			for episode in episodes:
				resultEpisode = {}
				resultTemp = {}

				if showId: resultEpisode['id'] = {'imdb' : showId}
				if showTitle: resultEpisode['tvshowtitle'] = self._extractTitle(showTitle)

				name = episode.find('a', {'itemprop' : 'name'})
				if name:
					idEpisode = Regex.extract(data = name['href'], expression = expressionId)
					if idEpisode:
						if not 'id' in resultEpisode or not resultEpisode['id']: resultEpisode['id'] = {}
						resultEpisode['id']['episode'] = {'imdb' : idEpisode}
					resultEpisode['title'] = self._extractTitle(name.text)

				plot = episode.find('div', {'itemprop' : 'description'})
				if plot: resultEpisode['plot'] = self._extractDescription(plot.text)

				ratings = episode.find('div', {'class' : 'ipl-rating-widget'})
				if ratings:
					rating = ratings.find('span', {'class' : 'ipl-rating-star__rating'})
					if rating:
						if not 'voting' in resultTemp: resultTemp['voting'] = {}
						resultTemp['voting']['rating'] = float(rating.text)

					votes = ratings.find('span', {'class' : 'ipl-rating-star__total-votes'})
					if votes:
						if not 'voting' in resultTemp: resultTemp['voting'] = {}
						resultTemp['voting']['votes'] = int(votes.text.replace(',', '').replace('(', '').replace(')', ''))

				premiered = episode.find('div', {'class' : 'airdate'})
				if premiered:
					date = None
					premiered = premiered.text
					for month, number in months.items():
						if month in premiered:
							try:
								number = '-%s-' % number
								premiered = premiered.replace(' %s. ' % month, number).replace(' %s ' % month, number)

								# Some episodes just have a month and year, but no day (eg: " May 2004").
								# Note that these dates have preceeding spaces or newlines, so strip below.
								# Just assume the 1st of the month.
								# https://www.imdb.com/title/tt0434706/episodes?season=1
								if premiered.strip().startswith('-'): premiered = '01' + premiered.strip()

								date = ConverterTime(premiered, format = '%d-%m-%Y', utc = True).string(format = '%Y-%m-%d')
								break
							except: Logger.error()
					if date:
						resultEpisode['premiered'] = date
						resultEpisode['aired'] = date
						resultEpisode['year'] = int(Regex.extract(data = date, expression = '(\d{4})'))

				thumbnail = episode.find('div', {'class' : 'image'})
				if thumbnail:
					number = thumbnail.text
					if number:
						number = Regex.extract(data = number, expression = 's(\d+).*?ep?(\d+)', group = None, all = True)
						if number:
							resultEpisode['season'] = int(number[0][0])
							resultEpisode['episode'] = int(number[0][1])

					thumbnail = thumbnail.find('img')
					if thumbnail:
						thumbnail = thumbnail['src']
						if thumbnail:
							if not 'image' in resultTemp: resultTemp['image'] = {}
							image = resultTemp['image']['thumb'] = self.linkImage(link = thumbnail)
							if image:
								image = MetaImage.create(link = image, provider = self.id(), sort = {MetaImage.SortIndex : 0, MetaImage.SortVote : 0})
								if image: resultEpisode[MetaImage.Attribute] = {MetaImage.TypeThumb : [image]}

				if resultTemp: resultEpisode['temp'] = {'imdb' : resultTemp}
				if resultEpisode: result.append(resultEpisode)

			return {'episodes' : result} if result else None
		except:
			Logger.error()
			return self._logFatal(id = id, code = 'metadata-episode-old-z')

	def _metadataEpisodeNew(self, id, season, parser):
		try:
			data = None
			datas = parser.find_all('script', {'type' : 'application/json'})
			for i in datas:
				try:
					i = Converter.jsonFrom(i.string)
					if 'props' in i:
						data = i
						break
				except: pass
			if not data: return None

			showId = None
			showTitle = None
			episodes = None

			try: data = data['props']['pageProps']['contentData']
			except:
				data = None
				self._logFatal(id = id, code = 'metadata-episode-new-a', update = True)
			if data:
				try: show = data['entityMetadata']
				except:
					show = None
					self._logFatal(id = id, code = 'metadata-episode-new-b', update = True)
				if show:
					showId = self._extract(id = id, data = show, keys = ['id'])
					showTitle = self._extract(id = id, data = show, keys = ['titleText', 'text'])
					try: episodes = data['section']['episodes']['items']
					except: self._logFatal(id = id, code = 'metadata-episode-new-c', missing = True) # Future shows sometimes have no episodes listed yet.

			if not showId: showId = id
			result = []
			bulk = {}

			# Add episodes from the bulk metadata, since it contains all episodes, instead of a maximum of 50 episodes from the HTML page.
			# This allows us to at least have the ID, rating, and votes for episodes beyond number 51+.
			# Add them here, and then overwrite them with the HTML data below.
			bulked = self.bulk(id = id, season = season, data = True)
			if bulked:
				bulked = bulked.get('episodes')
				if bulked:
					for episode, item in bulked.items():
						idEpisode = item.get('id')
						rating = item.get('rating')
						votes = item.get('votes')

						resultEpisode = {}
						if showId: resultEpisode['id'] = {'imdb' : showId}
						if showTitle: resultEpisode['tvshowtitle'] = showTitle
						if idEpisode:
							if not 'id' in resultEpisode: resultEpisode['id'] = {}
							resultEpisode['id']['episode'] = {'imdb' : idEpisode}
						resultEpisode.update({
							'season' : item.get('season'),
							'episode' : item.get('episode'),
							'rating' : rating,
							'votes' : votes,
							'temp' : {
								'voting' : {
									'rating' : rating,
									'votes' : votes,
								}
							},
						})
						result.append(resultEpisode)
						bulk[idEpisode] = resultEpisode

			if episodes:
				for episode in episodes:
					resultEpisode = {}
					resultTemp = {}

					if showId: resultEpisode['id'] = {'imdb' : showId}
					if showTitle: resultEpisode['tvshowtitle'] = showTitle

					idEpisode = self._extract(id = id, data = episode, keys = ['id'])
					if idEpisode:
						if not 'id' in resultEpisode or not resultEpisode['id']: resultEpisode['id'] = {}
						resultEpisode['id']['episode'] = {'imdb' : idEpisode}

					self._extract(id = id, result = resultEpisode, data = episode, attribute = 'season', keys = ['season'], function = int)
					self._extract(id = id, result = resultEpisode, data = episode, attribute = 'episode', keys = ['episode'], function = int)
					self._extract(id = id, result = resultEpisode, data = episode, attribute = 'title', keys = ['titleText'], function = self._extractTitle)
					self._extract(id = id, result = resultEpisode, data = episode, attribute = 'plot', keys = ['plot'], function = self._extractDescription)

					self._extract(id = id, result = resultEpisode, data = episode, attribute = 'year', keys = ['releaseYear'], function = int)
					premiered = self._extract(id = id, data = episode, keys = ['releaseDate'])
					if premiered:
						# In very few cases, IMDb returns the date as a dictionary.
						#	Eg: {'month': 5, 'day': 1, 'year': 2006, '__typename': 'ReleaseDate'}
						time = None
						if Tools.isDictionary(premiered):
							try:
								premiered = '%d-%02d-%02d' % (premiered['year'], premiered['month'], premiered['day'])
								time = ConverterTime(premiered, format = ConverterTime.FormatDate, utc = True).timestamp()
							except: premiered = None
						else:
							time = ConverterTime(premiered, format = ConverterTime.FormatDateAmerican, utc = True)
							premiered = time.string(format = ConverterTime.FormatDate)
							time = time.timestamp()

						if premiered:
							resultEpisode['premiered'] = premiered
							resultEpisode['aired'] = premiered
							resultEpisode['year'] = int(Regex.extract(data = premiered, expression = '(\d{4})'))

							# Important for episodes that are only on IMDb and will not get the time from anywhere else.
							# Eg: GoT S01E00.
							if time:
								if not resultEpisode.get('time'): resultEpisode['time'] = {}
								resultEpisode['time'][MetaTools.TimePremiere] = time

					self._extract(id = id, result = resultEpisode, data = episode, attribute = 'rating', keys = ['aggregateRating'], function = self._extractRating)
					self._extract(id = id, result = resultEpisode, data = episode, attribute = 'votes', keys = ['voteCount'], function = self._extractVotes)
					if 'rating' in resultEpisode:
						if not 'voting' in resultTemp: resultTemp['voting'] = {}
						resultTemp['voting']['rating'] = resultEpisode['rating']
					if 'votes' in resultEpisode:
						if not 'voting' in resultTemp: resultTemp['voting'] = {}
						resultTemp['voting']['votes'] = resultEpisode['votes']

					# Future/unreleased episodes might not have a thumbnail yet.
					# IMDb then uses the show poster for those episode thumbnails.
					# Do not add those posters, otherwise they are displayed in the menu and look ugly.
					# Assume it is a thumbnail if the width is greater than the height.
					try: width = episode['image']['maxWidth']
					except: width = None
					try: height = episode['image']['maxHeight']
					except: height = None
					if not width or not height or (width > height):
						self._extract(id = id, result = resultTemp, data = episode, attribute = ['image', 'thumb'], keys = ['image', 'url'], function = self.linkImage)

					image = (resultTemp.get('image') or {}).get('thumb')
					if image:
						image = MetaImage.create(link = image, provider = self.id(), sort = {MetaImage.SortIndex : 0, MetaImage.SortVote : 0})
						if image: resultEpisode[MetaImage.Attribute] = {MetaImage.TypeThumb : [image]}

					if resultTemp: resultEpisode['temp'] = {'imdb' : resultTemp}
					if resultEpisode:
						found = bulk.get(idEpisode)
						if found:
							Tools.update(found, resultEpisode, none = False, lists = True, unique = False)
						else:
							result.append(resultEpisode)

			if result:
				result = Tools.listSort(data = result, key = lambda i : i.get('episode') or -1)
				return {'episodes' : result}
			return None
		except:
			Logger.error()
			return self._logFatal(id = id, code = 'metadata-episode-new-z')

	def _metadataTimeout(self, retry = None):
		# Use a low timeout for metadata(), if IMDb temporarily blocks pages due to batch requests, IMDb lets the connection time out.
		# This makes the Kodi menu load a lot longer, waiting for the IMDb requests to finish (if it is new uncached metadata).
		# Use a short timeout to reduce loading times.
		# If it fails, it can still be reretrieved on the next metadata refresh.
		return 15 if (retry or retry is None) else 10

	def _metadataLock(self):
		# Hopefully further reduce the chances of temporary IMDb blocks, by reducing the number of concurrent requests.
		# Although there are still 1 or 2 blocks, even with a lock limit of 5.
		return 10

	# NB: This does not fully work. IMDb hides a lot of awards (including big ones like Academy Awards and Primetime Emmies), which requires additional requests to their Graphql API (eg: GoT).
	# TMDb wants to add a new feature in the API. Maybe use that: https://trello.com/c/zLTMoZhb/109-add-awards-nominations
	# Or just extract the the summary award info from the main IMDb page.
	def metadataAward(self, id, link = None, data = None, cache = False):
		if not id: return None

		data = self._request(link = self._linkAward(id = id), cache = MetaImdb.CacheMetadata if cache is True else cache if cache else MetaImdb.CacheNone, lock = self._metadataLock(), timeout = self._metadataTimeout())
		if not data: return None

		try:
			parser = self.parser(data = data)
			datas = parser.find_all('script', {'type' : 'application/json'})

			data = None
			for i in datas:
				try:
					i = Converter.jsonFrom(i.string)
					if 'props' in i:
						data = i
						break
				except: pass

			try: data = data['props']['pageProps']['contentData']
			except: return self._logFatal(id = id, code = 'metadata-awards-a', update = True)

			countries = {
				# Academy Awards
				# Golden Globe Awards
				# Los Angeles Film Critics' Association
				# National Board of Review
				# National Society of Film Critics
				# New York Film Critics' Circle
				# Annie Awards
				# Golden Raspberry Awards
				# Sundance Film Festival
				# Screen Actors Guild Awards
				# Hollywood Film Awards
				# Directors Guild of America Awards
				# Tony Awards
				# Pulitzer Prize
				# MTV
				# Satellite Awards
				# AFI Awards
				# Critics Choice Awards
				# Black Reel Awards
				# AARP Movies for Grownups Awards
				# North Carolina Film Critics Association
				# Columbus Film Critics Association
				# Austin Film Critics Association
				# Allywood Film Critics Association Awards
				# Music City Film Critics' Association Awards
				# San Diego Film Critics Society Awards
				# Set Decorators Society of America, USA
				# Critics Association of Central Florida Awards
				# Hawaii Film Critics Society
				# Georgia Film Critics Association (GAFCA)
				# Portland Critics Association Awards
				# Chicago Indie Critics Awards (CIC)
				# North Dakota Film Society
				# Seattle Film Critics Society
				# Denver Film Critics Society
				# Motion Picture Sound Editors
				# Houston Film Critics Society Awards
				# PGA Awards
				# Cinema Audio Society
				# Costume Designers Guild Awards
				# Casting Society of America
				# Gold Derby Awards
				# Visual Effects Society Awards
				# Kids' Choice Awards
				# Grammy Awards
				'us' : '([\s\,\.\-\(\[]+(usa?)[\s\.\)\]]?|united\s*states|america|los\s*angeles|new\s*york|carolina|florida|hawaii|dakota|denver|columbus|austin|san\s*diego|portland|chicago|seattle|houston|hollywood|allywood|academy\s*award|oscar|golden\s*globe|emm(?:y|ie)\s|national\s*board.*review|national\s*society.*critic|annie\s|raspberr|sundance|screen.*actor.*guild|tony\s*award|pulitzer|mtv|satellite\s*ward|afi\s*ward|critics\s*choice|black\s*reel|aarp|music\s*city|gafca|georgia\s*film\s*critics|motion \s*picture\s*sound\s*editors|pga\s*award|cinema\s*audio\s*society|costume\s*designers\s*guild|golden\s*derby|visual\s*effects\s*society|kid.*choice|grammy)',

				# BAFTA Film Awards
				'uk' : '([\s\,\.\-\(\[]+(uk|gb)[\s\.\)\]]?|great\s*britain|united\s*kingdom|london|liverpool|bafta)',

				# Golden Screen Award
				'ca' : '(canada|canadian|golden\s*screen\s*award)',

				# AACTA International Awards
				'au' : '(australia|sydney|perthaacta)',

				# Palme d’Or – The Cannes International Film Festival
				# César Awards
				# Méliès d’Or
				# Cartoon d’Or
				'fr' : '(france|french|paris|d(?:\'|’)or|palme.*or|cannes|c(?:é|e)sar)',

				# The Golden Bear – The Berlin International Film Festival
				'de' : '(german|deutsch|golden(?:er)?\s*b(?:ea|ä)r|berlin|m(?:u|ue|ü)nchen)',

				# The Golden Leopard
				'ch' : '(golden(?:er)?\s*leopard)',

				# National Film Awards
				# FilmFare Awards
				'in' : '(india|hindi|national\s*film\s*award|film\s*fare)',
			}

			result = {
				'count' : {
					'total' : None,
					'wins' : None,
					'losses' : None,
					'nominations' : None,
				},
				'awards' : [],
			}

			self._extract(id = id, data = data, keys = ['winsCount'], result = result['count'], attribute = 'wins')
			self._extract(id = id, data = data, keys = ['nominationsCount'], result = result['count'], attribute = 'nominations')

			# Not sure if this is accurate.
			result['count']['total'] = result['count']['nominations']
			if not result['count']['wins'] is None and not result['count']['nominations'] is None: result['count']['losses'] = max(0, result['count']['nominations'] - result['count']['wins'])

			try: data = data['categories']
			except:
				self._logFatal(id = id, code = 'metadata-awards-b')
				return result

			for item in data:
				try:
					entry = {
						'name' : None,
						'country' : None,
						'awards' : [],
					}

					name = self._extract(id = id, data = item, keys = ['name'])

					for country, expression in countries.items():
						if Regex.match(data = name, expression = expression):
							entry['country'] = country
							break

					entry['name'] = Regex.remove(data = name, expression = '([\s\,\.\-\(\[]*(usa?|uk|gb|de)[\s\.\)\]]*$)')

					if 'section' in item:
						item = item['section']
						if 'items' in item:
							item = item['items']
							if item:
								for subitem in item:
									subentry = {
										'award' : None,
										'type' : None,
										'year' : None,
										'category' : None,
										'subcategory' : None,
										'people' : [],
									}

									type = self._extract(id = id, data = subitem, keys = ['rowTitle'])

									year = Regex.extract(data = type, expression = '((?:19|2[01])\d{2})')
									if year: subentry['year'] = int(year)

									if Regex.match(data = type, expression = '(winner)'): subentry['type'] = 'winner'
									elif Regex.match(data = type, expression = '(nominee)'): subentry['type'] = 'nominee'

									self._extract(id = id, data = subitem, keys = ['rowSubTitle'], result = subentry, attribute = 'award')
									if 'listContent' in subitem:
										content = subitem['listContent']
										if content:
											expression = '\s*(?:[\(\[]|[\,\-]\s)\s*(.*?)[\s\)\]]*$'
											for i in content:
												if i and 'className' in i and i['className'] == 'awardCategoryName':
													category = self._extract(id = id, data = i, keys = ['text'])
													if category:
														subcategory = Regex.extract(data = category, expression = expression)
														if subcategory:
															subentry['category'] = Regex.remove(data = category, expression = expression)
															subentry['subcategory'] = subcategory
														else:
															subentry['category'] = category
														break
									if 'subListContent' in subitem:
										content = subitem['subListContent']
										if content:
											for i in content:
												i = self._extract(id = id, data = i, keys = ['text'])
												if i: subentry['people'].append(i)
									entry['awards'].append(subentry)
					result['awards'].append(entry)
				except:
					Logger.error()
					self._logFatal(id = id, code = 'metadata-awards-c')

			return result
		except:
			Logger.error()
			return self._logFatal(id = id, code = 'metadata-awards-z')

	def metadataAwardMovie(self, id, cache = False):
		return self.metadata(id = id, cache = cache)

	def metadataAwardShow(self, id, cache = False):
		return self.metadata(id = id, cache = cache)

	##############################################################################
	# PACK
	##############################################################################

	def metadataPack(self, id = None, imdb = None, detail = None):
		complete = True
		result = None
		try:
			if not id: id = imdb
			if id:
				data = self.bulk(id = id, data = True)
				if data:
					from lib.meta.pack import MetaPack

					data = Tools.copy(data) # Since we sort it inplace below.
					seasons = data.get('seasons')
					if seasons:
						for i, season in seasons.items():
							episodes = season.get('episodes')
							if episodes: season['episodes'] = Tools.listSort(episodes.values(), key = lambda i : i.get('episode'))
						data['seasons'] = Tools.listSort(seasons.values(), key = lambda i : i.get('season'))

						sequential = 0
						seasons = []
						for season in (data.get('seasons') or []):
							numberSeason = season.get('season')

							episodes = []
							for episode in (season.get('episodes') or []):
								numberEpisode = episode.get('episode')
								if numberSeason > 0 and not numberEpisode == 0: sequential += 1
								episodes.append({
									'id'		: {'imdb' : episode.get('id')},

									# Use the standard episode number if IMDb has a single absolute season.
									# Otherwise if there are a lot of episodes, the standard and sequential numbers can deviate from each other at the later episodes.
									# Eg: Good times bad times.
									'number'	: {MetaPack.NumberStandard : [numberSeason, numberEpisode], MetaPack.NumberSequential : [1, 0 if numberEpisode == 0 else numberEpisode if numberSeason == 1 else sequential if numberSeason else 0]},
								})

							seasons.append({
								'id'		: {'imdb' : season.get('id')},
								'number'	: {MetaPack.NumberStandard : numberSeason, MetaPack.NumberSequential : 1},
								'episodes'	: episodes,
							})

						result = {
							'id'		: {'imdb' : data.get('id')},
							'seasons'	: seasons,
						}
				else: complete = False
			else: complete = False
		except: Logger.error()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	##############################################################################
	# BULK
	##############################################################################

	@classmethod
	def bulkSettingsSelected(self):
		return Settings.getBoolean(MetaImdb.BulkSettingsSelected)

	@classmethod
	def bulkSettingsSelectedSet(self):
		Settings.set(MetaImdb.BulkSettingsSelected, True)

	@classmethod
	def bulkSettingsRefreshed(self):
		return Settings.getInteger(MetaImdb.BulkSettingsRefreshed)

	@classmethod
	def bulkSettingsRefreshedSet(self):
		Settings.set(MetaImdb.BulkSettingsRefreshed, Time.timestamp())

	@classmethod
	def bulkSettingsMode(self):
		return Settings.getString(MetaImdb.BulkSettingsMode).lower()

	@classmethod
	def bulkSettingsModeEnabled(self):
		return not self.bulkSettingsMode() == MetaImdb.BulkModeDisabled

	@classmethod
	def bulkSettingsModeDisabled(self):
		return self.bulkSettingsMode() == MetaImdb.BulkModeDisabled

	@classmethod
	def bulkSettingsModeSet(self, bulk):
		Settings.set(MetaImdb.BulkSettingsMode, bulk.capitalize())
		self.bulkSettingsSelectedSet() # Indicate that the user has picked an option, instead of the default option in settings.xml.

	@classmethod
	def bulkSettingsRefresh(self):
		return Settings.getInteger(MetaImdb.BulkSettingsRefresh)

	@classmethod
	def bulkSettingsNotification(self):
		return Settings.getInteger(MetaImdb.BulkSettingsNotification)

	@classmethod
	def bulkSettingsProgress(self):
		return Settings.getInteger(MetaImdb.BulkSettingsProgress)

	@classmethod
	def bulkSettingsAction(self):
		return Settings.getInteger(MetaImdb.BulkSettingsAction)

	@classmethod
	def bulkSettingsShow(self, settings = False):
		from lib.modules.window import WindowMetaBulk
		WindowMetaBulk.show(wait = True)
		if settings: Settings.launch(id = MetaImdb.BulkSettingsMode)

	@classmethod
	def bulkTimeout(self, bulk = None, generate = False, refresh = False):
		timeout = None
		if generate: timeout = MetaImdb.BulkTimeout[False]
		elif refresh is None: timeout = MetaImdb.BulkTimeout[None]
		else: timeout = MetaImdb.BulkTimeout[bulk or self.bulkSettingsMode()]
		return timeout

	@classmethod
	def bulkSizeDownload(self):
		return MetaImdb.BulkSizeDownload

	@classmethod
	def bulkSizeStorage(self):
		return MetaImdb.BulkSizeStorage

	@classmethod
	def bulkSizeMemory(self, bits = None):
		return MetaImdb.BulkSizeMemory.get(bits or Platform.architectureBits())

	@classmethod
	def bulkSizeMinimum(self, bits = None):
		return MetaImdb.BulkSizeMinimum.get(bits or Platform.architectureBits())

	@classmethod
	def bulkDuration(self):
		performance = Hardware.performanceRating()
		if performance >= 0.8: index = 0
		elif performance >= 0.5: index = 1
		elif performance >= 0.3: index = 2
		else: index = 3
		return MetaImdb.BulkDuration[index]

	@classmethod
	def bulkEnabled(self, force = False):
		return force or not self.bulkSettingsMode() == MetaImdb.BulkModeDisabled

	@classmethod
	def bulkEnabledDownload(self, refresh = True):
		return self.bulkUsageStorage(refresh = refresh) >= self.bulkSizeDownload()

	@classmethod
	def bulkEnabledStorage(self, refresh = True):
		return self.bulkUsageStorage(refresh = refresh) >= self.bulkSizeStorage()

	@classmethod
	def bulkEnabledMemory(self, refresh = True):
		return self.bulkUsageMemory(refresh = refresh) >= self.bulkSizeMemory()

	@classmethod
	def bulkEnabledMinimum(self, detail = True, memory = True, storage = True, refresh = True):
		from lib.meta.tools import MetaTools
		if not detail or not MetaTools.instance().settingsDetail() == MetaTools.DetailEssential:
			if not storage or self.bulkEnabledStorage(refresh = refresh):
				if memory:
					self.bulkUsageMemory(refresh = refresh)
					minimum = self.bulkSizeMinimum()
					return self.bulkUsageMemory(total = True) > minimum[0] and self.bulkUsageMemory() > minimum[1]
				else:
					return True
		return False

	@classmethod
	def bulkUsageMemory(self, total = False, percent = False, refresh = False):
		# This does not get the current readings: Hardware.memoryUsageTotalBytes(refresh = True)
		if refresh or MetaImdb.UsageMemory is None: MetaImdb.UsageMemory = Hardware.detectMemoryUsage()
		return MetaImdb.UsageMemory['total' if total else 'free']['percent' if percent else 'bytes']

	@classmethod
	def bulkUsageStorage(self, total = False, percent = False, refresh = False):
		# This does not get the current readings: Hardware.storageUsageTotalBytes(refresh = True)
		if refresh or MetaImdb.UsageStorage is None: MetaImdb.UsageStorage = Hardware.detectStorageUsage()
		return MetaImdb.UsageStorage['total' if total else 'free']['percent' if percent else 'bytes']

	# id: movie or show ID.
	# idEpisode: episode ID. Must also pass in a show ID.
	def bulk(self, id = None, idEpisode = None, imdb = None, imdbEpisode = None, season = None, episode = None, data = False, force = False, generate = False):
		try:
			if force or self.bulkEnabled():
				if id is None: id = imdb
				if idEpisode is None: idEpisode = imdbEpisode

				result = self._bulkCache(generate = generate).bulkSelect(idImdb = id)
				if result:
					if not season is None:
						result = result.get(str(season))
						if result:
							if episode is None:
								if not data:
									# Calculate the season rating from the average episode rating.
									# Only do this here instead of _bulkAssemble(), since most season ratings are never needed.
									# Plus S0 "Unknown" is stored as a list and the calculated rating cannot be added to the current structure.
									voting = self._bulkVoting(value = result)
									if voting:
										result = {'season' : season}
										result.update(voting)
										return result
									return None
							elif result:
								result = result.get(str(episode))
						return self._bulkValues(value = result, data = data, season = season, episode = episode)
					elif not idEpisode is None:
						# Create a ID lookup table for quick access.
						lookup = result.get(MetaImdb.BulkIdLookup)
						if lookup is None:
							lookup = {}
							for k1, v1 in result.items():
								if not k1 == MetaImdb.BulkIdShow:
									if Tools.isList(v1):
										for v2 in v1:
											lookup[v2[0]] = (v2, k1, None)
									elif Tools.isDictionary(v1):
										for k2, v2 in v1.items():
											lookup[v2[0]] = (v2, k1, k2)
							result[MetaImdb.BulkIdLookup] = lookup # Stores it in the orignal dict which is saved in the MetaCache memory.
						if lookup:
							# Sometimes an episode ID is requested that is not in the bulk.
							# Eg: tt4622118, which is a special on Trakt (S00E08), but is a separate show on IMDb.
							result = lookup.get(idEpisode)
							if result: return self._bulkValues(value = result[0], data = data, season = result[1], episode = result[2])
					else:
						return self._bulkValues(value = result, id = id, data = data)
		except: Logger.error()
		return None

	def _bulkValues(self, value, id = None, season = None, episode = None, data = False):
		if data:
			if value:
				result = {'id' : id, 'rating' : None, 'votes' : None}
				if Tools.isDictionary(value):
					voting = self._bulkValue(value = value)
					if voting:
						result['rating'] = voting.get('rating')
						result['votes'] = voting.get('votes')
					if MetaImdb.BulkIdShow in value or Tools.isDictionary(value.get(list(value.keys())[-1])): # Sometimes there is no BulkIdShow, because the show does not have a rating yet.
						result['seasons'] = {}
						for k, v in value.items():
							if not k == MetaImdb.BulkIdShow and not k == MetaImdb.BulkIdLookup:
								try: season = int(k)
								except:
									# "k" is not an int
									Logger.error(message = '%s => %s' % (str(k), str(v)))
									continue
								result['seasons'][season] = item = {'season' : season}
								voting = self._bulkVoting(value = v)
								if voting: item.update(voting)
								item['episodes'] = {int(k2) : self._bulkValue(value = v2, season = season, episode = int(k2)) for k2, v2 in v.items()}
					else:
						voting = self._bulkVoting(value = value)
						if voting: result.update(voting)
						result['episodes'] = {int(k) : self._bulkValue(value = v, season = season, episode = int(k)) for k, v in value.items() if not k == MetaImdb.BulkIdShow and not k == MetaImdb.BulkIdLookup}
				elif Tools.isArray(value) and Tools.isArray(value[0]):
					result['episodes'] = [self._bulkValue(value = i, season = season, episode = episode) for i in value]
				else:
					result = self._bulkValue(value = value, id = id, season = season, episode = episode)
				return result
		else:
			return self._bulkValue(value = value, id = id, season = season, episode = episode)
		return None

	def _bulkValue(self, value, id = None, season = None, episode = None):
		if value:
			force = False
			if Tools.isDictionary(value):
				value = value.get(MetaImdb.BulkIdShow)
				if not value:
					value = {}
					force = True

			if value or force:
				result = {'id' : id}
				if not season is None: result['season'] = season
				if not episode is None: result['episode'] = episode
				result['rating'] = None
				result['votes'] = None

				size = len(value)
				if size == 1:
					result['id'] = value[0]
				elif size == 2:
					result['rating'] = value[0]
					result['votes'] = value[1]
				elif size == 3:
					result['id'] = value[0]
					result['rating'] = value[1]
					result['votes'] = value[2]

				return result
		return None

	def _bulkVoting(self, value):
		if Tools.isDictionary(value): value = list(value.values())
		value = [self._bulkValue(value = i) for i in value]
		if value: return self.mMetatools.votingAverageWeighted(metadata = value, maximum = True, round = 6) # maximum: Do not return the total vote count.
		return None

	def _bulkCache(self, generate):
		return MetaCache.instance(generate = bool(generate))

	def _bulkSize(self, size):
		return ConverterSize(size).string(unit = ConverterSize.ByteGiga, places = 1)

	def _bulkNotification(self, silent, foreground, background, total, free):
		if silent is False or silent is None:
			settings = self.bulkSettingsNotification()
			if not settings == MetaImdb.BulkDialogDisabled:
				title = 36879
				format = (Format.fontBold(total), Format.fontBold(free))
				if settings == MetaImdb.BulkDialogForeground:
					Dialog.confirm(title = title, message = Translation.string(foreground) % format)
				elif settings == MetaImdb.BulkDialogBackground:
					message = [Translation.string(background), '%s: %s' % (Translation.string(35417), format[0]), '%s: %s' % (Translation.string(33334), format[1])]
					Dialog.notification(title = title, message = Format.iconJoin(message), time = 7000, icon = Dialog.IconError)
				return True
		return False

	def _bulkNotificationStorage(self, silent):
		total = self._bulkSize(self.bulkSizeStorage())
		free = self._bulkSize(self.bulkUsageStorage())
		Logger.log('BULK GENERATION: The device has insufficient free storage space to generate the IMDb bulkdata. [Required: %s | Available: %s]' % (total, free))
		return self._bulkNotification(silent = silent, foreground = 36892, background = 36890, total = total, free = free)

	def _bulkNotificationMemory(self, silent):
		total = self._bulkSize(self.bulkSizeMemory())
		free = self._bulkSize(self.bulkUsageMemory())
		Logger.log('BULK GENERATION: The device has insufficient free memory to generate the IMDb bulkdata. [Required: %s | Available: %s]' % (total, free))
		return self._bulkNotification(silent = silent, foreground = 36893, background = 36891, total = total, free = free)

	# refresh=True: Forcefully refresh the bulk data now, irrespective of how old it is.
	# refresh=False: Only refresh the bulk data if outdated, where the timeout is based on the user's hardware.
	# refresh=None: Refresh the bulk data if slightly outdated, where the timeout is fixed and not based on the user's hardware. This is a semi-forced refresh.
	def bulkRefresh(self, generate = False, force = False, refresh = False, reload = None, selection = None, silent = False, restart = None, wait = True):
		try:
			# Refresh the data on request, so that it can be accessed more quickly when needed later on without having to regenrate it first.
			if self.bulkEnabled(force = force):
				update = False

				if refresh is True:
					update = True
				else:
					if Tools.isInteger(refresh):
						timeout = refresh
					else:
						timeout = self.bulkTimeout(generate = generate, refresh = refresh)

						# Add a random value [0,24] hours to the timeout.
						# This ensures that users download the datasets at different times.
						# Otherwise if a major version is released that clears the cache, most users will download the dataset within the same day.
						# Adding a random value makes sure the refreshes deviate from each other over time.
						if not generate: timeout += Math.random(start = 0, end = 86400)

					# If the cache gets corrupted or cleared, this will redownload the bulkdata, even if it was done only a few hours/days ago.
					# The cache also sometimes gets corrupted during WizardVersion prelaoding. Not sure if it was caused by this. But maybe a good idea not to use the cache in any case.
					# Hence, do not do this with a cache timeout, but rather a setting.
					previous = self.bulkSettingsRefreshed()
					if not previous or (Time.timestamp() - previous) > timeout:
						update = True
					elif previous:
						return None # No refresh needed. Used in MetaManager.bulkImdbRefresh(). Also used in WindowMetaBulk.

				if update:
					if not silent:
						if selection is None: selection = self.bulkSettingsRefresh()
						if selection is True or selection == MetaImdb.BulkRefreshSelection:
							storage = Format.fontBold(ConverterSize(self.bulkSizeStorage()).stringOptimal())
							memory = Format.fontBold(ConverterSize(self.bulkSizeMemory()).stringOptimal())
							duration = '%s %s' % (Format.fontBold('-'.join([str(i) for i in self.bulkDuration()])), Translation.string(35620).lower())
							if reload:
								if not Dialog.options(title = 36879, message = Translation.string(36908) % (storage, memory, duration), labelConfirm = 32072, labelDeny = 35015, default = Dialog.ChoiceYes): return False
							else:
								if not Dialog.options(title = 36879, message = Translation.string(36898) % (storage, memory, duration)): return False

					if not self.bulkEnabledStorage():
						self._bulkNotificationStorage(silent = silent)
						return False
					elif not self.bulkEnabledMemory():
						self._bulkNotificationMemory(silent = silent)
						return False

					if wait: return self._bulkAssemble(generate = generate, silent = silent, restart = restart)
					else: Pool.thread(target = self._bulkAssemble, kwargs = {'generate' : generate, 'silent' : silent, 'restart' : restart}, start = True)
					return True
		except: Logger.error()
		return False

	@classmethod
	def bulkRefreshCancel(self):
		MetaImdb.BulkCanceled = True

	@classmethod
	def _bulkId(self, imdb):
		# Store the ID more efficiently to save memory.
		# More than 10 million IDs are stored in memory, plus most will be store a second time in a lookup table.
		# This requires a shit ton of memory, so every byte that can be saved helps.
		#	Padded integer:				32 bytes (64bit system)		20 bytes (32bit system)
		#	Unicode with tt prefix:		59 bytes (64bit system)		35 bytes (32bit system)
		#	Unicode without tt prefix:	57 bytes (64bit system)		33 bytes (32bit system)
		#	Ascii with tt prefix:		43 bytes (64bit system)		27 bytes (32bit system)
		#	Ascii without tt prefix:	41 bytes (64bit system)		25 bytes (32bit system)

		if not imdb or not imdb.startswith(MetaImdb.IdTitle): return None

		# It seems the shortest ID is 7 digits, including the left-padded 0s (eg: tt0000001).
		# The longest ID is 8 digits tt32857063, allow this will grow.
		# Make sure that the shortest generated int + 1 digit is always longer than the longest possible IMDb number.
		# If we assume a max IMDb length can grow to 10 (2 greater than the current IMDb IDs), then at least 4 padding-digits should be added to the front: (7 + 4) > 10.
		imdb = imdb.replace(MetaImdb.IdTitle, '')
		return int('99999' + imdb)

	@classmethod
	def _bulkIdPrepare(self, id):
		if not id: return id
		return MetaImdb.IdTitle + Tools.stringRemovePrefix(str(id), remove = MetaImdb.BulkIdPrefix)

	@classmethod
	def bulkPrepare(self, id, data):
		id = self._bulkIdPrepare(id = id)
		if Tools.isDictionary(data):
			for k1, v1 in data.items():
				if Tools.isDictionary(v1):
					for k2, v2 in v1.items():
						v2[0] = self._bulkIdPrepare(id = v2[0])
		return id, data

	def _bulkAssemble(self, generate = False, silent = False, restart = None):
		# The entire function (download + extraction + processing + writing to database) takes around 130-145 seconds on a high-end CPU and SSD, including all the Pool.check() in between.
		try:
			self.tUsage = [self.bulkUsageMemory(refresh = True)]

			MetaImdb.BulkCanceled = None # Use class variable, so it can be set bulkRefreshCancel() when the process is canceled during preloading.

			self.tSilent = silent
			self.tDialog = None
			self.tSettings = self.bulkSettingsProgress()
			self.tDuration = self.bulkDuration()
			self.tTitles = 0
			self.tItems = None
			self.tSize = 0
			self.tStatus = None
			self.tProgress = 0
			self.tPrevious = None
			self.tTimer = None

			# Still show a background dialog during preloading, otherwise the user might think preloading is stuck, because it takes so long.
			basic = silent is None
			if basic:
				self.tSilent = False
				self.tSettings = MetaImdb.BulkDialogBackground

			self.tTime = Time(start = True)
			show = MetaImdb.BulkIdShow

			self._bulkProgress(progress = 0, status = 'Preparing data collection')
			Pool.thread(target = self._bulkProgressor, start = True) # Smoother duration updates for foreground dialogs.

			items = self._bulkEpisode()
			if not self._bulkCheck(): return False
			self._bulkProgress(progress = 60)
			self.tUsage.append(self.bulkUsageMemory(refresh = True))

			if items and not Pool.aborted():
				ratings = self._bulkRating()
				if not self._bulkCheck(): return False
				self._bulkProgress(progress = 75)
				self.tUsage.append(self.bulkUsageMemory(refresh = True))

				if ratings and not Pool.aborted():
					self.tItems = items
					self._bulkProgress(status = 'Assembling episode data')
					count = 0
					increment = 10 * (1.0 / len(items))
					for id, v in items.items():
						# Sleep to allow more important code to execute, and abort if Kodi was exited.
						# About 230k items.
						count += 1
						if count > 10000:
							count = 0
							if not self._bulkCheck(delay = Pool.DelayQuick): return False # Prevent the function from getting executed again by the cache on failure.

						for k1, v1 in v.items():
							if Tools.isArray(v1):
								for v2 in v1:
									rating = ratings.get(v2[0])
									if not rating is None:
										del ratings[v2[0]] # Free up some memory.
										v2.extend(rating)

							elif Tools.isDictionary(v1):
								for k2, v2 in v1.items():
									rating = ratings.get(v2[0])
									if not rating is None:
										del ratings[v2[0]] # Free up some memory.
										v2.extend(rating)

						rating = ratings.get(id)
						if not rating is None:
							del ratings[id] # Free up some memory.
							if Tools.isDictionary(v): # Show ratings.
								value = []
								v[show] = value
								v = value
							v.extend(rating)

						self._bulkProgress(increment = increment)
					if not self._bulkCheck(): return False
					self._bulkProgress(progress = 85)
					self.tUsage.append(self.bulkUsageMemory(refresh = True))

					self._bulkProgress(status = 'Assembling rating data')
					count = 0
					increment = 5 * (1.0 / len(ratings))
					for id in list(ratings.keys()): # So that we can delete from the dict while looping.
						if id is None: continue # Already added in the previous loop.

						count += 1
						if count > 30000:
							count = 0
							if not self._bulkCheck(delay = Pool.DelayQuick): return False # Prevent the function from getting executed again by the cache on failure.

						items[id] = ratings[id]
						del ratings[id] # Free up some memory.

						self._bulkProgress(increment = increment)
					if not self._bulkCheck(): return False
					self._bulkProgress(progress = 90)
					self.tUsage.append(self.bulkUsageMemory(refresh = True))

				# Clear up some memory.
				ratings = None
				self.tItems = Tools.size(self.tItems) # Save the size for progress, and clear the dict to save some memory.
				self.tUsage.append(self.bulkUsageMemory(refresh = True))

				result = None
				if not self._bulkCheck(): return False
				self._bulkProgress(progress = 90)
				if items and not Pool.aborted() and self._bulkCheck():
					self._bulkProgress(status = 'Caching bulk data')
					result = self._bulkCache(generate = generate).bulkInsert(items = items, wait = True)

				self.bulkSettingsRefreshedSet()
				self._bulkProgress(progress = 100, final = True)
				self.tUsage.append(self.bulkUsageMemory(refresh = True))

				# Execute in a thread, so that this function can exit and the garbage collector can clean up, to detect how much memory could be freed up afterwards.
				if not MetaImdb.BulkCanceled:
					self.tElapsed = self.tTime.elapsed()
					def _usage():
						Time.sleep(15)
						titles = Math.thousand(self.tTitles)
						duration = ConverterDuration(self.tElapsed, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatClockMini)
						memory1 = ConverterSize(max([(self.tUsage[0] - i) for i in self.tUsage])).string(unit = ConverterSize.ByteMega, places = 0)
						memory2 = ConverterSize(self.tUsage[0] - self.bulkUsageMemory(refresh = True)).string(unit = ConverterSize.ByteMega, places = 0)
						Logger.log('BULK GENERATION: Bulkdata succefully refreshed. [Titles: %s | Duration: %s | Used Memory: %s | Lost Memory: %s]' % (titles, duration, memory1, memory2))
					Pool.thread(target = _usage, start = True)

				if not basic and not generate and not MetaImdb.BulkCanceled:
					reload = False
					self.bulkUsageMemory(refresh = True)
					try:
						usage = self.bulkUsageMemory()
						memory = (usage < 1395864371) or (usage < 2362232012 and self.bulkUsageMemory(percent = True) < 0.6) # Less than 1.3GB free or (less than 2.2GB free and less than 60% free).
					except: memory = False
					title = 36879
					summary = [
						Format.fontBold(36894),
						'%s %s' % (Format.fontBold(ConverterDuration(self.tTime.elapsed(), unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatClockMini)), Translation.string(35882)),
						'%s %s' % (Format.fontBold(ConverterSize(self.tSize).string(unit = ConverterSize.ByteMega, places = 0)), Translation.string(36839)),
						'%s %s' % (Format.fontBold(Math.thousand(self.tTitles)), Translation.string(33881)),
					]

					Dialog.closeAllProgress()
					if restart is False:
						summary = Format.newline().join([
							summary[0],
							'     %s' % Format.iconJoin([summary[1], summary[2], summary[3]]),
							Translation.string(36902),
						])
						Dialog.confirm(title = title, message = summary)
					else:
						action = self.bulkSettingsAction()
						if action == MetaImdb.BulkActionNotification:
							Dialog.notification(title = title, message = Format.iconJoin(summary), duplicates = True, icon = Dialog.IconSuccess)
						elif action == MetaImdb.BulkActionSelection:
							summary = Format.newline().join([
								summary[0],
								'     %s' % Format.iconJoin([summary[1], summary[2], summary[3]]),
								'%s %s' % (Translation.string(36901), Translation.string(36900)),
							])
							if Dialog.options(title = title, message = summary, labelConfirm = 32501, labelDeny = 35015, default = Dialog.ChoiceYes):
								reload = True
						elif action == MetaImdb.BulkActionRestart or (action == MetaImdb.BulkActionMemory and memory):
							reload = True

					# On some LibreELEC devices, a lot of the used memory is not returned. Not sure why.
					# This is not a memory leak, since the memory is correctly cleared up on a normal Linux device.
					# The device does not have to be rebooted. Restarting Kodi seems to work fine and is quicker. But this might be only supported on Windows and Linux.
					if reload:
						# Delay to allow any possible buffered writes to the database to finish.
						Time.sleep(1)
						System.power(action = System.PowerRestart, warning = True, notification = True, sound = True, delay = 10) # Restarts Kodi, not the device.

				return result
		except: Logger.error()

		# If download failed.
		try: self.tDialog.close()
		except: pass
		try: canceled = MetaImdb.BulkCanceled
		except: canceled = False
		self.tProgress = 100
		MetaImdb.BulkCanceled = True # Stop _bulkProgressor().
		if not canceled and not self.bulkSettingsProgress() == MetaImdb.BulkDialogDisabled: Dialog.confirm(title = 36879, message = 36906)

		return False # Prevent the function from getting executed again by the cache on failure.

	def _bulkCheck(self, delay = None):
		if MetaImdb.BulkCanceled: return False
		if self.tDialog and self.tDialog.iscanceled():
			if not MetaImdb.BulkCanceled:
				self.tDialog.close()
				choice = Dialog.option(title = 36879, message = 36895)
				if choice:
					MetaImdb.BulkCanceled = True
					self.tDialog.close()
					return False
				else:
					# Close and reopen the progress dialog.
					# Since if the dailog is canceled once, iscanceled() stays True.
					self.tDialog = None
					self._bulkProgress(force = True)
			else: return MetaImdb.BulkCanceled
		return Pool.check(delay = delay)

	def _bulkProgressor(self):
		if not self.tSilent and not self.tSettings == MetaImdb.BulkDialogDisabled:
			for i in range(1800): # If something went wrong and the loop is not broken out of, stop after 30 minutes.
				if Pool.aborted() or MetaImdb.BulkCanceled or self.tProgress == 100: break
				self._bulkProgress()
				Time.sleep(1)

	def _bulkProgress(self, increment = None, progress = None, status = None, title = False, final = False, force = False):
		try:
			if not self.tSilent and not MetaImdb.BulkCanceled and not self.tSettings == MetaImdb.BulkDialogDisabled:
				if increment: self.tProgress += increment
				elif progress: self.tProgress = progress
				if status: self.tStatus = status
				if title: self.tTitles += 1

				if self.tSettings == MetaImdb.BulkDialogForeground:
					padding = '     '
					message = '%s%s%s%s: %s' % (Format.fontBold(36852), Format.newline(), padding, Translation.string(33389), (self.tStatus or 'Busy'))
					if not self.tDialog: self.tDialog = Dialog.progress(title = 36879, message = message)
					base = 1 # Show every 1%.
				elif self.tSettings == MetaImdb.BulkDialogBackground:
					base = 5 if self.tDuration[0] >= 5 else 10 # Show every 5-10%, depending on how long the process takes on the device.

				stepProgress = Math.roundDownClosest(self.tProgress, base = base)
				if force or final or self.tPrevious is None or (stepProgress > self.tPrevious) or (self.tSettings == MetaImdb.BulkDialogForeground and (status or self.tTime.elapsed() > self.tTimer)):
					# There are a few ways in calculating the size:
					#	1. Tools.size(data): very fast, but returns the size in memory, which is considerably lower than the actual size of the JSON string stored.
					#	2. len(str(data)): closer to the actual JSON size, however takes very long to stringify and takes a total of 50+ secs for just a few calculations (every 10%).
					#	3. A combination of the previous 2. First calculate the size with Tools.size() and only if it changed, get the actual size with len(str()). Takes a total about 15-20 secs.
					#	4. Estimate the string size from using Tools.size(). The current ratios are: Episodes (30758320 bytes, 235892109 string) Ratings (61516544 bytes, 39298792 string).
					# Note that tDataEpisode can change from a full dict to an empty dict. So always use max() of the current and previous sizes, to avoid the size suddenly going down.
					size = self.tItems if Tools.isInteger(self.tItems) else Tools.size(self.tItems)
					self.tSize = max(self.tSize, size * 7.67) # Only use the episode dict, since it is later updated with the ratings.

					message = Translation.string(36894 if final else 36852)
					label = [
						Format.fontBold('%d%%' % stepProgress),
						Format.fontBold(ConverterDuration(self.tTime.elapsed(), unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatClockMini)),
						Regex.replace(data = ConverterSize(self.tSize).string(unit = ConverterSize.ByteMega, places = 0), expression = '(\d+(?:\.\d+)?)(.*)', replacement = r'[B]\1[/B]\2'),
						'%s %s' % (Format.fontBold(Math.thousand(self.tTitles)), Translation.string(33881)),
					]

					if self.tSettings == MetaImdb.BulkDialogForeground:
						message = [
							Format.fontBold(message),
							'%s%s: %s' % (padding, Translation.string(32037), Format.iconJoin([label[0], label[1]])),
							'%s%s: %s' % (padding, Translation.string(36839), Format.iconJoin([label[2], label[3]])),
							'%s%s: %s' % (padding, Translation.string(33389), (self.tStatus or 'Busy')),
						]
						message = Format.newline().join(message)
						self.tDialog.update(stepProgress, message)

					elif self.tSettings == MetaImdb.BulkDialogBackground:
						if self.tPrevious is None: # First notification.
							time = 8000
							icon = Dialog.IconWarning
							message += '.' + (Translation.string(36853) % Format.fontBold('-'.join([str(i) for i in self.tDuration])))
						else:
							if final:
								time = 8000
								icon = Dialog.IconSuccess
							else:
								time = 4000
								icon = Dialog.IconInformation
							message += ': %s' % Format.iconJoin(label)
						Dialog.notification(title = 36879, message = message, duplicates = True, icon = icon, time = time)

					self.tPrevious = Math.roundDownClosest(self.tProgress, base = base)
					self.tTimer = self.tTime.elapsed()
		except: Logger.error()

	def _bulkRetrieve(self, link, size, episode, progress = None):
		try:
			from lib.modules.tools import Hardware

			# Check if enough storage space is available.
			# These files are too big to retrieve them into memory using Networker.requestData().
			# Eg: The episode file is 50MB and takes 4 minutes to download into memory, but only 15 seconds to download to file.
			if self.bulkUsageStorage(refresh = True) > (size * 1.3) and not Pool.aborted():
				id = self.id()
				file = File.name(path = link, extension = False)
				directory = System.temporary(directory = id)
				path = System.temporary(directory = id, file = link)
				link = Networker.linkJoin(MetaImdb.LinkBulk, link)
				type = 'episode' if episode else 'rating'

				# Add a sleep interval check in between downloading chunks.
				# This allows other code to execute, instead of this code hogging all the resources during Kodi launch.
				# It also allows to abort the download if Kodi is exited.
				# Do not make this interval too large, since it is used between every chunk of 8192 bytes.
				# Eg: Episode data is 50MB, check is done every 1MB, so total extra time of 0.5 secs (check = Pool.DelayShort).
				self._bulkProgress(status = 'Downloading %s dataset' % type)
				Networker().request(link = link, path = path, check = Pool.DelayShort)

				if File.exists(path) and not Pool.aborted() and self._bulkCheck(delay = Pool.DelayShort):
					from lib.modules.compression import Archiver

					self._bulkProgress(status = 'Extracting %s dataset' % type, increment = progress[0] if progress else None)
					output = System.temporary(directory = File.joinPath(id, 'data'))
					Archiver.gzipDecompress(path = path, output = output)
					if not self._bulkCheck(delay = Pool.DelayShort): return None

					output = File.joinPath(output, file)
					if File.exists(output) and not Pool.aborted():
						self._bulkProgress(status = 'Processing %s dataset' % type, increment = progress[1] if progress else None)

						# This is too much work for low-end devices.
						# Reading the entire file into memory, and then using this inline loop to split the lines, makes low-end devices with less than 4GB RAM very slow, casuing Kodi to freeze or even crash.
						# This also increases memory consumption too much. The raw data (250MB + 30MB), plus the processed list data (75MB + 13MB). When reading chunked data from file, we only need (75MB + 13MB).
						# Split the workload into chunks and sleep in between.
						'''
							data = File.readNow(path = output)
							#items = Csv.decode(data = data, structured = False, header = True, delimiterColumn = '\t', convertInteger = True) # Takes too long to decode as a CSV (50-55 secs).
							items = [i.split('\t') for i in data.split('\n')] # Takes 10-15secs.
						'''

						def _convertEpisode(item):
							# Episode ID
							item[0] = self._bulkId(item[0])

							# Parent ID
							item[1] = self._bulkId(item[1])

							# Episodes listed under the "Unknown" season has numbers as "\N".
							# Season
							try: item[2] = int(item[2])
							except:
								try: item[2] = 0
								except: pass

							# Episode
							try: item[3] = int(item[3])
							except:
								try: item[3] = 0
								except: pass

						def _convertRating(item):
							# ID
							item[0] = self._bulkId(item[0])

							# Rating
							try: item[1] = float(item[1])
							except:
								try: item[1] = None
								except: pass

							# Votes
							try: item[2] = int(item[2])
							except:
								try: item[2] = None
								except: pass

						convert = _convertEpisode if episode else _convertRating

						import xbmcvfs
						file = xbmcvfs.File(output)

						# Use larger chunks to speed up the process.
						# Small chunk sizes (eg 1KB) take 150-200 secs to process the episode dataset.
						size = 262144 # 256KB (26 secs for the episode dataset on fast device and 80-90secs on slow device)

						data = ''
						items = []
						count = 0

						while True:
							count += 1
							if count > 10:
								count = 0
								if not self._bulkCheck(delay = Pool.DelayShort): break # Break to close the file below.

							bytes = file.read(size)
							if bytes:
								for i in bytes: data += i
							if data:
								split = data.split('\n')
								if split and len(split) > 1:
									for i in range(len(split) - 1):
										item = split[i].split('\t')
										convert(item) # Convert to int/float to save some memory, instead of storing the values as larger strings.
										items.append(item)
									data = split[-1]
							if not bytes: # End of file.
								if data: # Process the last line.
									split = data.split('\n')
									for i in split:
										item = i.split('\t')
										convert(item) # Convert to int/float to save some memory, instead of storing the values as larger strings.
										items.append(item)
								break
						file.close()

						File.deleteDirectory(path = directory)
						if not self._bulkCheck(): return None

						self._bulkProgress(increment = progress[2] if progress else None)
						return items

		except: Logger.error()
		return None

	def _bulkEpisode(self):
		try:
			# Download: 49.9MB
			# Extracted: 236.8MB
			# Stored in database as a single compressed object: 40MB.
			items = self._bulkRetrieve(link = MetaImdb.LinkBulkEpisode, size = 419430400, episode = True, progress = [5, 5, 15]) # 400MB.
			if items:
				self.tItems = result = {}
				episodes = {}
				count = 0
				increment = 25 * (1.0 / len(items))
				for i in range(len(items)):
					try:
						# Sleep to allow more important code to execute, and abort if Kodi was exited.
						# About 9 million items. Total sleep 1.8 seconds (limit = 50000, delay = 0.01).
						count += 1
						if count > 50000:
							count = 0
							if not self._bulkCheck(delay = Pool.DelayShort): return False

						# This can use up a lot of memory, since we create new dictionaries below.
						# Low-end devices might not have enough memory and Kodi freezes up.
						# As we iterate, set the original item to None to free up memory.
						item = items[i]
						items[i] = None

						# Header and last empty row.
						if not item or not item[0]: continue

						idParent = item[1]
						idEpisode = item[0]
						try: numberSeason = item[2]
						except: numberSeason = 0
						try: numberEpisode = item[3]
						except: numberEpisode = 0

						# Store as an list, since it is smaller and faster.
						entry1 = result.get(idParent)
						if entry1 is None: entry1 = result[idParent] = {}

						if numberSeason == 0:
							# Specials in the "Unknown" season do not have episode numbers.
							# This can be stored as a list.
							# Or: the IDs seem to be in order of release, so we can assume an episode number.
							# Update (2025-10): This is not always the case.
							# For Jimmy Fallon (tt3444938) there are a bunch of episodes under "Unknown", which are future episodes that were not assigned to a new season yet.
							# Many of those episodes are indeed ordered with sequential IMDb IDs. But there are also a number of episodes which do not fall within this order, where their ID is out of sequence.
							# The episode order in the bulk data is therefore not always the order in which the episodes appear on the website.
							# Hence, simply assuming that the IDs are sequential does not work.
							# But there is no quick fix for this. So leave the current (possible) incorrect IMDb episode numbering for S0. Some shows will simply have a few incorrect numbers in S0.

							#if not numberSeason in result[idParent]: result[idParent][numberSeason] = []
							#result[idParent][numberSeason].append([idEpisode])

							try: episodes[idParent] += 1
							except: episodes[idParent] = 1

							entry2 = entry1.get(numberSeason)
							if entry2 is None: entry1[numberSeason] = {episodes[idParent] : [idEpisode]}
							else: entry2[episodes[idParent]] = [idEpisode]
						else:
							entry2 = entry1.get(numberSeason)
							if entry2 is None: entry1[numberSeason] = {numberEpisode : [idEpisode]}
							else: entry2[numberEpisode] = [idEpisode]

						self._bulkProgress(increment = increment, title = True)
					except: Logger.error()

				episodes.clear() # Clear up some memory.

				# Sort by season and episode numbers.
				self._bulkProgress(status = 'Sorting episode dataset')
				count = 0
				increment = 5 * (1.0 / len(result))
				for k, v in result.items():
					count += 1
					if count > 200000:
						count = 0
						if not self._bulkCheck(delay = Pool.DelayQuick): return False

					# Slightly faster, but only 1-2 secs (from the total of 135 secs).
					#for k1, v2 in v.items():
					#	if Tools.isDictionary(v2): v[k1] = dict(sorted(v2.items()))
					#result[k] = dict(sorted(v.items()))
					for k1, v2 in v.items():
						if Tools.isDictionary(v2): v[k1] = {x : v2[x] for x in sorted(v2)}
					result[k] = {x : v[x] for x in sorted(v)}

					self._bulkProgress(increment = increment)

				# Cast the season/episode numbers to strings, since this will happen in any case if the data is JSON-encoded for the cache.
				# All lookups are done using strings.
				# Do this after the sorting above, since string sorting does not return the same order (eg: "1" vs "10").
				#result = {k1 : {str(k2) : {str(k3) : v3 for k3, v3 in v2.items()} if Tools.isDictionary(v2) else v2 for k2, v2 in v1.items()} for k1, v1 in result.items()}
				# Update: Do not do this anymore, since it requires extra processing and extra memory.
				# Since the keys are now stored as strings, they require almost twice the amount of memory as integers.
				# Plus the JSON-encoding will take care of converting the keys to strings.
				# If this is ever enabled again, make sure the increment percentages in this function add up to 60.
				'''
				self._bulkProgress(status = 'Converting episode dataset')
				self.tItems = temp = {}
				count = 0
				increment = 5 * (1.0 / len(result))
				for k1 in list(result.keys()): # So that we can delete from the dict while looping.
					count += 1
					if count > 200000:
						count = 0
						if not self._bulkCheck(delay = Pool.DelayQuick): return False

					temp[k1] = {str(k2) : {str(k3) : v3 for k3, v3 in v2.items()} if Tools.isDictionary(v2) else v2 for k2, v2 in result[k1].items()}

					# Free up memory, since we create a new dict above during every iteration.
					del result[k1]

					self._bulkProgress(increment = increment)
				result = temp'''

				return result
		except: Logger.error()
		return None

	def _bulkRating(self):
		try:
			# Download: 8.0MB
			# Extracted: 27.5MB
			# Stored in database as a single compressed object: 10MB.
			items = self._bulkRetrieve(link = MetaImdb.LinkBulkRating, size = 73400320, episode = False, progress = [4, 1, 5]) # 70MB.
			if items:
				self._bulkProgress(status = 'Populating rating dataset')
				result = {}
				count = 0
				increment = 5 * (1.0 / len(items))
				for i in range(len(items)):
					try:
						# Sleep to allow more important code to execute, and abort if Kodi was exited.
						# About 1.6 million items.
						count += 1
						if count > 100000:
							count = 0
							if not self._bulkCheck(delay = Pool.DelayQuick): return False

						# Free up memory during each iteration.
						item = items[i]
						items[i] = None

						try: rating = item[1]
						except: rating = None
						try: votes = item[2]
						except: votes = None
						if rating is None or votes is None: continue
						result[item[0]] = (rating, votes) # Store as an tuple, since it is smaller and faster than a dict, and also a bit smaller than a list.

						self._bulkProgress(increment = increment, title = True)
					except: Logger.error()
				return result
		except: Logger.error()
		return None
