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

from lib.providers.core.premium import ProviderPremium
from lib.modules.network import Networker
from lib.modules.cache import Cache
from lib.modules.stream import Stream
from lib.modules.tools import Tools, Video, Media
from lib.modules.concurrency import Lock

class ProviderDebrid(ProviderPremium):

	Lock		= None
	Data		= {}
	Threshold	= 0.7

	def __init__(self, **kwargs):
		ProviderPremium.__init__(self, **kwargs)
		if ProviderDebrid.Lock is None: ProviderDebrid.Lock = Lock()
		self.mVerifyCore = False

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		description		= None,
		rank			= 4,
		performance		= ProviderPremium.PerformanceGood,

		supportMovie	= True,
		supportShow		= True,
		supportPack		= False,

		searchThread	= False, # If a thread should be started to retrieve additional metadata for each stream after it was validated and before it is added to the final results.

		core			= None,

		propagate		= True,
		**kwargs
	):
		if not description: description = 'This provider scrapes your {name} cloud storage which is useful if you want to watch multiple movies or episodes from an already downloaded pack. Scraping takes longer the more files you have in your cloud storage.'

		if propagate:
			ProviderPremium.initialize(self,
				description		= description,
				rank			= rank,
				performance		= performance,

				supportMovie	= supportMovie,
				supportShow		= supportShow,
				supportPack		= supportPack,

				core			= core,

				**kwargs
			)

		self.mData['search'] = {'thread' : searchThread}

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		ProviderDebrid.Data = {}

	##############################################################################
	# VERIFY
	##############################################################################

	def verifyScrapeResult(self):
		result = ProviderPremium.VerifySuccess if self.mVerifyCore else ProviderPremium.VerifyFailure
		reason = None
		return result, reason

	def verifyCore(self):
		self.mVerifyCore = True

	##############################################################################
	# CACHE
	##############################################################################

	def cacheRequest(self, function, *args, **kwargs):
		# Make a copy of core to reset all its internal values, since core is used across threads and requests.
		function = Tools.getFunction(self.core(copy = True), function)

		# Only do queries once. Otherwise the same folders/files are requested by multiple providers (pack vs non-pack, alterntive titles, etc).
		cache = Cache.instance()
		kwargs2 = {key : value for key, value in kwargs.items() if not key in ['season', 'episode']}
		id = self.id() + cache.id(function, *args, **kwargs2)
		try: ProviderDebrid.Lock.acquire()
		except: pass
		if not id in ProviderDebrid.Data:
			ProviderDebrid.Data[id] = cache.execute(function, *args, **kwargs)
			self.statisticsUpdateSearch(request = True, page = True)
		try: ProviderDebrid.Lock.release()
		except: pass
		return ProviderDebrid.Data[id]

	##############################################################################
	# RESULT
	##############################################################################

	def resultAdd(self, stream):
		try:
			# Never mark debrid streams as file packs.
			# The parent directory name could contain pack keywords, but the retrund stream is always a single file.
			# Eg: The Orville S03E01 Electric Sheep 1080p DSNP WEBrip x265 DDP5.1 Atmos D0ct0rLew[SEV].mkv  [The Orville S03E01, E02, and E03 1080p DSNP WEBrip x265 DDP5.1 Atmos D0ct0rLew[SEV]]
			stream.filePackSet(Stream.FilePackDisabled)

			if not stream.sourcePublisher():
				domain = self.domain()
				if domain: stream.sourcePublisherSet(domain)
			if not stream.sourceHoster():
				hoster = Networker.linkDomain(link = stream.linkPrimary(), subdomain = False, topdomain = True, ip = True)
				if hoster: stream.sourceHosterSet(hoster)
			ProviderPremium.resultAdd(self, stream)
		except: self.logError()

	##############################################################################
	# SEARCH
	##############################################################################

	def searchThread(self):
		return self.mData['search']['thread']

	def searchValidName(self, name):
		# Since there is no guidance data to strip metadata from the file name, reduce the threshold to improve detection.
		# The threshold should be kept relatively low, since final validation will be done if the results are added.
		# This is only for parent folder detection, to reduce the number of subrequests that have to be made for individual folders.
		return Stream.titleValid(data = name, media = self.parameterMedia(), title = self.parameterTitles()['processed']['all'], adjust = ProviderDebrid.Threshold)

	def searchExclude(self, name):
		# Torrents/NZBs often contain other files that should not be included in the results.
		# Most of these are already filtered out, because of their small file size.
		# Others (like .ac3 files) are too large and should be excluded based on the extension.
		#Exclude = [
		#	'.rar', '.7z', # Allow ZIPs, since Kodi can sometimes play them.
		#	'.ac3', '.ac4',
		#	'.srt', '.txt', '.vtt', '.sub', '.ssf', '.usf',
		#	'.png', '.jpg', '.jpeg', '.bmp', '.gif',
		#	'.exe', '.aria', '.aria2',
		#	'.par', '.par1', '.par2', '.par3',
		#]
		#name = name.lower()
		#return any(name.endswith(exclude) for exclude in ProviderDebrid.Exclude)

		# Maybe better to just check for video extensions.
		return not Video.extensionValid(path = name)

	# files = [{'name', 'parent', 'parts', 'link (optional)', 'size (optional)', 'couunt (optional)', 'time (optional)'}, ...]
	def searchProcess(self, files, separateSize = True):
		lock = None
		try:
			if files:
				thread = self.searchThread()
				media = self.parameterMedia()
				titles = self.parameterTitles()
				titlesAll = titles['processed']['all']
				titlesMain = titles['processed']['main']

				count = 0
				added = {}
				items = [[], [], []]

				# First process files based on their name alone.
				# Only if no files from a folder was added by name, process them by the full path.
				# This is importantt for collections, eg:
				#	The Lord of The Rings
				#		- The Fellowship of the Ring.avi
				#		- The Two Towers.avi
				#		- The Return of the King.avi
				# If processing the full path from the start, all 3 files will be added, since it matches the collection title of "The Lord of The Rings".
				# Now the name is matched/validated first. If a file name is valid/addded, no other files in the folder are added based on the full path. Multiple files can still be added from the same folder if their name alone matches.
				# Only if no files were picked from a folder based on their name, are the files matched/validated on their full path.
				for item in files:
					try:
						name = item['name']
						if self.searchExclude(name): continue # Exclude unwanted files.

						if not separateSize:
							lower = name.lower()
							if not 'sample' in lower and not 'preview' in lower: count += 1

						parts = item['parts']
						if not parts: parts = []
						path = ' '.join(parts + [name])

						item['path'] = path

						# The path can be very long causing the validation to fail. Test the name first and then the path.
						# First try to match the name strictly, with the main titles (excluding the collection title), year, and numbers.
						# If that fails, match the name leniently, with the the main titles (excluding the collection title).
						# If that fails, match the full path leniently, with all titles (including the collection title).
						if self.searchValid(data = name, title = titlesMain, deviation = False): items[0].append(item)
						elif Stream.titleValid(data = name, media = media, title = titlesMain): items[1].append(item)
						elif Stream.titleValid(data = path, media = media, title = titlesAll): items[2].append(item)
					except: self.logError()

				if separateSize: count = None
				filePack = Stream.FilePackInternal if count and Media.isSerie(media) else None # So that OffCloud's show pack file sizes are estimated correctly.

				threads = []
				lock = self.priorityStart(lock = lock)
				for i in range(len(items)):
					for item in items[i]:
						try:
							if self.stopped(): break

							parent = item['parent']
							if i > 0 and parent in added: continue

							path = item['path']
							name = item['name']

							# Put the filename first, otherwise long names/paths require too long to scroll in Kodi's interface.
							if item['parts']: name += '  [%s]' % ('  |  ' . join(item['parts']))

							try: id = item['id']
							except: id = None
							try: link = item['link']
							except: link = None
							try: time = item['time']
							except: time = None
							try: size = item['size']
							except: size = None

							stream = self.resultStream(
								validateTitle = False,

								link = link,

								fileName = path,
								fileSize = size,
								filePack = filePack,

								sourceType = Stream.SourceTypePremium,
								sourceTime = time,

								thresholdSize = self.customSize(),
								thresholdTime = self.customTime(),
								thresholdPeers = self.customPeers(),
								thresholdSeeds = self.customSeeds(),
								thresholdLeeches = self.customLeeches(),
							)
							if stream:
								added[parent] = True
								stream.fileNameSet(name)
								if thread: threads.append(self.thread(self.searchAdd, id, stream))
								else: self.searchAdd(id = id, stream = stream)
						except: self.logError()
				self.priorityEnd(lock = lock)

				# Use at least 5 threads, since Premiumize can be a bit slow, since it retrieves additional metadata in searchAdd().
				if not self.stopped(): self.threadExecute(threads, limit = self.concurrencyTasks(level = 2, minimum = 5))
		except: self.logError()
		finally: self.priorityEnd(lock = lock)

	# Can be overwritten by subsclasses if additional metadata has to be retrieved.
	def searchAdd(self, id, stream):
		self.resultAdd(stream)
