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

	Name	= 'ExtendedInfo'
	Addon	= 'script.extendedinfo'

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

		if type == InformerBase.TypeMovie:
			parameters['info'] = 'extendedinfo'
			if tmdb: parameters['id'] = tmdb
			if imdb: parameters['imdb_id'] = imdb
			if title: parameters['name'] = title
		elif type == InformerBase.TypeShow:
			parameters['info'] = 'extendedtvinfo'
			if tmdb: parameters['id'] = tmdb
			if imdb: parameters['imdb_id'] = imdb
			if tvdb: parameters['tvdb_id'] = tvdb
			if title: parameters['name'] = title
		elif type == InformerBase.TypeSeason:
			parameters['info'] = 'seasoninfo'
			if tmdb: parameters['tvshow_id'] = tmdb
			if imdb: parameters['imdb_id'] = imdb
			if tvdb: parameters['tvdb_id'] = tvdb
			if title: parameters['tvshow'] = title
			if not season is None: parameters['season'] = season
		elif type == InformerBase.TypeEpisode:
			parameters['info'] = 'extendedepisodeinfo'
			if tmdb: parameters['tvshow_id'] = tmdb
			if imdb: parameters['imdb_id'] = imdb
			if tvdb: parameters['tvdb_id'] = tvdb
			if title: parameters['tvshow'] = title
			if not season is None: parameters['season'] = season
			if not episode is None: parameters['episode'] = episode
		elif type == InformerBase.TypePerson:
			parameters['info'] = 'extendedactorinfo'
			if title: parameters['name'] = title
		else:
			return None # Not supported.

		return parameters
