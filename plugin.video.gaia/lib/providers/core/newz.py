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

from lib.providers.core.usenet import ProviderUsenetJson
from lib.modules.network import Networker
from lib.modules.tools import Regex, Converter, Tools

'''

	This provider is for different forks. They all work very similarly, but have some structural and attribute-name differences.
		Newznab							http://newznab.com
		Newznab+ (Newznab fork)			https://github.com/anth0/nnplus
		nZEDb (Newznab+ fork)			https://nzedb.github.io
		NNTmux (Newznab+/nZEDb fork)	https://github.com/NNTmux/newznab-tmux
		Spotweb (no fork, but same query interface)

	Documentation:
		https://inhies.github.io/Newznab-API/
		https://buildmedia.readthedocs.org/media/pdf/newznab/latest/newznab.pdf

	Test queries:

		Movie (IMDb): /api?o=json&t=movie&imdbid=0499549&apikey=XXXXXXX
		Movie (Query): /api?o=json&t=search&q=avatar%202009&cat=2000,8000&apikey=XXXXXXX
		Movie (Pack): /api?o=json&t=search&q=lord%20of%20the%20rings%20trilogy&cat=2000,8000&apikey=XXXXXXX (or: harry potter if no lord of the rings, eg NZBFinder)

		Show (TVDb): /api?o=json&t=tvsearch&tvdbid=121361&season=8&ep=1&apikey=XXXXXXX
		Show (IMDb): /api?o=json&t=tvsearch&imdbid=0944947&season=8&ep=1&apikey=XXXXXXX
		Show (Title): /api?o=json&t=tvsearch&q=game%20of%20thrones&season=8&ep=1&apikey=XXXXXXX
		Show (Query): /api?o=json&t=search&q=game%20of%20thrones%20s08e01&cat=5000,8000&apikey=XXXXXXX

		Show (Show Pack TVDb): /api?o=json&t=tvsearch&tvdbid=121361&apikey=XXXXXXX
		Show (Show Pack Query): /api?o=json&t=search&q=game%20of%20thrones%20complete&cat=5000,8000&apikey=XXXXXXX

		Show (Season Pack TVDb): /api?o=json&t=tvsearch&tvdbid=121361&season=8&ep=0&apikey=XXXXXXX
		Show (Season Pack Title): /api?o=json&t=tvsearch&q=game%20of%20thrones&season=8&ep=0&apikey=XXXXXXX
		Show (Season Pack Query): /api?o=json&t=search&q=game%20of%20thrones%20season%208&cat=5000,8000&apikey=XXXXXXX (or: "s08", or "witcher s01" on NZBFinder)

		Show (Special TVDb): /api?o=json&t=tvsearch&tvdbid=121361&season=0&ep=41&apikey=XXXXXXX
		Show (Special Title): /api?o=json&t=tvsearch&q=game%20of%20thrones&season=0&ep=41&apikey=XXXXXXX
		Show (Special Query): /api?o=json&t=search&q=game%20of%20thrones%20the%20last%20watch&cat=5000,8000&apikey=XXXXXXX

		Attributes (check if the "grabs" attribute is listed): /api?o=json&t=movie&imdbid=0499549&attrs=grabs&apikey=XXXXXXX

	Usenet indexer lists:
		https://www.cogipas.com/best-nzb-search/
		https://www.usenet.com/best-nzb-sites-2017/
		https://www.ngprovider.com/nzb-sites.php
		https://usenetreviews.org/nzbsites/
		https://www.reddit.com/r/usenet/wiki/indexers
		https://usenet4all.nl/threads/free-indexers.3/

	These usenet indexers were not implemented, due to some issue:
		https://usenet-crawler.com			Website down. Cloudflare says the destination server times out.
		https://wtfnzb.pw					Website down. Cloudflare says the destination server times out.
		https://newznzb.info				Website down. Cloudflare says the destination server times out.
		https://newzleech.com				Website down. Cloudflare says unknown server error.
		https://newz69.keagaming.com		Website unreachable.
		http://nzbnation.com				Website unreachable.
		https://lulunzb.com					Website unreachable.
		https://scenenzb.com				Website unreachable.
		https://elitenzb.info				Website unreachable.
		http://6box.me						Website unreachable.
		https://nzb-tortuga.com				Website unreachable.
		http://a1nzb.com					Website unreachable.
		https://fastnzb.com					Website unreachable.
		https://scenenzb.com				Website unreachable.
		http://newztown.co.za				Website unreachable. Domain (parking) still up.
		http://anonzbs.com					Website unreachable. Domain (parking) still up.
		https://nzbmovieseeker.com			Website unreachable. Domain (parking) still up.
		https://nzbindex.in					Website shut down, domain still up.
		https://nzbs.org					Website shut down, domain still up.
		http://nzbclub.com					Website down. Domain up, but webserver shows 500 error page.
		https://nzb.is						Points to nzbwolf.com.
		https://nzbhydra.com				Now shows a ghost template website.
		https://gingadaddy.com				Seems to have Newnab API. But the generated API key (under the "RSS" tab) does not work (says invalid credentials). Seems the API key is different to the RSS key, and will probably only appear if premium subscsription.
		https://nzbwolf.com					Runs Newnab API. But the register/login buttons on the website do not work.
		https://nzb.su						Registration is open, but API is only available for premium users.
		https://nzbplanet.net				Requires premium account to use api.
		https://simplynzbs.com				Registration by invite only, but premium accounts can still be registered.
		https://oznzb.com					Has a WorPress login page, but no registration option.
		https://drunkenslug.com				Registration by invite only.
		https://omgwtfnzbs.me				Registration by invite only.
		https://nzb.cat						Registration by invite only. Has "free invites", but none available at the moment.
		https://spots.xenetix.nl/spotweb	Domain and server up, but webserver problems.
		https://pourcesoir.in				Runs Newnab API. French indexer. The free account cannot use the API. Requested an upgrade, but still waiting.
		https://headphones.codeshy.com		Only premium accounts availble.
		https://the-newgeneration.net		No open registration.
		https://nzbquality.com				No open registration.
		http://www.binabled.com   			On search: Binabled is temporarily down for maintenance. Please try again later.

	These usenet indexers were not implemented yet, since they use a different engines (not Newznab forks):
		https://nzbgrabit.xyz			Doesn't seem to have an API. Message board only.
		http://the-hive.be				Message board.
		https://nzbforyou.com			Message board.
		https://pirates4all.com			Message board.
		https://army-of-strangers.biz	Message board.
		https://binnews.ninja			Custom site. Search does work (with Google Translate disabled), but the NZB links point to other NZB indexing sites.
		https://big-bit.org				Custom crappy Dutch site.
		http://bd25.eu					Custom crappy site.
		https://brothers-of-usenet.net	Custom German board, but registration is closed.
		https://newz-complex.org		German message board.
		https://usenet-4all.pw			German message board.
		https://nzbnewzfrance.ninja		French message board.
		https://nzbchronicle.net		Dutch message board.
		https://soundtrack.live			Never receivevd registration email.

'''

