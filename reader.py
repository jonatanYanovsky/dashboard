import csv
import time
import datetime
import plotly.plotly as py
import plotly.graph_objs as go
import os
import linecache
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, FactorRange, ranges, FuncTickFormatter, DataRange1d, SingleIntervalTicker, LinearAxis
from bokeh.models.glyphs import VBar
import pandas as pd
import numpy as np


class GlobalData(object): # a data storage container that is passed to almost every function in reader.py

	def __init__(self):

		self._myHandlerDirectory = "" 
		self._detectedChange = False
		self._lineNum = 0 # used for parsing
		self._reachedEnd = False
		self._hasBeenModified = False
		self._newPlot = True
		self._startTime = 0
		self._limit = 3 # seconds
		self._stop = False # abort

		self._plotType = "" # plot type: total or current
		self._pst = "" # parsing for pipeline stage or task?
	
		self._pipelineStates = [] # data container for [taskID, state]
		self._stageStates = [] # data container for [taskID, state]
		self._taskStates = [] # data container for [taskID, state]

		self._pipelineLastIndex = 0 # used in processing taskStates
		self._stageLastIndex = 0 # used in processing taskStates
		self._taskLastIndex = 0 # used in processing taskStates

		self._pipelineNewIndex = 0 # used in processing taskStates
		self._stageNewIndex = 0 # used in processing taskStates
		self._taskNewIndex = 0 # used in processing taskStates

		self._pipelineStateHistory = []
		self._stageStateHistory = []
		self._taskStateHistory = []

		self._pipelineLastState = {}
		self._stageLastState = {}
		self._taskLastState = {} # dictionary holding last known state of each task

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
		self._taskStatesTotal = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # used for plotting task states
	
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

	def reset(self):
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
	def newPlot(self):
		"""'newPlot' property."""
		return self._newPlot
	@newPlot.setter
	def newPlot(self, value):
		self._newPlot = value

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


class MyHandler(FileSystemEventHandler): # used to detect changes, works in tandem with scanForChanges
	def on_modified(self, event):

		if self.detectedChange == True: # don't print more output than necessary
			return

		if event.src_path == self.myHandlerDirectory + "radical.entk.appmanager.0000.prof":
			print "detected change" 
			self.detectedChange = True

	myHandlerDirectory = "" 
	detectedChange = False


def scanForChanges(glob):

	if glob.stop == True:
		return

	glob.detectedChange = False

	event_handler = MyHandler()
	event_handler.myHandlerDirectory = glob.myHandlerDirectory

	observer = Observer()
	observer.schedule(event_handler, path=glob.myHandlerDirectory, recursive=False)
	observer.start()

	try:
		while event_handler.detectedChange == False:
			time.sleep(1) 
			t = time.time() - glob.startTime
			print "scanning for changes, time = " + str(t)
			
			if t > glob.limit:
				print "time limit reached, returning"
				break

		observer.stop()
		observer.join()
		return

	except KeyboardInterrupt:
		glob.stop = True
		observer.stop()
		observer.join()
		return


