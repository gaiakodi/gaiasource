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

	_Link	= ['https://findnzb.net']

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderNzbreader1.initialize(self,
			name	= 'FindNZB',
			link	= Provider._Link,

			# Update (2025-12):
			# The website does not return any results anymore: "No collections found".
			# More info under nzbID.
			status	= ProviderNzbreader1.StatusImpaired,
		)
