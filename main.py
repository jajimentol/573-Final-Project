from flask import Flask, render_template, request

import pymongo
from pymongo import MongoClient

import json
from bson import json_util

import os
import cgi
os.environ['FLASK_ENV'] = 'development'

app = Flask(__name__)

cluster = MongoClient('mongodb+srv://jaji:crazywamp@cluster0.5m64e.mongodb.net/myFirstDatabase?retryWrites=true&w=majority', ssl=True,ssl_cert_reqs='CERT_NONE')
db = cluster['PubMed']
collection = db['articles']

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

@app.route('/search', methods=['GET'])
def search():
	query =  request.args.get('searchbox').__str__()
	search_result = collection.find({"article_title": {'$regex': query}}).limit(10)
	sr_array = []
	for item in search_result:
		sr_array.append(item)
	return render_template('search_results.html', data=sr_array)

@app.route('/details/<article_id>', methods=['GET'])
def get_article_detail(article_id):
	search_result = collection.find_one({"id": article_id})

	#if search_result["abstract_text"] - abstarctları text halinde al
	print(search_result)
	return render_template('article_detail.html', data=search_result)