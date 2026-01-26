# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from lib.modules.tools import Tools, Regex, Platform, System, File, Hash, Settings, Media, Title, Language, Logger
from lib.modules.interface import Translation, Format, Dialog, Loader
from lib.modules.convert import ConverterSpeed
from lib.modules.network import Networker
from lib.modules.stream import Stream
from lib.modules.concurrency import Pool, Lock

##############################################################################
# CENTER
##############################################################################

class Center(object):

	Api						= 'emby'

	CategoryUsers			= 'Users'
	CategoryVideos			= 'Videos'
	CategoryItems			= 'Items'
	CategorySearch			= 'Search'
	CategoryShows			= 'Shows'

	ActionAuthenticate		= 'AuthenticateByName'
	ActionInfo				= 'PlaybackInfo'
	ActionHints				= 'Hints'
	ActionEpisodes			= 'Episodes'

	TypeBoth				= None
	TypeOriginal			= 'original'
	TypeTranscoded			= 'transcoded'
	TypeDefault				= TypeBoth
	TypeAll					= [
		{'value' : TypeBoth, 'label' : 33124, 'description' : 33697},
		{'value' : TypeOriginal, 'label' : 33693, 'description' : 33695},
		{'value' : TypeTranscoded, 'label' : 33694, 'description' : 33696},
	]

	FileBandwidthDefault	= None
	FileBandwidthAll		= [
		{'value' : FileBandwidthDefault, 'label' : 33800, 'description' : 33820}, # Automatic
		{'value' : True, 'label' : 35233, 'description' : 33831}, # Custom
		{'value' : 20971520, 'label' : 35240}, # 20mbps
		{'value' : 10485760, 'label' : 33644}, # 10mbps
		{'value' : 5242880, 'label' : 33999}, # 5mbps
		{'value' : 1048576, 'label' : 33643}, # 1mbps
	]

	FileContainerOriginal	= None
	FileContainerDefault	= Stream.FileContainerMkv
	FileContainerAll		= [FileContainerOriginal, Stream.FileContainerMkv, Stream.FileContainerWebm, Stream.FileContainerMp4, Stream.FileContainerMpg, Stream.FileContainerTs, Stream.FileContainerM2ts, Stream.FileContainerAsf, Stream.FileContainerOgg, Stream.FileContainerAvi, Stream.FileContainerWmv]
	FileContainerType		= { # https://github.com/MediaBrowser/Emby/wiki/Video-Streaming
		Stream.FileContainerMkv		: 'mkv',
		Stream.FileContainerWebm	: 'webm',
		Stream.FileContainerMp4		: 'mp4',
		Stream.FileContainerMpg		: 'mpeg',
		Stream.FileContainerTs		: 'ts',
		Stream.FileContainerM2ts	: 'm2ts',
		Stream.FileContainerAsf		: 'asf',
		Stream.FileContainerOgg		: 'ogv',
		Stream.FileContainerAvi		: 'avi',
		Stream.FileContainerWmv		: 'wmv',
	}

	VideoQualityOriginal	= None
	VideoQualityDefault		= VideoQualityOriginal
	VideoQualityAll			= [VideoQualityOriginal, Stream.VideoQualityHd8k, Stream.VideoQualityHd4k, Stream.VideoQualityHd1080, Stream.VideoQualityHd720, Stream.VideoQualitySd576, Stream.VideoQualitySd540, Stream.VideoQualitySd480, Stream.VideoQualitySd360, Stream.VideoQualitySd240, Stream.VideoQualitySd144]

	VideoCodecOriginal		= None
	VideoCodecDefault		= Stream.VideoCodecH264
	VideoCodecAll			= [VideoCodecOriginal, Stream.VideoCodecH265, Stream.VideoCodecH264, Stream.VideoCodecAv1, Stream.VideoCodecVp10, Stream.VideoCodecVp9, Stream.VideoCodecVp8, Stream.VideoCodecMpeg, Stream.VideoCodecThr, Stream.VideoCodecWmv]
	VideoCodecOrder			= [Stream.VideoCodecH264, Stream.VideoCodecVp9, Stream.VideoCodecVp8, Stream.VideoCodecMpeg, Stream.VideoCodecAv1, Stream.VideoCodecThr, Stream.VideoCodecH265, Stream.VideoCodecVp10, Stream.VideoCodecWmv]
	VideoCodecType			= {
		Stream.VideoCodecH265	: 'h265',
		Stream.VideoCodecH264	: 'h264',
		Stream.VideoCodecAv1	: 'av1',
		Stream.VideoCodecVp10	: 'vpx',
		Stream.VideoCodecVp9	: 'vp9',
		Stream.VideoCodecVp8	: 'vp8',
		Stream.VideoCodecMpeg	: 'mpeg4',
		Stream.VideoCodecThr	: 'theora',
		Stream.VideoCodecWmv	: 'wmv',
	}

	AudioChannelsOriginal	= None
	AudioChannelsDefault	= Stream.AudioChannels2
	AudioChannelsAll		= [AudioChannelsOriginal, Stream.AudioChannels1, Stream.AudioChannels2, Stream.AudioChannels4, Stream.AudioChannels6, Stream.AudioChannels8]

	AudioCodecOriginal		= None
	AudioCodecDefault		= Stream.AudioCodecAac
	AudioCodecAll			= [AudioCodecOriginal, Stream.AudioCodecPls, Stream.AudioCodecAc3, Stream.AudioCodecAac, Stream.AudioCodecMp3, Stream.AudioCodecFlac, Stream.AudioCodecVorbis, Stream.AudioCodecOpus, Stream.AudioCodecWma]
	AudioCodecCommon		= [Stream.AudioCodecAac, Stream.AudioCodecMp3, Stream.AudioCodecOpus, Stream.AudioCodecFlac, Stream.AudioCodecVorbis, Stream.AudioCodecWma] # Do not include AC3, otherwise it is always used, probably because the original video has this codec.
	AudioCodecType			= {
		Stream.AudioCodecPls	: 'eac3',
		Stream.AudioCodecAc3	: 'ac3',
		Stream.AudioCodecAac	: 'aac',
		Stream.AudioCodecMp3	: 'mp3',
		Stream.AudioCodecFlac	: 'flac',
		Stream.AudioCodecVorbis	: 'vorbis',
		Stream.AudioCodecOpus	: 'opus',
		Stream.AudioCodecWma	: 'wma',
	}

	DefaultHost			= '127.0.0.1'
	DefaultPort			= 8096
	DefaultEncryption	= False
	DefaultStream		= 'stream'

	# https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
	PortEncrypted	= [443, 8443, 8920]
	PortUnencrypted	= [80, 8008, 8080, 8096]

	###################################################################
	# CONSTRUCTOR
	###################################################################

	def __init__(self):
		self.mLock = Lock()
		self.mServers = []

	###################################################################
	# GENERAL
	###################################################################

	@classmethod
	def id(self):
		return self.Id

	@classmethod
	def name(self):
		return self.Name

	@classmethod
	def link(self):
		return self.Link

	@classmethod
	def website(self, open = False):
		link = Settings.getString('internal.link.%s' % self.id(), raw = True)
		if open: Networker.linkShow(link = link)
		return link

	@classmethod
	def settings(self):
		from lib.providers.core.manager import Manager
		Manager.settings(id = self.id())

	###################################################################
	# INTERNAL
	###################################################################

	def _lock(self):
		self.mLock.acquire()

	def _unlock(self):
		self.mLock.release()

	def _identifier(self):
		return Platform.identifier()

	def _execute(self, function, *arguments):
		threads = []
		arguments = list(arguments)
		for i in range(len(self.mServers)):
			args = Tools.copy(arguments)
			args.insert(0, i)
			threads.append(Pool.thread(target = function, args = args, start = True))
		[i.join() for i in threads]

	def _link(self, index, category = None, action = None, id = None, parameters = None, path = None):
		link = ''
		sever = self.mServers[index]
		if sever['server']['encryption']: link += 'https://'
		else: link += 'http://'
		try: host = Regex.extract(data = sever['server']['host'], expression = r'(^.*?\:\/\/)?([^\/:?#]+)(?:[\/:?#]|$)', group = 2)
		except: host = sever['server']['host']
		link += host + ':' + str(sever['server']['port'])
		if category:
			link = Networker.linkJoin(link, Center.Api, category)
			if id: link = Networker.linkJoin(link, str(id))
			if action: link = Networker.linkJoin(link, action)
		elif path:
			link = Networker.linkJoin(link, path)
		link = Networker.linkCreate(link = link, parameters = parameters)
		return link

	def _linkStream(self, index, info, item, mode = None, parameters = None):
		# Use the transcoded URL if the API returns it.
		# If no transcoded URL is returned, create one manually.
		# The advantage of using the returned transcoded URL is:
		#	1. Video and audio bitrate is automatically calculated from the global 'MaxStreamingBitrate'.
		#	2. Video and audio codec is automatically selected based on the container and which codec is supported.

		link = self._linkTypeTranscoded(index = index, info = info, mode = mode)
		if link: return link
		elif 'Path' in info and info['Path'] and Networker.linkIs(info['Path']): return info['Path']
		else: return self._linkStreamGenerate(index = index, idItem = item['id']['item'], idSource = item['id']['source'], idSession = item['id']['session'], container = item['file']['container'], mode = mode, parameters = parameters)

	def _linkTypeTranscoded(self, index, info, mode = None):
		if mode == Center.TypeTranscoded:
			if 'TranscodingUrl' in info:
				link = info['TranscodingUrl']
				if link:
					if not Networker.linkIs(link): link = self._link(index = index, path = link)
					return link
		return None

	def _linkStreamGenerate(self, index, idItem, idSource = None, idSession = None, container = None, mode = None, parameters = None):
		# https://github.com/MediaBrowser/Emby/wiki/Video-Streaming
		# https://swagger.emby.media/?staticview=true#/VideoService/getVideosByIdStream

		data = {}
		data['DeviceId'] = self._identifier()
		if idSource: data['MediaSourceId'] = idSource
		if idSession: data['PlaySessionId'] = idSession

		container = ''

		if mode == Center.TypeTranscoded:
			#https://xyz.com:443/videos/63e00884-6459-aa00-04b3-95582ac5e6ae/stream.mkv?DeviceId=XYZ&MediaSourceId=63e008846459aa0004b395582ac5e6ae&VideoCodec=h264,vp9,vp8,mpeg4,av1,theora,h265,vpx,wmv,h264&AudioCodec=aac,mp3,opus,flac,vorbis,wma&AudioStreamIndex=1&VideoBitrate=5709354&AudioBitrate=384000&MaxFramerate=23.976&MaxWidth=1280&PlaySessionId=XYZ&api_key=XYZ&SubtitleMethod=Encode&TranscodingMaxAudioChannels=2&RequireAvc=false&Tag=63f4163db38e99ed52dc7cd7d66a715f&h264-level=40&h264-videobitdepth=8&h264-profile=high&TranscodeReasons=ContainerBitrateExceedsLimit

			try: profile = parameters['DeviceProfile']['TranscodingProfiles'][0]
			except: profile = None

			data['TranscodeReasons'] = 'ContainerBitrateExceedsLimit'
			try: container = '.' + profile['Container'].lower()
			except: pass
			try: data['VideoBitrate'] = int(parameters['MaxStreamingBitrate'] * 0.92)
			except: pass
			try: data['MaxWidth'] = [i for i in profile['Conditions'] if i['Property'] == 'Width'][0]['Value']
			except: pass
			try: data['VideoCodec'] = profile['VideoCodec']
			except: pass
			try: data['AudioBitrate'] = int(parameters['MaxStreamingBitrate'] * 0.08)
			except: pass
			try: data['TranscodingMaxAudioChannels'] = profile['MaxAudioChannels']
			except: pass
			try: data['AudioCodec'] = profile['AudioCodec']
			except: pass
			try: data['AudioStreamIndex'] = parameters['AudioStreamIndex']
			except: pass
			try:
				data['SubtitleStreamIndex'] = parameters['SubtitleStreamIndex']
				data['SubtitleMethod'] = 'Encode'
			except: pass
		else:
			# This is important for the streaming the original file.
			# Otherwise Emby returns a stream that does not have chapters and Kodi hidess the Pause/Forward/Rewind buttons int he player.
			data['Static'] = 'true'

	 	# On Emby servers the stream links fail with:
		#	Access token is invalid or expired.
		# Adding the token as api_key to the link solves the problem.
		data['api_key'] = self.mServers[index]['authentication']['token']

		# Use the source ID in the link. The normal item ID also works, but some remote servers have pre-transcoded files that have the same item ID, but different source ID.
		return self._link(index = index, category = Center.CategoryVideos, action = Center.DefaultStream + container, id = idSource, parameters = data)

	def _request(self, index, method, category, action, id = None, parameters = None, authentication = True):
		link = self._link(index = index, category = category, action = action, id = id)
		headers = self._requestHeaders(index = index)

		if not parameters: parameters = {}

		# Adding UserId as a parameter seems only to be necessary in Jellyfin. Emby always worked without it, since the UserId is set in the headers.
		parameters['UserId'] = self.mServers[index]['authentication']['userid']

		# Important, otherwise the transcode parameters are ignored.
		if id: parameters['MediaSourceId'] = id

		networker = Networker()
		result = networker.request(method = method, type = None if parameters is None else Networker.DataJson, link = link, data = parameters, headers = headers)
		if result['error']['code'] == 401 and authentication: # Reauthenticate if token is expired or revoked.
			self._authenticate(index = index)
			return self._request(index = index, method = method, category = category, action = action, parameters = parameters, authentication = False)

		return networker.responseDataJson()

	def _requestHeaders(self, index):
		sever = self.mServers[index]
		version = System.versionKodi()
		device = System.name()
		identifier = self._identifier()
		userid = self.mServers[index]['authentication']['userid']
		token = self.mServers[index]['authentication']['token']
		return {'X-Emby-Authorization' : 'Emby UserId="%s", Client="Kodi", Device="%s", DeviceId="%s", Version="%s", Token="%s"' % (userid if userid else '', device, identifier, version, token if token else '')}

	def _authenticate(self, index, username = None, password = None):
		if username is None: username = self.mServers[index]['authentication']['username']
		if password is None: password = self.mServers[index]['authentication']['password']
		parameters = {
			'Username' : username,
			'Pw' : password,
			'Password' : Hash.sha1(password),
			'PasswordMd5' : Hash.md5(password),
		}
		result = self._request(index = index, method = Networker.MethodPost, category = Center.CategoryUsers, action = Center.ActionAuthenticate, parameters = parameters, authentication = False)
		try:
			token = result['AccessToken']
			userid = result['SessionInfo']['UserId']
			result = True
		except:
			token = None
			userid = None
			result = False
		self._lock()
		self.mServers[index]['authentication']['username'] = username
		self.mServers[index]['authentication']['password'] = password
		self.mServers[index]['authentication']['token'] = token
		self.mServers[index]['authentication']['userid'] = userid
		self._unlock()
		return result

	##############################################################################
	# LABEL
	##############################################################################

	def _labelTitle(self, value):
		return self.name() + ' ' + Translation.string(value)

	def _labelType(self, value):
		return Translation.string(32314 if Networker.linkIsLocal(value) else 35559)

	def _labelEncryption(self, value):
		return Translation.string(33341 if value else 33342)

	def _labelUsername(self, value):
		return value if value else Format.fontItalic(33112)

	def _labelPassword(self, value):
		return Format.FontPassword if value else Format.fontItalic(33112)

	def _labelOption(self, value, description, function, label1 = Stream.LabelShort, label2 = Stream.LabelLong, system = False):
		if value:
			stream = Stream()
			Tools.getFunction(stream, function + 'Set')(value, extract = False)
			getter = Tools.getFunction(stream, function)
			return getter(format = Stream.FormatBasic, label = label2 if description else label1)
		else:
			return 33820 if description else 33800

	def _labelStreamType(self, value, description = False):
		for i in Center.TypeAll:
			if i['value'] == value: return i['description' if description else 'label']
		return None

	def _labelFileBandwidth(self, value, description = False, label = False):
		if Tools.isInteger(value) and not label:
			return ConverterSpeed(value = value, unit = ConverterSpeed.Bit).stringOptimal(unit = ConverterSpeed.Bit, notation = ConverterSpeed.SpeedLetter, places = 0)
		else:
			for i in Center.FileBandwidthAll:
				if i['value'] == value: return i['description' if description else 'label']
		return 33800

	def _labelFileContainer(self, value, description = False):
		return self._labelOption(value = value, description = description, function = Stream.ParameterFileContainer, label1 = Stream.LabelShort, label2 = Stream.LabelMedium)

	def _labelVideoQuality(self, value, description = False):
		return self._labelOption(value = value, description = description, function = Stream.ParameterVideoQuality, label1 = Stream.LabelShort, label2 = Stream.LabelLong)

	def _labelVideoCodec(self, value, description = False):
		return self._labelOption(value = value, description = description, function = Stream.ParameterVideoCodec, label1 = Stream.LabelShort, label2 = Stream.LabelMedium)

	def _labelAudioChannels(self, value, description = False):
		return self._labelOption(value = value, description = description, function = Stream.ParameterAudioChannels, label1 = Stream.LabelMedium, label2 = Stream.LabelLong)

	def _labelAudioCodec(self, value, description = False):
		if value:
			stream = Stream()
			stream.audioCodecSet(value, extract = False)
			stream.audioSystemSet(value, extract = False)
			return stream.audioCodec(format = Stream.FormatBasic, label = Stream.LabelMedium if description else Stream.LabelShort, system = True)
		else:
			return 33820 if description else 33800

	def _labelLanguage(self, value):
		return Language.name(value)

	##############################################################################
	# SERVER
	##############################################################################

	def server(self, index = None, valid = None):
		if not index is None: return self.mServers[index]
		elif valid: return [i for i in self.mServers if i['authentication']['token']]
		else: return self.mServers

	def serverHas(self):
		return len(self.server()) > 0

	def serverValid(self):
		return len(self.server(valid = True)) > 0

	def serverInitialize(self, servers):
		if servers:
			if Tools.isDictionary(servers): servers = [servers]

			# In case the dictionary structure changes in the future and we want to use the settings still using the old structure.
			for i in range(len(servers)):
				data = self._serverCreate()
				Tools.update(data, servers[i])
				servers[i] = data

			self.mServers = servers

	def serverVerify(self, index = None, silent = True, confirm = False):
		if index is None:
			self._execute(self.serverVerify)
			count = sum(1 if i['authentication']['token'] else 0 for i in self.mServers)
			if count == 0: return False
			elif count == len(self.mServers): return True
			else: return None # Some of the servers work.
		else:
			if silent:
				return self._authenticate(index = index)
			else:
				Loader.show()
				success = self._authenticate(index = index)
				Loader.hide()
				title = self._labelTitle(33101)
				if success:
					Dialog.notification(title = title, message = 35462, icon = Dialog.IconSuccess, duplicates = True)
				else:
					Dialog.notification(title = title, message = 33218, icon = Dialog.IconError, duplicates = True)
					if confirm: Dialog.confirm(title = title, message = Translation.string(35578) % self.name())
				return success

	def serverSettings(self):
		def _serverItems():
			items = [
				{'title' : Dialog.prefixBack(35374), 'close' : True},
				{'title' : Dialog.prefixNext(33239), 'action' : self._serverHelp},
				{'title' : Dialog.prefixNext(35069), 'action' : self._serverAdd},
				'',
			]
			for i in range(len(self.mServers)):
				server = self.mServers[i]
				items.append({'title' : '%s %d' % (Translation.string(35553), i + 1), 'value' : '%s (%s)' % (server['server']['host'], self._labelType(server['server']['host'])), 'action' : self._server, 'parameters' : {'index' : i}})
			return items
		Dialog.information(title = self._labelTitle(35552), items = _serverItems(), refresh = _serverItems, reselect = Dialog.ReselectYes)
		return self.mServers

	def _serverHelp(self):
		name = self.name()
		items = [
			{'type' : 'text', 'value' : '%s is a locally or remotely hosted media server designed to organize, play, and stream audio and video to a variety of devices. The media server can be used in a browser or through an app, but can also be accessed through an API. %s typically requires a premium membership, since files are hosted on private servers.' % (name, name), 'break' : 2},

			{'type' : 'title', 'value' : 'Server', 'break' : 2},
			{'type' : 'text', 'value' : 'One or more %s servers can be specified. All servers are scanned for content.' % name, 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Host', 'value' : 'The IP address or domain, including any subdomains, of the %s server.' % name},
				{'title' : 'Port', 'value' : 'The port %s runs on. For locally hosted servers the port is typically 8096. For remote servers the port is typically 80 or 8096 if running over HTTP, or 443 or 8920 if running over HTTPS.' % name},
				{'title' : 'Encryption', 'value' : 'Whether or not to encrypt the connection to the server running over SSL or TLS. Remote servers running over HTTPS, typically with port 443 or 8920, use encryption. Servers running over HTTP, typically with port 80 or 8096, do not use encryption. Local servers typically do not use encryption.'},
			]},

			{'type' : 'title', 'value' : 'Authentication', 'break' : 2},
			{'type' : 'text', 'value' : 'Most %s servers require authentication.' % name, 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Username', 'value' : 'Your %s username.' % name},
				{'title' : 'Password', 'value' : 'Your %s password.' % name},
			]},

			{'type' : 'title', 'value' : 'Streaming', 'break' : 2},
			{'type' : 'text', 'value' : '%s servers allow you to access the original file, or to use a transcoded or converted version of the file. Transcoding is useful if you want to stream a lower quality file, such as when your internet connection is too slow to stream the original file. Note that transcoding requires %s to convert the file, which puts a heavy processing load on the server. You should therefore only use the transcoded file if absolutely necessary. Also note that %s might need some time to initiate the transcoding process. Playback in Kodi might timeout before the server starts replying with data. If playback of transcoded streams does not start, try to start playback again after failure. Alternatively, you can reduce the %s transcoding parameters to output a lower quality, since lower quality conversion is faster. A decent configuration to start with is a [I]MKV[/I], [I]WEBM[/I], or [I]TS[/I]  container with [I]10 mbps[/I]  or lower bandwidth, [I]H265[/I]  video codec, [I]2CH[/I]  audio encoded with [I]AAC[/I]. If all else fails, just stream the original file.' % (name, name, name, name), 'break' : 2},
			{'type' : 'text', 'value' : 'Transcoding can be configured in a number of ways. Note that these parameters are only a best attempt or maximum value, and the %s server might change or ignore certain parameters.' % name, 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Stream Type', 'value' : 'Include the original, transcoded, or both streams in the results. Note that transcoding only starts when you initiate playback. Just including the transcoded stream in the results does not start transcoding and does not put any extra load on the server.'},
				{'title' : 'File Bandwidth', 'value' : 'The maximum bandwidth that streaming should consume. This should be lower than your internet connection speed if you want to avoid buffering. The [I]Automatic[/I]  option will use your previous internet speed test and the original file size to determine the optimal streaming bandwidth.'},
				{'title' : 'File Container', 'value' : 'The file container the stream will be delivered in. Note that containers do not always support all video and audio codecs, and the server might change the codec if necessary. [I]MKV[/I], [I]WEBM[/I], or [I]TS[/I]  is recommended.'},
				{'title' : 'Video Quality', 'value' : 'The resolution of the video. Note that this is only the maximum allowed resolution and the server might return a lower resolution if necessary. By default, the resolution of the original file is used.'},
				{'title' : 'Video Codec', 'value' : 'The codec of the video. Note that some servers and containers might not support all codecs. Newer codecs might also require more processing power on the server and require longer waiting times before playback starts. Some codecs might also cause transcoding to fail on some servers. [I]H264[/I], [I]VP9[/I], or [I]VP8[/I]  is recommended.'},
				{'title' : 'Audio Channels', 'value' : 'The maximum number of audio channels. Note that this is the maximum and fewer channels might be returned. [I]2CH[/I]  is recommended.'},
				{'title' : 'Audio Codec', 'value' : 'The codec of the audio. Note that some servers and containers might not support all codecs. Newer codecs might also require more processing power on the server and require longer waiting times before playback starts. Some codecs might also cause transcoding to fail on some servers. [I]AAC[/I], [I]MP3[/I], or [I]Vorbis[/I]  is recommended.'},
				{'title' : 'Audio Language', 'value' : 'The audio language to use if available, otherwise English or the default language is selected. The [I]Automatic[/I]  option will use the audio language specified under the [I]Playback[/I]  settings section. If that is also set to [I]Automatic[/I], the language specified under the [I]General[/I]  settings section is used instead. Alternatively, a specific language can be used.'},
				{'title' : 'Subtitle Language', 'value' : 'The subtitle language to use if available, otherwise English or the default language is selected. The [I]Automatic[/I]  option will use the subtitle language specified under the [I]Playback[/I]  settings section. If that is also set to [I]Automatic[/I], the language specified under the [I]General[/I]  settings section is used instead. Alternatively, a specific language can be used. Note that subtitles are hardcoded during transcoding. Set the language to [I]None[/I]  if you do not want any subtitles.'},
			]},
		]
		Dialog.details(title = name, items = items)

	def _serverCreate(self, host = None, port = None, encryption = None, mode = None, username = None, password = None, userid = None, token = None):
		return {
			'server' : {
				'host' : Center.DefaultHost if host is None else host,
				'port' : Center.DefaultPort if port is None else port,
				'encryption' : Center.DefaultEncryption if encryption is None else encryption,
			},
			'authentication' : {
				'username' : '' if username is None else username,
				'password' : '' if password is None else password,
				'userid' : '' if userid is None else userid,
				'token' : '' if token is None else token,
			},
			'stream' : {
				'type' : Center.TypeDefault if mode is None else mode,
				'file' : {
					'bandwidth' : Center.FileBandwidthDefault,
					'container' : Center.FileContainerDefault,
				},
				'video' : {
					'quality' : Center.VideoQualityDefault,
					'codec' : Center.VideoCodecDefault,
				},
				'audio' : {
					'channels' : Center.AudioChannelsDefault,
					'codec' : Center.AudioCodecDefault,
					'language' : Language.CodeAutomatic,
				},
				'subtitle' : {
					'language' : Language.CodeAutomatic,
				},
			},
		}

	def _serverAdd(self):
		self.mServers.append(self._serverCreate())
		self._server(index = len(self.mServers) - 1, verify = True)

	def _serverRemove(self, index):
		del self.mServers[index]

	def _serverHost(self, index):
		host = Dialog.input(title = self._labelTitle(35556), default = self.mServers[index]['server']['host'], type = Dialog.InputAlphabetic)
		if not host is None:
			if not host: host = Center.DefaultHost

			if Networker.linkIsLocal(host):
				self.mServers[index]['server']['port'] = Center.DefaultPort
				self.mServers[index]['server']['encryption'] = False
			elif Networker.linkIs(host):
				scheme = Networker.linkScheme(host)
				port = Networker.linkPort(host)
				encryption = None
				if port:
					if port in Center.PortEncrypted: encryption = True
					elif port in Center.PortUnencrypted: encryption = False

				host = Networker.linkDomain(host, subdomain = True, topdomain = True, ip = True, scheme = False, port = False)

				if Networker.linkIsLocal(host):
					self.mServers[index]['server']['port'] = port if port else Center.DefaultPort
					self.mServers[index]['server']['encryption'] = False if encryption is None else encryption
				elif scheme:
					scheme = scheme.lower()
					if scheme in ['https', 'ftps']:
						self.mServers[index]['server']['port'] = port if port else 443
						self.mServers[index]['server']['encryption'] = True if encryption is None else encryption
					elif scheme in ['http', 'ftp']:
						self.mServers[index]['server']['port'] = port if port else 80
						self.mServers[index]['server']['encryption'] = False if encryption is None else encryption

			self.mServers[index]['server']['host'] = host

	def _serverPort(self, index):
		port = Dialog.input(title = self._labelTitle(35557), default = self.mServers[index]['server']['port'], type = Dialog.InputNumeric)
		if not port is None:
			if port <= 0: port = Center.DefaultPort
			port = int(port)

			if port in Center.PortEncrypted: self.mServers[index]['server']['encryption'] = True
			elif port in Center.PortUnencrypted: self.mServers[index]['server']['encryption'] = False

			self.mServers[index]['server']['port'] = port

	def _serverEncryption(self, index):
		encryption = Dialog.option(title = self._labelTitle(35558), message = 35574)
		if not encryption is None: self.mServers[index]['server']['encryption'] = encryption

	def _serverUsername(self, index):
		username = Dialog.input(title = self._labelTitle(33267), default = self.mServers[index]['authentication']['username'], type = Dialog.InputAlphabetic)
		if not username is None: self.mServers[index]['authentication']['username'] = username

	def _serverPassword(self, index):
		password = Dialog.input(title = self._labelTitle(32307), default = self.mServers[index]['authentication']['password'], type = Dialog.InputAlphabetic)
		if not password is None: self.mServers[index]['authentication']['password'] = password

	def _serverOptions(self, index, title, level1, level2, label, values, default):
		items = [{'title' : Dialog.prefixBack(35374), 'close' : True}, {'title' : Dialog.prefixNext(33239), 'action' : self._serverHelp}, {'title' : Dialog.prefixNext(33564)}, '',]

		offset = len(items)
		selection = None
		for i in range(len(values)):
			value = values[i]
			if Tools.isDictionary(value): value = value['value']
			if level2:
				if value == self.mServers[index]['stream'][level1][level2]: selection = offset + i
			else:
				if value == self.mServers[index]['stream'][level1]: selection = offset + i
			items.append({'title' : label(value), 'value' : label(value, description = True)})

		choice = Dialog.information(title = self._labelTitle(title), items = items, selection = selection)

		if choice and choice >= 0:
			if choice == 1:
				value = default
			elif choice >= offset:
				value = values[choice - offset]
				if Tools.isDictionary(value): value = value['value']

			if level2: self.mServers[index]['stream'][level1][level2] = value
			else: self.mServers[index]['stream'][level1] = value

	def _serverLanguage(self, index, type, title):
		language = Language.settingsSelect(title = self._labelTitle(title), automatic = True, none = True, current = self.mServers[index]['stream'][type]['language'], update = False, result = Language.Code)
		if language: self.mServers[index]['stream'][type]['language'] = language

	def _serverStreamType(self, index):
		return self._serverOptions(index = index, title = 33492, level1 = 'type', level2 = None, label = self._labelStreamType, values = Center.TypeAll, default = Center.TypeDefault)

	def _serverFileBandwidth(self, index):
		items = [{'title' : Dialog.prefixBack(35374), 'close' : True}, {'title' : Dialog.prefixNext(33239), 'action' : self._serverHelp}, {'title' : Dialog.prefixNext(33564)}, '',]

		offset = len(items)
		selection = None
		for i in range(len(Center.FileBandwidthAll)):
			value = Center.FileBandwidthAll[i]
			if Tools.isDictionary(value): value = value['value']
			if value == self.mServers[index]['stream']['file']['bandwidth']: selection = offset + i
			items.append({'title' : self._labelFileBandwidth(value, label = True), 'value' : self._labelFileBandwidth(value, description = True)})

		choice = Dialog.information(title = self._labelTitle(33133), items = items, selection = selection)

		if choice == 1:
			value = Center.FileBandwidthDefault
		elif choice >= offset:
			if choice == 4:
				value = Dialog.input(title = self._labelTitle(33133), type = Dialog.InputNumeric)
				value = ConverterSpeed(value = value, unit = ConverterSpeed.BitMega).value(unit = ConverterSpeed.Bit)
			else:
				value = Center.FileBandwidthAll[choice - offset]
				if Tools.isDictionary(value): value = value['value']

		self.mServers[index]['stream']['file']['bandwidth'] = value

	def _serverFileContainer(self, index):
		return self._serverOptions(index = index, title = 35727, level1 = 'file', level2 = 'container', label = self._labelFileContainer, values = Center.FileContainerAll, default = Center.FileContainerDefault)

	def _serverVideoQuality(self, index):
		return self._serverOptions(index = index, title = 33889, level1 = 'video', level2 = 'quality', label = self._labelVideoQuality, values = Center.VideoQualityAll, default = Center.VideoQualityDefault)

	def _serverVideoCodec(self, index):
		return self._serverOptions(index = index, title = 33127, level1 = 'video', level2 = 'codec', label = self._labelVideoCodec, values = Center.VideoCodecAll, default = Center.VideoCodecDefault)

	def _serverAudioChannels(self, index):
		return self._serverOptions(index = index, title = 33129, level1 = 'audio', level2 = 'channels', label = self._labelAudioChannels, values = Center.AudioChannelsAll, default = Center.AudioChannelsDefault)

	def _serverAudioCodec(self, index):
		return self._serverOptions(index = index, title = 33130, level1 = 'audio', level2 = 'codec', label = self._labelAudioCodec, values = Center.AudioCodecAll, default = Center.AudioCodecDefault)

	def _serverAudioLanguage(self, index):
		return self._serverLanguage(index = index, type = 'audio', title = 35038)

	def _serverSubtitleLanguage(self, index):
		return self._serverLanguage(index = index, type = 'subtitle', title = 35722)

	def _server(self, index, verify = False):
		def _serverItems(index):
			server = self.mServers[index]

			stream = [{'title' : 33492, 'value' : self._labelStreamType(server['stream']['type']), 'action' : self._serverStreamType, 'parameters' : {'index' : index}}]
			if server['stream']['type'] in [Center.TypeBoth, Center.TypeTranscoded]:
				stream.extend([
					{'title' : 33133, 'value' : self._labelFileBandwidth(server['stream']['file']['bandwidth']), 'action' : self._serverFileBandwidth, 'parameters' : {'index' : index}},
					{'title' : 35727, 'value' : self._labelFileContainer(server['stream']['file']['container']), 'action' : self._serverFileContainer, 'parameters' : {'index' : index}},
					{'title' : 33889, 'value' : self._labelVideoQuality(server['stream']['video']['quality']), 'action' : self._serverVideoQuality, 'parameters' : {'index' : index}},
					{'title' : 33127, 'value' : self._labelVideoCodec(server['stream']['video']['codec']), 'action' : self._serverVideoCodec, 'parameters' : {'index' : index}},
					{'title' : 33129, 'value' : self._labelAudioChannels(server['stream']['audio']['channels']), 'action' : self._serverAudioChannels, 'parameters' : {'index' : index}},
					{'title' : 33130, 'value' : self._labelAudioCodec(server['stream']['audio']['codec']), 'action' : self._serverAudioCodec, 'parameters' : {'index' : index}},
					{'title' : 35038, 'value' : self._labelLanguage(server['stream']['audio']['language']), 'action' : self._serverAudioLanguage, 'parameters' : {'index' : index}},
					{'title' : 35722, 'value' : self._labelLanguage(server['stream']['subtitle']['language']), 'action' : self._serverSubtitleLanguage, 'parameters' : {'index' : index}},
				])

			return [
				{'title' : Dialog.prefixBack(35374), 'close' : True},
				{'title' : Dialog.prefixNext(33239), 'action' : self._serverHelp},
				{'title' : Dialog.prefixNext(35406), 'action' : self._serverRemove, 'parameters' : {'index' : index}, 'close' : True, 'return' : False},
				{'title' : Dialog.prefixNext(33219), 'action' : self.serverVerify, 'parameters' : {'index' : index, 'silent' : False}},
				{'title' : 35553, 'items' : [
					{'title' : 35556, 'value' : server['server']['host'], 'action' : self._serverHost, 'parameters' : {'index' : index}},
					{'title' : 35557, 'value' : str(server['server']['port']), 'action' : self._serverPort, 'parameters' : {'index' : index}},
					{'title' : 35558, 'value' : self._labelEncryption(server['server']['encryption']), 'action' : self._serverEncryption, 'parameters' : {'index' : index}},
				]},
				{'title' : 33101, 'items' : [
					{'title' : 33267, 'value' : self._labelUsername(server['authentication']['username']), 'action' : self._serverUsername, 'parameters' : {'index' : index}},
					{'title' : 32307, 'value' : self._labelPassword(server['authentication']['password']), 'action' : self._serverPassword, 'parameters' : {'index' : index}},
				]},
				{'title' : 33487, 'items' : stream},
			]

		before = Tools.copy(self.mServers[index])
		result = Dialog.information(title = self._labelTitle(35553), items = _serverItems(index = index), refresh = lambda : _serverItems(index = index), reselect = Dialog.ReselectYes)
		if not result is False:
			# Do not verify if only the stream settings changed.
			after = Tools.copy(self.mServers[index])
			del before['stream']
			del after['stream']

			# If the user did not change the settings (eg: right after the authentication failure dialog was shown), do not verify again.
			# Assume that the user wants to keep thesse invalid settings (eg: to check the details on the website and then edit them here).
			if verify or not before == after:
				if not self.serverVerify(index = index, silent = False, confirm = True):
					self._server(index = index)

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media, title, year = None, numberSeason = None, numberEpisode = None, exact = False):
		self.mResults = []
		self._execute(self._search, media, title, year, numberSeason, numberEpisode, exact)

		# Emby can return multiple item IDs, but all items have the same source ID.
		# Seems to be episodes that can be listed multiple times (show, season, episode, etc).
		ids = []
		results = []
		for i in self.mResults:
			id = i['id']['source'] + str(i['stream']['type'])
			if not id in ids:
				ids.append(id)
				results.append(i)

		return results

	def _search(self, index, media, title, year, numberSeason, numberEpisode, exact):
		try:
			serie = None
			if exact:
				type = 'Movie,Series,Episode'
			else:
				# Do not search by "Episode" type, since it searches the episode title and not the series title.
				serie = Media.isSerie(media)
				type = 'Series' if serie else 'Movie'

			if not Tools.isArray(title): title = [title] if title else []
			if not Tools.isArray(year): year = [year] if year else []

			items = []
			threads = [Pool.thread(target = self._searchHints, args = (index, type, i, items), start = True) for i in title]
			[thread.join() for thread in threads]
			items = Tools.listUnique(items)

			# Returns other titles for "The Gentelmen (2019)", eg: "The League of Extraordinary Gentlemen" and "Ladies and Gentelmen, The Fabulous Stain".
			if not exact: items = [i for i in items if Stream.titleValid(data = i['Name'], media = media, title = title)]

			threads = []
			threads.extend([Pool.thread(target = self._searchEpisodes, args = (index, i['Id'], numberSeason, numberEpisode, exact), start = True) for i in items if i['Type'] == 'Series'])
			items = [i for i in items if not i['Type'] == 'Series']

			if not exact:
				if serie: items = [i for i in items if (not 'ParentIndexNumber' in i or i['ParentIndexNumber'] == numberSeason) and (not 'IndexNumber' in i or i['IndexNumber'] == numberEpisode)]
				else: items = [i for i in items if not 'ProductionYear' in i or i['ProductionYear'] in year] # Some do not have a ProductionYear entry.

			threads.extend([Pool.thread(target = self._searchInfo, args = (index, i), start = True) for i in items])
			[thread.join() for thread in threads]
		except: Logger.error()

	def _searchHints(self, index, type, title, result):
		items = self._request(index = index, method = Networker.MethodGet, category = Center.CategorySearch, action = Center.ActionHints, parameters = {'SearchTerm' : title, 'IncludeItemTypes' : type})
		if items:
			items = items['SearchHints']
			if items: result.extend(items)

	def _searchParameters(self, fileBandwidth = None, fileContainer = None, videoQuality = None, videoCodec = None, audioChannels = None, audioCodec = None, audioIndex = None, subtitleIndex = None, subtitleProfile = False):
		'''
		{"DeviceProfile":{"MaxStreamingBitrate":120000000,"MaxStaticBitrate":100000000,"MusicStreamingTranscodingBitrate":384000,"DirectPlayProfiles":[{"Container":"webm","Type":"Video","VideoCodec":"vp8,vp9,av1","AudioCodec":"vorbis,opus"},{"Container":"mp4,m4v","Type":"Video","VideoCodec":"h264,vp8,vp9,av1","AudioCodec":"aac,mp3,opus,flac,vorbis"},{"Container":"mov","Type":"Video","VideoCodec":"h264","AudioCodec":"aac,mp3,opus,flac,vorbis"},{"Container":"opus","Type":"Audio"},{"Container":"webm","AudioCodec":"opus","Type":"Audio"},{"Container":"mp3","Type":"Audio"},{"Container":"aac","Type":"Audio"},{"Container":"m4a","AudioCodec":"aac","Type":"Audio"},{"Container":"m4b","AudioCodec":"aac","Type":"Audio"},{"Container":"flac","Type":"Audio"},{"Container":"webma","Type":"Audio"},{"Container":"webm","AudioCodec":"webma","Type":"Audio"},{"Container":"wav","Type":"Audio"},{"Container":"ogg","Type":"Audio"}],"TranscodingProfiles":[{"Container":"ts","Type":"Audio","AudioCodec":"aac","Context":"Streaming","Protocol":"hls","MaxAudioChannels":"2","MinSegments":"1","BreakOnNonKeyFrames":true},{"Container":"aac","Type":"Audio","AudioCodec":"aac","Context":"Streaming","Protocol":"http","MaxAudioChannels":"2"},{"Container":"mp3","Type":"Audio","AudioCodec":"mp3","Context":"Streaming","Protocol":"http","MaxAudioChannels":"2"},{"Container":"opus","Type":"Audio","AudioCodec":"opus","Context":"Streaming","Protocol":"http","MaxAudioChannels":"2"},{"Container":"wav","Type":"Audio","AudioCodec":"wav","Context":"Streaming","Protocol":"http","MaxAudioChannels":"2"},{"Container":"opus","Type":"Audio","AudioCodec":"opus","Context":"Static","Protocol":"http","MaxAudioChannels":"2"},{"Container":"mp3","Type":"Audio","AudioCodec":"mp3","Context":"Static","Protocol":"http","MaxAudioChannels":"2"},{"Container":"aac","Type":"Audio","AudioCodec":"aac","Context":"Static","Protocol":"http","MaxAudioChannels":"2"},{"Container":"wav","Type":"Audio","AudioCodec":"wav","Context":"Static","Protocol":"http","MaxAudioChannels":"2"},{"Container":"ts","Type":"Video","AudioCodec":"aac,mp3","VideoCodec":"h264","Context":"Streaming","Protocol":"hls","MaxAudioChannels":"2","MinSegments":"1","BreakOnNonKeyFrames":true},{"Container":"webm","Type":"Video","AudioCodec":"vorbis,opus","VideoCodec":"vp8,vp9,av1,vpx","Context":"Streaming","Protocol":"http","MaxAudioChannels":"2"},{"Container":"mp4","Type":"Video","AudioCodec":"aac,mp3,opus,flac,vorbis","VideoCodec":"h264","Context":"Static","Protocol":"http"}],"ContainerProfiles":[],"CodecProfiles":[{"Type":"VideoAudio","Codec":"aac","Conditions":[{"Condition":"Equals","Property":"IsSecondaryAudio","Value":"false","IsRequired":false}]},{"Type":"VideoAudio","Conditions":[{"Condition":"Equals","Property":"IsSecondaryAudio","Value":"false","IsRequired":false}]},{"Type":"Video","Codec":"h264","Conditions":[{"Condition":"NotEquals","Property":"IsAnamorphic","Value":"true","IsRequired":false},{"Condition":"EqualsAny","Property":"VideoProfile","Value":"high|main|baseline|constrained baseline|high 10","IsRequired":false},{"Condition":"EqualsAny","Property":"VideoRangeType","Value":"SDR","IsRequired":false},{"Condition":"LessThanEqual","Property":"VideoLevel","Value":"52","IsRequired":false},{"Condition":"NotEquals","Property":"IsInterlaced","Value":"true","IsRequired":false}]},{"Type":"Video","Codec":"hevc","Conditions":[{"Condition":"NotEquals","Property":"IsAnamorphic","Value":"true","IsRequired":false},{"Condition":"EqualsAny","Property":"VideoProfile","Value":"main","IsRequired":false},{"Condition":"EqualsAny","Property":"VideoRangeType","Value":"SDR","IsRequired":false},{"Condition":"LessThanEqual","Property":"VideoLevel","Value":"120","IsRequired":false},{"Condition":"NotEquals","Property":"IsInterlaced","Value":"true","IsRequired":false}]},{"Type":"Video","Codec":"vp9","Conditions":[{"Condition":"EqualsAny","Property":"VideoRangeType","Value":"SDR|HDR10|HLG","IsRequired":false}]},{"Type":"Video","Codec":"av1","Conditions":[{"Condition":"EqualsAny","Property":"VideoRangeType","Value":"SDR|HDR10|HLG","IsRequired":false}]}],"SubtitleProfiles":[{"Format":"vtt","Method":"External"},{"Format":"ass","Method":"External"},{"Format":"ssa","Method":"External"}],"ResponseProfiles":[{"Type":"Video","Container":"m4v","MimeType":"video/mp4"}]}}
		'''

		# NB: If these values are changed, make sure _linkStreamGenerate() is also updated.

		result = {}
		parameters = {
			'Type' : 'Video',
			'Context' : 'Streaming',

			'Container' : Center.FileContainerType[fileContainer],

			# HLS requires manually stopping encoding after playback: https://github.com/MediaBrowser/Emby/wiki/Http-Live-Streaming
			# HLS might also cause a heavy server load.
			'Protocol' : 'http',
		}

		if fileBandwidth: result['MaxStreamingBitrate'] = fileBandwidth

		if videoQuality:
			resolution = Stream.videoResolutionConvert(quality = videoQuality)
			if resolution:
				parameters['Conditions'] = [
					{
						'Condition' : 'LessThanEqual',
						'Property' : 'Width',
						'IsRequired' : False,
						'Value' : resolution[Stream.VideoWidth],
					}
				]

		if videoCodec:
			videoCodecs = Tools.copy(Center.VideoCodecOrder)
			videoCodecs.remove(videoCodec)
			videoCodecs.insert(0, videoCodec)
			videoCodecs = [Center.VideoCodecType[i] for i in videoCodecs]
			parameters['VideoCodec'] = ','.join(videoCodecs)

		if audioChannels: parameters['MaxAudioChannels'] = audioChannels

		if audioCodec:
			audioCodecs = Tools.copy(Center.AudioCodecCommon)
			audioCodecs.remove(audioCodec)
			audioCodecs.insert(0, audioCodec)
			audioCodecs = [Center.AudioCodecType[i] for i in audioCodecs]
			parameters['AudioCodec'] = ','.join(audioCodecs)

		result['AudioStreamIndex'] = -1 if audioIndex is None else audioIndex

		result['SubtitleStreamIndex'] = -1 if subtitleIndex is None else subtitleIndex

		result['DeviceProfile'] = {'TranscodingProfiles' : [parameters]}

		if subtitleProfile:
			result['DeviceProfile']['SubtitleProfiles']= [
				{'Format' : 'vtt',		'Method' : 'Hls'},
				{'Format' : 'eia_608',	'Method' : 'VideoSideData',	'Protocol' : 'hls'},
				{'Format' : 'eia_708',	'Method' : 'VideoSideData',	'Protocol' : 'hls'},
				{'Format' : 'vtt',		'Method' : 'External'},
				{'Format' : 'ass',		'Method' : 'External'},
				{'Format' : 'ssa',		'Method' : 'External'},
			]

		return result

	def _searchInfo(self, index, item):
		try:
			from lib.modules.speedtest import SpeedTester
			from lib.modules.player import Audio, Subtitle

			host = self.mServers[index]['server']['host']
			source = 'localhost' if Networker.linkIsLocal(host) else Networker.linkDomain(host, subdomain = False, topdomain = False)

			streamType = self.mServers[index]['stream']['type']
			fileBandwidth = self.mServers[index]['stream']['file']['bandwidth']
			fileContainer = self.mServers[index]['stream']['file']['container']
			videoQuality = self.mServers[index]['stream']['video']['quality']
			videoCodec = self.mServers[index]['stream']['video']['codec']
			audioChannels = self.mServers[index]['stream']['audio']['channels']
			audioCodec = self.mServers[index]['stream']['audio']['codec']

			audioLanguage = self.mServers[index]['stream']['audio']['language']
			if audioLanguage == Language.CodeNone: audioLanguage = None
			else:
				if audioLanguage == Language.CodeAutomatic: audioLanguage = Audio.settingsLanguage(code = Language.CodePrimary)
				else: audioLanguage = [audioLanguage]
				if not Language.EnglishCode in audioLanguage: audioLanguage.append(Language.EnglishCode)

			subtitleLanguage = self.mServers[index]['stream']['subtitle']['language']
			if subtitleLanguage == Language.CodeNone: subtitleLanguage = None
			else:
				if subtitleLanguage == Language.CodeAutomatic: subtitleLanguage = Subtitle.settingsLanguage(code = Language.CodePrimary)
				else: subtitleLanguage = [subtitleLanguage]
				if not Language.EnglishCode in subtitleLanguage: subtitleLanguage.append(Language.EnglishCode)

			# Jellyfin allows this request to be GET or POST, but Emby only allows GET.
			infos = self._request(index = index, method = Networker.MethodGet, category = Center.CategoryItems, action = Center.ActionInfo, id = item['Id'])

			if infos:
				try: session = infos['PlaySessionId']
				except: session = None
				infos = infos['MediaSources']

				for position in range(len(infos)):
					try:
						info = infos[position]
						try: streams = info['MediaStreams']
						except: streams = []

						entry = {
							'id' :
							{
								'item' : item['Id'],
								'source' : None,
								'session' : session,
							},
							'stream' : {
								'type' : None,
								'link' : None,
								'server' : host,
								'source' : source,
							},
							'file' : {
								'name' : None,
								'description' : None,
								'size' : None,
								'container' : None,
							},
							'video' : {
								'quality' : None,
								'width' : None,
								'height' : None,
								'codec' : None,
								'range' : None,
								'depth' : None,
								'bitrate' : None,
								'framerate' : None,
								'3d' : None,
							},
							'audio' : {
								'language' : None,
								'channels' : None,
								'codec' : None,
								'bitrate' : None,
								'samplerate' : None,
							},
							'subtitle' : {
								'type' : None,
								'language' : None,
								'codec' : None,
							},
						}

						try: entry['id']['source'] = info['Id']
						except: pass

						title = None
						titleShow = None
						year = None
						season = None
						episode = None
						try: title = item['Name']
						except: pass
						try: titleShow = item['SeriesName']
						except: pass
						try: year = item['ProductionYear']
						except: pass
						try: season = item['ParentIndexNumber']
						except: pass
						try: episode = item['IndexNumber']
						except: pass

						description = []
						try: description.append(Title.titleUniversal(title = titleShow if titleShow else title, year = year, season = season, episode = episode))
						except: pass
						try: description.append(title if titleShow and not titleShow == title else None)
						except: pass
						try: description.append(info['Name'])
						except: pass
						try: entry['file']['description'] = ' | '.join([i for i in description if i])
						except: pass

						try:
							try: name = info['Name']
							except: name = None

							# On some servers the 'Name' attribute is correct.
							# On other servers, the 'Name' attribute is often partial and not the entire file name.
							#	"Name": "[WEBDL-1080p][AC3 5.1][h264]"
							#	"Path": "/mnt/SAN/Media/Movies/Spanish/Avatar (2009) [imdb-tt0499549][tmdb-19995]/Avatar (2009) [imdb-tt0499549][tmdb-19995][WEBDL-1080p][AC3 5.1][h264].mkv"
							# If possible, manually extract the file name from the path.
							if 'Path' in info and info['Path']:
								nameNew = File.name(path = info['Path'], extension = True)
								if nameNew and (not name or len(nameNew) > len(name)): name = nameNew

							entry['file']['name'] = name
						except: pass
						try: entry['file']['size'] = info['Size'] # STRM files do not have a size.
						except: pass
						try: entry['file']['container'] = info['Container']
						except: pass

						video = [i for i in streams if i['Type'] == 'Video']
						if len(video) > 0:
							if len(video) > 1:
								try: video = [i for i in video if i['IsDefault']][0]
								except: pass
							if Tools.isArray(video): video = video[0]
							try: entry['video']['quality'] = Stream.videoResolutionConvert(width = video['Width'], height = video['Height'])
							except: pass
							try: entry['video']['width'] = video['Width']
							except: pass
							try: entry['video']['height'] = video['Height']
							except: pass
							try: entry['video']['codec'] = video['Codec']
							except: pass
							try: entry['video']['range'] = ' - '.join([i for i in Tools.listUnique([video['VideoRange'] if 'VideoRange' in video else None, video['VideoRangeType'] if 'VideoRangeType' in video else None]) if i])
							except: pass
							try: entry['video']['depth'] = video['BitDepth']
							except: pass
							try: entry['video']['bitrate'] = video['BitRate']
							except: pass
							try: entry['video']['framerate'] = video['RealFrameRate']
							except: pass
						try: entry['video']['3d'] = bool(video['Video3DFormat'])
						except: entry['video']['3d'] = False

						audio = [i for i in streams if i['Type'] == 'Audio']
						audioDefault = None
						if len(audio) > 0:
							try:
								# Checking for IsExternal is mostly for subtitles, but also use here, in case there are external audio files.
								if audioLanguage:
									for i in audioLanguage:
										for j in [False, True]:
											for k in audio:
												if not 'IsExternal' in k or k['IsExternal'] is j:
													language = Language.code(k['Language'])
													if i == language:
														audioDefault = {'index' : k['Index'], 'language' : language}
														break
											if audioDefault: break
										if audioDefault: break
							except: pass
							try: entry['audio']['language'] = list(set([Language.code(i['Language']) for i in audio]))
							except: pass
							if len(audio) > 1:
								try:
									# Pick  the one with the highet number of channels, because the default audio is sometimes only 2CH in some other language.
									channels = max([i['Channels'] for i in audio])
									audio2 = [i for i in audio if i['Channels'] == channels]
									try: audio = [i for i in audio2 if i['IsDefault']][0]
									except: audio = audio2[0]
								except: pass
							if Tools.isArray(audio): audio = audio[0]
							try: entry['audio']['channels'] = audio['Channels']
							except: pass
							try: entry['audio']['codec'] = ' - '.join([i for i in Tools.listUnique([audio['Codec'] if 'Codec' in audio else None, audio['Profile'] if 'Profile' in audio else None]) if i])
							except: pass
							try: entry['audio']['bitrate'] = audio['BitRate']
							except: pass
							try: entry['audio']['samplerate'] = audio['SampleRate']
							except: pass

						subtitle = [i for i in streams if i['Type'] == 'Subtitle']
						subtitleDefault = None
						if len(subtitle) > 0:
							try:
								# When using external subtitles, they mostly fail, probably because the SRT file is not on the server.
								# Try first internal subtitles, and only use external subtitles if internal oness do not exist.
								if subtitleLanguage:
									for i in subtitleLanguage:
										for j in [False, True]:
											for k in subtitle:
												if not 'IsExternal' in k or k['IsExternal'] is j:
													language = Language.code(k['Language'])
													if i == language:
														subtitleDefault = {'index' : k['Index'], 'language' : language}
														break
											if subtitleDefault: break
										if subtitleDefault: break
							except: pass
							try: entry['subtitle']['language'] = list(set([Language.code(i['Language']) for i in subtitle]))
							except: pass
							if len(subtitle) > 1:
								try: subtitle = [i for i in subtitle if i['IsDefault']][0]
								except: pass
							else:
								subtitle = subtitle[0]
							try: entry['subtitle']['codec'] = subtitle['Codec']
							except: pass
							if entry['subtitle']['language']: entry['subtitle']['type'] = Stream.SubtitleTypeSoft

						for i in [Center.TypeOriginal, Center.TypeTranscoded]:
							if streamType in [i, Center.TypeBoth]:
								link = self._linkStream(index = index, info = info, item = entry, mode = i)
								if link:
									copy = Tools.copy(entry)
									copy['stream']['type'] = i
									copy['stream']['link'] = link

									# Estimate the transcoded file size.
									if i == Center.TypeTranscoded:
										bitrate = bitrateAll = entry['video']['bitrate']
										for a in [i for i in streams if i['Type'] == 'Audio']:
											if audioDefault and a['Index'] == audioDefault['index']:
												# On Emby, some audio streams do not have a bitrate attribute.
												try: bitrate += a['BitRate']
												except: pass
												break

										if fileBandwidth:
											bandwidth = fileBandwidth
										else:
											speedtest = SpeedTester.result()
											if speedtest and bitrate > speedtest: bandwidth = int(speedtest * 0.9)
											else: bandwidth = int(bitrate * 0.75)
										if bandwidth > bitrate: bandwidth = bitrate

										# The streaming link can be constructed manually from the parameters.
										# Manually request the transcoding URL with another API request, since it automatically calculates the video/audio bitrate, based on the global MaxStreamingBitrate value.
										parameters = self._searchParameters(
											fileBandwidth = bandwidth,
											fileContainer = fileContainer,
											videoQuality = videoQuality,
											videoCodec = videoCodec,
											audioIndex = audioDefault['index'] if audioDefault else None,
											audioChannels = audioChannels,
											audioCodec = audioCodec,
											subtitleIndex = subtitleDefault['index'] if subtitleDefault else None,
										)

										# On Jellyfin item['Id'] == info['Id'], but this is not the case on Emby, so use the newley extracted ID.
										# This also means that the new data returned by the request below contains only a single item and accessing by "position" will fail.
										multi = item['Id'] == info['Id']
										infos2 = self._request(index = index, method = Networker.MethodPost, category = Center.CategoryItems, action = Center.ActionInfo, id = info['Id'], parameters = parameters)
										if multi: info2 = infos2['MediaSources'][position]
										else: info2 = infos2['MediaSources'][0]

										link = self._linkStream(index = index, info = info2, item = entry, mode = i, parameters = parameters)

										# On Emby, the transcoded URL sometimes contains "TranscodeReasons=SubtitleCodecNotSupported", instead of the normal "TranscodeReasons=ContainerBitrateExceedsLimit".
										# Trying to play these streams fails.
										# Adding the "SubtitleProfiles" list to the request seems to solve the problem.
										# What excatly should be in "SubtitleProfiles" is not clear.
										# We just use the harcoded list from the Emby's server website (the in-browser player) - although these values might be different on other Emby servers.
										if 'TranscodeReasons=SubtitleCodecNotSupported' in link:
											parameters = self._searchParameters(
												fileBandwidth = bandwidth,
												fileContainer = fileContainer,
												videoQuality = videoQuality,
												videoCodec = videoCodec,
												audioIndex = audioDefault['index'] if audioDefault else None,
												audioChannels = audioChannels,
												audioCodec = audioCodec,
												subtitleIndex = subtitleDefault['index'] if subtitleDefault else None,
												subtitleProfile = True,
											)

											infos2 = self._request(index = index, method = Networker.MethodPost, category = Center.CategoryItems, action = Center.ActionInfo, id = info['Id'], parameters = parameters)
											if multi: info2 = infos2['MediaSources'][position]
											else: info2 = infos2['MediaSources'][0]

											link = self._linkStream(index = index, info = info2, item = entry, mode = i, parameters = parameters)

										copy['stream']['link'] = link
										copy['file']['size'] = int(copy['file']['size'] * (bandwidth / float(bitrate)))
										copy['file']['container'] = fileContainer
										if videoQuality: copy['video']['quality'] = videoQuality
										copy['video']['range'] = None
										copy['video']['depth'] = None

										value = Regex.extract(data = link, expression = r'VideoCodec=([a-z\d](?:$|[&,])')
										copy['video']['codec'] = value if value else Center.VideoCodecType[videoCodec]

										if audioChannels: copy['audio']['channels'] = audioChannels

										value = Regex.extract(data = link, expression = r'AudioCodec=([a-z\d](?:$|[&,])')
										copy['audio']['codec'] = value if value else Center.AudioCodecType[audioCodec]

										copy['audio']['language'] = [audioDefault['language']] if audioDefault else None
										copy['subtitle']['language'] = [subtitleDefault['language']] if subtitleDefault else None
										if copy['subtitle']['language']: copy['subtitle']['type'] = Stream.SubtitleTypeHard

									self._lock()
									self.mResults.append(copy)
									self._unlock()

					except: Logger.error()
		except: Logger.error()

	def _searchEpisodes(self, index, id, season, episode, exact):
		try:
			items = self._request(index = index, method = Networker.MethodGet, category = Center.CategoryShows, action = Center.ActionEpisodes, id = id, parameters = {'Recursive' : 'true'})
			items = [i for i in items['Items'] if i['Type'] == 'Episode']
			if not exact: items = [i for i in items if (not 'ParentIndexNumber' in i or i['ParentIndexNumber'] == season) and (not 'IndexNumber' in i or i['IndexNumber'] == episode)]
			threads = [Pool.thread(target = self._searchInfo, args = (index, i)) for i in items]
			[i.start() for i in threads]
			[i.join() for i in threads]
		except: Logger.error()

##############################################################################
# EMBY
##############################################################################

class Emby(Center):

	Id = 'emby'
	Name = 'Emby'
	Link = 'https://emby.media'

	def __init__(self):
		Center.__init__(self)

##############################################################################
# JELLYFIN
##############################################################################

class Jellyfin(Center):

	Id = 'jellyfin'
	Name = 'Jellyfin'
	Link = 'https://jellyfin.org'

	def __init__(self):
		Center.__init__(self)
