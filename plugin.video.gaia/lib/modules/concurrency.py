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

# NB: Do not import Gaia modules/classes here, since most other modules import this file, causing circular imports.
from threading import Thread as PyThread, current_thread as PyThreadCurrent, Lock as PyThreadLock, Semaphore as PyThreadSemaphore, Event as PyThreadEvent

Lock = None
Event = None

Semaphore = None

# These are just Semaphore wrapper classes, which can be passed to Pool.instance/thread/process(synchronizer = ...).
Premaphore = None	# Hard limit. The semaphore is acquired BEFORE the thread/process object is created and BEFORE it is executed. This tries to prevent too many thread objects being created, even if they do not all execute at the same time.
Postmaphore = None	# Soft limit. The semaphore is acquired AFTER the thread/process object was created, but BEFORE it is executed. This could create tons of idle threads that although not all executing at the same time, still stay in memory until they can finally be executed.

class Concurrency(object):

	StatusUnknown	= 0
	StatusInitial	= 1	# Initialized, but not started yet.
	StatusStarted	= 2	# Started, but not running yet.
	StatusQueued	= 3	# Queued and waiting for later execution. Previously started, but because no new thread could be created, never moved into running state. In can switch between started and queued multiple times.
	StatusDelaying	= 4	# Sleeping for a while in the run() function to allow other code to start executing before the thread's code starts to execute.
	StatusRunning	= 5	# Running, that is, executing the target code.
	StatusFinished	= 6	# Finished executing.
	StatusFailed	= 7	# Failed executing.
	StatusBusy		= [StatusStarted, StatusQueued, StatusDelaying, StatusRunning]

	ErrorNone		= None
	ErrorUnknown	= 'unknown'
	ErrorStart		= 'start'	# Cannot start a new thread.

	RetryLimit		= 5 # The maximum number of times to retry starting a thread.
	RetryTimeout	= 2 # The maximum seconds to wait until automatically retrying without being signaled.

	Property		= 'GaiaConcurrency%s'

	def __init__(self, target = None, group = None, name = None, daemon = None, synchronizer = None, delay = None, args = (), kwargs = {}):
		self._statusSet(Concurrency.StatusUnknown)
		base = self.base()
		if base:
			base.__init__(self, target = target, group = group, name = name, daemon = daemon, args = args, kwargs = kwargs)
			self._statusSet(Concurrency.StatusInitial)

		self.mParent = self.current()
		self.mRank = self.currentRank() + 1
		self.mSynchronizer = synchronizer
		self.mDelay = delay

	@classmethod
	def initialize(self):
		pass

	@classmethod
	def current(self):
		return None

	@classmethod
	def currentRank(self):
		try: return self.current().rank()
		except: return 0

	@classmethod
	def parent(self):
		try: return self.current().mParent
		except: return None

	@classmethod
	def parentRank(self):
		try: return self.parent().rank()
		except: return 0

	@classmethod
	def base(self):
		return None

	@classmethod
	def data(self):
		return {}

	@classmethod
	def support(self):
		result = False
		value = self._globalGet()
		if value is None:
			try:
				data = self.data()
				instance = self.base()(target = self._support, kwargs = {'data' : data}) # Do not use the Gaia classes, otherwise it will call the Pool functions.
				instance.start()
				instance.join()
				result = data['result']
			except: pass
			self._globalSet(result)
		else:
			result = value
		return result

	@classmethod
	def _support(self, data = None):
		# This must be a classmethod iinstead of a local function inside support().
		# This is important for Processes, otherwise when setting this:
		#	multiprocessing.set_start_method('spawn')
		# the following error is thrown:
		#	AttributeError: Can't pickle local object 'Concurrency.support.<locals>.execute
		data['result'] = True

	@classmethod
	def _name(self):
		return self.__name__

	@classmethod
	def _globalProperty(self):
		return Concurrency.Property % self._name()

	@classmethod
	def _globalGet(self):
		from lib.modules.tools import System
		result = System.windowPropertyGet(self._globalProperty())
		if result: result = bool(int(result))
		else: result = None
		return result

	@classmethod
	def _globalSet(self, value):
		from lib.modules.tools import System
		return System.windowPropertySet(self._globalProperty(), int(value))

	def id(self):
		return id(self)

	def label(self):
		return self.name

	def rank(self):
		return self.mRank

	def _statusSet(self, status):
		self.mStatus = status

	def status(self):
		return self.mStatus

	def alive(self):
		return self.status() in Concurrency.StatusBusy

	def _alive(self):
		return self.is_alive()

	def synchronizer(self):
		return self.mSynchronizer

	def synchronizerSet(self, synchronizer):
		self.mSynchronizer = synchronizer

	def _synchronizerAcquire(self, force = False):
		if self.mSynchronizer and (force or isinstance(self.mSynchronizer, Postmaphore)):
			try: self.mSynchronizer.acquire()
			except: pass

	def _synchronizerRelease(self):
		try: self.mSynchronizer.release()
		except: pass

	def start(self, retry = RetryLimit):
		# On low-end devices Python can run out of threads and will not be able to start a new thread.
		# In such a case the exception is thrown: "RuntimeError Can't start new thread".
		# Not sure if this is a limit in Python, Kodi, or maybe even the operating system, or if a limit is imposed on a per-addon or per-Python-invoker basis.
		# Also no sure if the limit is imposed on a single execution (single Python invoker), or globally on Kodi or the OS. So not sure if once the limit was reached, all subsequent executions might also run into this problem.
		# The general idea is as follows:
		#	1. Try to start the thread as normal. If it starts we are done.
		#	2. If it fails, wait for another running thread to finish before trying again.
		#	3. Wait a maximum of RetryTimeout seconds, in order to reduce the chances of a deadlock if for some reason the event is never triggered, because a running thread is waiting on results from this queued thread and both therefore do not finish.
		#	4. Continue retrying to start the thread RetryLimit number of times. In most cases the thread should start on the 2nd try.
		#	5. If we retried a number of times without success, give up and show the user a notification to restart the device. In this case we probably have a bunch of threads deadlocked.

		self._statusSet(Concurrency.StatusStarted)
		self._synchronizerAcquire()
		try:
			self.base().start(self)
			if not retry is None and not retry == Concurrency.RetryLimit:
				Pool._log(message = '%s [%s]: Restart succeeded.' % (self.id(), self.label()), developer = True)
		except Exception as exception:
			error = self._error(exception = exception)
			if error == Concurrency.ErrorStart:
				if not retry is None and retry > 0:
					self._statusSet(Concurrency.StatusQueued)
					Pool._log(message = '%s [%s]: Concurrency limit reached (%d threads). Waiting for restart.' % (self.id(), self.label(), Pool.threadCount()), developer = True)
					event = Pool.finishEvent(rank = self.rank())
					event.wait(timeout = Concurrency.RetryTimeout)
					Pool._log(message = '%s [%s]: Restarting instance.' % (self.id(), self.label()), developer = True)
					self.start(retry = retry - 1)
				else:
					self._finish(Concurrency.StatusFailed)
					Pool._log(message = '%s [%s]: Restarting instance failed %d times. Giving up.' % (self.id(), self.label(), Concurrency.RetryLimit), developer = True)
					self._errorNotification(error = error)
			else:
				self._finish(Concurrency.StatusFailed)
				from lib.modules.tools import Logger
				Logger.error()

	def run(self):
		if self.mDelay:
			self._statusSet(Concurrency.StatusDelaying)
			from lib.modules.tools import Time
			Time.sleep(self.mDelay)
		self._statusSet(Concurrency.StatusRunning)
		self.base().run(self)
		self._finish(Concurrency.StatusFinished) # Read comment in _finish().

	def join(self, timeout = None):
		# Read comment in _finish().
		try: self.base().join(self, timeout)
		except: pass # Throws an exception here if the process was forcefully exited - SystemExit.
		if not self._alive() or timeout is None: self._finish(Concurrency.StatusFinished)

	def terminate(self):
		# Read comment in _finish().
		try: self.base().terminate(self)
		except: pass
		self._finish(Concurrency.StatusFinished)

	def kill(self):
		# Read comment in _finish().
		try: self.base().kill(self)
		except: pass
		self._finish(Concurrency.StatusFinished)

	def close(self):
		# Read comment in _finish().
		try: self.base().close(self)
		except: pass
		self._finish(Concurrency.StatusFinished)

	def _finish(self, status):
		# The thread/process should be removed from the Pool once it is finihsed.
		# However, there is no way to create a signal/callback when the thread/process is done.
		# The logical idea is to call _finish() at the end of run().
		# This is fine for threads, since they share memory.
		# However, with processes that do not share the memory this does not work. The run() function is executed WITHIN the process and not OUTSIDE in the parent.
		# Hence, if a process run() finishes, it will try to remove the process from the copy of the Pool within the process, instead of the Pool of the parent process that actually added the process to its Pool list.
		# Another idea is to call _finish() at the end of join(), since join() is called from the parent. However, join() can have a timeout and does not mean the thread/process is actually finished.
		# We therefore try to call _finish() from any function that somehow handles the end of the thread/process (run, join, terminate, kill, close).
		self._statusSet(status)

		self._synchronizerRelease()
		Pool.remove(self)

	def _error(self, exception):
		from lib.modules.tools import Regex
		if not exception: return Concurrency.ErrorNone
		exception = str(exception)
		if not exception: return Concurrency.ErrorNone
		elif Regex.match(data = exception, expression = 'can\'t\s*start\s*new\s*thread'): return Concurrency.ErrorStart
		else: return Concurrency.ErrorUnknown

	def _errorNotification(self, error):
		from lib.modules.tools import Settings, System
		if error == Concurrency.ErrorStart:
			lock = Pool.globalLock()
			lock.acquire()
			if System.windowPropertyGet(Pool.PropertyNotification):
				lock.release()
			else:
				System.windowPropertySet(Pool.PropertyNotification, True)
				lock.release()
				setting = Pool.settingNotification()
				if setting > 0:
					from lib.modules.interface import Dialog, Translation, Player
					if setting == 1:
						Dialog.notification(title = 36037, message = 33245, icon = Dialog.IconError, time = 20000)
					elif setting == 2:
						playback = Player().isPlayback()
						timeout = 30000 if playback else None

						message = None
						if System.commandIsMenu(): message = 36038
						elif System.commandIsScrape(): message = 36622
						message = (Translation.string(36422) % Translation.string(message)) if message else ''

						message = Translation.string(36421) % (Translation.string(36619), message, Translation.string(32310))
						if Dialog.option(title = 36037, message = message, labelConfirm = 32501, labelDeny = 33486, timeout = timeout):
							System.power(action = System.PowerRestart, proper = True, notification = True)

