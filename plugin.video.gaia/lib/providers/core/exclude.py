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

# Used by offline.py

try:
	from multiprocessing import Process, Manager, cpu_count
	from threading import Thread
	import time, sys, re, atexit, signal, base64

	sys.path = sys.path[1:] # Otherwise it will try to import local json.py instead of Python's json.
	import json

	size = 1000 # How many excludes to combine into a single regex.
	threads = cpu_count()
	finished = False
	exited = False

	def log(message):
		print(message)

		# Not required when executed from terminal.
		# But required when executed in Kodi, otherwise the output hangs with subprocess.readline() after the 1st "Progress: ...".
		sys.stdout.flush()

	def exit():
		global exited
		if not exited:
			log('Exiting ...')
			exited = True
			time.sleep(5)
			sys.exit()
	atexit.register(exit)
	signal.signal(signal.SIGTERM, exit)

	def execute(data, exclude, result, dummy, filter):
		global exited
		try:
			for i in range(len(data)):
				if exited: return

				matched = False
				value = value2 = data[i]
				if value:
					if filter:
						try: value = filter.search(value).group(1)
						except: value = None
					if value:
						for j in exclude:
							match = j.search(value)
							if match:
								matched = True
								#log('Matched:  %s   -   %s' % (match.group(1), value))
								break

					if not value or matched:
						dummy.append(False)
					else:
						result.append(value2)
						dummy.append(True)
				data[i] = None # Free up memory.
		except KeyboardInterrupt:
			log('Exiting (execute) ...')
			exit()

	def progress(total, dummy):
		try:
			global finished
			global exited
			percent = -1
			total = float(total) / 100.0
			start = time.time()
			while not finished and not exited:
				p = round((len(dummy) / total), 1)
				if p > percent:
					valid = sum([1 for i in dummy if i])
					invalid = sum([1 for i in dummy if not i])
					percent = p
					timer = time.time() - start
					log('  Progress: ' + str(percent) + '% [Valid: ' + str(valid) + ' | Invalid: ' + str(invalid) + '] -- [Time: ' + str(int(timer / 60.0)) + ' min | Remaining: ' + str(int((((timer * (100.0 / (percent or 0.0001))) - timer) / 60.0)))  + ' min]')
				time.sleep(30)
			log('  Progress: 100%')
			finished = None
		except KeyboardInterrupt:
			log('Exiting (progress) ...')
			exit()

	log('Initializing ...')

	arguments = json.loads(base64.b64decode(sys.argv[1]))
	pathInput = arguments['input']
	pathOutput = arguments['output']
	pathExclude = arguments['exclude']
	filter = arguments['filter']

	log('Reading ...')
	with open(pathInput, 'r') as file:
		dataInput = file.read().split('\n')
	with open(pathExclude, 'r') as file:
		dataExclude = file.read().split('\n')

	log('Compiling ...')
	dataExclude = [dataExclude[i::size] for i in range(size)]
	dataExclude = [r'(?:^|[^a-z\d])(%s)(?:$|[^a-z\d])' % r'|'.join(i) for i in dataExclude]
	dataExclude = [re.compile(i, flags = re.IGNORECASE) for i in dataExclude]
	if filter: filter = re.compile(filter, flags = re.IGNORECASE)
	log('  Expressions: ' + str(len(dataExclude)))

	log('Excluding ...')
	manager = Manager()
	dummy = manager.list()
	total = len(dataInput)
	dataInput = [dataInput[i::threads] for i in range(threads)]
	thread = Thread(target = progress, args = (total, dummy)).start()

	processes = []
	results = []
	for i in dataInput:
		result = manager.list()
		results.append(result)
		process = Process(target = execute, args = (i, dataExclude, result, dummy, filter))
		processes.append(process)
		process.start()

	# Sometimes some processes are still running, even after calling join().
	# Update: it seems that the progress thread is the one that leaves a Python process in memory. Joining it solves the problem.
	# Update: No! Even when waiting for the thread, there are still 2 active Python processes running. But after some time they finish correctly it seems.
	[process.join() for process in processes]
	log('Waiting for completion')
	finished = True
	try: thread.join() # For some reason, an error can be thrown here: 'NoneType' object has no attribute 'join'.
	except: pass
	while not finished is None: time.sleep(1)
	try: [process.join() for process in processes]
	except: pass
	log('Finished waiting for completion')

	log('Finalizing data')
	result = []
	for i in results: result.extend(i)
	log('Valid: ' + str(len(result)))
	log('Invalid: ' + str(total - len(result)))
	log('Writing file')
	file = open(pathOutput, 'w')
	file.write('\n'.join(result))
	file.close()
	log('Finished')
except Exception as error:
	log('Error [Line %d]: %s' % (sys.exc_info()[2].tb_lineno, str(error)))
