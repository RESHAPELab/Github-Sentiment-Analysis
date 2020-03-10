from Config import MONGO_CLIENT_STRING
from pymongo import MongoClient
from collections import defaultdict
import pprint
import csv
import os

client = MongoClient(MONGO_CLIENT_STRING)
db = client['AUTHOR_INFO_BY_REPO']
collections = db.list_collection_names()

# print(db[collections[0]].find_one(sort=[('total_for_repo', -1)]))
# print(db[collections[0]].count_documents( {'total_for_repo' : 1}))

count = defaultdict(int)

for collect in collections:
    print(f"[WORKING] Gathering documents from: {collect}")
    for index in range(db[collect].find_one(sort=[('total_for_repo', -1)])['total_for_repo']):
        amount = db[collect].count_documents({'total_for_repo': index + 1})
        if amount > 0:
            print(f"[WORKING] Gathering count from: {collect} where index: {index}")
            count[index + 1] += amount
    print(count)


save_path = os.path.join(os.getcwd()[:-3], "resources/results.csv")

# Writes results.csv into a resources folder in source directory
with open(save_path, 'w') as csv_file:
    writer = csv.DictWriter(csv_file, count.keys())    
    writer.writeheader()
    writer.writerow(count)

print(count)
