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
from lib.modules import cache
from lib.modules import network
from lib.modules import interface
from lib.modules import window
from lib.modules.orionoid import Orionoid
from lib.modules.stream import Stream
from lib.modules.concurrency import Lock

# NB: Only initialize the services once, otherwise it takes about 150ms each time Handler._initialize is called, because the objects have to be created and the settings be read from file.
# NB: Do not declare these variables as class variables in Handler, because if no object of Handler exists, it will delete the class variables.
# NB: This is important for sources -> __init__.py -> addItem.
HandlerData = None

class Handler(object):

	ModeNone = None
	ModeDefault = 'default'
	ModeSelection = 'selection'
	ModeBest = 'best'
	ModeFile = 'file'

	ReturnUnavailable = 'unavailable'
	ReturnExternal = 'external'
	ReturnCancel = 'cancel'
	ReturnSelection = 'selection' # No file selected from list of items.
	ReturnPack = 'pack' # No file can be found in the pack that matches the title and year/season/episode.

	TypeAll = 'all'
	TypeDirect = 'direct'
	TypeTorrent = 'torrent'
	TypeUsenet = 'usenet'
	TypeHoster = 'hoster'

	Lock = Lock()
	Debrids = None

	def __init__(self, type = None):
		self.mServices = []
		self.mType = None
		self.mDefault = None
		self._initialize(type)

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True, full = True):
		if settings:
			global HandlerData
			HandlerData = None
			Handler.Debrids = None

		if full:
			HandleResolver.reset(settings = settings)
			HandleGaia.reset(settings = settings)
			HandleOrion.reset(settings = settings)

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def debrids(self):
		if Handler.Debrids is None:
			Handler.Lock.acquire()
			if Handler.Debrids is None:
				instances = []
				for handle in self.handles(debrid = True):
					values = handle().instances()
					if values: instances.extend(values)
				Handler.Debrids = instances
			Handler.Lock.release()
		return Handler.Debrids

	@classmethod
	def handles(self, type = None, debrid = False):
		if debrid:
			return [
				HandleGaia,
				HandleOrion,
				HandleResolveUrl,
				HandleUrlResolver,
			]
		elif type is None:
			return [
				HandleDirect,
				HandleGaia,
				HandleOrion,
				HandleResolveUrl,
				HandleUrlResolver,
				HandleElementum,
				HandleQuasar,
				HandleYoutube,
			]
		elif type == Handler.TypeTorrent:
			return [
				HandleGaia,
				HandleOrion,
				HandleResolveUrl,
				HandleUrlResolver,
				HandleElementum,
				HandleQuasar,
			]
		elif type == Handler.TypeUsenet:
			return [
				HandleGaia,
				HandleOrion,
			]
		elif type == Handler.TypeHoster:
			return [
				HandleDirect,
				HandleGaia,
				HandleOrion,
				HandleResolveUrl,
				HandleUrlResolver,
				HandleYoutube,
			]

	def _initialize(self, type):
		from lib import debrid
		if type is None: return

		try:
			direct = type['stream'].accessTypeDirect()
			type = type['stream'].sourceType()
		except:
			direct = type == Handler.TypeDirect
			type = type.lower()

		if not type == Handler.TypeTorrent and not type == Handler.TypeUsenet:
			if direct: type = Handler.TypeDirect
			else: type = Handler.TypeHoster
		if type == self.mType:
			return

		self.mType = type
		self.mServices = []
		self.mDefault = None

		selection = tools.Settings.getInteger('stream.general.selection')

		global HandlerData
		if HandlerData is None:
			HandlerData = {
				Handler.TypeDirect : {'initialized' : False, 'default' : None, 'services' : []},
				Handler.TypeTorrent : {'initialized' : False, 'default' : None, 'services' : []},
				Handler.TypeUsenet : {'initialized' : False, 'default' : None, 'services' : []},
				Handler.TypeHoster : {'initialized' : False, 'default' : None, 'services' : []},
			}

		types = []
		if type == Handler.TypeAll: types = [Handler.TypeDirect, Handler.TypeTorrent, Handler.TypeUsenet, Handler.TypeHoster]
		else: types = [type]

		handles = self.handles()
		for type in types:
			if not HandlerData[type]['initialized']:
				HandlerData[type]['initialized'] = True
				for handle in handles:
					handle = handle()
					if selection == 0 or selection == 1:
						if handle.enabled(type = type):
							HandlerData[type]['services'].append(handle)
					if selection == 0 or selection == 2:
						try:
							instances = handle.instances(type = type)
							for instance in instances:
								if instance.enabled(type = type):
									HandlerData[type]['services'].append(instance)
						except: pass
				HandlerData[type]['default'] = self.serviceDefault(type = type, services = HandlerData[type]['services'])
			self.mServices.extend(HandlerData[type]['services'])
			if not self.mDefault: self.mDefault = HandlerData[type]['default']

	def serviceHas(self):
		return self.serviceCount() > 0

	def serviceCount(self):
		return len(self.mServices)

	@classmethod
	def serviceSettings(self, type, extra = None):
		handles = {
			3 : {
				'id' : 'gaia',
				Handler.TypeAll : {3 : 'premiumize', 4 : 'offcloud', 5 : 'realdebrid'},
				Handler.TypeTorrent : {2 : 'premiumize', 3 : 'offcloud', 4 : 'realdebrid'},
				Handler.TypeUsenet : {2 : 'premiumize', 3 : 'offcloud', 4 : 'realdebrid'},
				Handler.TypeHoster : {2 : 'premiumize', 3 : 'offcloud', 4 : 'realdebrid'},
			},
			4 : {
				'id' : 'orion',
				Handler.TypeAll : {3 : 'premiumize', 4 : 'offcloud', 5 : 'realdebrid', 6 : 'debridlink', 7 : 'alldebrid'},
				Handler.TypeTorrent : {2 : 'premiumize', 3 : 'offcloud', 4 : 'realdebrid', 5 : 'debridlink', 6 : 'alldebrid'},
				Handler.TypeUsenet : {2 : 'premiumize', 3 : 'offcloud'},
				Handler.TypeHoster : {2 : 'premiumize', 3 : 'offcloud', 4 : 'realdebrid', 5 : 'debridlink', 6 : 'alldebrid'},
			},
		}

		resolveurl = {5 : {
			'id' : 'resolveurl',
			Handler.TypeAll : {3 : 'premiumize', 4 : 'realdebrid', 5 : 'debridlink', 6 : 'alldebrid', 7 : 'linksnappy', 8 : 'megadebrid', 9 : 'rapidpremium', 10 : 'simplydebrid', 11 : 'smoozed'},
			Handler.TypeTorrent : {2 : 'premiumize', 3 : 'realdebrid', 4 : 'debridlink', 5 : 'alldebrid', 6 : 'linksnappy'},
			Handler.TypeUsenet : {},
			Handler.TypeHoster : {2 : 'premiumize', 3 : 'realdebrid', 4 : 'debridlink', 5 : 'alldebrid', 6 : 'linksnappy', 7 : 'megadebrid', 8 : 'rapidpremium', 9 : 'simplydebrid', 10 : 'smoozed'},
		}}

		urlresolver = {6 : {
			'id' : 'urlresolver',
			Handler.TypeAll : {3 : 'premiumize', 4 : 'realdebrid', 5 : 'debridlink', 6 : 'alldebrid', 7 : 'linksnappy', 8 : 'megadebrid', 9 : 'rapidpremium', 10 : 'simplydebrid', 11 : 'smoozed'},
			Handler.TypeTorrent : {2 : 'premiumize', 3 : 'realdebrid', 4 : 'debridlink', 5 : 'alldebrid', 6 : 'linksnappy'},
			Handler.TypeUsenet : {},
			Handler.TypeHoster : {2 : 'premiumize', 3 : 'realdebrid', 4 : 'debridlink', 5 : 'alldebrid', 6 : 'linksnappy', 7 : 'megadebrid', 8 : 'rapidpremium', 9 : 'simplydebrid', 10 : 'smoozed'},
		}}

		elementum = {7 : {'id' : 'elementum'}}
		quasar = {8 : {'id' : 'quasar'}}
		youtube = {7 : {'id' : 'youtube'}}

		if extra is None:
			handles.update(resolveurl)
			handles.update(urlresolver)
			handles.update(elementum)
			handles.update(quasar)
		elif extra == Handler.TypeTorrent:
			handles.update(resolveurl)
			handles.update(urlresolver)
			handles.update(elementum)
			handles.update(quasar)
		elif extra == Handler.TypeUsenet:
			pass
		elif extra == Handler.TypeHoster:
			handles.update(resolveurl)
			handles.update(urlresolver)
			handles.update(youtube)

		return handles

	def serviceDefault(self, type, services):
		result = None
		extra = None

		setting = tools.Settings.getInteger('stream.general.handle')
		if setting == 0:
			return Handler.ModeBest
		elif setting == 1:
			return None
		elif setting == 2:
			setting = tools.Settings.getInteger('stream.general.handle.%s' % type)
			extra = type

		if setting == 1:
			return Handler.ModeBest
		elif setting == 2:
			return None
		elif setting >= 3:
			handles = self.serviceSettings(type = type, extra = extra)

			id = ''
			if setting in handles:
				handle = handles[setting]
				setting = tools.Settings.getInteger('stream.%s.handle' % handle['id'])
				if setting >= 1:
					id += handle['id']
					if setting > 1:
						if setting == 2:
							setting = tools.Settings.getInteger('stream.%s.handle.%s' % (handle['id'], type))
							if setting in handle[type]: id += handle[type][setting]
						else:
							if setting in handle[Handler.TypeAll]: id += handle[Handler.TypeAll][setting]

			if id:
				for service in services:
					if service.id() == id:
						result = service
						break

		return result

	def service(self, name = None):
		if self.serviceHas():
			if name is None:
				return self.mServices[0]
			else:
				name = name.lower()
				if name == HandleAutomatic.Id:
					return HandleAutomatic()
				else:
					for service in self.mServices:
						if service.id() == name:
							return service
		return None

	def supported(self, item = None, cloud = False):
		if item is None:
			return len(self.mServices) > 0
		else:
			if tools.Tools.isInstance(item, Stream): item = {'stream' : item}
			self._initialize(item)
			for service in self.mServices:
				if service.supported(item, cloud = cloud):
					return True
			return False

	def supportedType(self, type):
		if type == Handler.TypeDirect: return self.supportedDirect()
		elif type == Handler.TypeTorrent: return self.supportedTorrent()
		elif type == Handler.TypeUsenet: return self.supportedUsenet()
		elif type == Handler.TypeHoster: return self.supportedHoster()
		else: return False

	def supportedDirect(self):
		global HandlerData
		return len(HandlerData[Handler.TypeDirect]['services']) > 0

	def supportedTorrent(self):
		global HandlerData
		return len(HandlerData[Handler.TypeTorrent]['services']) > 0

	def supportedUsenet(self):
		global HandlerData
		return len(HandlerData[Handler.TypeUsenet]['services']) > 0

	def supportedHoster(self):
		global HandlerData
		return len(HandlerData[Handler.TypeHoster]['services']) > 0

	def supportedCount(self, item = None, cloud = False):
		if item is None:
			return len(self.mServices)
		else:
			count = 0
			self._initialize(item)
			for service in self.mServices:
				try:
					if service.supported(item, cloud = cloud):
						count += 1
				except: pass
			return count

	def serviceBest(self, item, cached = True, cloud = False, fallback = True, serviceGlobal = True, serviceIndividual = True, exclude = []):
		try:
			from lib import debrid
			self._initialize(item)
			services = [i.id() for i in self.mServices if i.supported(item, cloud = cloud)]

			cache = {}
			if not item['stream'].accessCacheAny(account = True):
				if cached and not fallback: return None
				cached = False
			if cached:
				cache = item['stream'].accessCache(account = True)

			# Try to find a cached link first.
			handles = self.handles()
			for handle in handles:
				handle = handle()

				id = handle.id()
				if not id in exclude:
					if serviceGlobal:
						if id in services and ((not cached) or (cached and id in cache and cache[id])): return id

					if serviceIndividual:
						try: instances = handle.instances()
						except: instances = None
						if instances:
							for instance in instances:
								id = instance.id()
								serviceId = instance.serviceId()
								if not id in exclude:
									if id in services and ((not cached) or (cached and serviceId in cache and cache[serviceId])): return id

			# If no service was found that has the link cached, search again for the the best sevice but do not check if it is cached this time.
			if fallback and cached: return self.serviceBest(item = item, cached = False, cloud = cloud, fallback = fallback, exclude = exclude)
		except: tools.Logger.error()
		return None

	def serviceDetermine(self, mode, item, popups = False, all = False, cloud = False, exclude = []):
		try:
			self._initialize(item)

			service = None
			if all: services = self.mServices
			else: services = [i for i in self.mServices if i.supported(item, cloud = cloud)]

			# Always show the dialog, even if there is only a single option.
			#if False and len(services) == 1:
			#	service = services[0].id()
			#else:
			if True:
				if mode == Handler.ModeBest or (mode == Handler.ModeDefault and self.mDefault == Handler.ModeBest):
					service = HandleAutomatic.Id
				else:
					if popups:
						if mode == Handler.ModeNone or mode == Handler.ModeDefault:
							if self.mDefault == Handler.ModeBest:
								service = self.serviceBest(item = item, cloud = cloud, exclude = exclude)
							elif self.mDefault == Handler.ModeNone or self.mDefault == Handler.ModeSelection or self.mDefault == Handler.ModeFile:
								service = self.options(item = item, popups = popups, all = all, cloud = cloud)
							else:
								try: service = self.mDefault.id()
								except: service = self.options(item = item, popups = popups, all = all, cloud = cloud)
						elif mode == Handler.ModeBest:
							service = self.serviceBest(item = item, cloud = cloud, exclude = exclude)
						else:
							service = self.options(item = item, popups = popups, all = all, cloud = cloud)
					elif mode == Handler.ModeDefault: # Autoplay
						try:
							service = self.mDefault.id()
						except:
							service = self.serviceBest(item = item, cloud = cloud, exclude = exclude)

			if service is None: service = self.options(item = item, popups = popups, all = all, cloud = cloud)

			if popups and (service is None or service == Handler.ReturnUnavailable): self.serviceUnsupported(item = item, cloud = cloud)

			if service is None:
				return Handler.ReturnUnavailable
			elif service == Handler.ReturnCancel or service == Handler.ReturnUnavailable:
				return service
			else:
				if self.service(name = service).supported(item, cloud = cloud):
					return service
				else:
					return self.serviceBest(item = item, cloud = cloud)
		except:
			tools.Logger.error()

	@classmethod
	def serviceUnsupported(self, item = None, cloud = False):
		try:
			if item:
				support = False
				type = item['stream'].sourceType()
				handles = self.handles(type = type)
				for handle in handles:
					handle = handle()
					if handle.enabled(type = type) and handle.supported(item = item, cloud = cloud):
						support = True
						break

				if not support:
					message = None
					if type == Stream.SourceTypeTorrent: message = 33355
					elif type == Stream.SourceTypeUsenet: message = 33356
					elif type == Stream.SourceTypeHoster: message = 33357
					if message: interface.Dialog.confirm(title = 35452, message = message)
			else:
				interface.Dialog.confirm(title = 35452, message = 33375)
		except: tools.Logger.error()

	@classmethod
	def serviceExternal(self, service):
		if not tools.Tools.isString(service):
			try: service = service.id()
			except: return False
		return service == HandleElementum().id() or service == HandleQuasar().id() or service == HandleYoutube().id()

	def options(self, item, popups = False, all = False, cloud = False):
		try:
			if popups:
				self._initialize(item)

				layout = tools.Settings.getInteger('stream.general.selection.layout')
				if layout == 0: layout = 2 if interface.Skin.supportDialogDetail() else 1

				if layout == 2: quality = interface.Skin.supportDialogDetailIcon(default = True)
				else: quality = True
				quality = interface.Icon.QualityLarge if quality else interface.Icon.QualitySmall

				bold = interface.Skin.supportDialogDetailBold(default = True)

				if self.mType == Handler.TypeTorrent: title = 33473
				elif self.mType == Handler.TypeUsenet: title = 33482
				else: title = 33488

				if all: services = self.mServices
				else: services = [i for i in self.mServices if i.supported(item, cloud = cloud)]
				servicesCount = len(services)

				# Always show the dialog, even if there is only a single option.
				#if servicesCount == 1:
				#	return services[0].name()
				#elif servicesCount > 1:
				if servicesCount > 0:
					automatic = interface.Translation.string(33800)
					external = interface.Translation.string(35354)
					gaia = interface.Translation.string(35639)
					streamFrom = interface.Translation.string(33808)
					streamThrough = interface.Translation.string(33809)
					streamDirect = interface.Translation.string(33810)

					stream = item['stream']
					items = []
					for i in services:
						extra = None
						if stream.accessTypeDirect(): extra = interface.Format.font(33489, color = interface.Format.colorLighter(color = interface.Format.colorSpecial(), change = 10))
						elif stream.sourceTypePremium(): extra = interface.Format.font(33768, color = interface.Format.colorLighter(color = interface.Format.colorSpecial(), change = 10))
						elif i.cache(item = item): extra = interface.Format.font(33884, color = interface.Format.colorSpecial())
						elif i.debrid() and stream.accessTypeDebrid(): extra = interface.Format.font(33209, color = interface.Format.colorLighter(color = interface.Format.colorSpecial(), change = 30))
						elif i.open() and stream.accessTypeOpen(): extra = interface.Format.font(33211, color = interface.Format.colorLighter(color = interface.Format.colorSpecial(), change = 50))
						elif i.addon(): extra = interface.Format.font(35614, color = interface.Format.colorLighter(color = interface.Format.colorSpecial(), change = 50))
						if extra: extra = interface.Format.fontUppercase(extra)

						mode = None
						handleId = None
						handleName = None
						id = i.id()
						name = i.name()

						serviceId = None
						serviceName = None
						serviceHas = False
						try:
							serviceId = i.serviceId()
							serviceName = i.serviceName()
							serviceHas = True
						except: pass

						if serviceHas:
							handleId = id
							handleName = name
							if not serviceName: mode = automatic
						elif i.addon():
							handleId = id
							handleName = name
							mode = external
						elif stream.accessTypeDirect():
							handleId = Handler.TypeDirect
							handleName = gaia
						elif stream.sourceTypePremium():
							serviceId = stream.providerId()
							serviceName = stream.providerName()
							handleId = 'gaia' + serviceId
							handleName = gaia
						else:
							serviceId = id
							serviceName = name
							handleId = 'gaia' + id
							handleName = gaia

						items.append({'handle' : {'id' : handleId, 'name' : handleName}, 'service' : {'id' : serviceId, 'name' : serviceName}, 'extra' : extra, 'mode' : mode})

					if layout == 2:
						directory = interface.Directory()
						for i in range(len(items)):
							item = items[i]

							label = None
							if item['service']['name']: label = item['service']['name']
							elif item['handle']['name']: label = item['handle']['name']
							if bold: label = interface.Format.fontBold(label)

							label2 = []
							if item['extra']: label2.append(interface.Format.fontBold(item['extra']))
							if item['handle']['id'] == Handler.TypeDirect: label2.append(streamDirect % item['handle']['name'])
							elif item['service']['name'] and item['handle']['name']: label2.append(streamFrom % (item['service']['name'], item['handle']['name']))
							elif item['service']['name']: label2.append(streamThrough % item['service']['name'])
							elif item['handle']['name']: label2.append(streamThrough % item['handle']['name'])
							label2 = interface.Format.iconJoin(label2)

							icon = None
							if item['handle']['id']: icon = interface.Icon.path(icon = 'gaia' if item['handle']['id'] == Handler.TypeDirect else item['handle']['id'], type = interface.Icon.TypeIcon, special = interface.Icon.SpecialHandlers, quality = quality)

							items[i] = directory.item(label = label, label2 = label2, path = None, icon = icon)
						index = interface.Dialog.select(title = title, items = items, details = True)
					else:
						for i in range(len(items)):
							item = items[i]
							label = []
							if item['handle']['name']:
								if item['handle']['id'] == 'gaia': label.append(interface.Format.fontColor(item['handle']['name'], color = interface.Format.colorLighter(color = interface.Format.colorAlternative())))
								else: label.append(interface.Format.fontColor(item['handle']['name'], color = interface.Format.colorLighter(color = interface.Format.colorAlternative(), change = 40)))
							if item['service']['name']: label.append(item['service']['name'])
							if item['mode']: label.append(item['mode'])
							if item['extra']: label.append(item['extra'])
							items[i] = interface.Format.fontBold(interface.Format.iconJoin(label))
						index = interface.Dialog.select(title = title, items = items)

					if index < 0: return Handler.ReturnCancel
					else: return services[index].id()
		except: tools.Logger.error()
		return Handler.ReturnUnavailable

	def handle(self, link, item, name = None, download = False, popups = False, close = True, mode = ModeNone, cloud = False, strict = False, notification = True):
		self._initialize(item)

		if popups and name is None:
			name = self.options(item = item, popups = popups, cloud = cloud)
			if name == Handler.ReturnUnavailable or name == Handler.ReturnCancel:
				return {'success' : False, 'error' : name}

		service = self.service(name = name)

		if popups and service is None:
			if self.mType == Handler.TypeTorrent:
				title = 33473
				message = 33483
			elif self.mType == Handler.TypeUsenet:
				title = 33482
				message = 33484
			elif self.mType == Handler.TypeHoster:
				title = 33488
				message = 33485
			if interface.Dialog.option(title = title, message = message, labelConfirm = 33011, labelDeny = 33486):
				tools.Settings.launch(tools.Settings.CategoryStream)
			return Handler.ReturnUnavailable

		result = service.handle(link = link, item = item, download = download, popups = popups, close = close, select = mode == Handler.ModeFile, cloud = cloud, strict = strict)

		# Needed by debrid services to delete files from cloud after playback.
		handle = None
		if result and 'handle' in result: handle = result['handle'] # From HandleGaia.
		if not handle:
			try: handle = service.serviceId()
			except: pass
			if not handle: handle = service.id()
		result['handle'] = handle

		# Used by player.py.
		try: result['service'] = service.serviceName() # Resolvers and Orion.
		except: result['service'] = service.name()

		if not result['success']:
			if not result['error'] in [Handler.ReturnUnavailable, Handler.ReturnExternal, Handler.ReturnCancel, Handler.ReturnPack]:
				if notification and (not 'notification' in result or not result['notification']):
					try: tools.Logger.log('Resolving or playback failure: ' + tools.Converter.jsonTo(result), type = tools.Logger.TypeError)
					except:
						try: tools.Logger.log('Resolving or playback failure: ' + str(result), type = tools.Logger.TypeError)
						except: pass
					interface.Dialog.notification(title = 33448, message = 35295, icon = interface.Dialog.IconError)
				result['error'] = Handler.ReturnUnavailable
		return result

