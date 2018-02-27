import csv
import time
import datetime
import plotly.plotly as py
import plotly.graph_objs as go


# https://plot.ly/python/tree-plots/


def pst():   # function for implementing PST plot

	with open('radical.entk.appmanager.0000.prof') as csvfile:
		row_count = 0   # initialize number of rows in file to 0
		csvfile.readline() # skip first line
		csvfile.readline() # skip second line
		timevalues = []     # time array
		pstinfo = []        # pipeline, task, stage values
		for row in csvfile.readlines(): # read every line in the file
			array = row.split(',')  # split row into elements
			first_item = array[0]	 # isolate time element		
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
				time_value = time.strftime("%H:%M:%S", time.localtime(float(first_item)))   #epoch to date format
				timevalues.append(time_value)
				pstinfo_item = pst_item+number_item	#pst information
				pstinfo.append(pstinfo_item)    # tasknumber array			
			else:
				break		

		trace0 = go.Scatter(
			x = timevalues,
			y = pstinfo
		)		

		data = [trace0]
		py.plot(data)



def taskseries():    # function for implementing task series plot

	with open('radical.entk.task_manager.0000-proc.prof') as csvfile:
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
		py.plot(data)


def timeseries():   # function for implementing time series plot
	
	with open('radical.entk.task_manager.0000-proc.prof') as csvfile:
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
		py.plot(data)


## FUNCTION CALLS
#timeseries()  # call timeseries() function
#taskseries()  # call taskseries() function
#pst()         # call pst() function
