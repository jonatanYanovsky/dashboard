# Written by Jonatan Yanovsky

from flask import Flask # used for the Flask server
from flask import request # used to parse the frontend graphing request
from flask_cors import CORS # for localhost communication between frontend and backend
import reader # the file that contains parsing functionality
import webbrowser # a file from GitHub (not my own) that can open a webpage in user's browser
import os # for os._exit(1) to terminate execution
import globalData # the file that contains the "glob" object
import plotting # the file that contains plotting functionality


glob = globalData.GlobalData() # intialize data storage container
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
			if glob.plotType != "visualization": 
				print "performing graphing" 
				return plotting.doGraphing(glob)
			else:
				print "performing visualization" 
				return plotting.doAnalytics(glob)

		if glob.reachedEnd == True: # we have not seen any new data
			if req == "new": # request from new window, but requesting a plot that has been previously parsed (its data is saved, so we do not need to parse a second time)
				# we do not store plots (yet), so redo graphing
				if glob.plotType != "visualization":
					print "returning old graph" 
					return plotting.doGraphing(glob)
				else:
					print "returning old visualization" 
					return plotting.doAnalytics(glob)

			else: # existing window, but no need to display new data
				print "We've reached the end of the log file. Your EnTK execution has concluded."
				return "sleep"
		else: # still waiting on EnTK to print new data for parsing
			print "We haven't yet found any meaningful data, please wait for the EnTK execution to continue"
			return "sleep"
		
