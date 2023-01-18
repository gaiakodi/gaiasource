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

	def __init__(self, target = None, group = None, name = None, daemon = None, args = (), kwargs = {}):
		self._statusSet(Concurrency.StatusUnknown)
		base = self.base()
		if base:
			base.__init__(self, target = target, group = group, name = name, daemon = daemon, args = args, kwargs = kwargs)
			self._statusSet(Concurrency.StatusInitial)
		self.mParent = self.current()
		self.mRank = self.currentRank() + 1

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
					from lib.modules.interface import Dialog
					if setting == 1: Dialog.notification(title = 36037, message = 33245, icon = Dialog.IconError, time = 20000)
					elif setting == 2: Dialog.confirm(title = 36037, message = 33246)


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

	SettingLimit = 'general.concurrency.limit'
	SettingNotifications = 'general.concurrency.notifications'

	PropertyNotification = 'GaiaConcurrencyNotification'

	Instances = {}
	Lock = None
	Semaphore = None
	Limit = None

	GlobalLock = None
	EventFinish = {}

	@classmethod
	def _log(self, message, prefix = True, developer = True):
		from lib.modules.tools import Logger, System
		if not developer or System.developer():
			if prefix: message = 'CONCURRENCY POOL: ' + message
			Logger.log(message = message, type = Logger.TypeInfo, level = Logger.LevelExtended)

	@classmethod
	def limit(self):
		if Pool.Limit is None:
			from lib.modules.tools import Settings
			limit = Settings.getCustom(id = Pool.SettingLimit)
			return limit if limit else 0
		else:
			return Pool.Limit

	@classmethod
	def limitSet(self, limit):
		Pool.Limit = limit

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

			System.windowPropertyClear(Pool.PropertyNotification)
			self._log('Finished in %s seconds' % time.elapsed())
		else:
			if busy:
				while instance.alive(): Time.sleep(busy)
			else:
				instance.join()

	@classmethod
	def instance(self, type, target = None, args = (), kwargs = {}, start = False, join = False):
		try:
			Pool.Lock.acquire()

			if Pool.Semaphore is None:
				limit = self.limit()
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

			instance = type(target = target, name = name, args = args, kwargs = kwargs)
			Pool.Instances[instance.id()] = instance
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
	def thread(self, target = None, args = (), kwargs = {}, start = False, join = False):
		return self.instance(type = Thread, target = target, args = args, kwargs = kwargs, start = start, join = join)

	@classmethod
	def threads(self):
		return self.instances(type = Thread)

	@classmethod
	def threadCount(self):
		return self.count(type = Thread)

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
	def process(self, target = None, args = (), kwargs = {}, start = False, join = False):
		return self.instance(type = Process, target = target, args = args, kwargs = kwargs, start = start, join = join)

	@classmethod
	def processes(self):
		return self.instances(type = Process)

	@classmethod
	def processCount(self):
		return self.count(type = Process)

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