class Handle(object):

	def __init__(self, name, id = None, abbreviation = None, acronym = None, priority = None, debrid = False, open = False, addon = False, account = None):
		self.mId = self.mType = name.lower() if id is None else id
		self.mName = name
		self.mAbbreviation = abbreviation
		self.mAcronym = acronym
		self.mPriority = priority
		self.mDebrid = debrid
		self.mOpen = open
		self.mAddon = addon
		self.mAccount = account

	def data(self):
		return {
			'id' : self.mId,
			'type' : self.mType,
			'name' : self.mName,
			'abbreviation' : self.mAbbreviation,
			'acronym' : self.mAcronym,
			'priority' : self.mPriority,
			'debrid' : self.mDebrid,
			'open' : self.mOpen,
			'addon' : self.mAddon,
			'account' : self.mAccount,
		}

	def id(self):
		return self.mId

	def type(self):
		return self.mType

	def name(self):
		return self.mName

	def abbreviation(self):
		return self.mAbbreviation

	def acronym(self):
		return self.mAcronym

	def priority(self):
		return self.mPriority

	def debrid(self):
		return self.mDebrid

	def open(self):
		return self.mOpen

	def addon(self):
		return self.mAddon

	def account(self):
		return self.mAccount

	def cache(self, item):
		if tools.Tools.isDictionary(item):
			try: item = item['stream']
			except: pass

		# Main Gaia debrid handlers.
		if item.accessCache(self.id()): return True

		# Sub-debrids.
		try:
			id = self.serviceId()
			if id and item.accessCache(id): return True
		except:
			id = True

		# Use any sub-debrids cache for the main "Automatic" option.
		if (id is True or id is None):
			debrids = self.debrids()
			if debrids:
				for debrid in debrids:
					if item.accessCache(debrid): return True

		return False

	def enabled(self, type):
		generic = type is None or type == Handler.TypeAll

		if tools.Settings.getInteger('stream.general.handle') == 2:
			if not generic and tools.Settings.getInteger('stream.general.handle.%s' % type) == 0: return False

		if type == Handler.TypeDirect and self.type() == Handler.TypeDirect: return True

		setting = tools.Settings.getInteger('stream.%s.handle' % self.type())
		if setting == 2:
			if generic: return True
			if tools.Settings.getInteger('stream.%s.handle.%s' % (self.type(), type)) >= 1: return True
		elif setting >= 1:
			return True

		return False

	def supported(self, item, cloud = False):
		try:
			services = self.services()
			if services is None:
				return False
			else:
				stream = None
				if tools.Tools.isDictionary(item):
					try: stream = item['stream']
					except: pass
				elif tools.Tools.isInstance(item, Stream):
					stream = item

				if stream:
					# Some debrid services, like Premiumize, still have some old hoster files cached, although they do not support new downloads for the hoster anymore.
					# If the file is cached, assume it is supported, even if the hoster is not listed in the debrid's service list anymore.
					if self.cache(item = item): return True

					modes = stream.sourceMode(all = True)
					if not modes: return False
				else:
					modes = [item]

				all = []
				for service in services:
					service = service.lower()
					all.append(service)

					# The legacy Orion returns hosters without any symbols (eg: "nitrodownload" instead of "nitro.download").
					plain = tools.Tools.replaceNotAlphaNumeric(service)
					if not plain == service: all.append(plain)

				for mode in modes:
					mode = mode.lower()
					modePlain = tools.Tools.replaceNotAlphaNumeric(mode)

					# External providers do not always set the full hoster domain (eg: vidoza instead of vidoza.net).
					# Do not just check if the domain contains the hoster, since this would match eg: "cloud" and "icloud".
					# Instead check if the domain starts with the hoster and followed by a ".".
					modeExtra = None if '.' in mode else (mode + '.')

					for service in all:
						if mode == service or modePlain == service or (modeExtra and '.' in service and service.startswith(modeExtra)): return True

					if mode == self.id():
						if 'offcloud' in self.id(): return True
		except: tools.Logger.error()
		return False

	def debrids(self, all = False):
		if all:
			from lib.debrid.debrid import Debrid
			return [i.id() for i in Debrid.handles()]
		return None

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False, strict = False):
		pass

	def services(self):
		pass

