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

from lib.modules.tools import File, Tools
from lib.modules.concurrency import Lock

class Debrid(object):

	TypeCore		= 'core'
	TypeInterface	= 'interface'
	TypeHandle		= 'handle'

	Meta			= {
						'premiumize'	: {'id' : 'premiumize',		'name' : 'Premiumize',		'abbreviation' : 'P',	'acronym' : 'PM'},
						'offcloud'		: {'id' : 'offcloud',		'name' : 'OffCloud',		'abbreviation' : 'O',	'acronym' : 'OC'},
						'realdebrid'	: {'id' : 'realdebrid',		'name' : 'RealDebrid',		'abbreviation' : 'R',	'acronym' : 'RD'},
						'debridlink'	: {'id' : 'debridlink',		'name' : 'DebridLink',		'abbreviation' : 'D',	'acronym' : 'DL'},
						'alldebrid'		: {'id' : 'alldebrid',		'name' : 'AllDebrid',		'abbreviation' : 'A',	'acronym' : 'AD'},
						'linksnappy'	: {'id' : 'linksnappy',		'name' : 'LinkSnappy',		'abbreviation' : 'L',	'acronym' : 'LS'},
						'megadebrid'	: {'id' : 'megadebrid',		'name' : 'MegaDebrid',		'abbreviation' : 'M',	'acronym' : 'MD'},
						'rapidpremium'	: {'id' : 'rapidpremium',	'name' : 'RapidPremium',	'abbreviation' : 'R',	'acronym' : 'RP'},
						'simplydebrid'	: {'id' : 'simplydebrid',	'name' : 'SimplyDebrid',	'abbreviation' : 'S',	'acronym' : 'SD'},
						'smoozed'		: {'id' : 'smoozed',		'name' : 'Smoozed',			'abbreviation' : 'S',	'acronym' : 'SM'},
					}

	Lock			= Lock()
	Instances		= {}

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True, full = True):
		for instances in Debrid.Instances.values():
			if instances:
				for instance in instances:
					try: instance.reset(settings = settings)
					except: pass

		if settings:
			Debrid.Instances = {}

		if full:
			from lib.debrid.external import External
			External.reset(settings = settings)

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _path(self):
		return File.directory(__file__)

	@classmethod
	def _import(self):
		import importlib
		directories, files = File.listDirectory(self._path(), absolute = False)
		for directory in directories:
			if not directory.startswith('_'):
				# Only import if not already imported.
				# Otherwise import_module(...) can end up in deadlock if this functions is called in parallel.
				# Eg: _frozen_importlib._DeadlockError: deadlock detected by _ModuleLock('lib.debrid.easynews')
				module = 'lib.debrid.' + directory
				if not importlib.find_loader(module): importlib.import_module(module)

	@classmethod
	def _instances(self, type = TypeCore):
		if not type in Debrid.Instances:
			Debrid.Lock.acquire()
			if not type in Debrid.Instances:
				import importlib
				instances = []
				directories, files = File.listDirectory(self._path(), absolute = False)
				for directory in directories:
					if not directory.startswith('_'):
						module = importlib.import_module('lib.debrid.' + directory + '.' + type.lower())
						try: module = getattr(module, type.capitalize())()
						except: continue # If does not have the class (eg: EasyNews Handle).
						instances.append(module)
				Debrid.Instances[type] = instances
			Debrid.Lock.release()
		return Debrid.Instances[type]

	@classmethod
	def _instance(self, id, type = TypeCore):
		import importlib
		module = importlib.import_module('lib.debrid.%s.%s' % (id, type))
		try: return getattr(module, type.capitalize())()
		except: return None

	@classmethod
	def enabled(self):
		for instance in self._instances():
			if instance.accountEnabled() and instance.accountValid(): return True
		return False

	@classmethod
	def services(self):
		result = {}
		for instance in self._instances():
			if instance.accountEnabled() and instance.accountValid():
				result[instance.id()] = instance.servicesList(onlyEnabled = True)
		return result

	@classmethod
	def cached(self, items):
		for value in items.values():
			if value: return True
		return False

	@classmethod
	def meta(self, id = None):
		if id is None:
			return Debrid.Meta
		else:
			try: return Debrid.Meta[id]
			except: return None

	@classmethod
	def deletePlayback(self, link, source):
		id = source['stream'].streamId()
		if not id: id = link
		handle = source['stream'].streamHandle()
		category = source['stream'].streamCategory()
		pack = source['stream'].filePack(boolean = True)
		for instance in self._instances():
			if instance.id() == handle:
				if instance.deletePossible(source['stream'].sourceType()):
					instance.deletePlayback(id = id, pack = pack, category = category)
				break

	@classmethod
	def handles(self, data = False, priority = False):
		instances = self._instances(type = Debrid.TypeHandle)
		if priority:
			highest = 0
			for instance in instances:
				if instance.priority() > highest:
					highest = instance.priority()
			temp = [None] * (max(highest, len(instances)) + 1)
			for instance in instances:
				temp[instance.priority() - 1] = instance
			instances = [i for i in temp if i]
		if data:
			for i in range(len(instances)):
				instances[i] = instances[i].data()
		return instances

	@classmethod
	def providers(self):
		return [
			{
				'id' : 'premiumize',
				'name' : 33566,
				'description' : 'Premiumize is the best overall service and provides the most features. It has a large torrent and hoster cache and is one of the few that support usenet. This is the service to go with if you can afford it and want the best experience.',

				'general' : {'rating' : 5,  'recommend' : 1, 'native' : True, 'limit' : False},
				'subscription' : {'rating' : 2, 'fee' : 6.50},
				'customer' : {'rating' : 5, 'label' : 36247},
				'api' : {'rating' : 5, 'label' : 36244},
				'network' : {'rating' : 5, 'support' : {'torrent' : True, 'usenet' : True, 'hoster' : True}},
				'stream' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : True, 'resolver' : True}},
				'cache' : {'rating' : 5, 'label' : 36250, 'support' : {'gaia' : True, 'orion' : True, 'resolver' : False}},
				'select' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : True, 'resolver' : False}},
				'extra' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'offcloud',
				'name' : 35200,
				'description' : 'OffCloud is one of the few services that support usenet and the only one that has a usenet cache. OffCloud is an overall good service, but has a small cache and relative high prices.',

				'general' : {'rating' : 5,  'recommend' : 1, 'native' : True, 'limit' : False},
				'subscription' : {'rating' : 3, 'fee' : 5.80},
				'customer' : {'rating' : 5, 'label' : 36247},
				'api' : {'rating' : 4, 'label' : 36244},
				'network' : {'rating' : 5, 'support' : {'torrent' : True, 'usenet' : True, 'hoster' : True}},
				'stream' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : True, 'resolver' : False}},
				'cache' : {'rating' : 3, 'label' : 36252, 'support' : {'gaia' : True, 'orion' : True, 'resolver' : False}},
				'select' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : True, 'resolver' : False}},
				'extra' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'easynews',
				'name' : 33794,
				'description' : 'EasyNews is substantially different to other debrid services, in that they handle scraping and streaming in one solution. EasyNews only supports usenet, but does so very well. All links from EasyNews are cached and can be instantly streamed. Besides the price, they are a good option for both English and non-English releases.',

				'general' : {'rating' : 4,  'recommend' : 2, 'native' : True, 'limit' : False},
				'subscription' : {'rating' : 1, 'fee' : 10.00},
				'customer' : {'rating' : 4, 'label' : 36247},
				'api' : {'rating' : 4, 'label' : 36244},
				'network' : {'rating' : 3, 'support' : {'torrent' : False, 'usenet' : True, 'hoster' : False}},
				'stream' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : False, 'resolver' : False}},
				'cache' : {'rating' : 5, 'label' : 36250, 'support' : {'gaia' : True, 'orion' : False, 'resolver' : False}},
				'select' : {'rating' : 4, 'support' : {'gaia' : True, 'orion' : False, 'resolver' : False}},
				'extra' : {'rating' : 4, 'support' : {'gaia' : True, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'realdebrid',
				'name' : 33567,
				'description' : 'RealDebrid is one of the oldest debrid services around. Although their customer support and API design is lacking, they offer good value for money. RealDebrid has a large torrent cache. [B]As of November 2024, RealDebrid does not support cache lookups anymore. The cache still works, you will just not know the cache status beforehand.[/B]',

				'general' : {'rating' : 3,  'recommend' : 3, 'native' : True, 'limit' : False},
				'subscription' : {'rating' : 5, 'fee' : 3.00},
				'customer' : {'rating' : 2, 'label' : 36248},
				'api' : {'rating' : 2, 'label' : 36246},
				'network' : {'rating' : 4, 'support' : {'torrent' : True, 'usenet' : False, 'hoster' : True}},
				'stream' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : True, 'resolver' : True}},
				'cache' : {'rating' : 2, 'label' : 36712, 'support' : {'gaia' : True, 'orion' : True, 'resolver' : False}},
				'select' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : True, 'resolver' : False}},
				'extra' : {'rating' : 5, 'support' : {'gaia' : True, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'debridlink',
				'name' : 35263,
				'description' : 'DebridLink is an overall good service and has great value for money. Although not natively supported in Gaia, most functionality can be utilized through external addons. DebridLink is good choice if you are on a budget and want a service with a decent cache. [B]As of November 2024, DebridLink does not support cache lookups anymore. The cache still works, you will just not know the cache status beforehand.[/B]',

				'general' : {'rating' : 3,  'recommend' : 3, 'native' : False, 'limit' : False},
				'subscription' : {'rating' : 5, 'fee' : 2.80},
				'customer' : {'rating' : 5, 'label' : 36247},
				'api' : {'rating' : 5, 'label' : 36244},
				'network' : {'rating' : 4, 'support' : {'torrent' : True, 'usenet' : False, 'hoster' : True}},
				'stream' : {'rating' : 5, 'support' : {'gaia' : False, 'orion' : True, 'resolver' : True}},
				'cache' : {'rating' : 2, 'label' : 36712, 'support' : {'gaia' : False, 'orion' : True, 'resolver' : True}},
				'select' : {'rating' : 3, 'support' : {'gaia' : False, 'orion' : True, 'resolver' : False}},
				'extra' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'alldebrid',
				'name' : 33568,
				'description' : 'AllDebrid is an overall good service and has great value for money. The API is very poorly designed by uploading torrents to file hosters before streaming from there. Although not natively supported in Gaia, most functionality can be utilized through external addons. AllDebrid is good choice if you are on a budget and want a service with a decent cache. [B]As of November 2024, AllDebrid does not support cache lookups anymore. The cache still works, you will just not know the cache status beforehand.[/B]',

				'general' : {'rating' : 3,  'recommend' : 3, 'native' : False, 'limit' : False},
				'subscription' : {'rating' : 5, 'fee' : 2.80},
				'customer' : {'rating' : 4, 'label' : 36247},
				'api' : {'rating' : 1, 'label' : 36246},
				'network' : {'rating' : 4, 'support' : {'torrent' : True, 'usenet' : False, 'hoster' : True}},
				'stream' : {'rating' : 5, 'support' : {'gaia' : False, 'orion' : True, 'resolver' : True}},
				'cache' : {'rating' : 2, 'label' : 36712, 'support' : {'gaia' : False, 'orion' : True, 'resolver' : True}},
				'select' : {'rating' : 3, 'support' : {'gaia' : False, 'orion' : True, 'resolver' : False}},
				'extra' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'linksnappy',
				'name' : 35264,
				'description' : 'LinkSnappy is a less-known debrid service. LinkSnappy only has support for streaming through an external addon, but not for any of the other functionality.',

				'general' : {'rating' : 3,  'recommend' : 3, 'native' : False, 'limit' : True},
				'subscription' : {'rating' : 1, 'fee' : 9.20},
				'customer' : {'rating' : 3, 'label' : 36247},
				'api' : {'rating' : 2, 'label' : 36246},
				'network' : {'rating' : 4, 'support' : {'torrent' : True, 'usenet' : False, 'hoster' : True}},
				'stream' : {'rating' : 4, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : True}},
				'cache' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'select' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'extra' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'megadebrid',
				'name' : 35265,
				'description' : 'MegaDebrid is a less-known debrid service. MegaDebrid only has support for streaming through an external addon, but not for any of the other functionality.',

				'general' : {'rating' : 2,  'recommend' : 3, 'native' : False, 'limit' : True},
				'subscription' : {'rating' : 5, 'fee' : 3.00},
				'customer' : {'rating' : 5, 'label' : 36247},
				'api' : {'rating' : 2, 'label' : 36246},
				'network' : {'rating' : 2, 'support' : {'torrent' : False, 'usenet' : False, 'hoster' : True}},
				'stream' : {'rating' : 4, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : True}},
				'cache' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'select' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'extra' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'rapidpremium',
				'name' : 33569,
				'description' : 'RapidPremium is a less-known debrid service. RapidPremium only has support for streaming through an external addon, but not for any of the other functionality.',

				'general' : {'rating' : 2,  'recommend' : 3, 'native' : False, 'limit' : True},
				'subscription' : {'rating' : 2, 'fee' : 6.50},
				'customer' : {'rating' : 1, 'label' : 36248},
				'api' : {'rating' : 2, 'label' : 36246},
				'network' : {'rating' : 2, 'support' : {'torrent' : False, 'usenet' : False, 'hoster' : True}},
				'stream' : {'rating' : 4, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : True}},
				'cache' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'select' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'extra' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'simplydebrid',
				'name' : 35266,
				'description' : 'SimplyDebrid is a less-known debrid service. SimplyDebrid only has support for streaming through an external addon, but not for any of the other functionality.',

				'general' : {'rating' : 2,  'recommend' : 3, 'native' : False, 'limit' : True},
				'subscription' : {'rating' : 5, 'fee' : 3.00},
				'customer' : {'rating' : 1, 'label' : 36248},
				'api' : {'rating' : 1, 'label' : 36246},
				'network' : {'rating' : 2, 'support' : {'torrent' : False, 'usenet' : False, 'hoster' : True}},
				'stream' : {'rating' : 4, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : True}},
				'cache' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'select' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'extra' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
			},
			{
				'id' : 'smoozed',
				'name' : 35267,
				'description' : 'Smoozed is a less-known debrid service. Smoozed only has support for streaming through an external addon, but not for any of the other functionality.',

				'general' : {'rating' : 2,  'recommend' : 3, 'native' : False, 'limit' : True},
				'subscription' : {'rating' : 4, 'fee' : 3.70},
				'customer' : {'rating' : 1, 'label' : 36248},
				'api' : {'rating' : 1, 'label' : 36246},
				'network' : {'rating' : 2, 'support' : {'torrent' : False, 'usenet' : False, 'hoster' : True}},
				'stream' : {'rating' : 4, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : True}},
				'cache' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'select' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
				'extra' : {'rating' : 1, 'label' : 36106, 'support' : {'gaia' : False, 'orion' : False, 'resolver' : False}},
			},
		]

	@classmethod
	def help(self, title = None):
		from lib.modules.interface import Translation, Format, Dialog

		def _help(service):
			labels = []

			if 'label' in service:
				labels.append(service['label'])
			if 'support' in service:
				for support in [['gaia', 35639], ['orion', 35400], ['resolver', [35310, 33747]], ['torrent', 33199], ['usenet', 33200], ['hoster', 33198]]:
					if support[0] in service['support'] and service['support'][support[0]]:
						if Tools.isArray(support[1]): labels.extend(support[1])
						else: labels.append(support[1])
			if 'recommend' in service:
				labels.append('%s %s' % (Translation.string(35486 if service['recommend'] == 1 else 35487 if service['recommend'] == 2 else 35334), Translation.string(36256)))
			if 'native' in service:
				labels.append('%s %s' % (Translation.string(36253 if service['native'] else 36255 if 'limit' in service and service['limit'] else 36254), Translation.string(33921)))
			if 'fee' in service:
				labels.append('%s %s %s' % (Translation.string(36208), Translation.string(36226), Translation.string(33849) % '$%.2f' % service['fee']))

			if not labels: labels.append(36106)
			labels = [Translation.string(i) for i in labels]

			if 'rating' in service: labels.insert(0, Format.iconRating(count  = service['rating'], color = True, fixed = True))

			return Format.iconJoin(labels)

		items = [
			{'type' : 'title', 'value' : 'Debrid Services', 'break' : 2},
			{'type' : 'text', 'value' : 'Debrid services provide fast and instant access to different filesharing networks. It is highly recommended to authenticate at least one debrid account, otherwise you will only have access to free streams which are few, slow, unreliable, and of low quality. You only need [B]one[/B] debrid account, but multiple accounts can increase the number of instantly available streams.', 'break' : 2},

			{'type' : 'title', 'value' : 'Filesharing Networks', 'break' : 2},
			{'type' : 'text', 'value' : 'Debrid services offer access to one or more filesharing networks:', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Torrents', 'value' : 'BitTorrent is a distributed peer-to-peer filesharing network. Torrents are reliable and resistant to takedowns. They provide most of the high quality streams and is the overall best network for English releases. Torrents require other users to actively share the files, and if no one seeds old files, they might become inaccessible. Most debrid services support torrents. Gaia natively supports torrent scraping with detailed metadata extraction.'},
				{'title' : 'Usenet', 'value' : 'Newsgroups or Usenet is a decentralized filesharing network. Usenet is resilient to takedowns and provides high quality streams. Many non-English speaking European countries, like Germany and the Netherlands, prefer sharing files over usenet rather than torrents. The network is retention-based, meaning that old files are automatically deleted, but most major usenet providers have a retention span of more than 10 years. Only a few debrid providers support usenet. Gaia natively supports usenet scraping with detailed metadata extraction.'},
				{'title' : 'Hosters', 'value' : 'Hosters are traditional centralized filesharing servers. Hosters are notorious for takedowns and most files get deleted very quickly, often days after being published. There are a few free hosters that allow streaming without a premium or debrid account, but they are unreliable and slow. Paid hosters require a debrid account for streaming and are slightly more reliable and faster than free ones. Hosters generally have fewer streams, are of lower quality, and do not support file packs. Always try to use torrents or usenet over hosters. Most debrid services support hosters. Gaia does not support hoster scraping natively, but instead uses external addons, which limits the metadata that can be extracted.'},
			]},

			{'type' : 'title', 'value' : 'Debrid Features', 'break' : 2},
			{'type' : 'text', 'value' : 'Debrid services offer the following functionality:', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Video Streaming', 'value' : 'Videos are resolved and streamed from fast and reliable servers or CDNs. In most cases videos are streamed from dedicated debrid servers instead of directly from filesharing nodes. This improves your anonymity, since only the debrid provider can see your IP address and not the torrent network nodes or hoster servers.'},
				{'title' : 'Cache Lookups', 'value' : 'Debrid providers cache files on their servers the first time a user requests them. Other users can subsequently access these files without having to wait for the debrid service to download them first. The debrid cache is inspected during scraping and streams are labeled accordingly so that you know which files can be streamed instantly. Most debrid services only have a cache for torrents, but a few also have a usenet or hoster cache. Note that the cache size differs among debrid services, and some services have more files cached than others.'},
				{'title' : 'File Selection', 'value' : 'Certain releases contain multiple files, such as show and season packs, or movie collections. In order to utilize these packs, there must be support to check the individual file names and select the correct one. Most debrid services only support file selection for torrents and usenet, but not for hosters. File packs are almost useless without selection support, since most of the time the wrong file will be picked during playback.'},
				{'title' : 'Extra Features', 'value' : 'Extra features which include automatically and manually adding and removing files from the debrid download list, accessing account details, selecting servers closest to you, and improved error handling.'},
			]},

			{'type' : 'title', 'value' : 'Addon Support', 'break' : 2},
			{'type' : 'text', 'value' : 'Debrid cache lookups, resolving, and streaming can be handled by one of the following addons:', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Gaia', 'value' : 'Some debrid services are natively supported by Gaia. Native services provide all available functionality, including cache lookups, file selection, resolving, streaming, and extra features. Gaia can handle torrents, usenet, and hosters. It is recommended to choose a service that is natively supported, since you will get the most out of it.'},
				{'title' : 'Orion', 'value' : 'Some debrid services are supported by Orion. For this you need an active Orion account and have your debrid account authenticated with Orion. Cache lookups, file selection, resolving, and streaming are supported. Orion can handle torrents, usenet, and hosters. Note that Orion has daily limits on both cache lookups and resolving. Configure your preferences for Orion cache lookups and streaming under the [I]Scraping[/I]  and [I]Streaming[/I]  settings tabs.'},
				{'title' : 'Resolvers', 'value' : 'External resolver addons, like [I]ResolveUrl[/I]  or [I]UrlResolver[/I], support a variety of debrid services and many different file hosters. Resolvers handle account authentication and resolving on behalf of Gaia. They do not support cache lookups, but for certain services, Gaia can lookup the cache, even if they are not natively supported. Resolver addons can only handle torrents and hosters, and do not support file selection or extra features. Configure your preferences for resolver streaming under the [I]Streaming[/I]  settings tab.'},
				{'title' : 'Torrenters', 'value' : 'Besides the options above, the external addons, [I]Quasar[/I]  and [I]Elementum[/I], can also be used to stream torrents locally without the need for a paid account. These addons do not have instant cache functionality and torrents always have to be downloaded before they can be streamed. Only some of the video has to be buffered before streaming commences, so if there are enough seeds, this is a reliable and free alternative. Note that these addons launch their own player when streaming. Hence, all the nice features in Gaia\'s player, like subtitles and progress tracking, will not work. Configure your preferences for torrent streaming under the [I]Streaming[/I]  settings tab.'},
			]},
		]

		for provider in self.providers():
			items.extend([
				{'type' : 'title', 'value' : Translation.string(provider['name']), 'break' : 2},
				{'type' : 'text', 'value' : Translation.string(provider['description']), 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 'Overall Service', 'value' : _help(provider['general'])},
					{'title' : 'Subscription Fee', 'value' : _help(provider['subscription'])},
					{'title' : 'Customer Care', 'value' : _help(provider['customer'])},
					{'title' : 'API Design', 'value' : _help(provider['api'])},
					{'title' : 'File Networks', 'value' : _help(provider['network'])},
					{'title' : 'Video Streaming', 'value' : _help(provider['stream'])},
					{'title' : 'Cache Lookups', 'value' : _help(provider['cache'])},
					{'title' : 'File Selection', 'value' : _help(provider['select'])},
					{'title' : 'Extra Features', 'value' : _help(provider['extra'])},
				]}
			])

		Dialog.details(title = title if title else 36239, items = items)
