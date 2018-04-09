# Written by Jonatan Yanovsky

import datetime # for converting from epoch to milliseconds
import time # used for implementing timeouts while waiting on new data to be written to logs
import os # used in getConf
import linecache # used for parsing individual lines from log files
from watchdog.observers import Observer # object that scans for any changes to log files
from watchdog.events import FileSystemEventHandler # event handler used in tandem with the above import
from bokeh.plotting import figure # for plotting
from bokeh.models import FuncTickFormatter, SingleIntervalTicker, LinearAxis # for formatting plots
from bokeh.models.glyphs import VBar # for a vertical bar graph
from bokeh.embed import components # for components(), which is used to embed plots in an iframe
from flask import render_template # used in doGraphing()
import globalData # the file that contains the "glob" object


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
	
	
def doGraphing(glob): # plot pst

	glob.pst = "pipeline" # plot the pipeline data
	plot = createPlot(glob)
	myDiv1, myScript1 = components(plot) # get components of the plot

	glob.pst = "stage" # do the same for other plots
	plot = createPlot(glob)
	myDiv2, myScript2 = components(plot)

	glob.pst = "task" 
	plot = createPlot(glob)
	myDiv3, myScript3 = components(plot)

	glob.hasBeenModified = False # we are done plotting 

	# embed those plot components into an html file; send it to frontend
	return render_template("frame.html", div1=myDiv1, script1=myScript1, div2=myDiv2, script2=myScript2, div3=myDiv3, script3=myScript3)


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
			newState = item[1] # get the new state for that pst

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
			newState = item[1]

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
			newState = item[1]

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


def doAnalytics(glob):

	glob.pst = "executing" # I should probably create a separate variable instead of using pst
	plot = taskDistributionPlot(glob) # processing and graphing
	myDiv1, myScript1 = components(plot) # for embedding

	glob.pst = "total"
	plot = taskDistributionPlot(glob)
	myDiv2, myScript2 = components(plot)

	glob.hasBeenModified = False # we are done plotting 

	# embed those plot components into an html file; send it to frontend
	return render_template("frame2.html", div1=myDiv1, script1=myScript1, div2=myDiv2, script2=myScript2)


def taskDistributionAnalytics(glob): # algorithm for the time spent on each task (total + executing)
	
	while glob.taskLastIndex < glob.taskNewIndex: # if new data
		item = glob.taskStateHistory[glob.taskLastIndex] # get the next event from the data structure
		nameID = item[0] # get the pst ID
		newState = item[1] # get the state (the event)
		epoch = item[2] # get the epoch time (only for tasks)

		# total time spent (including waiting for cpu)
		if newState == 0: # if SCHEDULING
			glob.taskStartTimeTotal[nameID] = epoch # save the current time in a dictionary
		if newState == 7 or newState == 8 or newState == 9: # if terminated
			lastTimeVal = glob.taskStartTimeTotal[nameID]
			mySeconds = (epoch - lastTimeVal).total_seconds() # get seconds elapsed
			checkIndices(glob, nameID) # add in empty list items
			item = glob.taskDuration[nameID] # get existing data
			item[0] = mySeconds # store the seconds elapsed between 0 and now
			glob.taskDuration[nameID] = item # save in memory
			print nameID, mySeconds
		
		# just the time spent executing
		if newState == 3: # if SUBMITTED
			glob.taskStartTimeExecution[nameID] = epoch # save the current time in a dictionary
		if newState == 4: # if EXECUTED
			lastTimeVal = glob.taskStartTimeExecution[nameID]
			mySeconds = (epoch - lastTimeVal).total_seconds() # get seconds elapsed
			checkIndices(glob, nameID) # add in empty list items
			item = glob.taskDuration[nameID] # get existing data
			item[1] = mySeconds # store the seconds elapsed between 0 and now
			glob.taskDuration[nameID] = item # save in memory
			print nameID, mySeconds

		glob.taskLastIndex += 1 # move to next new data


def checkIndices(glob, idx): # helper function that fills in "holes" in the taskDuration list
	try: # check if the index exists
		glob.taskDuration[idx]
	except: # initialize null elements as 0
		length = len(glob.taskDuration) # e.g. len(0,1,2) = 3. 
		for x in range(length, idx+1): # Add indices (3 to idx) as [0, 0]
			glob.taskDuration.append([0, 0])

	
def taskDistributionPlot(glob):
	taskDistributionAnalytics(glob)

	yy = []

	if glob.pst == "total":
		myColor = "darkviolet"
		for item in glob.taskDuration: 
			yy.append(item[0]) # create a list of the data stored in taskDuration
	else: # "executing"
		myColor = "navy"
		for item in glob.taskDuration:
			yy.append(item[1])

	xx = range(0, len(yy)) # set the x-axis to have the same number of points as the y-axis

	p = figure(plot_height=400, plot_width=800, title=glob.pst, toolbar_location=None, tools="") # make an empty plot
	p.vbar(x=xx, width=0.95, bottom=0, top=yy, color=myColor) # add a vertical bar glyph
	
	p.xaxis.visible = False # This axis contains minor ticks that I cannot remove (1.5, 2.5) which messes up categorical state representation, so hide it.
	p.yaxis.visible = False # same as above

	ticker = SingleIntervalTicker(interval=1, num_minor_ticks=0) # create new axis format

	xaxis = LinearAxis(ticker=ticker) # create the x-axis
	p.add_layout(xaxis, 'below') # add the new x-axis which works properly (no 1.5, 2.5, etc ticks)

	yaxis = LinearAxis(ticker=ticker) # create the y-axis
	p.add_layout(yaxis, 'left') # add the new y-axis which works properly (no 1.5, 2.5, etc ticks)

	p.xaxis.axis_label = "task ID" # x-axis label
	p.xaxis.axis_label_text_font_style = "normal" # non-italicized

	p.yaxis.axis_label = "time in seconds" # y-axis label: total or current
	p.yaxis.axis_label_text_font_style = "normal" # non-italicized

	p.xgrid.grid_line_color = None # no grid color

	p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
	p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks

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