class HandleAutomatic(Handle):

	Id = 'automatic'

	def __init__(self, service = None):
		Handle.__init__(self, name = 'Automatic', debrid = True, open = True, addon = False)

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False, strict = False):
		from lib.debrid import core

		exclude = []
		handler = Handler()

		result = None

		if item['stream'].accessTypeDirect():
			service = handler.serviceBest(item = item, cached = False, cloud = cloud, serviceGlobal = True, serviceIndividual = True, fallback = False, exclude = exclude)
			if service and not service in exclude:
				result = handler.handle(name = service, link = link, item = item, download = download, popups = popups, close = close, cloud = cloud, strict = strict, notification = False)
				if not result or ('error' in result and result['error'] == Handler.ReturnUnavailable): exclude.append(service)

		# Cached
		while True:
			service = handler.serviceBest(item = item, cached = True, cloud = cloud, serviceGlobal = False, serviceIndividual = True, fallback = False, exclude = exclude)
			if not service or service in exclude: break
			result = handler.handle(name = service, link = link, item = item, download = download, popups = popups, close = close, cloud = cloud, strict = strict, notification = False)
			if not result or ('error' in result and result['error'] == Handler.ReturnUnavailable): exclude.append(service)
			else: break

		# Uncached
		if not result or ('error' in result and result['error'] == Handler.ReturnUnavailable):
			while True:
				service = handler.serviceBest(item = item, cached = False, cloud = cloud, serviceGlobal = False, serviceIndividual = True, fallback = True, exclude = exclude)
				if not service or service in exclude: break
				result = handler.handle(name = service, link = link, item = item, download = download, popups = popups, close = close, cloud = cloud, strict = strict, notification = False)
				if not result or ('error' in result and result['error'] == Handler.ReturnUnavailable): exclude.append(service)
				else: break

		return result if result else core.Core.addResult(link = None)

	def enabled(self, type):
		return True

	def supported(self, item, cloud = False):
		return True

