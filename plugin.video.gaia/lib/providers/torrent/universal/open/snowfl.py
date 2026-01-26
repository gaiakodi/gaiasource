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

from lib.providers.core.json import ProviderJson
from lib.modules.tools import Math, Regex, Time

class Provider(ProviderJson):

	_Link					= ['https://snowfl.com']
	_Unblock				= {ProviderJson.UnblockFormat1 : 'snowfl', ProviderJson.UnblockFormat2 : 'snowfl', ProviderJson.UnblockFormat3 : 'snowfl', ProviderJson.UnblockFormat4 : 'snowfl'}
	_Path					= '%s/%s/%s/%s/%s/%s/1'
	_Script					= 'b.min.js'

	_ParameterSeed			= 'SEED'
	_ParameterNone			= 'NONE'
	_ParameterVersion		= 'v'
	_ParameterTimestamp		= '_'

	_AttributeCode			= 'code'
	_AttributeMagnet		= 'magnet'
	_AttributeName			= 'name'
	_AttributeSize			= 'size'
	_AttributeAge			= 'age'
	_AttributeType			= 'type'
	_AttributeSeeds			= 'seeder'
	_AttributeLeeches		= 'leecher'
	_AttributeTrusted		= 'trusted'
	_AttributeNsfw			= 'nsfw'

	_ExpressionType			= r'(?:^|\s|\-|:|>|\/)\s*(video|movie|tv|show|episode|hd|4k|3d|hdr|x264|x265|other|foreign)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderJson.initialize(self,
			name						= 'Snowfl',
			description					= '{name} is a less-known {container} site. The API contains results in various languages, but most of them are in English. {name} has various mechanisms to prevent automated scraping and might therefore not always work or not return all available links.',
			rank						= 4,
			performance					= ProviderJson.PerformanceGood,

			link						= Provider._Link,
			unblock						= Provider._Unblock,

			customVerified				= True,
			customAdult					= True,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			accountAuthentication		= {
											ProviderJson.ProcessMode : ProviderJson.AccountModeScrape,
											ProviderJson.ProcessRequest : {
												ProviderJson.RequestPath : Provider._Script,
												ProviderJson.RequestData : {
													Provider._ParameterVersion : self.puzzelGenerate(), # Must add random data, otherwise the old JS script is returned.
												},

											},
											ProviderJson.ProcessExtract : {
												ProviderJson.RequestData : r'var\s*[a-z0-9]+\s*=\s*"((?!abcde)[a-z0-9]{30,})"', # The size of the string does not always have the same length (eg sometimes 35, other times 34).
											},
										},

			offsetStart					= 0,
			offsetIncrease				= 1,

			formatEncode				= ProviderJson.FormatEncodeQuote,

			searchQuery					= [
											{
												ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
												ProviderJson.RequestPath : Provider._Path % (ProviderJson.TermAuthentication, ProviderJson.TermQuery, self.puzzelGenerate(), ProviderJson.TermOffset, Provider._ParameterSeed, Provider._ParameterNone),
												ProviderJson.RequestData : {
													Provider._ParameterTimestamp : Time.timestamp(),
												},
											},
										],

			extractLink					= Provider._AttributeMagnet,
			extractFileName				= Provider._AttributeName,
			extractFileSize				= Provider._AttributeSize,
			extractSourceTimeInexact 	= Provider._AttributeAge,
			extractSourceSeeds			= Provider._AttributeSeeds,
			extractSourceLeeches		= Provider._AttributeLeeches,
		)

	##############################################################################
	# PUZZEL
	##############################################################################

	def puzzelGenerate(self):
		# Generate a random string, as done in https://snowfl.com/b.min.js
		# It seems that any random string works, even if it is not generated with this function.
		'''
			randomString: function() {
	            for (var r = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP1234567890", t = "", e = 0; e < 8; e++) {
	                var a = Math.floor(Math.random() * r.length);
	                t += r.charAt(a)
	            }
	            return t
	        }
		'''

		code = ''
		alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP1234567890'
		length = len(alphabet)
		for i in range(8):
			number = Math.roundDown(Math.random() * length)
			code += alphabet[number]
		return code

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		if not Regex.match(data = item[Provider._AttributeType], expression = Provider._ExpressionType): return ProviderJson.Skip
		elif self.customVerified() and not item[Provider._AttributeTrusted]: return ProviderJson.Skip
		elif self.customAdult() and item[Provider._AttributeNsfw]: return ProviderJson.Skip

	def processLink(self, value, item, details = None, entry = None):
		# A lot of the entries do not have a magnet.
		return value if value else ProviderJson.Skip
