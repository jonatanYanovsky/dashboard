# Written by Jonatan Yanovsky

import datetime # for converting from epoch to milliseconds
from bokeh.plotting import figure # for plotting
from bokeh.models import FuncTickFormatter, SingleIntervalTicker, LinearAxis # for formatting plots
from bokeh.models.glyphs import VBar # for a vertical bar graph
from bokeh.embed import components # for components(), which is used to embed plots in an iframe
from flask import render_template # used in doGraphing()


"""
Plot 3-in-1 PST plot. Can return an old (existing) plot or create a new one if there is none available (new data to plot has been found).
"""
def doGraphing(glob, old):

	if old == False: # a new plot

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
		html = render_template("frame.html", div1=myDiv1, script1=myScript1, div2=myDiv2, script2=myScript2, div3=myDiv3, script3=myScript3)

		glob.html = html # save the plot
		return html

	else: #return old plot
		return glob.html # restore plot from memory

"""
Process data for 3-in-1 PST plot. This algorithm computes the SUM of the total number of tasks that have passed through each state.
"""
def plotTotal(glob):

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
		

"""
Process data for 3-in-1 PST plot. This algorithm for the number of tasks that ARE in each state.
"""
def plotCurrent(glob):

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

"""
Bokeh plotting functionality. This function gets called three times by doGraphing(), each time creating a plot for one of the three PST plots. Configures plot colors, axes, and titles. In addition, sets the x-axis labels to look as if they are categorical data, although x-axis data is saved as integers instead of strings to save memory.
"""
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


"""
Similar to doGraphing(), but creates two analytics plots.
"""
def doAnalytics(glob, old):

	if old == False: # a new plot

		glob.pst = "executing" # I should probably create a separate variable instead of using pst
		plot = taskDistributionPlot(glob) # processing and graphing
		myDiv1, myScript1 = components(plot) # for embedding

		glob.pst = "total"
		plot = taskDistributionPlot(glob)
		myDiv2, myScript2 = components(plot)

		glob.hasBeenModified = False # we are done plotting 

		# embed those plot components into an html file; send it to frontend
		html = render_template("frame2.html", div1=myDiv1, script1=myScript1, div2=myDiv2, script2=myScript2)

		glob.html = html # save plot
		return html

	else: #return old plot
		return glob.html # restore plot from memory

"""
Process data for 2-in-1 Analytics plot. This algorithm computes the time spent on each task (total + executing).
"""
def taskDistributionAnalytics(glob):
	
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

		glob.taskLastIndex += 1 # move to next new data


"""
helper function that fills in "holes" in the taskDuration list created during taskDistributionAnalytics()
"""
def checkIndices(glob, idx):
	try: # check if the index exists
		glob.taskDuration[idx]
	except: # initialize null elements as 0
		length = len(glob.taskDuration) # e.g. len(0,1,2) = 3. 
		for x in range(length, idx+1): # Add indices (3 to idx) as [0, 0]
			glob.taskDuration.append([0, 0])

	
"""
Plots analytics functions.
"""
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

