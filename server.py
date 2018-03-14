from flask import Flask
from flask import request
from flask_cors import CORS
import reader
import webbrowser
from flask import jsonify
from multiprocessing import Pool  # from multiprocessing.dummy import Pool as ThreadPool 


app = Flask(__name__)
CORS(app)
webbrowser.open_new_tab("index.html")
#reader.testReader()
pool = Pool(1)

@app.route('/', methods=['GET', 'POST'])
def getPlotlyURL():
	if request.method == 'POST':		
		
	    	req = request.form['plot']
		url = ""
		
#	    	if req == "timeseries":
#	    		url = reader.timeseries()
#			
#	    	elif req == "taskseries":
#			url = reader.taskseries()
#		
#		elif req == "pst":
#			url = reader.pst()
#		
		if req == "testReader": # ping for existing data or start new parsing
			#print reader.GlobalData.myHandlerDirectory
			if reader.GlobalData.myHandlerDirectory == "" and reader.GlobalData.reachedEnd != True: # start new
				#print "starting async"
				
				r = pool.apply_async(reader.testReader, ()) # runs in *only* one process
				#print "skipped async"
   				return "sleep"

			else: # ping for data
				ret = reader.getParsedData()
				print "ping"
				return jsonify(ret)
			#ret = reader.testReader()
			
		
		else:
			print("invalid: " + req)
	    		return "<p>Invalid Syntax</p>" 

	   	print(url)

		if url == -1:
			return "<p>Bad code on our end!</p>" 

		#return "<iframe width='640' height='480' frameborder='0' scrolling='no' src='" + url + ".embed?width=640&height=480'> </iframe>"
		


