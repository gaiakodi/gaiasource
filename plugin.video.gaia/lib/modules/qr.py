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

from lib.modules.tools import Hash, System, File, Tools, Regex, Logger, Time
from lib.modules.interface import Format
from lib.modules.network import Networker
from lib.modules.concurrency import Pool
from lib.modules.external import Importer

class Qr(object):

	ImagerPil			= 'pil'					# Python Image Library: Should be available on most Kodis, but no guarantee.
	ImagerPymaging		= 'pymaging'			# Pymaging: Is always available, since it is a module local to Gaia without any further dependecies.
	ImagerDefault		= ImagerPil

	ColorFront			= 'FF000000'
	ColorBack			= 'FFFFFFFF'
	ColorGaia			= 'gaia'
	ColorAutomatic		= True

	CorrectionLow		= 'low'					# About 7% or less errors can be corrected.
	CorrectionMedium	= 'medium'				# About 15% or less errors can be corrected.
	CorrectionHigh		= 'high'				# About 25% or less errors can be corrected.
	CorrectionExtended	= 'extended'			# About 30% or less errors can be corrected.
	CorrectionDefault	= CorrectionExtended

	DetailMinimum		= 1
	DetailMaximum		= 40					# Too much detail can make some QR scanners interpret the wrong data.
	DetailDefault		= None					# Automatically determine the detail.

	StyleSquare			= 'sqaure'				# Standard square pixels.
	StyleRound			= 'round'				# Rounded square pixels.
	StyleGap			= 'gap'					# Square pixels with gaps in between.
	StyleCircle			= 'circle'				# Circle pixels.
	StyleVertical		= 'vertical'			# Vertical bar pixels.
	StyleHorizontal		= 'horizontal'			# Horizontal bar pixels.
	StyleDefault		= StyleRound

	AdjustRound			= 0.5					# Default is 1.0 which is too round.
	AdjustGap			= None
	AdjustVertical		= None
	AdjustHorizontal	= None
	AdjustAutomatic		= True
	AdjustDefault		= AdjustAutomatic

	QualityLow			= 10
	QualityMedium		= 30
	QualityHigh			= 50
	QualityAutomatic	= None
	QualityDefault		= QualityAutomatic

	ResolutionLow		= 128
	ResolutionMedium	= 512
	ResolutionHigh		= 1024
	ResolutionDefault	= ResolutionMedium

	PaddingNone			= 0
	PaddingThin			= 3
	PaddingMedium		= 5
	PaddingThick		= 10
	PaddingAutomatic	= True
	PaddingDefault		= PaddingMedium

	IconNone			= None
	IconLogo			= 'logo'			# Add the padded Gaia logo to the center of the QR code.
	IconSquare			= 'square'			# Add an empty white square to the center of the QR code.
	IconRound			= 'round'			# Add an empty white rounded square to the center of the QR code.
	IconCircle			= 'circle'			# Add an empty white circle to the center of the QR code.
	IconDefault			= IconNone

	BorderRadius		= 0.07				# Percentage of image resolution in [0, 1].
	BorderSize			= 0.015				# Percentage of image resolution in [0, 1].

	CacheNone			= None				# Do not cache an regenerate the QR image.
	CacheTemporary		= 'temporary'		# Cache the QR image in the Kodi temporary directory. The image will be deleted after Kodi restarts.
	CachePermanent		= 'permanent'		# Cache the QR image in the Gaia userdata directory. The image will remain after Kodi restarts.
	CacheDefault		= CacheTemporary

	LimitMaximum		= 1250				# The absolute maximum data length, after which the QR generation will fail since there are not enough pixels. The real limit is around 1300.
	LimitScanner		= 600				# The maximum data length after which QR readers struggle to read the QR code. At 700 it sometimes works, but you must hold still for a long time.

	Error				= True

	##############################################################################
	# GENERAL
	##############################################################################

	# This function can be called for a single or multiple QR codes.
	# 1. For a single QR code:
	#	Pass in named parameters as specified by self._generate().
	#	Eg: Qr.generate(data = 'http://example.com', colorFront = 'FFFF0000', ..., wait = True)
	# 2. For multiple QR codes:
	#	Pass in an unamed dictionaries, one for each QR code. The dictionary keys/values are the parameters specified by self._generate().
	#	Eg: Qr.generate(
	#			{'data' : 'http://example1.com', 'colorFront' : 'FFFF0001'},
	#			{'data' : 'http://example2.com', 'colorFront' : 'FFFF0002'},
	#			...,
	#			wait = True
	#		)
	# In addition to the parameters specified by self._generate(), an additional boolean parameter "wait" caan be passed to the function.
	# The "wait" parameter must be named. For multiple images, the "wait" parameter must be lasst, after all the dictionaries.
	# If "wait" is True, the QR codes are generated in the main thread and the function returns once all QR codes were generated.
	# If "wait" is False, the QR codes are generated in sub-threads thread and the function returns even if the QR codes are still generating.
	# In most cases "wait" should be True, since it is slightly faster thatn running in sub-threads.
	# The function returns as follows:
	#	1. Single QR code with "wait = True": Returns the image path on success, or None on failure.
	#	2. Single QR code with "wait = False": Returns None.
	#	3. Multiple QR codes with "wait = True": Returns a dictionary with the keys being the "data" parameter and the values the generate image paths. If an image failed to generate, the value is None.
	#	4. Multiple QR codes with "wait = False": Returns None.
	@classmethod
	def generate(self, *args, **kwargs):
		wait = True
		slow = False
		if kwargs:
			if 'wait' in kwargs:
				wait = kwargs['wait']
				del kwargs['wait']
			if 'slow' in kwargs:
				slow = kwargs['slow']
				del kwargs['slow']

		if slow: Time.sleep(0.2)

		if kwargs or (args and not Tools.isDictionary(args[0])):
			if wait: return self._generate(*args, **kwargs)
			else: Pool.thread(target = self._generate, args = args, kwargs = kwargs, start = True)
		elif args:
			result = {}
			for i in args:
				i['result'] = result
				if wait: self._generate(**i)
				else: Pool.thread(target = self._generate, kwargs = i, start = True)
				if slow: Time.sleep(0.1)

		return None

	##############################################################################
	# CLEAN
	##############################################################################

	@classmethod
	def clean(self, cache = CacheDefault):
		if cache:
			path = self._path(cache = cache)
			if path: return File.deleteDirectory(path)
		return False

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _error(self, error = None):
		if error and (Tools.isInstance(error, ImportError) or Tools.isInstance(error, ModuleNotFoundError)):
			# PIL should always be available, since it is compiled and shipped with Kodi.
			# However, there are some exceptions.
			# For instance, under Android, script.module.pil has to be imported from addon.xml for PIL to work.
			# Do this special exception handeling here, in case there are some Kodi versions (eg: custom builds) that do not have PIL.
			if Qr.Error: # Only print this error once, otherwise it will be printed many times for all the QR codes.
				Qr.Error = False
				Logger.log('Neither the "Pillow" (PIL) not the "Image" module could be imported. QR codes will be of lower quality. Nothing to worry about.', prefix = True, type = Logger.TypeError)
		else:
			Logger.error()

	@classmethod
	def _generate(self,
		data,								# The data to encode.

		colorFront = ColorFront,			# Color of the QR code. If a list/tuple is passed in, a gradient between the colors is used.
		colorBack = ColorBack,				# Color of the background.
		colorBorder = ColorAutomatic,		# Color of the border.

		borderRadius = BorderRadius,		# The size of the border radius as a percentage of the iamge resolution, or in pixels.
		borderSize = BorderSize,			# The thickness of the border as a percentage of the iamge resolution, or in pixels.

		correction = CorrectionDefault,		# Level of error correction.
		detail = DetailDefault,				# The detail of QR pixels.

		style = StyleDefault,				# The style/shape of the QR pixels.
		styleAdjust = AdjustDefault,		# Additional parameter for some styles (StyleGap, StyleRound, StyleVertical, StyleHorizontal) to adjust the size, roundness, or gap. Decimal number, typically in [0.0, 1.0].

		padding = PaddingAutomatic,			# The empty padding around the QR code.
		quality = QualityDefault,			# The quality of the image. This is the intial resolution when generating the QR code. The final resolution is specified by "resolution", and only works if PIL works.
		resolution = ResolutionDefault,		# The final resolution of the image in pixels.

		icon = IconDefault,					# An icon added to the middle of the QR code.

		imager = ImagerDefault,				# The image module used for generating the QR code.

		truncate = True,					# Truncate if the data is too long.
		extended = False,					# Instead of returning the QR path, return a dictionary with extra information.
		fallback = None,					# If the image cannot be generated in Kodi's temp directory, use the addon profile directory instead.
		cache = CacheDefault,				# Reuse the image if it already exists.
		result = {},						# For thread usage.
	):
		try:
			image = None
			path = None
			try:
				if data is None: return None
				qrcode = Importer.moduleQrCode(error = self._error)
				qrdrawers = Importer.moduleQrDrawers(error = self._error)

				parameters = Tools.copy({
					'data' : data,
					'colorFront' : colorFront,
					'colorBack' : colorBack,
					'colorBorder' : colorBorder,
					'borderRadius' : borderRadius,
					'borderSize' : borderSize,
					'correction' : correction,
					'detail' : detail,
					'style' : style,
					'styleAdjust' : styleAdjust,
					'padding' : padding,
					'quality' : quality,
					'resolution' : resolution,
					'icon' : icon,
					'imager' : imager,
				})

				truncated = False
				if truncate:
					sizeBefore = len(data)
					data = self._data(data = data)
					sizeAfter = len(data)
					truncated = not sizeBefore == sizeAfter

				path = self._path(cache = cache, profile = bool(fallback), **parameters)
				if cache and File.exists(path):
					result[data] = path
					return {'path' : path, 'data' : data, 'truncated' : truncated} if  extended else path

				colorBorder = self._color(color = colorBorder, default = colorFront)
				colorFront = self._color(color = colorFront)
				colorBack = self._color(color = colorBack)

				if correction == Qr.CorrectionLow: correction = qrcode.constants.ERROR_CORRECT_L
				elif correction == Qr.CorrectionMedium: correction = qrcode.constants.ERROR_CORRECT_M
				elif correction == Qr.CorrectionHigh: correction = qrcode.constants.ERROR_CORRECT_Q
				else: correction = qrcode.constants.ERROR_CORRECT_H

				if detail: detail = min(Qr.DetailMaximum, max(Qr.DetailMinimum, detail))
				else: detail = Qr.DetailDefault

				# When using StyledPilImage with a large quality, generating the image can take 30+ seconds on a fast CPU.
				# Calculate the quality to get a close a possibler to the target resolution.
				if quality is Qr.QualityAutomatic: quality = min(40, max(5, int(resolution / ((0.262 * len(data)) + 33))))

				if padding is Qr.PaddingAutomatic: padding = Qr.PaddingDefault * max(1, len(data) / 300.0)
				else: padding = Qr.PaddingDefault

				styler = None
				if qrdrawers:
					if style == Qr.StyleSquare:
						styler = qrdrawers.SquareModuleDrawer()
					elif style == Qr.StyleRound:
						if styleAdjust is Qr.AdjustAutomatic: styleAdjust = Qr.AdjustRound
						if not styleAdjust is None:
							try: styler = qrdrawers.RoundedModuleDrawer(styleAdjust)
							except: pass
						if styler is None: styler = qrdrawers.RoundedModuleDrawer()
					elif style == Qr.StyleGap:
						if styleAdjust is Qr.AdjustAutomatic: styleAdjust = Qr.AdjustGap
						if not styleAdjust is None:
							try: styler = qrdrawers.GappedSquareModuleDrawer(styleAdjust)
							except: pass
						if styler is None: styler = qrdrawers.GappedSquareModuleDrawer()
					elif style == Qr.StyleCircle:
						styler = qrdrawers.CircleModuleDrawer()
					elif style == Qr.StyleVertical:
						if styleAdjust is Qr.AdjustAutomatic: styleAdjust = Qr.AdjustVertical
						if not styleAdjust is None:
							try: styler = qrdrawers.VerticalBarsDrawer(styleAdjust)
							except: pass
						if styler is None: styler = qrdrawers.VerticalBarsDrawer()
					elif style == Qr.StyleHorizontal:
						if styleAdjust is Qr.AdjustAutomatic: styleAdjust = Qr.AdjustHorizontal
						if not styleAdjust is None:
							try: styler = qrdrawers.HorizontalBarsDrawer(styleAdjust)
							except: pass
						if styler is None: styler = qrdrawers.HorizontalBarsDrawer()

				if icon and (icon.isalpha()): icon = File.joinPath(System.pathResources(), 'resources', 'media', 'qr', icon + '.png')

				factory = None
				mask = None
				if imager == Qr.ImagerPymaging:
					factory = Importer.moduleQrPymaging()
					if colorFront and Tools.isArray(colorFront) and Tools.isArray(colorFront[0]): colorFront = colorFront[1]
				elif icon or styler:
					factory = Importer.moduleQrStyledPil()

					# Must use a mask with StyledPilImage, otherwise the colors do not work.
					# If the alpha channel is full (255), only pass in RGB, otherwise the QR code is covered by the background color.
					if self._gradient(colorFront): mask = Importer.moduleQrGradiant()(center_color = colorFront[0], edge_color = colorFront[1], back_color = colorBack[:3] if colorBack[3] == 255 else colorBack)
					else: mask = Importer.moduleQrFill()(front_color = colorFront, back_color = colorBack[:3] if colorBack[3] == 255 else colorBack)

				qr = qrcode.QRCode(error_correction = correction, box_size = quality, border = padding, version = detail)
				qr.add_data(data)
				qr.make(fit = True)
				image = qr.make_image(image_factory = factory, module_drawer = styler, fill_color = colorFront, back_color = colorBack, color_mask = mask, embeded_image_path = icon)
			except Exception as exception:
				image = None
				path = None
				self._error(error = exception)

			# In case the QR generation fails, fall back to Pymaging (which is pure Python PNG code) instead of PIL.
			# PIL should generally work, but there are some old posts that say PIL module could not be found (eg: on Android), but this should be fixed in the new Kodi.
			# First try PIL and if something fails, try Pymaging.
			if image and path:
				try:
					if imager == Qr.ImagerPymaging:
						image.save(path)
						image = None
					image = self._border(image = image, path = path, radius = borderRadius, size = borderSize, color = colorBorder, resolution = resolution)
					image.save(path)
				except PermissionError:
					# (2025-05-01) A user reported this on Android:
					#	... "/storage/emulated/0/Android/data/org.xbmc.kodi/files/.kodi/addons/plugin.video.gaia/lib/modules/qr.py", line 331, in _generate
					#		image.save(path)
					#	File "/data/user/0/org.xbmc.kodi/cache/apk/assets/addons/script.module.pil/lib/PIL/Image.py", line 2237, in save
					#		fp = builtins.open(filename, "w+b")
					#	PermissionError: [Errno 13] Permission denied: /storage/emulated/0/Android/data/org.xbmc.kodi/files/.kodi/temp/gaia/qr/0AF8ED8F4705A971945D80D0D445CE68EF4DAAEA36C1958945D80570A5B03EB1.png
					# The Kodi temp directory should always be writable, so not sure why there are permission errors.
					# If it fails, try to save the file in the addon's profile temp directory.
					if fallback is None: return self._generate(truncate = truncate, extended = extended, cache = cache, result = result, fallback = True, **parameters)
					else: Logger.error()
				except:
					Logger.error()
				if not File.exists(path): path = None
				result[data] = path
				return {'path' : path, 'data' : data, 'truncated' : truncated} if extended else path
			elif not imager == Qr.ImagerPymaging:
				parameters['imager'] = Qr.ImagerPymaging
				return self._generate(truncate = truncate, extended = extended, cache = cache, result = result, fallback = fallback, **parameters)
		except:
			Logger.error()
			return None

	@classmethod
	def clean(self, cache = CachePermanent):
		return File.deleteDirectory(self._path(cache = cache, make = False))

	@classmethod
	def size(self, cache = CachePermanent):
		return File.sizeDirectory(self._path(cache = cache, make = False))

	@classmethod
	def _data(self, data):
		# If the data is too large, the QR generation can fail or the QR readers struggle to scan.
		if len(data) > Qr.LimitScanner:
			if Networker.linkIsMagnet(data):
				while len(data) > Qr.LimitScanner:
					try:
						index = data.rindex('&tr=')
						data = data[:index]
					except: break
			if Networker.linkIs(data, magnet = True):
				while len(data) > Qr.LimitScanner:
					try:
						index = Regex.index(data = data, expression = r'.*(&.*?=)', group = 1)
						data = data[:index]
					except: break
		return data

	@classmethod
	def _path(self, cache, make = True, profile = False, data = None, **kwargs):
		if data is None: name = None
		else: name = Hash.sha256(data + str(kwargs)) + '.png'
		if cache == Qr.CachePermanent:
			path = File.joinPath(System.profile(), 'Qr')
			if make: File.makeDirectory(path)
			if name: return File.joinPath(path, name)
			else: return path
		else:
			return System.temporary(directory = 'qr', file = name, gaia = not profile, make = True, clear = False, profile = profile)

	@classmethod
	def _color(self, color, default = None):
		if color is Qr.ColorAutomatic: return self._color(default)
		elif color == Qr.ColorGaia: return self._color((Format.colorSecondary(), Format.colorPrimary()))

		if self._gradient(color):
			return (self._color(color = color[0], default = default), self._color(color = color[1], default = default))
		else:
			if Tools.isString(color): color = Format.colorToRgb(color, alpha = True)
			# Both PIL and PymagingImage have the alpha channel last.
			if len(color) > 3: return (color[1], color[2], color[3], color[0])
			else: return (color[0], color[1], color[2], 255)

	@classmethod
	def _gradient(self, color):
		return color and Tools.isArray(color) and not Tools.isInteger(color[0])

	# Radius and border are a percentage of the image resolution in [0,1].
	@classmethod
	def _border(self, image = None, path = None, radius = BorderRadius, size = BorderSize, color = ColorFront, resolution = ResolutionDefault):
		try:
			from PIL import Image, ImageDraw

			if image is None: image = Image.open(path)
			width, height = image.size
			dimension = max(width, height)

			if radius:
				radius = int(dimension * radius)
				circle = Image.new('L', (radius * 2, radius * 2), 0)
				draw = ImageDraw.Draw(circle)
				draw.ellipse((0, 0, radius * 2, radius * 2), fill = 255)
				alpha = Image.new('L', image.size, 'white')
				alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
				alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, height - radius))
				alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (width - radius, 0))
				alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (width - radius, height - radius))
				image.putalpha(alpha)

			if size:
				if self._gradient(color): color = color[1]

				size = int(dimension * size)
				width -= (size * 2)
				height -= (size * 2)
				draw = ImageDraw.Draw(image)

				# Draw rounded corners.
				draw.arc([(0, 0), (2 * radius - 1, 2 * radius -1)], 180, 270, color, size + 1)
				draw.arc([(width - 2 * radius + 2 * size, 0), (width + 2 * size, 2 * radius - 1)], 270, 0, color, size + 1)
				draw.arc([(width - 2 * radius + 2 * size, height - 2 * radius + 2 * size), (width + 2 * size, height + 2 * size)], 0, 90, color, size + 1)
				draw.arc([(0, height - 2 * radius + 2 * size), (2 * radius - 1, height + 2 * size)], 90, 180, color, size + 1)

				# Draw side edges.
				draw.line([(radius - 1, size / 2 - 1), (width - radius + 2 * size, size / 2 - 1)], color, size)
				draw.line([(size / 2 - 1, radius - 1), (size / 2 - 1, height - radius + 2 * size)], color, size)
				draw.line([(width + 1.5 * size, radius - 1), (width + 1.5 * size, height - radius + 2 * size)], color, size)
				draw.line([(radius - 1, height + 1.5 * size), (width - radius + 2 * size, height + 1.5 * size)], color, size)

			try: antialias = Image.ANTIALIAS # Python 3.11 + PIL 9.0 and prior.
			except: antialias = Image.LANCZOS # Python 3.12 + PIL 10.0 and prior.
			image = image.resize((resolution, resolution), antialias) # Smooth.
		except: Logger.error()
		return image
