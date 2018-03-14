from flask import Flask
from flask import request
from flask_cors import CORS
import reader
import webbrowser
from flask import jsonify


glob = reader.GlobalData()
app = Flask(__name__)
CORS(app)
webbrowser.open_new_tab("index.html")
#reader.testReader()

#reader.GlobalData.zero()
#print "zeroed"

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
			#print "dir:", glob.myHandlerDirectory

			if glob.myHandlerDirectory == "": # start new
				#print "starting async"
				#r = pool.apply_async(reader.testReader, (glob,)) # runs in *only* one process
				#r.get(10) 

				reader.testReader(glob)
				url = glob.url
				
				#print "sleep"
   				return url #"<iframe width='1000' height='1000' frameborder='0' scrolling='no' src='" + url + ".embed?width=500&height=1000'> </iframe>"

			else: # ping for data
				url = reader.extend(glob)
				return url #"<iframe width='1000' height='1000' frameborder='0' scrolling='no' src='" + url + ".embed?width=500&height=1000'> </iframe>"
				#print ret
				#print "ping"
				#return jsonify(ret)
			#ret = reader.testReader()
			
		
		else:
			print("invalid: " + req)
	    		return "<p>Invalid Syntax</p>"  

		#return "<iframe width='640' height='480' frameborder='0' scrolling='no' src='" + url + ".embed?width=640&height=480'> </iframe>"
		


