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

from lib.modules import api
from lib.modules import tools
from lib.modules import interface
from lib.modules.network import Networker

class Support(object):

	def __init__(self):
		pass

	@classmethod
	def _error(self):
		interface.Dialog.notification(title = 35311, message = tools.System.name() + ' ' + interface.Translation.string(35312), icon = interface.Dialog.IconError)

	@classmethod
	def bugs(self):
		Networker.linkShow(link = tools.Settings.getString('internal.link.support', raw = True))

	@classmethod
	def menu(self):
		directory = interface.Directory()
		directory.add(label = 35314, action = 'supportCategories', folder = True, icon = 'help')
		directory.add(label = 36097, action = 'supportReport', folder = False, icon = 'bug')
		directory.add(label = 35313, action = 'supportBugs', folder = False, icon = 'support')
		directory.finish()

	@classmethod
	def report(self):
		try:
			from lib.modules.database import Database

			interface.Dialog.confirm(title = 36097, message = 36098)
			interface.Dialog.notification(title = 36097, message = 36102, icon = interface.Dialog.IconInformation)

			pathReport = interface.Dialog.browse(title = 36097, type = interface.Dialog.BrowseDirectoryWrite)
			pathReport = tools.File.joinPath(pathReport, 'Gaia_Bug_Report_%s.zip' % tools.Time.format())

			pathData = tools.System.temporary(directory = 'report')
			paths = [tools.Logger.path(),  tools.Settings.pathProfile(), tools.Settings.pathDatabase()]
			for path in paths:
				pathNew = tools.File.joinPath(pathData, tools.File.name(path, extension = True))
				tools.File.copy(path, pathNew)
				if pathNew.endswith(Database.Extension):
					Database(path = pathNew)._deleteAll(query = 'DELETE FROM %s WHERE id LIKE "account.%%" or id LIKE "premium.%%";', commit = True, compact = True)

			import zipfile
			zip = zipfile.ZipFile(pathReport, 'w')
			directories, files = tools.File.listDirectory(pathData, absolute = True)
			for file in files:
				zip.write(file, tools.File.name(file, extension = True))
			zip.close()

			tools.File.deleteDirectory(path = pathData, force = True)
		except: tools.Logger.error()

		if tools.File.exists(pathReport):
			interface.Dialog.notification(title = 36097, message = 36100, icon = interface.Dialog.IconSuccess)
			if interface.Dialog.option(title = 36097, message = 36099): self.bugs()
			return True
		else:
			interface.Dialog.notification(title = 36097, message = 36101, icon = interface.Dialog.IconError)
			return False

	@classmethod
	def categories(self):
		interface.Loader.show()
		try:
			categories = api.Api.supportCategories()
			directory = interface.Directory()
			for category in categories:
				label = interface.Format.bold(category['name'] + ': ') + category['description'].replace('.', '')
				directory.add(label = label, action = 'supportQuestions', parameters = {'id' : category['id']}, folder = True, icon = 'help')
			directory.finish()
		except:
			self._error()
		interface.Loader.hide()

	@classmethod
	def questions(self, id):
		interface.Loader.show()
		try:
			questions = api.Api.supportList(id)
			directory = interface.Directory()
			for question in questions:
				directory.add(label = question['title'], action = 'supportQuestion', parameters = {'id' : question['id']}, folder = False, icon = 'help')
			directory.finish()
		except:
			self._error()
		interface.Loader.hide()

	@classmethod
	def question(self, id):
		interface.Loader.show()
		try:
			question = api.Api.supportQuestion(id)
			interface.Dialog.text(title = question['title'], message = question['message']['format'])
		except:
			self._error()
		interface.Loader.hide()
