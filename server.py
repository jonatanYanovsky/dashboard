# Written by Jonatan Yanovsky

from flask import Flask, render_template # used for the Flask server
from flask import request # used to parse the frontend graphing request
from flask_cors import CORS # for localhost communication between frontend and backend
import reader # the file that contains graphing and parsing functionality
import webbrowser # a file from GitHub (not my own) that can open a webpage in user's browser
from bokeh.embed import components # for components(), which is used to embed plots in an iframe
import os # for os._exit(1) to terminate execution


glob = reader.GlobalData() # intialize data storage container
app = Flask(__name__) # start the server
CORS(app) # allow communication from server to browser over localhost (same machine). This is acceptable as dashboard is not a web application, but rather a local-running application
webbrowser.open_new_tab("index.html") # open the webpage in the browser: start the frontend


@app.route('/', methods=['GET', 'POST']) # when we recieve a request from frontend
def getPlot(): # our primary controller function
	if request.method == 'POST': # if the request is set to 'POST': a sanity check
		
	    	req = request.form['plot'] # parse request for either 'new' or 'old'
		plotType = request.form['plotType'] # 'current' or 'total'
		
		if glob.plotType == "": # if we have not already set plotType
			glob.plotType = plotType

		# if frontend requests a different plot, then reset parsed data, start over
		if glob.plotType != plotType:
			glob.reset()
			glob.plotType = plotType

		if glob.stop == True: # if user has pressed ^C
			os._exit(1) # terminate

		if glob.reachedEnd == False: # if we have not parsed to the end of the log
			print "parsing"
			returnValue = reader.testReader(glob) # parse
			if returnValue == -1: # if we should avoid plotting (code below)
				print "No EnTK execution data found. Please start your EnTK execution or check your configuration file to point towards the correct directory"
				return "sleep" # respond to frontend that it should not plot

		if glob.hasBeenModified == True: # new data has appeared, plot it
			print "performing graphing"

			plot = reader.doGraphing(glob, "pipeline") # plot the pipeline data
			myDiv1, myScript1 = components(plot) # get components of the plot
			plot = reader.doGraphing(glob, "stage") # do the same for other plots
			myDiv2, myScript2 = components(plot)
			plot = reader.doGraphing(glob, "task")
			myDiv3, myScript3 = components(plot)

			glob.hasBeenModified = False # we are done plotting 
			# embed those plot components into an html file; send it to frontend
			return render_template("frame.html", div1=myDiv1, script1=myScript1, div2=myDiv2, script2=myScript2, div3=myDiv3, script3=myScript3)

		if glob.reachedEnd == True: # we have not seen any new data
			if req == "new": # request from new window, but requesting a plot that has been previously parsed (its data is saved, so we do not need to parse a second time)
				# we do not store plots (yet), so redo graphing
				print "returning old graph" 
				plot = reader.doGraphing(glob, "pipeline")
				myDiv1, myScript1 = components(plot)
				plot = reader.doGraphing(glob, "stage")
				myDiv2, myScript2 = components(plot)
				plot = reader.doGraphing(glob, "task")
				myDiv3, myScript3 = components(plot)

				glob.hasBeenModified = False # we are done plotting 
				return render_template("frame.html", div1=myDiv1, script1=myScript1, div2=myDiv2, script2=myScript2, div3=myDiv3, script3=myScript3)

			else: # existing window, but no need to display new data
				print "We've reached the end of the log file. Your EnTK execution has concluded."
				return "sleep"
		else: # still waiting on EnTK to print new data for parsing
			print "We haven't yet found any meaningful data, please wait for the EnTK execution to continue"
			return "sleep"
		
