from flask import Flask, request
from flask import jsonify
from flask_cors import CORS, cross_origin
import os



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
cache = {}
urlFile = "tunnelUrl.txt"
@app.route('/', methods=['GET'])
def home():
    return "<h1>ACC randomize app URL Api</h1>"
# A route to return all data.
@app.route('/get_url', methods=['GET'])
def start_championnship():
    if os.path.isfile(urlFile) : 
        f = open(urlFile, "r")
        url = f.read()
        return jsonify({
            "url" : url
            })
    else :
        return jsonify({
            "error" : "no url found"
            })
@app.route('/post_url', methods=['POST'])
def display_result():
    data = request.form
    if "tunnel_url" in data:
        # cache.pop('tunnel_url', None)
        # cache['tunnel_url'] = data['tunnel_url']
        f = open(urlFile, "w")
        f.write(data['tunnel_url'])
        f.close()
        return "success"
    else :
        return "Error. Post data not correct"


if __name__ == "__main__":
    app.run(host='0.0.0.0')