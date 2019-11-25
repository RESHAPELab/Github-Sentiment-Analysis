'''
Filename: get_repos.py
Author(s): Joshua Kruse and Champ Foronda
Description: Script that runs a query on repositories on GitHub and writes them into a MongoDatabase
'''

# imports
import requests
import json
import csv
import pymongo
import time
import datetime
from config import GITHUB_AUTHORIZATION_KEY, MONGO_USER, MONGO_PASSWORD

# Variables
headers = {"Authorization": "token 8236a34a73dc4b44c6b969a20cda40c87459cc51"}
mongo_client_string = "mongodb+srv://" + MONGO_USER + ":" + MONGO_PASSWORD + "@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority"
min_stars = 0
max_stars = 10
last_activity = 90 # within the last __ days
created = 364 * 4 # withinthe last __ days
total_pull_num = 0 # amount of pull requests a repository needs
database_name = "repositories"
collection_name = "collect_mnst" + str(min_stars) + "_mxst" + str(max_stars) + "_lsact" + str(last_activity) + "_crtd" + str(created) + "_nmpll" + str(total_pull_num)

# Defines the query to run
def setup_query( query_string, end_cursor ):
    query = f'''
    query {{
       rateLimit{{
        cost
        remaining
        resetAt
       }}
       search(query: "{query_string}", type: REPOSITORY, first:50 {end_cursor}) {{
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
        raise Exception(f'ERROR [{request.status_code}]: Query failed to execute...\nRESPONSE: {request.text}')

# Builds the query filter string compatible to github
def query_filter( min_stars, max_stars, last_activity, created ):
    date_last_act = datetime.datetime.now() - datetime.timedelta( days=last_activity )
    date_created = datetime.datetime.now() - datetime.timedelta( days=created )
    stars = f'{min_stars}..{max_stars}'

    return f'is:public archived:false fork:false stars:{stars} pushed:20{date_last_act:%y-%m-%d}..* created:20{date_created:%y-%m-%d}..*'

# Runs the query and iterates through all pages of repositories
def find_repos( query_string, db_collection, total_pull_num ):

    end_cursor = ""
    end_cursor_string = ""
    hasNextPage = True
    index = 0
    
    while( hasNextPage ):
        query = setup_query( query_string, end_cursor_string )
        result = run_query( query )

        repo_checker( result, db_collection, total_pull_num )

        # if there is a next page, update the endcursor string and continue loop
        if( result["data"]["search"]["pageInfo"]["hasNextPage"] ):
            end_cursor = result["data"]["search"]["pageInfo"]["endCursor"]
            end_cursor_string = f', after:"{end_cursor}"'
        else:
            hasNextPage = False

        index += 1
        time.sleep(1)

# Iterates through all repositories found on each page
# saves valid repositories into a database
def repo_checker( query_data, db_collection, total_pull_num ):

    repository_nodes = query_data["data"]["search"]["nodes"]
    dict_of_repositories = {"repository" : []}
    list_of_repositories = []

    index = 0
    for node in repository_nodes:
        if( is_repo_valid( node, total_pull_num ) ):
            
            list_of_repositories.append( {"name" : node["name"],
                                                        "owner" : node["owner"]["login"],
                                                        "contributers" : node["contributors"]["totalCount"],
                                                        "stars" : node["stargazers"]["totalCount"],
                                                        "forks" : node["forks"],
                                                        "commits" : node["commits"]["target"]["history"]["totalCount"],
                                                        "pullRequests" : node["pullRequests"]["totalCount"]} )
            print( "Repository: " + str(index) )
            index += 1

    db_collection.insert_many( list_of_repositories )

# checks that a repository is valid
# a repo is valid if it has more pull requests than the param
# TODO: more requirments?
# returns a boolean
def is_repo_valid( node, total_pull_num ):
    if( node["pullRequests"]["totalCount"] > total_pull_num ):
        return True
    return False

# create the query filter and setup the query string
query_string = query_filter( min_stars, max_stars, last_activity, created )

# Establishing connection to mongoClient
client = pymongo.MongoClient( mongo_client_string )
database = client[ database_name ]
db_collection = database[ collection_name ]

# run the query
find_repos( query_string, db_collection, total_pull_num )

# Adds comments to a MongoDB
# client = pymongo.MongoClient("mongodb+srv://jek248:SentimentAnalysis@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority")
# db = client['testing_db']
# db_collection = db['pull_request_comments']
# db_collection.insert_one( list_of_pull_request_comments )
# db_collection.insert_one( list_of_review_thread_comments )
# client.close()
