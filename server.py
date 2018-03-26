from flask import Flask, render_template
from flask import request
from flask_cors import CORS
import reader
import webbrowser
from flask import jsonify
from bokeh.embed import components
import os


glob = reader.GlobalData()
#glob.pst = "pipeline"
#glob.plotType = "total"
app = Flask(__name__)
CORS(app)
#webbrowser.open_new_tab("index.html")


@app.route('/', methods=['GET', 'POST'])
def getPlotlyURL():
	if request.method == 'POST':		
		
	    	req = request.form['plot']
		pst = request.form['pst']
		plotType = request.form['plotType']
		
		if glob.pst == "":
			glob.pst = pst
		if glob.plotType == "":
			glob.plotType = plotType
		
		if req == "testReader": # client-side is asking for plot url
			#plot = reader.doGraphing(glob) # for testing
			#div, script = components(plot)
			#return render_template("frame.html", the_div=div, the_script=script)
		
			if glob.stop == True:
				os._exit(1)

			if glob.reachedEnd == False:
				print "parse"
				reader.testReader(glob) # do parsing only if not done

			if glob.hasBeenModified == True: # new data appeared
				print "performed graphing"
				plot = reader.doGraphing(glob)
				div, script = components(plot)
				return render_template("frame.html", the_div=div, the_script=script)

			if glob.reachedEnd == True: # we have not seen any new data
				print "We've reached the end of the log file. Your EnTK execution has concluded."
				return "sleep"
			else:
				print "We haven't yet found any meaningful data, please wait for the EnTK execution to continue"
				return "sleep"
			
		else:
			print "invalid: " + req 
	    		return "<p>Invalid Syntax</p>" 



#	    	if req == "timeseries":
#	    		url = reader.timeseries()
#			
#	    	elif req == "taskseries":
#			url = reader.taskseries()
#		
#		elif req == "pst":
#			url = reader.pst()
#		
 
