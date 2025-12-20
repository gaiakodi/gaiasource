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

from lib.providers.core.nzbreader import ProviderNzbreader1

class Provider(ProviderNzbreader1):

	_Link	= ['http://nzbid.net']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderNzbreader1.initialize(self,
			name	= 'nzbID',
			link	= Provider._Link,

			# Update (2025-12):
			# The website does not return any results anymore: "No collections found".
			# This is the case for most common search queries. Although some other queries ("the", "nzb", "*") does return results.
			# Searching "mkv" returns very few results, all porn. So maybe they only index porn now.
			# This seems to be the same with other NzbReader sites, like NZBFriends and FindNZB.
			status	= ProviderNzbreader1.StatusImpaired,
		)
