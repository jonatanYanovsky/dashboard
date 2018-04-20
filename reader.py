# Written by Jonatan Yanovsky

import datetime # for converting from epoch to milliseconds
import time # used for implementing timeouts while waiting on new data to be written to logs
import os # used in getConf
import linecache # used for parsing individual lines from log files
from watchdog.observers import Observer # object that scans for any changes to log files
from watchdog.events import FileSystemEventHandler # event handler used in tandem with the above import


"""
class used to detect file-system changes. Waits for scanForChanges() to raise a file-system event, then processes the event to see if it is valid (the file we were watching was modified)
"""
class MyHandler(FileSystemEventHandler): # 
	def on_modified(self, event): # if the Observer has detected a change to a file

		if self.detectedChange == True: # don't print multiple copies of the same line
			return

		if event.src_path == self.myHandlerDirectory + "radical.entk.appmanager.0000.prof": # if a change has occurred at the log file's location
			print "detected change" 
			self.detectedChange = True

	# public variables
	myHandlerDirectory = "" # a copy of the myHandlerDirectory variable used in GlobalData
	detectedChange = False # a copy of the detectedChange variable used in GlobalData


"""
Watches for changes to the log file. Configures MyHandler and contains the logic to keep waiting on or stop waiting on changes. Also has a KeyboardInterrupt exception that checks if the user wants to terminate the program.
"""
def scanForChanges(glob):

	if glob.stop == True: # do not wait for changes if we need to terminate
		return

	glob.detectedChange = False # overwrite variable so that we scan for new changes

	event_handler = MyHandler() # create event handler class
	event_handler.myHandlerDirectory = glob.myHandlerDirectory # copy variable over to event handler

	observer = Observer() # create an object to scan for changes
	observer.schedule(event_handler, path=glob.myHandlerDirectory, recursive=False) # init
	observer.start() # start waiting for changes

	try:
		while event_handler.detectedChange == False: # no new changes
			time.sleep(1) # wait
			t = time.time() - glob.startTime # record the time
			print "scanning for changes, time = " + str(t)
			
			if t > glob.limit: # timeout
				print "time limit reached, returning"
				break

		observer.stop() # kill wait object
		observer.join()
		return

	except KeyboardInterrupt: # ^C pressed so terminate
		glob.stop = True
		observer.stop()
		observer.join()
		return


"""
The one-size fits all parser. Currently only reads through a single file - "appdata". Checking a different file requires the user to terminate and restart dashboard. This function retrieves data from GlobalData and calls scanForChanges if it has not detected new data in the log file. Each line in the log file is read and parsed for time, event, pst, and ID data. This data is then saved into the GlobalData instance for use in processing.
"""
def testReader(glob): 

	if glob.reachedEnd == True: # do not parse if done parsing
		return 0

	glob.startTime = time.time() # for timeout

	if glob.myHandlerDirectory != "":
		myDir = glob.myHandlerDirectory # continue from last file
		lineCount = glob.lineNum # start at last line number
	else:
		myDir = getConf(glob) # start fresh
		if myDir == -1:
			return -1 # if we did not find a single EnTK execution
		lineCount = 1 # start from line 1, skip line 0

	myFile = myDir + "radical.entk.appmanager.0000.prof" # set our file at this location

	while 1: # read every line in the file, starting from the last line
		row = linecache.getline(myFile, lineCount) # get the current line
		
		if row == "": # no data on this line. Wait for EnTK to write new data
			print "Waiting for changes to log file"
			
			scanForChanges(glob) # wait for changes to log file

			t = time.time() - glob.startTime
			print "parser, time: " + str(t)
			
			if t > glob.limit: # we have done enough parsing (including the time spent scanning for changes) for now
				print "time limit reached, returning"
				return

			if glob.stop == True:
				print "aborting"
				glob.reachedEnd = True
				return

			linecache.checkcache(myFile) # used for when the file has been modified by EnTK while we were waiting for changes
			
			continue # go back and reread the line

		lineCount += 1 # move to next line
		glob.lineNum = lineCount # save current line number for later parsing
		array = row.split(',') # split parsed row into string elements	

		try:
			timeVal = float(array[0]) # get epoch, convert to numeric form
			timeVal = datetime.datetime.fromtimestamp(timeVal) # epoch -> datetime
		except:
			pass # don't do anything if we failed to get the time
		
		try:			
			eventName = array[1] # try to get second element: the string that contains event data
		except:
			continue # skip to next line

		if eventName == "END":
			print "END" # we have reached the last line, we can stop scanning for changes at this point
			glob.reachedEnd = True
			break
		
		try: # gets the cell potentially containing the pipeline, stage, or task (pst)
			pstName = array[4]
		except:
			continue # skip to next line
		
		parts = pstName.split('.') # parse for pst information
		nameID = 0 # init pst ID, ex: 0004

		try:
			name = parts[2] # pst identifier
			nameID = parts[3] # pst number, not used for current plots
		except:
			continue
		
		if name == "pipeline":
			if eventName.find("publishing sync ack for obj with state") != -1: # if the event string contains useful data
				event = eventName.split() # trim the start of this string
				event = event[-1] # get last element - state description: SCHEDULING, DONE, FAILED, etc
				
				glob.hasBeenModified = True # we have found new, useful data
				
				eventNum = glob.pipeline_state_values[event] # convert string to integer (state) representation to save memory
				nameID = int(nameID) # convert string to int
				
				glob.pipelineStates.append(eventNum) # store the new state
				glob.pipelineStateHistory.append([nameID, eventNum]) # store id, state, and the epoch of the event. Only tasks (below) contain the epoch time
				glob.pipelineNewIndex += 1 # more data to process for graphing

		elif name == "stage":
			if eventName.find("publishing sync ack for obj with state") != -1:
				event = eventName.split() 
				event = event[-1]
				
				glob.hasBeenModified = True
				
				eventNum = glob.stage_state_values[event]
				nameID = int(nameID)

				glob.stageStates.append(eventNum)
				glob.stageStateHistory.append([nameID, eventNum])
				glob.stageNewIndex += 1

		else:
			if eventName.find("publishing sync ack for obj with state") != -1:
				event = eventName.split()
				event = event[-1]

				glob.hasBeenModified = True
				
				eventNum = glob.task_state_values[event]
				nameID = int(nameID)

				glob.taskStates.append(eventNum)
				glob.taskStateHistory.append([nameID, eventNum, timeVal])
				glob.taskNewIndex += 1
	

