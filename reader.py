# Written by Jonatan Yanovsky

import time # used for implementing timeouts while waiting on new data to be written to logs
import os # used in getConf
import linecache # used for parsing individual lines from log files
from watchdog.observers import Observer # object that scans for any changes to log files
from watchdog.events import FileSystemEventHandler # event handler used in tandem with the above import
from bokeh.plotting import figure # for plotting
from bokeh.models import FuncTickFormatter, SingleIntervalTicker, LinearAxis # for formatting plots
from bokeh.models.glyphs import VBar # for a vertical bar graph


class GlobalData(object): # a data storage container that is passed to almost every function in reader.py

	def __init__(self):

		self._myHandlerDirectory = "" # where the log file is located
		self._detectedChange = False # used by Observer (operating system event handler) to check if the log file has been modified
		self._lineNum = 0 # store which line we last parsed, so we can start from that line when we continue parsing
		self._reachedEnd = False # have we parsed to the end of the file
		self._hasBeenModified = False # whether we have found new data
		self._startTime = 0 # used for storing the epoch time at which we start parsing, used by timeouts
		self._limit = 3 # seconds until timeout
		self._stop = False # should we terminate this process: has ^C been pressed

		self._plotType = "" # plot type: total or current
		self._pst = "" # graphing for pipeline stage or task?
	
		self._pipelineStates = [] # data container for [ID, state]
		self._stageStates = []
		self._taskStates = []

		self._pipelineLastIndex = 0 # used in processing event states in graphing
		self._stageLastIndex = 0 
		self._taskLastIndex = 0

		self._pipelineNewIndex = 0 # used in processing event states in graphing
		self._stageNewIndex = 0
		self._taskNewIndex = 0 

		self._pipelineStateHistory = [] # used in processing event states in graphing
		self._stageStateHistory = []
		self._taskStateHistory = []

		self._pipelineLastState = {}
		self._stageLastState = {}
		self._taskLastState = {} # dictionary holding last known state of each pst

		self._task_state_values = { # dictionary to convert from string to int to save mem
			'SCHEDULING': 0,
			'SCHEDULED': 1,
			'SUBMITTING': 2,
			'SUBMITTED': 3,
			'EXECUTED': 4,
			'DEQUEUEING': 5,
			'DEQUEUED': 6,
			'DONE': 7,
			'FAILED': 8,
			'CANCELED': 9
		}
		self._taskStatesTotal = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # used for plotting all the states possible for that pst
	
		self._stage_state_values = {
			'SCHEDULING': 0,
			'SCHEDULED': 1,
			'DONE': 2,
			'FAILED': 3,
			'CANCELED': 4
		}
		self._stageStatesTotal = [0, 0, 0, 0, 0]

		self._pipeline_state_values = {
			'SCHEDULING': 0,
			'DONE': 1,
			'FAILED': 2,
			'CANCELED': 3
		}
		self._pipelineStatesTotal = [0, 0, 0, 0]

	def reset(self): # to restart parsing
		self.__init__()
		print "reset self"

	# setters and getters below

	@property
	def myHandlerDirectory(self):
		"""'myHandlerDirectory' property."""
		return self._myHandlerDirectory
	@myHandlerDirectory.setter
	def myHandlerDirectory(self, value):
		self._myHandlerDirectory = value

	@property
	def detectedChange(self):
		"""'detectedChange' property."""
		return self._detectedChange
	@detectedChange.setter
	def detectedChange(self, value):
		self._detectedChange = value

	@property
	def lineNum(self):
		"""'lineNum' property."""
		return self._lineNum
	@lineNum.setter
	def lineNum(self, value):
		self._lineNum = value

	@property
	def reachedEnd(self):
		"""'reachedEnd' property."""
		return self._reachedEnd
	@reachedEnd.setter
	def reachedEnd(self, value):
		self._reachedEnd = value

	@property
	def hasBeenModified(self):
		"""'hasBeenModified' property."""
		return self._hasBeenModified
	@hasBeenModified.setter
	def hasBeenModified(self, value):
		self._hasBeenModified = value

	@property
	def startTime(self):
		"""'startTime' property."""
		return self._startTime
	@startTime.setter
	def startTime(self, value):
		self._startTime = value

	@property
	def limit(self):
		"""'limit' property."""
		return self._limit
	@limit.setter
	def limit(self, value):
		self._limit = value

	@property
	def stop(self):
		"""'stop' property."""
		return self._stop
	@stop.setter
	def stop(self, value):
		self._stop = value

	@property
	def plotType(self):
		"""'plotType' property."""
		return self._plotType
	@plotType.setter
	def plotType(self, value):
		self._plotType = value

	@property
	def pst(self):
		"""'pst' property."""
		return self._pst
	@pst.setter
	def pst(self, value):
		self._pst = value

	@property
	def pipelineStates(self):
		"""'pipelineStates' property."""
		return self._pipelineStates
	@pipelineStates.setter
	def pipelineStates(self, value):
		self._pipelineStates = value
	def __getitem__(self, idx):
		return self._pipelineStates[idx]
	def __setitem__(self, idx, value):
		self._pipelineStates[idx] = value
	def append(self, val):
		self._pipelineStates = self._pipelineStates + [val]
		return self._pipelineStates  
	def extend(self, val):
		return self._pipelineStates.extend(val)

	@property
	def stageStates(self):
		"""'stageStates' property."""
		return self._stageStates
	@stageStates.setter
	def stageStates(self, value):
		self._stageStates = value
	def __getitem__(self, idx):
		return self._stageStates[idx]
	def __setitem__(self, idx, value):
		self._stageStates[idx] = value
	def append(self, val):
		self._stageStates = self._stageStates + [val]
		return self._stageStates  
	def extend(self, val):
		return self._stageStates.extend(val)

	@property
	def taskStates(self):
		"""'taskStates' property."""
		return self._taskStates
	@taskStates.setter
	def taskStates(self, value):
		self._taskStates = value
	def __getitem__(self, idx):
		return self._taskStates[idx]
	def __setitem__(self, idx, value):
		self._taskStates[idx] = value
	def append(self, val):
		self._taskStates = self._taskStates + [val]
		return self._taskStates  
	def extend(self, val):
		return self._taskStates.extend(val)

	@property
	def pipelineLastIndex(self):
		"""'pipelineLastIndex' property."""
		return self._pipelineLastIndex
	@pipelineLastIndex.setter
	def pipelineLastIndex(self, value):
		self._pipelineLastIndex = value

	@property
	def stageLastIndex(self):
		"""'stageLastIndex' property."""
		return self._stageLastIndex
	@stageLastIndex.setter
	def stageLastIndex(self, value):
		self._stageLastIndex = value

	@property
	def taskLastIndex(self):
		"""'taskLastIndex' property."""
		return self._taskLastIndex
	@taskLastIndex.setter
	def taskLastIndex(self, value):
		self._taskLastIndex = value

	@property
	def pipelineNewIndex(self):
		"""'pipelineNewIndex' property."""
		return self._pipelineNewIndex
	@pipelineNewIndex.setter
	def pipelineNewIndex(self, value):
		self._pipelineNewIndex = value

	@property
	def stageNewIndex(self):
		"""'stageNewIndex' property."""
		return self._stageNewIndex
	@stageNewIndex.setter
	def stageNewIndex(self, value):
		self._stageNewIndex = value

	@property
	def taskNewIndex(self):
		"""'taskNewIndex' property."""
		return self._taskNewIndex
	@taskNewIndex.setter
	def taskNewIndex(self, value):
		self._taskNewIndex = value

	@property
	def pipelineStateHistory(self):
		"""'pipelineStateHistory' property."""
		return self._pipelineStateHistory
	@pipelineStateHistory.setter
	def pipelineStateHistory(self, value):
		self._pipelineStateHistory = value
	def __getitem__(self, idx):
		return self._pipelineStateHistory[idx]
	def __setitem__(self, idx, value):
		self._pipelineStateHistory[idx] = value
	def append(self, val):
		self._pipelineStateHistory = self._pipelineStateHistory + [val]
		return self._pipelineStateHistory  
	def extend(self, val):
		return self._pipelineStateHistory.extend(val)

	@property
	def stageStateHistory(self):
		"""'stageStateHistory' property."""
		return self._stageStateHistory
	@stageStateHistory.setter
	def stageStateHistory(self, value):
		self._stageStateHistory = value
	def __getitem__(self, idx):
		return self._stageStateHistory[idx]
	def __setitem__(self, idx, value):
		self._stageStateHistory[idx] = value
	def append(self, val):
		self._stageStateHistory = self._stageStateHistory + [val]
		return self._stageStateHistory  
	def extend(self, val):
		return self._stageStateHistory.extend(val)

	@property
	def taskStateHistory(self):
		"""'taskStateHistory' property."""
		return self._taskStateHistory
	@taskStateHistory.setter
	def taskStateHistory(self, value):
		self._taskStateHistory = value
	def __getitem__(self, idx):
		return self._taskStateHistory[idx]
	def __setitem__(self, idx, value):
		self._taskStateHistory[idx] = value
	def append(self, val):
		self._taskStateHistory = self._taskStateHistory + [val]
		return self._taskStateHistory  
	def extend(self, val):
		return self._taskStateHistory.extend(val)

	@property
	def pipelineLastState(self):
		"""'pipelineLastState' property."""
		return self._pipelineLastState
	@pipelineLastState.setter
	def pipelineLastState(self, value):
		self._pipelineLastState = value
	def __getitem__(self, idx):
		return self._pipelineLastState[idx]
	def __setitem__(self, idx, value):
		self._pipelineLastState[idx] = value
	def append(self, val):
		self._pipelineLastState = self._pipelineLastState + [val]
		return self._pipelineLastState  
	def extend(self, val):
		return self._pipelineLastState.extend(val)

	@property
	def stageLastState(self):
		"""'stageLastState' property."""
		return self._stageLastState
	@stageLastState.setter
	def stageLastState(self, value):
		self._stageLastState = value
	def __getitem__(self, idx):
		return self._stageLastState[idx]
	def __setitem__(self, idx, value):
		self._stageLastState[idx] = value
	def append(self, val):
		self._stageLastState = self._stageLastState + [val]
		return self._stageLastState  
	def extend(self, val):
		return self._stageLastState.extend(val)

	@property
	def taskLastState(self):
		"""'taskLastState' property."""
		return self._taskLastState
	@taskLastState.setter
	def taskLastState(self, value):
		self._taskLastState = value
	def __getitem__(self, idx):
		return self._taskLastState[idx]
	def __setitem__(self, idx, value):
		self._taskLastState[idx] = value
	def append(self, val):
		self._taskLastState = self._taskLastState + [val]
		return self._taskLastState  
	def extend(self, val):
		return self._taskLastState.extend(val)

	@property
	def task_state_values(self):
		"""'task_state_values' property."""
		return self._task_state_values
	@task_state_values.setter
	def task_state_values(self, value):
		self._task_state_values = value
	def __getitem__(self, idx):
		return self._task_state_values[idx]
	def __setitem__(self, idx, value):
		self._task_state_values[idx] = value

	@property
	def taskStatesTotal(self):
		"""'taskStatesTotal' property."""
		return self._taskStatesTotal
	@taskStatesTotal.setter
	def taskStatesTotal(self, value):
		self._taskStatesTotal = value
	def __getitem__(self, idx):
		return self._taskStatesTotal[idx]
	def __setitem__(self, idx, value):
		self._taskStatesTotal[idx] = value

	@property
	def stage_state_values(self):
		"""'stage_state_values' property."""
		return self._stage_state_values
	@stage_state_values.setter
	def stage_state_values(self, value):
		self._stage_state_values = value
	def __getitem__(self, idx):
		return self._stage_state_values[idx]
	def __setitem__(self, idx, value):
		self._stage_state_values[idx] = value

	@property
	def stageStatesTotal(self):
		"""'stageStatesTotal' property."""
		return self._stageStatesTotal
	@stageStatesTotal.setter
	def stageStatesTotal(self, value):
		self._stageStatesTotal = value
	def __getitem__(self, idx):
		return self._stageStatesTotal[idx]
	def __setitem__(self, idx, value):
		self._stageStatesTotal[idx] = value

	@property
	def pipeline_state_values(self):
		"""'pipeline_state_values' property."""
		return self._pipeline_state_values
	@pipeline_state_values.setter
	def pipeline_state_values(self, value):
		self._pipeline_state_values = value
	def __getitem__(self, idx):
		return self._pipeline_state_values[idx]
	def __setitem__(self, idx, value):
		self._pipeline_state_values[idx] = value

	@property
	def pipelineStatesTotal(self):
		"""'pipelineStatesTotal' property."""
		return self._pipelineStatesTotal
	@pipelineStatesTotal.setter
	def pipelineStatesTotal(self, value):
		self._pipelineStatesTotal = value
	def __getitem__(self, idx):
		return self._pipelineStatesTotal[idx]
	def __setitem__(self, idx, value):
		self._pipelineStatesTotal[idx] = value


