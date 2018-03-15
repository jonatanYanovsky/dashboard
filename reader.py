import csv
import time
import datetime
import plotly.plotly as py
import plotly.graph_objs as go
import os
import linecache
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class GlobalData(object): # for use in MyHandler and scanForChanges
	#@staticmethod
	def zero(self):
		myHandlerDirectory = "" 
		detectedChange = False
		timeData = []
		pipelineData = []
		#newData = []
		lineNum = []
		reachedEnd = False
		url = ""
		hasBeenModified = False
		newPlot = True
		startTime = 0
		limit = 3
		stop = False

	#@staticmethod


	myHandlerDirectory = "" 
	detectedChange = False
	timeData = []
	pipelineData = []
	#newData = []
	lineNum = []
	reachedEnd = False
	url = ""
	hasBeenModified = False
	newPlot = True
	startTime = 0
	limit = 3 # seconds
	stop = False # abort
	


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

	#print "scanning for changes in: " + myDir

	event_handler = MyHandler()
	event_handler.myHandlerDirectory = glob.myHandlerDirectory

	observer = Observer()
	observer.schedule(event_handler, path=glob.myHandlerDirectory, recursive=False)
	observer.start()

	try:
		while event_handler.detectedChange == False:
			time.sleep(1) 
			
			print "scanning for changes, time = "
			t = time.time() - glob.startTime
			print t
			if t > glob.limit:
				print "time limit reached, returning"
				break
		#print "returning"
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

	#print "testReader" #, GlobalData.myHandlerDirectory
	if glob.myHandlerDirectory != "":
		myDir = glob.myHandlerDirectory # continue from last file
		lineCount = glob.lineNum # start at last line number
		glob.newPlot = False # update existing plot
	else:
		myDir = getConf(glob) # start fresh
		lineCount = 1

	#print myDir, glob.myHandlerDirectory
	#print "return"

	if myDir == -1:
		print("Config file is unreadable")
		return

	myFile = myDir + "radical.entk.appmanager.0000.prof"

	#print "opening file: " + myFile

	
	numElements = 1 # TODO: fix x axis


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
			print "parser, time: "
			print t
			
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
		
		if name == "pipeline":
			if nameID == "0000":
				glob.pipelineData.append(eventName)
				myTime = time.strftime("%H:%M:%S", time.localtime(float(epoch)))   #epoch to date format 
				glob.timeData.append(numElements)
				numElements += 1
				glob.hasBeenModified = True
				
	
def doGraphing(glob):
	clean(glob)
	return glob

	if glob.newPlot:
		newPlot(glob)
	else:
		extend(glob)

	clean(glob)


def clean(glob): # don't return a url again until there are new changes
	glob.timeData = []
	glob.pipelineData = []
	glob.hasBeenModified = False


def newPlot(glob):
	trace0 = go.Scatter(
			x = glob.timeData,
			y = glob.pipelineData
		)	

	data = [trace0]
	myUrl = py.plot(data, filename='a', auto_open=False)
	glob.url = myUrl
	return


def extend(glob):
	trace0 = go.Scatter(
			x = glob.timeData,
			y = glob.pipelineData
		)

	data = [trace0]
	py.plot(data, filename='a', auto_open=False, fileopt='extend')
	return

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


def pst():   # function for implementing PST plot
	myFile = getConf()
	if myFile == -1:
		print("Config file is unreadable")
		return

	myFile += "radical.entk.appmanager.0000.prof"

	print myFile

	with open(myFile) as csvfile:

		row_count = 0   # initialize number of rows in file to 0
		csvfile.readline() # skip first line
		csvfile.readline() # skip second line
		startTime = int(round(time.time() * 1000))
		timevalues = []     # time array
		pstinfo = []        # pipeline, task, stage values

		for row in csvfile.readlines(): # read every line in the file
			array = row.split(',')  # split row into elements		
			try:
				event_item = array[1]   # assign event values
			except:
				event_item = -1   # else set to -1
			try:
				pst_item = array[4].split('.')[2]   # isolate pst terms (pipeline, stage, or task)
			except:
				pst_item = -1    # else set to -1
			try:
				number_item = array[4].split('.')[3]   # isolate tasknumber values
			except:
				number_item = -1

			if pst_item != -1: # avoid collecting garbage for ALL elements 
				row_count = row_count + 1    # increment row counter
				currentTime = int(round(time.time() * 1000)) - startTime     # epoch to milliseconds
				timevalues.append(currentTime)
				pstinfo_item = pst_item+number_item	#pst information
				pstinfo.append(pstinfo_item)    # tasknumber array			
			else:
				break		

		trace0 = go.Scatter(
			x = timevalues,
			y = pstinfo
		)		

		data = [trace0]
		return py.plot(data, filename='a', auto_open=False)



