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
Semaphore = None
Event = None

class Concurrency(object):

	StatusUnknown	= 0
	StatusInitial	= 1	# Initialized, but not started yet.
	StatusStarted	= 2	# Started, but not running yet.
	StatusQueued	= 3	# Queued and waiting for later execution. Previously started, but because no new thread could be created, never moved into running state. In can switch between started and queued multiple times.
	StatusRunning	= 4	# Running, that is, executing the target code.
	StatusFinished	= 5	# Finished executing.
	StatusFailed	= 6	# Failed executing.
	StatusBusy		= [StatusStarted, StatusQueued, StatusRunning]

	ErrorNone		= None
	ErrorUnknown	= 'unknown'
	ErrorStart		= 'start'	# Cannot start a new thread.

	RetryLimit		= 5 # The maximum number of times to retry starting a thread.
	RetryTimeout	= 2 # The maximum seconds to wait until automatically retrying without being signaled.

	Property		= 'GaiaConcurrency%s'

	def __init__(self, target = None, group = None, name = None, daemon = None, synchronizer = None, args = (), kwargs = {}):
		self._statusSet(Concurrency.StatusUnknown)
		base = self.base()
		if base:
			base.__init__(self, target = target, group = group, name = name, daemon = daemon, args = args, kwargs = kwargs)
			self._statusSet(Concurrency.StatusInitial)
		self.mParent = self.current()
		self.mRank = self.currentRank() + 1
		self.mSynchronizer = synchronizer

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
				def execute(data):
					data['result'] = True
				data = self.data()
				instance = self.base()(target = execute, kwargs = {'data' : data}) # Do not use the Gaia classes, otherwise it will call the Pool functions.
				instance.start()
				instance.join()
				result = data['result']
			except: pass
			self._globalSet(result)
		else:
			result = value
		return result

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

	def _synchronizerAcquire(self):
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
		# However, with processes that do not share the memoery this does not work. The run() function is executed WITHIN the process and not OUTSIDE in the parent.
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
				setting = Settings.getInteger(id = Pool.SettingNotifications)
				if setting > 0:
					from lib.modules.tools import Regex
					from lib.modules.interface import Dialog, Translation
					if setting == 1:
						Dialog.notification(title = 36037, message = 33245, icon = Dialog.IconError, time = 20000)
					elif setting == 2:
						message = Translation.string(33246)
						if System.commandIsScrape(): message = message % (Regex.extract(data = Translation.string(36063), expression = '(.*?)(?:$|\s*\[)'), Translation.string(35539))
						else: message = message % (Translation.string(36038), Translation.string(32310))
						Dialog.confirm(title = 36037, message = message)


class Thread(Concurrency, PyThread):

	@classmethod
	def initialize(self):
		global Lock, Semaphore, Event
		Lock = PyThreadLock
		Semaphore = PyThreadSemaphore
		Event = PyThreadEvent

	@classmethod
	def current(self):
		return PyThreadCurrent()

	@classmethod
	def base(self):
		return PyThread