class HandleDirect(Handle):

	def __init__(self):
		Handle.__init__(self, interface.Translation.string(33489))

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False, strict = False):
		from lib import debrid
		provider = item['stream'].sourceProvider().lower()

		# RealDebrid premium links need to be resolved through RealDebrid.
		# Other debrid services have direct links.
		handle = debrid.realdebrid.Handle()
		if provider == handle.id(): return handle.handle(link = link, item = item, download = download, popups = popups, close = close, select = select, cloud = cloud, strict = strict)
		else: return debrid.core.Core.addResult(link = link)

	def supported(self, item, cloud = False):
		if tools.Tools.isInstance(item, Stream): item = {'stream' : item}
		if item['stream'].accessTypeDirect(): return True
		elif cloud and not item['stream'].sourceProvider().lower() == 'realdebrid': return False
		else: return False

	def services(self):
		return None

class HandleResolver(Handle):

	# Order of appearance in the selection dialog.
	Debrids = ['premiumize', 'offcloud', 'realdebrid', 'debridlink', 'alldebrid', 'linksnappy', 'megadebrid', 'rapidpremium', 'simplydebrid', 'smoozed']

	Support = {}
	Services = {}
	Modules = {}

	def __init__(self, name, module, id = None, abbreviation = None, acronym = None, priority = None, debrid = False, open = False, addon = False, service = None):
		Handle.__init__(self, name = name, id = id, abbreviation = abbreviation, acronym = acronym, priority = priority, debrid = debrid, open = open, addon = addon)

		self.mModule = module
		self.mService = service
		self.mServiceId = None
		self.mServiceName = None
		if service: self.mServiceName = self.serviceClean(service, lower = False)
		if self.mServiceName:
			self.mServiceId = self.mServiceName.lower()
			self.mId += self.mServiceId

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			HandleResolver.Support = {}
			HandleResolver.Services = {}

	##############################################################################
	# GENERAL
	##############################################################################

	def module(self):
		# Do not import at the start of the script, otherwise the resolver code will be loaded everytime handler.py is imported, drastically slowing down menus.
		if not self.mModule in HandleResolver.Modules:
			try:
				import importlib
				HandleResolver.Modules[self.mModule] = importlib.import_module(self.mModule)
			except:
				HandleResolver.Modules[self.mModule] = False
		return HandleResolver.Modules[self.mModule]

	def resolver(self):
		for resolver in [tools.ResolveUrl, tools.UrlResolver]:
			if resolver.Id == self.mModule: return resolver
		return None

	def instances(self, type = None):
		result = None
		try:
			result = []
			module = self.module()
			if module:
				for i in module.relevant_resolvers(order_matters = True, include_universal = True):
					i = i()
					if i.isUniversal():
						try: hosts = i.get_hosts()
						except:
							try: hosts = i.get_all_hosters()
							except: hosts = i.get_hosters()
						if hosts and tools.Tools.isArray(hosts) and tools.Tools.isArray(hosts[0]): hosts = hosts[0]
						if type is None:
							result.append(i)
						elif type == Handler.TypeTorrent:
							if 'torrent' in hosts or 'magnet' in hosts: result.append(i)
						elif type == Handler.TypeUsenet:
							if 'usenet' in hosts or 'nzb' in hosts: result.append(i)
						elif type == Handler.TypeHoster:
							result.append(i)

				# Sort resolvers to have the same order as Gaia.
				sort = []
				resolver = self.resolver()
				for i in result:
					id = self.serviceClean(i.name, lower = True)
					if resolver.authenticated(type = id):
						instance = self.__class__(service = i.name)
						try: index = HandleResolver.Debrids.index(instance.serviceId())
						except: index = 99999
						sort.append((index, instance))
				result = [i[1] for i in sorted(sort, key = lambda i: i[0])]
		except:
			tools.Logger.error()
			result = []

		return result

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False, strict = False):
		from lib.debrid import core
		try:
			if item and item['stream'].accessTypeDirect():
				return core.Core.addResult(link = link)
			else:
				# Resolvers do currently not support .torrent file uploads through debrid APIs.
				# Try to convert to magnet and use that instead.
				# For normal .torrent files this should always work.
				# For special .torrent files (eg: YGG with private tracker/account info) this will probably not work, but at least cached torrents should still work, since debrid APIs seems to only use the hash from the magnet for cached torrent retrieval.
				# Should technically also work for private torrents, since the privacy is just a private tracker with auth data in its URI (at least for YGG).
				if item and item['stream'].sourceTypeTorrent() and not network.Networker.linkIsMagnet(link):
					container = network.Container(link)
					magnet = container.torrentMagnet()
					if magnet: link = magnet

				module = self.module()
				if module:
					if self.service():
						for i in module.relevant_resolvers(order_matters = True):
							if i.name == self.service():
								i = i()
								try:
									i.login()
									host, id = i.get_host_and_id(link)
									linkNew = i.get_media_url(host, id)
									if linkNew: return self.result(link = linkNew, item = item)
								except: pass
								break
					else:
						# First check if a debrid resolver is available.
						resolvers = [i() for i in module.relevant_resolvers(order_matters = True) if i.isUniversal()]
						if len(resolvers) == 0: resolvers = [i() for i in module.relevant_resolvers(order_matters = True, include_universal = False) if 'rapidgator.net' in i.domains]
						for i in resolvers:
							try:
								i.login()
								host, id = i.get_host_and_id(link)
								linkNew = i.get_media_url(host, id)
								if linkNew: return self.result(link = linkNew, item = item)
							except: pass

						# If not supported by debrid, try normal resolvers.
						media = module.HostedMediaFile(url = link, include_disabled = True, include_universal = False)
						if media.valid_url() == True: return self.result(link = media.resolve(allow_popups = popups), item = item)
		except: tools.Logger.error()
		return core.Core.addResult(link = None)

	def result(self, link, item = None):
		from lib.debrid import core
		if link and item and item['stream'].filePack(): interface.Dialog.notification(title = 33755, message = 33756, icon = interface.Dialog.IconWarning, duplicates = True)
		return core.Core.addResult(link = link)

	def enabled(self, type):
		if type in [Handler.TypeTorrent, Handler.TypeHoster, Handler.TypeAll] and self.module():
			if type == Handler.TypeTorrent and not self.debrids(): return False
			resolver = tools.Resolver.resolver(self.mModule)
			if resolver and (not self.serviceId() or resolver.authenticated(type = self.serviceId())):
				return Handle.enabled(self, type = type)
		return False

	def supported(self, item, cloud = False):
		if tools.Tools.isInstance(item, Stream): item = {'stream' : item}
		if cloud: return False
		elif item['stream'].accessTypeDirect(): return True
		elif item['stream'].sourceTypeTorrent(): return True
		else: return Handle.supported(self, item)

	def debrids(self, item = None):
		try:
			result = []
			module = self.module()
			if module:
				resolvers = module.relevant_resolvers(order_matters = True)
				debrids = Handle.debrids(self, all = True)
				for i in debrids:
					for j in resolvers:
						if i in str(j).lower():
							if item:
								j = j()
								link = item['stream'].linkPrimary()
								host, id = j.get_host_and_id(link)
								if j.valid_url(url = link, host = host): result.append(i)
							else:
								result.append(i)
							break
			return result
		except:
			tools.Logger.error()
			return []

	def service(self):
		return self.mService

	def serviceId(self):
		return self.mServiceId

	def serviceName(self):
		return self.mServiceName

	def serviceClean(self, service, lower = True):
		service = tools.Regex.remove(data = service, expression = '.*?(\..*)', group = 1) # Remove TLD. Eg: Premiumize.me
		service = tools.Regex.remove(data = service, expression = tools.Regex.Symbol, all = True) # Remove symbols. Eg: Real-Debrid
		if service.lower() == 'rpnet': service = 'RapidPremium'
		if lower: service = service.lower()
		return service

	def services(self):
		if not self.mModule in HandleResolver.Services:
			HandleResolver.Support[self.mModule] = {}
			HandleResolver.Services[self.mModule] = []
			try: from functools import reduce
			except: pass
			try:
				result = []

				module = self.module()
				if module:
					resolvers = module.relevant_resolvers(order_matters = True)
					for resolver in resolvers:
						resolver = resolver()
						# The "domains" attribute of universal debrid resolvers is not always fully populated with all TLDs.
						# For instance, the ".cc" TLD is missing for clicknupload although other TLDs are present.
						# Use the get_hosts function to retrieve all available domains.
						if resolver.isUniversal():
							try: hosts = resolver.get_hosts()
							except:
								try: hosts = resolver.get_all_hosters()
								except:
									try: hosts = resolver.get_hosters()
									except: hosts = resolver.domains
							if hosts and tools.Tools.isArray(hosts) and tools.Tools.isArray(hosts[0]): hosts = hosts[0]
							HandleResolver.Support[self.mModule][self.serviceClean(resolver.name)] = hosts
						else:
							hosts = resolver.domains
						if not '*' in hosts: result.append(hosts)

					result = [i.lower() for i in reduce(lambda x, y : x + y, result)]
					result = [x for y, x in enumerate(result) if x not in result[:y]]

				HandleResolver.Services[self.mModule] = result
			except: tools.Logger.error()

		try: return HandleResolver.Support[self.mModule][self.serviceId()]
		except: return HandleResolver.Services[self.mModule]

