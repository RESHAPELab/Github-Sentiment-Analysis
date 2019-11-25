from pymongo import MongoClient
from collections import defaultdict
import pprint
import csv

MONGO_CLIENT_STRING = "mongodb+srv://jek248:SentimentAnalysis@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority"

client = MongoClient( MONGO_CLIENT_STRING )

db = client[ 'AUTHOR_INFO_BY_REPO' ]
collections = db.list_collection_names()

print( db[ collections[0] ].find_one(sort=[('total_for_repo', -1)]) )
print(db[ collections[0] ].count_documents( {'total_for_repo' : 1} ))

count = defaultdict(int)

for collect in collections:
    print(f"[WORKING] Gathering documents from: {collect}")
    for index in range( db[collect].find_one(sort=[('total_for_repo', -1)])['total_for_repo'] ):
        amount = db[collect].count_documents({'total_for_repo': index+1})
        if amount > 0:
            print(f"[WORKING] Gathering count from: {collect} where index: {index}")
            count[ index+1 ] += amount
    print( count )

#writing
with open('results.csv', 'w') as f:
    writer = csv.DictWriter(f, count.keys())    
    writer.writeheader()
    writer.writerow( count )

print( count )
