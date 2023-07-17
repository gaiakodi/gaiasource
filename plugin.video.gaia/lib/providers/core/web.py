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

from lib.providers.core.base import ProviderBase
from lib.modules.tools import Tools, Media, Time, Regex, Converter, Language, System, Logger
from lib.modules.network import Networker
from lib.modules.stream import Stream
from lib.modules.concurrency import Lock, Semaphore

class ProviderWeb(ProviderBase):

	# Term

	TermTitle						= '{title}'				# Movie or show title
	TermTitleMovie					= '{title_movie}'		# Movie title
	TermTitleCollection				= '{title_collection}'	# Movie collection title
	TermTitleShow					= '{title_show}'		# Show title
	TermTitleEpisode				= '{title_episode}'		# Episode title
	TermYear						= '{year}'				# Year
	TermSeason						= '{season}'			# Season number without leading 0s
	TermSeasonZero					= '{season_zero}'		# Season number with leading 0s
	TermEpisode						= '{episode}'			# Episode number without leading 0s
	TermEpisodeZero					= '{episode_zero}'		# Episode number with leading 0s
	TermIdImdb						= '{id_imdb}'			# IMDb ID
	TermIdImdbNumber				= '{id_imdb_number}'	# IMDb ID with the "tt" prefix stripped away.
	TermIdTmdb						= '{id_tmdb}'			# TMDb ID
	TermIdTvdb						= '{id_tvdb}'			# TVDb ID

	TermQuery						= '{query}'				# Query search string
	TermLetter						= '{letter}'			# The first letter of the query search string, used by MagnetDl
	TermCategory					= '{category}'			# Category to search in
	TermOffset						= '{offset}'			# Page or offset number

	TermLinkFull					= '{link_full}'			# URL with host, full path and parameters (eg: https://example.com/path/?x=1&y=2)
	TermLinkParameters				= '{link_parameters}'	# URL without host, but with path and parameters (eg: path/?x=1&y=2)
	TermLinkPath					= '{link_path}'			# URL without host or parameters, but with path  (eg: path)
	TermLinkHost					= '{link_host}'			# URL with host, but without path and parameters  (eg: https://example.com)
	TermLinkDomain					= '{link_domain}'		# Domain and TLD.  (eg: example.com)

	# These terms do not contain any value (they will be replaced by an empty string).
	# Instead they can be used to force a query/data to only execute for a specific media type.
	# For instance, if a query is intended only for movies, add TermTypeMovie anywhere to the query. If a show is now searched, this query will be skipped (or going to the fallback queries if specified).
	# Check how this is used in NewzNab.
	TermTypeExact					= '{type_exact}'		# For exact movie/show searches.
	TermTypeExactMovie				= '{type_exact_movie}'	# For exact movie searches.
	TermTypeExactShow				= '{type_exact_show}'	# For exact show searches.
	TermTypeDirect					= '{type_direct}'		# For normal/direct movie/show searches.
	TermTypeDirectMovie				= '{type_direct_movie}'	# For normal/direct movie searches.
	TermTypeDirectShow				= '{type_direct_show}'	# For normal/direct show searches.
	TermTypeMovie					= '{type_movie}'		# For exact/direct movie searches.
	TermTypeShow					= '{type_show}'			# For exact/direct show searches.
	TermTypePack					= '{type_pack}'			# For pack searches.
	TermTypePackNone				= '{type_pack_none}'	# For non-pack searches.
	TermTypeSpecial					= '{type_special}'		# For special episode searches.
	TermTypeSpecialNone				= '{type_special_none}'	# For normal (non-special) episode searches.

	TermAuthentication				= '{authentication}'	# Main authentication parameter.
	TermAuthentications				= '{authentication_%s}'	# Custom authentication parameters where %s is a number or custom name.
	TermAuthenticationUsername		= TermAuthentications % ProviderBase.AccountTypeUsername
	TermAuthenticationEmail			= TermAuthentications % ProviderBase.AccountTypeEmail
	TermAuthenticationPassword		= TermAuthentications % ProviderBase.AccountTypePassword
	TermAuthenticationKey			= TermAuthentications % ProviderBase.AccountTypeKey
	TermAuthenticationOther			= TermAuthentications % ProviderBase.AccountTypeOther

	TermCustom						= '{custom_%s}'				# Parameters for custom settings. The first %s is the custom setting ID.
	TermCustomized					= '{custom_%s_%s}'			# Parameters for custom settings. The first %s is a custom label. The second %s is the custom setting ID.

	# Query - Type
	QueryTypeMovie					= 'movie'
	QueryTypeMovieYear				= 'movieyear'
	QueryTypeCollection				= 'collection'
	QueryTypeShow					= 'show'
	QueryTypeSeason					= 'season'
	QueryTypeEpisode				= 'episode'
	QueryTypeSpecial				= 'special'

	# Query - Mode
	QueryModeFull					= 'full'	# Use all available keywords. Takes longer to scrape all the different queries.
	QueryModeQuick					= 'quick'	# Only use a subset of keywords. Reduces scraping time. Only available for some queries and languages.

	# Queries
	# Universal and English queries are always included.

	Queries							= {
										# Universal
										Language.UniversalCode : {
											QueryTypeMovie : {
												QueryModeFull : ['%s' % TermTitleMovie],
											},
											QueryTypeMovieYear : {
												QueryModeFull : ['%s %s' % (TermTitleMovie, TermYear)],
											},
											QueryTypeSeason : {
												QueryModeFull : ['%s S%s' % (TermTitleShow, TermSeasonZero)],
											},
											QueryTypeEpisode : {
												QueryModeFull : ['%s S%sE%s' % (TermTitleShow, TermSeasonZero, TermEpisodeZero)],
											},
											QueryTypeSpecial : {
												QueryModeFull : ['%s %s' % (TermTitleShow, TermTitleEpisode)], # Search special episodes by name. All special episodes are added to season 0 by Trakt and TVDb. Hence, do not search by number (eg: S02E00), since the season is not known.
											},
										},

										# English
										Language.EnglishCode : {
											# Most English movie collections contain the keyword "collection", followed by "complete".
											QueryTypeCollection : {
												QueryModeFull : ['%s collection' % TermTitleCollection, '%s complete' % TermTitleCollection, '%s pack' % TermTitleCollection, '%s trilogy' % TermTitleCollection],
												QueryModeQuick : ['%s collection' % TermTitleCollection, '%s complete' % TermTitleCollection],
											},
											# "complete" returns most results. "collection" typically returns a few more results than "pack", but both are very few.
											QueryTypeShow : {
												QueryModeFull : ['%s complete' % TermTitleShow, '%s collection' % TermTitleShow, '%s pack' % TermTitleShow, '%s series' % TermTitleShow],
												QueryModeQuick : ['%s complete' % TermTitleShow, '%s collection' % TermTitleShow],
											},
											QueryTypeSeason : {
												QueryModeFull : ['%s season %s' % (TermTitleShow, TermSeason)],
											},
										},

										# French
										# Sadly we have to use multiple versions of "integrale", since many sites cannot find all of them with one keyword.
										# Some sites (eg YggTorrent) do not make a distinction between é and e, so integral will also find intégral. Look at the "Quick" French queries below that does not include the é versions of the keywords.
										# Other words do not seem to be interchangeable during searching: integrale vs integral vs l'integrale vs l'integral.
										# Not sure, but the e at the end might be gender-based, and the l' is an article.
										Language.CodeFrench : {
											QueryTypeCollection : {
												QueryModeFull : ['%s integrale' % TermTitleCollection, '%s intégrale' % TermTitleCollection, '%s integral' % TermTitleCollection, '%s intégral' % TermTitleCollection, '%s l\'integrale' % TermTitleCollection, '%s l\'intégrale' % TermTitleCollection, '%s l\'integral' % TermTitleCollection, '%s l\'intégral' % TermTitleCollection, '%s complet' % TermTitleCollection, '%s complète' % TermTitleCollection, '%s trilogie' % TermTitleCollection],
												QueryModeQuick : ['%s integrale' % TermTitleCollection, '%s integral' % TermTitleCollection, '%s l\'integrale' % TermTitleCollection, '%s l\'integral' % TermTitleCollection],
											},
											QueryTypeShow : {
												QueryModeFull : ['%s integrale' % TermTitleShow, '%s intégrale' % TermTitleShow, '%s integral' % TermTitleShow, '%s intégral' % TermTitleShow, '%s l\'integrale' % TermTitleShow, '%s l\'intégrale' % TermTitleShow, '%s l\'integral' % TermTitleShow, '%s l\'intégral' % TermTitleShow, '%s saisons' % TermTitleShow, '%s complet' % TermTitleShow, '%s complète' % TermTitleShow],
												QueryModeQuick : ['%s integrale' % TermTitleShow, '%s integral' % TermTitleShow, '%s l\'integrale' % TermTitleShow, '%s l\'integral' % TermTitleShow],
											},
											QueryTypeSeason : {
												QueryModeFull : ['%s saison %s' % (TermTitleShow, TermSeason)],
											},
										},

										# German
										Language.CodeGerman : {
											QueryTypeCollection : {
												QueryModeFull : ['%s Sammlung' % TermTitleCollection, '%s Trilogie' % TermTitleCollection],
												QueryModeQuick : ['%s Sammlung' % TermTitleCollection],
											},
											QueryTypeShow : {
												QueryModeFull : ['%s Staffeln' % TermTitleShow, '%s Sammlung' % TermTitleShow],
												QueryModeQuick : ['%s Staffeln' % TermTitleShow],
											},
											QueryTypeSeason : {
												QueryModeFull : ['%s Staffel %s' % (TermTitleShow, TermSeason)],
											},
										},

										# Dutch
										Language.CodeDutch : {
											QueryTypeCollection : {
												QueryModeFull : ['%s verzameling' % TermTitleCollection, '%s collectie' % TermTitleCollection, '%s trilogie' % TermTitleCollection],
												QueryModeQuick : ['%s verzameling' % TermTitleCollection],
											},
											QueryTypeShow : {
												QueryModeFull : ['%s verzameling' % TermTitleShow, '%s collectie' % TermTitleShow],
												QueryModeQuick : ['%s verzameling' % TermTitleShow],
											},
											QueryTypeSeason : {
												QueryModeFull : ['%s seizoen %s' % (TermTitleShow, TermSeason)],
											},
										},

										# Spanish
										Language.CodeSpanish : {
											QueryTypeCollection : {
												QueryModeFull : ['%s completa' % TermTitleCollection, '%s colección' % TermTitleCollection, '%s trilogía' % TermTitleCollection],
												QueryModeQuick : ['%s completa' % TermTitleCollection, '%s colección' % TermTitleCollection],
											},
											QueryTypeShow : {
												QueryModeFull : ['%s completa' % TermTitleShow, '%s temporadas' % TermTitleShow, '%s colección' % TermTitleShow],
												QueryModeQuick : ['%s completa' % TermTitleShow, '%s temporadas' % TermTitleShow],
											},
											QueryTypeSeason : {
												QueryModeFull : ['%s temporada %s' % (TermTitleShow, TermSeason)],
											},
										},

										# Portuguese
										Language.CodePortuguese : {
											QueryTypeCollection : {
												QueryModeFull : ['%s completa' % TermTitleCollection, '%s coleção' % TermTitleCollection, '%s trilogia' % TermTitleCollection],
												QueryModeQuick : ['%s completa' % TermTitleCollection, '%s coleção' % TermTitleCollection],
											},
											QueryTypeShow : {
												QueryModeFull : ['%s completa' % TermTitleShow, '%s temporadas' % TermTitleShow, '%s coleção' % TermTitleShow],
												QueryModeQuick : ['%s completa' % TermTitleShow, '%s temporadas' % TermTitleShow],
											},
											QueryTypeSeason : {
												QueryModeFull : ['%s temporada %s' % (TermTitleShow, TermSeason)],
											},
										},

										# Italian
										Language.CodeItalian : {
											QueryTypeCollection : {
												QueryModeFull : ['%s collezione' % TermTitleCollection, '%s trilogia' % TermTitleCollection],
												QueryModeQuick : ['%s collezione' % TermTitleCollection],
											},
											QueryTypeShow : {
												QueryModeFull : ['%s stagioni' % TermTitleShow, '%s collezione' % TermTitleShow],
												QueryModeQuick : ['%s stagioni' % TermTitleShow],
											},
											QueryTypeSeason : {
												QueryModeFull : ['%s stagione %s' % (TermTitleShow, TermSeason)],
											},
										},

										# Russian
										Language.CodeRussian : {
											QueryTypeCollection : {
												QueryModeFull : ['%s трилогия' % TermTitleCollection, '%s trilogiya' % TermTitleCollection, '%s коллекция' % TermTitleCollection, '%s kollektsiya' % TermTitleCollection],
												QueryModeQuick : ['%s трилогия' % TermTitleCollection, '%s коллекция' % TermTitleCollection],
											},
											QueryTypeShow : {
												QueryModeFull : [u'%s сезоны' % TermTitleShow, u'%s sezony' % TermTitleShow, u'%s коллекция' % TermTitleShow, u'%s kollektsiya' % TermTitleShow],
												QueryModeQuick : [u'%s сезоны' % TermTitleShow, u'%s коллекция' % TermTitleShow],
											},
											QueryTypeSeason : {
												QueryModeFull : [u'%s сезон %s' % (TermTitleShow, TermSeason), u'%s sezon %s' % (TermTitleShow, TermSeason)],
												QueryModeQuick : [u'%s сезон %s' % (TermTitleShow, TermSeason)],
											},
										},
									}

	# Format - Encode
	FormatEncodeNone				= None		# No encoding. Spaces are treated as spaces.
	FormatEncodeQuote				= 'quote'	# URL encoding with special symbols and spaces escaped with %XX.
	FormatEncodePlus				= 'plus'	# URL encoding with special symbols escaped with %XX and spaces escaped with a plus sign.
	FormatEncodeMinus				= 'minus'	# Same as FormatEncodePlus, but "+" is replaced with "-".
	FormatEncodeDefault				= FormatEncodePlus

	# Format - Case
	FormatCaseNone					= None		# Keep the case as is.
	FormatCaseUpper					= 'upper'	# Make query all upper case.
	FormatCaseLower					= 'lower'	# Make query all lower case.
	FormatCaseDefault				= FormatCaseNone

	# Format - Include
	FormatIncludeAll				= 'all'		# Include all characters in the query.
	FormatIncludeBasic				= 'basic'	# Include only ASCII alphabet and numbers. All symbols and unicodes are removed.
	FormatIncludeEncode				= 'encode'	# Same as FormatIncludeBasic, but also allow the encoding symbol. "+" for FormatEncodePlus, "-" for FormatEncodeMinus, "% for FormatEncodeQuote.
	FormatIncludeDefault			= FormatIncludeAll

	# Format - Charset
	# Values must correspond with Python encoding type.
	# Can use Python aliases, since these values are passed to the networker for the HTTP header with "charset=xxx".
	# https://docs.python.org/2.4/lib/standard-encodings.html
	# https://webcheatsheet.com/html/character_sets_list.php
	FormatSetUtf8					= Networker.CharsetUtf8		# UTF-8 character set.
	FormatSetWin1251				= Networker.CharsetWin1251	# Windows-1251 character set.
	FormatSetDefault				= FormatSetUtf8

	# Account

	AccountAuthorizationBasic		= Networker.AuthorizationBasic
	AccountAuthorizationBearer		= Networker.AuthorizationBearer

	AccountModeAll					= 'all'		# Apply authentication duuring both scraping and resolving.
	AccountModeScrape				= 'scrape'	# Apply authentication before starting to scrape.
	AccountModeResolve				= 'resolve'	# Apply authentication when the link is resolved.
	AccountModeDefault				= AccountModeScrape

	AccountAuthentication			= {}

	# Stream
	# Many Russian titles contain the director's name (before the year). Make the title matching/validation more lenient for Russian providers, otherwise many or even all links are rejected.
	# And Russian titles often have a bunch of other keywords early in the file name.
	# Eg: Аватар / Avatar (Джеймс Кэмерон) [2009, фантастика, боевик, триллер, драма, приключения, BDRip 1080p]
	# Eg: Аватар 3Д / Avatar 3D (Джеймс Кэмерон / James Cameron) [2009 г., фантастика, боевик, триллер, драма, приключения, BDrip 720p] OverUnder / Вертикальная стереопара
	StreamAdjustRussian				= 0.7

	# Request - Error
	RequestError					= {}
	RequestCloudflare				= {}

	# Request - Count
	RequestCountSemaphore			= {}

	# Request - Delay
	RequestDelayLock				= {}
	RequestDelayCurrent				= {}
	RequestDelayExtra				= 0.05 # Extra time to sleep to ensure the delay is always met.

	# Other

	DetailsData						= {}

	def __init__(self, **kwargs):
		ProviderBase.__init__(self, **kwargs)

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		replacements				= None,						# A dictionary of additional string formatting replacements.

		queryYear					= True,						# Wether or not to include the year in movie searches.

		queryMovie					= None,						# The custom query format for movies. Replaces the default formats. If not provided, the default format is use
		queryCollection				= None,						# The custom query format for collections. Replaces the default formats. If not provided, the default format is used.
		queryShow					= None,						# The custom query format for shows. Replaces the default formats. If not provided, the default format is used.
		querySeason					= None,						# The custom query format for seasons. Replaces the default formats. If not provided, the default format is used.
		queryEpisode				= None,						# The custom query format for episodes. Replaces the default formats. If not provided, the default format is used.
		querySpecial				= None,						# The custom query format for special episodes. Replaces the default formats. If not provided, the default format is used.

		queryExtraMovie				= None,						# Addtional custom query format for movies. Added to the default formats.
		queryExtraCollection		= None,						# Addtional custom query format for collections. Added to the default formats.
		queryExtraShow				= None,						# Addtional custom query format for shows. Added to the default formats.
		queryExtraSeason			= None,						# Addtional custom query format for seasons. Added to the default formats.
		queryExtraEpisode			= None,						# Addtional custom query format for episodes. Added to the default formats.
		queryExtraSpecial			= None,						# Addtional custom query format for special episodes. Added to the default formats.

		formatEncode				= FormatEncodeDefault,		# The encoding of the query string. If not provided, the default encoding is used.
		formatCase					= FormatCaseDefault,		# The case of the query string. If not provided, the default case is used.
		formatInclude				= FormatIncludeDefault,		# The type of characters to include/removed from the query string.
		formatSet					= FormatSetDefault,			# The character set encoding for the query string.

		# The search query added to the link. All the query replacements are available (eg: {title}, {id_imdb}, etc).
		# Can be a single query, or a list of queries:
		#	1. String: GET query.
		#	2. Dictionary: {method : <optional GET/POST/etc, path : <URL path>, data : <dictionary of GET/POST parameters}.
		#	3. List of strings/dictionaries: These are fallback queries. Try the first query and if it has missing replacements, continue to the next.
		#	4. List-of-lists of strings/dictionaries: Same as fallback list, but each query in the nested list will be used (AND instead of OR). Eg: [..., [q1, q2], ...] both q1 and q2 are executed. Eg: two different queries for special episodes (one searching by number, one by title).
		searchQuery					= None,

		searchConcurrency			= None,						# Wether or not to run the extraction of individual items in parallel. Only set this to True if absolutely necessary, since thread creation has computational overhead. This is useful if each item requires further requests to get more metadata.
		searchCategory				= None,						# A list of movie/show categories.
		searchCategoryMovie			= None,						# A list of movie categories.
		searchCategoryShow			= None,						# A list of show categories.

		# Authentication:
		#	Dictionary: {
		#		ProcessMode (string)			# Optional authentication mode. Authenticate before scraping, before resolving, or both.
		#		ProcessAuthorization (string)	# Optional HTTP Authorization. If "Basic" will use the account username/email and password. If "Bearer" will use the account key.
		#		ProcessIterations (integer)		# How many times the request should be executed (default: 1). With every iteration, the cookies from the previous iteration are passed on. YggTorrent needs to call the login request twice, first time to get a cookie, and the second time to authenticate the cookie.
		#		ProcessRequest (dictionary)		# Optional request to make to retrieve the data.
		#		ProcessExtract (dictionary)		# Optional instructions to extract the data from the request.
		#		ProcessFixed (dictionary)		# Optional fixed headers, cookies, and data to add to the authentication, besides those that are extracted.
		#		ProcessValidate (dictionary)	# Optional instructions to validate the extracted data to determine if the authentication was successful. If not provided (default), will check that the request was succesful (no HTTP errors) and all extracted attributes have a value.
		#	}
		#
		# ProcessRequest:
		#	String: GET URL of the request.
		#	Dictionary: {
		#		RequestMethod (string)			# Optional HTTP method.
		#		RequestLink (string)			# Optional authentication link (excluding the query) if it is different to the main link. Either a link or a query (or both) must be provided.
		#		RequestPath (string)			# Optional query path appended to the link for the authentication request.
		#		RequestData (dictionary)		# Optional GET/POST parameters to add to the authentication request.
		#		RequestCookies (dictionary)		# Optional cookies to add to the authentication request.
		#		RequestHeaders (dictionary)		# Optional headers to add to the authentication request.
		#	}
		#
		# ProcessExtract:
		#	String: Equivalent to {RequestData : xyz}
		#	Dictionary: {
		#		RequestData (string/list/list-of/lists/dictionary)		# Optional JSON keys or regular expressions to extract the authentication data from the body.
		#		RequestCookies (bool/string/list/dictionary)			# Optional cookie names to extract the authentication data from the cookies.
		#		RequestHeaders (bool/string/list/dictionary)			# Optional header names to extract the authentication data from the headers.
		#	}
		#	Data can be JSON keys or regular expressions. If it contains round brackets () or starts/ends with ^/$ it is assumed to be regular expressions, otherwise it is assumed to be JSON keys.
		#	Data, Cookies, Headers can be in one of these formats:
		#	None (All): Do not use/extract.
		#	True (Cookies/Headers): Extracts all cookies/headers.
		#		Stored in: cookies[name]/headers[name]
		#		Formatted to: "authentication" (first value) and "authentication_<name>"
		#	String (Cookies/Headers): Extracts a single cookies.
		#		Stored in: cookies[name]
		#		Formatted to: "authentication" and "authentication_<name>"
		#	String (Data): Extracts a single value.
		#		Stored in: data[0]
		#		Formatted to: "authentication" and "authentication_0"
		#	List (Cookies/Headers): Extracts multiple values from the list of cookie/header names.
		#		Stored in: cookies[name]/headers[name]
		#		Formatted to: "authentication" (first value) and "authentication_<name>"
		#	List (Data-JSON): Extracts a single value from the list of keys.
		#		Stored in: data[0]
		#		Formatted to: "authentication" and "authentication_0"
		#	List (Data-EXP): Extracts multiple values from the list of expressions.
		#		Stored in: data[index]
		#		Formatted to: "authentication" (first value) and "authentication_<index>"
		#	List-Of-Lists (Data-JSON): Extracts multiple values for list of keys in the list.
		#		Stored in: data[index]
		#		Formatted to: "authentication" (first value) and "authentication_<index>"
		#	Dictionary (Cookies/Headers): Extracts multiple values. The dictionary keys are the new names under which the dictionary/cookie/header values are stored.
		#		Stored in: cookies[name]/headers[name]
		#		Formatted to: "authentication" (first value) and "authentication_<name>"
		#	Dictionary (Data): Extracts multiple values. The dictionary keys are the new names. The dictionary values are the JSON keys or expressions.
		#		Stored in: data[name]
		#		Formatted to: "authentication" (first value) and "authentication_<name>"
		#	Dictionary with lists (Cookies/Headers/Data): Same as the other "Dictionary" modes, but the dictionary values are lists of expression. The expressions are executed recursivley, extracting the groups and formatting it into the next expression. If the last expression has multiple matches, they are joined into a single string. Check BitLord for an example.
		#		Stored in: cookies/headers/data[name]
		#		Formatted to: "authentication" (first value) and "authentication_<name>"
		#
		# ProcessFixed:
		#	Dictionary: {
		#		RequestData (dictionary)		# Optional fixed GET/POST parameters to add to requests.
		#		RequestCookies (dictionary)		# Optional fixed cookies to add to requests.
		#		RequestHeaders (dictionary)		# Optional fixed headers to add to requests.
		#	}
		#
		# ProcessValidate:
		#	Dictionary: {
		#		RequestData (string/dictionary)		# Optional dictionary where the values are regular expressions. If string, matches the entire data.
		#		RequestCookies (string/dictionary)	# Optional dictionary where the values are regular expressions. If string, matches all cookies.
		#		RequestHeaders (string/dictionary)	# Optional dictionary where the values are regular expressions. If string, matches all headers.
		#	}
		accountAuthentication		= None,

		# A request, like "accountAuthentication", to verify that the authentication/account is valid.
		# By default, the "accountAuthentication" will fail if the request returns an HTTP error code or if any of the specified extracted attributes are empty.
		# Additionally "ProcessValidate" can be added to "accountAuthentication" to check for specfic values in the extracted attributes.
		# If both the above options are not enough, an "accountVerification" request can be specified.
		# This is useful if the only way to determine if the authetication was succesful is to request a completely differnt page to the one in "accountAuthentication" (eg: request an account webpage and extract a value from there).
		accountVerification			= None,

		requestCount				= None,						# Some servers have a maximum number of concurrent connections allowed per client. If too many connections come in at the same time, such as when the subpages have to be requested, they are aborted by the server.If None, thene an infinite number of parallel connections can be made.
		requestDelay				= None,						# Some APIs have limits on how many requests can be made within a time period. Set this value to the number of seconds between requests. Assumes that the maximum number of concurrent connections is 1. If None, then there is no delay.

		certificateCurve			= None,						# The Elliptic Curve Cryptography (ECC to use for SSL/TLS certificates. More info in cloudflare.py.

		# All the retry attributes can be a single value or a list of values.
		# A single value only deals with a single retry error.
		# A list of values can handle multiple/different errors, each with their own count and delay.
		retryCount					= None,						# The number of retries if a network request fails.
		retryDelay					= None,						# The delay in number of seconds to wait between retries. This is added on top of "delay".
		retryError					= None,						# The HTTP error code that triggers a retry. If True, all errors are used. A single code or list of codes can be passed in. If the code is shorter than 3 digits, codes starting with those digits are used. Eg [41, 50] will match 41x and 50x codes.
		retryExpression				= None,						# A regular expression on the response body that triggers a retry.

		offsetStart					= None, 					# The number at which pages start.
		offsetIncrease				= None,						# The number to increase for each new page.

		streamAdjust				= None,						# An adjustment ratio to multiple title validation thresholds with during stream file name validation. Used to make file name matching stricter (values in (1,inf]) or more lenient (value in [0,1)).
		streamTime					= None,						# A custom date/time format for the sourceTime attribute. Should be used if the provider returns a US date format (where the month is first).

		propagate					= True,
		**kwargs
	):
		try:
			if propagate:
				ProviderBase.initialize(self,
					scrapeQuery		= None,
					scrapePage		= False if (offsetStart is None and offsetIncrease is None) else None,
					scrapeRequest	= None,

					**kwargs
				)

			if searchQuery is None: searchQuery = []
			if not Tools.isArray(searchQuery): searchQuery = [searchQuery]

			searchCategoryAll = None
			if searchCategory:
				if not searchCategoryMovie: searchCategoryMovie = Tools.copy(searchCategory)
				if not searchCategoryShow: searchCategoryShow = Tools.copy(searchCategory)
			if searchCategoryMovie or searchCategoryShow:
				if searchCategoryMovie and not Tools.isArray(searchCategoryMovie): searchCategoryMovie = [searchCategoryMovie]
				if searchCategoryShow and not Tools.isArray(searchCategoryShow): searchCategoryShow = [searchCategoryShow]

				searchCategoryAll = []
				if searchCategoryMovie: searchCategoryAll.extend(searchCategoryMovie)
				if searchCategoryShow: searchCategoryAll.extend(searchCategoryShow)

			if replacements: replacements = {self.replaceClean(key) : value for key, value in replacements.items()}

			if retryError and not retryError is True:
				if not Tools.isArray(retryError): retryError = [retryError]
				if Tools.isArray(retryError[0]): retryError = [[str(error) for error in errors] for errors in retryError]
				else: retryError = [str(error) for error in retryError]

			if accountAuthentication:
				if not ProviderBase.ProcessMode in accountAuthentication or not accountAuthentication[ProviderBase.ProcessMode]:
					accountAuthentication[ProviderBase.ProcessMode] = ProviderWeb.AccountModeDefault
				if not ProviderBase.ProcessIterations in accountAuthentication or not accountAuthentication[ProviderBase.ProcessIterations]:
					accountAuthentication[ProviderBase.ProcessIterations] = 1
				if ProviderBase.ProcessExtract in accountAuthentication and not Tools.isDictionary(accountAuthentication[ProviderBase.ProcessExtract]):
					accountAuthentication[ProviderBase.ProcessExtract] = {ProviderBase.RequestData : accountAuthentication[ProviderBase.ProcessExtract]}
				if ProviderBase.ProcessValidate in accountAuthentication and not Tools.isDictionary(accountAuthentication[ProviderBase.ProcessValidate]):
					accountAuthentication[ProviderBase.ProcessValidate] = {ProviderBase.RequestData : accountAuthentication[ProviderBase.ProcessValidate]}

			if accountVerification:
				if ProviderBase.ProcessExtract in accountVerification and not Tools.isDictionary(accountVerification[ProviderBase.ProcessExtract]):
					accountVerification[ProviderBase.ProcessExtract] = {ProviderBase.RequestData : accountVerification[ProviderBase.ProcessExtract]}

			if streamAdjust is None:
				if self.modeRussian(): streamAdjust = ProviderWeb.StreamAdjustRussian

			data = {
				'replacements' : replacements,

				'query' : {
					'movie' : {'data' : [], 'template' : {'custom' : queryMovie, 'extra' : queryExtraMovie, 'year' : queryYear}},
					'collection' : {'data' : [], 'template' : {'custom' : queryCollection, 'extra' : queryExtraCollection}},
					'show' : {'data' : [], 'template' : {'custom' : queryShow, 'extra' : queryExtraShow}},
					'season' : {'data' : [], 'template' : {'custom' : querySeason, 'extra' : queryExtraSeason}},
					'episode' : {'data' : [], 'template' : {'custom' : queryEpisode, 'extra' : queryExtraEpisode}},
					'special' : {'data' : [], 'template' : {'custom' : querySpecial, 'extra' : queryExtraSpecial}},
				},

				'format' : {
					'encode' : formatEncode,
					'case' : formatCase,
					'include' : formatInclude,
					'set' : formatSet,
				},

				'search' : {
					'query' : searchQuery,
					'concurrency' : searchConcurrency,
					'category' : {
						'all' : searchCategoryAll,
						'movie' : searchCategoryMovie,
						'show' : searchCategoryShow,
					},
				},

				'account' : {
					'authentication' : accountAuthentication,
					'verification' : accountVerification,
				},

				'request' : {
					'count' : requestCount,
					'delay' : requestDelay,
				},

				'certificate' : {
					'curve' : certificateCurve,
				},

				'retry' : {
					'count' : retryCount,
					'delay' : retryDelay,
					'error' : retryError,
					'expression' : retryExpression,
				},

				'offset' : {
					'start' : offsetStart,
					'increase' : offsetIncrease,
				},

				'stream' : {
					'adjust' : streamAdjust,
					'time' : streamTime,
				},
			}

			self.dataUpdate(data)
			self.initializeReplace()
			self.requestClear()
		except: self.logError()

	def initializeReplace(self):
		# Format replacements in certain attributes.
		# More attributes might have to be added later on.
		# Allows to eg use a custom setting to change the retry count.
		# Eg: ApiBay separate vs combined categories.

		def _replace(value, replacements):
			new = value
			if Tools.isArray(value):
				new = []
				for val in value:
					try:
						cleaned = self.replaceClean(val)
						if val == cleaned:
							new.append(val)
						else:
							if cleaned in replacements and not Tools.isString(replacements[cleaned]): result = replacements[cleaned]
							else: result = self.replace(data = val, replacements = replacements)
							if Tools.isArray(result): new.extend(result)
							else: new.append(result)
					except: pass
			elif Tools.isString(value):
				try:
					cleaned = self.replaceClean(value)
					if not value == cleaned:
						if cleaned in replacements and not Tools.isString(replacements[cleaned]): new = replacements[cleaned]
						else: new = self.replace(data = value, replacements = replacements)
				except: pass
			return new

		attributes = [
			['search', 'category'],
			['request'],
			['retry'],
			['offset'],
		]
		replacements = self.replacements()
		for attribute in attributes:
			value = Tools.dictionaryGet(dictionary = self.mData, keys = attribute)
			if Tools.isDictionary(value):
				for key, val in value.items():
					Tools.dictionarySet(dictionary = self.mData, keys = attribute + [key], value = _replace(val, replacements))
			else:
				Tools.dictionarySet(dictionary = self.mData, keys = attribute, value = _replace(value, replacements))

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		ProviderWeb.RequestError = {}
		ProviderWeb.RequestCloudflare = {}
		ProviderWeb.RequestCountSemaphore = {}
		ProviderWeb.RequestDelayLock = {}
		ProviderWeb.RequestDelayCurrent = {}

		ProviderWeb.DetailsData = {}

		if settings:
			ProviderWeb.AccountAuthentication = {}

	##############################################################################
	# VERIFY
	##############################################################################

	def verifyScrapeStatus(self):
		if self.id() in ProviderWeb.RequestCloudflare: return ProviderWeb.VerifyLimited, ProviderWeb.VerifyCloudflare
		return None, None

	##############################################################################
	# REQUEST
	##############################################################################

	def request(self, link = None, path = None, subdomain = None, method = None, data = None, headers = None, cookies = None, certificate = None, retries = None, scrape = False):
		try:
			if not self.timerCheck(): return None

			# Exclude other requests, like account authentication, from the request limit.
			if scrape and not self.scrapeRequestAllow(increase = True): return None

			id = self.id()

			# Previous request failed with a Cloudflare error.
			if id in ProviderWeb.RequestError: return None

			networker = Networker()
			set = False

			if method is None: method = Networker.MethodGet

			if data is None: data = {}
			auth = self.accountAuthenticationData()
			if auth: data.update(auth)

			if headers is None: headers = {}
			auth = self.accountAuthenticationHeaders()
			if auth: headers.update(auth)

			if cookies is None: cookies = {}
			auth = self.accountAuthenticationCookies()
			if auth: cookies.update(auth)

			curve = None
			if certificate is None: certificate = self.certificate()
			if certificate and ProviderBase.RequestCurve in certificate: curve = certificate[ProviderBase.RequestCurve]

			retryCount = self.retryCount()
			if retryCount:
				retryDelay = self.retryDelay()
				if not retryDelay: retryDelay = 0
				retryError = self.retryError()
				if retryError and not retryError is True: retryError = tuple(retryError)
				retryExpression = self.retryExpression()

			fixed = not link is None
			if fixed:
				if path: link = Networker.linkJoin(link, path)
			else:
				enabled = self.settingsGlobalMirrorEnabled()
				limit = self.settingsGlobalMirrorLimit()
				counter = 0
				link = self.linkPrevious()
				if link:
					link = self.linkPath(link = link, path = path)
				else:
					counter += 1
					link = self.linkNext(link = link, path = path)

			requestCount = self.requestCount()
			if requestCount:
				ProviderWeb.RequestCountSemaphore[id].acquire()

			requestDelay = self.requestDelay()
			if requestDelay:
				ProviderWeb.RequestDelayLock[id].acquire()
				difference = Time.timestamp() - ProviderWeb.RequestDelayCurrent[id]
				if difference <= requestDelay: Time.sleep((requestDelay - difference) + ProviderWeb.RequestDelayExtra)
				requestDelay += ProviderWeb.RequestDelayExtra

			replacements = self.accountAuthenticationFormat()

			concurrency = self.settingsGlobalConcurrencyConnection()

			headersNew = None
			cookiesNew = None
			dataNew = None

			error = False

			while link:
				timeout = self.timerRequest()
				if not timeout:
					networker = None
					break

				link = self.replace(data = link, replacements = replacements)
				if subdomain:
					subdomainNew = self.replace(data = subdomain, replacements = replacements)
					linkNew = Networker.linkSubdomain(link = link, subdomain = subdomainNew)
				else:
					linkNew = link

				domain = Networker.linkDomain(link = link, subdomain = False, topdomain = True, ip = True, scheme = False)

				# Previous request failed with a timeout error.
				if domain in ProviderWeb.RequestError: break

				replacementsNew = Tools.dictionaryMerge(replacements, {
					self.replaceClean(ProviderWeb.TermLinkFull) : link,
					self.replaceClean(ProviderWeb.TermLinkParameters) : Networker.linkPath(link = link, parameters = True),
					self.replaceClean(ProviderWeb.TermLinkPath) : Networker.linkPath(link = link, parameters = False),
					self.replaceClean(ProviderWeb.TermLinkHost) : Networker.linkDomain(link = link, subdomain = True, topdomain = True, ip = True, scheme = True),
					self.replaceClean(ProviderWeb.TermLinkDomain) : domain,
				})

				if headers:
					headersNew = self.replace(data = Tools.copy(headers), replacements = replacementsNew)
				if cookies:
					cookiesNew = self.replace(data = Tools.copy(cookies), replacements = replacementsNew)
				if data:
					dataNew = self.replace(data = Tools.copy(data), replacements = replacementsNew)

					# Encode here. Check if already encoded from the query string.
					# We force the encoding type, and then tell networker "encode = False".
					set = self.formatSet()
					encode = self.formatEncode()
					if encode:
						encodePlus = encode == ProviderWeb.FormatEncodePlus
						for key, value in dataNew.items():
							if Tools.isArray(value): value = [Networker.linkQuote(data = val, plus = encodePlus, check = True) for val in value]
							else: value = Networker.linkQuote(data = value, plus = encodePlus, check = True)
							dataNew[key] = value

				#self.log('PROVIDER REQUEST: Method [%s] - Link [%s] - Data [%s] - Headers [%s] - Cookies [%s]' % (str(method), str(linkNew), Converter.jsonTo(dataNew), Converter.jsonTo(headersNew), Converter.jsonTo(cookiesNew)), developer = True)
				self.statisticsUpdateSearch(request = True)
				networker.request(link = linkNew, method = method, data = dataNew, headers = headersNew, cookies = cookiesNew, curve = curve, encode = False, charset = set, timeout = Networker.timeoutAdjust(timeout), concurrency = concurrency, debug = self.name())

				# If there are Cloudflare errors, prevent all future requests to the domain, since they will most likley also fail with a Cloudflare error.
				# Rather do this on a per-provider basis, instead of a per-domain basis, since mirror domains typically point to the same server.
				# Specifically for: Detected a Cloudflare version 2 challenge, This feature is not available in the opensource (free) version.
				# Queries with alias titles are execute concurrently and will not benefit from this.
				if networker.responseErrorCloudflare():
					ProviderWeb.RequestError[id] = True
					ProviderWeb.RequestCloudflare[id] = True
					error = True
					break
				# If there are timeout errors, add the domain, since other domains might not have the issue.
				# Timeouts (eg: 45 seconds) can drastically increase scraping time, since some providers might take very long to finish.
				elif networker.responseErrorTimeout():
					ProviderWeb.RequestError[domain] = True
					error = True
					break

				if retryCount:
					retryIndex = 0
					retryPrevious = retryIndex
					countRetry = 0

					if Tools.isArray(retryCount):
						try: countBase = retryCount[retryIndex]
						except: countBase = retryCount[0]
					else:
						countBase = retryCount

					if Tools.isArray(retryDelay):
						try: delay = retryDelay[retryIndex]
						except: delay = retryDelay[0]
					else:
						delay = retryDelay

					while (countBase - countRetry) > 0:
						timeout = self.timerRequest()
						if not timeout:
							networker = None
							break

						retry = False

						# HTTP errors
						if retryError:
							errorType = networker.responseErrorType()
							errorCode = str(networker.responseErrorCode())
							if Tools.isArray(retryError):
								for i in range(len(retryError)):
									if retryError[i] is True and errorType:
										retry = True
										retryIndex = i
										break
									elif errorCode.startswith(retryError[i]):
										retry = True
										retryIndex = i
										break
							else:
								if retryError is True and errorType: retry = True
								elif errorCode.startswith(retryError): retry = True

						# Expressions
						if not retry and retryExpression:
							body = networker.responseDataText()
							if Tools.isString(body):
								if Tools.isArray(retryExpression):
									for i in range(len(retryExpression)):
										if Regex.match(data = body, expression = retryExpression[i], flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines):
											retry = True
											retryIndex = i
											break
								else:
									if Regex.match(data = body, expression = retryExpression, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines): retry = True

						if not retry: break

						if Tools.isArray(retryCount):
							try: countBase = retryCount[retryIndex]
							except: countBase = retryCount[0]
						if Tools.isArray(retryDelay):
							try: delay = retryDelay[retryIndex]
							except: delay = retryDelay[0]

						# Only increase the retry count if the detected error stays the same.
						if retryIndex == retryPrevious: countRetry += 1
						retryPrevious = retryIndex

						if requestDelay: Time.sleep(requestDelay + (delay if delay else 0))
						elif delay: Time.sleep(delay)

						#self.log('PROVIDER RETRY: Method [%s] - Link [%s] - Data [%s] - Headers [%s] - Cookies [%s]' % (str(method), str(linkNew), Converter.jsonTo(dataNew), Converter.jsonTo(headersNew), Converter.jsonTo(cookiesNew)), developer = True)
						networker.request(link = linkNew, method = method, data = dataNew, headers = headersNew, cookies = cookiesNew, curve = curve, encode = False, charset = set, timeout = Networker.timeoutAdjust(timeout), concurrency = concurrency, debug = self.name())

						if networker.responseErrorCloudflare():
							ProviderWeb.RequestError[id] = True
							error = True
							break
						elif networker.responseErrorTimeout():
							ProviderWeb.RequestError[domain] = True
							error = True
							break

				if fixed or error or networker is None:
					break
				else:
					result, _ = self.linkVerifyConnection(networker, special = not scrape)
					if result:
						self.linkPreviousSet(link)
						break
					elif not enabled or counter > limit or not self.timerAllow() or self.stopped():
						break

				# Do not continue with mirror domains if the error was caused by servers rejecting too many simultaneous connections.
				# Because too many connections means the domain is working and we do not want to waste time iterating over mirrors.
				if networker and networker.responseErrorConnections(): break

				if requestDelay: Time.sleep(requestDelay)

				counter += 1
				link = self.linkNext(link = link, path = path)
				if link and retries: retries[0] += 1

			if requestCount:
				ProviderWeb.RequestCountSemaphore[id].release()

			if requestDelay:
				ProviderWeb.RequestDelayCurrent[id] = Time.timestamp()
				ProviderWeb.RequestDelayLock[id].release()

			return networker
		except:
			self.logError()
			return None

	def requestText(self, link = None, path = None, subdomain = None, method = None, data = None, headers = None, cookies = None, certificate = None, scrape = False):
		# Use bytes and not text, since there are special characters (like the yellow star) in file names. Returning responseDataText() converts these characters to some other weird characters.
		# Do not work with bytes, because providers do string processing on the var (eg: TorrentProject -> processRequest()).
		# Instead, get the bytes and manual convert to unicode. The special icon characters are in any case removed in streams.py.
		#try: return self.request(link = link, path = path, subdomain = subdomain, method = method, data = data, headers = headers, cookies = cookies, scrape = scrape).responseDataBytes()
		#except: return None

		try: return self.request(link = link, path = path, subdomain = subdomain, method = method, data = data, headers = headers, cookies = cookies, certificate = certificate, scrape = scrape).responseDataText()
		except: return None

	def requestJson(self, link = None, path = None, subdomain = None, method = None, data = None, headers = None, cookies = None, certificate = None, scrape = False):
		try: return self.request(link = link, path = path, subdomain = subdomain, method = method, data = data, headers = headers, cookies = cookies, certificate = certificate, scrape = scrape).responseDataJson()
		except: return None

	def requestExtract(self, data = None, request = None, extract = None, fixed = None):
		try:
			def _requestExtractClean(extract):
				if not Tools.isDictionary(extract):
					if not Tools.isArray(extract): extract = [extract]
					extract = {i if _requestExtractExpression( extract[i]) else extract[i] : extract[i] for i in range(len(extract))}
				return extract

			def _requestExtractExpression(extract):
				return ('(' in extract and ')' in extract) or extract.startswith('^') or extract.endswith('$')

			def _requestExtractRecursive(value, primary = None, secondary = None):
				result = None
				for data in [primary, secondary]:
					if data:
						result = []
						for val in value:
							try: val = val % tuple(result)
							except: pass
							result = Regex.extract(data = data, expression = val, group = None, all = True)
							if not result: break
						if result: break
				if result: result = ''.join(result)
				return result

			if data:
				if not request:
					try: request = data[ProviderBase.ProcessRequest]
					except: pass
				if not extract:
					try: extract = data[ProviderBase.ProcessExtract]
					except: pass
				if not fixed:
					try: fixed = data[ProviderBase.ProcessFixed]
					except: pass

			result = {ProviderBase.RequestData : {}, ProviderBase.RequestCookies : {}, ProviderBase.RequestHeaders : {}}

			if fixed:
				request = Tools.copy(request)
				for key, value in fixed.items():
					if not key in request: request[key] = value
					else: request[key].update(value)

			if Tools.isDictionary(request): networker = self.request(**request)
			else: networker = self.request(link = request)
			result['networker'] = networker
			bytes = networker.responseDataText()

			try: data = extract[ProviderBase.RequestData]
			except: data = None
			if data:
				value = data
				if Tools.isDictionary(value): value = list(data.values())[0]
				if Tools.isArray(value): value = value[0]
				if Tools.isArray(value): value = value[0]

				if _requestExtractExpression(value):
					values = bytes
					if values:
						data = _requestExtractClean(data)
						for key, value in data.items():
							if not key in result[ProviderBase.RequestData]:
								if Tools.isArray(value):
									value = _requestExtractRecursive(value = value, primary = values)
								else:
									value = Regex.extract(data = values, expression = value)
								if not value is None: result[ProviderBase.RequestData][key] = value
				else:
					values = networker.responseDataJson()
					if values:
						data = _requestExtractClean(data)
						for key, value in data.items():
							if not Tools.isArray(value): data[key] = [value]
						for key, value in data.items():
							if not key in result[ProviderBase.RequestData]:
								result[ProviderBase.RequestData][key] = Tools.dictionaryGet(values, value)

			for type in [ProviderBase.RequestCookies, ProviderBase.RequestHeaders]:
				try: data = extract[type]
				except: data = None
				if data:
					if Tools.isString(data): data = {data : data}
					values = networker.response()[type]

					# The User-Agent is only in the request and not in the response headers.
					# Add it here, since some providers need it.
					if type == ProviderBase.RequestHeaders:
						try:
							agent = networker.request()[type][ProviderBase.RequestHeaderUserAgent]
							values[ProviderBase.RequestHeaderUserAgent] = agent
						except: pass

					valuesData = None
					if data is True:
						result[type] = values
					else:
						data = _requestExtractClean(data)
						for key, value in data.items():
							if not key in result[type]:
								if Tools.isArray(value):
									if valuesData is None: valuesData = Converter.jsonTo(values)
									result[type][key] = _requestExtractRecursive(value = value, primary = valuesData, secondary = bytes)
								else:
									if _requestExtractExpression(value):
										if valuesData is None: valuesData = Converter.jsonTo(values)
										result[type][key] = Regex.extract(data = valuesData, expression = value)
									else:
										result[type][key] = values[value]

			return result
		except: self.logError()
		return None

	def requestCount(self):
		return self.mData['request']['count']

	def requestDelay(self):
		return self.mData['request']['delay']

	def requestClear(self):
		id = self.id()

		if self.requestCount():
			if not id in ProviderWeb.RequestCountSemaphore: ProviderWeb.RequestCountSemaphore[id] = Semaphore(self.requestCount())

		if self.requestDelay():
			ProviderWeb.RequestDelayCurrent[id] = 0
			if not id in ProviderWeb.RequestDelayLock: ProviderWeb.RequestDelayLock[id] = Lock()

	##############################################################################
	# CERTIFICATE
	##############################################################################

	def certificate(self):
		return self.mData['certificate']

	def certificateCurve(self):
		return self.mData['certificate']['curve']

	##############################################################################
	# REPLACEMENTS
	##############################################################################

	def replacements(self):
		result = {}
		try:
			replacements = self.mData['replacements']
			if replacements:
				for key, value in replacements.items():
					custom = Regex.extract(data = key, expression = 'custom_(.*?)_(.*)', group = None)
					if custom:
						customId = custom[0]
						customLabel = custom[1]
						customSetting = self.custom(id = customId)
						if customSetting in value:
							result[key] = value[customSetting]
						else:
							# For dicitionary keys that are integers. The keys get cast to strings during JSON conversion.
							try:
								customSetting = int(customSetting)
								if customSetting in value:
									result[key] = value[customSetting]
							except: pass
					else:
						result[key] = value

			custom = self.customId()
			if custom:
				for id in custom:
					result[self.replaceClean(ProviderWeb.TermCustom) % id] = self.custom(id = id)

			result = {key : value for key, value in result.items() if not key is None and not value is None}
		except: self.logError()
		return result

	def replace(self, data, replacements, nested = False):
		if data:
			for key, value in replacements.items():
				if value is None: replacements[key] = ''
				elif Tools.isBoolean(value): replacements[key] = int(value)

			if Tools.isDictionary(data):
				# Convert bool to integer. If this is ever changed, make sure to update EasyNews.
				for key, value in data.items():
					if Tools.isBoolean(value): data[key] = int(value)
				result = {}
				if nested:
					for key, value in data.items():
						try:
							if Tools.isArray(value): value = [str(val).format(**replacements).format(**replacements) for val in value]
							else: value = str(value).format(**replacements).format(**replacements)
							result[str(key).format(**replacements).format(**replacements)] = value
						except: result[key] = ProviderBase.Skip
				else:
					for key, value in data.items():
						try:
							if Tools.isArray(value): value = [str(val).format(**replacements) for val in value]
							else: value = str(value).format(**replacements)
							result[str(key).format(**replacements)] = value
						except: result[key] = ProviderBase.Skip
				data = result
			elif Tools.isArray(data): # If the GET path is an array (eg: Lapumia provider).
				for i in range(len(data)):
					try:
						data[i] = data[i].format(**replacements)
						if nested: data[i] = data[i].format(**replacements)
					except: pass
			else:
				try:
					data = data.format(**replacements)
					if nested: data = data.format(**replacements)
				except: pass
		return data

	def replaceClean(self, value):
		try: return value.strip('{}')
		except: return value

	def replaceSearch(self, search, replacements):
		link = None
		subdomain = None
		path = None
		method = None
		headers = None
		cookies = None
		data = None

		# All {format} must have a corresponding value in the replacements.
		# Some values are only replaced later on (like authentication).
		if Tools.isString(search):
			path = search
			matches = Regex.extract(data = path, expression = '(\{.*?\})', group = None, all = True)
		else:
			try: link = search['link']
			except: pass
			try: subdomain = search['subdomain']
			except: pass
			try: path = search['path']
			except: pass
			try: method = search['method']
			except: pass
			try: headers = search['headers']
			except: pass
			try: cookies = search['cookies']
			except: pass
			try: data = search['data']
			except: pass

			matches = []
			if path:
				matches = Regex.extract(data = path, expression = '(\{.*?\})', group = None, all = True)
				if not matches: matches = []

			for item in [headers, cookies, data]:
				if item:
					for key, value in item.items():
						sub = Regex.extract(data = value, expression = '(\{.*?\})', group = None, all = True)
						if sub: matches.extend(sub)

		for match in matches:
			key = self.replaceClean(match)
			if not key in replacements: replacements[key] = match

		return link, subdomain, path, method, headers, cookies, data, replacements

	##############################################################################
	# LINK
	##############################################################################

	def linkVerify(self):
		result = None
		type = None
		if self.linkHas():
			retries = [0]
			networker = self.request(retries = retries)
			type = networker.responseErrorType()
			if type == Networker.ErrorConnection: return ProviderBase.VerifyFailure, type
			elif type and networker.responseError4xx() and not type == Networker.ErrorCloudflare: return ProviderBase.VerifySuccess, None # Ignore HTTP 4xx errors (eg 403 with TorrentApi). Server is up, just misformed request. Still detect Cloudflare 4xx errors.
			elif retries[0] > 0 or type: return ProviderBase.VerifyLimited, type # Ignore HTTP 4xx errors (eg 403 with TorrentApi).
			else: return ProviderBase.VerifySuccess, type
		return result, type

	##############################################################################
	# QUERY
	##############################################################################

	def queryMovie(self):
		return self.mData['query']['movie']['data']

	def queryCollection(self):
		return self.mData['query']['collection']['data']

	def queryShow(self):
		return self.mData['query']['show']['data']

	def querySeason(self):
		return self.mData['query']['season']['data']

	def queryEpisode(self):
		return self.mData['query']['episode']['data']

	def querySpecial(self):
		return self.mData['query']['special']['data']

	def queryInitialize(self, language = None):
		try:
			if not self.mData['query']['movie']['data']:
				self.lock() # Lock, since this function can be called multiple times for each subquery.
				if not self.mData['query']['movie']['data']:
					data = self.mData['query']
					self.mData['query']['movie']['data'] = self._queryInitialize(type = ProviderWeb.QueryTypeMovieYear if data['movie']['template']['year'] else ProviderWeb.QueryTypeMovie, default = data['movie']['template']['custom'], extra = data['movie']['template']['extra'], language = language)
					self.mData['query']['collection']['data'] = self._queryInitialize(type = ProviderWeb.QueryTypeCollection, default = data['collection']['template']['custom'], extra = data['collection']['template']['extra'], language = language)
					self.mData['query']['show']['data'] = self._queryInitialize(type = ProviderWeb.QueryTypeShow, default = data['show']['template']['custom'], extra = data['show']['template']['extra'], language = language)
					self.mData['query']['season']['data'] = self._queryInitialize(type = ProviderWeb.QueryTypeSeason, default = data['season']['template']['custom'], extra = data['season']['template']['extra'], language = language)
					self.mData['query']['episode']['data'] = self._queryInitialize(type = ProviderWeb.QueryTypeEpisode, default = data['episode']['template']['custom'], extra = data['episode']['template']['extra'], language = language)
					self.mData['query']['special']['data'] = self._queryInitialize(type = ProviderWeb.QueryTypeSpecial, default = data['special']['template']['custom'], extra = data['special']['template']['extra'], language = language)
				self.unlock()
		except: self.logError()

	def _queryInitialize(self, type, default, extra = None, language = None):
		result = []

		def _add(language = None, mode = None, universal = False, original = False, queries = None):
			if queries is None:
				try: queries = ProviderWeb.Queries[language][type][mode]
				except:
					try:
						mode = ProviderWeb.QueryModeFull
						queries = ProviderWeb.Queries[language][type][mode]
					except: pass
			else:
				if not Tools.isArray(queries): queries = [queries]

			if queries:
				for query in queries:
					result.append({'template' : query, 'language' : language, 'mode' : mode, 'universal' : universal, 'original' : original})

		if default is None:
			# Always include Universal queries.
			_add(language = Language.UniversalCode, mode = ProviderWeb.QueryModeFull, universal = True)

			if self.settingsGlobalKeywordEnabled():
				settingsEnglish = self.settingsGlobalKeywordEnglish()
				settingsEnglish = ProviderWeb.QueryModeQuick if settingsEnglish == ProviderBase.KeywordQuick else ProviderWeb.QueryModeFull if settingsEnglish == ProviderBase.KeywordFull else None
				settingsOriginal = self.settingsGlobalKeywordOriginal()
				settingsOriginal = ProviderWeb.QueryModeQuick if settingsOriginal == ProviderBase.KeywordQuick else ProviderWeb.QueryModeFull if settingsOriginal == ProviderBase.KeywordFull else None
				settingsNative = self.settingsGlobalKeywordNative()
				settingsNative = ProviderWeb.QueryModeQuick if settingsNative == ProviderBase.KeywordQuick else ProviderWeb.QueryModeFull if settingsNative == ProviderBase.KeywordFull else None
				settingsCustom = self.settingsGlobalKeywordCustom()
				settingsCustom = ProviderWeb.QueryModeQuick if settingsCustom == ProviderBase.KeywordQuick else ProviderWeb.QueryModeFull if settingsCustom == ProviderBase.KeywordFull else None

				# Include English queries.
				if settingsEnglish: _add(language = Language.EnglishCode, mode = settingsEnglish)

				# Include the language the title was originally released in.
				if settingsOriginal and language:
					_add(language = language, mode = settingsOriginal, original = True)

				# Include languages specified by the provider.
				if settingsNative:
					for lang in self.languages():
						if not lang == Language.UniversalCode and (not lang == Language.EnglishCode or not settingsEnglish):
							_add(language = lang, mode = settingsNative)

				# Include custom language specified by the user in the settings.
				if settingsCustom:
					lang = self.settingsGlobalKeywordLanguage()
					if not lang == Language.UniversalCode and (not lang == Language.EnglishCode or not settingsEnglish):
						_add(language = lang, mode = settingsCustom)
		else: _add(queries = default)

		if extra: _add(queries = extra)

		result = Tools.listUnique(result)
		return result

	def queryGenerate(self, media, titles, years, time, idImdb, idTmdb, idTvdb, numberSeason, numberEpisode, language, exact):
		queries = []
		queryTitles = []
		try:
			self.queryInitialize(language = language)

			try: mainProcessed = titles['processed']['main']
			except: mainProcessed = []
			try: originalProcessed = titles['processed']['original']
			except: originalProcessed = []
			try: originalSearch = titles['search']['original']
			except: originalSearch = []

			yearDefault = None
			if years:
				for i in ['common', 'original', 'mean']:
					if i in years and years[i]:
						yearDefault = years[i]
						break

			def _queryGenerate(search = None, query = None, format = None, title = None, year = None, pack = None, priority = None, universal = None, original = None, indexTitle = 0, indexQuery = 0):
				try:
					'''
						We try to push the queries that are likley to return better results before those who are less likley to return good results.
						Due to hardware and time contraints, there is a limit on the number of queries that will actually be executed.
						All queries beyond this limit will be cut off and not executed.
						We therefore need the best queries to be within this limit.
						This is mostly not an issue, since the limit is not exceeded in many cases.
						However, titles with aliases or foreign titles, might cause this limit to be reached quickly.

						We generally want the priority as follows:
							1. Episode numbers first (S01E01), including those of original title and variations.
							2. Generic season numbers (S01), including those of original title and variations.
							3. All other language-specific pack keywords.

						Eg: German show on Amazon:
							German title: "Luden: Könige Der Reeperbahn"
							English title: "The Pimp - No F***Ing Fairytale"
							Streams found:
								The.Pimp.No.Fucking.Fairytale.S01E01.MULTi.1080p.WEB.H264-AMB3R[eztv.re].mkv
								Luden.Konige.Der.Reeperbahn.S01.1080p.Ultradox
								Luden.Konige.Der.Reeperbahn.S01.720p.Ultradox
								Luden.Konige.Der.Reeperbahn.S01.400p.Ultradox

						Not only do we have German and English titles whhich both erturn results, but we also have variations:
							English:
								The Pimp - No F***Ing Fairytale
								The Pimp - No F Ing Fairytale
								The Pimp - No Fucking Fairytale (the censored *** part is filled in by modules -> core.py).
							German:
								Luden: Könige Der Reeperbahn
								Luden: Konige Der Reeperbahn
								Luden: Koenige Der Reeperbahn

						EXAMPLES:

						Amélie (2001):
							[
							  "Am%C3%A9lie 2001",
							  "Amelie 2001",
							  "Le Fabuleux Destin d Am%C3%A9lie Poulain 2001",
							  "Le Fabuleux Destin dAm%C3%A9lie Poulain 2001",
							  "Le Fabuleux Destin d Amelie Poulain 2001",
							  "Amlie 2001",
							  "Le Fabuleux Destin d Poulain 2001"
							]

						Harry Potter and the Sorcerer's Stone (2001):
							[
							  "Harry Potter and the Sorcerers Stone 2001",
							  "Harry Potter and the Sorcerer Stone 2001",
							  "Harry Potter and the Philosophers Stone 2001",
							  "Harry Potter and the Philosopher Stone 2001",
							  "Harry Potter collection",
							  "Harry Potter complete",
							  "Harry Potter pack",
							  "and the Philosophers Stone 2001",
							  "and the Philosopher Stone 2001",
							  "Harry Potter trilogy"
							]

						The Lord of the Rings: The Two Towers (2002):
							[
							  "The Lord of the Rings The Two Towers 2002",
							  "The Two Towers 2002",
							  "The Lord of the Rings collection",
							  "The Lord of the Rings complete",
							  "The Lord of the Rings pack",
							  "The Lord of the Rings trilogy"
							]

						The Pimp No fucking Fairytale (2023) S01E01:
							[
							  "The Pimp No fucking Fairytale S01E01",
							  "Luden K%C3%B6nige der Reeperbahn S01E01",
							  "Luden Konige der Reeperbahn S01E01",
							  "Luden Koenige der Reeperbahn S01E01",
							  "The Pimp No fucking Fairytale S01",
							  "Luden K%C3%B6nige der Reeperbahn S01",
							  "Luden Konige der Reeperbahn S01",
							  "Luden Koenige der Reeperbahn S01",
							  "The Pimp No F ing Fairytale S01E01",
							  ---------------------------------------------- (9 query limit cut off for high-performance devices)
							  "The Pimp No fucking Fairytale complete",
							  "Luden K%C3%B6nige der Reeperbahn Staffel 1",
							  "The Pimp No fucking Fairytale season 1",
							  "Luden Konige der Reeperbahn Staffel 1",
							  "The Pimp No fucking Fairytale collection",
							  "Luden K%C3%B6nige der Reeperbahn Staffeln",
							  "Luden Konige der Reeperbahn Staffeln",
							  "The Pimp No F ing Fairytale S01",
							  "Luden K%C3%B6nige der Reeperbahn Sammlung",
							  "Luden Konige der Reeperbahn Sammlung",
							  "The Pimp No fucking Fairytale pack",
							  "Luden Koenige der Reeperbahn Staffel 1",
							  "Luden Koenige der Reeperbahn Staffeln",
							  "The Pimp No fucking Fairytale series",
							  "Luden Koenige der Reeperbahn Sammlung",
							  "The Pimp No F ing Fairytale complete",
							  "The Pimp No F ing Fairytale season 1",
							  "The Pimp No F ing Fairytale collection",
							  "The Pimp No F ing Fairytale pack",
							  "The Pimp No F ing Fairytale series"
							]

						Game of Thrones (2011) S08E01:
							[
							  "Game of Thrones S08E01",
							  "Game of Thrones S08",
							  "Game of Thrones season 8",
							  "Game of Thrones complete",
							  "Game of Thrones collection",
							  "Game of Thrones pack",
							  "Game of Thrones series"
							]

						Dark (2017) S02E02:
							[
							  "Dark S02E02",
							  "Dark S02",
							  "Dark season 2",
							  "Dark Staffel 2",
							  "Dark complete",
							  "Dark collection",
							  "Dark pack",
							  "Dark series",
							  "Dark Staffeln",
							  "Dark Sammlung"
							]
					'''

					if query:
						if format: format = Tools.copy(format) # Changed in replace().
						if search is None: search = self.replace(data = query['template'], replacements = format)
						if universal is None: universal = query['universal']
						if original is None: original = query['original']

					originalIs = False
					originalRank = 0
					originalIndex = -1
					orignalSame = False

					if originalProcessed and title:
						titleQuery = title['query']
						for i in range(len(originalProcessed)):
							if originalProcessed[i] in titleQuery:
								originalIs = True
								originalRank = i + 1
								orignalSame = mainProcessed and (mainProcessed[0] in originalProcessed[i] or originalProcessed[i] in mainProcessed[0])
								break

					if originalSearch and search:
						for i in range(len(originalSearch)):
							if originalSearch[i] in search:
								originalIndex = i
								break

					# Only add original keywords to original titles/queries.
					# Also do not add English keywords to non-English titles/queries.
					# Eg: Do not add French keywords to the English titles. Only add French keywords to French titles.
					# NB: Check orignalSame, since we do not want to do this if the original title is the sasme as the other alias titles. Eg: the sshow "Dark".
					if universal is False and not orignalSame:
						if original is True and not originalIs: return
						elif original is False and originalIs: return

					priorities = priority
					if Tools.isArray(priority): priority = (priority[0] if indexTitle == 0 else (priority[0] + originalRank) if originalRank else (priority[1] + (priority[2] * indexTitle))) + indexQuery
					priority = (1000000000 + len(queries)) if priority is None else priority

					# Try to pull original pack queries above alias pack queries.
					if not orignalSame: priority *= ((0.8 if original else 2.0) * (1.0 if universal else 1.5) * (indexQuery + 1))

					# If there are non-ASCII characters in title, there can be a few variations of the title.
					# 1. The original UTF characters, or 2. The UTF characters mapped to ASCII characters, or 3. The UTF characters removed.
					# Only prioritize the first variations  of the original title, otherwise the season pack queries might not be used, since there are to many episode queries with title variations.
					if originalIndex >= 0: priority *= min(2.0, 1.05 + (0.05 * originalIndex * max(1, originalIndex - 1)))

					# Move higher-changed original title variations further down the list.
					if originalIndex > 1: priority *= 1.3 + (0.1 * originalIndex * max(1, originalIndex - 1))

					# Movie queries with universal numbering (S01 or S01E01) before local-language numbering (season 1 or saison 1").
					if not orignalSame and not language == Language.EnglishCode and Regex.match(data = search, expression = '\s\d+(?:e\d+|$|\s)'):
						if universal is True: multiplier = 0.4 if originalIndex >= 0 else 0.5
						elif universal is False: multiplier = (3.0 if pack else 1.6) if originalIndex >= 0 else (2.5 if pack else 1.5)
						else: multiplier = 1.0

						if originalIndex >= 0: priority *= multiplier * min(1.0, 0.6 + (0.1 * originalIndex * max(1, originalIndex - 1)))
						else: priority *= multiplier * 0.5

					if priorities:
						# Try to pull very short alias titles forward, since they probably will return more results.
						# Instead of: ["Am%C3%A9lie 2001","Le Fabuleux Destin d Am%C3%A9lie Poulain 2001","Le Fabuleux Destin dAm%C3%A9lie Poulain 2001","Le Fabuleux Destin d Amelie Poulain 2001","Amelie 2001","Amlie 2001","Le Fabuleux Destin d Poulain 2001"]
						# Rather we want: ["Am%C3%A9lie 2001","Amelie 2001","Le Fabuleux Destin d Am%C3%A9lie Poulain 2001","Le Fabuleux Destin dAm%C3%A9lie Poulain 2001","Le Fabuleux Destin d Amelie Poulain 2001","Amlie 2001","Le Fabuleux Destin d Poulain 2001"]
						if title and originalSearch and not original and universal:
							lengthCurrent = len(title['query'])
							lengthOriginal = len(originalSearch[0])
							if lengthCurrent < lengthOriginal * 0.8:
								priority = max(1, priority - max(priorities[1], priority * lengthCurrent / float(lengthOriginal)))

						# Move cut-off titles lower.
						# Eg: and the Philosophers Stone 2001
						expression = '^[a-z]{2,}\s'
						if Regex.match(data = search, expression = expression, flags = Regex.FlagNone) and (not originalSearch or not Regex.match(data = originalSearch[0], expression = expression, flags = Regex.FlagNone)):
							priority += (priorities[1] * 7.0)

					priority = max(0, priority)

					# NB: This structure should be the same as base.py -> parameterQueryXYZ().
					# Also check stream.py -> infoQuery().
					queries.append({
						# Use a priority to execute queries first that are assumed to return more links.
						# For instance, any query with a the main title should be placed before queries with aliases or other titles.
						'priority' : priority,

						'search' : search,
						'raw' : search,
						'pack' : bool(pack),
						'special' : bool((not numberSeason is None) and numberSeason == 0 and numberEpisode),
						'universal' : universal,
						'original' : original,
						'year' : None if pack else year if year else yearDefault,
						'time' : None if pack else time,
						'id' : {
							'imdb' : None if pack == 'movie' else idImdb,
							'tmdb' : None if pack == 'movie' else idTmdb,
							'tvdb' : None if pack == 'movie' else idTvdb,
						},
						'title' : title,
						'number' : {
							'season' : None if pack == 'show' else numberSeason,
							'episode' : None if (pack == 'show' or pack == 'season') else numberEpisode,
						},
					})
				except: self.logError()

			def _queryEncode(value, caseLower, caseUpper, set, encodeQuote, encodePlus, encodeMinus, includeBasic, includeEncode, includeHas, formatTitles, formatExpression1, formatExpression2):
				if not value: return None
				value = self._queryClean(value)

				# If FormatIncludeBasic or FormatIncludeEncode, unicode characters are removed from the string.
				# Do not use the query if the title contains only unicode characters, which will lead to the query only having the year or season/episode numbers and the title will be removed.
				if includeHas:
					valueLower = value.lower()
					for title in formatTitles:
						if title in valueLower:
							title = Regex.remove(data = title, expression = formatExpression1, all = True)
							if not title: return None

				if caseLower: value = value.lower()
				elif caseUpper: value = value.upper()

				# Must be before the encoding, otherwise the unicode characters are replaced with % url.
				if includeHas: value = Regex.remove(data = value, expression = formatExpression2, all = True)

				if encodeQuote or encodePlus or encodeMinus:
					value = Networker.linkQuote(data = value, plus = (encodePlus or encodeMinus))
					if encodeMinus: value = value.replace('+', '-')

				return value

			if self.typeExternal():
				if Media.typeTelevision(media):
					if self.supportShow() and (self.supportSpecial() or not(numberSeason is None and numberEpisode is None)):
						title = titles['search']['main'][0]
						format = {
							'title' : title,
							'title_show' : title,
							'year' : yearDefault,
							'season' : numberSeason,
							'season_zero' : None if numberSeason is None else ('%02d' % numberSeason),
							'episode' : numberEpisode,
							'episode_zero' : None if numberEpisode is None else ('%02d' % numberEpisode),
						}
						try: format['title_episode'] = titles['search']['episode'][0]
						except: format['title_episode'] = None
						_queryGenerate(query = self.queryEpisode()[0], format = format, title = {'query' : title, 'main' : format['title'], 'show' : format['title_show'], 'episode' : format['title_episode']})
						queryTitles.extend([format['title'], format['title_episode']])
				else:
					if self.supportMovie():
						title = titles['search']['main'][0]
						format = {
							'title' : title,
							'title_movie' : title,
						}
						try: format['title_collection'] = titles['search']['collection'][0]
						except: format['title_collection'] = None
						if years and 'all' in years and years['all']:
							for year in years['all']:
								format['year'] = year
								_queryGenerate(query = self.queryMovie()[0], format = format, title = {'query' : title, 'main' : format['title'], 'movie' : format['title_movie'], 'collection' : format['title_collection']}, year = year)
						else:
							format['year'] = yearDefault
							_queryGenerate(query = self.queryMovie()[0], format = format, title = {'query' : title, 'main' : format['title'], 'movie' : format['title_movie'], 'collection' : format['title_collection']})
						queryTitles.extend([format['title'], format['title_collection']])
			else:
				if exact:
					for title in titles['search']['exact']:
						_queryGenerate(search = title, title = {'query' : title, 'exact' : title})
					queryTitles.extend(titles['search']['exact'])
				else:
					titlesSearch = Tools.copy(titles['search']['main']) # Copy, since we add to it below.
					for lang in self.languages():
						if lang in titles['search']['native']:
							titlesSearch.extend(titles['search']['native'][lang])
					titlesSearch = Tools.listUnique(titlesSearch)

					if Media.typeTelevision(media):
						if self.supportShow() and (self.supportSpecial() or not(numberSeason is None and numberEpisode is None)):
							format = {
								'year' : yearDefault,
								'season' : numberSeason,
								'season_zero' : None if numberSeason is None else ('%02d' % numberSeason),
								'episode' : numberEpisode,
								'episode_zero' : None if numberEpisode is None else ('%02d' % numberEpisode),
							}
							try: format['title_episode'] = titles['search']['episode'][0]
							except: format['title_episode'] = None

							# Episode Queries.
							for i in range(len(titlesSearch)):
								try:
									title = titlesSearch[i]
									format['title'] = title
									format['title_show'] = title
									queryEpisode = self.queryEpisode()
									for j in range(len(queryEpisode)):
										try: _queryGenerate(priority = [0, 3000, 1001], query = queryEpisode[j], format = format, title = {'query' : title, 'main' : format['title'], 'show' : format['title_show'], 'episode' : format['title_episode']}, indexTitle = i, indexQuery = j)
										except: pass
								except: pass

							# Special Episode Queries.
							if not numberSeason or not numberEpisode:
								try:
									format['title'] = titlesSearch[0]
									format['title_show'] = titlesSearch[0]
									for i in range(len(titles['search']['episode'])):
										title = titles['search']['episode'][i]
										format['title_episode'] = title
										querySpecial = self.querySpecial()
										for j in range(len(querySpecial)):
											try: _queryGenerate(priority = [1000, 6000, 1002], query = querySpecial[j], format = format, title = {'query' : title, 'main' : format['title'], 'show' : format['title_show'], 'episode' : format['title_episode']}, indexTitle = i, indexQuery = j)
											except: pass
								except: pass

							# Season Pack Queries.
							if self.supportPackSeason() and self.settingsGlobalPackSeason(): # Allow season packs for special episodes: S00.
								try:
									for i in range(len(titlesSearch)):
										title = titlesSearch[i]
										format['title'] = title
										format['title_show'] = title
										querySeason = self.querySeason()
										for j in range(len(querySeason)):
											try: _queryGenerate(priority = [2000, 9000, 1003], query = querySeason[j], format = format, pack = 'season', title = {'query' : title, 'main' : format['title'], 'show' : format['title_show'], 'episode' : format['title_episode']}, indexTitle = i, indexQuery = j)
											except: pass
								except: pass

							# Show Pack Queries.
							if self.supportPackShow() and self.settingsGlobalPackShow() and not numberSeason == 0: # Do not retrieve packs when searching special episodes.
								try:
									for i in range(len(titlesSearch)):
										title = titlesSearch[i]
										format['title'] = title
										format['title_show'] = title
										queryShow = self.queryShow()
										for j in range(len(queryShow)):
											try: _queryGenerate(priority = [3000, 12000, 1004], query = queryShow[j], format = format, pack = 'show', title = {'query' : title, 'main' : format['title'], 'show' : format['title_show'], 'episode' : format['title_episode']}, indexTitle = i, indexQuery = j)
											except: pass
								except: pass

							queryTitles.extend(titlesSearch)
							queryTitles.append(format['title_episode'])
					else:
						if self.supportMovie():
							format = {}
							try: format['title_collection'] = titles['search']['collection'][0]
							except: format['title_collection'] = None

							# Movie Queries.
							if years and 'all' in years and years['all']:
								for i in range(len(titlesSearch)):
									for year in years['all']:
										try:
											title = titlesSearch[i]
											format['title'] = title
											format['title_movie'] = title
											format['year'] = year
											queryMovie = self.queryMovie()
											for j in range(len(queryMovie)):
												try: _queryGenerate(priority = [0, 1000, 1001], query = queryMovie[j], format = format, title = {'query' : title, 'main' : format['title'], 'movie' : format['title_movie'], 'collection' : format['title_collection']}, year = year, indexTitle = i, indexQuery = j)
												except: pass
										except: pass
							else:
								format['year'] = yearDefault
								for i in range(len(titlesSearch)):
									try:
										title = titlesSearch[i]
										format['title'] = title
										format['title_movie'] = title
										queryMovie = self.queryMovie()
										for j in range(len(queryMovie)):
											try: _queryGenerate(priority = [0, 1000, 1001], query = queryMovie[j], format = format, title = {'query' : title, 'main' : format['title'], 'movie' : format['title_movie'], 'collection' : format['title_collection']}, indexTitle = i, indexQuery = j)
											except: pass
									except: pass

							# Movie Collection Queries.
							if self.supportPackMovie() and self.settingsGlobalPackMovie():
								try:
									format['year'] = yearDefault
									format['title'] = titlesSearch[0]
									format['title_movie'] = titlesSearch[0]
									for i in range(len(titles['search']['collection'])):
										title = titles['search']['collection'][i]
										format['title_collection'] = title
										queryCollection = self.queryCollection()
										for j in range(len(queryCollection)):
											try: _queryGenerate(priority = [1000, 4000, 1002], query = queryCollection[j], format = format, pack = 'movie', title = {'query' : title, 'main' : format['title'], 'movie' : format['title_movie'], 'collection' : format['title_collection']}, indexTitle = i, indexQuery = j)
											except: pass
								except: pass

							queryTitles.extend(titlesSearch)
							queryTitles.append(format['title_collection'])

			case = self.formatCase()
			caseLower = case == ProviderWeb.FormatCaseLower
			caseUpper = case == ProviderWeb.FormatCaseUpper

			set = self.formatSet()

			encode = self.formatEncode()
			encodeQuote = encode == ProviderWeb.FormatEncodeQuote
			encodePlus = encode == ProviderWeb.FormatEncodePlus
			encodeMinus = encode == ProviderWeb.FormatEncodeMinus

			include = self.formatInclude()
			includeBasic = include == ProviderWeb.FormatIncludeBasic
			includeEncode = include == ProviderWeb.FormatIncludeEncode
			includeHas = includeBasic or includeEncode

			formatTitles = None
			formatExpression1 = None
			formatExpression2 = None
			if includeHas:
				formatTitles = [self._queryClean(i).lower() for i in queryTitles if i]
				formatTitles = [i for i in formatTitles if i]

				formatExpression = ''
				if includeEncode:
					if encodeQuote: formatExpression = '%'
					elif encodePlus: formatExpression = '\+'
					elif encodeMinus: formatExpression = '\-'
				formatExpression1 = '[^a-z\d]'
				formatExpression2 = '[^a-z\d\s%s]' % formatExpression

			queries = Tools.listSort(data = queries, key = lambda x : x['priority'])
			result = []
			for query in queries:
				value = _queryEncode(value = query['search'], caseLower = caseLower, caseUpper = caseUpper, set = set, encodeQuote = encodeQuote, encodePlus = encodePlus, encodeMinus = encodeMinus, includeBasic = includeBasic, includeEncode = includeEncode, includeHas = includeHas, formatTitles = formatTitles, formatExpression1 = formatExpression1, formatExpression2 = formatExpression2)
				if value is None: continue
				query['raw'] = query['search']
				query['search'] = value

				# Encode the titles as well, since some providers (eg: Newznab) might use the title instead of the query for searching.
				for key, value in query['title'].items():
					value = _queryEncode(value = value, caseLower = caseLower, caseUpper = caseUpper, set = set, encodeQuote = encodeQuote, encodePlus = encodePlus, encodeMinus = encodeMinus, includeBasic = includeBasic, includeEncode = includeEncode, includeHas = includeHas, formatTitles = formatTitles, formatExpression1 = formatExpression1, formatExpression2 = formatExpression2)
					if not value is None: query['title'][key] = value

				result.append(query)
			queries = Tools.listUnique(result, attribute = 'search')
		except: self.logError()

		return queries

	def queryReplacements(self, media, title, year, time, idImdb, idTmdb, idTvdb, numberSeason, numberEpisode, pack, exact, special):
		movie = Media.typeMovie(media)
		show = Media.typeTelevision(media)

		replacements = {
			self.replaceClean(ProviderWeb.TermTypeExact) : '' if exact else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermTypeExactMovie) : '' if exact and movie else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermTypeExactShow) : '' if exact and show else ProviderBase.Skip,

			self.replaceClean(ProviderWeb.TermTypeDirect) : '' if not exact else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermTypeDirectMovie) : '' if not exact and movie else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermTypeDirectShow) : '' if not exact and show else ProviderBase.Skip,

			self.replaceClean(ProviderWeb.TermTypeMovie) : '' if movie else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermTypeShow) : '' if show else ProviderBase.Skip,

			self.replaceClean(ProviderWeb.TermTypePack) : '' if pack else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermTypePackNone) : '' if not pack else ProviderBase.Skip,

			self.replaceClean(ProviderWeb.TermTypeSpecial) : '' if special else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermTypeSpecialNone) : '' if not special else ProviderBase.Skip,

			self.replaceClean(ProviderWeb.TermYear) : year if year else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermIdImdb) : idImdb if idImdb else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermIdImdbNumber) : idImdb.replace('tt', '') if idImdb else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermIdTmdb) : idTmdb if idTmdb else ProviderBase.Skip,
			self.replaceClean(ProviderWeb.TermIdTvdb) : idTvdb if idTvdb else ProviderBase.Skip,
		}

		if exact:
			title = title['exact'] if 'exact' in title and title['exact'] else ProviderBase.Skip
			replacements.update({
				self.replaceClean(ProviderWeb.TermTitle) : title,
				self.replaceClean(ProviderWeb.TermTitleMovie) : title,
				self.replaceClean(ProviderWeb.TermTitleCollection) : title,
				self.replaceClean(ProviderWeb.TermTitleShow) : title,
				self.replaceClean(ProviderWeb.TermTitleEpisode) : title,
				self.replaceClean(ProviderWeb.TermSeason) : ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermSeasonZero) : ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermEpisode) : ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermEpisodeZero) : ProviderBase.Skip,
			})
		elif movie:
			replacements.update({
				self.replaceClean(ProviderWeb.TermTitle) : title['main'] if 'main' in title and title['main'] else ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermTitleMovie) : title['movie'] if 'movie' in title and title['movie'] else ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermTitleCollection) : title['collection'] if 'collection' in title and title['collection'] else ProviderBase.Skip,
			})
		elif show:
			replacements.update({
				self.replaceClean(ProviderWeb.TermTitle) : title['main'] if 'main' in title and title['main'] else ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermTitleShow) : title['show'] if 'show' in title and title['show'] else ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermTitleEpisode) : title['episode'] if 'episode' in title and title['episode'] else ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermSeason) : numberSeason if not numberSeason is None else ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermSeasonZero) : ('%02d' % numberSeason) if not numberSeason is None else ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermEpisode) : numberEpisode if not numberEpisode is None else ProviderBase.Skip,
				self.replaceClean(ProviderWeb.TermEpisodeZero) : ('%02d' % numberSeason) if not numberEpisode is None else ProviderBase.Skip,
			})

		return replacements

	def _queryClean(self, query):
		query = Regex.remove(data = query, expression = '[\'\`]', all = True)
		query = Regex.replace(data = query, expression = '[\-\!\$\%%\^\&\*\(\)\_\+\|\~\=\`\{\}\\\[\]\:\"\;\'\<\>\?\,\.\\\/]', replacement = ' ', all = True)
		query = Regex.replace(data = query, expression = '\s{2,}', replacement = ' ', all = True).strip()
		return query

	##############################################################################
	# FORMAT
	##############################################################################

	def formatEncode(self):
		return self.mData['format']['encode']

	def formatCase(self):
		return self.mData['format']['case']

	def formatInclude(self):
		return self.mData['format']['include']

	def formatSet(self):
		return self.mData['format']['set']

	##############################################################################
	# ACCOUNT
	##############################################################################

	# Can be overwritten by subclasses to do more advanced authentication than the one provided with the constructor parameteres.
	# If False is returned, the provider will not be scraped.
	# Otherwise the authentication data should be returned in one of these formats:
	# 	1. String with single value.
	#	2. List of strings with multiple values.
	#	3. Dictionary with key-value pairs of multiple values.
	#	4. Dictionary in the format: {'data' : {...}, 'cookies' : {...}, 'headers' : {...}}
	def accountAuthenticate(self):
		return None

	def accountAuthentication(self):
		return ProviderWeb.AccountAuthentication[self.id()]

	def accountAuthenticationSet(self, data):
		ProviderWeb.AccountAuthentication[self.id()] = data

	def accountAuthenticationHas(self):
		return bool(self.accountAuthenticationMode())

	def accountAuthenticationMode(self):
		try: return self.mData['account']['authentication']['mode']
		except: return None

	def accountAuthenticationModeScrape(self):
		mode = self.accountAuthenticationMode()
		return mode == ProviderWeb.AccountModeScrape or mode == ProviderWeb.AccountModeAll

	def accountAuthenticationModeResolve(self):
		mode = self.accountAuthenticationMode()
		return mode == ProviderWeb.AccountModeResolve or mode == ProviderWeb.AccountModeAll

	def accountAuthenticationData(self, id = None):
		try:
			result = self.accountAuthentication()[ProviderBase.RequestData]
			if not id is None: result = result[id]
			return result
		except: return None

	def accountAuthenticationCookies(self, id = None):
		try:
			result = self.accountAuthentication()[ProviderBase.RequestCookies]
			if not id is None: result = result[id]
			return result
		except: return None

	def accountAuthenticationHeaders(self, id = None):
		try:
			result = self.accountAuthentication()[ProviderBase.RequestHeaders]
			if not id is None: result = result[id]
			return result
		except: return None

	def accountAuthenticationFormat(self):
		try: return self.accountAuthentication()[ProviderBase.ProcessFormat]
		except: return {}

	def accountAuthenticationUpdate(self):
		try:
			# Add raw account values to format.
			result = {}
			format = {}
			queryAuthentication = self.replaceClean(ProviderWeb.TermAuthentication)
			queryAuthentications = self.replaceClean(ProviderWeb.TermAuthentications)
			for type in ProviderBase.AccountTypeOrder:
				value = self.account(type = type)
				if value: format[queryAuthentications % type] = value
			result[ProviderBase.ProcessFormat] = format
			self.accountAuthenticationSet(result)

			# There can be authentication values (user/pass, key, etc) without the need for an authentication request (eg: NewzNab).
			if self.accountAuthenticationHas():
				result = self.accountRequest(self.mData['account']['authentication'])
				if result:
					for category in result.keys():
						for key, value in result[category].items():
							key = queryAuthentications % key
							if not key in format: format[key] = value
							if not queryAuthentication in format: format[queryAuthentication] = value

					result[ProviderBase.ProcessFormat] = format
					self.accountAuthenticationSet(result)

					return True
			else:
				return True
		except: self.logError()
		return False

	def accountRequest(self, request):
		try:
			if request:
				result = {ProviderBase.RequestData : {}, ProviderBase.RequestCookies : {}, ProviderBase.RequestHeaders : {}}
				types = [ProviderBase.RequestData, ProviderBase.RequestCookies, ProviderBase.RequestHeaders]

				# Certain old domains can redirect to new domains (eg: YggTorrent).
				# If cookies are used, a request is made to the old domain which in turn redirects to the new domain.
				# Cookies are then created and returned for the new domain.
				# When accessing the link (eg: downloading a torrent file), the old domain is used.
				# The download will then fail, because the cookie is from the new domain, whereas the download link is from the old domain.
				# Get the redirected domain and use it later on in resolve().
				# Only do this for providers with multiple alternative domains, assuming that those with a single domain will not have any redirects to new domains.
				if ProviderBase.ProcessExtract in request and request[ProviderBase.ProcessExtract]:
					if ProviderBase.RequestCookies in request[ProviderBase.ProcessExtract] and request[ProviderBase.ProcessExtract][ProviderBase.RequestCookies]:
						if len(self.links()) > 1:
							networker = self.request()
							response = networker.response()
							linkRequest = Networker.linkDomain(link = response['request']['link'], subdomain = False, topdomain = True, ip = True, scheme = False)
							linkResponse = Networker.linkDomain(link = response['link'], subdomain = False, topdomain = True, ip = True, scheme = False)
							if not linkRequest == linkResponse: self.linkRedirectSet(Networker.linkDomain(link = response['link'], subdomain = True, topdomain = True, ip = True, scheme = True))

				# Dynamic
				if ProviderBase.ProcessRequest in request and request[ProviderBase.ProcessRequest]:
					if ProviderBase.ProcessIterations in request and request[ProviderBase.ProcessIterations] > 1:
						request = Tools.copy(request) # Can be edited below with ProcessIterations.
						try: cookies = request[ProviderBase.ProcessRequest][ProviderBase.RequestCookies]
						except: cookies = {}
						request[ProviderBase.ProcessRequest][ProviderBase.RequestCookies] = cookies
						for i in range(request[ProviderBase.ProcessIterations]):
							result = self.requestExtract(data = request)
							cookies.update(result['networker'].responseCookies())
						result[ProviderBase.RequestCookies].update(cookies)
					else:
						result = self.requestExtract(data = request)
				else:
					values = self.accountAuthenticate()
					if not values is None and not values is False:
						if Tools.isDictionary(value):
							found = False
							for type in types:
								if type in values:
									result[type] = values[type]
									found = True
							if not found: result[ProviderBase.RequestData] = values
						elif Tools.isArray(result):
							result[ProviderBase.RequestData] = {i : values[i] for i in range(len(values))}
						else:
							result[ProviderBase.RequestData][0] = values

				# Fixed
				if ProviderBase.ProcessFixed in request:
					fixed = request[ProviderBase.ProcessFixed]
					if fixed:
						for type in types:
							if type in fixed:
								value = fixed[type]
								if value: result[type].update(value)

				# Authorization
				if ProviderBase.ProcessAuthorization in request:
					authorization = request[ProviderBase.ProcessAuthorization]
					if authorization:
						header = None
						if authorization == ProviderWeb.AccountAuthorizationBasic:
							username = self.accountUsername()
							if not username: username = self.accountEmail()
							header = Networker.authorizationHeader(type = authorization, username = username, password = self.accountPassword())
						elif authorization == ProviderWeb.AccountAuthorizationBearer:
							header = Networker.authorizationHeader(type = authorization, value = self.accountKey())
						if header: result[ProviderBase.RequestHeaders].update(header)

				# Validate
				# Regex.FlagAllLines: to match all lines of the data (important for NewzNab account validation).
				validate = False
				if ProviderBase.ProcessValidate in request:
					validate = request[ProviderBase.ProcessValidate]
					if validate:
						reponse = result['networker'].response() # In case the type was only specified in ProcessValidate and not in ProcessExtract.
						for type in types:
							if (type in result or type in reponse) and type in validate:
								try: data = result[type]
								except: data = None
								if not data:
									if type == ProviderBase.RequestData: data = result['networker'].responseDataText()
									else: data = reponse[type]
								check = validate[type]
								if Tools.isDictionary(check):
									for key, value in check.items():
										if key in data:
											if not Regex.match(data = data[key], expression = value, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines): return None
								else:
									try: data = ' '.join(list(data.values()))
									except: pass
									if not Regex.match(data = data, expression = check, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines): return None
				else:
					try:
						if not result['networker'].responseSuccess(): return None
					except: pass

				if not validate and all(not i for i in result.values()): return None

				try: del result['networker']
				except: pass
				return result
		except: self.logError()
		return None

	def accountVerification(self):
		try: return self.mData['account']['verification']
		except: return None

	def accountVerificationHas(self):
		return bool(self.accountVerification())

	def accountVerify(self, open = False):
		# Ignore accounts for open providers (eg: TorrentApi/Torrentz2k that uses accountless tokens).
		if self.accountHas() and (open or not self.accessOpen()):
			authenticationHas = self.accountAuthenticationHas()
			verificationHas = self.accountVerificationHas()
			if authenticationHas or verificationHas:
				if self.accountAuthenticationUpdate():
					verification = self.accountVerification()
					if not verification or self.accountRequest(verification): return True
				return False
		return None

	##############################################################################
	# RETRY
	##############################################################################

	def retryCount(self):
		return self.mData['retry']['count']

	def retryCountSet(self, count):
		self.mData['retry']['count'] = count

	def retryDelay(self):
		return self.mData['retry']['delay']

	def retryDelaySet(self, delay):
		self.mData['retry']['delay'] = delay

	def retryError(self):
		return self.mData['retry']['error']

	def retryErrorSet(self, error):
		self.mData['retry']['error'] = error

	def retryExpression(self):
		return self.mData['retry']['expression']

	def retryExpressionSet(self, expression):
		self.mData['retry']['expression'] = expression

	##############################################################################
	# OFFSET
	##############################################################################

	def offsetStart(self):
		return self.mData['offset']['start']

	def offsetIncrease(self):
		return self.mData['offset']['increase']

	##############################################################################
	# STREAM
	##############################################################################

	def streamAdjust(self):
		return self.mData['stream']['adjust']

	def streamTime(self):
		return self.mData['stream']['time']

	##############################################################################
	# SEARCH
	##############################################################################

	def searchQuery(self):
		return self.mData['search']['query']

	def searchConcurrency(self):
		return self.mData['search']['concurrency']

	def searchConcurrencySet(self, concurrency):
		self.mData['search']['concurrency'] = concurrency

	def searchCategoryAll(self):
		return self.mData['search']['category']['all']

	def searchCategoryMovie(self):
		return self.mData['search']['category']['movie']

	def searchCategoryShow(self):
		return self.mData['search']['category']['show']

	def searchRequest(self, path = None, link = None, subdomain = None, method = None, data = None, headers = None, cookies = None):
		return self.requestText(scrape = True, link = link, path = path, subdomain = subdomain, method = method, data = data, headers = headers, cookies = cookies)

	def searchExtract(self, item, data = None, details = None, entry = None):
		try:
			if not data: data = self.searchData()
			result = self.searchData()

			sourceType = data[Stream.ParameterSourceType]
			if sourceType is None:
				sourceType = self.processSourceType(value = self.extractSourceType(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourceType == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourceType] = sourceType

			# Do first to quickly filter out exisitng ones.

			if data[Stream.ParameterLink] is None:
				link = self.processLink(value = self.extractLink(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if link == ProviderBase.Skip: return ProviderBase.Skip

				# Clean the link.
				# Some links do not have a protocol (//www...) so that the browser automatically fills it in based on if the user visited the HTTP/HTTPS page.
				# Some have a relative path (/download/...) so thaat the browser automatically fills it in with the current domain.
				if link and not Networker.linkIs(link = link, magnet = True):
					if link.startswith('//'): link = Networker.linkScheme(link = self.linkCurrent(), syntax = False) + ':' + link
					else: link = self.linkCurrent(path = link)

				if link and self.resultContains(type = sourceType, link = link): return ProviderBase.Skip
				result[Stream.ParameterLink] = link

			hash = None
			if data[Stream.ParameterHash] is None:
				hash = self.processHash(value = self.extractHash(item = item, details = details, entry = entry), item = item, details = details)
				if hash == ProviderBase.Skip: return ProviderBase.Skip
				if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
				result[Stream.ParameterHash] = hash
			if hash is None:
				if data[Stream.ParameterHashContainer] is None:
					hash = self.processHashContainer(value = self.extractHashContainer(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
					if hash == ProviderBase.Skip: return ProviderBase.Skip
					if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
					result[Stream.ParameterHashContainer] = hash
				if hash is None:
					if data[Stream.ParameterHashContainerMd5] is None:
						hash = self.processHashContainerMd5(value = self.extractHashContainerMd5(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashContainerMd5] = hash
					if data[Stream.ParameterHashContainerSha1] is None:
						hash = self.processHashContainerSha1(value = self.extractHashContainerSha1(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashContainerSha1] = hash
					if data[Stream.ParameterHashContainerSha256] is None:
						hash = self.processHashContainerSha256(value = self.extractHashContainerSha256(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashContainerSha256] = hash
					if data[Stream.ParameterHashContainerSha512] is None:
						hash = self.processHashContainerSha512(value = self.extractHashContainerSha512(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashContainerSha512] = hash

				if data[Stream.ParameterHashFile] is None:
					hash = self.processHashFile(value = self.extractHashFile(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
					if hash == ProviderBase.Skip: return ProviderBase.Skip
					if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
					result[Stream.ParameterHashFile] = hash
				if hash is None:
					if data[Stream.ParameterHashFileMd5] is None:
						hash = self.processHashFileMd5(value = self.extractHashFileMd5(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashFileMd5] = hash
					if data[Stream.ParameterHashFileSha1] is None:
						hash = self.processHashFileSha1(value = self.extractHashFileSha1(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashFileSha1] = hash
					if data[Stream.ParameterHashFileSha256] is None:
						hash = self.processHashFileSha256(value = self.extractHashFileSha256(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashFileSha256] = hash
					if data[Stream.ParameterHashFileSha512] is None:
						hash = self.processHashFileSha512(value = self.extractHashFileSha512(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashFileSha512] = hash

				if data[Stream.ParameterHashOther] is None:
					hash = self.processHashOther(value = self.extractHashOther(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
					if hash == ProviderBase.Skip: return ProviderBase.Skip
					if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
					result[Stream.ParameterHashOther] = hash
				if hash is None:
					if data[Stream.ParameterHashOtherMd5] is None:
						hash = self.processHashOtherMd5(value = self.extractHashOtherMd5(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashOtherMd5] = hash
					if data[Stream.ParameterHashOtherSha1] is None:
						hash = self.processHashOtherSha1(value = self.extractHashOtherSha1(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashOtherSha1] = hash
					if data[Stream.ParameterHashOtherSha256] is None:
						hash = self.processHashOtherSha256(value = self.extractHashOtherSha256(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashOtherSha256] = hash
					if data[Stream.ParameterHashOtherSha512] is None:
						hash = self.processHashOtherSha512(value = self.extractHashOtherSha512(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
						if hash == ProviderBase.Skip: return ProviderBase.Skip
						if self.resultContains(type = sourceType, hash = hash): return ProviderBase.Skip
						result[Stream.ParameterHashOtherSha512] = hash

			# ID

			if data[Stream.ParameterIdProviderLocal] is None:
				idLocal = self.processIdLocal(value = self.extractIdLocal(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if idLocal == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterIdProviderLocal] = idLocal
			if data[Stream.ParameterIdProviderUniversal] is None:
				idUniversal = self.processIdUniversal(value = self.extractIdUniversal(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if idUniversal == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterIdProviderUniversal] = idUniversal
			if data[Stream.ParameterIdProviderCollection] is None:
				idCollection = self.processIdCollection(value = self.extractIdCollection(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if idCollection == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterIdProviderCollection] = idCollection
			if data[Stream.ParameterIdProviderItem] is None:
				idItem = self.processIdItem(value = self.extractIdItem(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if idItem == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterIdProviderItem] = idItem

			# Do the rest.

			if data[Stream.ParameterVideoQuality] is None:
				videoQuality = self.processVideoQuality(value = self.extractVideoQuality(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoQuality == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoQuality] = videoQuality

			if data[Stream.ParameterVideoQualityInexact] is None:
				videoQualityInexact = self.processVideoQualityInexact(value = self.extractVideoQualityInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoQualityInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoQualityInexact] = videoQualityInexact

			if data[Stream.ParameterVideoResolution] is None:
				videoResolution = self.processVideoResolution(value = self.extractVideoResolution(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoResolution == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoResolution] = videoResolution

			if data[Stream.ParameterVideoResolutionInexact] is None:
				videoResolutionInexact = self.processVideoResolutionInexact(value = self.extractVideoResolutionInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoResolutionInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoResolutionInexact] = videoResolutionInexact

			if data[Stream.ParameterVideoWidth] is None:
				videoWidth = self.processVideoWidth(value = self.extractVideoWidth(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoWidth == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoWidth] = videoWidth

			if data[Stream.ParameterVideoWidthInexact] is None:
				videoWidthInexact = self.processVideoWidthInexact(value = self.extractVideoWidthInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoWidthInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoWidthInexact] = videoWidthInexact

			if data[Stream.ParameterVideoHeight] is None:
				videoHeight = self.processVideoHeight(value = self.extractVideoHeight(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoHeight == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoHeight] = videoHeight

			if data[Stream.ParameterVideoHeightInexact] is None:
				videoHeightInexact = self.processVideoHeightInexact(value = self.extractVideoHeightInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoHeightInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoHeightInexact] = videoHeightInexact

			if data[Stream.ParameterVideoAspect] is None:
				videoAspect = self.processVideoAspect(value = self.extractVideoAspect(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoAspect == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoAspect] = videoAspect

			if data[Stream.ParameterVideoAspectInexact] is None:
				videoAspectInexact = self.processVideoAspectInexact(value = self.extractVideoAspectInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoAspectInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoAspectInexact] = videoAspectInexact

			if data[Stream.ParameterVideoCodec] is None:
				videoCodec = self.processVideoCodec(value = self.extractVideoCodec(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoCodec == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoCodec] = videoCodec

			if data[Stream.ParameterVideoDepth] is None:
				videoDepth = self.processVideoDepth(value = self.extractVideoDepth(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoDepth == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoDepth] = videoDepth

			if data[Stream.ParameterVideoRange] is None:
				videoRange = self.processVideoRange(value = self.extractVideoRange(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if videoRange == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideoRange] = videoRange

			if data[Stream.ParameterVideo3d] is None:
				video3d = self.processVideo3d(value = self.extractVideo3d(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if video3d == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterVideo3d] = video3d

			if data[Stream.ParameterAudioType] is None:
				audioType = self.processAudioType(value = self.extractAudioType(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if audioType == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterAudioType] = audioType

			if data[Stream.ParameterAudioChannels] is None:
				audioChannels = self.processAudioChannels(value = self.extractAudioChannels(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if audioChannels == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterAudioChannels] = audioChannels

			if data[Stream.ParameterAudioSystem] is None:
				audioSystem = self.processAudioSystem(value = self.extractAudioSystem(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if audioSystem == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterAudioSystem] = audioSystem

			if data[Stream.ParameterAudioCodec] is None:
				audioCodec = self.processAudioCodec(value = self.extractAudioCodec(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if audioCodec == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterAudioCodec] = audioCodec

			if data[Stream.ParameterAudioLanguage] is None:
				audioLanguage = self.processAudioLanguage(value = self.extractAudioLanguage(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if audioLanguage == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterAudioLanguage] = audioLanguage

			if data[Stream.ParameterAudioLanguageInexact] is None:
				audioLanguageInexact = self.processAudioLanguageInexact(value = self.extractAudioLanguageInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if audioLanguageInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterAudioLanguageInexact] = audioLanguageInexact

			if data[Stream.ParameterSubtitleType] is None:
				subtitleType = self.processSubtitleType(value = self.extractSubtitleType(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if subtitleType == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSubtitleType] = subtitleType

			if data[Stream.ParameterSubtitleLanguage] is None:
				subtitleLanguage = self.processSubtitleLanguage(value = self.extractSubtitleLanguage(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if subtitleLanguage == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSubtitleLanguage] = subtitleLanguage

			if data[Stream.ParameterSubtitleLanguageInexact] is None:
				subtitleLanguageInexact = self.processSubtitleLanguageInexact(value = self.extractSubtitleLanguageInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if subtitleLanguageInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSubtitleLanguageInexact] = subtitleLanguageInexact

			if data[Stream.ParameterReleaseType] is None:
				releaseType = self.processReleaseType(value = self.extractReleaseType(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if releaseType == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterReleaseType] = releaseType

			if data[Stream.ParameterReleaseFormat] is None:
				releaseFormat = self.processReleaseFormat(value = self.extractReleaseFormat(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if releaseFormat == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterReleaseFormat] = releaseFormat

			if data[Stream.ParameterReleaseEdition] is None:
				releaseEdition = self.processReleaseEdition(value = self.extractReleaseEdition(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if releaseEdition == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterReleaseEdition] = releaseEdition

			if data[Stream.ParameterReleaseNetwork] is None:
				releaseNetwork = self.processReleaseNetwork(value = self.extractReleaseNetwork(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if releaseNetwork == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterReleaseNetwork] = releaseNetwork

			if data[Stream.ParameterReleaseGroup] is None:
				releaseGroup = self.processReleaseGroup(value = self.extractReleaseGroup(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if releaseGroup == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterReleaseGroup] = releaseGroup

			if data[Stream.ParameterReleaseUploader] is None:
				releaseUploader = self.processReleaseUploader(value = self.extractReleaseUploader(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if releaseUploader == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterReleaseUploader] = releaseUploader

			if data[Stream.ParameterFileName] is None:
				fileName = self.processFileName(value = self.extractFileName(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if fileName == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterFileName] = fileName

			if data[Stream.ParameterFileNameInexact] is None:
				fileNameInexact = self.processFileNameInexact(value = self.extractFileNameInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if fileNameInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterFileNameInexact] = fileNameInexact

			if data[Stream.ParameterFileExtra] is None:
				fileExtra = self.processFileExtra(value = self.extractFileExtra(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if fileExtra == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterFileExtra] = fileExtra

			if data[Stream.ParameterFileSize] is None:
				fileSize = self.processFileSize(value = self.extractFileSize(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if fileSize == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterFileSize] = fileSize

			if data[Stream.ParameterFileSizeInexact] is None:
				fileSizeInexact = self.processFileSizeInexact(value = self.extractFileSizeInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if fileSizeInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterFileSizeInexact] = fileSizeInexact

			if data[Stream.ParameterFileContainer] is None:
				fileContainer = self.processFileContainer(value = self.extractFileContainer(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if fileContainer == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterFileContainer] = fileContainer

			if data[Stream.ParameterFilePack] is None:
				filePack = self.processFilePack(value = self.extractFilePack(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if filePack == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterFilePack] = filePack

			if data[Stream.ParameterSourceSeeds] is None:
				sourceSeeds = self.processSourceSeeds(value = self.extractSourceSeeds(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourceSeeds == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourceSeeds] = sourceSeeds

			if data[Stream.ParameterSourceSeedsInexact] is None:
				sourceSeedsInexact = self.processSourceSeedsInexact(value = self.extractSourceSeedsInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourceSeedsInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourceSeedsInexact] = sourceSeedsInexact

			if data[Stream.ParameterSourceLeeches] is None:
				sourceLeeches = self.processSourceLeeches(value = self.extractSourceLeeches(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourceLeeches == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourceLeeches] = sourceLeeches

			if data[Stream.ParameterSourceLeechesInexact] is None:
				sourceLeechesInexact = self.processSourceLeechesInexact(value = self.extractSourceLeechesInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourceLeechesInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourceLeechesInexact] = sourceLeechesInexact

			if data[Stream.ParameterSourceTime] is None:
				sourceTime = self.processSourceTime(value = self.extractSourceTime(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourceTime == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourceTime] = sourceTime

			if data[Stream.ParameterSourceTimeInexact] is None:
				sourceTimeInexact = self.processSourceTimeInexact(value = self.extractSourceTimeInexact(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourceTimeInexact == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourceTimeInexact] = sourceTimeInexact

			if data[Stream.ParameterSourcePopularity] is None:
				sourcePopularity = self.processSourcePopularity(value = self.extractSourcePopularity(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourcePopularity == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourcePopularity] = sourcePopularity

			if data[Stream.ParameterSourceApproval] is None:
				sourceApproval = self.processSourceApproval(value = self.extractSourceApproval(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourceApproval == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourceApproval] = sourceApproval

			if data[Stream.ParameterSourcePublisher] is None:
				sourcePublisher = self.processSourcePublisher(value = self.extractSourcePublisher(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourcePublisher == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourcePublisher] = sourcePublisher

			if data[Stream.ParameterSourceHoster] is None:
				sourceHoster = self.processSourceHoster(value = self.extractSourceHoster(item = item, details = details, entry = entry), item = item, details = details, entry = entry)
				if sourceHoster == ProviderBase.Skip: return ProviderBase.Skip
				result[Stream.ParameterSourceHoster] = sourceHoster

		except: self.logError()

		return result

	def searchData(self):
		return {
			Stream.ParameterThresholdSize : self.customSize(),
			Stream.ParameterThresholdTime : self.customTime(),
			Stream.ParameterThresholdPeers : self.customPeers(),
			Stream.ParameterThresholdSeeds : self.customSeeds(),
			Stream.ParameterThresholdLeeches : self.customLeeches(),

			Stream.ParameterFileNameProcess : self.cleanFileName,
			Stream.ParameterSourceTimeFormat : self.streamTime(),

			Stream.ParameterLink : None,

			Stream.ParameterIdProviderLocal : None,
			Stream.ParameterIdProviderUniversal : None,
			Stream.ParameterIdProviderCollection : None,
			Stream.ParameterIdProviderItem : None,

			Stream.ParameterHash : None,
			Stream.ParameterHashContainer : None,
			Stream.ParameterHashContainerMd5 : None,
			Stream.ParameterHashContainerSha1 : None,
			Stream.ParameterHashContainerSha256 : None,
			Stream.ParameterHashContainerSha512 : None,
			Stream.ParameterHashFile : None,
			Stream.ParameterHashFileMd5 : None,
			Stream.ParameterHashFileSha1 : None,
			Stream.ParameterHashFileSha256 : None,
			Stream.ParameterHashFileSha512 : None,
			Stream.ParameterHashOther : None,
			Stream.ParameterHashOtherMd5 : None,
			Stream.ParameterHashOtherSha1 : None,
			Stream.ParameterHashOtherSha256 : None,
			Stream.ParameterHashOtherSha512 : None,

			Stream.ParameterVideoQuality : None,
			Stream.ParameterVideoQualityInexact : None,
			Stream.ParameterVideoResolution : None,
			Stream.ParameterVideoResolutionInexact : None,
			Stream.ParameterVideoWidth : None,
			Stream.ParameterVideoWidthInexact : None,
			Stream.ParameterVideoHeight : None,
			Stream.ParameterVideoHeightInexact : None,
			Stream.ParameterVideoAspect : None,
			Stream.ParameterVideoAspectInexact : None,
			Stream.ParameterVideoCodec : None,
			Stream.ParameterVideoDepth : None,
			Stream.ParameterVideoRange : None,
			Stream.ParameterVideo3d : None,

			Stream.ParameterAudioType : None,
			Stream.ParameterAudioChannels : None,
			Stream.ParameterAudioSystem : None,
			Stream.ParameterAudioCodec : None,
			Stream.ParameterAudioLanguage : None,
			Stream.ParameterAudioLanguageInexact : None,

			Stream.ParameterSubtitleType : None,
			Stream.ParameterSubtitleLanguage : None,
			Stream.ParameterSubtitleLanguageInexact : None,

			Stream.ParameterReleaseType : None,
			Stream.ParameterReleaseFormat : None,
			Stream.ParameterReleaseEdition : None,
			Stream.ParameterReleaseNetwork : None,
			Stream.ParameterReleaseGroup : None,
			Stream.ParameterReleaseUploader : None,

			Stream.ParameterFileName : None,
			Stream.ParameterFileNameInexact : None,
			Stream.ParameterFileExtra : None,
			Stream.ParameterFileSize : None,
			Stream.ParameterFileSizeInexact : None,
			Stream.ParameterFileContainer : None,
			Stream.ParameterFilePack : None,

			Stream.ParameterSourceType : None,
			Stream.ParameterSourceSeeds : None,
			Stream.ParameterSourceSeedsInexact : None,
			Stream.ParameterSourceLeeches : None,
			Stream.ParameterSourceLeechesInexact : None,
			Stream.ParameterSourceTime : None,
			Stream.ParameterSourceTimeInexact : None,
			Stream.ParameterSourcePopularity : None,
			Stream.ParameterSourceApproval : None,
			Stream.ParameterSourcePublisher : None,
			Stream.ParameterSourceHoster : None,
		}

	def searchProcess(self, added, item, validate):
		try:
			if self.stopped(): return

			id = self.id()

			item = self.processItem(item = item)
			if item == ProviderBase.Skip: return

			if self.processBefore(item = item) == ProviderBase.Skip: return

			data = self.searchExtract(item = item)
			if data == ProviderBase.Skip: return

			if self.processAfter(item = item) == ProviderBase.Skip: return

			stream = self.resultStream(
				validate = validate,
				validateAdjust = self.streamAdjust(),
				**data
			)
			if stream:
				details = self.processDetails(value = self.extractDetails(item = item), item = item)
				if details == ProviderBase.Skip: return
				elif not details is None:
					if not id in ProviderWeb.DetailsData:
						ProviderBase.ResultLock[id].acquire()
						if not id in ProviderWeb.DetailsData: ProviderWeb.DetailsData[id] = {}
						ProviderBase.ResultLock[id].release()

					value = None
					if Tools.isDictionary(details):
						value = Converter.jsonTo(details)
					elif Networker.linkIs(details):
						value = details
						details = {ProviderBase.RequestLink: details}
					else:
						value = Converter.jsonTo(details) if Tools.isArray(details) else details
						details = {ProviderBase.RequestPath: details}

					if value in ProviderWeb.DetailsData[id]: return # Already retrieved by another query.
					ProviderBase.ResultLock[id].acquire()
					ProviderWeb.DetailsData[id][value] = True
					ProviderBase.ResultLock[id].release()

					details = self.searchRequest(**details)
					if not details: return
					details = self.extractData(data = details, details = True)

					if self.processDetailsBefore(item = details) == ProviderBase.Skip: return

					entries = self.processEntries(value = self.extractEntries(item = item, details = details), item = item, details = details)
					if entries == ProviderBase.Skip: return
					elif entries is None: # Single entry on details page.
						data = self.searchExtract(data = data, item = item, details = details)
						if data == ProviderBase.Skip: return
						if self.processDetailsAfter(item = details) == ProviderBase.Skip: return
						if not stream.reload(**data, validate = validate, validateAdjust = self.streamAdjust()): return
					else: # Multiple entries on details page.
						streams = []
						if self.searchConcurrency():
							threads = [self.thread(self.searchEntry, streams, stream, data, item, details, entry) for entry in entries]
							self.threadExecute(threads = threads, limit = self.concurrencyTasks(level = 3))
						else:
							[self.searchEntry(streams, stream, data, item, details, entry) for entry in entries]
						stream = streams
						if self.processDetailsAfter(item = details) == ProviderBase.Skip: return

				# Process as list in casae there are multiple entries on the details page.
				streams = stream
				if not Tools.isList(streams): streams = [(streams, None)]
				for stream in streams:
					entry = stream[1]
					stream = stream[0]

					stream = self.resultProcess(stream = stream)
					if stream == ProviderBase.Skip: continue

					stream = self.processStream(stream = stream, item = item, details = details, entry = entry)
					if stream == ProviderBase.Skip: continue

					if self.resultAdd(stream): added[0] = True
		except: self.logError()

	def searchEntry(self, result, stream, data, item, details, entry):
		entry = self.processEntry(item = entry)
		if entry == ProviderBase.Skip: return

		if self.processEntryBefore(item = entry) == ProviderBase.Skip: return

		dataEntry = Tools.copy(data)
		dataEntry = self.searchExtract(data = dataEntry, item = item, details = details, entry = entry)
		if dataEntry == ProviderBase.Skip: return

		if self.processEntryAfter(item = entry) == ProviderBase.Skip: return

		streamEntry = stream.copy()
		if not streamEntry.reload(**dataEntry, validateAdjust = self.streamAdjust()): return

		result.append((streamEntry, entry))

	def searchValid(self, data, validateTitle = True, validateYear = True, validateShow = True, validateSeason = True, validateEpisode = True, adjust = None):
		return ProviderBase.searchValid(self,
			data = data,
			validateAdjust = self.streamAdjust() if adjust is None else adjust,
			validateTitle = validateTitle,
			validateYear = validateYear,
			validateShow = validateShow,
			validateSeason = validateSeason,
			validateEpisode = validateEpisode,
		)

	def search(self, link, subdomain, path, method, headers, cookies, data, replacements, category, validate, media, titles, years, time, idImdb, idTmdb, idTvdb, numberSeason, numberEpisode, language, pack):
		timer = self.statisticsTimer()
		try:
			offset = self.offsetStart()
			replacement = self.replaceClean(ProviderWeb.TermOffset)

			while self.scrapePageAllow(increase = True):
				replacements[replacement] = offset
				linkNew = self.replace(data = link, replacements = replacements)
				subdomainNew = self.replace(data = subdomain, replacements = replacements)
				pathNew = self.replace(data = path, replacements = replacements)
				dataNew = self.replace(data = data, replacements = replacements)

				result = None
				items = None
				added = [False]

				if self.queryAllow(pathNew, dataNew) and not self.stopped():
					self.statisticsUpdateSearch(page = True)
					result = self.searchRequest(link = linkNew, subdomain = subdomainNew, path = pathNew, method = method, headers = headers, cookies = cookies, data = dataNew)
					if result and not result == ProviderBase.Skip and not self.stopped():
						result = self.processRequest(data = result)
						if result and not result == ProviderBase.Skip and not self.stopped():
							result = self.extractData(data = result)
							if result and not result == ProviderBase.Skip and not self.stopped():
								result = self.processData(data = result)
								if result and not result == ProviderBase.Skip and not self.stopped():
									items = self.extractList(data = result)
									if items and not items == ProviderBase.Skip and not self.stopped():
										items = self.processItems(items = items)
										if items and not items == ProviderBase.Skip and not self.stopped():
											if self.searchConcurrency():
												threads = [self.thread(self.searchProcess, added, item, validate) for item in items]
												self.threadExecute(threads, limit = self.concurrencyTasks(level = 2))
											else:
												for item in items:
													self.searchProcess(added = added, item = item, validate = validate)

				if offset is None or not added[0]: break
				elif not self.timerAllow() or not self.scrapeRequestAllow() or self.stopped() or self.verifyBusy(): break
				elif self.processOffset(data = result, items = items) == ProviderBase.Skip: break
				else: offset += self.offsetIncrease()
		except: self.logError()
		self.statisticsUpdateSearch(duration = timer)

	##############################################################################
	# EXECUTE
	##############################################################################

	def executeSearch(self, media, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, language = None, pack = None, duration = None, exact = False, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		try:
			self.parametersSet(media = media, titles = titles, years = years, time = time, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, numberSeason = numberSeason, numberEpisode = numberEpisode, language = language, pack = pack, duration = duration, exact = exact, silent = silent)
			self.processInitial()

			validate = not exact
			searches = self.searchQuery()
			queries = self.queryGenerate(media = media, titles = titles, years = years, time = time, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, numberSeason = numberSeason, numberEpisode = numberEpisode, language = language, exact = exact)
			replacements = self.replacements()

			if Media.typeMovie(media): categories = self.searchCategoryMovie()
			elif Media.typeTelevision(media): categories = self.searchCategoryShow()
			else: categories = self.searchCategoryAll()
			if not categories: categories = [None]

			threads = []
			for query in queries:
				if self.scrapeQueryAllow():
					self.scrapeQueryIncrease()

					queryTitle = query['title']
					queryYear = query['year']
					queryTime = query['time']
					queryIdImdb = query['id']['imdb']
					queryIdTmdb = query['id']['tmdb']
					queryIdTvdb = query['id']['tvdb']
					queryNumberSeason = query['number']['season']
					queryNumberEpisode = query['number']['episode']
					queryPack = query['pack']
					querySpecial = query['special']
					queryRaw = query['raw']
					querySearch = query['search']

					# Set the season/episode number to None for packs.
					# Ensures that replacements will skip certain fallback queries (eg Newznab).
					# Eg: if we are searching show packs, the season/episode number, year, and time should be None.
					replacements.update(self.queryReplacements(media = media, title = queryTitle, year = queryTime, time = queryTime, idImdb = queryIdImdb, idTmdb = queryIdTmdb, idTvdb = queryIdTvdb, numberSeason = queryNumberSeason, numberEpisode = queryNumberEpisode, pack = queryPack, exact = exact, special = querySpecial))

					timer = self.statisticsTimer()
					streams = self.cacheRetrieve(cache = cacheLoad, query = querySearch, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, numberSeason = numberSeason, numberEpisode = numberEpisode)

					if streams is None:
						replacements[self.replaceClean(ProviderWeb.TermQuery)] = querySearch
						letter = self.replaceClean(ProviderWeb.TermLetter)
						try: replacements[letter] = querySearch[0]
						except: replacements[letter] = ''

						if cacheSave: self.cacheInitialize(query = querySearch, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, numberSeason = numberSeason, numberEpisode = numberEpisode)

						for category in categories:
							replacements[self.replaceClean(ProviderWeb.TermCategory)] = category if not category is None else ProviderBase.Skip
							for search in searches:
								if not Tools.isArray(search): search = [search]

								values = []
								for se in search:
									linkNew, subdomainNew, pathNew, methodNew, headersNew, cookiesNew, dataNew, replacementsNew = self.replaceSearch(search = se, replacements = replacements)
									linkNew = self.replace(data = linkNew, replacements = replacementsNew, nested = True)
									subdomainNew = self.replace(data = subdomainNew, replacements = replacementsNew, nested = True)
									pathNew = self.replace(data = pathNew, replacements = replacementsNew, nested = True)
									headersNew = self.replace(data = headersNew, replacements = replacementsNew, nested = True)
									cookiesNew = self.replace(data = cookiesNew, replacements = replacementsNew, nested = True)
									dataNew = self.replace(data = dataNew, replacements = replacementsNew, nested = True)

									# Do not execute the query if some metadata is missing.
									# For instance, if a query needs an IMDb ID, but it is not available, do not search, since it will return no or incorrect results.
									if (pathNew or dataNew) and not((pathNew and ProviderBase.Skip in pathNew) or (dataNew and any(ProviderBase.Skip in d for d in dataNew.values()))):
										values.append({'replacements' : replacementsNew, 'link' : linkNew, 'subdomain' : subdomainNew, 'path' : pathNew, 'method' : methodNew, 'headers' : headersNew, 'cookies' : cookiesNew, 'data' : dataNew})

								if values:
									for value in values:
										provider = self.copy() # Create a copy, since some class variables might be accessed by multiple threads (eg: self.added).
										provider.parametersSet(query = query, media = media, titles = titles, years = years, time = time, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, numberSeason = numberSeason, numberEpisode = numberEpisode, language = language, pack = pack, duration = duration, exact = exact, silent = silent)
										provider.statisticsUpdateSearch(query = True)
										threads.append(self.thread(provider.search, value['link'], value['subdomain'], value['path'], value['method'], value['headers'], value['cookies'], value['data'], value['replacements'], category, validate, media, titles, years, time, idImdb, idTmdb, idTvdb, numberSeason, numberEpisode, language, pack))
									break # Skip fallback queries.
					else:
						self.statisticsUpdateSearch(cache = True)
						self.resultSet(streams)
						self.statisticsUpdateSearch(duration = timer)

			if len(threads) > 0 and not self.stopped():
				if not self.accountAuthenticationModeScrape() or self.accountAuthenticationUpdate():
					self.threadExecute(threads = threads, factor = ProviderBase.TimeFactorScrape, limit = self.concurrencyTasks(level = 1))

		except: self.logError()

	##############################################################################
	# RESOLVE
	##############################################################################

	def resolve(self, link, renew = False):
		try:
			# Always authenticate here again and readd the authentication headers/cookies to the link.
			# This makes sure that new cookies are retireved if an old locally cached link is used which has expiered cookies.
			# Or if unauthenticated links are returned by external services like Orion.
			authenticate = self.accountAuthenticationModeResolve()
			if not authenticate or self.accountAuthenticationUpdate():
				data = None
				headers = Networker.linkHeaders(link = link)
				cookies = Networker.linkCookies(link = link)

				# Extract existing headers/cookies from link, clean the link, and pass the updated authenticated headers/cookies to resolveLink().
				if authenticate:
					header = self.accountAuthenticationHeaders()
					if header: headers.update(header)
					cookie = self.accountAuthenticationCookies()
					if cookie: cookies.update(cookie)

					data = self.accountAuthenticationData()
					if data: data = self.replace(data = data, replacements = self.accountAuthenticationFormat())

				link = Networker.linkClean(link = link, headersStrip = True)
				link = self.resolveLink(link = link, data = data, headers = headers, cookies = cookies)

				# The headers/cookies parameters can be updated inside resolveLink(), or they can be added to the link returneed by resolveLink().
				# Add the updated headers/cookies to the link.
				header = Networker.linkHeaders(link = link)
				if header: headers.update(header)
				cookie = Networker.linkCookies(link = link)
				if cookie: cookies.update(cookie)

				# Some providers (eg: YggTorrent) change their domain frequently.
				# Old domains might redirect to new domains, or old domains might be completely down.
				# During account authentication, if cookies are involved, the new redirected domain is determined.
				# Replace the old domain with the new domain.
				# This is also useful if Orion contains old links from YggTorrent (or other providers) that have old taken-down domains.
				# When "renew", any old non-exisitng domain is replaced with the one hardcoded in the provider code. Useful if Orion has links with old domains.
				if not Networker.linkIsMagnet(link = link):
					if renew: linkNew = self.linkPrevious(redirect = False)
					else: linkNew = self.linkRedirect()
					if linkNew:
						linkOld = Networker.linkDomain(link = link, subdomain = True, topdomain = True, ip = True, scheme = True)
						linkNew = Networker.linkDomain(link = linkNew, subdomain = True, topdomain = True, ip = True, scheme = True)
						link = link.replace(linkOld, linkNew)

				link = Networker.linkClean(link = link, headersStrip = True)
				link = Networker.linkCreate(link = link, parameters = data)
				link = Networker.linkHeaders(link = link, headers = headers, cookies = cookies)

				return link
		except: self.logError()
		return None

	##############################################################################
	# EXTRACT
	##############################################################################

	'''
		FUNCTION:
			Functions called to extract the raw values from the body returned by the request.
			These functions can be overwritten by subclasses if additional extracting is required on the attribute.
		PARAMETERS:
			item: The raw data of the entire item being processed.
			data: The raw data of the entire request being processed.
		RETURNS:
			The function should return the raw extracted value.
	'''

	# Called right aftr the request to extract a subpart of the text before passing it on on the rest of extraction.
	def extractData(self, data, details = False):
		return data

	# Called for extracting the list of items. Should return a list where each entry represents the data of one item.
	def extractList(self, data):
		return data

	# Called for extracting a link or path for a sub-page containing additional metadata.
	def extractDetails(self, item):
		return None

	# Called for extracting a list of streams from a sub-page. The sub-page might contain multiple links/streams/episodes that should all be their own stream object added to the results.
	def extractEntries(self, item, details = None):
		return None

	def extractLink(self, item, details = None, entry = None):
		return None

	def extractIdLocal(self, item, details = None, entry = None):
		return None

	def extractIdUniversal(self, item, details = None, entry = None):
		return None

	def extractIdCollection(self, item, details = None, entry = None):
		return None

	def extractIdItem(self, item, details = None, entry = None):
		return None

	def extractHash(self, item, details = None, entry = None):
		return None

	def extractHashContainer(self, item, details = None, entry = None):
		return None

	def extractHashContainerMd5(self, item, details = None, entry = None):
		return None

	def extractHashContainerSha1(self, item, details = None, entry = None):
		return None

	def extractHashContainerSha256(self, item, details = None, entry = None):
		return None

	def extractHashContainerSha512(self, item, details = None, entry = None):
		return None

	def extractHashFile(self, item, details = None, entry = None):
		return None

	def extractHashFileMd5(self, item, details = None, entry = None):
		return None

	def extractHashFileSha1(self, item, details = None, entry = None):
		return None

	def extractHashFileSha256(self, item, details = None, entry = None):
		return None

	def extractHashFileSha512(self, item, details = None, entry = None):
		return None

	def extractHashOther(self, item, details = None, entry = None):
		return None

	def extractHashOtherMd5(self, item, details = None, entry = None):
		return None

	def extractHashOtherSha1(self, item, details = None, entry = None):
		return None

	def extractHashOtherSha256(self, item, details = None, entry = None):
		return None

	def extractHashOtherSha512(self, item, details = None, entry = None):
		return None

	def extractVideoQuality(self, item, details = None, entry = None):
		return None

	def extractVideoQualityInexact(self, item, details = None, entry = None):
		return None

	def extractVideoResolution(self, item, details = None, entry = None):
		return None

	def extractVideoResolutionInexact(self, item, details = None, entry = None):
		return None

	def extractVideoWidth(self, item, details = None, entry = None):
		return None

	def extractVideoWidthInexact(self, item, details = None, entry = None):
		return None

	def extractVideoHeight(self, item, details = None, entry = None):
		return None

	def extractVideoHeightInexact(self, item, details = None, entry = None):
		return None

	def extractVideoAspect(self, item, details = None, entry = None):
		return None

	def extractVideoAspectInexact(self, item, details = None, entry = None):
		return None

	def extractVideoCodec(self, item, details = None, entry = None):
		return None

	def extractVideoDepth(self, item, details = None, entry = None):
		return None

	def extractVideoRange(self, item, details = None, entry = None):
		return None

	def extractVideo3d(self, item, details = None, entry = None):
		return None

	def extractAudioType(self, item, details = None, entry = None):
		return None

	def extractAudioChannels(self, item, details = None, entry = None):
		return None

	def extractAudioSystem(self, item, details = None, entry = None):
		return None

	def extractAudioCodec(self, item, details = None, entry = None):
		return None

	def extractAudioLanguage(self, item, details = None, entry = None):
		return None

	def extractAudioLanguageInexact(self, item, details = None, entry = None):
		return None

	def extractSubtitleType(self, item, details = None, entry = None):
		return None

	def extractSubtitleLanguage(self, item, details = None, entry = None):
		return None

	def extractSubtitleLanguageInexact(self, item, details = None, entry = None):
		return None

	def extractReleaseType(self, item, details = None, entry = None):
		return None

	def extractReleaseFormat(self, item, details = None, entry = None):
		return None

	def extractReleaseEdition(self, item, details = None, entry = None):
		return None

	def extractReleaseNetwork(self, item, details = None, entry = None):
		return None

	def extractReleaseGroup(self, item, details = None, entry = None):
		return None

	def extractReleaseUploader(self, item, details = None, entry = None):
		return None

	def extractFileName(self, item, details = None, entry = None):
		return None

	def extractFileNameInexact(self, item, details = None, entry = None):
		return None

	def extractFileExtra(self, item, details = None, entry = None):
		return None

	def extractFileSize(self, item, details = None, entry = None):
		return None

	def extractFileSizeInexact(self, item, details = None, entry = None):
		return None

	def extractFileContainer(self, item, details = None, entry = None):
		return None

	def extractFilePack(self, item, details = None, entry = None):
		return None

	def extractSourceType(self, item, details = None, entry = None):
		return self.type()

	def extractSourceSeeds(self, item, details = None, entry = None):
		return None

	def extractSourceSeedsInexact(self, item, details = None, entry = None):
		return None

	def extractSourceLeeches(self, item, details = None, entry = None):
		return None

	def extractSourceLeechesInexact(self, item, details = None, entry = None):
		return None

	def extractSourceTime(self, item, details = None, entry = None):
		return None

	def extractSourceTimeInexact(self, item, details = None, entry = None):
		return None

	def extractSourcePopularity(self, item, details = None, entry = None):
		return None

	def extractSourceApproval(self, item, details = None, entry = None):
		return ProviderBase.ApprovalDefault

	def extractSourcePublisher(self, item, details = None, entry = None):
		return None

	def extractSourceHoster(self, item, details = None, entry = None):
		return None

	##############################################################################
	# PROCESS
	##############################################################################

	'''
		FUNCTION:
			Functions called to process the raw extracted values into a standard format.
			These functions can be overwritten by subclasses if additional processing is required on the attribute.
		PARAMETERS:
			value: The specific attribute that has to be formatted.
			item: The raw data of the entire item being processed.
		RETURNS:
			The function should return the standardized value, or ProviderBase.Skip if the current item should be ingored and not included in the final results.
	'''

	# Called a single time before the scraping of the provider (and its subqueries) start.
	# Ideal for authentication or things that have to be done once before scraping commences.
	def processInitial(self):
		return None

	# Called after the request was made, but before the data is passed on to extractData.
	# Is useful if the data returned by the request is in an unexpected format.
	# For instance, the provider might expect JSON to be returned, but when an error occurs, XML is returned (eg: NewzNab).
	def processRequest(self, data):
		return data

	# Called before processing the items, right after the data has been retrieved and before the list of items are extracted.
	def processData(self, data):
		return data

	# Called before processing the items, right after the data has been retrieved and the list of items extracted.
	def processItems(self, items):
		return items

	# Called when the page offset is increased, before the next page is retrieved.
	# Only called on subsequent pages, not before the first page.
	# Ideal for checking if the scraping of the next page should stop.
	# There is another mechanism to retrieve the next page and stop if it does not contain usable results. But this requires an additional page to be retrieved.
	# Some providers already know from the current page that no more results are availble.
	def processOffset(self, data, items):
		return None

	# Called before processing a single item, before processBefore, and before any of the values are processed.
	# Extends the item with additional info, like making additional sub-requests to get info from a sub-page.
	# The item must be returned.
	def processItem(self, item):
		return item

	# Called before processing a single item and before any of the values are processed.
	# Does not have to return the item, can only return Skip or nothing. If the item must be edited, use processItem() instead.
	def processBefore(self, item):
		return None

	# Called after processing a single item, after all values were processed, but before the stream object is created, validated, and added to the results.
	# Does not have to return the item, can only return Skip or nothing.
	def processAfter(self, item):
		return None

	# Called after processing a single item, and after the stream object was created.
	# Can be used to update the stream object with additional metadata after it was created and validated.
	def processStream(self, stream, item, details = None, entry = None):
		return stream

	# Called for a details sub-page.
	def processDetails(self, value, item):
		return value if value else None

	def processDetailsBefore(self, item):
		return None

	def processDetailsAfter(self, item):
		return None

	# Called for multiple entries on the details sub-page.
	def processEntries(self, value, item, details = None):
		return value if value else None

	# Can request a sub-sub page. Entries are run concurrently if searchConcurrency is set.
	def processEntry(self, item):
		return item

	def processEntryBefore(self, item):
		return None

	def processEntryAfter(self, item):
		return None

	def processLink(self, value, item, details = None, entry = None):
		return value if value else None

	def processIdLocal(self, value, item, details = None, entry = None):
		return value if value else None

	def processIdUniversal(self, value, item, details = None, entry = None):
		return value if value else None

	def processIdCollection(self, value, item, details = None, entry = None):
		return value if value else None

	def processIdItem(self, value, item, details = None, entry = None):
		return value if value else None

	def processHash(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashContainer(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashContainerMd5(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashContainerSha1(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashContainerSha256(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashContainerSha512(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashFile(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashFileMd5(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashFileSha1(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashFileSha256(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashFileSha512(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashOther(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashOtherMd5(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashOtherSha1(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashOtherSha256(self, value, item, details = None, entry = None):
		return value if value else None

	def processHashOtherSha512(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoQuality(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoQualityInexact(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoResolution(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoResolutionInexact(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoWidth(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoWidthInexact(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoHeight(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoHeightInexact(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoAspect(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoAspectInexact(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoCodec(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoDepth(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideoRange(self, value, item, details = None, entry = None):
		return value if value else None

	def processVideo3d(self, value, item, details = None, entry = None):
		return value if value else None

	def processAudioType(self, value, item, details = None, entry = None):
		return value if value else None

	def processAudioChannels(self, value, item, details = None, entry = None):
		return value if value else None

	def processAudioSystem(self, value, item, details = None, entry = None):
		return value if value else None

	def processAudioCodec(self, value, item, details = None, entry = None):
		return value if value else None

	def processAudioLanguage(self, value, item, details = None, entry = None):
		return value if value else None

	def processAudioLanguageInexact(self, value, item, details = None, entry = None):
		return value if value else None

	def processSubtitleType(self, value, item, details = None, entry = None):
		return value if value else None

	def processSubtitleLanguage(self, value, item, details = None, entry = None):
		return value if value else None

	def processSubtitleLanguageInexact(self, value, item, details = None, entry = None):
		return value if value else None

	def processReleaseType(self, value, item, details = None, entry = None):
		return value if value else None

	def processReleaseFormat(self, value, item, details = None, entry = None):
		return value if value else None

	def processReleaseEdition(self, value, item, details = None, entry = None):
		return value if value else None

	def processReleaseNetwork(self, value, item, details = None, entry = None):
		return value if value else None

	def processReleaseGroup(self, value, item, details = None, entry = None):
		return value if value else None

	def processReleaseUploader(self, value, item, details = None, entry = None):
		return value if value else None

	def processFileName(self, value, item, details = None, entry = None):
		return value if value else None

	def processFileNameInexact(self, value, item, details = None, entry = None):
		return value if value else None

	def processFileExtra(self, value, item, details = None, entry = None):
		return value if value else None

	def processFileSize(self, value, item, details = None, entry = None):
		return value

	def processFileSizeInexact(self, value, item, details = None, entry = None):
		return value

	def processFileContainer(self, value, item, details = None, entry = None):
		return value if value else None

	def processFilePack(self, value, item, details = None, entry = None):
		return value if value else None

	def processSourceType(self, value, item, details = None, entry = None):
		return value if value else None

	def processSourceSeeds(self, value, item, details = None, entry = None):
		return value

	def processSourceSeedsInexact(self, value, item, details = None, entry = None):
		return value

	def processSourceLeeches(self, value, item, details = None, entry = None):
		return value

	def processSourceLeechesInexact(self, value, item, details = None, entry = None):
		return value

	def processSourceTime(self, value, item, details = None, entry = None):
		return value

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		return value

	def processSourcePopularity(self, value, item, details = None, entry = None):
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		return value

	def processSourcePublisher(self, value, item, details = None, entry = None):
		return value if value else None

	def processSourceHoster(self, value, item, details = None, entry = None):
		return value if value else None

	##############################################################################
	# CLEAN
	##############################################################################

	# Function that can be overwritten by subclasses.
	# Further cleans the file name after it was processed by stream.py.
	@classmethod
	def cleanFileName(self, value):
		return value
