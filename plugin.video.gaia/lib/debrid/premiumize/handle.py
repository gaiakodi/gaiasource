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

from lib.debrid.base import Handle as HandleBase
from lib.debrid.premiumize.core import Core
from lib.debrid.premiumize.interface import Interface
from lib.modules.stream import Stream

class Handle(HandleBase):

	def __init__(self):
		self.mService = Core()
		self.mServices = None

		HandleBase.__init__(self, id = Core.Id, name = Core.Name, abbreviation = Core.Abbreviation, acronym = Core.Acronym, priority = Core.Priority, debrid = True, account = self.mService.accountValid())

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False, strict = False):
		if self.mService.accountValid():
			stream = item['stream']
			type = stream.sourceType()
			name = stream.fileName(generate = True)
			pack = stream.filePack(boolean = True)
			cached = stream.accessCachePremiumize()
			title = stream.metaTitle(title = Stream.TitleMain) # Do not include collection titles.
			year = stream.metaYear()
			season = stream.metaSeason()
			episode = stream.metaEpisode()

			if select: pack = True # Even non-season-pack archives should be selectable.

			return Interface().add(link = link, name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, close = close, type = type, cached = cached, select = select, cloud = cloud)
		return None

	def services(self, cached = True):
		try:
			if self.mServices is None and self.mService.accountValid():
				self.mServices = self.mService.servicesList(cached = cached, onlyEnabled = True)
		except: pass
		return self.mServices

	def enabled(self, type):
		return type in [Core.ModeTorrent, Core.ModeUsenet, Core.ModeHoster] and self.mService.streaming(type) and self.mService.accountValid()

	def supported(self, item, cloud = False):
		try: type = item['stream'].sourceType()
		except: type = item
		if type == Core.ModeTorrent or type == Core.ModeUsenet: return True
		return HandleBase.supported(self, item)