class ThreadPremaphore(PyThreadSemaphore):
	pass

class ThreadPostmaphore(PyThreadSemaphore):
	pass

class Thread(Concurrency, PyThread):

	@classmethod
	def initialize(self):
		global Lock, Event, Semaphore, Premaphore, Postmaphore

		Lock = PyThreadLock
		Event = PyThreadEvent

		Semaphore = PyThreadSemaphore
		Premaphore = ThreadPremaphore
		Postmaphore = ThreadPostmaphore

	@classmethod
	def current(self):
		return PyThreadCurrent()

	@classmethod
	def base(self):
		return PyThread

try:

	'''
		It seems that multiprocessing does not work in the new Kodi or Python.
		This always did seem to work (Python 3.6 and 3.8), but doesn't seem to work in Python 3.10 anymore.
		Whenever we start a new process (just a nomal multiprocessing.Process, not even the custom class below), the following happens:
			1. The process begins with process.start() and Kodi creates a new LanguageInvoker process.
			2. When calling process.join(), the code seems to hang. The actual process function coded is never executed.
			3. The LanguageInvoker stays in memory. If manually killed, Kodi continues executing the code after the process.join() statement.
			4. At no time is any of the code in the process target function executed. It seems that Kodi struggles to actuually start the target code.
			5. A similar thing also happens when we call manager.dict(). The manager internally calls manager.start(), which causes the same things as above.
			6. Every time we start a new process, Kodi pprints this to log: "info <general>: AddOnLog: peripheral.joystick: Disabling joystick interface "linux"".
			7. So maybe Kodi uses multiprocessing for its own purposes, maybe having overwritten some of its coded. And that is why we cannot start manual processes anymore.

		For now, we leave multiprocessing disabled.
		We raise an exception here, otherwise if Process-support is checked during service.py, or later on in tools.Hardware, a LanguageInvoker is left in memory, due to a process being created in support().
	'''
	raise Exception()

	# The synchronize "classes" in "multiprocessing" are not actually classes, but functions, and can therefore not be inherited from. At least not in newer Python versions
	#from multiprocessing import Process as PyProcess, Manager as PyProcessManager, current_process as PyProcessCurrent, Lock as PyProcessLockBase, Semaphore as PyProcessSemaphore, Event as PyProcessEvent
	from multiprocessing import Process as PyProcess, Manager as PyProcessManager, current_process as PyProcessCurrent
	from multiprocessing.synchronize import Lock as PyProcessLockBase, Semaphore as PyProcessSemaphore, Event as PyProcessEven

	class ProcessPremaphore(PyProcessSemaphore):
		pass

	class ProcessPostmaphore(PyProcessSemaphore):
		pass

	class PyProcessLock(PyProcessLockBase):

		# The multiprocessing Lock does not have a locked() function.
		def locked(self):
			if self.acquire(block = False):
				self.release()
				return False
			else:
				return True

	class Process(Concurrency, PyProcess):

		#Manager = None
		Shared = 0

		@classmethod
		def initialize(self):
			global Lock, Event, Semaphore, Premaphore, Postmaphore

			Lock = PyProcessLock
			Event = PyProcessEvent

			Semaphore = PyProcessSemaphore
			Premaphore = ProcessPremaphore
			Postmaphore = ProcessPostmaphore

		@classmethod
		def current(self):
			return PyProcessCurrent()

		@classmethod
		def base(self):
			return PyProcess

		@classmethod
		def data(self, size = 8388608): # 8MB
			# NB: Do not use a global var for the manager.
			# Otherwise the process (Python LanguageInvoker) that uses it stays in memory forever and Kodi hangs when being closed.
			#if Process.Manager is None: Process.Manager = PyProcessManager()
			#return Process.Manager.dict()

			# NB: This does not work in the new Kodi/Python anymore.
			# Inside the multiprocessing.Manager function, there is a call "manager.start()" which causes the script to stop.
			# So maybe Kodi has overwritten/disabled some multiprocessing stuff.
			# https://github.com/python/cpython/blob/main/Lib/multiprocessing/context.py
			# Update: This is the same error as above. A bunch of Python LanguageInvoker are left in memory when calling this function.
			return PyProcessManager().dict()

			# Update: With the new Kodi/Python this does not seem to work at all anymore.
			# Whenever this function is called (either manually or automatically by the serrvice when calling "Pool.processSupport()"), the Python Invoker freezes without finishing or returning results.
			# The invoker is then left in memory until Kodi exits.
			# Every time this function is called, an new invoker is created and left in memory.
			# Every time this function is called, Kodi shows an error in the log:
			#	info <general>: AddOnLog: peripheral.joystick: Disabling joystick interface "linux"
			# This happens when we create a new multiprocessing.Manager() instance. The issue seems to be in the Manager function in the multiprocessing module, when "manager.start()" iss called.
			# Maybe Kodi does something weird or overwrites some multiprocessing stuff.
			# Or maybe the manager does not work, because Kodi uses its own manager and Python only allows a single manager instance.
			# Or maybe we can just not create a manager in the single-invoker context of Kodi addons.
			# So we currently use a custom module to handle the shared dict. Not sure about cross-platform compatibility or performance implications.
			# Also note that we have to set a size of the shared memory for this module. Make sure enough memory is allocated for the given task.
			# Generally, users should use Threads over Processes from the addon settings. This should only be used by the dev in providers->core->offline.py.
			# Update: This does not solve the problem, so the shared memory module was removed. There seems to be a wider problem with multiprocessing. More info at the start of the class.
			'''from lib.modules.external import Importer
			Process.Shared += 1
			memory = Importer.moduleSharedMemoryDict()
			return memory(name = 'GaiaProcessShared%d' % Process.Shared, size = size)'''

