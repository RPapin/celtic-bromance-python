from flask import Flask, request
import json
from os import path, listdir
import os.path
from os.path import isfile, join
import accRandomizer as accR
from flask_cors import CORS, cross_origin
from flask import jsonify
from flask_ngrok import run_with_ngrok
from threading import Timer
import atexit
import subprocess
from pathlib import Path
import tempfile
import time
import requests
from pyngrok import ngrok
from dotenv import dotenv_values

config = dotenv_values(".env")

ngrok.set_auth_token(config['NGROK_AUTH_TOKEN'])

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
run_with_ngrok(app)
# app.config["DEBUG"] = True

onlyfiles = [f for f in listdir(os.getcwd()) if isfile(join(os.getcwd(), f))]
pathData = os.path.join(os.getcwd(), 'data.json')
ngrok_address = ''

@app.route('/', methods=['GET'])
def home():
    return "<h1>ACC randomize app Info Api</h1>"
# A route to return all data.
@app.route('/start_championnship', methods=['GET'])
@cross_origin()
def start_championnship():
    firstRoundSettings = accR.startChampionnship()
    return jsonify(firstRoundSettings)
@app.route('/display_result', methods=['GET'])
def display_result():
    fullResult = accR.checkResult()
    return fullResult
        
@app.route('/launch_server', methods=['GET'])
def launch_server():
    serverStatus = accR.launchServer()
    return jsonify(serverStatus)
@app.route('/reset_championnship', methods=['GET'])
def reset_championnship():
    serverStatus = accR.resetChampionnship()
    return jsonify(serverStatus)

@app.route('/api/v1/resources/books', methods=['GET'])
def api_id():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'id' in request.args:
        id = int(request.args['id'])
    else:
        return "Error: No id field provided. Please specify an id."

def ngrok_url():
    # ngrok_path = str(Path(tempfile.gettempdir(), "ngrok"))
    # executable = str(Path(ngrok_path, "ngrok.exe"))
    # ngrok = subprocess.Popen([executable, 'http', '5000'])
    # atexit.register(ngrok.terminate)
    localhost_url = "http://localhost:4040/api/tunnels"  # Url with tunnel details
    time.sleep(1)
    tunnel_url = requests.get(localhost_url).text  # Get the tunnel information
    j = json.loads(tunnel_url)

    tunnel_url = j['tunnels'][0]['public_url'] + "/" # Do the parsing of the get
    API_ENDPOINT = "https://celtic-bromance-url.herokuapp.com/post_url"
    
    # data to be sent to api
    data = {'tunnel_url':tunnel_url}
    
    # sending post request and saving response as response object
    r = requests.post(url = API_ENDPOINT, data = data)
    pastebin_url = r.text
    print(pastebin_url)

if __name__ == "__main__":
    thread = Timer(5, ngrok_url)
    thread.setDaemon(True)
    thread.start()
    app.run()