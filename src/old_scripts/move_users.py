from pymongo import MongoClient
from collections import defaultdict
import pprint
import csv

MONGO_CLIENT_STRING = "mongodb+srv://jek248:SentimentAnalysis@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority"

client = MongoClient( MONGO_CLIENT_STRING )

db = client[ 'AUTHOR_INFO_BY_REPO_2' ]
collections = db.list_collection_names()

print( db[ collections[0] ].find_one(sort=[('total_for_repo', -1)]) )
print(db[ collections[0] ].count_documents( {'total_for_repo' : 1} ))

count = defaultdict(int)

'''for collect in collections:
    print(f"[WORKING] Gathering documents from: {collect}")
    for index in range( db[collect].find_one(sort=[('total_for_repo', -1)])['total_for_repo'] ):
        amount = db[collect].count_documents({'total_for_repo': index+1})
        if amount > 0:
            print(f"[WORKING] Gathering count from: {collect} where index: {index}")
            count[ index+1 ] += amount
    print( count )'''

new_db = client[ 'AUTHOR_INFO_BY_PR_NUM' ]
one_collect = new_db[ 'AUTHOR_INFO_BY_ONE_PR' ]
multi_collect = new_db[ 'AUTHOR_INFO_BY_MANY_PR' ]

for collect in new_db.list_collection_names():
        for document in new_db[collect].find():
                bodyText = document['bodyText']
                bodyText = bodyText.replace( "\n", " " )
                bodyText = bodyText.replace( ",", " " )

                new_db[collect].update_one({'author':document['author']},{"$set":{'bodyText':bodyText}})
                print("UPDATED")
'''
for collect in collections:
        print(f"[WORKING] Gathering documents from: {collect}")
        for document in db[collect].find():
                print(f"[SUCCESS] Inserted into DB: {collect}")

                bodyText = document['bodyText']
                bodyText = bodyText.replace( "\n", " " )
                bodyText = bodyText.replace( ",", " " )

                db[collect].update_one({'author':document['author']},{"$set":{'bodyText':bodyText}})
                
                #if( document['total_for_repo'] == 1 ): one_collect.insert_one(document)
                #else: multi_collect.insert_one(document)
'''