class HandleResolveUrl(HandleResolver):

	def __init__(self, service = None):
		HandleResolver.__init__(self, name = interface.Translation.string(35310), module = 'resolveurl', debrid = True, open = True, addon = True, service = service)

class HandleUrlResolver(HandleResolver):

	def __init__(self, service = None):
		HandleResolver.__init__(self, name = interface.Translation.string(33747), module = 'urlresolver', debrid = True, open = True, addon = True, service = service)

class HandleGaia(Handle):

	Support = None
	Services = None

	def __init__(self, service = None):
		Handle.__init__(self, name = 'Gaia', debrid = True, open = True, addon = False)

		self.mServiceTypes = None
		self.mService = service
		self.mServiceId = None
		self.mServiceName = None
		if service:
			service = tools.Regex.remove(data = service, expression = '.*?(\..*)', group = 1) # Remove TLD. Eg: Premiumize.me
			service = tools.Regex.remove(data = service, expression = tools.Regex.Symbol, all = True) # Remove symbols. Eg: Real-Debrid
			self.mServiceName = service

		if self.mServiceName:
			self.mServiceId = self.mServiceName.lower()
			self.mId += self.mServiceId

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			HandleGaia.Support = {}
			HandleGaia.Services = {}

	##############################################################################
	# GENERAL
	##############################################################################

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False, strict = False):
		from lib.debrid import core

		result = None

		try:
			services = [self.support()[self.serviceId()]]
			automatic = False
		except:
			services = self.support().values()
			automatic = True

		try: type = item['stream'].sourceType()
		except: type = None

		# First try cached services.
		cached = []
		if automatic:
			for service in services:
				if (not type or not type in service or service[type]):
					if service['handle'].cache(item):
						cached.append(service['handle'].id())
						result = service['handle'].handle(link = link, item = item, download = download, popups = popups, close = close, select = select, cloud = cloud, strict = strict)

						try: handle = service['handle'].serviceId()
						except: handle = None
						if not handle: handle = service['handle'].id()
						result['handle'] = handle

						if result['success'] or result['error'] in [Handler.ReturnExternal, Handler.ReturnCancel, Handler.ReturnSelection, Handler.ReturnPack]: return result

		# Do not try uncached services during automatic selection if the file is cached at at least one service.
		# Otherwise if the file is cached with only one service, and the user clicks play, and that one service fails, it will start the download process with the next available debrid service.
		# In such a case, just fail the playback. If the user still wants to add it to the download list, he can do so from the context menu -> Play -> Play With.
		if automatic and cached:
			interface.Dialog.notification(title = 35325, message = 33411, icon = interface.Dialog.IconError, duplicates = True)
			return core.Core.addResult(error = Handler.ReturnUnavailable, notification = True)

		cached = []
		for service in services:
			if (not type or not type in service or service[type]):
				if service['handle'].cache(item): cached.append(service['handle'].id())
				if service['handle'].supported(item = item, cloud = cloud):
					result = service['handle'].handle(link = link, item = item, download = download, popups = popups, close = close, select = select, cloud = cloud, strict = strict)

					try: handle = service['handle'].serviceId()
					except: handle = None
					if not handle: handle = service['handle'].id()
					result['handle'] = handle

					if result['success'] or result['error'] in [Handler.ReturnExternal, Handler.ReturnCancel, Handler.ReturnSelection, Handler.ReturnPack]: return result

		return result if (result and result['success']) else core.Core.addResult(error = Handler.ReturnUnavailable)

	def enabled(self, type):
		if type in [Handler.TypeTorrent, Handler.TypeUsenet, Handler.TypeHoster, Handler.TypeAll]:
			try: service = self.support()[self.serviceId()]
			except: service = None
			if service: return service['handle'].enabled(type = type)
			else: return Handle.enabled(self, type = type)
		return False

	def supported(self, item, cloud = False):
		if tools.Tools.isInstance(item, Stream): item = {'stream' : item}
		type = item['stream'].sourceType()

		try: services = [self.support()[self.serviceId()]]
		except: services = self.support().values() # Automatic

		for service in services:
			if (not type in service or service[type]) and service['handle'].supported(item = item, cloud = cloud): return True

		return False

	def instances(self, type = None):
		instances = []
		for service in self.support().values():
			if type is None or (type in service and service[type]):
				instances.append(self.__class__(service = service['handle'].name()))
		return instances

	def debrids(self):
		return list(self.support().keys())

	def service(self):
		return self.mService

	def serviceId(self):
		return self.mServiceId

	def serviceName(self):
		return self.mServiceName

	def services(self):
		if HandleGaia.Support is None:
			from lib import debrid

			HandleGaia.Support = {}
			HandleGaia.Services = []

			debrids = [
				[debrid.premiumize.Core(), debrid.premiumize.Handle()],
				[debrid.offcloud.Core(), debrid.offcloud.Handle()],
				[debrid.realdebrid.Core(), debrid.realdebrid.Handle()],
			]
			for debrid in debrids:
				if debrid[0].accountValid():
					torrent = debrid[0].streamingTorrent()
					usenet = debrid[0].streamingUsenet()
					hoster = debrid[0].streamingHoster()

					services = debrid[1].services()
					if usenet: services.insert(0, Handler.TypeUsenet)
					if torrent: services.insert(0, Handler.TypeTorrent)

					HandleGaia.Support[debrid[0].id()] = {
						'handle' : debrid[1],
						'service' : services,
						Handler.TypeTorrent : torrent,
						Handler.TypeUsenet : usenet,
						Handler.TypeHoster : hoster,
					}

					if services: HandleGaia.Services.extend(services)

			HandleGaia.Services = tools.Tools.listUnique(HandleGaia.Services)

		try: return HandleGaia.Support[self.serviceId()]['service']
		except: return HandleGaia.Services

	def support(self):
		self.services() # Initialize.
		return HandleGaia.Support if HandleGaia.Support else {}