try:

	from multiprocessing import Process as PyProcess, Manager as PyProcessManager, current_process as PyProcessCurrent, Lock as PyProcessLockBase, Semaphore as PyProcessSemaphore, Event as PyProcessEvent

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

		@classmethod
		def initialize(self):
			global Lock, Semaphore, Event
			Lock = PyProcessLock
			Semaphore = PyProcessSemaphore
			Event = PyProcessEvent

		@classmethod
		def current(self):
			return PyProcessCurrent()

		@classmethod
		def base(self):
			return PyProcess

		@classmethod
		def data(self):
			# NB: Do not use a global var for the manager.
			# Otherwise the process (Python LanguageInvoker) that uses it stays in memory forever and Kodi hangs when being closed.
			#if Process.Manager is None: Process.Manager = PyProcessManager()
			#return Process.Manager.dict()
			return PyProcessManager().dict()

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

	SettingTask				= 'general.concurrency.task'
	SettingInstance			= 'general.concurrency.instance'
	SettingNotifications	= 'general.concurrency.notifications'

	PropertyNotification	= 'GaiaConcurrencyNotification'

	LimitTask				= None
	LimitInstance			= None
	LimitInternal			= 200 # The internal limit of the maximum threads that should be created. Running more than these threads concurrently propbably means a design mistake.
	LimitWarning			= 500 # After how many threads a warning message should be shown. Keep in mind that during scraping more threads are used.

	CountTotal				= {Thread : 0, Process : 0}	# The total number of threads created during this execution.
	CountConcurrent			= {Thread : 0, Process : 0}	# The maximum number of threads that were running concurrently during this execution.

	Instances				= {}
	Lock					= None
	Semaphore				= None

	GlobalLock				= None
	EventFinish				= {}

	@classmethod
	def _log(self, message, prefix = True, developer = True):
		from lib.modules.tools import Logger, System
		if not developer or System.developer():
			if prefix: message = 'CONCURRENCY POOL: ' + message
			Logger.log(message = message, type = Logger.TypeInfo, level = Logger.LevelExtended)

	@classmethod
	def reset(self, settings = True):
		if settings:
			Pool.LimitTask = None
			Pool.LimitInstance = None
		Pool.CountTotal = {Thread : 0, Process : 0}
		Pool.CountConcurrent = {Thread : 0, Process : 0}

	@classmethod
	def limitTask(self):
		if Pool.LimitTask is None:
			from lib.modules.tools import Settings
			limit = Settings.getCustom(id = Pool.SettingTask)

			if not limit:
				from lib.modules.tools import Hardware, Math

				performance = Hardware.performanceRating()
				limit = Math.scale(performance, fromMinimum = 0, fromMaximum = 1, toMinimum = 35, toMaximum = 50)

				processor = Hardware.processorType()
				if processor:
					if processor in [Hardware.ProcessorArm, Hardware.ProcessorArc]: limit -= 5
					elif processor in [Hardware.ProcessorIntel, Hardware.ProcessorAmd]: limit += 5

				memory = Hardware.memoryBytes()
				if memory:
					adjust = Math.scale(memory, fromMinimum = 1073741824, fromMaximum = 4294967296, toMinimum = -10, toMaximum = 0)
					if adjust < 0: limit += adjust

				limit = max(20, min(50, int(limit)))

			Pool.LimitTask = limit
		return Pool.LimitTask

	@classmethod
	def limitInstance(self):
		if Pool.LimitInstance is None:
			from lib.modules.tools import Settings
			limit = Settings.getCustom(id = Pool.SettingInstance)
			Pool.LimitInstance = limit if limit else 0
		return Pool.LimitInstance

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
	def join(self, instance = None, busy = False):
		from lib.modules.tools import Time, System
		if busy is True: busy = 0.05

		if instance is None:
			# Wait for all instances to finish.
			# Low-end devices have a limited number of threads (eg: 400) that can be created.
			# If the threads are not joined and cleaned up (eg: Gaia throws an exception and exits while threads are still running), the threads seem to not be returned to the OS for reuse.
			# If trying to create a new thread in such a case, Python throws an error: RuntimeError: can't start new thread
			# It seems that no new threads can be created, because the limit has been reached, and the ones created before were not returned to the OS properley.
			# Wait for all threads to return before exiting Gaia - not sure if this solves the problem.

			time = Time(start = True)
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
								while instance.alive(): Time.sleep(busy)
							else:
								instance.join()
							running = True
					except:
						nonrunning = True
				recheck = running and nonrunning

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
		else:
			if busy:
				while instance.alive(): Time.sleep(busy)
			else:
				instance.join()

	@classmethod
	def instance(self, type, target = None, args = (), kwargs = {}, synchronizer = None, start = False, join = False):
		try:
			Pool.Lock.acquire()

			if Pool.Semaphore is None:
				limit = self.limitInstance()
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

			instance = type(target = target, name = name, synchronizer = synchronizer, args = args, kwargs = kwargs)
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
	def instances(self, type = None):
		# Use "list(Pool.Instances.items())" to create a copy of the items iterator.
		# Otherwise there might be a rare error: RuntimeError: dictionary changed size during iteration
		if type is None: return Pool.Instances
		else: return {id : instance for id, instance in list(Pool.Instances.items()) if isinstance(instance, type)}

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
	def count(self, type = None):
		return len(self.instances(type = type).keys())

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
	def thread(self, target = None, args = (), kwargs = {}, synchronizer = None, start = False, join = False):
		return self.instance(type = Thread, target = target, args = args, kwargs = kwargs, synchronizer = synchronizer, start = start, join = join)

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
	def process(self, target = None, args = (), kwargs = {}, synchronizer = None, start = False, join = False):
		return self.instance(type = Process, target = target, args = args, kwargs = kwargs, synchronizer = synchronizer, start = start, join = join)

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