except:

	class Process(Concurrency):

		@classmethod
		def support(self):
			result = False
			value = self._globalGet()
			if value is None: self._globalSet(result)
			else: result = value
			return result

class Pool(object):

	LevelAutomatic			= 0
	LevelCustom				= 1
	LevelLow				= 2
	LevelMedium				= 3
	LevelHigh				= 4

	ModeAutomatic			= 0
	ModeThread				= 1
	ModeProcess				= 2

	DelayNone				= None
	DelayShort				= 0.01	# 10ms
	DelayMedium				= 0.05	# 50ms
	DelayLong				= 0.1	# 100ms
	DelayExtended			= 0.5	# 500ms
	DelayDefault			= DelayMedium

	SettingLevel			= 'general.concurrency.level'
	SettingNotification		= 'general.concurrency.notification'
	SettingGlobal			= 'general.concurrency.global'
	SettingGlobalLimit		= 'general.concurrency.global.limit'
	SettingMetadata			= 'general.concurrency.metadata'
	SettingMetadataLimit	= 'general.concurrency.metadata.limit'
	SettingScrape			= 'general.concurrency.scrape'
	SettingScrapeLimit		= 'general.concurrency.scrape.limit'
	SettingScrapeBinge		= 'general.concurrency.scrape.binge'
	SettingScrapeConnection	= 'general.concurrency.scrape.connection'
	SettingScrapeMode		= 'general.concurrency.scrape.mode'

	PropertyNotification	= 'GaiaConcurrencyNotification'

	LimitInternal			= 200 # The internal limit of the maximum threads that should be created. Running more than these threads concurrently propbably means a design mistake.
	LimitWarning			= 400 # After how many threads a warning message should be shown. Keep in mind that during scraping more threads are used.

	CountTotal				= {Thread : 0, Process : 0}	# The total number of threads created during this execution.
	CountConcurrent			= {Thread : 0, Process : 0}	# The maximum number of threads that were running concurrently during this execution.

	TimeoutStandard			= 1200	# 20 minutes.
	TimeoutDeveloper		= 60	# 1 minute.

	DataGlobal				= None
	DataMetadata			= None
	DataScrape				= None
	DataConnection			= None
	DataMode				= None

	Instances				= {}
	Lock					= None
	Semaphore				= None
	Joining					= False

	GlobalLock				= None
	EventFinish				= {}

	@classmethod
	def _developer(self):
		from lib.modules.tools import System
		return System.developer()

	@classmethod
	def _timeout(self):
		return Pool.TimeoutDeveloper if self._developer() else Pool.TimeoutStandard

	@classmethod
	def _log(self, message, prefix = True, developer = True):
		from lib.modules.tools import Logger
		if not developer or self._developer():
			if prefix is True: message = 'CONCURRENCY POOL: ' + message
			elif prefix: message = prefix + message
			Logger.log(message = message, type = Logger.TypeInfo, level = Logger.LevelExtended)

	@classmethod
	def _logLine(self, extra = '', developer = True):
		self._log(message = '-' * 70 + extra, prefix = False, developer = developer)

	@classmethod
	def _logDangling(self, instance, developer = True):
		from lib.modules.tools import System
		if not developer or self._developer():
			try: action = System.commandResolve(initialize = False).get('action')
			except: action = 'Unknown'
			label = instance.label()

			# Note that certain invokers are ment to stay alive, like the "streamsShow" that will remain active until the stream window was closed.
			excepted = False
			exceptions = [
				{'action' : 'scrape', 'instance' : 'Window._initialize1'},		# WindowStreams
				{'action' : 'streamsShow', 'instance' : 'Window._initialize1'},	# WindowStreams
				{'action' : 'scrape', 'instance' : 'Trailer._cinemaStart'},		# Cinema Window

			]
			for exception in exceptions:
				if action == exception['action'] and label == exception['instance']:
					excepted = True
					break

			if not excepted:
				self._logLine()
				self._logLine(extra = ' ') # Avoid: Skipped 1 duplicate messages..
				self._log('--  CONCURRENCY POOL - DANGLING PROCESS', prefix = False)
				self._log('--     A concurrency instance did not finish for a long time', prefix = False)
				self._log('--     and is still running. This is most likley a bug causing', prefix = False)
				self._log('--     the current Python invoker to never finish. This will', prefix = False)
				self._log('--     cause the Python invoker to never clean up and return', prefix = False)
				self._log('--     threads back to the OS.', prefix = False)
				self._log('--        ACTION: %s' % str(action), prefix = False)
				self._log('--        INSTANCE: %s [%s]' % (instance.id(), label), prefix = False)
				self._logLine()
				self._logLine(extra = ' ')

	@classmethod
	def reset(self, settings = True):
		if settings:
			Pool.DataGlobal = None
			Pool.DataMetadata = None
			Pool.DataScrape = None
			Pool.DataConnection = None
		Pool.CountTotal = {Thread : 0, Process : 0}
		Pool.CountConcurrent = {Thread : 0, Process : 0}
		Pool.Joining = False

	@classmethod
	def _settingPerformance(self, limit):
		from lib.modules.tools import Hardware, Math

		initial = limit.get('initial') or limit

		performance = Hardware.performanceRating()
		value = Math.scale(performance, fromMinimum = 0, fromMaximum = 1, toMinimum = initial['minimum'], toMaximum = initial['maximum'])

		if 'processor' in limit:
			processor = Hardware.processorType()
			if processor:
				if processor in [Hardware.ProcessorArm, Hardware.ProcessorArc]: value += limit['processor']['minimum']
				elif processor in [Hardware.ProcessorIntel, Hardware.ProcessorAmd]: value += limit['processor']['maximum']

		# The OS assigns fixed stack memory to each thread.
		# If a system has little memory, not that many thread objects can be created and executed simultaneously.
		# Hence, the thread limit is more affected by the memory limit than the processor.
		if 'memory' in limit:
			memory = Hardware.memoryBytes()
			if memory:
				adjust = Math.scale(memory, fromMinimum = 1073741824, fromMaximum = 4294967296, toMinimum = limit['memory']['minimum'], toMaximum = limit['memory']['maximum'])
				if adjust < 0: value += adjust

		return self._settingLimit(value = value, limit = limit)

	@classmethod
	def _settingLimit(self, value, limit):
		limit = limit.get('final') or limit.get('initial') or limit
		return max(limit['minimum'], min(limit['maximum'], int(value)))

	@classmethod
	def settingData(self):
		from lib.modules.tools import Settings

		unknown = 'Unknown'
		unlimited = 'Unlimited'
		labels = {
			Pool.LevelAutomatic	: 'Automatic',
			Pool.LevelCustom	: 'Custom',
			Pool.LevelLow		: 'Low',
			Pool.LevelMedium	: 'Medium',
			Pool.LevelHigh		: 'High',
		}

		level = self.settingLevel()
		levelGlobal = level
		levelMetadata = level
		levelScrape = level
		levelBinge = level
		levelConnection = level
		levelMode = level

		if level == Pool.LevelCustom:
			levelGlobal = Settings.getInteger(id = Pool.SettingGlobal)
			levelMetadata = Settings.getInteger(id = Pool.SettingMetadata)
			levelScrape = Settings.getInteger(id = Pool.SettingScrape)
			levelBinge = levelScrape
			levelConnection = levelScrape
			levelMode = levelScrape

		valueGlobal = None
		valueMetadata = None
		valueScrape = None
		valueBinge = None
		valueConnection = None
		valueMode = None

		label = labels.get(level, unknown)
		labelGlobal = unknown
		labelMetadata = unknown
		labelScrape = unknown
		labelBinge = unknown
		labelConnection = unknown
		labelMode = unknown

		try:
			valueGlobal = self.settingGlobal()
			labelGlobal = '%s (%s Threads)' % (labels.get(levelGlobal, unknown), str(valueGlobal) if valueGlobal else unlimited)
		except: pass

		try:
			valueMetadata = self.settingMetadata()
			labelMetadata = '%s (%s Tasks)' % (labels.get(levelMetadata, unknown), str(valueMetadata) if valueMetadata else unlimited)
		except: pass

		try:
			valueScrape = self.settingScrape(binge = False)
			labelScrape = '%s (%s Tasks)' % (labels.get(levelScrape, unknown), str(valueScrape) if valueScrape else unlimited)
		except: pass

		try:
			valueBinge = self.settingScrape(binge = True)
			labelBinge = '%s (%s Tasks)' % (labels.get(levelBinge, unknown), str(valueBinge) if valueBinge else unlimited)
		except: pass

		try:
			valueConnection = self.settingConnection()
			labelConnection = '%s (%s Connections)' % (labels.get(levelConnection, unknown), str(valueConnection) if valueConnection else unlimited)
		except: pass

		try:
			valueMode = Settings.getInteger(id = Pool.SettingScrapeMode) if levelMode == Pool.LevelCustom else Pool.ModeThread
			labelMode = '%s (%s)' % (labels.get(levelMode, unknown), 'Multi-Processing' if valueMode == Pool.ModeProcess else 'Multi-Threading')
		except: pass

		return {
			'level' : level,
			'label' : label,

			'global' : {
				'level' : levelGlobal,
				'value' : valueGlobal,
				'label' : labelGlobal,
			},
			'metadata' : {
				'level' : levelMetadata,
				'value' : valueMetadata,
				'label' : labelMetadata,
			},
			'scrape' : {
				'level' : levelScrape,
				'value' : valueScrape,
				'label' : labelScrape,
			},
			'binge' : {
				'level' : levelBinge,
				'value' : valueBinge,
				'label' : labelBinge,
			},
			'connection' : {
				'level' : levelConnection,
				'value' : valueConnection,
				'label' : labelConnection,
			},
			'mode' : {
				'level' : levelMode,
				'value' : valueMode,
				'label' : labelMode,
			},
		}

	@classmethod
	def settingLevel(self):
		from lib.modules.tools import Settings
		return Settings.getInteger(id = Pool.SettingLevel)

	@classmethod
	def settingCustom(self):
		return self.settingLevel() == Pool.LevelCustom

	@classmethod
	def settingNotification(self):
		from lib.modules.tools import Settings
		return Settings.getInteger(id = Pool.SettingNotification)

	@classmethod
	def settingGlobal(self):
		# Intel i7:
		#	LevelLow: 250
		#	LevelMedium: 581
		#	LevelHigh: 1422
		# ARM Cortex-A73:
		#	LevelLow: 176
		#	LevelMedium: 418
		#	LevelHigh: 1075

		if Pool.DataGlobal is None:
			from lib.modules.tools import Settings, Hardware

			value = 0
			main = True
			level = self.settingLevel()
			if level == Pool.LevelCustom:
				main = False
				level = Settings.getInteger(id = Pool.SettingGlobal)

			threads = Hardware.threadLimit(memory = False, adjust = True, minimum = 150, maximum = 2000)
			if not threads or threads >= 1500: threads = 0

			if level == Pool.LevelCustom:
				value = Settings.getCustom(id = Pool.SettingGlobalLimit)
				if value is None: value = threads
			elif level == Pool.LevelAutomatic:
				value = threads
			else:
				limit = {
					'minimum' : 150,
					'maximum' : 1000,
					'processor'	: {'minimum' : -20, 'maximum' : 20},
					'memory'	: {'minimum' : -50, 'maximum' : 50},
				}
				if level == Pool.LevelLow: limit.update({'minimum' : 150, 'maximum' : 250})
				elif level == Pool.LevelMedium: limit.update({'minimum' : 300, 'maximum' : 600})
				elif level == Pool.LevelHigh: limit.update({'minimum' : 750, 'maximum' : 1500})
				value = self._settingPerformance(limit = limit)

				if main and value:
					base = Hardware.threadLimit(memory = False, adjust = False)
					if base and base >= 150: value = min(value, base)

			Pool.DataGlobal = value or 0
		return Pool.DataGlobal

	@classmethod
	def settingMetadata(self):
		# Intel i7:
		#	LevelLow: 35
		#	LevelMedium: 50
		#	LevelHigh: 60
		# ARM Cortex-A73:
		#	LevelLow: 26
		#	LevelMedium: 36
		#	LevelHigh: 51

		if Pool.DataMetadata is None:
			from lib.modules.tools import Settings

			value = 0
			limit = {
				'initial'	: {'minimum' : 35, 'maximum' : 50},
				'final'		: {'minimum' : 25, 'maximum' : 50},
				'processor'	: {'minimum' : -5, 'maximum' : 5},
				'memory'	: {'minimum' : -10, 'maximum' : 10},
			}

			level = self.settingLevel()
			if level == Pool.LevelCustom: level = Settings.getInteger(id = Pool.SettingMetadata)

			if level == Pool.LevelCustom:
				value = Settings.getCustom(id = Pool.SettingMetadataLimit)
				if value == 0:
					# Still impose an upper limit on "Unlimited", due to metadata provider request rate limits.
					# 150 migfht already be too high if metadata for all titles in a menu have to be retrieved.
					value = 150
					limit.update({'final' : {'minimum' : 10, 'maximum' : value}})
				elif not value is None:
					limit.update({'final' : {'minimum' : 1, 'maximum' : 100}})
			elif level == Pool.LevelLow:
				limit.update({
					'initial'	: {'minimum' : 25, 'maximum' : 40},
					'final'		: {'minimum' : 20, 'maximum' : 35},
				})
			elif level == Pool.LevelMedium:
				limit.update({
					'initial'	: {'minimum' : 35, 'maximum' : 50},
					'final'		: {'minimum' : 25, 'maximum' : 50},
				})
			elif level == Pool.LevelHigh:
				limit.update({
					'initial'	: {'minimum' : 50, 'maximum' : 65},
					'final'		: {'minimum' : 30, 'maximum' : 60},
				})

			if not value: value = self._settingPerformance(limit = limit)
			value = self._settingLimit(value = value, limit = limit)

			Pool.DataMetadata = value
		return Pool.DataMetadata

	@classmethod
	def settingScrape(self, binge = None):
		# Normal (Threads)
		#	Intel i7:
		#		LevelLow: 6
		#		LevelMedium: 15
		#		LevelHigh: 30
		#	ARM Cortex-A73:
		#		LevelLow: 2
		#		LevelMedium: 6
		#		LevelHigh: 14
		# Binge (Threads)
		#	Intel i7:
		#		LevelLow: 3
		#		LevelMedium: 9
		#		LevelHigh: 18
		#	ARM Cortex-A73:
		#		LevelLow: 2
		#		LevelMedium: 3
		#		LevelHigh: 6
		# Normal (Processes)
		#	Intel i7: 12
		#	ARM Cortex-A73: 7
		# Binge (Processes)
		#	Intel i7: 7
		#	ARM Cortex-A73: 4

		binge = True if binge else False
		if Pool.DataScrape is None or not binge in Pool.DataScrape:
			from lib.modules.tools import Settings, Math

			adjust = 0.6 # Binge adjustment percentage.
			value = 0
			limit = {
				'initial'	: {'minimum' : 5, 'maximum' : 20},
				'final'		: {'minimum' : 3, 'maximum' : 15},
				'processor'	: {'minimum' : -5, 'maximum' : 5},
				'memory'	: {'minimum' : -10, 'maximum' : 10},
			}

			level = self.settingLevel()
			if level == Pool.LevelCustom: level = Settings.getInteger(id = Pool.SettingScrape)

			if level == Pool.LevelCustom:
				value = Settings.getCustom(id = Pool.SettingScrapeBinge if binge else Pool.SettingScrapeLimit)
				if value == 0:
					# Still impose an upper limit on "Unlimited".
					value = 150
					limit.update({'final' : {'minimum' : 1, 'maximum' : value}})
				elif not value is None:
					limit.update({'final' : {'minimum' : 1, 'maximum' : 100}})

				if value is None:
					mode = Settings.getInteger(id = Pool.SettingScrapeMode)
					if mode == Pool.ModeProcess:
						# 0.5x core-count (3): 100 seconds | 51% CPU load
						# 1x core-count + 1 (7): 68 seconds | 72% CPU load
						# 2x core-count + 1 (13): 58 seconds | 83% CPU load
						# Unlimited: 60 seconds | 81% CPU load
						from lib.modules.tools import Hardware
						threads = Hardware.processorCountThread() or 3
						limit.update({
							'initial'	: {'minimum' : max(2, int(threads * 0.5)), 'maximum' : max(2, threads * 2)},
							'final'		: {'minimum' : max(2, threads + 1), 'maximum' : max(2, threads * 2)},
							'processor'	: {'minimum' : -3, 'maximum' : 3},
							'memory'	: {'minimum' : 0, 'maximum' : 0},
						})
						if binge:
							for i in ['initial', 'final']:
								for j in ['minimum', 'maximum']:
									limit[i][j] = max(2, int(Math.roundDown(limit[i][j] * adjust)))

			elif level == Pool.LevelLow:
				limit.update({
					'initial'	: {'minimum' : 4, 'maximum' : 8},
					'final'		: {'minimum' : 2, 'maximum' : 6},
				})
			elif level == Pool.LevelMedium:
				limit.update({
					'initial'	: {'minimum' : 5, 'maximum' : 20},
					'final'		: {'minimum' : 3, 'maximum' : 15},
				})
			elif level == Pool.LevelHigh:
				limit.update({
					'initial'	: {'minimum' : 6, 'maximum' : 35},
					'final'		: {'minimum' : 4, 'maximum' : 30},
				})

			if binge and not level == Pool.LevelCustom:
				for i in ['initial', 'final']:
					for j in ['minimum', 'maximum']:
						limit[i][j] = max(1, int(Math.roundDown(limit[i][j] * adjust)))

			if not value: value = self._settingPerformance(limit = limit)
			if binge and not level == Pool.LevelCustom and value <= 3: value += 1
			value = self._settingLimit(value = value, limit = limit)

			if Pool.DataScrape is None: Pool.DataScrape = {}
			Pool.DataScrape[binge] = value
		return Pool.DataScrape[binge]

	@classmethod
	def settingConnection(self):
		if Pool.DataConnection is None:
			from lib.modules.tools import Settings

			value = 0

			level = self.settingLevel()
			if level == Pool.LevelCustom: level = Settings.getInteger(id = Pool.SettingScrape)
			if level == Pool.LevelCustom: value = Settings.getCustom(id = Pool.SettingScrapeConnection)

			Pool.DataConnection = value or 0
		return Pool.DataConnection

	@classmethod
	def settingMode(self):
		if Pool.DataMode is None:
			from lib.modules.tools import Settings

			value = 0

			level = self.settingLevel()
			if level == Pool.LevelCustom: level = Settings.getInteger(id = Pool.SettingScrape)
			if level == Pool.LevelCustom: value = Settings.getInteger(id = Pool.SettingScrapeMode)

			# If "Automatic" is selected, always use threading, even if the system supports multi-processing.
			# Multi-processing has many potential problems and is mostly not even faster (1-5 secs slower = 10%).
			Pool.DataMode = value or Pool.ModeThread
		return Pool.DataMode

	# Returns the maximum number of threads allowed by the system.
	# Returns None if there is probably no maximum limit, aka an unlimited number of threads can be created.
	@classmethod
	def benchmark(self):
		from lib.modules.tools import Time

		self.tStop = False
		def _benchmark():
			while not self.tStop: Time.sleep(0.3)

		threads = []
		unlimited = 10000 # Do not create too many, otherwise systems with unlimited threads starting lagging.
		for i in range(unlimited):
			try:
				thread = Thread.base()(target = _benchmark)
				thread.start()
				threads.append(thread)
			except RuntimeError:
				break

		count = len(threads)
		if count == unlimited: count = None

		self.tStop = True
		[thread.join() for thread in threads]

		self._log('Unlimited threads' if count is None else ('Maximum of %d threads' % count))
		return count

	@classmethod
	def join(self, instance = None, busy = False, timeout = None):
		from lib.modules.tools import Time, System, Tools

		if busy is True: busy = 0.05

		if instance is None:
			# Wait for all instances to finish.
			# Low-end devices have a limited number of threads (eg: 400) that can be created.
			# If the threads are not joined and cleaned up (eg: Gaia throws an exception and exits while threads are still running), the threads seem to not be returned to the OS for reuse.
			# If trying to create a new thread in such a case, Python throws an error: RuntimeError: can't start new thread
			# It seems that no new threads can be created, because the limit has been reached, and the ones created before were not returned to the OS properley.
			# Wait for all threads to return before exiting Gaia - not sure if this solves the problem.

			Pool.Joining = True
			time = Time(start = True)

			# Use a timeout by default if joining all remaining instances at the end of invoker execution.
			timeoutDefault = timeout is None
			if timeout is None or timeout is True: timeout = self._timeout()
			elif timeout is False: timeout = None

			self._logLine()
			self._log('Waiting for %d instances' % (self.count()))
			for id, instance in self.processes().items():
				self._log('   PROCESS: %s [%s]' % (id, instance.label()), prefix = False)
			for id, instance in self.threads().items():
				self._log('   THREAD: %s [%s]' % (id, instance.label()), prefix = False)

			# Not all instances might have been started yet.
			# Do multiple loops, so that we can wait on instances that might have started during the first iteration.
			recheck = True
			while recheck:
				running = False
				nonrunning = False

				for instance in list(Pool.Instances.values()): # Use a list, since instances can be removed while iterating. Otherwise throws: dictionary changed size during iteration.
					try:
						if instance and not instance.isDaemon():
							if busy:
								if timeout:
									timer = Time(start = True)
									while instance.alive():
										Time.sleep(busy)
										if timer.elapsed() > timeout:
											if instance.alive(): self._logDangling(instance = instance)
											break
									if timeoutDefault:
										while instance.alive():
											Time.sleep(busy)
								else:
									while instance.alive():
										Time.sleep(busy)
							else:
								instance.join(timeout = timeout)
								if instance.alive():
									self._logDangling(instance = instance)
									if timeoutDefault: instance.join()
							running = True
					except:
						nonrunning = True

				recheck = running and nonrunning

				# NB: Sometimes while one thread is joining, another thread might start a new sub-thread.
				# This new sub-thread will then not be part of the instances in the for-loop above.
				# Check here again and if there are any new still-running threads, restart the outer loop to join those as well.
				if not recheck:
					for instance in list(Pool.Instances.values()):
						try:
							if instance and not instance.isDaemon() and instance.alive():
								recheck = True
								break
						except: pass

			self._log('Total created instances')
			self._log('   PROCESS: %s' % Pool.CountTotal[Process], prefix = False)
			self._log('   THREAD: %s' % Pool.CountTotal[Thread], prefix = False)
			self._log('Total concurrent instances')
			self._log('   PROCESS: %s' % Pool.CountConcurrent[Process], prefix = False)
			self._log('   THREAD: %s' % Pool.CountConcurrent[Thread], prefix = False)
			Pool.CountTotal[Process] = 0
			Pool.CountTotal[Thread] = 0
			Pool.CountConcurrent[Process] = 0
			Pool.CountConcurrent[Thread] = 0

			System.windowPropertyClear(Pool.PropertyNotification)
			self._log('Finished in %s seconds' % time.elapsed())
			self._logLine()
		else:
			if not Tools.isArray(instance): instance = [instance]

			# No timeout by default when joining individual instances.
			if timeout is True: timeout = self._timeout()
			elif timeout is None or timeout is False: timeout = None

			if busy:
				if timeout:
					timer = Time(start = True)
					for i in instance:
						while i.alive():
							Time.sleep(busy)
							if timer.elapsed() > timeout:
								if i.alive(): self._logDangling(instance = i)
								break
				else:
					for i in instance:
						while i.alive():
							Time.sleep(busy)
			else:
				for i in instance:
					i.join(timeout = timeout)
					if i.alive(): self._logDangling(instance = i)

	@classmethod
	def wait(self, delay = 1, interval = 0.5):
		# Either wait the full delay, or until the Python process is finishing (addon.py -> Pool.join()).
		# If the Python process is done in any case, there is no need to wait any longer, since there is no other code to be execute that could interfer.
		if delay:
			from lib.modules.tools import Logger
			from lib.modules.tools import Time
			if delay <= interval:
				Time.sleep(delay)
			else:
				for i in range(int(delay / float(interval))):
					if Pool.Joining: break
					Time.sleep(interval)

	# synchronizer: If Semaphore/Premaphore, it is aqcuired BEFORE creating a thread object and BEFORE starting execution.
	# synchronizer: If Postmaphore, it is aqcuired AFTER creating a thread object, but BEFORE starting execution.
	# delay:	Let the thread sleep for a while before executing its code.
	#			This is useful for running threads in the background while executing more important code in the foreground first.
	#			If a thread is started, Python immediatly starts executing the thread's code (for a while), until switching over to other code.
	#			If we therefore want to execute some code in the background using a thread, it will actually start executing in the foreground, and not immediatly continue with the outer code.
	#			By adding a delay/sleep in the thread's execution, Python is forced to continue with other (more important) code, until the sleep is done and Python executes the thread.
	#	True:	Default delay.
	#	Float:	Custom number of seconds to delay.
	#	start:	The delay can also be passed in as the "start" parameter.
	@classmethod
	def instance(self, type, target = None, args = (), kwargs = {}, synchronizer = None, start = False, join = False, delay = None):
		try:
			Pool.Lock.acquire()

			if Pool.Semaphore is None:
				limit = self.settingGlobal()
				if limit: Pool.Semaphore = Semaphore(limit)
				else: Pool.Semaphore = True
			try: Pool.Semaphore.acquire()
			except: pass

			name = target.__qualname__
			if name == 'Cache._cache':
				try: function = kwargs['function']
				except:
					try: function = args[0]
					except: function = None
				if function: name += ' | ' + str(function)

			if synchronizer and not isinstance(synchronizer, Postmaphore):
				# NB: Important to release the global lock before waiting for the synchronizer.
				# Otherwise a synchronized thread that starts its own internal thread(s) will deadlock, since the child thread cannot acquire the global lock still held by the parent.
				try: Pool.Lock.release()
				except: pass
				try: synchronizer.acquire()
				except: pass
				try: Pool.Lock.acquire()
				except: pass

			if start and isinstance(start, (int, float)): delay = start
			if delay is True: delay = Pool.DelayDefault

			instance = type(target = target, name = name, synchronizer = synchronizer, delay = delay, args = args, kwargs = kwargs)
			Pool.Instances[instance.id()] = instance

			# On high-end Intel/AMD devices with a lot of memory, we can create a ton of threads without a problem.
			# However, on low-end ARM devices with limited memory, there is mostly a limit to how many threads can be created.
			# So how many threads is too many?
			#	https://stackoverflow.com/questions/481970/how-many-threads-is-too-many
			# According to the 2nd answer, under Linux, the default thread stack size is 8MB (Windows uses 1MB).
			# The new Linux kernel for most ARM devices supports 4GB of virtual address space.
			# However, some devices might have less memory (eg: 1.5GB - 3GB) or the OS/Kodi uses some of the available memory.
			# Assuming 2GB memory is available, we can barley create 256 threads.
			# Python threads might not always use the full 8MB stack size. The default thread stack size can be changed using: threading.stack_size(...).
			# On a 4GB ARMv8 device, threads seem to run out after about 260 to 290 threads. So the generic calculation is more or less accurate.
			# In any case, using more than 200 threads seem to be a design issue, and it should be reduced.
			# The most common place to run out of threads is when loading an uncahced Trakt show progress list:
			#	1. Each episode in the list will be retrieved.
			#	2. For each episode, the metadata for all episodes in that season and the next season is retrieved.
			#	3. For each episode, the metadata for all the seasons is retrieved.
			#	4. For each episode, the metadata for the show is retrieved.
			# If threads are used everywhere on the lowest level, this can spawn 100s of threads.
			# This does not even include all the threads started by other parts of Gaia, like the Cache class.
			# The indexer classes have now been updated to reduce/disable sub-threads.
			# Only on the outer level in metadata(), threads are started for each movie/episode in the list. All sub-function calls do not use threads anymore if they were called from a parent thread.
			# Update: the default thread stack size on Linux is 8MB (ulimit -a), so on a 4GB device, 512 threads is the theoretical maximum, but since the OS/programs also use RAM, it will probably be more between 250-350.
			count = self.count(type = type)
			Pool.CountTotal[type] += 1
			Pool.CountConcurrent[type] = max(Pool.CountConcurrent[type], count)
			if count > Pool.LimitWarning: self._log('%d threads are running concurrently. This might be too many for low-end devices. Rethink the code and reduce the number of threads.' % count)

			if start: instance.start()
			if join:
				# Release here, otherwise threads started from another thread will deadlock.
				try: Pool.Lock.release()
				except: pass
				instance.join()

			return instance
		finally:
			try: Pool.Lock.release()
			except: pass

	@classmethod
	def instances(self, type = None, alive = None):
		# Use "list(Pool.Instances.items())" to create a copy of the items iterator.
		# Otherwise there might be a rare error: RuntimeError: dictionary changed size during iteration
		if type is None: instances = Pool.Instances
		else: instances = {id : instance for id, instance in list(Pool.Instances.items()) if isinstance(instance, type)}
		if not alive is None: instances = {id : instance for id, instance in list(Pool.Instances.items()) if instance.alive() is alive}
		return instances

	# A global lock that can be used by any classes to to minor quick/things that require mutual exclusion.
	# Should not be used if the lock will be locked for a long time.
	# Typical use is for classes to initialize their own Lock/Event/Semaphore.
	@classmethod
	def globalLock(self):
		return Pool.GlobalLock

	# Create an Event object that waits for a thread to finish and be removed from the pool.
	@classmethod
	def finishEvent(self, rank = None):
		if rank is None: rank = 99999999
		if not rank in Pool.EventFinish: Pool.EventFinish[rank] = []
		event = Event()
		Pool.EventFinish[rank].append(event)
		return event

	@classmethod
	def finishSignal(self):
		# Pick an event with the highest rank, that is a thread that is lowest in the parent-child hierarchy.
		# Parent threads might spawn child threads that must finish before the parent finishes.
		# It is therefore more important to complete the child threads first, to reduce the chance of parent threadsa deadlocking.
		# Pick a random event from a given rank to reduce the chances of the same thread being readded to the queue.
		if Pool.EventFinish:
			from lib.modules.tools import Tools
			rank = max(Pool.EventFinish.keys())
			events = Pool.EventFinish[rank]
			Tools.listPick(events, remove = True).set()
			if not events: del Pool.EventFinish[rank] # Remove empty rank lists.

	@classmethod
	def count(self, type = None, alive = None):
		return len(self.instances(type = type, alive = alive).keys())

	@classmethod
	def available(self, type = None, percent = False):
		available = max(0, Pool.LimitInternal - self.count(type = type))
		return (available / float(Pool.LimitInternal)) if percent else available

	@classmethod
	def data(self, type = None):
		if type is None: return Concurrency.data()
		else: return type.data()

	@classmethod
	def support(self, type = None):
		if type is None: return Thread.support() or Process.support()
		else: return type.support()

	@classmethod
	def initialize(self):
		Pool.Lock = Lock()
		Pool.GlobalLock = Lock()

	@classmethod
	def thread(self, target = None, args = (), kwargs = {}, synchronizer = None, start = False, join = False, delay = None):
		return self.instance(type = Thread, target = target, args = args, kwargs = kwargs, synchronizer = synchronizer, start = start, join = join, delay = delay)

	@classmethod
	def threads(self):
		return self.instances(type = Thread)

	@classmethod
	def threadCount(self):
		return self.count(type = Thread)

	@classmethod
	def threadAvailable(self, percent = False):
		return self.available(type = Thread, percent = percent)

	@classmethod
	def threadData(self):
		return self.data(type = Thread)

	@classmethod
	def threadSupport(self):
		return self.support(type = Thread)

	@classmethod
	def threadCurrent(self):
		return Thread.current()

	@classmethod
	def threadCurrentId(self):
		try: return Thread.current().id()
		except: return None # Main thread.

	@classmethod
	def threadInitialize(self):
		Thread.initialize()
		self.initialize()

	@classmethod
	def process(self, target = None, args = (), kwargs = {}, synchronizer = None, start = False, join = False, delay = None):
		return self.instance(type = Process, target = target, args = args, kwargs = kwargs, synchronizer = synchronizer, start = start, join = join, delay = delay)

	@classmethod
	def processes(self):
		return self.instances(type = Process)

	@classmethod
	def processCount(self):
		return self.count(type = Process)

	@classmethod
	def processAvailable(self, percent = False):
		return self.available(type = Process, percent = percent)

	@classmethod
	def processData(self):
		return self.data(type = Process)

	@classmethod
	def processSupport(self):
		return self.support(type = Process)

	@classmethod
	def processCurrent(self):
		return Process.current()

	@classmethod
	def processCurrentId(self):
		try: return Process.current().id()
		except: return None # Main process.

	@classmethod
	def processInitialize(self):
		Process.initialize()
		self.initialize()

	@classmethod
	def remove(self, instance):
		try:
			del Pool.Instances[instance.id()]
			try: Pool.Semaphore.release()
			except: pass
		except:
			pass
			# Do not log here anymore, since the remove() is now called multiple times by the same thread/process.
			#self._log('Cannot find instance to remove: %s' % instance.id())
		self.finishSignal()

# Use threading classes by default, and only use multiprocessing classes if manually initialized.
# Multiprocessing classes would also work in threading, but threading classes a lightweight/faster and better in most cases.
# Threading classes can cause sporadic deadlocks when used in a child process.
Pool.threadInitialize()