class ProviderNewz(ProviderUsenetJson):

	_Fork						= 'Newznab'
	_Path						= 'api'

	_TypeMovie					= 'movie'
	_TypeShow					= 'tvsearch'
	_TypeSearch					= 'search'
	_TypeDownload				= 'get'
	_TypeDetails				= 'details'

	# Do no search by all subcategories, since some sites, like Spotweb, cannot handle that.
	#_CategoryMovie				= ['2000', '2010', '2020', '2030', '2040', '2045', '2050', '2060', '2070', '2080', '2090'] # 2000 = Movies, 2010 = Movies/Foreign, 2020 = Movies/Other, 2030 = Movies/SD, 2040 = Movies/HD, 2045 = Movies/UHD, 2050 = Movies/BluRay, 2060 = Movies/3D, 2070/2080/2090 = might be added in the future
	#_CategoryShow				= ['5000', '5010', '5020', '5030', '5040', '5050', '5060', '5070', '5080', '5090'] # 5000 = TV, 5020 = TV/Foreign, 5030 = TV/SD, 5040 = TV/HD, 5050 = TV/Other, 5060 = TV/Sport, 5070 = TV/Anime, 5080 = TV/Documentary, 5010/5090 = might be added in the future
	#_CategoryOther				= ['8000', '8010'] # 8000 = Other, 8010 = Misc (On older Newznab versions these categories were 7000 and 7010)
	_CategoryMovie				= ['2000']
	_CategoryShow				= ['5000']
	_CategoryOther				= ['8000']

	_ParameterKey				= 'apikey'
	_ParameterType				= 't'
	_ParameterOutput			= 'o'
	_ParameterJson				= 'json'
	_ParameterExtended			= 'extended'
	_ParameterId				= 'id'
	_ParameterLimit				= 'limit'
	_ParameterOffset			= 'offset'
	_ParameterAge				= 'maxage' # In days.
	_ParameterQuery				= 'q'
	_ParameterImdb				= 'imdbid'
	_ParameterTvdb				= 'tvdbid'
	_ParameterSeason			= 'season'
	_ParameterEpisode			= 'ep'
	_ParameterCategory			= 'cat'

	_AttributeId				= 'id'
	_AttributeGuid				= 'guid'
	_AttributeItem				= 'item'
	_AttributeChannel			= 'channel'
	_AttributeName				= 'title'
	_AttributeDescription		= 'description'
	_AttributeSize				= 'size'
	_AttributeTime				= ['pubDate', 'usenetdate', 'adddate']
	_AttributeLink				= 'link'
	_AttributeText				= 'text'
	_AttributeComment			= 'comment'
	_AttributeEnclosure			= 'enclosure'
	_AttributeUrl				= '_url'
	_AttributePassword			= 'password'
	_AttributeDownloads			= 'grabs'
	_AttributeVotesUp			= 'thumbsup'
	_AttributeVotesDown			= 'thumbsdown'

	_AttributeMd5				= 'md5'
	_AttributeSha1				= 'sha1'
	_AttributeSha256			= 'sha256'

	_AttributeAttributes		= 'attrs'
	_AttributeAttributeData		= ['newznab:attr', 'attr']
	_AttributeAttributeList		= ['@attributes']
	_AttributeAttributeName		= ['_name', 'name']
	_AttributeAttributeValue	= ['_value', 'value']

	_AttributeResponseData		= ['newznab:response', 'response']
	_AttributeResponseTotal		= ['_total', 'total']
	_AttributeResponseOffset	= ['_offset', 'offset']

	_AttributeExtensions		= [_AttributeId, _AttributeGuid, _AttributeSize, _AttributePassword, _AttributeDownloads, _AttributeVotesUp, _AttributeVotesDown, _AttributeMd5, _AttributeSha1, _AttributeSha256] + _AttributeTime

	_RequestSuccess				= '^((?!code\s*=\s*"10[02]"|incorrect\s*user\s*credentials|wrong\s*(?:api\s*)?key).)*$'
	_RequestErrors				= [
									{'message' : 35792, 'expression' : '(code\s*=\s*"(?:429|500|501)"|limit\s*reached)'}, # Limit reached
									{'message' : 35793, 'expression' : '(upgrade\s*to)'}, # Premium required. Also has error code 100, like the incorrect credentials ereror, so check message instead.
									{'message' : 35794, 'expression' : '(code\s*=\s*"100"|incorrect\s*user\s*credentials|wrong\s*(?:api\s*)?key)'}, # Incorrect credentials
									{'message' : 35795, 'expression' : '(code\s*=\s*"(?:101)")'}, # Suspended
									{'message' : 35796, 'expression' : '(code\s*=\s*"(?:102)")'}, # Insufficient privileges
								]

	# Links can contain both the GUID and the API key.
	# Both can have the same length and be indistinguishable from each other.
	# Test the expressions sequentially, instead of a single expression matching any prefix, since first prefixes are more likley to be the GUID.
	# Try longer strings first, since they are more likley to be the GUID.
	_IdLengths					= [44, 40, 36, 32]
	_IdPrefixes					= ['\/', _AttributeGuid, _AttributeId, '=', '']
	_IdExtras					= ['\-', ''] # First try with dashes "-" in the GUID. This seems to have been added in the new NewzNab API. API keys do not seem to have dashes.
	_IdExpression				= '^.*%s([a-z0-9%s]{%d,})(?:&|\/|\.|$)'

	_LimitOffset				= 100	# Maximum number of links returned per request. Technically every site can provide a custom value for this, but it seems to be 100 in most cases.
	_LimitDownloads				= 500	# How many grabs/downloads count towards the approval.
	_LimitVotes					= 5		# How many thumbs/votes up/down count towards the approval.

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		fork					= _Fork,
		path					= _Path,

		description				= None,

		performance				= ProviderUsenetJson.PerformanceExcellent - ProviderUsenetJson.PerformanceStep,

		supportMovie			= True,		# Supports movie searches.
		supportMovieImdb		= True,		# Supports movie searches by IMDb ID.
		supportMovieQuery		= True,		# Supports movie searches by query string.

		supportShow				= True,		# Supports show searches.
		supportShowImdb			= True,		# Supports show searches by IMDb ID (imdbid=123).
		supportShowTvdb			= True,		# Supports show searches by TVDb ID (tvdbid=123).
		supportShowTitle		= True,		# Supports show searches by title (query) and season/episode (q=Title&season=1&episode=1).
		supportShowQuery		= True,		# Supports show searches by query string (q=Title%20S01E01).

		supportSpecial			= True,		# Supports special episode searches.
		supportSpecialImdb		= True,		# Supports special episode searches by IMDb ID.
		supportSpecialTvdb		= True,		# Supports special episode searches by TVDb ID.
		supportSpecialTitle		= True,		# Supports special episode searches by title (query) and season/episode.
		supportSpecialQuery		= True,		# Supports special episode searches by query string.

		supportPack				= True,		# Supports pack searches.

		supportPackMovie		= True,		# Supports movie pack searches.

		supportPackShow			= True,		# Supports show pack searches.
		supportPackShowImdb		= True,		# Supports show pack searches by IMDb ID.
		supportPackShowTvdb		= True,		# Supports show pack searches by TVDb ID.
		supportPackShowQuery	= True,		# Supports show pack searches by query string.

		supportPackSeason		= True,		# Supports season pack searches.
		supportPackSeasonImdb	= True,		# Supports season pack searches by IMDb ID.
		supportPackSeasonTvdb	= True,		# Supports season pack searches by TVDb ID.
		supportPackSeasonTitle	= True,		# Supports season pack searches by title (query) and season.
		supportPackSeasonQuery	= True,		# Supports season pack searches by query string.

		supportExact			= True,		# Supports exact string searches.

		supportZero				= True,		# Supports 0 as episode number for searching packs (q=Title&season=1&ep=0). Otherwise the episode zero-number is not added at all.
		supportOffset			= True,		# Supports offset and paging.
		supportCategory			= True,		# Supports the "cat" parameter to search individual categories.
		supportAttributes		= True,		# Supports the "attrs" (instead of "extended=1") parameter in queries.

		**kwargs
	):
		self.mPath = path
		if description: description = description = description.replace('{fork}', fork) # Replace manually, since string formatting requires all keywords to be present.

		if not supportMovie:
			supportMovieImdb = False
			supportMovieQuery = False
			supportPackMovie = False

		if not supportShow:
			supportShowImdb = False
			supportShowTvdb = False
			supportShowTitle = False
			supportShowQuery = False
			supportSpecial = False
			supportPackShow = False
			supportPackSeason = False

		if not supportSpecial:
			supportSpecialImdb = False
			supportSpecialTvdb = False
			supportSpecialTitle = False
			supportSpecialQuery = False

		if not supportPack:
			supportPackMovie = False
			supportPackShow = False
			supportPackSeason = False

		if not supportPack or not supportPackShow:
			supportPackShowImdb = False
			supportPackShowTvdb = False
			supportPackShowQuery = False
		if not supportPack or not supportPackSeason:
			supportPackSeasonImdb = False
			supportPackSeasonTvdb = False
			supportPackSeasonTitle = False
			supportPackSeasonQuery = False
		if not supportShowImdb:
			supportSpecialImdb = False
			supportPackShowImdb = False
			supportPackSeasonImdb = False
		if not supportShowTvdb:
			supportSpecialTvdb = False
			supportPackShowTvdb = False
			supportPackSeasonTvdb = False
		if not supportShowQuery:
			supportSpecialQuery = False
			supportPackShowQuery = False
			supportPackSeasonQuery = False
		if not supportShowTitle:
			supportSpecialTitle = False
			supportPackSeasonTitle = False

		searchId = supportMovieImdb or supportShowImdb or supportSpecialImdb or supportSpecialTvdb or supportPackShowImdb or supportPackShowTvdb or supportPackSeasonImdb or supportPackSeasonTvdb # Before applying the customSearch settings.
		if self.customSearchTitle():
			supportMovieImdb = False
			supportShowImdb = False
			supportSpecialImdb = False
			supportSpecialTvdb = False
			supportPackShowImdb = False
			supportPackShowTvdb = False
			supportPackSeasonImdb = False
			supportPackSeasonTvdb = False

		# There are numerous problems with different  versions/implementations of NewzNab on different sites.
		# Problem 1:
		#	The NewzNab documentation might be outdated or sites simply implement extra stuff for the API.
		#	The NewzNab documentation states that movies can be searched with the IMDb ID and shows with the show title and season/episode number.
		#	Some sites, like NzbFinder, also allows to search by IMDb/TMDb/TVDb/Trakt ID.
		#	Most, if not all, sites also allow shows to be searched by ID (instead of the docs stating to search by title).
		# Problem 2:
		#	Some sites, like NzbGeek, only returns show results with the TVDb ID, but does not return results when the IMDb is used.
		#	Other sites, like NzbFinder, allow you to use other IDs for the show as well. But it seems that this was manually added by NzbFinder and is not officially supported by NewzNab.
		#	Also do not add both IDs, since no results will be returned.
		#	Always add the TVDb ID if available. Only try the IMDb ID afterwards.
		# Problem 3:
		#	Some sites, like NzbFinder, do not support packs very well.
		#	Searching with "season=1&ep=0" does not return anything on NzbFinder. On other sites this returns season packs.
		#	Although NzbFinder has some movie/show/season packs, there are not many and they must be searched by query.
		# Problem 4:
		#	On some sites, like NzbGeek, some season packs are not listed under the TV category, but instead under Movies or Other.
		#	On NzbGeek, this could be mitigated by "t=search", instead of "t=tvsearch". The normal search also works with IDs and season/episode numbers.
		#	However, other sites like NzbFinder do not support season/episode numbers when using "t=search".
		# Problem 5:
		#	Some sites, especially many Spotweb sites, do not support query searches with "t=movie" or "t=tvsearch" or both.
		#	Other sites do allow this, but sometimes return less results then when searching with "t=search".
		#	Therefore always do a universal query search with "t=search" and append the categories as a parameter.
		queries = []

		if supportMovieImdb: queries.append(self._linkCreateMovie(imdb = True, offset = supportOffset, attributes = supportAttributes))
		elif supportMovieQuery: queries.append(self._linkCreateMovie(query = True, offset = supportOffset, attributes = supportAttributes, category = supportCategory))
		if supportPackMovie: queries.append(self._linkCreateMovie(query = True, pack = True, offset = supportOffset, attributes = supportAttributes, category = supportCategory))
		if supportExact: queries.append(self._linkCreateMovie(exact = True, offset = supportOffset, attributes = supportAttributes, category = supportCategory))

		# Many special episodes have and incorrect season/episode number (eg: Game of Thrones real episode S00E55, but Newznab metadata says S00E41 or S08E00).
		# Additionally, many special episodes do not have a number, but only the episode title, or the wrong number with the correct episode title (due to the problem above).
		# Newznab also does not have the number in the attributes metadata for some special episodes (would not be found when searching by ID), although the number is in the filename (would be found when searching by query).
		# Therefore, always search by query (first).
		# Make searching by ID secondary, so those links are cut away if the user has set a request limit, but the query link remains.
		queriesSpecial = []
		if supportSpecialQuery: queriesSpecial.append(self._linkCreateShow(query = True, special = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes, category = supportCategory))
		if supportSpecialTvdb:
			queriesSpecial.append(self._linkCreateShow(tvdb = True, season = True, episode = True, special = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
			if supportPackSeasonTvdb: queriesSpecial.append(self._linkCreateShow(tvdb = True, season = True, special = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportSpecialImdb:
			queriesSpecial.append(self._linkCreateShow(imdb = True, season = True, episode = True, special = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
			if supportPackSeasonImdb: queriesSpecial.append(self._linkCreateShow(imdb = True, season = True, special = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportSpecialTitle:
			queriesSpecial.append(self._linkCreateShow(title = True, season = True, episode = True, special = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
			if supportPackSeasonTitle: queriesSpecial.append(self._linkCreateShow(title = True, season = True, special = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		queries.append(queriesSpecial)

		if supportShowTvdb: queries.append(self._linkCreateShow(tvdb = True, season = True, episode = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportShowImdb: queries.append(self._linkCreateShow(imdb = True, season = True, episode = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportShowTitle: queries.append(self._linkCreateShow(title = True, season = True, episode = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportShowQuery: queries.append(self._linkCreateShow(query = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes, category = supportCategory))

		# Must be before show packs.
		if supportPackSeasonTvdb: queries.append(self._linkCreateShow(tvdb = True, season = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportPackSeasonImdb: queries.append(self._linkCreateShow(imdb = True, season = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportPackSeasonTitle: queries.append(self._linkCreateShow(title = True, season = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportPackSeasonQuery: queries.append(self._linkCreateShow(query = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes, category = supportCategory))

		# Must be after season packs.
		if supportPackShowImdb: queries.append(self._linkCreateShow(tvdb = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportPackShowTvdb: queries.append(self._linkCreateShow(imdb = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes))
		elif supportPackShowQuery: queries.append(self._linkCreateShow(query = True, pack = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes, category = supportCategory))

		if supportExact: queries.append(self._linkCreateShow(exact = True, zero = supportZero, offset = supportOffset, attributes = supportAttributes, category = supportCategory))

		ProviderUsenetJson.initialize(self,
			description			= description,

			performance			= performance,

			supportMovie		= supportMovie,
			supportShow			= supportShow,
			supportSpecial		= supportSpecial,
			supportPack			= supportPack,
			supportPackMovie	= supportPackMovie,
			supportPackShow		= supportPackShow,
			supportPackSeason	= supportPackSeason,

			customSearch		= {ProviderUsenetJson.SettingsDescription : 'Search {name} using either the title, or the IMDb or TVDB ID. Some files, mostly new ones, do not have an associated ID and will therefore not be found during an ID search. Searching by title is slower and can return incorrect results. The title will be used if no ID is available.'} if searchId else None,

			offsetStart			= 0 if supportOffset else None,
			offsetIncrease		= ProviderNewz._LimitOffset if supportOffset else None,

			formatEncode		= ProviderUsenetJson.FormatEncodeQuote,

			searchQuery			= queries,
			searchCategoryMovie	= ProviderNewz._TypeMovie,
			searchCategoryShow	= ProviderNewz._TypeShow,

			extractData			= False,

			**kwargs
		)

	##############################################################################
	# LINK
	##############################################################################

	def _linkCreate(self, type, key = False, extended = False, attributes = False, id = None, query = None, imdb = None, tvdb = None, season = None, episode = None, category = None, limit = None, offset = None, age = None, link = None, path = None):
		try:
			if link is None: link = self.linkCurrent()
			if path is None: path = self.mPath

			# Always use the same order of parameters to ensure the link is always exactly the same. Required for Orion.
			parameters = []
			if key:
				key = self.accountKey() if key is True else key
				if key: parameters.append([ProviderNewz._ParameterKey, key])

			if not type == ProviderNewz._TypeDownload: parameters.append([ProviderNewz._ParameterOutput, ProviderNewz._ParameterJson])
			parameters.append([ProviderNewz._ParameterType, type])

			# One can specify "extended=1" which returns all available attributes.
			# Sites like NzbGeek have many attributes, like the entire IMDb plot text, which increases the reponses size.
			# Instead only specify which attributes to return.
			# Don't do this, since some sites like NzbFinder seem to ignore the attrs parameter.
			if attributes: parameters.append([ProviderNewz._AttributeAttributes, ','.join(ProviderNewz._AttributeExtensions)])
			elif extended: parameters.append([ProviderNewz._ParameterExtended, 1])

			if not id is None: parameters.append([ProviderNewz._ParameterId, id])
			if not query is None: parameters.append([ProviderNewz._ParameterQuery, query])
			if not tvdb is None: parameters.append([ProviderNewz._ParameterTvdb, tvdb]) # Some sites can lookup shows with any ID, but many do not work with the IMDb ID and only return results with a TVDb ID.
			elif not imdb is None: parameters.append([ProviderNewz._ParameterImdb, imdb.replace('tt', '')]) # Do not attach an IMDb ID if there is already one for TVDb, otherwise no results are returned.
			if not season is None: parameters.append([ProviderNewz._ParameterSeason, season])
			if not episode is None: parameters.append([ProviderNewz._ParameterEpisode, episode])

			if not category is None: parameters.append([ProviderNewz._ParameterCategory, ','.join(category) if Tools.isArray(category) else category])
			if not limit is None: parameters.append([ProviderNewz._ParameterLimit, limit])
			if not offset is None: parameters.append([ProviderNewz._ParameterOffset, offset])
			if not age is None: parameters.append([ProviderNewz._ParameterAge, age])

			path = [link, path] if link else path
			return Networker.linkCreate(link = path, parameters = parameters, encode = bool(link))
		except: self.logError()

	def _linkCreateSearch(self, query = None, title = None, imdb = None, tvdb = None, season = None, episode = None, special = False, zero = False, offset = False, category = None, attributes = False):
		local = bool(title or imdb or tvdb)
		query = ProviderUsenetJson.TermQuery if query is True else query if query else None
		title = ProviderUsenetJson.TermTitle if title is True else title if title else None
		imdb = ProviderUsenetJson.TermIdImdbNumber if imdb is True else imdb if imdb else None
		tvdb = ProviderUsenetJson.TermIdTvdb if tvdb is True else tvdb if tvdb else None
		season = ProviderUsenetJson.TermSeason if season is True else season if season else None
		episode = ProviderUsenetJson.TermEpisode if episode is True else episode if episode else None if special else 0 if (season and zero) else None # Do not use ep=0 for special episode season packs.
		age = self.customTime(days = True)
		return self._linkCreate(
			extended = True,
			query = title if title else query,
			imdb = imdb,
			tvdb = tvdb,
			season = season,
			episode = episode,
			link = False,
			type = ProviderUsenetJson.TermCategory if local else ProviderNewz._TypeSearch,
			offset = ProviderUsenetJson.TermOffset if offset else None,
			limit = ProviderNewz._LimitOffset if offset else None,
			age = age,
			category = None if local and category else category,
			attributes = attributes,
		)

	def _linkCreateMovie(self, query = False, imdb = False, pack = False, exact = False, offset = False, category = False, attributes = False):
		return ProviderUsenetJson.TermTypeMovie + (ProviderUsenetJson.TermTypeExact if exact else ProviderUsenetJson.TermTypePack if pack else ProviderUsenetJson.TermTypePackNone) + self._linkCreateSearch(
			query = True if exact else query,
			imdb = imdb,
			offset = offset,
			category = (ProviderNewz._CategoryMovie + ProviderNewz._CategoryOther) if category else None,
			attributes = attributes,
		)

	def _linkCreateShow(self, query = False, title = False, imdb = False, tvdb = False, season = False, episode = False, special = False, pack = False, zero = False, exact = False, offset = False, category = False, attributes = False):
		return ProviderUsenetJson.TermTypeShow + (ProviderUsenetJson.TermTypeSpecial if special else ProviderUsenetJson.TermTypeSpecialNone) + (ProviderUsenetJson.TermTypeExact if exact else ProviderUsenetJson.TermTypePack if pack else ProviderUsenetJson.TermTypePackNone) + self._linkCreateSearch(
			query = True if exact else query,
			title = title,
			imdb = imdb,
			tvdb = tvdb,
			season = season,
			episode = episode,
			special = special,
			zero = zero,
			offset = offset,
			category = (ProviderNewz._CategoryShow + ProviderNewz._CategoryOther) if category else None,
			attributes = attributes,
		)

	##############################################################################
	# EXTRACT
	##############################################################################

	def extractData(self, data, details = False):
		result = None

		if data:
			result = Converter.jsonFrom(data)

			# Some sites have PHP errors/warnings (eg: deprecated functions, timezone issues, etc) before the JSON data.
			# This only applies to some sites, mostly Spotweb, and only certain queries.
			if result is None:
				try: index = data.index('[{')
				except:
					try: index = data.index('{')
					except:
						try: index = data.index('[')
						except: index = None
				if index: result = Converter.jsonFrom(data[index:])

		return result

class ProviderNewzMember(ProviderNewz):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self, path = ProviderNewz._Path, **kwargs):
		ProviderNewz.initialize(self,
			accountKey				= True,
			accountAuthentication	= {
										ProviderUsenetJson.ProcessMode : ProviderUsenetJson.AccountModeAll,
										ProviderUsenetJson.ProcessFixed : {
											ProviderUsenetJson.RequestData : {
												ProviderNewz._ParameterKey : ProviderUsenetJson.TermAuthenticationKey,
											},
										},
									},
			accountVerification		= {
										ProviderUsenetJson.ProcessRequest : {
											ProviderUsenetJson.RequestPath : self._linkCreate(link = False, type = ProviderNewz._TypeDetails, path = path),
										},
										ProviderUsenetJson.ProcessValidate : {
											ProviderUsenetJson.RequestData : ProviderNewz._RequestSuccess,
										},
									},

				**kwargs
		)

	##############################################################################
	# EXTRACT
	##############################################################################

	@classmethod
	def _extractValue(self, item, values, default = None):
		result = default
		for i in values:
			try:
				result = item[i]
				break
			except: pass
		return result

	@classmethod
	def _extractAttribute(self, item, key):
		try:
			attributes = self._extractValue(item = item, values = ProviderNewz._AttributeAttributeData)
			for attribute in attributes:
				attribute = self._extractValue(item = attribute, values = ProviderNewz._AttributeAttributeList, default = attribute)
				attributeKey = self._extractValue(item = attribute, values = ProviderNewz._AttributeAttributeName)
				if attributeKey == key: return self._extractValue(item = attribute, values = ProviderNewz._AttributeAttributeValue, default = None)
		except: pass
		return None

	def _extractId(self, link):
		try:
			parameters = Networker.linkDecode(link)
			if parameters[ProviderNewz._ParameterType] == ProviderNewz._ParameterDownload:
				return parameters[ProviderNewz._ParameterId]
		except: pass

		# Make sure to nexted loop order is correct.
		# First try all with dashes, then nested with longer lengths first, and most inner used the prefixes.
		for extra in ProviderNewz._IdExtras:
			for length in ProviderNewz._IdLengths:
				for prefix in ProviderNewz._IdPrefixes:
					try:
						expression = ProviderNewz._IdExpression % (prefix, extra, length)
						match = Regex.extract(data = link, expression = expression)
						if match: return match
					except: pass

		return None

	def extractList(self, data):
		result = self.extractJson(item = data, keys = ProviderNewz._AttributeItem)
		if Tools.isDictionary(result): result = [result] # If only a single result is found, a dict is returned instead of a list. Or at least on NZBFinder.
		return result

	def extractLink(self, item, details = None, entry = None):
		id = self.extractIdUniversal(item = item, details = details)
		if id: return self._linkCreate(type = ProviderNewz._TypeDownload, id = id, key = False) # Do not add the key, this is only done during resolving.
		return None

	def extractIdUniversal(self, item, details = None, entry = None):
		links = []
		try: links.append(item[ProviderNewz._AttributeGuid][ProviderNewz._AttributeText])
		except: pass
		try: links.append(self._extractAttribute(item = item, key = ProviderNewz._AttributeGuid))
		except: pass
		try: links.append(item[ProviderNewz._AttributeLink])
		except: pass
		try: links.append(item[ProviderNewz._AttributeComment])
		except: pass
		try: links.append(item[ProviderNewz._AttributeEnclosure][ProviderNewz._AttributeUrl])
		except: pass

		for link in links:
			if link:
				id = self._extractId(link = link)
				if id: return id

		return None

	def extractHashOtherMd5(self, item, details = None, entry = None):
		hash = self._extractAttribute(item = item, key = ProviderNewz._AttributeMd5)
		if not hash: hash = None
		return hash

	def extractHashOtherSha1(self, item, details = None, entry = None):
		hash = self._extractAttribute(item = item, key = ProviderNewz._AttributeSha1)
		if not hash: hash = None
		return hash

	def extractHashOtherSha256(self, item, details = None, entry = None):
		hash = self._extractAttribute(item = item, key = ProviderNewz._AttributeSha256)
		if not hash: hash = None
		return hash

	def extractFileName(self, item, details = None, entry = None):
		return self.extractJson(item = item, keys = ProviderNewz._AttributeName)

	def extractFileExtra(self, item, details = None, entry = None):
		extra = self.extractJson(item = item, keys = ProviderNewz._AttributeDescription)
		if extra:
			name = self.extractFileName(item = item, details = details)
			if not name == extra: return extra # Often the description and name is the same, if so, ignore it.
		return None

	def extractFileSize(self, item, details = None, entry = None):
		return self._extractAttribute(item = item, key = ProviderNewz._AttributeSize)

	def extractFileSize(self, item, details = None, entry = None):
		return self._extractAttribute(item = item, key = ProviderNewz._AttributeSize)

	def extractSourceTime(self, item, details = None, entry = None):
		time = self._extractValue(item = item, values = ProviderNewz._AttributeTime)
		if not time: time = self._extractAttribute(item = item, key = ProviderNewz._AttributeTime)
		return time

	def extractSourceApproval(self, item, details = None, entry = None):
		values = []

		try:
			downloads = self._extractAttribute(item = item, key = ProviderNewz._AttributeDownloads)
			if downloads: values.append(float(downloads) / ProviderNewz._LimitDownloads)
		except: pass

		# NzbGeek
		try:
			votesUp = self._extractAttribute(item = item, key = ProviderNewz._AttributeVotesUp)
			votesDown = self._extractAttribute(item = item, key = ProviderNewz._AttributeVotesDown)
			if votesUp or votesDown: values.append((float(votesUp) - float(votesDown)) / ProviderNewz._LimitVotes)
		except: pass

		if values:
			values = [min(ProviderUsenetJson.ApprovalExcellent, max(-ProviderUsenetJson.ApprovalExcellent, value)) for value in values]
			return max(0, sum(values) / float(len(values)))
		else:
			return ProviderUsenetJson.ApprovalDefault

	##############################################################################
	# PROCCESS
	##############################################################################

	def processRequest(self, data):
		# When an error occurs, NewzNab returns XML instead of JSON.
		# Detect the errors with regular expressions.
		if not data or not data.lstrip().startswith(('{', ']')):
			for error in ProviderNewz._RequestErrors:
				if Regex.match(data = data, expression = error['expression']):
					from lib.modules.interface import Translation, Dialog
					title = '%s %s' % (self.name(), Translation.string(35311))
					message = Translation.string(error['message'])
					Dialog.notification(title = title, message = message, icon = Dialog.IconError)
					self.log('%s - %s' % (title, message))
					return ProviderUsenetJson.Skip
		return data

	def processData(self, data):
		# NZBgeek has wrapped the Newznab data in an outer "channel" object.
		try: result = self.extractJson(item = data, keys = ProviderNewz._AttributeChannel)
		except: result = None
		return result if result else data

	def processOffset(self, data, items):
		try:
			response = self._extractValue(item = data, values = ProviderNewz._AttributeResponseData)
			attribute = self._extractValue(item = response, values = ProviderNewz._AttributeAttributeList) # NZBgeek
			if attribute: response = attribute
			total = int(self._extractValue(item = response, values = ProviderNewz._AttributeResponseTotal))
			offset = int(self._extractValue(item = response, values = ProviderNewz._AttributeResponseOffset))
			if total <= (offset + ProviderNewz._LimitOffset): return ProviderUsenetJson.Skip
		except: pass

	def processBefore(self, item):
		password = self._extractAttribute(item = item, key = ProviderNewz._AttributePassword)
		if password and Converter.boolean(password): return ProviderUsenetJson.Skip

##############################################################################
# FORKS
##############################################################################

class ProviderNewznab(ProviderNewzMember):

	def initialize(self, fork = 'Newznab', path = 'api', **kwargs):
		ProviderNewzMember.initialize(self, fork = fork, path = path, **kwargs)

class ProviderNewznabplus(ProviderNewzMember):

	def initialize(self, fork = 'Newznab+', path = 'api', **kwargs):
		ProviderNewzMember.initialize(self, fork = fork, path = path, **kwargs)

class ProvideNzedb(ProviderNewzMember):

	def initialize(self, fork = 'nZEDb', path = 'api', **kwargs):
		ProviderNewzMember.initialize(self, fork = fork, path = path, **kwargs)

class ProviderNntmux(ProviderNewzMember):

	def initialize(self, fork = 'NNTmux', path = 'api/v1/api', **kwargs): # Some sites (TabulaRasa) automatically redirect the path "api" to "api/v1/api". Some sites (nzbs2go) do not redirect and must use the full path. There is also a V2 of NNTmux that works a bit different.
		ProviderNewzMember.initialize(self, fork = fork, path = path, **kwargs)

class ProviderSpot(ProviderNewz):

	def initialize(self, fork = 'Spotweb', path = 'index.php?page=newznabapi', **kwargs):
		ProviderNewz.initialize(self, fork = fork, path = path, **kwargs)
