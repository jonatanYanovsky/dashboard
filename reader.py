import csv
import time
import datetime
import plotly.plotly as py
import plotly.graph_objs as go


with open('radical.entk.task_manager.0000-proc.prof') as csvfile:
	row_count = 0   # initialize number of rows in file to 0
	xvalues = []    # create array called xvalues
	yvalues = []    # create array called yvalues
	for row in csvfile.readlines(): # read every line in the file
		array = row.split(',')  # split row into elements
       		first_item = array[0]   # get first element in row
		if first_item != '#time' and first_item != "":   #cleanup
			date_item = time.strftime("%H:%M:%S", time.localtime(float(first_item)))   #epoch to date format 
			#print(date_item)  (commented out to display below output)
			row_count = row_count + 1    # increment number of rows per iteration
			xvalues.append(date_item)    # append each date_item value (for each row) to array xvalues

	counter = 1     # number of rows executed per second (y-variable in this case)
	for i in range(1,row_count):    # for each row
		if xvalues[i] == xvalues[i-1]:    # if current xvalue = previous xvalue...
			counter = counter + 1     # ...increment counter to compute number of rows executed per second
		else:
			yvalues.append(counter)   # append counter value to array yvalues (should correspond to each xvalue)
			counter = 1               # set counter back to 1 for next element
	
	data = [go.Bar(x=xvalues,y=yvalues)]
	py.plot(data)

# *** (Note) The above added code works and computes the number of xvalues as 790 (# of rows)
# and the number of yvalues as 45 (varying # of rows executed per time element).
# Terminal directs me to Plot.ly where a bar graph is populated; however, only three xvalues are showing. (Rahul)
