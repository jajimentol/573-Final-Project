from flask import Flask, render_template, request, redirect, url_for, session

from flask_login import LoginManager, login_required, current_user, login_user

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
user_collection = db['userAuth']
app.secret_key = 'memcached'
app.config['SESSION_TYPE'] = 'filesystem'
# collection.insert_one({"name": "aydin"})

@app.route('/')
def index():
	return render_template('login.html')

@app.route('/home')
def landing():
	return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
	request_payload = request.form
	username = request_payload["username"]
	password = request_payload["password"]
	user = user_collection.find_one({"username": username})
	if user:
		is_password_true = user["password"]
		if is_password_true == password:
			session["username"] = username
			print(session["username"])
			return render_template('main_page.html')
	return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():

	if request.method == 'POST':
		request_payload = request.form
		username = request_payload["username"]
		password = request_payload["password"]
		is_username_exists = user_collection.find_one({"username": username})
		if is_username_exists:
			print("username var")
		else:
			user_collection.insert_one({"username": username, "password": password})
			user = user_collection.find_one({"username": username, "password": password})
			print(user)
			print("işlem tamam")
			render_template('main_page.html')
	elif request.method == 'GET':
		return render_template("register.html")



@app.route('/details/saveTag', methods=['POST'])
def save_tag():
	request_payload = request.form
	tag = request_payload["tagbox"]
	# tag'i wikidata'da ara urlini al
	# db'ye kaydet
	# article'a ekle
	print(tag)
	return render_template('main_page.html')

@app.route('/search', methods=['GET'])
def search():
	query =  request.args.get('q').__str__()
	search_result = collection.find({"article_title": {'$regex': query}}).limit(100)
	sr_array = []
	for item in search_result:
		item["authors"] = item["authors"][:-2]
		if len(item["authors"]) > 100:
			item["authors"] = item["authors"][0:100] + "..."
		sr_array.append(item)
	print(session["username"])
	return render_template('search_results.html', data=sr_array)

@app.route('/search/title', methods=['GET'])
def search_in_title():
	query =  request.args.get('title').__str__()
	search_result = collection.find({"article_title": {'$regex': query}}).limit(100)
	sr_array = []
	for item in search_result:
		item["authors"] = item["authors"][:-2]
		if len(item["authors"]) > 100:
			item["authors"] = item["authors"][0:100] + "..."
		sr_array.append(item)
	return render_template('search_results.html', data=sr_array)

@app.route('/search/author', methods=['GET'])
def search_author():
	query =  request.args.get('author').__str__()
	search_result = collection.find({"authors": {'$regex': query}}).limit(100)
	sr_array = []
	for item in search_result:
		item["authors"] = item["authors"][:-2]
		if len(item["authors"]) > 100:
			item["authors"] = item["authors"][0:100] + "..."
		sr_array.append(item)
	return render_template('search_results.html', data=sr_array)

@app.route('/search/abstract', methods=['GET'])
def search_abstract():
	query =  request.args.get('abstract').__str__()
	search_result = collection.find({"abstract_text": {'$regex': query}}).limit(100)
	sr_array = []
	for item in search_result:
		item["authors"] = item["authors"][:-2]
		if len(item["authors"]) > 100:
			item["authors"] = item["authors"][0:100] + "..."
		sr_array.append(item)
	return render_template('search_results.html', data=sr_array)

@app.route('/details/<article_id>', methods=['GET'])
def get_article_detail(article_id):
	search_result = collection.find_one({"id": article_id})
	total_abstact = ""
	abstract_data = search_result["abstract_text"]
	if isinstance(abstract_data, str):
		total_abstact = abstract_data
	elif isinstance(abstract_data, list):
		for item in abstract_data:
			total_abstact += item["#text"] + " "
	elif isinstance(abstract_data, object):
		total_abstact = ''.join(abstract_data["#text"])
	return render_template('article_detail.html', data=search_result, abstract=total_abstact, tagSearch = wikidata_search())

def wikidata_search():
	print("wikidata")