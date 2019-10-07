'''
Filename: get_repos.py
Author(s): Joshua Kruse and Champ Foronda
Description: Script that runs a query on pull requests in a repository and writes them into a MongoDatabase
'''
import requests
import json
import csv
import pymongo
import time
import datetime
from config import GITHUB_AUTHORIZATION_KEY, MONGO_USER, MONGO_PASSWORD

# Variables
headers = {"Authorization": "token 1d095120a008e8c6f96ccb1a7ffd0bbdf1c59aa2"}
owner_name = "astropy"
repo_name = "astropy"
number_of_pull_requests = 20
comment_range = 100
mongo_client_string = "mongodb+srv://" + MONGO_USER + ":" + MONGO_PASSWORD + "@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority"
database_name = repo_name + "_database"
collection_name = "comments"

# Defines the query to run
def setup_query( query_string ):
    query = f'''

    query {{
       rateLimit{{
        cost
        remaining
        resetAt
       }}
       search(query: {query_string}, type: REPOSITORY, first:2) {{
           pageInfo {{
               endCursor
               hasNextPage
            }}
            repositoryCount
            nodes {{
                ... on Repository {{
                    owner {{
                        login
                    }}
                    name
                    createdAt
                    pushedAt
                    isMirror
                    diskUsage
                    primaryLanguage {{
                        name
                    }}
                    languages {{
                        totalCount
                    }}
                    contributors: mentionableUsers {{
                        totalCount
                    }}
                    watchers {{
                        totalCount
                    }}
                    stargazers {{
                        totalCount
                    }}
                    forks: forkCount
                    issues {{
                        totalCount
                    }}
                    commits: defaultBranchRef {{
                        target {{
                            ... on Commit {{
                                history {{
                                    totalCount
                                }}
                            }}
                        }}
                    }}
                    pullRequests {{
                        totalCount
                    }}
                    branches: refs(refPrefix: "refs/heads/") {{
                        totalCount
                    }}
                    tags: refs(refPrefix: "refs/tags/") {{
                        totalCount
                    }}
                    releases {{
                        totalCount
                    }}
                    description
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

# Builds the query filter string compatible to github
def query_filter( min_stars, max_stars, last_activity, created ):
    date_last_act = datetime.datetime.now() - datetime.timedelta( days=last_activity )
    print(f'{date_last_act:%y-%m-%d}')
    date_created = datetime.datetime.now() - datetime.timedelta( days=created )
    print(f'{date_created:%y-%m-%d}')
    stars = f'{min_stars}..{max_stars}'

    return f'\"is:public archived:false fork:false stars:{stars} pushed:20{date_last_act:%y-%m-%d}..* created:20{date_created:%y-%m-%d}..*\"'

'''

'''

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
#client = pymongo.MongoClient( mongo_client_string )
#db = client[ database_name ]
#db_collection = db[ collection_name ]

min_stars = 0
max_stars = 10000
last_activity = 90 # within the last __ days
created = 364 * 4 # within the last __ days

# create the query filter and setup the query string
query_string = query_filter( min_stars, max_stars, last_activity, created )
print(query_string)
query = setup_query( query_string )

# run the query
query_data = run_query(query)
print(query_data)

# Adds comments to a MongoDB
# client = pymongo.MongoClient("mongodb+srv://jek248:SentimentAnalysis@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority")
# db = client['testing_db']
# db_collection = db['pull_request_comments']
# db_collection.insert_one( list_of_pull_request_comments )
# db_collection.insert_one( list_of_review_thread_comments )
# client.close()
