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

from lib.providers.core.base import ProviderBase
from lib.providers.core.json import ProviderJson
from lib.providers.core.html import ProviderHtml

class ProviderUsenet(object):

	CustomSize	= {ProviderBase.SettingsDescription : 'Only retrieve {containers} that have a minimum file size. Some providers have indexed some {containers} with an incorrect small size, although the actual files are a lot larger. In some cases a small file size can indicate a corrupt {container}. Adjust the minimum size if small {containers} should also be included in the results.'}
	CustomTime	= {ProviderBase.SettingsDescription : 'The maximum age of the {container} upload. Older {containers} will be discarded. Most usenet providers have a retention time of more than 10 years. Specifying a maximum age is therefore unnecessary in most cases and will only lead to less {containers} being found.'}

class ProviderUsenetJson(ProviderJson):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		customSize	= True,
		customTime	= True,
		**kwargs
	):
		ProviderJson.initialize(self,
			customSize	= ProviderUsenet.CustomSize if customSize is True else customSize,
			customTime	= ProviderUsenet.CustomTime if customTime is True else customTime,
			**kwargs
		)

class ProviderUsenetHtml(ProviderHtml):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		customSize	= True,
		customTime	= True,
		**kwargs
	):
		ProviderHtml.initialize(self,
			customSize	= ProviderUsenet.CustomSize if customSize is True else customSize,
			customTime	= ProviderUsenet.CustomTime if customTime is True else customTime,
			**kwargs
		)
