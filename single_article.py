import requests
import pymongo
import json
from pymongo import MongoClient

import xmltodict

cluster = MongoClient('mongodb+srv://jaji:crazywamp@cluster0.5m64e.mongodb.net/myFirstDatabase?retryWrites=true&w=majority', ssl=True,ssl_cert_reqs='CERT_NONE')
db = cluster['PubMed']
collection = db['articles']

articleIds = collection.find()
for document in articleIds:

    #author_exists = (document['authors'] != "")

    title_in_document = 'article_title' in document
    if title_in_document:
        continue
    else:
        document_id = document['id']
        print(document_id)
        query = {'db': 'pubmed', 'id': document_id, 'rettype': 'abstract'}
        r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", params=query)
        xml_data = r.text
        my_dict = xmltodict.parse(xml_data)
        json_resp = json.dumps(my_dict)
        json_r = json.loads(json_resp)
        article_set = json_r['PubmedArticleSet']
        article_in_data = 'PubmedArticle' in article_set
        if article_in_data:

            article = article_set['PubmedArticle']
            medline_citation = article['MedlineCitation']
            article_data = medline_citation['Article']

            article_title = article_data['ArticleTitle']  ##
            abstract_text = ""
            authors_total = ""
            total_date = ""

            abstract_in_data = 'Abstract' in article_data
            if abstract_in_data:
                abstract_data = article_data['Abstract']
                abstract_text = abstract_data['AbstractText']  ##

            authors_in_article = 'AuthorList' in article_data

            if authors_in_article:
                author_list = article_data['AuthorList']
                authors = author_list['Author']

                if isinstance(authors, list):
                    for item in authors:
                        lastname_in_author = 'LastName' in item
                        collective_name_in_author = 'CollectiveName' in item
                        forename_in_author = 'ForeName' in item
                        if lastname_in_author:
                            lastname = item['LastName']
                            if forename_in_author:
                                forename = item['ForeName']
                            total_name = lastname + " " + forename
                            authors_total += total_name + ", "
                else:
                    lastname_in_author = 'LastName' in authors
                    collective_name_in_author = 'CollectiveName' in authors
                    forename_in_author = 'ForeName' in authors
                    if lastname_in_author:
                        lastname = authors['LastName']
                        if forename_in_author:
                            forename = authors['ForeName']
                        total_name = lastname + " " + forename
                        authors_total += total_name
                    elif collective_name_in_author:
                        name = authors['CollectiveName']
                        authors_total = name

            article_date_in_data = 'ArticleDate' in article_data
            journal_in_article = 'Journal' in article_data
            if article_date_in_data:
                date = article_data['ArticleDate']
                total_date = date['Day'] + "." + date['Month'] + "." + date['Year']
            elif journal_in_article:
                journal = article_data['Journal']
                journal_issue = journal['JournalIssue']
                pub_date = journal_issue['PubDate']
                date_in_pupdate = 'Day' in pub_date
                medline_date_in_pubdate = 'MedlineDate' in pub_date
                if date_in_pupdate:
                    total_date = pub_date['Day'] + "." + pub_date['Month'] + "." + pub_date['Year']
                elif medline_date_in_pubdate:
                    total_date = pub_date['MedlineDate']

            print("document updated id: ", document_id)
            articleData_to_db = {"id": document_id,
                                 "article_title": article_title,
                                 "abstract_text": abstract_text,
                                 "authors": authors_total,
                                 "date": total_date}

            collection.update_one({'id' : document_id}, {"$set" : articleData_to_db}, upsert=True )
        else:
            print("document deleted: ", document_id)
            collection.delete_one({"id" : document_id})
#print(articleData_to_db)