def testReader(glob): # prototype for changes-scanning file parsing

	if glob.reachedEnd == True:
		return -1

	glob.startTime = time.time()

	if glob.myHandlerDirectory != "":
		myDir = glob.myHandlerDirectory # continue from last file
		lineCount = glob.lineNum # start at last line number
	else:
		myDir = getConf(glob) # start fresh
		if myDir == -1:
			return -2
		lineCount = 1

	if myDir == -1:
		print("Config file is unreadable")
		return

	myFile = myDir + "radical.entk.appmanager.0000.prof"

	numElements = 1 

	while 1: # read every line in the file
		row = linecache.getline(myFile, lineCount)
		lineCount += 1

		if row == "": # we did NOT encounter the "END", so we must keep scanning until we reach the end
			print "Keep scanning"
			
			scanForChanges(glob)

			t = time.time() - glob.startTime
			print "parser, time: " + str(t)
			
			if t > glob.limit:
				print "time limit reached, returning"
				return

			if glob.stop == True:
				print "aborting"
				glob.reachedEnd = True
				return

			linecache.checkcache(myFile) # used for when the file has been modified
			lineCount -= 1 # go back and reread the line
			continue

		array = row.split(',')  # split row into elements	

		try:
			#epoch = array[0]
			eventName = array[1]
		except:
			eventName = -1

		glob.lineNum = lineCount

		if eventName == "END":
			print "END" # we have reached the last line, we can stop scanning for changes at this point
			glob.reachedEnd = True
			break
		
		try: # gets the cell potentially containing the pipeline, stage, or task
			pstName = array[4]
		except:
			pstName = -1
		
		parts = pstName.split('.')
		nameID = 0

		try:
			name = parts[2] # check for pipeline
			nameID = parts[3]
		except:
			continue
		
		if name == "pipeline":
			if eventName.find("publishing sync ack for obj with state") != -1:
				event = eventName.split() # trim the start of this string
				event = event[-1] # get last element - state description
				
				glob.hasBeenModified = True
				
				eventNum = glob.pipeline_state_values[event]
				
				nameID = int(nameID)
				stateList = [nameID, eventNum] # TODO: can remove nameID to save mem
				glob.pipelineStates.append(stateList)
				glob.pipelineStateHistory.append([nameID, -1, eventNum])
				glob.pipelineNewIndex += 1

		elif name == "stage":
			if eventName.find("publishing sync ack for obj with state") != -1:
				event = eventName.split() # trim the start of this string
				event = event[-1] # get last element - state description
				
				glob.hasBeenModified = True
				
				eventNum = glob.stage_state_values[event]
				
				nameID = int(nameID)
				stateList = [nameID, eventNum] # TODO: can remove nameID to save mem
				glob.stageStates.append(stateList)
				glob.stageStateHistory.append([nameID, -1, eventNum])
				glob.stageNewIndex += 1

		else:
			if eventName.find("publishing sync ack for obj with state") != -1:
				event = eventName.split() # trim the start of this string
				event = event[-1] # get last element - state description
				
				glob.hasBeenModified = True
				
				eventNum = glob.task_state_values[event]
				
				nameID = int(nameID)
				stateList = [nameID, eventNum] # TODO: can remove nameID to save mem
				glob.taskStates.append(stateList)
				glob.taskStateHistory.append([nameID, -1, eventNum])
				glob.taskNewIndex += 1
	
	
def doGraphing(glob, myPST):
	glob.pst = myPST # what we are plotting	
	p = createPlot(glob)
	glob.hasBeenModified = False
	return p


def plotTotal(glob):
	# go through new collected data and add it to the taskStatesTotal (= y axis data) array
	# assume there is new data
	item = []

	if glob.pst == "pipeline":
		while glob.pipelineLastIndex < glob.pipelineNewIndex: # plot-specific algorithm for the SUM of the total number of tasks that have passed through a state
			item = glob.pipelineStates[glob.pipelineLastIndex] 
			glob.pipelineLastIndex += 1
			glob.pipelineStatesTotal[item[1]] += 1 

	elif glob.pst == "stage":
		while glob.stageLastIndex < glob.stageNewIndex: # plot-specific algorithm for the SUM of the total number of tasks that have passed through a state
			item = glob.stageStates[glob.stageLastIndex] 
			glob.stageLastIndex += 1
			glob.stageStatesTotal[item[1]] += 1 

	else:
		while glob.taskLastIndex < glob.taskNewIndex: # plot-specific algorithm for the SUM of the total number of tasks that have passed through a state
			item = glob.taskStates[glob.taskLastIndex] 
			glob.taskLastIndex += 1
			glob.taskStatesTotal[item[1]] += 1 
		

def plotCurrent(glob):

	if glob.pst == "pipeline":
		while glob.pipelineLastIndex < glob.pipelineNewIndex:
			item = glob.pipelineStateHistory[glob.pipelineLastIndex]
			nameID = item[0]
			newState = item[2]

			try:
				oldState = glob.pipelineLastState[nameID] # access existing element
				glob.pipelineLastState[nameID] = newState # update state

				# decrement last state, increment new state
				glob.pipelineStatesTotal[oldState] -= 1
				glob.pipelineStatesTotal[newState] += 1
				
			except:
				glob.pipelineLastState[nameID] = newState # create new element in dictionary
				glob.pipelineStatesTotal[0] += 1 # increment state 0

			glob.pipelineLastIndex += 1

	elif glob.pst == "stage":
		while glob.stageLastIndex < glob.stageNewIndex:
			item = glob.stageStateHistory[glob.stageLastIndex]
			nameID = item[0]
			newState = item[2]

			try:
				oldState = glob.stageLastState[nameID] # access existing element
				glob.stageLastState[nameID] = newState # update state

				# decrement last state, increment new state
				glob.stageStatesTotal[oldState] -= 1
				glob.stageStatesTotal[newState] += 1
				
			except:
				glob.stageLastState[nameID] = newState # create new element in dictionary
				glob.stageStatesTotal[0] += 1 # increment state 0

			glob.stageLastIndex += 1

	else:
		while glob.taskLastIndex < glob.taskNewIndex:
			item = glob.taskStateHistory[glob.taskLastIndex]
			nameID = item[0]
			newState = item[2]

			try:
				oldState = glob.taskLastState[nameID] # access existing element
				glob.taskLastState[nameID] = newState # update state

				# decrement last state, increment new state
				glob.taskStatesTotal[oldState] -= 1
				glob.taskStatesTotal[newState] += 1
				
			except:
				glob.taskLastState[nameID] = newState # create new element in dictionary
				glob.taskStatesTotal[0] += 1 # increment state 0

			glob.taskLastIndex += 1

