import requests
import pymongo
from pymongo import MongoClient

import xmltodict

cluster = MongoClient('mongodb+srv://jaji:crazywamp@cluster0.5m64e.mongodb.net/myFirstDatabase?retryWrites=true&w=majority', ssl=True,ssl_cert_reqs='CERT_NONE')
db = cluster['PubMed']
collection = db['articles']

retMax = 1000
retStart = 1000

query = {'db': 'pubmed', 'term': 'muscle','RetMax':retMax,'RetStart':retStart}
r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=query)
xml_data=r.text
my_dict = xmltodict.parse(xml_data)
eSearchResult = my_dict['eSearchResult']
id_list = eSearchResult['IdList']
items = list(id_list.items())
id_array = items[0][1]
#for item in id_array:
    #collection.insert_one({"id": item})