class MyHandler(FileSystemEventHandler): # class used to detect changes, works in tandem with scanForChanges
	def on_modified(self, event): # if the Observer has detected a change to a file

		if self.detectedChange == True: # don't print multiple copies of the same line
			return

		if event.src_path == self.myHandlerDirectory + "radical.entk.appmanager.0000.prof": # if a change has occurred at the log file's location
			print "detected change" 
			self.detectedChange = True

	# public variables
	myHandlerDirectory = "" # a copy of the myHandlerDirectory variable used in GlobalData
	detectedChange = False # a copy of the detectedChange variable used in GlobalData


def scanForChanges(glob): # a function that waits for new changes to the log file

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


def testReader(glob): # prototype for changes-scanning file parsing

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
				glob.pipelineStateHistory.append([nameID, -1, eventNum]) # 
				glob.pipelineNewIndex += 1 # more data to process for graphing

		elif name == "stage":
			if eventName.find("publishing sync ack for obj with state") != -1:
				event = eventName.split() 
				event = event[-1]
				
				glob.hasBeenModified = True
				
				eventNum = glob.stage_state_values[event]
				nameID = int(nameID)

				glob.stageStates.append(eventNum)
				glob.stageStateHistory.append([nameID, -1, eventNum])
				glob.stageNewIndex += 1

		else:
			if eventName.find("publishing sync ack for obj with state") != -1:
				event = eventName.split()
				event = event[-1]

				glob.hasBeenModified = True
				
				eventNum = glob.task_state_values[event]
				nameID = int(nameID)

				glob.taskStates.append(eventNum)
				glob.taskStateHistory.append([nameID, -1, eventNum])
				glob.taskNewIndex += 1
	
	
