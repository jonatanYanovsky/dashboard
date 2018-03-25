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


class GlobalData(object): # for use in MyHandler and scanForChanges

	def zero(self):
		self.myHandlerDirectory = "" 
		self.detectedChange = False
		self.timeData = []
		self.pipelineData = []
		self.stateDict = []
		self.states = []
		#newData = []
		self.lineNum = []
		self.reachedEnd = False
		self.url = ""
		self.hasBeenModified = False
		self.newPlot = True
		self.startTime = 0
		self.limit = 3
		self.stop = False




	myHandlerDirectory = "" 
	detectedChange = False
	timeData = []
	pipelineData = []
	stateDict = []
	states = []
	#newData = []
	lineNum = []
	reachedEnd = False
	url = ""
	hasBeenModified = False
	newPlot = True
	startTime = 0
	limit = 3 # seconds
	stop = False # abort
	
	task_state_values = {
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
	taskStates = []
	taskStatesTotal = [0, 0, 0, 0, 0, 0, 0, 0, 0]
	lastIndex = 0
	newIndex = 0
	


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

	glob.startTime = time.time()

	if glob.myHandlerDirectory != "":
		myDir = glob.myHandlerDirectory # continue from last file
		lineCount = glob.lineNum # start at last line number
	else:
		myDir = getConf(glob) # start fresh
		lineCount = 1

	if myDir == -1:
		print("Config file is unreadable")
		return

	myFile = myDir + "radical.entk.appmanager.0000.prof"

	numElements = 1 

	while 1: # read every line in the file
		#print lineCount, myFile
		row = linecache.getline(myFile, lineCount)
		lineCount += 1
		#print "readline: " + row

		if row == "":
			print "Keep scanning"
			# we did NOT encounter the "END", so we must keep scanning until we reach the end
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

		try: # used for breaking the while loop
			epoch = array[0]
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
		
		if name == "task":
			#if nameID == "0000":
			
			if eventName.find("publishing sync ack for obj with state") != -1:
				event = eventName.split()
				event = event[-1]
			if eventName.find("received obj with state") != -1:
				event = eventName.split()
				# trim the start of this string:
				#event = eventName.split()
				event = event[4]
				#print event[-1] # get last element - state description
				
				#glob.timeData.append(numElements)
			glob.hasBeenModified = True
			eventNum = glob.task_state_values[event]
			stateList = [nameID, eventNum]
			glob.taskStates.append(stateList)
			glob.newIndex += 1
	
def doGraphing(glob):
	#print "Plots disabled |\--/||\--/||\--/||\--/|"
	#return
	
	
	

	p = createPlot(glob)
	glob.hasBeenModified = False
	return p


def createPlot(glob):

	# go through new collected data and add it to the taskStatesTotal (= y axis data) array
	# assume there is new data
	item = []
	while glob.lastIndex < glob.newIndex:
		item = glob.taskStates[glob.lastIndex]
		print item
		glob.lastIndex += 1
		glob.taskStatesTotal[item[1]] += 1

	xx = [1, 2, 3, 4, 5, 6, 7, 8, 9]
	yy = glob.taskStatesTotal
	#yy = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] # height
	
	

	p = figure(plot_height=400, plot_width=800, title="testReader", toolbar_location=None, tools="")
	#p.vbar(x=xx, y=yy, left=0.5, right=0.5)
	p.vbar(x=xx, width=0.95, bottom=0, top=yy, color="#CAB2D6")
	p.xaxis.visible = False # This axis is broken, so hide it.
	p.yaxis.visible = False # get rid of minor ticks

	ticker = SingleIntervalTicker(interval=1, num_minor_ticks=0)
	xaxis = LinearAxis(ticker=ticker)
	p.add_layout(xaxis, 'below') # add a new x-axis which works properly (no 1.5, 2.5, etc ticks)
	yaxis = LinearAxis(ticker=ticker)
	p.add_layout(yaxis, 'left') # add a new y-axis which works properly (no 1.5, 2.5, etc ticks)

	p.y_range.start = 0
	p.xgrid.grid_line_color = None
	p.xaxis.major_label_orientation = 1
	#p.min_border_left = 100 # padding to display labels cleanly

	p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
	p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks
	


	states = ["", "SCHEDULING", "SCHEDULED", "SUBMITTING", "SUBMITTED", "EXECUTED", "DEQUEUEING", "DEQUEUED", "DONE", "FAILED", "CANCELED", ""]
	label_dict = {}
	for i, s in enumerate(states): # convert to dictionary, put this in __init__
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

		for x in os.listdir(row.rstrip()): # only the names of the files/directories

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
		except: #  IndexError
			return -1

		ret = rs + theDirectory.rstrip() + "/"
		#print "[" + ret + "][" + glob.myHandlerDirectory + "]"
		#if ret != glob.myHandlerDirectory:
		#	glob.zero() # make preparations for new execution
			#print "zeroed"

		#print "before", glob.myHandlerDirectory
		glob.myHandlerDirectory = ret
		#print "after", glob.myHandlerDirectory

		return rs + theDirectory.rstrip() + "/" # the path to the directory

