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

# https://ninjacentral.co.za/apihelp

from lib.providers.core.newz import ProvideNzedb

class Provider(ProvideNzedb):

	_Link	= ['https://ninjacentral.co.za']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProvideNzedb.initialize(self,
			name					= 'NinjaCentral',
			description				= '{name} is a usenet indexer based on {fork}. The API contains many English titles, but is also a great source for other European languages. {name} offers both free and premium accounts. {name} has few results and should therefore not be the first choice for a usenet indexer.',
			rank					= 4,

			link					= Provider._Link,

			# Does not support IMDb for shows, specials, and packs.
			supportShowImdb			= False,

			# Does not support searches with title and season/episode.
			supportShowTitle		= False,
		)