"""
Get the data stored in configuration file, and find the directory that it points to. This is a multi-step processes as EnTK uses files to save its event logs instead of a queue. A queue would allow dashboard to read from a pipe and store the information directly into GlobalData, without the need for file interactions.
"""
def getConf(glob): 
	with open('dashboard.conf') as conf: # open configuration file
		conf.readline() # skip first line
		row = conf.readline() # get second line, the path to the example/executable, but not the output
		if row == "" or row == None: # sanity check
			print "Please check your dashboard.conf file and add the path to your EnTK executable file"
			os._exit(1) # terminate
	
		directories = []
		rs = row.rstrip() # get rid of line-terminating-character

		filesInDir = os.listdir(row.rstrip()) # get files from that directory specified in dashboard.conf

		if len(filesInDir) == 0:
			print "Please check your dashboard.conf file and add the path to your EnTK executable file, and make sure to start an EnTK execution before running dashboard"
			os._exit(1) # terminate

		for x in filesInDir: # for every file in the directory

			z = rs + x # the absolute path to the file
			if os.path.isdir(z): # if the file is a directory, we are in the right place, EnTK logs should be stored in named re.session.user1.user2.num1.num2
				name =  x.split('.') # split up to parse for latest EnTK execution
				if name[0] == "re": # if it starts with re: 
					directories.append(x) # we found an execution

		highestValue = 0
		# find today's (or most recent) executions - the highest numbered ones in the list
		for myDir in directories:
			num = myDir.split('.')[4] 
			if num > highestValue:
				highestValue = num

		directories2 = []
		# place most recent into a separate list
		for myDir in directories: 
			num = myDir.split('.')[4] # get num1 
			if num == highestValue: 
				directories2.append(myDir)

		highestValue = 0
		highestIndex = 0
		idx = 0

		# again, look through this list to find the most recent (or current execution)
		for myDir in directories2: 
			num = myDir.split('.')[5] # get num2
			if num > highestValue:
				highestValue = num
				highestIndex = idx
			idx += 1

		try: # get the directory
			theDirectory = directories2[highestIndex]
		except: 
			return -1 # If the file does not exist

		ret = rs + theDirectory.rstrip() + "/" # the path to directory
		glob.myHandlerDirectory = ret # save it in memory

		return rs + theDirectory.rstrip() + "/" # the path to the directory

