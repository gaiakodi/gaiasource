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

from lib.informers import Informer as InformerBase

class Informer(InformerBase):

	Name	= 'EmbuaryInfo'
	Addon	= 'script.embuary.info'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		InformerBase.__init__(self, name = Informer.Name, addon = Informer.Addon)

	##############################################################################
	# PARAMETERS
	##############################################################################

	def parameters(self, type, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None):
		parameters = {}

		if type == InformerBase.TypeMovie: parameters['call'] = 'movie'
		elif type == InformerBase.TypeShow or type == InformerBase.TypeSeason: parameters['call'] = 'tv'
		elif type == InformerBase.TypePerson: parameters['call'] = 'person'
		else: return None # Not supported.

		if tmdb: parameters['tmdb_id'] = tmdb
		elif imdb: parameters['external_id'] = imdb
		elif tvdb: parameters['external_id'] = tvdb
		elif title: parameters['query'] = title

		if not year is None: parameters['year'] = year
		if not season is None: parameters['season'] = season

		return parameters
