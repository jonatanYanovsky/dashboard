from flask import Flask
from flask import request
from flask_cors import CORS
import importlib

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET', 'POST'])
def getPlotlyURL():
	if request.method == 'POST':
		#print("Send iframe")
		#return "<iframe width='640' height='480' frameborder='0' scrolling='no' src='https://plot.ly/~rgupta2018/59/.embed?width=640&height=480'> </iframe>"
	#else:
	    	print("Create Plot")
	    	#if request.form['plot'] != None:
			#if
			
	    	importlib.import_module("reader.py") # get our graphing code
		
	    	req = request.form['plot']
		url = ""
		
	    	if req == "timeseries":
	    		url = timeseries()
			
	    	elif req == "taskseries":
			url = taskseries()
		
		elif req == "pst":
			url = pst()
		
		else:
	    		return "<p>Invalid Synatax</p>" 
	   
		return "<iframe width='640' height='480' frameborder='0' scrolling='no' src='" + url + ".embed?width=640&height=480'> </iframe>"
		
