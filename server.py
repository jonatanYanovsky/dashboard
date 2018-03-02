from flask import Flask
from flask import request
from flask_cors import CORS
#import importlib
import reader

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
			
	    	#importlib.import_module("reader") # get our graphing code
		
		print(request)
		#print(request.form)
	    	req = request.form['plot']
		url = ""

		#graphsClassInstance = reader.graphing()
		
	    	if req == "timeseries":
	    		url = reader.timeseries()
			
	    	elif req == "taskseries":
			url = reader.taskseries()
		
		elif req == "pst":
			url = reader.pst()
		
		else:
			print("invalid")
	    		return "<p>Invalid Synatax</p>" 

	   	print(url)
		print("<iframe width='640' height='480' frameborder='0' scrolling='no' src='" + url + ".embed?width=640&height=480'> </iframe>")
		return "<iframe width='640' height='480' frameborder='0' scrolling='no' src='" + url + ".embed?width=640&height=480'> </iframe>"
		