class HandleOrion(Handle):

	Support = None
	Services = None

	def __init__(self, service = None):
		Handle.__init__(self, name = 'Orion', debrid = True, open = False, addon = True)

		self.mService = service
		self.mServiceId = None
		self.mServiceName = None
		if service: self.mServiceName = service
		if self.mServiceName:
			self.mServiceId = self.mServiceName.lower()
			self.mId += self.mServiceId

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			HandleOrion.Support = {}
			HandleOrion.Services = {}

	##############################################################################
	# GENERAL
	##############################################################################

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False, strict = False):
		from lib.debrid import core

		stream = item['stream']
		media = stream.metaMedia()
		title = stream.metaTitle()
		season = stream.metaSeason()
		episode = stream.metaEpisode()

		containerData = None
		containerName = None
		containerType = None
		containerSize = None
		if (stream.sourceTypeTorrent() and not network.Networker.linkIsMagnet(link)) or stream.sourceTypeUsenet():
			container = network.Container(link = link, download = True).information()
			if container:
				containerData = container['data']
				containerType = container['mime']
				containerSize = container['size']
				if not containerName:
					try: containerName = stream.fileName(generate = True)
					except: pass
					if not containerName:
						try: containerName = container['name']
						except: pass
						if not containerName:
							try: containerName = source.hash()
							except: pass
				if containerName and container['extension'] and not containerName.endswith(container['extension']):
					containerName += container['extension']

		error = None
		result = None
		data = Orionoid().debridResolve(link = link, type = self.serviceId(), containerData = containerData, containerName = containerName, containerType = containerType, containerSize = containerSize)
		if data:
			if 'error' in data:
				interface.Dialog.notification(title = 35325, message = data['error'], icon = interface.Dialog.IconError, duplicates = True)
				return core.Core.addResult(error = data['error'], notification = True)
			elif 'files' in data:
				links = [i for i in data['files'] if i['original']['link']]
				if 'redirect' in data and len(links) == 0:
					interface.Dialog.notification(title = 35321, message = 35322, icon = interface.Dialog.IconInformation, duplicates = True)
					return core.Core.addResult(error = 'Remote Downloading', notification = True)

				data = data['files']
				if select:
					data = [i for i in data if not i['original']['category'] or i['original']['category'] == 'video']
					data = tools.Tools.listSort(data = data, key = lambda i : i['original']['name'])
					items = [i['original']['name'] for i in data]
					choice = interface.Dialog.select(title = self.serviceName(), items = items)
					if choice >= 0: result = data[choice]['original']['link']
				else:
					files = []

					# Match video, match title, match number, and exclude prohibited keywords.
					for file in data:
						name = file['original']['name']
						validVideo = False
						validTitle = False
						validNumber = False
						validProhibited = False
						if not file['original']['category'] or file['original']['category'] == 'video':
							validVideo = True
							if Stream.titleValid(data = name, media = media, title = title):
								validTitle = True
								if tools.Media.typeMovie(media) or Stream.numberShowValid(data = name, season = season, episode = episode):
									validNumber = True
									if not Stream.titleProhibited(data = name, title = title, exception = not season is None and season == 0):
										validProhibited = True
										result = file['original']['link']
										break
						files.append({'video' : validVideo, 'title' : validTitle, 'number' : validNumber, 'prohibited' : validProhibited, 'data' : file})

					if not result:
						# Match video, match title, match number, and allow prohibited keywords.
						for file in files:
							if file['video'] and file['title'] and file['number']:
								result = file['original']['link']
								break

						if result is None and tools.Media.typeTelevision(media):
							# Match video, ignore title, match number, and allow prohibited keywords.
							for file in files:
								if file['video'] and file['number']:
									result = file['original']['link']
									break
							# Ignore video, ignore title, match number, and allow prohibited keywords.
							for file in files:
								if file['number']:
									result = file['original']['link']
									break

						if result is None:
							# Ignore video, match title, match number, and allow prohibited keywords.
							for file in files:
								if file['title'] and file['number']:
									result = file['original']['link']
									break

						# Pick largest file.
						if result is None:
							if strict and stream.filePack() and not episode is None:
								error = core.Core.ErrorPack
								interface.Dialog.notification(title = 35052, message = 35053, icon = interface.Dialog.IconError)
							else:
								data = tools.Tools.listSort(data = data, key = lambda i : i['original']['size'], reverse = True)
								result = data[0]['original']['link']
			elif 'redirect' in data and not 'files' in data:
				interface.Dialog.notification(title = 35321, message = 35322, icon = interface.Dialog.IconInformation, duplicates = True)
				return core.Core.addResult(error = 'Remote Downloading', notification = True)

		return core.Core.addResult(link = result, error = error)

	def enabled(self, type):
		return type in [Handler.TypeTorrent, Handler.TypeUsenet, Handler.TypeHoster, Handler.TypeAll] and Orionoid().accountEnabled() and Handle.enabled(self, type = type)

	def supported(self, item, cloud = False):
		if tools.Tools.isInstance(item, Stream): item = {'stream' : item}
		if cloud: return True

		try: services = [self.support()[self.serviceId()]]
		except: services = self.support().values() # Automatic

		for service in services:
			if item['stream'].sourceTypeTorrent():
				if Handler.TypeTorrent in service and service[Handler.TypeTorrent]['status']: return True
			elif item['stream'].sourceTypeUsenet():
				if Handler.TypeUsenet in service and service[Handler.TypeUsenet]['status']: return True
			elif item['stream'].sourceTypeHoster():
				if Handle.supported(self, item): return True

		return False

	def instances(self, type = None):
		instances = []
		for service in self.support().values():
			if type is None or type in service:
				instances.append(self.__class__(service = service['name']))
		return instances

	def debrids(self):
		return list(self.support().keys())

	def service(self):
		return self.mService

	def serviceId(self):
		return self.mServiceId

	def serviceName(self):
		return self.mServiceName

	def services(self):
		if HandleOrion.Support is None:
			try:
				# Do not cache for too long, in case the user authenticates a new account on Orion and the Gaia cache still has the old unauthenticated data.
				# This function is called multiple times during scraping, so do not use cacheRefreshXXX().
				data = cache.Cache.instance().cacheShort(Orionoid().debridSupport)

				if data:
					HandleOrion.Support = data
					HandleOrion.Services = []

					for id, value in data.items():
						services = []
						if 'torrent' in value: services.append(Handler.TypeTorrent)
						if 'usenet' in value: services.append(Handler.TypeUsenet)

						if 'hoster' in value and 'service' in value['hoster']:
							for j in value['hoster']['service']:
								services.extend(j['domain']['all'])

						HandleOrion.Services.extend(services)
						HandleOrion.Support[id]['service'] = services

					HandleOrion.Services = tools.Tools.listUnique(HandleOrion.Services)
			except: tools.Logger.error()

		try: return HandleOrion.Support[self.serviceId()]['service']
		except: return HandleOrion.Services

	def support(self):
		self.services() # Initialize.
		return HandleOrion.Support if HandleOrion.Support else {}

