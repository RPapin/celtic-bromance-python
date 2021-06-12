from flask import Flask, request
import json
from flask import jsonify
from flask_cors import CORS, cross_origin



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
cache = {}
@app.route('/', methods=['GET'])
def home():
    return "<h1>ACC randomize app URL Api</h1>"
# A route to return all data.
@app.route('/get_url', methods=['GET'])
def start_championnship():
    if "tunnel_url" in cache:
        return jsonify({
            "url" : cache['tunnel_url']
            })
    else :
        return "no url found"
@app.route('/post_url', methods=['POST'])
def display_result():
    data = request.form
    cache['tunnel_url'] = data['tunnel_url']
    return "success"



if __name__ == "__main__":
    app.run(host='0.0.0.0')