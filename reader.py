import csv
import time
import datetime
import plotly.plotly as py
import plotly.graph_objs as go


with open('radical.entk.task_manager.0000-proc.prof') as csvfile:
	row_count = 0   # initialize number of rows in file to 0
	xvalues = []    # create array called xvalues
	yvalues = []    # create array called yvalues
	csvfile.readline() # skip first line
	for row in csvfile.readlines(): # read every line in the file
		array = row.split(',')  # split row into elements
       		first_item = array[0]   # get first element in row
		if first_item != '#time' and first_item != "": # avoid collecting garbage
			date_item = time.strftime("%H:%M:%S", time.localtime(float(first_item)))   #epoch to date format 
			row_count = row_count + 1    # increment number of rows per iteration
			xvalues.append(date_item)    # append each date_item value (for each row) to array xvalues
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
	#	print(xvalues[i], yvalues2[i]) # debug, 

	data = [go.Bar(x=xvalues,y=yvalues2)]
	py.plot(data)
