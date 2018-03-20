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
#reader.testReader()


@app.route('/', methods=['GET', 'POST'])
def getPlotlyURL():
	if request.method == 'POST':		
		
	    	req = request.form['plot']
		
		if req == "testReader": # client-side is asking for plot url
			print "got request"
			plot = reader.doGraphing(glob)
			div, script = components(plot)
			return render_template("frame.html", the_div=div, the_script=script)
			#os._exit(1) # tests!!

			if glob.stop == True:
				#shutdown_server()
				os._exit(1)

			if glob.reachedEnd == False:
				print "parse"
				reader.testReader(glob) # do parsing only if not done

			if glob.hasBeenModified == True: # new data appeared
				reader.doGraphing(glob)
				url = glob.url
				print "return new url - performed graphing: " + url
				return url # 

			else: # we have not seen any new data
				url = glob.url

				if url == "": 
					if glob.reachedEnd == True:
						glob.zero()
						print "Your EnTK execution probably crashed. Restart it."
						return "sleep"
					else:
						print "We haven't yet found any meaningful data, please wait for the EnTK execution to continue"
						return "sleep"
				else:
					print "return sleep - no new graphing" 
					return "sleep" # don't refresh iframe on client-side

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
 

			#if glob.myHandlerDirectory == "": # start new
			#print "starting async"
			#r = pool.apply_async(reader.testReader, (glob,)) # runs in *only* one process
			#r.get(10) 

				

			#glob.hasBeenModified = False
				
			 #return "<iframe width='1000' height='1000' frameborder='0' scrolling='no' src='" + url + ".embed?width=500&height=1000'> </iframe>"

			#else: # ping for data
				
			#	url = glob.url
				
			#	return url 
				#"<iframe width='1000' height='1000' frameborder='0' scrolling='no' src='" + url + ".embed?width=500&height=1000'> </iframe>"
				#print ret
				#print "ping"
				#return jsonify(ret)
			#ret = reader.testReader()
			
		


		#return "<iframe width='640' height='480' frameborder='0' scrolling='no' src='" + url + ".embed?width=640&height=480'> </iframe>"
		


