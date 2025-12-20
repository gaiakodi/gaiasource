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

from lib.modules.tools import Tools, Time, Logger, Regex, Media, System
from lib.modules.account import Tvdb as Account
from lib.meta.provider import MetaProvider
from lib.meta.tools import MetaTools
from lib.meta.image import MetaImage
from lib.meta.data import MetaData
from lib.meta.core import MetaCore

class MetaTvdb(MetaProvider):

	Genres								= {
		MetaTools.GenreAction			: MetaData.GenreAction,
		MetaTools.GenreScifi			: MetaData.GenreScifi,
		MetaTools.GenreFantasy			: MetaData.GenreFantasy,
		MetaTools.GenreAdventure		: MetaData.GenreAdventure,
		MetaTools.GenreHorror			: MetaData.GenreHorror,
		MetaTools.GenreMystery			: MetaData.GenreMystery,
		MetaTools.GenreSuspense			: MetaData.GenreSuspense,
		MetaTools.GenreThriller			: MetaData.GenreThriller,
		MetaTools.GenreCrime			: MetaData.GenreCrime,
		MetaTools.GenreMartial			: MetaData.GenreMartial,
		MetaTools.GenreWestern			: MetaData.GenreWestern,
		MetaTools.GenreWar				: MetaData.GenreWar,
		MetaTools.GenrePolitics			: MetaData.GenrePolitics,
		MetaTools.GenreHistory			: MetaData.GenreHistory,
		MetaTools.GenreComedy			: MetaData.GenreComedy,
		MetaTools.GenreRomance			: MetaData.GenreRomance,
		MetaTools.GenreDrama			: MetaData.GenreDrama,

		MetaTools.GenreFamily			: MetaData.GenreFamily,
		MetaTools.GenreChildren			: MetaData.GenreChildren,
		MetaTools.GenreAnimation		: MetaData.GenreAnimation,
		MetaTools.GenreAnime			: MetaData.GenreAnime,
		MetaTools.GenreMusic			: MetaData.GenreMusic,
		MetaTools.GenreMusical			: MetaData.GenreMusical,

		MetaTools.GenreDocumentary		: MetaData.GenreDocumentary,
		MetaTools.GenreBiography		: MetaData.GenreBiography,
		MetaTools.GenreSport			: MetaData.GenreSport,
		MetaTools.GenreSporting			: MetaData.GenreSporting,
		MetaTools.GenreTravel			: MetaData.GenreTravel,
		MetaTools.GenreHoliday			: MetaData.GenreHoliday,
		MetaTools.GenreHome				: MetaData.GenreHome,
		MetaTools.GenreFood				: MetaData.GenreFood,

		MetaTools.GenreSoap				: MetaData.GenreSoap,
		MetaTools.GenreReality			: MetaData.GenreReality,
		MetaTools.GenreNews				: MetaData.GenreNews,
		MetaTools.GenreTalk				: MetaData.GenreTalk,
		MetaTools.GenreGame				: MetaData.GenreGame,
		MetaTools.GenreAward			: MetaData.GenreAward,
		MetaTools.GenreMini				: MetaData.GenreMini,
		MetaTools.GenrePodcast			: MetaData.GenrePodcast,
		MetaTools.GenreTelevision		: MetaData.GenreTelevision,

		MetaTools.GenreShort			: MetaData.GenreShort,
		MetaTools.GenreIndie			: MetaData.GenreIndie,
		MetaTools.GenreNoir				: MetaData.GenreNoir,
	}

	Status								= {
		MetaTools.StatusRumored			: MetaData.StatusRumored,
		MetaTools.StatusPlanned			: MetaData.StatusPlanned,
		MetaTools.StatusPreproduction	: MetaData.StatusPreproduction,
		MetaTools.StatusProduction		: MetaData.StatusProduction,
		MetaTools.StatusPostproduction	: MetaData.StatusPostproduction,
		MetaTools.StatusCompleted		: MetaData.StatusCompleted,
		MetaTools.StatusReleased		: MetaData.StatusReleased,
		MetaTools.StatusUpcoming		: MetaData.StatusUpcoming,
		MetaTools.StatusPiloted			: MetaData.StatusPiloted,
		MetaTools.StatusContinuing		: MetaData.StatusContinuing,
		MetaTools.StatusEnded			: MetaData.StatusEnded,
		MetaTools.StatusCanceled		: MetaData.StatusCanceled,
	}

	Types								= {
		(Media.Standard,)							: MetaData.SerieTypeStandard, # Add a comma to the tuple, otherwise it only retruns a string.
		(Media.Special, Media.Exclusive)			: MetaData.SerieTypeSpecial, # Keep Media.Special for clarity. Media.Exclusive will later be used for the niche in MetaTools.
		(Media.Premiere, Media.Outer)				: MetaData.SerieTypePremiereShow,
		(Media.Premiere, Media.Inner)				: MetaData.SerieTypePremiereSeason,
		(Media.Premiere, Media.Middle)				: MetaData.SerieTypePremiereMiddle,
		(Media.Premiere, Media.Finale, Media.Outer)	: MetaData.SerieTypePremiereFinale,
		(Media.Finale, Media.Outer)					: MetaData.SerieTypeFinaleShow,
		(Media.Finale, Media.Inner)					: MetaData.SerieTypeFinaleSeason,
		(Media.Finale, Media.Middle)				: MetaData.SerieTypeFinaleMiddle,
	}

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		MetaProvider.__init__(self, account = Account.instance())

	##############################################################################
	# METADATA
	##############################################################################

	def metadataShow(self, imdb = None, tvdb = None, language = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if tvdb or imdb:
				manager = MetaCore(provider = MetaCore.ProviderTvdb, threaded = MetaCore.ThreadedDynamic if threaded is False else threaded)
				data = manager.show(idTvdb = tvdb, idImdb = imdb, level = MetaCore.Level3, cache = cache if cache else False)

				if data and data.idTvdb():
					result = {}

					result['id'] = {}
					id = data.idImdb()
					if id: result['id']['imdb'] = id
					id = data.idTmdb()
					if id: result['id']['tmdb'] = id
					id = data.idTvdb()
					if id: result['id']['tvdb'] = id

					title = data.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					if title:
						result['title'] = title
						result['tvshowtitle'] = title

					title = data.titleOriginal(selection = MetaData.SelectionSingle)
					if title:
						result['originaltitle'] = title
						if not 'title' in result: result['title'] = title
						if not 'tvshowtitle' in result: result['tvshowtitle'] = title

					plot = data.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					if plot: result['plot'] = plot

					year = data.year()
					if year: result['year'] = year

					premiered = data.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
					if premiered:
						premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
						if premiered:
							result['premiered'] = premiered
							result['aired'] = premiered

					time = data.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
					if not time and premiered: time = Time.timestamp(premiered, format = Time.FormatDate, utc = True)
					if time: result['time'] = {MetaTools.TimePremiere : time}

					airs = {}
					airTime = data.releaseTime(zone = MetaData.ZoneOriginal)
					if airTime: airs['time'] = airTime
					airDay = data.releaseDay()
					if airDay: airs['day'] = [i.title() for i in airDay]
					airZone = data.releaseZoneName()
					if airZone: airs['zone'] = airZone
					if airs: result['airs'] = airs

					genre = data.genre()
					if genre: result['genre'] = self._convertGenre(genre = genre, inverse = True)

					mpaa = data.certificateCode(country = MetaData.CountryUnitedStates, selection = MetaData.SelectionSingle)
					if not mpaa: mpaa = data.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
					if mpaa: result['mpaa'] = self._convertCertificate(certificate = mpaa, inverse = True)

					# TVDb does not have ratings/votes anymore.
					# Check tvdb.py -> _processVote() for more info.
					'''rating = data.voteRating()
					if not rating is None: result['rating'] = rating

					votes = data.voteCount()
					if not votes is None: result['votes'] = votes'''

					duration = data.durationSeconds()
					if not duration is None: result['duration'] = duration

					status = data.status()
					if status: result['status'] = self._convertStatus(status = status, inverse = True)

					country = data.releaseCountry()
					if country: result['country'] = [country]

					language = data.languageOriginal()
					if language: result['language'] = language if Tools.isArray(language) else [language]

					studio = data.companyNameStudio()
					if studio: result['studio'] = studio

					network = data.companyNameNetwork()
					if network: result['network'] = network

					cast = data.personKodiCast()
					if cast: result['cast'] = cast

					director = data.personKodiDirector()
					if director: result['director'] = director

					writer = data.personKodiWriter()
					if writer: result['writer'] = writer

					image = {
						MetaImage.TypePoster : data.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
						MetaImage.TypeThumb : data.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
						MetaImage.TypeFanart : data.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackNone, sort = MetaData.SortSettings, extract = False), # Do not use a fallback.
						MetaImage.TypeLandscape : data.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
						MetaImage.TypeBanner : data.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
						MetaImage.TypeClearlogo : data.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
						MetaImage.TypeClearart : data.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
						MetaImage.TypeDiscart : data.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
						MetaImage.TypeKeyart : data.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackNone, sort = MetaData.SortSettings, extract = False), # Do not use a fallback.
					}
					image = self._imageCreate(image = image)
					if image: result[MetaImage.Attribute] = image
				else: complete = False
		except: Logger.error()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	def metadataSeason(self, imdb = None, tvdb = None, language = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if tvdb or imdb:
				manager = MetaCore(provider = MetaCore.ProviderTvdb, threaded = MetaCore.ThreadedDynamic if threaded is False else threaded)
				show = manager.show(idTvdb = tvdb, idImdb = imdb, level = MetaCore.Level5, cache = cache if cache else False)
				if show and show.idTvdb():
					result = []
					current = Time.timestamp()

					showId = show.id()
					showTitle = show.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					showPlot = show.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					showYear = show.year()
					showPremiered = show.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
					showTime = show.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
					showAirTime = show.releaseTime(zone = MetaData.ZoneOriginal)
					showAirDay = show.releaseDay()
					showAirZone = show.releaseZoneName()
					showGenre = show.genre()
					showMpaa = show.certificateCode(country = MetaData.CountryUnitedStates, selection = MetaData.SelectionSingle) or show.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
					showDuration = show.durationSeconds()
					showStatus = show.status()
					showCountry = show.releaseCountry()
					showLanguage = show.languageOriginal()
					showStudio = show.companyNameStudio()
					showNetwork = show.companyNameNetwork()
					showCast = show.personKodiCast()
					showDirector = show.personKodiDirector()
					showWriter = show.personKodiWriter()

					seasons = show.season(sort = True)
					episodes = show.episode(sort = True)

					seasonLast = None
					seasonRelease = []
					for season in seasons:
						if season:
							number = season.numberSeason()
							if not number is None:
								if seasonLast is None or number > seasonLast: seasonLast = number
								release = {'season' : number, 'time' : None, 'type' : None}
								episodeLast = season.episode(sort = True)
								if episodeLast:
									episodeLast = episodeLast[-1]
									if episodeLast:
										release['time'] = episodeLast.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
										release['type'] = episodeLast.type()
								seasonRelease.append(release)
					seasonRelease = Tools.listSort(seasonRelease, key = lambda x : x['season'])
					seasonReleased = None
					for season in reversed(seasonRelease):
						# If the last episode is a mid-season-finale, assume it has not ended.
						# Eg: One Piece S22E1122 (Trakt) is a mid-season-finale, before S22E1123 continues 6 months later.
						# At the same time, the One Piece S21 ends with a mid-season-finale on Trakt, so it does not always mean the season will continue later on.
						if season['time'] and season['time'] < current and not season['type'] == MetaData.SerieTypeFinaleMiddle:
							# NB: Do not assume the season has finished if the last episode has aired, since the season might be continuing and new episodes are added on a daily/weekly basis.
							if showStatus in (MetaData.StatusEnded, MetaData.StatusCanceled) or season['type'] in (MetaData.SerieTypeFinaleShow, MetaData.SerieTypeFinaleSeason) or season['season'] < seasonRelease[-1]['season']:
								seasonReleased = season['season']
								break

					images = {}
					for season in seasons:
						try:
							resultSeason = {}
							resultSeason['id'] = Tools.copy(showId) # Copy, since we edit it for each season by adding the season IDs.

							numberSeason = season.numberSeason()
							resultSeason['season'] = numberSeason

							episodesSeason = season.episode(sort = True)
							try: episodeFirst = episodesSeason[0]
							except: episodeFirst = None
							try: episodeLast = episodesSeason[-1]
							except: episodeLast = None
							if numberSeason == 0:
								# For S0 the episodes numbers might not be correctly ordered according to date.
								# Eg: The Last of Us: S00E01 (2023-01-15) vs S00E33 (2023-01-05)
								episodesMinimum = [None, None]
								episodesMaximum = [None, None]
								if episodesSeason:
									for episode in episodesSeason:
										episodeTime = episode.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatTimestamp)
										if episodeTime:
											if not episodesMinimum[0] or episodeTime < episodesMinimum[0]: episodesMinimum = [episodeTime, episode]
											if not episodesMaximum[0] or episodeTime > episodesMaximum[0]: episodesMaximum = [episodeTime, episode]
								if episodesMinimum[1]: episodeFirst = episodesMinimum[1]
								if episodesMaximum[1]: episodeLast = episodesMaximum[1]

							if showTitle: resultSeason['tvshowtitle'] = showTitle

							title = season.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
							if title: resultSeason['title'] = title

							title = season.titleOriginal(selection = MetaData.SelectionSingle)
							if title:
								resultSeason['originaltitle'] = title
								if not 'title' in resultSeason: resultSeason['title'] = title

							plot = season.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
							if not plot: plot = showPlot
							if plot: resultSeason['plot'] = plot

							# Always use the show's year, used for search by title-and-year and for adding multiple seasons under the same tvshowtitle-and-year folder in the local library.
							if showYear: resultSeason['year'] = showYear

							premiered = season.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
							if not premiered:
								if episodeFirst: premiered = episodeFirst.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
								if not premiered and resultSeason['season'] <= 1: premiered = showPremiered # Do not do this for later seasons, since they might be new/unaired seasons and we do not want to use the years-earlier show premier date.
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									resultSeason['premiered'] = premiered
									resultSeason['aired'] = premiered

							time = season.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
							if not time and resultSeason['season'] <= 1: time = showTime
							if not time and premiered: time = Time.timestamp(premiered, format = Time.FormatDate, utc = True)
							if time: resultSeason['time'] = {MetaTools.TimePremiere : time}

							if episodeLast:
								ended = episodeLast.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp)
								if ended:
									if not 'time' in resultSeason: resultSeason['time'] = {}
									resultSeason['time'][MetaTools.TimeEnded] = ended

							airs = {}
							airTime = season.releaseTime(zone = MetaData.ZoneOriginal)
							if not airTime:
								if episodeFirst: airTime = episodeFirst.releaseTime(zone = MetaData.ZoneOriginal)
								if not airTime: airTime = showAirTime
							if airTime: airs['time'] = airTime
							airDay = season.releaseDay()
							if not airDay:
								if episodeFirst: airDay = episodeFirst.releaseDay()
								if not airDay: airDay = showAirDay
							if airDay: airs['day'] = [i.title() for i in airDay]
							airZone = season.releaseZoneName()
							if not airZone:
								if episodeFirst: airZone = episodeFirst.releaseZoneName()
								if not airZone: airZone = showAirZone
							if airZone: airs['zone'] = airZone
							if airs: resultSeason['airs'] = airs

							genre = season.genre()
							if not genre:
								genre = showGenre
								if not genre and episodeFirst: genre = episodeFirst.genre()
							if genre: resultSeason['genre'] = MetaTvdb._convertGenre(genre = genre, inverse = True)

							mpaa = season.certificateCode(country = MetaData.CountryUnitedStates, selection = MetaData.SelectionSingle)
							if not mpaa:
								mpaa = season.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
								if not mpaa:
									mpaa = showMpaa
									if not mpaa and episodeFirst:
										mpaa = episodeFirst.certificateCode(country = MetaData.CountryUnitedStates, selection = MetaData.SelectionSingle)
										if not mpaa: mpaa = episodeFirst.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
							if mpaa: resultSeason['mpaa'] = MetaTvdb._convertCertificate(certificate = mpaa, inverse = True)

							duration = season.durationSeconds()
							if duration is None:
								if episodeFirst: duration = episodeFirst.durationSeconds()
								if duration is None: duration = showDuration
							if not duration is None: resultSeason['duration'] = duration

							# If the episode is available, but does not have an airing date yet, set the value to False.
							# The "False" value is specifically checked in MetaTools.mergeStatus() to not mark the season as "ended" if there are still some unaired episodes without a date.
							timeFirst = (episodeFirst.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) or False) if episodeFirst else None # Return the timestamp in UTC, not the original timezone.
							timeLast = (episodeLast.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) or False) if episodeLast else None # Return the timestamp in UTC, not the original timezone.

							type = season.type()
							if type: type = self._convertType(type = type, inverse = True, list = True)

							status = season.status()
							if status:
								status = MetaTvdb._convertStatus(status = status, inverse = True)
							else:
								# timeFirst/timeLast
								#	Only mark the last season as "ended" if the final episode is the series finale AND the final episode's release date is in the past.
								#	Otherwise if the final season of a show is released, but the episodes have not aired yet, it will be marked as "ended", but that should only be the case if the last episodes has aired already.
								status = self.mMetatools.mergeStatus(media = Media.Season, season = numberSeason, seasonReleased = seasonReleased, time = time, timeFirst = timeFirst, timeLast = timeLast, type = type, status = MetaTvdb._convertStatus(status = showStatus, inverse = True), statusLast = MetaTvdb._convertStatus(status = episodeLast.status(), inverse = True) if episodeLast else None)
							if status: resultSeason['status'] = status

							if type:
								type = self.mMetatools.mergeType(values = type, season = numberSeason, seasonLastStandard = seasonLast, seasonLastRelease = seasonRelease[-1]['season'] if seasonRelease else None, timeLast = timeLast, statusShow = showStatus, fix = True)
								if type: resultSeason['type'] = type

							country = season.releaseCountry()
							if not country:
								country = showCountry
								if not country and episodeFirst: country = episodeFirst.releaseCountry()
							if country: resultSeason['country'] = [country]

							language = season.languageOriginal()
							if not language:
								language = showLanguage
								if not language and episodeFirst: language = episodeFirst.languageOriginal()
							if language: resultSeason['language'] = language if Tools.isArray(language) else [language]

							studio = season.companyNameStudio()
							if not studio:
								studio = showStudio
								if not studio and episodeFirst: studio = episodeFirst.companyNameStudio()
							if studio: resultSeason['studio'] = studio

							network = season.companyNameNetwork()
							if not network:
								network = showNetwork
								if not network and episodeFirst: network = episodeFirst.companyNameNetwork()
							if network: resultSeason['network'] = network

							cast = season.personKodiCast()
							if not cast:
								# NB: Do not use the show cast, since they can be very different from the current season's cast.
								# Eg: White Lotus S03.
								# If no/few cast is available, it will in any case be aggregated from the show/season cast in MetaManager.
								#cast = showCast
								if not cast and episodeFirst: cast = episodeFirst.personKodiCast()
							if cast: resultSeason['cast'] = cast

							director = season.personKodiDirector()
							if not director:
								# NB: Do not use the show director, since many shows have different directors for each season.
								# If no director is available, it will in any case be aggregated from the show director in MetaManager.
								#director = showDirector
								if not director and episodeFirst: director = episodeFirst.personKodiDirector()
							if director: resultSeason['director'] = director

							writer = season.personKodiWriter()
							if not writer:
								# NB: Do not use the show writer, since many shows have different writers for each season.
								# If no writer is available, it will in any case be aggregated from the show writer in MetaManager.
								#writer = showWriter
								if not writer and episodeFirst: writer = episodeFirst.personKodiWriter()
							if writer: resultSeason['writer'] = writer

							# Do not use a fallback for fanart and keyart, which should not contain any decor/text.
							# Otherwise the landscape might be set as the fanart if not fanart is available, which makes menus look ugly.
							# Eg: TBBT season fanart.
							# Let the correct fanart/landscape be later aggregated in MetaManager/MetaImage.
							image = {
								MetaImage.TypePoster : season.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
								MetaImage.TypeThumb : season.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
								MetaImage.TypeFanart : season.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackNone, sort = MetaData.SortSettings, extract = False), # Do not use a fallback.
								MetaImage.TypeLandscape : season.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
								MetaImage.TypeBanner : season.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
								MetaImage.TypeClearlogo : season.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
								MetaImage.TypeClearart : season.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
								MetaImage.TypeDiscart : season.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
								MetaImage.TypeKeyart : season.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackNone, sort = MetaData.SortSettings, extract = False), # Do not use a fallback.
							}
							for k, v in image.items(): image[k] = [{'link' : i.get('link'), 'language' : i.get('language'), 'quality' : (i.get('resolution') or {}).get('quality'), 'sort' : {k2 : v2[1] for k2, v2 in i.get('sort').items()}} for i in v] if v else []
							images[numberSeason] = image

							result.append(resultSeason)
						except: Logger.error()

					# Try to group season images (eg posters) by common theme.
					images = self._imageSeason(images = images)
					for season in result:
						image = images.get(season['season'])
						if image:
							image = self._imageCreate(image = image)
							if image: season[MetaImage.Attribute] = image
		except: Logger.error()

		if not result: result = None
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	def metadataEpisode(self, imdb = None, tvdb = None, season = None, language = None, pack = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if tvdb or imdb:
				manager = MetaCore(provider = MetaCore.ProviderTvdb, threaded = MetaCore.ThreadedDynamic if threaded is False else threaded)

				# numberAdjust=False: Do not adjust the season number if the show uses the year as season.
				# Eg: https://thetvdb.com/series/82495-show
				show = manager.show(idTvdb = tvdb, idImdb = imdb, level = MetaCore.Level6, numberSeason = season, cache = cache if cache else False, numberAdjust = False)

				if show and show.idTvdb():
					# Previously "Dragon Ball Super" had perfectly matching episodes (131 episodes) between TVDb and Trakt/TMDb, except that TVDb had them split over multiple seasons.
					# Then a recent update (2025-05) suddenly added specials as additional standard episodes to some seasons, after the season finale.
					#	S00E04 (DVD Order) -> S01E15 (New Aired Order)
					#	S00E05 (DVD Order) -> S02E14 (New Aired Order)
					#	S00E01 (DVD Order) -> S05E56 (New Aired Order)
					# Not sure why this was done. Maybe it was an ignorant TVDb end-user that decided to add these episodes because he does not understand that specials should be kept in S0 and then use the before/after numbers to determine where the special should be interleaved.
					# Or maybe this was done by a TVDb admin/mod who added the specials that only appeared in the "DVD Order" to the "Aired Order" seasons. Technically these "DVD Order" specials should just be added under the "Aired Order" specials S0 as well.
					# What makes this even worse is that these new episodes are returned with (used by MetaPack):
					#	https://api4.thetvdb.com/v4/series/295068/extended?meta=episodes
					# but they are not included with (used by this function):
					#	https://api4.thetvdb.com/v4/seasons/644129/extended
					# Maybe this is a caching issue and those episodes will appear in the season metadata in a few days once the cache has been updated.
					# Or maybe this is a more permanent problem and the season metadata will never contain those new episodes.
					# Update: This is most likley a caching issue.
					# This does not return the new episode S05E56:
					#	https://api4.thetvdb.com/v4/seasons/688948/extended
					# but this one does:
					#	https://api4.thetvdb.com/v4/seasons/688948/extended?meta=translations
					# but for S02, even when adding the extra peramater, S02E14 is not returned.
					# So this looks like a caching issue and might get updated soon.
					# This now creates various issues, including in MetaManager.metadataEpisodeNext().
					# The pack states that there is an episode S02E14, but the episode metadata only contains up to S02E13.
					# metadataEpisodeNext() will therefore not work with S02E13, since it will use the pack to determine the next episode (S02E14), but when retrieving the detailed metadata of that episode, it will not find it.
					# So the solution is to use the TVDb IDs from the pack, and if they are not returned by MetaCore().show(...) call above, make additional requests to retrieve the individual episodes below.
					# This is not perfect, since there is also a special in Dragon Ball Super S01E15, which will be ignored, since Trakt/TMDb have a single season and they will just continue with the abolsute order after S01E14.
					missing = {}
					if pack:
						from lib.meta.pack import MetaPack
						episodes = pack.episode(season = season)
						if episodes:
							for episode in episodes:
								if pack.numberSeason(item = episode, provider = MetaPack.ProviderTvdb) == season: # Check the season, since Dragon Ball Super S01 contains all episodes from all seasons (since Trakt only has one season).
									try: missing[pack.id(item = episode, provider = MetaPack.ProviderTvdb)] = True
									except: pass

					seasons = show.season(sort = True)

					# This does not work if we only retrieve a single season.
					# Retrieving all seasons (and their episodes) takes unnecessarily long with MetaCore.Level6, since requests are not cached and each season/episode needs its own API call.
					# Instead retrieve the pack data from the MetaCache from the previous seasons.py in _metadataEpisodeUpdate().

					if seasons:
						showId = show.id()
						showTitle = show.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
						showPlot = show.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
						showYear = show.year()
						showPremiered = show.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
						showAirTime = show.releaseTime(zone = MetaData.ZoneOriginal)
						showAirDay = show.releaseDay()
						showAirZone = show.releaseZoneName()
						showGenre = show.genre()
						showMpaa = show.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
						showDuration = show.durationSeconds()
						showStatus = show.status()
						showCountry = show.releaseCountry()
						showLanguage = show.languageOriginal()
						showStudio = show.companyNameStudio()
						showNetwork = show.companyNameNetwork()
						showCast = show.personKodiCast()
						showDirector = show.personKodiDirector()
						showWriter = show.personKodiWriter()

						result = []
						if not Tools.isArray(seasons): seasons = [seasons]

						for season in seasons:
							seasonId = None
							seasonPlot = None
							seasonYear = None
							seasonPremiered = None
							seasonTime = None
							seasonAirTime = None
							seasonAirDay = None
							seasonAirZone = None
							seasonGenre = None
							seasonMpaa = None
							seasonDuration = None
							seasonStatus = None
							seasonCountry = None
							seasonLanguage = None
							seasonStudio = None
							seasonNetwork = None
							seasonCast = None
							seasonDirector = None
							seasonWriter = None
							seasonImage = None

							try:
								seasonId = season.id()

								seasonPlot = season.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
								if not seasonPlot: seasonPlot = showPlot

								previousPremiered = None
								seasonTime = season.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
								seasonPremiered = season.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
								if not seasonPremiered and season.numberSeason() == 1: seasonPremiered = showPremiered # Do not do this for later seasons. Otherwise new unaired season/episodes without a release date yet, will get the 1st season's date.
								if seasonPremiered: seasonPremiered = Regex.extract(data = seasonPremiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)

								seasonAirs = {}
								seasonAirTime = season.releaseTime(zone = MetaData.ZoneOriginal)
								if not seasonAirTime: seasonAirTime = showAirTime
								seasonAirDay = season.releaseDay()
								if not seasonAirDay: seasonAirDay = showAirDay
								seasonAirZone = season.releaseZoneName()
								if not seasonAirZone: seasonAirZone = showAirZone

								seasonGenre = season.genre()
								if not seasonGenre: seasonGenre = showGenre

								seasonMpaa = season.certificateCode(country = MetaData.CountryUnitedStates, selection = MetaData.SelectionSingle) or season.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
								if not seasonMpaa: seasonMpaa = showMpaa

								seasonDuration = season.durationSeconds()
								if seasonDuration is None: seasonDuration = showDuration

								seasonStatus = season.status()
								if not seasonStatus: seasonStatus = showStatus

								seasonCountry = season.releaseCountry()
								if not seasonCountry: seasonCountry = showCountry

								seasonLanguage = season.languageOriginal()
								if not seasonLanguage: seasonLanguage = showLanguage

								seasonStudio = season.companyNameStudio()
								if not seasonStudio: seasonStudio = showStudio

								seasonNetwork = season.companyNameNetwork()
								if not seasonNetwork: seasonNetwork = showNetwork

								seasonCast = season.personKodiCast()
								if not seasonCast: seasonCast = showCast

								seasonDirector = season.personKodiDirector()
								if not seasonDirector: seasonDirector = showDirector

								seasonWriter = season.personKodiWriter()
								if not seasonWriter: seasonWriter = showWriter
							except: Logger.error()

							episodes = season.episode(sort = True)
							if episodes: # Some Special or not-yet-released seasons do not have episodes.
								# Check above on why this is done.
								if missing:
									for id in missing.keys():
										for episode in episodes:
											if episode and episode.id(provider = MetaData.ProviderTvdb) == id:
												missing[id] = False
												break
									missing = [k for k, v in missing.items() if v]
									if missing and len(missing) <= 3: # Only do this if there are 3 or less episodes missing. Otherwise something might be wrong and we do not want to make too many extra requests.
										for id in missing:
											episode = manager.episode(idTvdb = id, level = MetaCore.Level6, cache = cache if cache else False)
											if episode: episodes.append(episode)
										if System.developerVersion(): Logger.log('METATVDB: FOUND MISSING TVDB EPISODES [%s - %s - S%02d]: %s' % (imdb, tvdb, season.numberSeason(), ' | '.join(missing)))

								episodeLast = episodes[-1]
								for episode in episodes:
									if episode: # Sometimes TVDb fails to retrieve the episode, and then the episode is None.
										try:
											resultEpisode = {}

											resultEpisode['id'] = Tools.copy(showId) # Copy, since we edit it for each episode by adding the season/episode IDs.
											if seasonId: resultEpisode['id']['season'] = seasonId
											id = episode.id()
											if id: resultEpisode['id']['episode'] = id

											resultEpisode['season'] = numberSeason = episode.numberSeason()
											resultEpisode['episode'] = numberEpisode = episode.numberEpisode()

											# Sometimes TVDb has episodes that should not be there.
											# Eg: LEGO Masters (US) S01E11 - S01E16 (which do not have a title/date/thumbnail/duration and are also not on Trakt/TMDb).
											# When requesting the episode's detailed metadata, it has a season/episode number:
											#	https://api4.thetvdb.com/v4/episodes/11102362/extended (TVDb S01E11)
											# However, when also retrieving the translations, suddenly there are not season/episode numbers anymore:
											#	https://api4.thetvdb.com/v4/episodes/11102362/extended?meta=translations
											# This might be due to caching. This has previously been observed elsewhere, that TVDb sometimes returns different metadata when making a request with and without "meta=translations".
											# Or different metadata is returned, because those episodes should not have been there in the first place?
											# If there is not season/episode numbers, do not return the episode.
											if numberSeason is None or numberEpisode is None: continue

											# This does not work currently. A separate request has to be made to retrieve the "Absolute Order" season to get the absolute number.
											# Update: there is now a "absoluteNumber" attribute added to episodes which does not require separate requests.
											resultEpisode['absolute'] = episode.numberEpisode(number = MetaData.NumberAbsolute)

											if showTitle: resultEpisode['tvshowtitle'] = showTitle

											title = episode.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
											if title: resultEpisode['title'] = title

											title = episode.titleOriginal(selection = MetaData.SelectionSingle)
											if title:
												resultEpisode['originaltitle'] = title
												if not 'title' in resultEpisode: resultEpisode['title'] = title

											plot = episode.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
											if not plot: plot = seasonPlot
											if plot: resultEpisode['plot'] = plot

											# Always use the show's year, used for search by title-and-year and for adding multiple seasons under the same tvshowtitle-and-year folder in the local library.
											if showYear: resultEpisode['year'] = showYear

											premiered = episode.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
											# NB: Only use the season premiere as the episode dates if none of the previous episodes have dates (previousPremiered).
											# Otherwise if a new season is released, only the first few episodes might have an airing date yet, but not the rest.
											# Do not use the season premiere date for those episodes without a date, since it is often wrong, especially for weekly/batchly released episodes.
											# Aka the season premiere date might be EARLIER than the airing date of some later episodes.
											if not premiered and not previousPremiered: premiered = seasonPremiered
											if premiered:
												premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
												if premiered:
													resultEpisode['premiered'] = premiered
													resultEpisode['aired'] = premiered
											if numberEpisode > 0 and not previousPremiered: previousPremiered = premiered

											time = episode.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
											if not time: time = seasonTime
											if not time and premiered: time = Time.timestamp(premiered, format = Time.FormatDate, utc = True)
											if time: resultEpisode['time'] = {MetaTools.TimePremiere : time}

											airs = {}
											airTime = episode.releaseTime(zone = MetaData.ZoneOriginal)
											if not airTime: airTime = seasonAirTime
											if airTime: airs['time'] = airTime
											airDay = episode.releaseDay()
											if not airDay: airDay = seasonAirDay
											if airDay: airs['day'] = [i.title() for i in airDay]
											airZone = episode.releaseZoneName()
											if not airZone: airZone = seasonAirZone
											if airZone: airs['zone'] = airZone
											if airs: resultEpisode['airs'] = airs

											genre = episode.genre()
											if not genre: genre = seasonGenre
											if genre: resultEpisode['genre'] = MetaTvdb._convertGenre(genre = genre, inverse = True)

											mpaa = episode.certificateCode(country = MetaData.CountryUnitedStates, selection = MetaData.SelectionSingle)
											if not mpaa:
												mpaa = episode.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
												if not mpaa: mpaa = seasonMpaa
											if mpaa: resultEpisode['mpaa'] = MetaTvdb._convertCertificate(certificate = mpaa, inverse = True)

											duration = episode.durationSeconds()
											if not duration is None: resultEpisode['duration'] = duration

											status = episode.status()
											if status: status = MetaTvdb._convertStatus(status = status, inverse = True)
											else: status = self.mMetatools.mergeStatus(media = Media.Episode, season = numberSeason, episode = numberEpisode, time = time)
											if status: resultEpisode['status'] = status

											type = episode.type()
											if type:
												type = self._convertType(type = type, inverse = True, list = True)
												if type:
													# Sometimes middle finales are listed as season finales.
													# Eg: Vikings S06E10
													# Do not do this for specials.
													# Eg: Downton Abbey S00E02 (season finale, do not make it a midseason finale).
													type = self.mMetatools.mergeType(values = type, season = numberSeason, episode = numberEpisode, episodeLastStandard = episodeLast.numberEpisode() if episodeLast else None, fix = True)
												if type: resultEpisode['type'] = type

											country = episode.releaseCountry()
											if not country: country = seasonCountry
											if country: resultEpisode['country'] = [country]

											language = episode.languageOriginal()
											if not language: language = seasonLanguage
											if language: resultEpisode['language'] = language if Tools.isArray(language) else [language]

											studio = episode.companyNameStudio()
											if not studio: studio = seasonStudio
											if studio: resultEpisode['studio'] = studio

											network = episode.companyNameNetwork()
											if not network: network = seasonNetwork
											if network: resultEpisode['network'] = network

											cast = episode.personKodiCast()
											# NB: Do not use the show cast, since they can be very different from the current season's cast.
											# Eg: White Lotus S03.
											# If no/few cast is available, it will in any case be aggregated from the show/season cast in MetaManager.
											#if not cast: cast = seasonCast
											if cast: resultEpisode['cast'] = cast

											director = episode.personKodiDirector()
											# NB: Do not use the show director, since many shows have different directors for each episode.
											# If no director is available, it will in any case be aggregated from the show/season director in MetaManager.
											#if not director: director = seasonDirector
											if director: resultEpisode['director'] = director

											writer = episode.personKodiWriter()
											# NB: Do not use the show writer, since many shows have different writers for each episode.
											# If no writer is available, it will in any case be aggregated from the show/season writer in MetaManager.
											#if not writer: writer = seasonWriter
											if writer: resultEpisode['writer'] = writer

											if resultEpisode['season'] == 0 or resultEpisode['episode'] == 0:
												resultEpisode['special'] = {
													'type' : episode.specialType(),
													'story' : episode.specialStory(),
													'extra' : episode.specialExtra(),
													'before' : episode.specialBefore(),
													'after' : episode.specialAfter(),
												}

											image = {
												MetaImage.TypePoster : episode.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
												MetaImage.TypeThumb : episode.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
												MetaImage.TypeFanart : episode.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackNone, sort = MetaData.SortSettings, extract = False), # Do not use a fallback.
												MetaImage.TypeLandscape : episode.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
												MetaImage.TypeBanner : episode.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
												MetaImage.TypeClearlogo : episode.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
												MetaImage.TypeClearart : episode.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
												MetaImage.TypeDiscart : episode.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings, extract = False),
												MetaImage.TypeKeyart : episode.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackNone, sort = MetaData.SortSettings, extract = False), # Do not use a fallback.
											}

											image = self._imageCreate(image = image)
											if image: resultEpisode[MetaImage.Attribute] = image

											result.append(resultEpisode)
										except: Logger.error()
		except: Logger.error()

		if not result: result = None
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	##############################################################################
	# PACK
	##############################################################################

	def metadataPack(self, id = None, tvdb = None, imdb = None, data = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if id:
				if not imdb and Tools.isString(id) and id.startswith('tt'): imdb = id
				if not tvdb: tvdb = id

			if data or tvdb or imdb:
				from lib.meta.pack import MetaPack

				def _packNumber(season, episode):
					return int(('%06d' % season) + ('%06d' % episode))

				if data is None and (tvdb or imdb):
					core = MetaCore(provider = MetaCore.ProviderTvdb, threaded = MetaCore.ThreadedDynamic if threaded is False else threaded)
					data = core.show(idTvdb = tvdb, idImdb = imdb, level = MetaCore.Level4, cache = cache if cache else False)

				if data:
					dataSeasons = data.season(sort = True)
					dataEpisodes = data.episode(sort = True)

					if dataSeasons and not Tools.isArray(dataSeasons): dataSeasons = [dataSeasons]
					if dataEpisodes and not Tools.isArray(dataEpisodes): dataEpisodes = [dataEpisodes]

					# Collect all available episodes.
					dataSeries = []
					if dataSeasons:
						for i in dataSeasons:
							i = i.episode(sort = True)
							if i: dataSeries.extend(i)
					if dataEpisodes: dataSeries.extend(dataEpisodes)
					temp = []
					seen = set()
					for i in dataSeries:
						number = i.number(format = MetaData.FormatUniversal)
						if not number in seen:
							seen.add(number)
							temp.append(i)
					dataSeries = temp

					# Determine the abolsute episode number.
					order = []
					for i in dataSeries:
						numberSeason = i.numberSeason()
						if numberSeason > 0: order.append(_packNumber(season = numberSeason, episode = i.numberEpisode()))
					order = Tools.listSort(order)
					order = {order[i] : i + 1 for i in range(len(order))}

					# Collect all available seasons.
					if dataSeasons:
						finished = data.status() in (MetaData.StatusEnded, MetaData.StatusCanceled)
						lastSeason = [j.numberSeason() for j in dataSeasons]
						lastSeason = [j for j in lastSeason if not j is None]
						lastSeason = max(lastSeason) if lastSeason else None

						seasons = []
						for i in dataSeasons:
							episodes = []
							dates = []
							times = []
							types = []
							durations = []

							numberSeason = i.numberSeason()
							try: numbersSeason = Tools.copy(i.numbersSeason()) # Make a copy, since these are edited below. Otherwise exceptions are thrown if MetaTvdb.pack(...) is called multiple times after each other.
							except: numbersSeason = None
							if not numbersSeason: numbersSeason = {MetaPack.NumberStandard : numberSeason}
							if not MetaPack.NumberAbsolute in numbersSeason: numbersSeason[MetaPack.NumberAbsolute] = 1 if numberSeason > 0 else 0
							if not MetaPack.NumberSequential in numbersSeason: numbersSeason[MetaPack.NumberSequential] = 1 if numberSeason > 0 else 0

							episode = i.episode(sort = True)
							if episode:
								if not Tools.isArray(episode): episode = [episode]

								# Already needed for lastEpisode.
								for j in range(len(episode)):
									#gaiafuture
									# Not sure why, but there are sporadic errors that sometimes returns the episode as a dict.
									# This is very sporadic/rare. When generating the pack again, the error is gone and episodes are objects again.
									# Convert to a MetaData object if this happens.
									# The real origin of this problem has to be figured out at some point.
									# Seems to happen more frequently when calling Tester.metadataPack(refresh = True) in tester.py.
									# Maybe the object gets serialize/cached somewhere, so that when retrieving it again, it now is a dict.
									if Tools.isDictionary(episode[j]): episode[j] = MetaData(media = Media.Episode, data = episode[j])

								lastEpisode = [j.numberEpisode() for j in episode]
								lastEpisode = [j for j in lastEpisode if not j is None]
								lastEpisode = max(lastEpisode) if lastEpisode else None

								for j in episode:
									try:
										numberEpisode = j.numberEpisode()
										try: numbersEpisode = Tools.copy(j.numbersEpisode()) # Make a copy, since these are edited below. Otherwise exceptions are thrown if MetaTvdb.pack(...) is called multiple times after each other.
										except: numbersEpisode = None
										if not numbersEpisode: numbersEpisode = {MetaPack.NumberStandard : numberEpisode}
										try: numbersEpisode[MetaPack.NumberStandard] = [numberSeason, numbersEpisode[MetaPack.NumberStandard]]
										except: pass
										try: numbersEpisode[MetaPack.NumberAbsolute] = [1, numbersEpisode[MetaPack.NumberAbsolute]]
										except: pass
										if not MetaPack.NumberSequential in numbersEpisode:
											if numberSeason == 0:
												numbersEpisode[MetaPack.NumberSequential] = [1, 0]
											else:
												try: numbersEpisode[MetaPack.NumberSequential] = [1, order[_packNumber(season = numberSeason, episode = numberEpisode)]]
												except: pass

										date = j.releaseDateFirst(format = MetaData.FormatDate)
										if date: dates.append(date)
										time = j.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
										times.append(time if time else 0)

										status = j.status()
										if status: status = MetaTvdb._convertStatus(status = status, inverse = True)
										else: status = self.mMetatools.mergeStatus(media = Media.Episode, season = numberSeason, episode = numberEpisode, time = time)

										type = self._convertType(type = j.type(), inverse = True, list = True)
										types.append(type)

										# Sometimes TVDb does not label season finales.
										# Eg: Dragon Ball Super S01E14 was previously marked as a season finale, but not anymore. Even though the other seasons all have marked finales.
										if numberEpisode == lastEpisode:
											try: type.remove(Media.Standard)
											except: pass
											if not Media.Finale in type: type.append(Media.Finale)
											if not Media.Outer in type and not Media.Inner in type and not Media.Middle in type:
												if numberSeason == lastSeason and finished: type.append(Media.Outer)
												else: type.append(Media.Inner)

										duration = j.duration()
										if duration: durations.append(duration)

										episodes.append({
											'id' : {
												'imdb'	: j.idImdb(),
												'tmdb'	: j.idTmdb(),
												'tvdb'	: j.idTvdb(),
												'trakt'	: j.idTrakt(),
											},
											'title'		: j.titleSettings(),
											'alias'		: j.title(language = True),
											'number'	: numbersEpisode,
											'year'		: Time.year(timestamp = time) if time else j.year(),
											'date'		: date,
											'time'		: time,
											'status'	: status,
											'serie'		: type,
											'duration'	: duration,
										})
									except: Logger.error()

							date = i.releaseDateFirst(format = MetaData.FormatDate)
							time = i.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
							if not time and times: time = min(times)
							if not date and dates: date = min(dates)

							type = self._convertType(type = i.type(), inverse = True, list = True)

							# TVDb only has a status for shows, but not for seasons. Calculate the status based on the episode release dates.
							status = i.status()
							if not status:
								# Do not mark the season as ended purley on time.
								# Since the season might still continue, although the last episode has already been aired, but there are new unaired episodes that were not scraped by Trakt yet.
								try: timeNext = data.season(number = numberSeason + 1).episode(sort = True)[0].releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
								except: timeNext = None
								try: timeLast = data.season(sort = True)[-1].episode(sort = True)[-1].releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
								except: timeLast = None

								status = self.mMetatools.mergeStatus(media = Media.Season, season = numberSeason, time = time, timeSeasonLast = timeLast, timeSeasonNext = timeNext, timeEpisode = times, type = type, typeEpisode = types, status = MetaTvdb._convertStatus(status = data.status(), inverse = True))

							duration = i.duration()
							if not duration and durations: duration = int(sum(durations) / float(len(durations)))

							seasons.append({
								'id' : {
									'imdb'	: i.idImdb(),
									'tmdb'	: i.idTmdb(),
									'tvdb'	: i.idTvdb(),
									'trakt'	: i.idTrakt(),
								},
								'title'		: i.titleSettings(),
								'alias'		: i.title(language = True),
								'number'	: numbersSeason,
								'year'		: Time.year(timestamp = time) if time else i.year(),
								'date'		: date,
								'time'		: time,
								'status'	: status,
								'serie'		: type,
								'duration'	: duration,
								'episodes'	: episodes,
							})

						date = data.releaseDateFirst(format = MetaData.FormatDate)
						time = data.releaseDateFirst(zone = MetaData.ZoneUtc, format = MetaData.FormatTimestamp) # Return the timestamp in UTC, not the original timezone.
						result = {
							'id' : {
								'imdb'	: data.idImdb(),
								'tmdb'	: data.idTmdb(),
								'tvdb'	: data.idTvdb(),
								'trakt'	: data.idTrakt(),
							},
							'title'		: data.titleSettings(),
							'alias'		: data.title(language = True),
							'year'		: data.year() or (Time.year(timestamp = time) if time else None),
							'date'		: date,
							'time'		: time,
							'status'	: data.status(),
							'duration'	: data.duration(),
							'seasons'	: seasons,
						}
				else: complete = False
		except: Logger.error()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	###################################################################
	# IMAGE
	###################################################################

	def _imageCreate(self, image):
		for k, v in image.items():
			if not v: v = []
			for i in range(len(v)):
				j = v[i]
				sort = j.get('sort')
				if Tools.isDictionary(sort): sort = {k2 : v2[1] if (v2 and Tools.isList(v2) and Tools.isList(v2[0])) else v2 for k2, v2 in sort.items()}
				v[i] = MetaImage.create(link = j.get('link'), provider = MetaImage.ProviderTvdb, language = j.get('language'), theme = j.get('theme'), sort = sort)
			image[k] = v
		return image

	def _imageSeason(self, images):
		# This function tries to pick season images (eg: posters) that belong to the same theme/group, so that menus look better and more consistent.
		# This problem is mainly with TVDb images.
		# Trying to group the images based on the number of votes or other attributes (in MetaData/MetaTvdb) works sometimes, but in too many cases combines the wrong posters.
		# The best approach (although still not perfect) is to get all season images and then use the filenames to determine which ones belong together.
		# There are 2 naming conventions on TVDb:
		#	1. Hexadecimal names
		#		These seem to be the new standard, since they are used by newer shows.
		#		Many older shows also have some images with this naming convention, probably because they were uploaded later on.
		#		Not sure how these names are generated, but images belonging to the same group/theme seem to have the same first few characters.
		#		Maybe they are generated based on the upload date? Or the same theme always gets the same fixed prefix?
		#		Often the first 6 characters match, but sometimes it is only the first 5 characters.
		#			https://artworks.thetvdb.com/banners/v4/season/2012707/posters/67b2ca755999e.jpg
		#			https://artworks.thetvdb.com/banners/v4/season/2160815/posters/67b2ca4673008.jpg
		#	2. Number names
		#		These seem to be the old standard, since mostly older shows use them.
		#		Have not found newer shows that use these.
		#		The format: <TVDb_show_ID>-<season-number> OR <TVDb_show_ID>-<season-number>-<some-theme-group-number>
		#		In many cases the last number actually indicates the theme/group correctly.
		#			https://artworks.thetvdb.com/banners/seasons/73787-1-6.jpg
		#			https://artworks.thetvdb.com/banners/seasons/73787-2-6.jpg
		#			https://artworks.thetvdb.com/banners/seasons/73787-3-6.jpg
		#			https://artworks.thetvdb.com/banners/seasons/73787-4-6.jpg
		#		But in fewer cases they do not match.
		#			https://artworks.thetvdb.com/banners/seasons/73787-3-6.jpg
		#			https://artworks.thetvdb.com/banners/seasons/73787-4-6.jpg
		#			https://artworks.thetvdb.com/banners/seasons/73787-5-6.jpg
		#		Either the last number if not used for the them/group, or it was simply specified incorrectly by the uploader.
		#
		# The solution:
		#	1. If all images from all seasons have a vote/favorite on TVDb, keep the original order, since those votes were probably cast to create a common theme (eg: One Piece).
		#	2. If all images from TVDb are of low quality, push TVDb images to the back, and prefer Fanart/TMDb images (eg: That '70s show).
		#	3. Otherwise pick the theme/group (filename prefix) that has most images.
		#
		# Test this with:
		#	1. The Big Bang Theory
		#	2. One Piece (Anime)
		#	3. White Lotus
		#	4. That '70s show
		#	5. Game of Thrones
		#	6. House
		#	7. The Righteous Gemstones

		try:
			from lib.modules.network import Networker

			# Not sure if this should be done for fanart and landscape as well?
			# TVDb does not have season backgrounds for many older shows.
			for type in [MetaImage.TypePoster, MetaImage.TypeKeyart]:
				ids = {}
				votes = []
				total = len(images)
				threshold = total * 0.4 # The theme/group needs to cover at least 40% of the seasons.

				def _name(image):
					return Networker.linkName(image.get('link'), extension = False)

				def _id(name):
					return Regex.replace(data = name, expression = '\-(\d+)(?:$|\-)', replacement = 'x', group = 1)

				def _add(id, vote, index, quality):
					try:
						ids[id]['count'] += 1
						ids[id]['vote'] += vote
						ids[id]['index'] += index
						if not ids[id]['quality']: ids[id]['quality'] = quality
					except:
						ids[id] = {'count' : 1, 'quality' : quality, 'vote' : vote, 'index' : index}

				for image in images.values():
					subids = {}
					voted = False
					for i in image[type]:
						name = _name(image = i)
						if name:
							try: vote = i['sort']['vote'][0] or 0
							except: vote = 0
							if not voted:
								votes.append(vote)
								voted = True

							try: index = i['sort']['index'][0] or 0
							except: index = 0

							quality = i.get('quality')
							if '-' in name:
								_add(id = _id(name = name), vote = vote, index = index, quality = quality)
							else:
								id = name
								for k in range(len(name)):
									id = id[:-1]

									# Use 4, not 5, for House S01/S02.
									# 4 also picks better images for TBBT.
									if len(id) < 4: break

									# Do not add twice for the same image group.
									# Otherwise shorter prefixes can be added multiple times and then having a larger count than longer prefixes.
									if not id in subids:
										subids[id] = True
										_add(id = id, vote = vote, index = index, quality = quality)

				# If there are multiple votes/favorites for each season poster in the show, keep the original order.
				# If each poster has more than 1 vote, they were probably specifically voted to make them the primary choice in order to combined posters of the same theme.
				# Eg: One Piece (has 2-8 votes for each season poster, except S0 with only one vote).
				# Trying to use the mechanism below to pick the posters for One Piece always ends in a mess.
				exception = False
				if len(votes) >= total:
					# Skip S0 and possibly the last unreleased/future season.
					if all(i >= 1 for i in (votes[1:] if len(votes) < 5 else votes[1:-1])):
						# At least an average count of 3.
						# Exclude eg: Game of Thrones.
						if sum(votes) >= (total * 3):
							exception = True

				if not exception and ids:
					# Firstly sort by how many images are available.
					# Secondly sort by quality. First high, then None, then low.
					# Thirdly sort by votes.
					# Fourthly sort by the subname length. Longer prefixes should be preferred.
					# Lastly sort by index if all the previous values are the same. Eg: Rick & Morty S08, only 2 posters without any votes. Pick the first one.
					ids = {k : v for k, v in sorted(ids.items(), key = lambda i : (i[1]['count'], 2 if i[1]['quality'] == MetaData.ImageQualityHigh else 0 if i[1]['quality'] == MetaData.ImageQualityLow else 1, i[1]['vote'], len(i[0]), i[1]['index']), reverse = True)}

					# Group by quality.
					id = [None, None, None]
					for k, v in ids.items():
						if v['quality'] == MetaData.ImageQualityHigh:
							if id[0] is None: id[0] = k
							break
						elif v['quality'] == MetaData.ImageQualityLow:
							if id[2] is None: id[2] = k
						else:
							if id[1] is None: id[1] = k

					# If there are not enough high quality images, move TVDb to the back and prefer Fanart/TMDb images, which are typically of higher quality.
					# Eg: That '70s Show (Fanart also does not have a consistent them/group, but at least look better from those on TVDb).
					# Only do this if enough images are available for enough seasons.
					# Eg: The Recruit only has 2 seasons, so do not mark as ignored if there are that few seasons.
					if id[0] is None or (ids[id[0]]['count'] < threshold and threshold >= 2):
						for number, image in images.items():
							for i in image[type]: i['sort'][MetaImage.SortIgnore] = 1

					# Add the theme/group index.
					keys = list(ids.keys())
					for number, image in images.items():
						for i in image[type]:
							name = _name(image = i)
							if name:
								if '-' in name:
									match = _id(name = name)
									for j in range(len(keys)):
										if match == keys[j]:
											i[MetaImage.AttributeTheme] = keys[j]
											i['sort'][MetaImage.SortTheme] = j
											break
								else:
									match = name
									for j in range(len(keys)):
										if match.startswith(keys[j]):
											i[MetaImage.AttributeTheme] = keys[j]
											i['sort'][MetaImage.SortTheme] = j
											break

					id = id[0] or id[1] or id[2]

					# Only do this if there are common images across at least "threshold"% of the seasons.
					# Otherwise keep the orignal order.
					if id and ids[id]['count'] >= threshold:
						for number, image in images.items():
							temp1 = []
							temp2 = []
							for i in image[type]:
								name = name = _name(image = i)
								if name:
									if '-' in name: match = _id(name = name) == id
									else: match = name.startswith(id)
									if match: temp1.append(i)
									else: temp2.append(i)
							if temp1 or temp2: images[number][type] = temp1 + temp2
		except: Logger.error()
		return images