def doGraphing(glob, myPST):
	glob.pst = myPST # what we are plotting	
	p = createPlot(glob)
	return p


def plotTotal(glob):

	# algorithm for the SUM of the total number of tasks that have passed through each state
	if glob.pst == "pipeline":
		while glob.pipelineLastIndex < glob.pipelineNewIndex: # if new data
			item = glob.pipelineStates[glob.pipelineLastIndex] # get the next event from the data structure
			glob.pipelineLastIndex += 1 # move to next saved event
			glob.pipelineStatesTotal[item] += 1 # add to the total count for event: the list containing the y-axis data

	elif glob.pst == "stage":
		while glob.stageLastIndex < glob.stageNewIndex:
			item = glob.stageStates[glob.stageLastIndex] 
			glob.stageLastIndex += 1
			glob.stageStatesTotal[item] += 1 

	else:
		while glob.taskLastIndex < glob.taskNewIndex:
			item = glob.taskStates[glob.taskLastIndex] 
			glob.taskLastIndex += 1
			glob.taskStatesTotal[item] += 1 
		

def plotCurrent(glob):

	# algorithm for the number of tasks that ARE in each state
	if glob.pst == "pipeline":
		while glob.pipelineLastIndex < glob.pipelineNewIndex: # if new data
			item = glob.pipelineStateHistory[glob.pipelineLastIndex] # get the next event from the data structure
			nameID = item[0] # get the pst ID
			newState = item[2] # get the new state for that pst

			try:
				oldState = glob.pipelineLastState[nameID] # get the last state
				glob.pipelineLastState[nameID] = newState # update with the new state
				# in the list containing the y-axis data, decrement the last state, increment new state 
				glob.pipelineStatesTotal[oldState] -= 1
				glob.pipelineStatesTotal[newState] += 1
				
			except: # there was no previous state, this is a newly created pst
				glob.pipelineLastState[nameID] = newState # create new element in state dictionary
				glob.pipelineStatesTotal[0] += 1 # increment state 0

			glob.pipelineLastIndex += 1 # move to next event

	elif glob.pst == "stage":
		while glob.stageLastIndex < glob.stageNewIndex:
			item = glob.stageStateHistory[glob.stageLastIndex]
			nameID = item[0]
			newState = item[2]

			try:
				oldState = glob.stageLastState[nameID]
				glob.stageLastState[nameID] = newState 

				glob.stageStatesTotal[oldState] -= 1
				glob.stageStatesTotal[newState] += 1
				
			except:
				glob.stageLastState[nameID] = newState 
				glob.stageStatesTotal[0] += 1

			glob.stageLastIndex += 1

	else:
		while glob.taskLastIndex < glob.taskNewIndex:
			item = glob.taskStateHistory[glob.taskLastIndex]
			nameID = item[0]
			newState = item[2]

			try:
				oldState = glob.taskLastState[nameID]
				glob.taskLastState[nameID] = newState

				glob.taskStatesTotal[oldState] -= 1
				glob.taskStatesTotal[newState] += 1
				
			except:
				glob.taskLastState[nameID] = newState
				glob.taskStatesTotal[0] += 1

			glob.taskLastIndex += 1

