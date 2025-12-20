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

from lib.modules import tools
from lib.modules import network

class Core(object):

	# Modes
	ModeTorrent = 'torrent'
	ModeUsenet = 'usenet'
	ModeHoster = 'hoster'

	ErrorUnknown = 'unknown'
	ErrorUnavailable = 'unavailable'
	ErrorExternal = 'external'
	ErrorCancel = 'cancel'
	ErrorSelection = 'selection' # No file selected from list of items.
	ErrorPack = 'pack' # No file can be found in the pack that matches the title and year/season/episode.
	ErrorFormat = 'format' # File format not supported.

	Exclusions = (
		'.txt', '.nfo', '.srt',
		'.pdf', '.doc', '.docx', '.rtf',
		'.ini', '.lnk', '.csvs', '.xml', '.html', '.json', '.uue',
		'.md5', '.sha', '.sha1',

		'.jpg', '.jpeg', '.png', '.tiff', '.gif', '.bmp',

		'.nzb', '.torrent',

		'.zip', '.zipx', '.7z', '.7zip', '.s7z', '.rar', '.lzh', '.lzs', '.lha', '.par',
		'.gz', '.gzip', '.tar', '.bz2', '.lz', '.xz', '.zst', '.tgz', '.tbz2', '.tlz', '.txz', '.tzst',
		'.img', '.iso', '.udf', '.smi', '.dmg', '.nrg',

		'.exe', '.msi', '.apk',
	)

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, id, name, link):
		self.mId = id
		self.mName = name
		self.mLink = link

	def clone(self):
		return self.__class__()

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		pass

	##############################################################################
	# COMPONENTS
	##############################################################################

	@classmethod
	def interface(self):
		from lib.debrid.debrid import Debrid
		return Debrid._instance(id = self.Id, type = Debrid.TypeInterface)

	@classmethod
	def handle(self):
		from lib.debrid.debrid import Debrid
		return Debrid._instance(id = self.Id, type = Debrid.TypeHandle)

	##############################################################################
	# GENERAL
	##############################################################################

	def id(self):
		return self.mId

	def name(self):
		return self.mName

	def link(self):
		return self.mLink

	##############################################################################
	# ACCOUNT
	##############################################################################

	# Virtual
	def accountEnabled(self):
		return False

	# Virtual
	def accountValid(self):
		return False

	def accountAuthentication(self, settings = False):
		self.interface().accountAuthentication(settings = settings)

	##############################################################################
	# SERVICES
	##############################################################################

	# Virtual
	def servicesList(self, onlyEnabled = False):
		return []

	##############################################################################
	# ADD
	##############################################################################

	@classmethod
	def addError(self, error = ErrorUnknown):
		return self.addResult(error = error if error else Core.ErrorUnknown)

	@classmethod
	def addResult(self, error = None, id = None, link = None, notification = None, items = None, category = None, extra = None, loader = None, new = None, strict = False):
		extension = None
		if error is None:
			# Link can be to an external Kodi addon.
			if not link or (not network.Networker.linkIs(link) and not link.startswith('plugin:')):
				files = items.get('files') if items else None

				# Premiumize will return no link if none of the files are in a supported format.
				# Manually detect the foile format here.
				if files:
					try:
						for file in files:
							if file:
								fileStream = file.get('stream')
								fileLink = file.get('link')
								fileExtension = file.get('extension')
								if not fileExtension and fileLink: fileExtension = network.Networker.linkExtension(link = fileLink)
								excluded = fileLink.endswith(Core.Exclusions) if fileLink else None

								if fileStream is True or (fileLink and not excluded):
									# Reset if a valid link was found.
									error = None
									extension = None
									break
								elif fileStream is False or (fileLink and excluded):
									error = Core.ErrorFormat
									extension = fileExtension
					except: tools.Logger.error()

				if error is None:
					if files and strict: error = Core.ErrorPack
					else: error = Core.ErrorUnknown

		result = {
			'success' : (error is None),
			'error' : error,
			'id' : id,
			'link' : link,
			'items' : items,
			'notification' : notification,
			'category' : category,
			'loader' : loader,
			'new' : new,
			'extension' : extension,
		}
		if extra:
			for key, value in extra.items():
				result[key] = value
		return result

	##############################################################################
	# DELETE
	##############################################################################

	# Virtual
	def deletePlayback(self, id, pack = None, category = None):
		pass

	##############################################################################
	# SUPPORT
	##############################################################################

	@classmethod
	def supportedModes(self):
		return {}

	@classmethod
	def supportedTorrent(self):
		return Core.ModeTorrent in self.supportedModes()

	@classmethod
	def supportedUsenet(self):
		return Core.ModeUsenet in self.supportedModes()

	@classmethod
	def supportedHoster(self):
		return Core.ModeHoster in self.supportedModes()

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {}

	# Virtual
	def cached(self, id, timeout = None, callback = None, sources = None):
		pass

	##############################################################################
	# STREAMING
	##############################################################################

	def streaming(self, mode):
		if tools.Settings.getInteger('stream.general.handle') == 2:
			if tools.Settings.getInteger('stream.general.handle.%s' % mode) == 0: return False

		setting = tools.Settings.getInteger('stream.gaia.handle')
		if setting == 2:
			if tools.Settings.getInteger('stream.gaia.handle.%s' % mode) >= 1: return True
		elif setting >= 1:
			return True

		return False

	def streamingTorrent(self, support = True):
		if support and not self.supportedTorrent(): return False
		return self.streaming(Core.ModeTorrent)

	def streamingUsenet(self, support = True):
		if support and not self.supportedUsenet(): return False
		return self.streaming(Core.ModeUsenet)

	def streamingHoster(self, support = True):
		if support and not self.supportedHoster(): return False
		return self.streaming(Core.ModeHoster)
