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

from lib.modules.tools import Tools, Time, Logger, Regex
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
		MetaTools.StatusPiloted			: MetaData.StatusPilot,
		MetaTools.StatusContinuing		: MetaData.StatusContinuing,
		MetaTools.StatusEnded			: MetaData.StatusEnded,
		MetaTools.StatusCanceled		: MetaData.StatusCanceled,
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

					time = data.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatTimestamp)
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
						MetaImage.TypePoster : data.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeThumb : data.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeFanart : data.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeLandscape : data.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeBanner : data.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeClearlogo : data.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeClearart : data.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeDiscart : data.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeKeyart : data.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
					}
					for k, v in image.items():
						image[k] = [MetaImage.create(link = i, provider = MetaImage.ProviderTvdb) for i in v] if v else []
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

					showId = show.id()
					showTitle = show.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					showPlot = show.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					showYear = show.year()
					showPremiered = show.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
					showTime = show.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatTimestamp)
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
					showImage = {
						MetaImage.TypePoster : show.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeThumb : show.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeFanart : show.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeLandscape : show.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeBanner : show.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeClearlogo : show.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeClearart : show.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeDiscart : show.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeKeyart : show.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
					}

					seasons = show.season(sort = True)
					episodes = show.episode(sort = True)

					for season in seasons:
						try:
							episodesSeason = season.episode()
							try: episodesFirst = episodesSeason[0]
							except: episodesFirst = None
							try: episodesLast = episodesSeason[-1]
							except: episodesLast = None

							resultSeason = {}
							resultSeason['id'] = Tools.copy(showId) # Copy, since we edit it for each season by adding the season IDs.

							resultSeason['season'] = season.numberSeason()

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
								if episodesFirst: premiered = episodesFirst.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
								if not premiered and resultSeason['season'] <= 1: premiered = showPremiered # Do not do this for later seasons, since they might be new/unaired seasons and we do not want to use the years-earlier show premier date.
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									resultSeason['premiered'] = premiered
									resultSeason['aired'] = premiered

							time = season.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatTimestamp)
							if not time and resultSeason['season'] <= 1: time = showTime
							if not time and premiered: time = Time.timestamp(premiered, format = Time.FormatDate, utc = True)
							if time: resultSeason['time'] = {MetaTools.TimePremiere : time}

							airs = {}
							airTime = season.releaseTime(zone = MetaData.ZoneOriginal)
							if not airTime:
								if episodesFirst: airTime = episodesFirst.releaseTime(zone = MetaData.ZoneOriginal)
								if not airTime: airTime = showAirTime
							if airTime: airs['time'] = airTime
							airDay = season.releaseDay()
							if not airDay:
								if episodesFirst: airDay = episodesFirst.releaseDay()
								if not airDay: airDay = showAirDay
							if airDay: airs['day'] = [i.title() for i in airDay]
							airZone = season.releaseZoneName()
							if not airZone:
								if episodesFirst: airZone = episodesFirst.releaseZoneName()
								if not airZone: airZone = showAirZone
							if airZone: airs['zone'] = airZone
							if airs: resultSeason['airs'] = airs

							genre = season.genre()
							if not genre:
								genre = showGenre
								if not genre and episodesFirst: genre = episodesFirst.genre()
							if genre: resultSeason['genre'] = MetaTvdb._convertGenre(genre = genre, inverse = True)

							mpaa = season.certificateCode(country = MetaData.CountryUnitedStates, selection = MetaData.SelectionSingle)
							if not mpaa:
								mpaa = season.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
								if not mpaa:
									mpaa = showMpaa
									if not mpaa and episodesFirst:
										mpaa = episodesFirst.certificateCode(country = MetaData.CountryUnitedStates, selection = MetaData.SelectionSingle)
										if not mpaa: mpaa = episodesFirst.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
							if mpaa: resultSeason['mpaa'] = MetaTvdb._convertCertificate(certificate = mpaa, inverse = True)

							duration = season.durationSeconds()
							if duration is None:
								if episodesFirst: duration = episodesFirst.durationSeconds()
								if duration is None: duration = showDuration
							if not duration is None: resultSeason['duration'] = duration

							status = season.status()
							if not status:
								if episodesLast: status = episodesLast.status()
								# It does not make sense to have a status for episodes.
								# It only clutters the info dialog with an extra label.
								# And Kodi docs say it is for shows only.
								#if not status: status = showStatus
							if status: resultSeason['status'] = MetaTvdb._convertStatus(status = status, inverse = True)

							country = season.releaseCountry()
							if not country:
								country = showCountry
								if not country and episodesFirst: country = episodesFirst.releaseCountry()
							if country: resultSeason['country'] = [country]

							language = season.languageOriginal()
							if not language:
								language = showLanguage
								if not language and episodesFirst: language = episodesFirst.languageOriginal()
							if language: resultSeason['language'] = language if Tools.isArray(language) else [language]

							studio = season.companyNameStudio()
							if not studio:
								studio = showStudio
								if not studio and episodesFirst: studio = episodesFirst.companyNameStudio()
							if studio: resultSeason['studio'] = studio

							network = season.companyNameNetwork()
							if not network:
								network = showNetwork
								if not network and episodesFirst: network = episodesFirst.companyNameNetwork()
							if network: resultSeason['network'] = network

							cast = season.personKodiCast()
							if not cast:
								cast = showCast
								if not cast and episodesFirst: cast = episodesFirst.personKodiCast()
							if cast: resultSeason['cast'] = cast

							director = season.personKodiDirector()
							if not director:
								director = showDirector
								if not director and episodesFirst: director = episodesFirst.personKodiDirector()
							if director: resultSeason['director'] = director

							writer = season.personKodiWriter()
							if not writer:
								writer = showWriter
								if not writer and episodesFirst: writer = episodesFirst.personKodiWriter()
							if writer: resultSeason['writer'] = writer

							image = {
								MetaImage.TypePoster : season.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeThumb : season.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeFanart : season.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeLandscape : season.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeBanner : season.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeClearlogo : season.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeClearart : season.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeDiscart : season.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeKeyart : season.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
							}
							for k, v in image.items(): image[k] = [MetaImage.create(link = i, provider = MetaImage.ProviderTvdb) for i in v] if v else []
							if image: resultSeason[MetaImage.Attribute] = image

							result.append(resultSeason)
						except: Logger.error()
		except: Logger.error()

		if not result: result = None
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	def metadataEpisode(self, imdb = None, tvdb = None, season = None, language = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if tvdb or imdb:
				manager = MetaCore(provider = MetaCore.ProviderTvdb, threaded = MetaCore.ThreadedDynamic if threaded is False else threaded)
				show = manager.show(idTvdb = tvdb, idImdb = imdb, level = MetaCore.Level6, numberSeason = season, cache = cache if cache else False)
				if show and show.idTvdb():
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

								seasonTime = season.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatTimestamp)
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
								for episode in episodes:
									if episode: # Sometimes TVDb fails to retrieve the episode, and then the episode is None.
										try:
											resultEpisode = {}

											resultEpisode['id'] = Tools.copy(showId) # Copy, since we edit it for each episode by adding the season/episode IDs.
											if seasonId: resultEpisode['id']['season'] = seasonId
											id = episode.id()
											if id: resultEpisode['id']['episode'] = id

											resultEpisode['season'] = episode.numberSeason()
											resultEpisode['episode'] = episode.numberEpisode()

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
											if not premiered: premiered = seasonPremiered
											if premiered:
												premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
												if premiered:
													resultEpisode['premiered'] = premiered
													resultEpisode['aired'] = premiered

											time = episode.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatTimestamp)
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
											# It does not make sense to have a status for episodes.
											# It only clutters the info dialog with an extra label.
											# And Kodi docs say it is for shows only.
											#if not status: status = seasonStatus
											if status: resultEpisode['status'] = MetaTvdb._convertStatus(status = status, inverse = True)

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
											if not cast: cast = seasonCast
											if cast: resultEpisode['cast'] = cast

											director = episode.personKodiDirector()
											if not director: director = seasonDirector
											if director: resultEpisode['director'] = director

											writer = episode.personKodiWriter()
											if not writer: writer = seasonWriter
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
												MetaImage.TypePoster : episode.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeThumb : episode.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeFanart : episode.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeLandscape : episode.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeBanner : episode.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeClearlogo : episode.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeClearart : episode.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeDiscart : episode.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeKeyart : episode.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
											}
											for k, v in image.items(): image[k] = [MetaImage.create(link = i, provider = MetaImage.ProviderTvdb) for i in v] if v else []
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
					current = Time.timestamp()

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
						seasons = []
						for i in dataSeasons:
							episodes = []
							times = []
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
								for j in episode:
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

									time = j.releaseDateFirst(format = MetaData.FormatTimestamp)
									times.append(time if time else 0)

									status = j.status()
									if not status and time: status = MetaPack.StatusEnded if time <= current else MetaPack.StatusUpcoming

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
										'time'		: time,
										'status'	: status,
										'duration'	: duration,
									})

							# TVDb only has a status for shows, but not for seasons. Calculate the status based on the episode release dates.
							status = i.status()
							if not status:
								if times and times[-1] > 0 and max(times) < current: status = MetaPack.StatusEnded
								elif not times or min(times) > current: status = MetaPack.StatusUpcoming
								else: status = MetaPack.StatusContinuing

							time = i.releaseDateFirst(format = MetaData.FormatTimestamp)
							if not time and times: time = min(times)

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
								'time'		: time,
								'status'	: status,
								'duration'	: duration,
								'episodes'	: episodes,
							})

						time = data.releaseDateFirst(format = MetaData.FormatTimestamp)
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
							'time'		: time,
							'status'	: data.status(),
							'duration'	: data.duration(),
							'seasons'	: seasons,
						}
				else: complete = False
		except: Logger.error()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result
