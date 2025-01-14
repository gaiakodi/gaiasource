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

# https://scenenzbs.com/apihelp

from lib.providers.core.newz import ProviderNewznab

class Provider(ProviderNewznab):

	_Link	= ['https://scenenzbs.com']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderNewznab.initialize(self,
			name					= 'SceneNZBs',
			description				= '{name} is a usenet indexer based on {fork}. The API contains mostly German titles, but occasionaly also has English titles. {name} offers both free and premium accounts.',
			rank					= 4, # Since it mostly has German content only.

			link					= Provider._Link,

			# Does not return any episodes.
			supportShowQuery		= False,

			# Returns individual episodes.
			supportPackShow			= False,

			# Does not return any episodes.
			supportPackSeasonQuery	= False,
		)
