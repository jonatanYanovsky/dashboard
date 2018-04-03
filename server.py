from flask import Flask, render_template
from flask import request
from flask_cors import CORS
import reader
import webbrowser
from flask import jsonify
from bokeh.embed import components
import os


glob = reader.GlobalData()
app = Flask(__name__)
CORS(app)
webbrowser.open_new_tab("index.html")


@app.route('/', methods=['GET', 'POST'])
def getPlotlyURL():
	if request.method == 'POST':		
		
	    	req = request.form['plot']
		plotType = request.form['plotType']
		
		if glob.plotType == "":
			glob.plotType = plotType

		# if glob is not empty and is not equal to the new pst/plotType, then reset
		if glob.plotType != plotType: # new plot
			glob.reset()
			glob.plotType = plotType

		#if req == "testReader": # client-side is asking for plot url
		if glob.stop == True:
			os._exit(1)

		if glob.reachedEnd == False:
			print "parse"
			returnValue = reader.testReader(glob) # do parsing only if not done
			if returnValue == -2:
				print "No EnTK execution data found. Please start your EnTK execution or check your configuration file to point towards the correct directory"
				return "sleep"

		if glob.hasBeenModified == True: # new data appeared
			print "performed graphing"

			plot = reader.doGraphing(glob, "pipeline")
			myDiv1, myScript1 = components(plot)
			plot = reader.doGraphing(glob, "stage")
			myDiv2, myScript2 = components(plot)
			plot = reader.doGraphing(glob, "task")
			myDiv3, myScript3 = components(plot)

			return render_template("frame.html", div1=myDiv1, script1=myScript1, div2=myDiv2, script2=myScript2, div3=myDiv3, script3=myScript3)

		if glob.reachedEnd == True: # we have not seen any new data
			if req == "new":
				print "returned old graph"
				plot = reader.doGraphing(glob, "pipeline")
				myDiv1, myScript1 = components(plot)
				plot = reader.doGraphing(glob, "stage")
				myDiv2, myScript2 = components(plot)
				plot = reader.doGraphing(glob, "task")
				myDiv3, myScript3 = components(plot)

				return render_template("frame.html", div1=myDiv1, script1=myScript1, div2=myDiv2, script2=myScript2, div3=myDiv3, script3=myScript3)

			else:
				print "We've reached the end of the log file. Your EnTK execution has concluded."
				return "sleep"
		else:
			print "We haven't yet found any meaningful data, please wait for the EnTK execution to continue"
			return "sleep"
		