def taskseries():    # function for implementing task series plot
	myFile = getConf()
	if myFile == -1:
		print("Config file is unreadable")
		return

	myFile += "radical.entk.task_manager.0000-proc.prof"

	print myFile

	with open(myFile) as csvfile:
		row_count = 0   # initialize number of rows in file to 0
		taskvalues = []
		csvfile.readline() # skip first line
		csvfile.readline() # skip second line
		for row in csvfile.readlines(): # read every line in the file
			array = row.split(',')  # split row into elements
			try:
				task_item = array[4].split('.')[3]   # isolate (task #) from string
			except:
				task_item = -1   # else set to -1
			if task_item != -1: # avoid collecting garbage for ALL elements 
				row_count = row_count + 1    # increment row counter		
				taskvalues.append(task_item)  # append (task #) elements to taskvalues array
			else:
				break

		xvalues = range(1,row_count)    # time values
			
		#for i in range(0, row_count):
		#	print(xvalues[i], xtaskvalues[i]) # debug, 
		#print(len(xvalues), len(yvalues2), len(y1values))

		trace0 = go.Scatter(
			x = xvalues,
			y = taskvalues
		)		

		data = [trace0]
		return py.plot(data, filename='a', auto_open=False)


def timeseries():   # function for implementing time series plot
	myFile = getConf()
	if myFile == -1:
		print("Config file is unreadable")
		return

	myFile += "radical.entk.task_manager.0000-proc.prof"

	print myFile

	with open(myFile) as csvfile:
		row_count = 0   # initialize number of rows in file to 0
		xvalues = []    # x-variable array for time series
		yvalues = []    # y-variable array for time series
		y1values = []   # y-variable array for state series
		csvfile.readline() # skip first line
		csvfile.readline() # skip second line
		for row in csvfile.readlines(): # read every line in the file
			array = row.split(',')  # split row into elements
	       		first_item = array[0]   # get first element in row
			#state_item = array[1]  # get second element in row
			if first_item != '#time' and first_item != "": # avoid collecting garbage for ALL elements
				date_item = time.strftime("%H:%M:%S", time.localtime(float(first_item)))   #epoch to date format 
				row_count = row_count + 1    # increment row counter		
				xvalues.append(date_item)    # append each date_item value (for each row) to array xvalues
				#y1values.append(state_item)  # append state elements to x1values array
			else:
				break

		counter = 1     # height (y-value) for each second (x-value)
		for i in range(0,row_count):    # for each row
			if xvalues[i] == xvalues[i-1]:    # if current xvalue = previous xvalue...
				counter = counter + 1     # ...increment counter to compute number of rows executed per second
			else:
				yvalues.append(counter)   # append counter value to array yvalues (should correspond to each xvalue)
				counter = 1               # set counter back to 1 for next element

		yvalues.append(counter) # don't forget to add the last element

		yvalues.remove(1) # remove first element - the first occurrence of a pesky "1"

		yvalues2 = []
		for y in yvalues: # create multiple copies of this y value for other x values
			for i in range(0, y):
				yvalues2.append(y)

		#for i in range(0, row_count):
		#	print(xvalues[i], xtaskvalues[i]) # debug, 
		#print(len(xvalues), len(yvalues2), len(y1values))

		data = [go.Bar(x=xvalues,y=yvalues2)]
		return py.plot(data, filename='a', auto_open=False)


## FUNCTION CALLS
#timeseries()  # call timeseries() function
#taskseries()  # call taskseries() function
#pst()         # call pst() function
