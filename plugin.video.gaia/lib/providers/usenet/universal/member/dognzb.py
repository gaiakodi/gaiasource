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

# https://nzbndx.com/apihelp

from lib.providers.core.newz import ProviderNewznab

class Provider(ProviderNewznab):

	_Link	= ['https://api.dognzb.cr']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderNewznab.initialize(self,
			name					= 'DOGnzb',
			description				= '{name} is a usenet indexer based on {fork}. The API contains many English titles, but is also a great source for other European languages. {name} offers both trial and premium accounts, but registration of new accounts is often not open and requires an invitation. {name}\'s API has a number of bugs and timeout issues and should therefore not be the first choice for a usenet indexer.',
			rank					= 4,
			performance				= ProviderNewznab.PerformanceGood,

			link					= Provider._Link,

			# DOGnzb has many API and timeout problems.
			# Sometimes the API returns an XML response without results.
			# Retry and there is a good chance of the results being retruned.
			# Might be a temporary issue.
			retryCount				= 2,
			retryExpression			= r'(^<\?xml\s|504\*gateway)',

			# Does not support IMDb for shows, specials, and packs.
			supportShowImdb			= False,

			# Returns indiviual episodes, but not packs.
			supportPackShowTvdb		= False,

			# Returns special episode (S08E00) with ID and "ep=0".
			# Returns individual episodes with query "s01".
			# Returns nothing with query "season 1".
			supportPackSeason		= False,

			# Returns indiviual episodes with "ep=0".
			supportPackSeasonTitle	= False,
		)
