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
headers = {"Authorization": "GITHUB_AUTHORIZATION_KEY"}
owner_name = "astropy"
repo_name = "astropy"
number_of_pull_requests = 20
comment_range = 100
mongo_client_string = "mongodb+srv://" + MONGO_USER + ":" + MONGO_PASSWORD + "@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority"
database_name = repo_name + "_database"
collection_name = "comments"

# Defines the query to run
def setup_query( query_string, end_cursor ):
    query = f'''
    query {{
       rateLimit{{
        cost
        remaining
        resetAt
       }}
       search(query: "{query_string}", type: REPOSITORY, first:2 {end_cursor}) {{
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
                    pullRequests(last:10){{
                        totalCount
                        nodes {{
                            createdAt
                        }}
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

'''
--- Workflow ---
    I. Create query string and build query
    II. run query, iterating through all pages of repos:
        i. iterate through all repositories on each page:
            I. add specific repository to database if it matches specific parameters
    III. Pull comments from each repository in repo_database and save to a new database
'''

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

    return f'is:public archived:false fork:false stars:{stars} pushed:20{date_last_act:%y-%m-%d}..* created:20{date_created:%y-%m-%d}..*'

# Runs the query and iterates through all pages of repositories
def find_repos( query_string, database, db_collection ):

    end_cursor = ""
    end_cursor_string = ""
    hasNextPage = True
    index = 0
    
    while( hasNextPage and index <= 4 ):
        query = setup_query( query_string, end_cursor_string )
        result = run_query( query )
        print(json.dumps(result, indent=2))
        index += 1
        
        if( result["data"]["search"]["pageInfo"]["hasNextPage"] ):
            end_cursor = result["data"]["search"]["pageInfo"]["endCursor"]
            end_cursor_string = f', after:"{end_cursor}"'
        else:
            hasNextPage = False

# Iterates through all repositories found on each page
# saves valid repositories into a database
def repo_checker( query_data, database, db_collection ):
    return false #TODO

# checks that a repository is valid based off of parameters
# returns a boolean
def is_repo_valid( ):
    return false #TODO

min_stars = 1000
max_stars = 10000
last_activity = 90 # within the last __ days
created = 364 * 4 # within the last __ days

# create the query filter and setup the query string
query_string = query_filter( min_stars, max_stars, last_activity, created )
print( query_string )

# Establishing connection to mongoClient
client = pymongo.MongoClient( mongo_client_string )
database = client[ database_name ]
db_collection = database[ collection_name ]

# run the query
find_repos( query_string, database, db_collection )
print( "did i get here" )

# Adds comments to a MongoDB
# client = pymongo.MongoClient("mongodb+srv://jek248:SentimentAnalysis@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority")
# db = client['testing_db']
# db_collection = db['pull_request_comments']
# db_collection.insert_one( list_of_pull_request_comments )
# db_collection.insert_one( list_of_review_thread_comments )
# client.close()