class HandleYoutube(Handle):

	def __init__(self):
		Handle.__init__(self, 'YouTube', addon = True)
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False, strict = False):
		from lib.debrid import core
		from lib.modules.video import Video
		try:
			interface.Loader.hide()
			interface.Dialog.notification(title = 35296, message = 35365, icon = interface.Dialog.IconSuccess, time = 10000)
			interface.Core.close()

			Video(internal = True).play(link = link)

			interface.Loader.hide()
			tools.Time.sleep(0.5)
			interface.Loader.hide()

			player = interface.Player()
			started = False
			for i in range(30):
				# YouTube can show a download progress dialog, or a list dialog for selecting a specific file from the torrent, and possibly other dialogs.
				# YouTube does not start playing if the Gaia playback window is visible. Therefore check >= IdDialogCustom.
				if player.isPlaying():

					# Use the custom isPlayback() function to wait until the video has actually started.
					# Otherwise no loader or loading window is visible while the YopuTube addon starts the playback.
					for j in range(20):
						if player.isPlayback() or player.statusFinished(): break
						tools.Time.sleep(0.5)
						interface.Loader.hide()

					started = True
					break
				tools.Time.sleep(0.5)
				interface.Loader.hide()

			# Close the stream window, otherwise YouTube opens the player behind it.
			if player.isPlaying() and window.WindowStreams.enabled():
				window.WindowStreams.close()

			# Assume that YouTube failed to start/resolve the torrent. YouTube only shows an error in the Kodi log file.
			if not started:
				interface.Dialog.notification(title = 35296, message = 35366, icon = interface.Dialog.IconWarning, time = 4000)
				return core.Core.addResult(error = Handler.ReturnUnavailable)

			return core.Core.addResult(error = Handler.ReturnExternal) # Return because YouTube will handle the playback.
		except:
			tools.Logger.error()

	def enabled(self, type):
		return type in [Handler.TypeHoster, Handler.TypeAll] and tools.YouTube.installed() and Handle.enabled(self, type = type)

	def supported(self, item, cloud = False):
		if tools.Tools.isInstance(item, Stream): item = {'stream' : item}
		if cloud: return False
		return Handle.supported(self, item)

	def services(self):
		if self.mServices is None:
			from lib.modules.video import Video
			self.mServices = []
			# Videos do play, even without authentication.
			#if Video.enabled(external = True) and Video.authenticated(external = True): self.mServices.extend(Video.domains())
			if Video.enabled(external = True): self.mServices.extend(Video.domains())
		return self.mServices

