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

from lib.providers.core.spot import ProviderSpotJson

class Provider(ProviderSpotJson):

	_Link	= ['https://spotnzb.xyz']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderSpotJson.initialize(self,
			name					= 'SpotNZB',
			description				= '{name} is a usenet indexer based on {fork}. The API contains many English titles, but is also a great source for other European languages.',
			rank					= 4,

			# Domain is unresponsive.
			# Update (2025-12): Domain still down.
			status					= ProviderSpotJson.StatusDead,

			link					= Provider._Link,

			# Does not support ID searches for shows.
			# Returns random results.
			supportShowTvdb			= False,
			supportShowImdb			= False,

			# Returns seasons instead of special episodes.
			supportSpecialTitle		= False,

			# Does not support searching with title and season/episode.
			supportPackSeasonTitle	= False,
		)
