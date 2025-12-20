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

	_Link	= ['https://clubnzb.com']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderSpotJson.initialize(self,
			name					= 'ClubNZB',
			description				= '{name} is a usenet indexer based on {fork}. The API contains many English titles, but is also a great source for other European languages.',
			rank					= 2,

			link					= Provider._Link,

			# Does not support ID searches.
			supportShowTvdb			= False,
			supportShowImdb			= False,
		)
