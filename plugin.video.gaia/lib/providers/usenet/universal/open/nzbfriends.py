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

from lib.providers.core.nzbreader import ProviderNzbreader2

class Provider(ProviderNzbreader2):

	_Link	= ['http://nzbfriends.com']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderNzbreader2.initialize(self,
			name	= 'NZBFriends',
			link	= Provider._Link,

			# Update (2025-12):
			# The website does not return any results anymore: "No collections found".
			# More info under nzbID.
			status	= ProviderNzbreader2.StatusImpaired,
		)