class HandleTorrenter(Handle):

	def __init__(self, name, module):
		Handle.__init__(self, name = name, addon = True)
		self.mModule = module
		self.mServices = None
		self.mLog = None

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False, strict = False):
		from lib.debrid import core
		try:
			self.logStart()
			data = []

			try: stream = item['stream']
			except: stream = None

			try: metadata = item['metadata']
			except: metadata = None

			try: imdb = stream.idImdb()
			except:
				try: imdb = metadata['imdb']
				except: imdb = None

			try: tmdb = stream.idTmdb()
			except:
				try: tmdb = metadata['tmdb']
				except: tmdb = None

			try: tvdb = stream.idTvdb()
			except:
				try: tvdb = metadata['tvdb']
				except: tvdb = None

			# Link
			if not network.Networker.linkIsMagnet(link):
				container = network.Container(link)

				source = container.information()
				if source['path'] is None and source['data'] is None: return self.failure(file = True)

				name = None
				try: name = stream.fileName()
				except: pass
				if not name:
					try: name = stream.fileName(generate = True)
					except: pass
					if not name:
						try: name = stream.hash()
						except: pass
				if not name: name = 'Download'
				if source['extension'] and not name.endswith(source['extension']): name += source['extension']

				data.append({'name' : 'file', 'filename' : name, 'type' : source['mime'], 'data' : source['data']})
			else:
				data.append({'name' : 'uri', 'data' : link})

			# Media
			media = 'movie'
			if item:
				if stream:
					if stream.metaMediaShow(): media = 'episode'
				elif 'type' in item and item['type']:
					if tools.Media.typeTelevision(item['type']): media = 'episode'
				elif 'tvshowtitle' in item: media = 'episode'
			data.append({'name' : 'type', 'data' : media})

			# Show
			season = None
			episode = None
			if media == 'episode':
				if stream:
					season = stream.metaSeason()
					episode = stream.metaEpisode()
				elif metadata:
					season = metadata['season']
					episode = metadata['episode']
				if not season is None: data.append({'name' : 'season', 'data' : str(season)})
				if not episode is None: data.append({'name' : 'episode', 'data' : str(episode)})

			# TMDB
			if media == 'movie' and tmdb:
				data.append({'name' : 'tmdb', 'data' : str(tmdb)})
			else:
				try:
					from lib.modules.account import Tmdb
					key = Tmdb().key()
					if key:
						if media == 'episode' and tvdb: # Shows - IMDb ID for episodes does not work on TMDb.
							result = cache.Cache.instance().cacheExtended(network.Networker().requestJson, link = 'http://api.themoviedb.org/3/find/%s?api_key=%s&external_source=tvdb_id' % (tvdb, key))
							result = result['tv_results']
							if tools.Tools.isArray(result): result = result[0]
							if result and 'id' in result and result['id']:
								data.append({'name' : 'show', 'data' : str(result['id'])})
								if not season is None and not episode is None:
									result = cache.Cache.instance().cacheExtended(network.Networker().requestJson, link = 'http://api.themoviedb.org/3/tv/%s/season/%s/episode/%s?api_key=%s' % (result['id'], season, episode, key))
									if result and 'id' in result: data.append({'name' : 'tmdb', 'data' : str(result['id'])})
						elif media == 'movie' and imdb:
							result = cache.Cache.instance().cacheExtended(network.Networker().requestJson, link = 'http://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % (imdb, key))
							result = result['movie_results']
							if tools.Tools.isArray(result): result = result[0]
							if result and 'id' in result and result['id']: data.append({'name' : 'tmdb', 'data' : str(result['id'])})
				except: tools.Logger.error()

			interface.Dialog.notification(title = 35316, message = 35319, icon = interface.Dialog.IconSuccess)
			interface.Core.close()
			interface.Loader.hide() # Make sure Gaia's loaders are hidden, so that we only detect Elementum loaders below.

			if download: hash = network.Networker().requestText(method = network.Networker.MethodPost, type = network.Networker.DataMulti, link = self.mModule.linkAdd(), data = data)
			else: hash = network.Networker().requestText(method = network.Networker.MethodPost, type = network.Networker.DataMulti, link = self.mModule.linkPlay(), data = data)

			if not hash:
				try: hash = stream.hash()
				except: pass
				if not hash: hash = network.Container(link).torrentHash()
				if not hash: return self.failure(hash = True)
				hash = hash.lower() # Hash must be lower case.

			started = False
			for i in range(0, 60): # Do not check forever, in case Elementum fails to add/resolve the torrent. Default Elementum resolve timeout is 40 secs.
				result = network.Networker().requestJson(link = self.mModule.linkList())
				if result:
					for j in result:
						if j['id'].lower() == hash:
							started = True
							break
					if started: break
				elif i > 10 and not interface.Loader.visible(): # Elementum failed to resolve the torrent and closes the loader. Give some time for the loader to show up in the first place.
					break
				tools.Time.sleep(1)

			# Assume that Elementum failed to start/resolve the torrent. Elementum only shows an error in the Kodi log file.
			if not started: return self.failure(resolve = True)

			if not download:
				streamable = None
				removed = False
				while True:
					found = False
					result = network.Networker().requestJson(link = self.mModule.linkList())
					if result:
						for i in result:
							if i['id'].lower() == hash:
								found = True
								if 'status' in i and i['status']:
									status = i['status'].lower()
									if status in ['paused', 'stalled'] and 'progress' in i and i['progress'] == 0 and 'download_rate' in i and i['download_rate'] == 0:
										# If torrent is paused right at the start.
										# Eg: not enough disk space to fully download the file (eg: file is 40GB and free space is 20GB).
										streamable = False
										break
									elif not status in ['buffering', 'paused', 'stalled']:
										streamable = status in ['downloading', 'finished', 'seeding', 'playing']
										break

					# Otherwise removed by user or somhow failed to download.
					if not found:
						removed = True
						break
					elif not streamable is None:
						break

					tools.Time.sleep(1)

				# If the user manually cancels the buffering dialog in Kodi.
				# There seems to be no other way of detecting this.
				if self.logCheck(cancel = True):
					return self.failure(cancel = True)

				if streamable:
					player = interface.Player()
					if not player.isPlaying():
						interface.Loader.show()

						# Once Elementum finished buffering, it sends a play command to Kodi.
						# This command can take some time to initialize the Python invoker, execute the code, and start playback.
						# Sometimes this happens fast, but often it takes more than 5 seconds.
						# Make sure to wait long enough here.
						for i in range(30):
							if player.isPlaying(): break
							tools.Time.sleep(0.5)

						if not player.isPlaying():
							network.Networker().request(link = self.mModule.linkPlay({'resume' : hash}))

							# Sometimes resuming does not start playback.
							# Try one more time.
							for i in range(6):
								if player.isPlaying(): break
								tools.Time.sleep(0.5)
							if not player.isPlaying(): network.Networker().request(link = self.mModule.linkPlay({'resume' : hash}))

						interface.Loader.hide()
				else:
					return self.failure(stream = True)

			# Close the stream window, otherwise Elementum opens the player behind it.
			if player.isPlaying() and window.WindowStreams.enabled():
				window.WindowStreams.close()

			self.logEnd()
			return core.Core.addResult(error = Handler.ReturnExternal) # Return because Elementum will handle the playback.
		except:
			tools.Logger.error()

	def failure(self, file = False, hash = False, resolve = False, stream = False, cancel = False):
		self.logEnd()
		from lib.debrid import core
		if file: message = 35424
		elif hash: message = 35423
		elif resolve: message = 35422
		elif stream: message = 35425
		elif cancel: message = 35427
		else: message = 35426
		interface.Dialog.notification(title = 35316, message = message, icon = interface.Dialog.IconWarning, duplicates = True)
		return core.Core.addResult(error = Handler.ReturnUnavailable)

	def logStart(self):
		if not self.mLog: self.mLog = tools.Hash.sha1(str(tools.Time.timestamp()) + str(tools.Math.random()))
		tools.Logger.log('[%s %s /]' % (self.mModule.Name.upper(), self.mLog))

	def logEnd(self):
		tools.Logger.log('[/ %s %s]' % (self.mModule.Name.upper(), self.mLog))

	def logCheck(self, cancel = False):
		data = tools.Logger.data()
		if data:
			expression = '\[%s\s%s\s\/\](.*)(?:$|\[\/\s%s\s%s\])' % (self.mModule.Name.upper(), self.mLog, self.mModule.Name.upper(), self.mLog)
			data = tools.Regex.extract(data = data, expression = expression, flags = tools.Regex.FlagAllLines)
			if cancel: return tools.Regex.match(data = data, expression = 'user\s*cancelled\s*the\s*buffering') and not tools.Regex.match(data = data, expression = 'not\s*enough\s*space\s*on\s*download\s*destination')
			else: return data
		return None

	def enabled(self, type):
		return type in [Handler.TypeTorrent, Handler.TypeAll] and self.mModule.installed() and Handle.enabled(self, type = type)

	def supported(self, item, cloud = False):
		if tools.Tools.isInstance(item, Stream): item = {'stream' : item}
		if cloud: return False
		elif item['stream'].sourceTypeTorrent(): return True
		else: return False

	def services(self):
		if self.mServices is None: self.mServices = ['torrent']
		return self.mServices

class HandleElementum(HandleTorrenter):

	def __init__(self):
		HandleTorrenter.__init__(self, name = 'Elementum', module = tools.Elementum)

class HandleQuasar(HandleTorrenter):

	def __init__(self):
		HandleTorrenter.__init__(self, name = 'Quasar', module = tools.Quasar)