def createPlot(glob):

	if glob.plotType == "total":
		plotTotal(glob)
	else:
		plotCurrent(glob)

	if glob.pst == "pipeline":
		xx = [1, 2, 3, 4]
		yy = glob.pipelineStatesTotal
		myColor = "orange"
	elif glob.pst == "stage":
		xx = [1, 2, 3, 4, 5]
		yy = glob.stageStatesTotal
		myColor = "green"
	else:
		xx = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
		yy = glob.taskStatesTotal
		myColor = "blue"

	p = figure(plot_height=400, plot_width=800, title=glob.plotType, toolbar_location=None, tools="")
	p.vbar(x=xx, width=0.95, bottom=0, top=yy, color=myColor)
	p.xaxis.visible = False # This axis is broken, so hide it.
	p.yaxis.visible = False # ^^ get rid of minor ticks

	

	ticker = SingleIntervalTicker(interval=1, num_minor_ticks=0)
	xaxis = LinearAxis(ticker=ticker)
	p.add_layout(xaxis, 'below') # add a new x-axis which works properly (no 1.5, 2.5, etc ticks)
	yaxis = LinearAxis(ticker=ticker)
	p.add_layout(yaxis, 'left') # add a new y-axis which works properly (no 1.5, 2.5, etc ticks)

	p.yaxis.axis_label = glob.pst
	p.yaxis.axis_label_text_font_style = "normal"

	p.y_range.start = 0
	p.xgrid.grid_line_color = None
	p.xaxis.major_label_orientation = 1

	p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
	p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks

	if glob.pst == "pipeline":
		theStates = ["", "SCHEDULING", "DONE", "FAILED", "CANCELED", ""]
	elif glob.pst == "stage":
		theStates = ["", "SCHEDULING", "SCHEDULED", "DONE", "FAILED", "CANCELED", ""]
	else:
		theStates = ["", "SCHEDULING", "SCHEDULED", "SUBMITTING", "SUBMITTED", "EXECUTED", "DEQUEUEING", "DEQUEUED", "DONE", "FAILED", "CANCELED", ""]

	label_dict = {}
	for i, s in enumerate(theStates): # convert to dictionary, put this in __init__
		label_dict[i] = s
	
	p.xaxis.formatter = FuncTickFormatter(code="""
	    var labels = %s;
	    return labels[tick];
	""" % label_dict) # convert x-axis-labels into categorical labels: 1 -> "INITIAL", etc

	return p


def getConf(glob):	# get data stored in configuration file, and find the directory that it points to
	with open('dashboard.conf') as conf:
		conf.readline() # skip first line
		row = conf.readline() # get second line, the path to the example/executable, but not the output
		if row == "" or row == None:
			return -1
	
		directories = []
		rs = row.rstrip()

		filesInDir = os.listdir(row.rstrip())
		if len(filesInDir) == 0:
			return -1

		for x in filesInDir: # only the names of the files/directories

			z = rs + x # the absolute path to the directory
			if os.path.isdir(z): #print x
				name =  x.split('.')
				if name[0] == "re":
					directories.append(x)

		highestValue = 0

		for myDir in directories:
			num = myDir.split('.')[4] # get today's executions
			if num > highestValue:
				highestValue = num

		directories2 = []
	
		for myDir in directories:
			num = myDir.split('.')[4] # place largest numbers into another list
			if num == highestValue:
				directories2.append(myDir)

		highestValue = 0
		highestIndex = 0
		idx = 0

		# again, look through this list to find the most recent (or current execution)
		
		for myDir in directories2:
			num = myDir.split('.')[5]
			if num > highestValue:
				highestValue = num
				highestIndex = idx
			idx += 1

		try:
			theDirectory = directories2[highestIndex]
		except: 
			return -1

		ret = rs + theDirectory.rstrip() + "/"
		glob.myHandlerDirectory = ret

		return rs + theDirectory.rstrip() + "/" # the path to the directory

