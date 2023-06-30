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
from lib.modules.tools import File, Matcher, Media, Settings, Tools, Regex
from lib.modules.interface import Translation
from lib.modules.stream import Stream

class ProviderLocal(ProviderBase):

	MatchDirectory	= 0.5	# Minimum title match ratio for directory names.
	MatchFile		= 0.3	# Minimum title match ratio for file names. Keep low, since file names can contain other stuff.

	Popularity		= 1		# Local provider's default popularity.

	def __init__(self, **kwargs):
		ProviderBase.__init__(self, **kwargs)
		self.mData['prefix'] = None

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		prefix 		= None,
		propagate	= True,
		**kwargs
	):
		if propagate: ProviderBase.initialize(self, **kwargs)
		self.mData['prefix'] = prefix

	##############################################################################
	# PREFIX
	##############################################################################

	def prefix(self):
		return self.mData['prefix']

	##############################################################################
	# ENABLED
	##############################################################################

	def enabledInternal(self):
		return Settings.getBoolean(self.prefix() + '.enabled')

	##############################################################################
	# PATH
	##############################################################################

	def paths(self, media):
		paths = []
		if Media.typeTelevision(media):
			paths.append(self.pathShow())
		else:
			paths.append(self.pathMovie())
			paths.append(self.pathDocumentary())
			paths.append(self.pathShort())
		paths.append(self.pathOther())
		return paths

	def path(self, type, label):
		prefix = self.prefix()
		if Settings.getInteger(prefix + '.location.selection') == 0: path = File.joinPath(Settings.path(prefix + '.location.combined'), Translation.string(label))
		else: path = Settings.path(prefix + '.location.' + type)
		return path

	def pathMovie(self):
		return self.path(type = 'movies', label = 'Movies')

	def pathDocumentary(self):
		return self.path(type = 'documentaries', label = 'Documentaries')

	def pathShort(self):
		return self.path(type = 'shorts', label = 'Shorts')

	def pathShow(self):
		return self.path(type = 'shows', label = 'Shows')

	def pathOther(self):
		return self.path(type = 'other', label = 'Other')

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media, titles, years = None, date = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, language = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		try:
			paths = self.paths(media = media)
			for path in paths:
				self.searchFind(path = path, media = media, titles = titles, years = years, numberSeason = numberSeason, numberEpisode = numberEpisode, language = language, pack = pack)
				self.statisticsUpdateSearch(page = True)
		except: self.logError()

	def searchMatch(self, name, parents, titles, years, numberSeason, numberEpisode):
		# This should be very lenient matching, since proper validation is done by Stream.
		# Only filter out clearly incorrect files, since disk I/O has do be reduced when the Extractor detects metadata from the file in Stream.

		name = Regex.remove(data = name, expression = Regex.Symbol, all = True)
		parents = [Regex.remove(data = i, expression = Regex.Symbol, all = True) for i in Tools.copy(parents)]

		extras = ['']
		if years: extras.extend(years['all'])
		extras.extend([numberSeason, numberEpisode])
		extras = [(' ' + str(i)) for i in extras if not i is None]

		for title in titles['processed']['all']:
			title = Regex.remove(data = title, expression = Regex.Symbol, all = True)
			titleLower = title.lower()
			extra = [(name + i) for i in extras]
			for i in extra:
				if titleLower in i.lower(): return True
				if Matcher.levenshtein(title, i) > ProviderLocal.MatchFile: return True
			for parent in parents:
				extra = [(parent + i) for i in extras]
				for i in extra:
					if titleLower in i.lower(): return True
					if Matcher.levenshtein(title, i) > ProviderLocal.MatchDirectory: return True

		return False

	def searchFind(self, path, media, titles, years, numberSeason, numberEpisode, language, pack, parents = []):
		if not path.endswith('\\') and not path.endswith('/'): path += '/' # Must end with a slash for tools.File.exists.

		if not self.stopped() and File.exists(path):
			directories, files = File.listDirectory(path)
			self.statisticsUpdateSearch(request = True)

			for file in files:
				if self.stopped(): break
				if self.searchMatch(name = file, parents = parents, titles = titles, years = years, numberSeason = numberSeason, numberEpisode = numberEpisode):
					self.searchProcess(path = File.joinPath(path, file), parents = parents)

			for directory in directories:
				if self.stopped(): break
				sub = Tools.copy(parents)
				sub.append(directory)
				self.searchFind(path = File.joinPath(path, directory), parents = sub, media = media, titles = titles, years = years, numberSeason = numberSeason, numberEpisode = numberEpisode, language = language, pack = pack)

	def searchProcess(self, path, parents):
		link = File.translate(path)

		fileExtra = '/'.join(parents)
		fileName = None
		fileSize = None
		sourceTime = None
		try: fileName = File.name(path = path, extension = True)
		except: pass
		try: fileSize = File.size(path = path)
		except: pass
		try: sourceTime = File.timeCreated(path = path)
		except: pass

		stream = self.resultStream(
			validateSize = False,
			extractor = True,

			link = link,

			fileName = fileName,
			fileExtra = fileExtra,
			fileSize = fileSize,

			sourceType = Stream.SourceTypeLocal,
			sourceTime = sourceTime,
			sourcePopularity = ProviderLocal.Popularity,

			thresholdSize = self.customSize(),
			thresholdTime = self.customTime(),
			thresholdPeers = self.customPeers(),
			thresholdSeeds = self.customSeeds(),
			thresholdLeeches = self.customLeeches(),
		)
		if stream: self.resultAdd(stream)
