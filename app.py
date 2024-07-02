from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB connection setup
client = MongoClient(os.getenv("MONGODB_URI"))

# Define databases for each app
db_zig = client['zig']
db_mdot = client['mdot']
db_ecolane = client['ecolane']
db_goaccess = client['goaccess']

# Define collections within each database
logs_collection_zig = db_zig['logs']
logs_collection_mdot = db_mdot['logs']
logs_collection_ecolane = db_ecolane['logs']
logs_collection_goaccess = db_goaccess['logs']

@app.route("/", methods=['GET'])
def get_hello():
    return 'Hello World!'

@app.route('/logs', methods=['POST'])
def create_log():
    log = request.json
    
    # Check if log is a dictionary and contains required keys
    if not isinstance(log, dict):
        return jsonify({"error": "Invalid input"}), 400
    
    required_keys = ["app_name", "api_type", "api_response", "mobile_type", "input", "user_id", "user_name", "current_location"]
    for key in required_keys:
        if key not in log:
            return jsonify({"error": f"Missing key: {key}"}), 400
    
    # Determine the correct database and collection based on app_name
    app_name = log['app_name']
    if app_name == 'zig':
        logs_collection = logs_collection_zig
    elif app_name == 'mdot':
        logs_collection = logs_collection_mdot
    elif app_name == 'ecolane':
        logs_collection = logs_collection_ecolane
    elif app_name == 'goaccess':
        logs_collection = logs_collection_goaccess
    else:
        return jsonify({"error": "Invalid app_name"}), 400
    
    # Ensure api_response is properly structured
    if isinstance(log['api_response'], str):
        try:
            log['api_response'] = json.loads(log['api_response'].replace("Optional(", "").replace(")", ""))
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format for api_response"}), 400
    
    log['timestamp'] = datetime.now()
    logs_collection.insert_one(log)
    return jsonify({"message": "Log created successfully"}), 201

@app.route('/logs', methods=['GET'])
def get_logs():
    user_id = request.args.get('user_id')
    app_name = request.args.get('app_name')
    date_from_str = request.args.get('from')  # Get 'from' date parameter
    date_to_str = request.args.get('to')      # Get 'to' date parameter
    
    # Convert date strings to datetime objects if provided
    date_from = datetime.strptime(date_from_str, '%Y-%m-%d') if date_from_str else datetime.min
    date_to = datetime.strptime(date_to_str, '%Y-%m-%d') + timedelta(days=1) if date_to_str else datetime.max
    
    # Determine the correct database and collection based on app_name
    if app_name == 'zig':
        logs_collection = logs_collection_zig
    elif app_name == 'mdot':
        logs_collection = logs_collection_mdot
    elif app_name == 'ecolane':
        logs_collection = logs_collection_ecolane
    elif app_name == 'goaccess':
        logs_collection = logs_collection_goaccess
    else:
        return jsonify({"error": "Invalid app_name"}), 400
    
    # Construct query based on user_id and date range
    query = {}
    if user_id:
        query['user_id'] = user_id
    query['timestamp'] = {'$gte': date_from, '$lt': date_to}
    
    # Fetch logs based on the query
    logs = list(logs_collection.find(query))
    
    # Convert ObjectId to string for JSON serialization
    for log in logs:
        log['_id'] = str(log['_id'])
    
    return jsonify(logs), 200

@app.route('/<app_name>/allusers', methods=['GET'])
def get_all_users(app_name):
    user_id = request.args.get('user_id')
    
    # Determine the correct database and collection based on app_name
    if app_name == 'zig':
        logs_collection = logs_collection_zig
    elif app_name == 'mdot':
        logs_collection = logs_collection_mdot
    elif app_name == 'ecolane':
        logs_collection = logs_collection_ecolane
    elif app_name == 'goaccess':
        logs_collection = logs_collection_goaccess
    else:
        return jsonify({"error": "Invalid app_name"}), 400
    
    query = {}
    if user_id:
        query['user_id'] = user_id
    
    # Fetch logs based on the query
    logs = list(logs_collection.find(query))
    
    # Convert ObjectId to string for JSON serialization
    for log in logs:
        log['_id'] = str(log['_id'])
    
    return jsonify(logs), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