def createPlot(glob):

	if glob.plotType == "total": # which plot do we want
		plotTotal(glob)
	else:
		plotCurrent(glob)

	if glob.pst == "pipeline":
		xx = [1, 2, 3, 4] # set the x-axis range
		yy = glob.pipelineStatesTotal # get the y-axis data
		myColor = "orange" # set the color

	elif glob.pst == "stage":
		xx = [1, 2, 3, 4, 5]
		yy = glob.stageStatesTotal
		myColor = "green"

	else:
		xx = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
		yy = glob.taskStatesTotal
		myColor = "blue"

	p = figure(plot_height=400, plot_width=800, title=glob.plotType, toolbar_location=None, tools="") # make an empty plot
	p.vbar(x=xx, width=0.95, bottom=0, top=yy, color=myColor) # add a vertical bar glyph
	
	p.xaxis.visible = False # This axis contains minor ticks that I cannot remove (1.5, 2.5) which messes up categorical state representation, so hide it.
	p.yaxis.visible = False # same as above

	ticker = SingleIntervalTicker(interval=1, num_minor_ticks=0) # create new axis format

	xaxis = LinearAxis(ticker=ticker) # create the x-axis
	p.add_layout(xaxis, 'below') # add the new x-axis which works properly (no 1.5, 2.5, etc ticks)

	yaxis = LinearAxis(ticker=ticker) # create the y-axis
	p.add_layout(yaxis, 'left') # add the new y-axis which works properly (no 1.5, 2.5, etc ticks)

	p.yaxis.axis_label = glob.pst # y-axis label: total or current
	p.yaxis.axis_label_text_font_style = "normal" # non-italicized

	#p.y_range.start = 0 # start at 
	p.xgrid.grid_line_color = None # no grid color
	p.xaxis.major_label_orientation = 1 # 45 degree sloped x-axis labels

	p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
	p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks

	if glob.pst == "pipeline": # init categorical states
		theStates = ["", "SCHEDULING", "DONE", "FAILED", "CANCELED", ""]
	elif glob.pst == "stage":
		theStates = ["", "SCHEDULING", "SCHEDULED", "DONE", "FAILED", "CANCELED", ""]
	else:
		theStates = ["", "SCHEDULING", "SCHEDULED", "SUBMITTING", "SUBMITTED", "EXECUTED", "DEQUEUEING", "DEQUEUED", "DONE", "FAILED", "CANCELED", ""]

	label_dict = {} # convert above states to dictionary form
	for i, s in enumerate(theStates): 
		label_dict[i] = s
	
	p.xaxis.formatter = FuncTickFormatter(code="""
	    var labels = %s;
	    return labels[tick];
	""" % label_dict) # convert x-axis labels into categorical labels: 3 -> "DONE", etc

	return p


def getConf(glob): # get data stored in configuration file, and find the directory that it points to
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

