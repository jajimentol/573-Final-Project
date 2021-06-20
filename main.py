from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
from flask_login import LoginManager, login_required, current_user, login_user
import hashlib
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
tag_collection = db['tags']

app.secret_key = 'memcached'
app.config['SESSION_TYPE'] = 'filesystem'
# collection.insert_one({"name": "aydin"})

@app.route('/')
def index():
	if "username" in session:
		del session["username"]
	return render_template('login.html')

@app.route('/home')
def landing():
	return render_template('login.html')

@app.route('/main')
def main():
	if "username" not in session:
		return redirect("/")
	return render_template('main_page.html', my_tags= get_user_tags())

@app.route('/login', methods=['POST'])
def login():
	request_payload = request.form
	username = request_payload["username"]
	password = request_payload["password"]
	user = user_collection.find_one({"username": username})
	if user:
		is_password_true = user["password"]
		hashed_pw = hashlib.sha224(password.encode("utf-8")).hexdigest()
		if is_password_true == hashed_pw:
			session["username"] = username
			return redirect("/main")
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
			hashed_pw = hashlib.sha224(password.encode("utf-8")).hexdigest()
			user_collection.insert_one({"username": username, "password": hashed_pw})

			user = user_collection.find_one({"username": username, "password": hashed_pw})
			session["username"] = username
			print("kullanıcı eklendi")
			return redirect("/main")
	elif request.method == 'GET':
		return render_template("register.html")


@app.route('/search', methods=['GET'])
def search():
	query =  request.args.get('q').__str__()
	search_result = collection.find({"article_title": {'$regex': query}}).limit(100)
	sr_array = []
	sr_array = order_search_resutlts(search_result)
	return render_template('search_results.html', data=sr_array, my_tags= get_user_tags())

@app.route('/search/title', methods=['GET'])
def search_in_title():
	query = request.args.get('title').__str__()
	search_result = collection.find({"article_title": {'$regex': query}}).limit(100)
	sr_array = order_search_resutlts(search_result)
	return render_template('search_results.html', data=sr_array, my_tags= get_user_tags())

@app.route('/search/author', methods=['GET'])
def search_author():
	query = request.args.get('author').__str__()
	search_result = collection.find({"authors": {'$regex': query}}).limit(100)
	sr_array = order_search_resutlts(search_result)
	return render_template('search_results.html', data=sr_array, my_tags= get_user_tags())

@app.route('/search/abstract', methods=['GET'])
def search_abstract():
	query = request.args.get('abstract').__str__()
	search_result = collection.find({"abstract_text": {'$regex': query}}).limit(100)
	sr_array = order_search_resutlts(search_result)
	return render_template('search_results.html', data=sr_array, my_tags= get_user_tags())

@app.route('/search/tags', methods=['GET'])
def search_in_tags():
	query = request.args.get('tag').__str__()
	user_tags = tag_collection.find({"username" : session["username"]})

	tag_id = ""
	for item in user_tags:
		if item["custom_name"] == query:
			tag_id = item["id"]
		elif item["label"] == query:
			tag_id = item["id"]

	if tag_id != "":
		search_result = collection.find({"tags": {'$regex': tag_id}}).limit(100)
	else:
		return redirect("/main")

	sr_array = order_search_resutlts(search_result)
	return render_template('search_results.html', data=sr_array, my_tags= get_user_tags())

@app.route('/search/mytags/<tag>', methods=['GET'])
def search_my_tags(tag):
	query = tag
	user_tags = tag_collection.find({"username" : session["username"]})

	tag_id = ""
	for item in user_tags:
		if item["custom_name"] == query:
			tag_id = item["id"]
		elif item["label"] == query:
			tag_id = item["id"]

	if tag_id != "":
		search_result = collection.find({"tags": {'$regex': tag_id}}).limit(100)
	else:
		return redirect("/main")

	sr_array = order_search_resutlts(search_result)
	return render_template('search_results.html', data=sr_array, my_tags= get_user_tags())

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

	is_tags_exist = "tags" in search_result
	tags_list = []
	if is_tags_exist:
		tags = search_result["tags"]
		if isinstance(tags, list):
			for tag_item in tags:
				tag = tag_collection.find_one({"id": tag_item, "username": session["username"]})
				if tag:
					if tag["custom_name"] == "":
						tag["custom_name"] = tag["label"]
					if tag:
						tags_list.append(tag)
		elif isinstance(tags, str):
			tag = tag_collection.find_one({"id": tags, "username": session["username"]})
			if tag:
				if tag["custom_name"] == "":
					tag["custom_name"] = tag["label"]
				tag["custom_name"] = tag["custom_name"]
				tags_list.append(tag)
	return render_template('article_detail.html', data=search_result, abstract=total_abstact, tags=tags_list)

