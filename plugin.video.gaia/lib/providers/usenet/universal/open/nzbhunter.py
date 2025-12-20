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

from lib.providers.core.spot import ProviderSpotHtml

# When executing an API query in the browser, a JS error is show: "This query is not allowed!".
# Executing the query with CURL mostly returns "Missing parameter" errors.
# A few type of queries actually execute, but return random results.

class Provider(ProviderSpotHtml):

	_Link	= ['https://nzbhunter.com']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderSpotHtml.initialize(self,
			name					= 'NZBhunter',
			description				= '{name} is a usenet indexer. The API contains many English titles, but is also a great source for other European languages. {name} has various bugs, incomplete metadata, missing {containers} and file sizes, and should therefore not be the first choice for a usenet indexer.',
			rank					= 2,

			# Update (2025-01): Redirects to a Plesk site.
			# Update (2025-12): Still the same.
			status					= ProviderSpotHtml.StatusDead,

			link					= Provider._Link,
		)
