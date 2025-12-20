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

from lib.providers.core.web import ProviderWeb
from lib.modules.tools import Tools, Regex, Converter

class ProviderJson(ProviderWeb):

	def __init__(self, **kwargs):
		ProviderWeb.__init__(self, **kwargs)

	def initialize(self,
		# Attributes can be None (do not extract), a string/integer (single key/index to access the JSON element), a list (multiple keys/indexes to access a nested JSON element), or a list-of-lists (same as list, but multiple values are extracted together - the value passed along to processing will then contain a list of extracted values)

		extractData						= None, # A regular expression which can be used to extract the JSON string if it is not returned as JSON data, but as part of some text. The JSON might for instance be hardcoded into the JS of an HTML page.

		extractList						= None,	# The outer list/array containing the individual items.

		# Extract a full link or path from JSON that points to a sub-page. The sub-page is requested and passed into the extract functions.
		# Can be used to extract additional metadata from a sub-page for each item in extractList.
		# searchConcurrency will be set to True if it was not already set.
		# Will only be executed if the file name is valid.
		extractDetails					= None,

		extractLink						= None,

		extractIdLocal					= None,
		extractIdUniversal				= None,
		extractIdCollection				= None,
		extractIdItem					= None,

		extractHash						= None,
		extractHashContainer			= None,
		extractHashContainerMd5			= None,
		extractHashContainerSha1		= None,
		extractHashContainerSha256		= None,
		extractHashContainerSha512		= None,
		extractHashFile					= None,
		extractHashFileMd5				= None,
		extractHashFileSha1				= None,
		extractHashFileSha256			= None,
		extractHashFileSha512			= None,
		extractHashOther				= None,
		extractHashOtherMd5				= None,
		extractHashOtherSha1			= None,
		extractHashOtherSha256			= None,
		extractHashOtherSha512			= None,

		extractVideoQuality				= None,
		extractVideoQualityInexact		= None,
		extractVideoResolution			= None,
		extractVideoResolutionInexact	= None,
		extractVideoWidth				= None,
		extractVideoWidthInexact		= None,
		extractVideoHeight				= None,
		extractVideoHeightInexact		= None,
		extractVideoAspect				= None,
		extractVideoAspectInexact		= None,
		extractVideoCodec				= None,
		extractVideoDepth				= None,
		extractVideoRange				= None,
		extractVideo3d					= None,

		extractAudioType				= None,
		extractAudioChannels			= None,
		extractAudioSystem				= None,
		extractAudioCodec				= None,
		extractAudioLanguage			= None,
		extractAudioLanguageInexact		= None,

		extractSubtitleType				= None,
		extractSubtitleLanguage			= None,
		extractSubtitleLanguageInexact	= None,

		extractReleaseType				= None,
		extractReleaseFormat			= None,
		extractReleaseEdition			= None,
		extractReleaseNetwork			= None,
		extractReleaseGroup				= None,
		extractReleaseUploader			= None,

		extractFileName					= None,
		extractFileNameInexact			= None,
		extractFileExtra				= None,
		extractFileSize					= None,
		extractFileSizeInexact			= None,
		extractFileContainer			= None,
		extractFilePack					= None,

		extractSourceType				= None,
		extractSourceSeeds				= None,
		extractSourceSeedsInexact		= None,
		extractSourceLeeches			= None,
		extractSourceLeechesInexact		= None,
		extractSourceTime				= None,
		extractSourceTimeInexact		= None,
		extractSourcePopularity			= None,
		extractSourceApproval			= None,
		extractSourcePublisher			= None,
		extractSourceHoster				= None,

		propagate						= True,
		**kwargs
	):
		if propagate: ProviderWeb.initialize(self, **kwargs)

		if extractData is None: self.extractData = (lambda data, details = False: Converter.jsonFrom(data))
		elif not extractData is False: self.extractData = (lambda data, details = False: self.extractJsonData(data, extractData))

		if not extractList is None: self.extractList = (lambda data: self.extractJson(item = data, keys = extractList))

		if not extractDetails is None:
			if self.searchConcurrency() is None: self.searchConcurrencySet(True)
			self.extractDetails = (lambda data: self.extractJson(item = item, keys = extractDetails))

		if not extractLink is None: self.extractLink = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractLink))

		if not extractIdLocal is None: self.extractIdLocal = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractIdLocal))
		if not extractIdUniversal is None: self.extractIdUniversal = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractIdUniversal))
		if not extractIdCollection is None: self.extractIdCollection = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractIdCollection))
		if not extractIdItem is None: self.extractIdItem = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractIdItem))

		if not extractHash is None: self.extractHash = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHash))
		else:
			if not extractHashContainer is None: self.extractHashContainer = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashContainer))
			else:
				if not extractHashContainerMd5 is None: self.extractHashContainerMd5 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashContainerMd5))
				if not extractHashContainerSha1 is None: self.extractHashContainerSha1 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashContainerSha1))
				if not extractHashContainerSha256 is None: self.extractHashContainerSha256 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashContainerSha256))
				if not extractHashContainerSha512 is None: self.extractHashContainerSha512 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashContainerSha512))
			if not extractHashFile is None: self.extractHashFile = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashFile))
			else:
				if not extractHashFileMd5 is None: self.extractHashFileMd5 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashFileMd5))
				if not extractHashFileSha1 is None: self.extractHashFileSha1 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashFileSha1))
				if not extractHashFileSha256 is None: self.extractHashFileSha256 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashFileSha256))
				if not extractHashFileSha512 is None: self.extractHashFileSha512 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashFileSha512))
			if not extractHashOther is None: self.extractHashOther = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashOther))
			else:
				if not extractHashOtherMd5 is None: self.extractHashOtherMd5 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashOtherMd5))
				if not extractHashOtherSha1 is None: self.extractHashOtherSha1 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashOtherSha1))
				if not extractHashOtherSha256 is None: self.extractHashOtherSha256 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashOtherSha256))
				if not extractHashOtherSha512 is None: self.extractHashOtherSha512 = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractHashOtherSha512))

		if not extractVideoQuality is None: self.extractVideoQuality = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoQuality))
		if not extractVideoQualityInexact is None: self.extractVideoQualityInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoQualityInexact))
		if not extractVideoResolution is None: self.extractVideoResolution = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoResolution))
		if not extractVideoResolutionInexact is None: self.extractVideoResolutionInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoResolutionInexact))
		if not extractVideoWidth is None: self.extractVideoWidth = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoWidth))
		if not extractVideoWidthInexact is None: self.extractVideoWidthInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoWidthInexact))
		if not extractVideoHeight is None: self.extractVideoHeight = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoHeight))
		if not extractVideoHeightInexact is None: self.extractVideoHeightInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoHeightInexact))
		if not extractVideoAspect is None: self.extractVideoAspect = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoAspect))
		if not extractVideoAspectInexact is None: self.extractVideoAspectInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoAspectInexact))
		if not extractVideoCodec is None: self.extractVideoCodec = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoCodec))
		if not extractVideoDepth is None: self.extractVideoDepth = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoDepth))
		if not extractVideoRange is None: self.extractVideoRange = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideoRange))
		if not extractVideo3d is None: self.extractVideo3d = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractVideo3d))

		if not extractAudioType is None: self.extractAudioType = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractAudioType))
		if not extractAudioChannels is None: self.extractAudioChannels = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractAudioChannels))
		if not extractAudioSystem is None: self.extractAudioSystem = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractAudioSystem))
		if not extractAudioCodec is None: self.extractAudioCodec = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractAudioCodec))
		if not extractAudioLanguage is None: self.extractAudioLanguage = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractAudioLanguage))
		if not extractAudioLanguageInexact is None: self.extractAudioLanguageInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractAudioLanguageInexact))

		if not extractSubtitleType is None: self.extractSubtitleType = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSubtitleType))
		if not extractSubtitleLanguage is None: self.extractSubtitleLanguage = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSubtitleLanguage))
		if not extractSubtitleLanguageInexact is None: self.extractSubtitleLanguageInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSubtitleLanguageInexact))

		if not extractReleaseType is None: self.extractReleaseType = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractReleaseType))
		if not extractReleaseFormat is None: self.extractReleaseFormat = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractReleaseFormat))
		if not extractReleaseEdition is None: self.extractReleaseEdition = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractReleaseEdition))
		if not extractReleaseNetwork is None: self.extractReleaseNetwork = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractReleaseNetwork))
		if not extractReleaseGroup is None: self.extractReleaseGroup = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractReleaseGroup))
		if not extractReleaseUploader is None: self.extractReleaseUploader = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractReleaseUploader))

		if extractFileName is True: self.extractFileName = (lambda item, details = None, entry = None: True)
		elif not extractFileName is None: self.extractFileName = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractFileName))
		if extractFileNameInexact is True: self.extractFileNameInexact = (lambda item, details = None, entry = None: True)
		elif not extractFileNameInexact is None: self.extractFileNameInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractFileNameInexact))
		if not extractFileExtra is None: self.extractFileExtra = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractFileExtra))
		if not extractFileSize is None: self.extractFileSize = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractFileSize))
		if not extractFileSizeInexact is None: self.extractFileSizeInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractFileSizeInexact))
		if not extractFileContainer is None: self.extractFileContainer = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractFileContainer))
		if not extractFilePack is None: self.extractFilePack = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractFilePack))

		if not extractSourceType is None: self.extractSourceType = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourceType))
		if not extractSourceSeeds is None: self.extractSourceSeeds = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourceSeeds))
		if not extractSourceSeedsInexact is None: self.extractSourceSeedsInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourceSeedsInexact))
		if not extractSourceLeeches is None: self.extractSourceLeeches = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourceLeeches))
		if not extractSourceLeechesInexact is None: self.extractSourceLeechesInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourceLeechesInexact))
		if not extractSourceTime is None: self.extractSourceTime = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourceTime))
		if not extractSourceTimeInexact is None: self.extractSourceTimeInexact = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourceTimeInexact))
		if not extractSourcePopularity is None: self.extractSourcePopularity = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourcePopularity))
		if not extractSourceApproval is None: self.extractSourceApproval = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourceApproval))
		if not extractSourcePublisher is None: self.extractSourcePublisher = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourcePublisher))
		if not extractSourceHoster is None: self.extractSourceHoster = (lambda item, details = None, entry = None: self.extractJson(item = item, details = details, entry = entry, keys = extractSourceHoster))

	def extractJsonData(self, data, expression):
		match = Regex.extract(data = data, expression = expression)
		if match: return Converter.jsonFrom(match)
		else: return None

	def extractJson(self, item, keys, details = None, entry = None):
		try:
			if Tools.isArray(keys):
				data = item
				if Tools.isArray(keys[0]):
					if keys[0][0] == ProviderWeb.Details:
						data = details
						keys = keys[1:]
					return [Tools.dictionaryGet(dictionary = data, keys = key, merge = True) for key in keys]
				else:
					if keys[0] == ProviderWeb.Details:
						data = details
						keys = keys[1:]
					return Tools.dictionaryGet(dictionary = data, keys = keys, merge = True)
			else:
				return Tools.dictionaryGet(dictionary = item, keys = keys, merge = True)
		except: self.logError()
