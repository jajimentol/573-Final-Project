from flask import Flask, render_template

import pymongo
from pymongo import MongoClient

import json
from bson import json_util

import os
os.environ['FLASK_ENV'] = 'development'

app = Flask(__name__)

cluster = MongoClient('mongodb+srv://jaji:crazywamp@cluster0.5m64e.mongodb.net/myFirstDatabase?retryWrites=true&w=majority', ssl=True,ssl_cert_reqs='CERT_NONE')
db = cluster['testDB']
collection = db['test']
collection.find({ 'title': 'foobar' })
collection.find({"title" : { "$regex": ".*foobar.*" } })

# collection.insert_one({"name": "aydin"})

@app.route('/')
def index():
	return render_template('main_page.html')

@app.route('/names', methods=['GET'])
def get_names():
	all_names = list(collection.find({}))
	return json.dumps(all_names, default=json_util.default)

@app.route('/addName', methods=['POST'])
def add_name():
	request_payload = request.json
	name = request_payload['name']
	existing_name = collection.find({"name":name})

	if existing_name:
		return 'name exists'
	else:
		collection.insert_one({"name":name})
		return 'name added'
