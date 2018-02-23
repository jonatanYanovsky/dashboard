import csv
import time
import datetime
import plotly.plotly as py
import plotly.graph_objs as go

# https://plot.ly/python/tree-plots/


with open('radical.entk.task_manager.0000-proc.prof') as csvfile:
	row_count = 0   # initialize number of rows in file to 0
	xvalues = []    # x-variable array for time series
	yvalues = []    # y-variable array for time series
	y1values = []   # y-variable array for state series
	csvfile.readline() # skip first line
	for row in csvfile.readlines(): # read every line in the file
		array = row.split(',')  # split row into elements
       		first_item = array[0]   # get first element in row
		state_item = array[1]  # get second element in row
		if first_item != '#time' and first_item != "": # avoid collecting garbage for ALL elements, not just first_state
			date_item = time.strftime("%H:%M:%S", time.localtime(float(first_item)))   #epoch to date format 
			row_count = row_count + 1    # increment row counter		
			xvalues.append(date_item)    # append each date_item value (for each row) to array xvalues
			y1values.append(state_item)  # append state elements to x1values array
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
	#print(len(xvalues), len(yvalues2), len(y1values))

	data = [go.Bar(x=xvalues,y=yvalues2)]
	
	

	trace0 = go.Scatter(
		x=xvalues,
		y=y1values,
		mode='markers',
		marker=dict(
			size=[40],
		)
	)
	data1 = [trace0]

	#py.plot(data)
	#py.plot(data1)#, filename='bubblechart-size')  # error, something must be added
