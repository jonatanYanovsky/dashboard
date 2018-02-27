from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def getPlotlyURL():
	print("return")
	return "<iframe width='640' height='480' frameborder='0' scrolling='no' src='https://plot.ly/~rgupta2018/59/.embed?width=640&height=480'> </iframe>"
