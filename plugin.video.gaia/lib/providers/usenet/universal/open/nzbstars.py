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

# New provider working via the API (post 2025-12).

from lib.providers.core.spot import ProviderSpotJson

class Provider(ProviderSpotJson):

	_Link	= ['https://nzbstars.com']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderSpotJson.initialize(self,
			name					= 'NZBStars',
			description				= '{name} is a usenet indexer. The API contains many English titles, but is also a great source for other European languages. {name} has various bugs, incomplete metadata, missing {containers} and file sizes, and should therefore not be the first choice for a usenet indexer.',
			rank					= 2,

			link					= Provider._Link,

			# Does not support ID searches.
			# Returns error: IMDB information returned is invalid.
			supportMovieImdb		= False,

			# Does not support ID searches.
			supportShowTvdb			= False,
			supportShowImdb			= False,
		)


# Old provider using HTML (pre 2025).
'''
# When executing an API query in the browser, a JS error is show: "This query is not allowed!".
# Executing the query with CURL mostly returns "Missing parameter" errors.
# A few type of queries actually execute, but return random results.

from lib.providers.core.spot import ProviderSpotHtml

class Provider(ProviderSpotHtml):

	_Link	= ['https://nzbstars.com']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderSpotHtml.initialize(self,
			name					= 'NZBStars',
			description				= '{name} is a usenet indexer. The API contains many English titles, but is also a great source for other European languages. {name} has various bugs, incomplete metadata, missing {containers} and file sizes, and should therefore not be the first choice for a usenet indexer.',
			rank					= 2,

			link					= Provider._Link,
		)
'''
