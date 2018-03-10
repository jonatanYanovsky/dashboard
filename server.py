from flask import Flask
from flask import request
from flask_cors import CORS
import reader

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET', 'POST'])
def getPlotlyURL():
	if request.method == 'POST':
		#print(request)
		#print(request.form)
	    	req = request.form['plot']
		url = ""

	    	if req == "timeseries":
	    		url = reader.timeseries()
			
	    	elif req == "taskseries":
			url = reader.taskseries()
		
		elif req == "pst":
			url = reader.pst()
		
		else:
			print("invalid: " + req)
	    		return "<p>Invalid Syntax</p>" 

	   	print(url)

		return "<iframe width='640' height='480' frameborder='0' scrolling='no' src='" + url + ".embed?width=640&height=480'> </iframe>"
		
