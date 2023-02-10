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
from lib.modules.tools import Time, System, Media
from lib.modules.interface import Loader, Dialog, Directory
from lib.modules.window import WindowBackground, WindowStreams

from lib.meta.tools import MetaTools
from lib.meta.image import MetaImage

class Informer(InformerBase):

	Name	= 'Kodi'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		InformerBase.__init__(self, name = Informer.Name)

	##############################################################################
	# PARAMETERS
	##############################################################################

	def parameters(self, type, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, episode = None):
		parameters = {}

		if type == InformerBase.TypeMovie: parameters['call'] = 'movie'
		elif type == InformerBase.TypeSet: parameters['call'] = 'set'
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

	##############################################################################
	# DIALOG
	##############################################################################

	def _dialog(self, type = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, episode = None, metadata = None, wait = True):
		if metadata:
			# Get rid of possible double year (one from the skin and the other one that was forcefully added to the title).
			if 'originaltitle' in metadata and metadata['originaltitle']: metadata['title'] = metadata['originaltitle']

			if not type:
				try: type = metadata['mediatype']
				except: type = None
				if type == 'tvshow': type = Informer.TypeShow
				elif type == 'season': type = Informer.TypeSeason
				elif type == 'episode': type = Informer.TypeEpisode
				elif type == 'person': type = Informer.TypePerson
				elif type == 'set': type = Informer.TypeSet
				else: type = Informer.TypeMovie

		if type in [InformerBase.TypeSet, InformerBase.TypeMovie, InformerBase.TypeShow, InformerBase.TypeSeason, InformerBase.TypeEpisode]:
			# Wait to determine if WindowStreams is showing.
			# Otheriwse the current dialog will be the Loader.
			# Keep the loader when the calls comes from external widgets, since widgets need longer to load the infi dialog.
			if not System.originWidget(): Loader.hide(wait = True)

			# The item must be selected in the Kodi GUI for the info dialog to work.
			# If the context menu is still open, Kodi will not be able to get the selected movie/show.
			#Time.sleep(0.5) # 0.1 is often too little waiting time.
			#System.execute('Action(Info)')

			background = None
			item = Directory(cache = False, lock = False).item()
			if metadata:
				metatools = MetaTools.instance()
				metadataKodi = metatools.clean(metadata = metadata, studio = False)
				item = metatools.item(item = item, metadata = metadata, clean = metadataKodi)
				try: background = item['images'][MetaImage.TypeFanart]
				except: pass
				item = item['item']

			# With the default Estaury skin, there is no background for the movie info dialog when launched from WindowStreams.
			# This is probably a Kodi or skin bug.
			# Show a background window below to make it look better.
			Time.sleep(0.3) # In rare cases WindowStreams.currentType() only updates after a little while.
			if WindowStreams.currentType(type = WindowStreams):
				WindowBackground.show(observeDialog = WindowBackground.IdWindowInformation, backgroundType = WindowBackground.BackgroundFanart, background = background)

			Dialog.info(item)

			return True
		else:
			return None # Not supported.