@app.route('/fetch/wikidata/<search>', methods= ['GET'])
def fetch_wikidata(search):
	query = {'action': 'wbsearchentities', 'format': 'json', 'language': 'en', 'type': 'item', 'continue' : '0','search' : search}
	r = requests.get("http://www.wikidata.org/w/api.php", params=query)
	wikidata_search = r.json()["search"]
	if isinstance(wikidata_search, list):
		label_array = []
		for item in wikidata_search:
			label_array.append(item["label"] + " (" + item["description"] + ")")
		return jsonify(label_array)
	else:
		return jsonify(["test"])

@app.route('/details/<article_id>/saveTag', methods=['POST'])
def save_tag_for_article(article_id):
	payload = request.form
	tag_label = payload['tagbox']
	tag_label_array = tag_label.split(' (')
	tag_label = tag_label_array[0]
	custom_tag_label = payload['customTagBox']

	query = {'action': 'wbsearchentities', 'format': 'json', 'language': 'en', 'type': 'item', 'continue': '0',
			 'search': tag_label}
	r = requests.get("http://www.wikidata.org/w/api.php", params=query)
	wikidata_search = r.json()["search"]

	for item in wikidata_search:
		if item['label'] == tag_label:
			tag_collection.insert_one({"id" : item["id"], "label" : item["label"], "custom_name": custom_tag_label, "username" : session["username"], "tagURL" : item["url"] })
			article_in_db = collection.find_one({"id" : article_id})
			is_tags_exist = "tags" in article_in_db
			if is_tags_exist:
				tags = article_in_db["tags"]
				if isinstance(tags, list):
					tags.append(item["id"])
					collection.update_one({"id" : article_id}, {"$set": {"tags": tags}})
				elif isinstance(tags, str):
					tag_array = [tags, item["id"]]
					collection.update_one({"id": article_id}, {"$set": {"tags": tag_array}})
				break
			else:
				collection.update_one({"id": article_id}, {"$set": {"tags": item["id"]}})

	return redirect("/details/"+article_id)
	#return redirect("/main")

def get_user_tags():
	user_tags = tag_collection.find({"username": session["username"]})
	my_tags_list = []
	for item in user_tags:
		if item["custom_name"] != "":
			my_tags_list.append(item["custom_name"])
		elif item["label"] != "":
			my_tags_list.append(item["label"])
	return my_tags_list

def order_search_resutlts(db_cursor):
	return_array = []
	for item in db_cursor:
		item["authors"] = item["authors"][:-2]
		if len(item["authors"]) > 100:
			item["authors"] = item["authors"][0:100] + "..."
		tag_labels = " "
		is_tags_exist = "tags" in item
		if is_tags_exist:
			tags = item["tags"]
			if isinstance(tags, list):
				for tag_item in tags:
					tag = tag_collection.find_one({"id": tag_item, "username": session["username"]})
					print(tag_item)
					if tag:
						if tag["custom_name"] != "":
							tag_labels = tag["custom_name"] + ", " + tag_labels
						else:
							tag_labels = tag["label"] + ", " + tag_labels
					else:
						tag_labels = tag_labels + " "
				tag_labels = tag_labels[:-3]
			elif isinstance(tags, str):
				tag = tag_collection.find_one({"id": tags, "username": session["username"]})
				if tag:
					if tag["custom_name"] != "":
						tag_labels = tag["custom_name"]
					else:
						tag_labels = tag["label"]
			item["tags"] = tag_labels

		return_array.append(item)
	return return_array