'''
Filename: run_query.py
Author(s): Joshua Kruse and Champ Foronda
Description: Script that runs a query on pull requests in a repository and writes them into a CSV file
'''
import requests
import json
import csv
import pymongo
import time
from config import GITHUB_AUTHORIZATION_KEY, MONGO_USER, MONGO_PASSWORD

# Variables
headers = {"Authorization": "token 4d949e25e16134830d6af7130b4bdc237dd9facb"}
owner_name = "astropy"
repo_name = "astropy"
number_of_pull_requests = 20
comment_range = 100
mongo_client_string = "mongodb+srv://" + MONGO_USER + ":" + MONGO_PASSWORD + "@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority"
database_name = repo_name + "_database"
collection_name = "comments"

# Defines the query to run
def setup_query(owner = "", name = "", pull_request_number = 1, comment_range = 10):
    query = f'''
    query {{
        repository(owner: {owner}, name: {name}) {{
            pullRequest: issueOrPullRequest(number: {pull_request_number}) {{
            __typename
            ... on PullRequest {{
                title
                number
                closed
                author {{
                    login 
                }}
                bodyText
                comments(first: {comment_range}) {{
                edges {{
                    node {{
                    author {{
                        login
                    }}
                    bodyText
                    }}
                }}
                }}
                reviewThreads(first: 100) {{
                edges {{
                    node {{
                    comments(first: {comment_range}) {{
                        nodes {{
                        author {{
                            login
                        }}
                        bodyText
                        authorAssociation
                        }}
                    }}
                    }}
                }}
                }}
            }}
            }}
        }}
        }}'''
    return query

# Funtion that uses requests.post to make the API call
def run_query(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
            raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

# Function that pulls parents comments from the pull request and saves to dict
def get_comments_from_pull_request(query_data):
    try:
        comment_edges = query_data['data']['repository']['pullRequest']['comments']['edges']
        dict_of_comments = {"comment" : []}
        for edge in comment_edges:
            dict_of_comments["comment"].append( {"author" : edge['node']['author']['login'], "bodyText" : edge['node']['bodyText']} )
            #dict_of_comments.update({"comment" : {"author" : edge['node']['author']['login'], "bodyText" : edge['node']['bodyText']}})

    except KeyError:
        dict_of_comments = {}

    return dict_of_comments

# Function that pulls all reveiw comments from the pull request and saves to dict
def get_comments_from_review_threads(query_data):
    try:
        review_nodes = query_data['data']['repository']['pullRequest']['reviewThreads']['edges']
        dict_of_comments = {"comment" : []}
        for review_node in review_nodes:
            for comment in review_node['node']['comments']['nodes']:
                dict_of_comments["comment"].append( {"author" : comment['author']['login'], "bodyText" : comment['bodyText']} )
                #dict_of_comments.update({"comment" : {"author" : comment['author']['login'], "bodyText" : comment['bodyText']}})
    except KeyError:
        dict_of_comments = {}

    return dict_of_comments


# Establishing connection to mongoClient
client = pymongo.MongoClient( mongo_client_string )
db = client[ database_name ]
db_collection = db[ collection_name ]

# Loop for executing the query
for pull_request_index in range( 1, number_of_pull_requests + 1 ):
    # Executes the query
    query = setup_query( owner_name, repo_name, pull_request_index, comment_range )
    query_data = run_query( query )
    list_of_pull_request_comments = get_comments_from_pull_request( query_data )
    list_of_review_thread_comments = get_comments_from_review_threads( query_data )

    # Inserts into database
    if( list_of_pull_request_comments ):
        db_collection.insert_one( list_of_pull_request_comments )
    elif( list_of_review_thread_comments ):
        db_collection.insert_one( list_of_review_thread_comments )
    else:
        print( "Pull Request - Empty" )
    print( "Pull Request - {}".format( pull_request_index ) )

    time.sleep(.2)
    
# Closing Connection
client.close()

# Executes the query
# query = setup_query("astropy", "astropy", 5, 10)
# query_data = run_query(query)
# list_of_pull_request_comments = get_comments_from_pull_request(query_data)
# list_of_review_thread_comments = get_comments_from_review_threads(query_data)

# Adds comments to a MongoDB
# client = pymongo.MongoClient("mongodb+srv://jek248:SentimentAnalysis@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority")
# db = client['testing_db']
# db_collection = db['pull_request_comments']
# db_collection.insert_one( list_of_pull_request_comments )
# db_collection.insert_one( list_of_review_thread_comments )
# client.close()

