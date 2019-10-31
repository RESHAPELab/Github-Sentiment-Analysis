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
headers = {"Authorization": "token 2997183101a4b7362f1b9bafc1f9216cc859c601"}
mongo_client_string = "mongodb+srv://" + MONGO_USER + ":" + MONGO_PASSWORD + "@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority"
min_stars = 100
max_stars = 1000
last_activity = 90 # within the last __ days
created = 364 * 4 # withinthe last __ days
total_pull_num = 100 # amount of pull requests a repository needs
repo_database_name = "repositories"
repo_collection_name = "collect_mnst" + str(min_stars) + "_mxst" + str(max_stars) + "_lsact" + str(last_activity) + "_crtd" + str(created) + "_nmpll" + str(total_pull_num)
pull_database_name = "comments"
pull_collection_name = "default_collection"
now = datetime.datetime.now()

# Runs the query and iterates through all pages of repositories
def find_repos( ):

    # create the query filter and setup the query string
    query_string = query_filter( min_stars, max_stars, last_activity, created )

    # Establishing connection to mongoClient
    client = pymongo.MongoClient( mongo_client_string )
    repo_database = client[ repo_database_name ]
    db_repo_collection = repo_database[ repo_collection_name ]

    end_cursor = ""
    end_cursor_string = ""
    hasNextPage = True
    index = 0
    
    while( hasNextPage ):
        query = setup_repo_query( query_string, end_cursor_string )
        result = run_query( query )

        repo_checker( result, db_repo_collection, total_pull_num, client, db_repo_collection )

        # if there is a next page, update the endcursor string and continue loop
        if( result["data"]["search"]["pageInfo"]["hasNextPage"] ):
            end_cursor = result["data"]["search"]["pageInfo"]["endCursor"]
            end_cursor_string = f', after:"{end_cursor}"'
        else:
            hasNextPage = False

        index += 1
        time.sleep(.5)

# Builds the query filter string compatible to github
def query_filter( min_stars, max_stars, last_activity, created ):
    date_last_act = datetime.datetime.now() - datetime.timedelta( days=last_activity )
    date_created = datetime.datetime.now() - datetime.timedelta( days=created )
    stars = f'{min_stars}..{max_stars}'

    return f'is:public archived:false fork:false stars:{stars} pushed:20{date_last_act:%y-%m-%d}..* created:20{date_created:%y-%m-%d}..*'

# Funtion that uses requests.post to make the API call
def run_query(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
            raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

# Iterates through all repositories found on each page
# saves valid repositories into a database
def repo_checker( query_data, db_collection, total_pull_num, client, db_repo_collection ):

    repository_nodes = query_data["data"]["search"]["nodes"]
    dict_of_repositories = {"repository" : []}
    list_of_repositories = []

    index = 0
    for node in repository_nodes:
        if( is_repo_valid( node, total_pull_num ) ):

            repo_owner = node['owner']['login']
            repo_name = node['name']

            # Save comments from each valid repo to a database
            get_comments( repo_owner, repo_name, client )
            
            list_of_repositories.append( {"name" : node["name"],
                                                        "owner" : node["owner"]["login"],
                                                        "contributers" : node["contributors"]["totalCount"],
                                                        "stars" : node["stargazers"]["totalCount"],
                                                        "forks" : node["forks"],
                                                        "commits" : node["commits"]["target"]["history"]["totalCount"],
                                                        "pullRequests" : node["pullRequests"]["totalCount"]} )
            print( "Repository: " + str(index) )
            index += 1

    db_repo_collection.insert_many( list_of_repositories )

# checks that a repository is valid
# a repo is valid if it has more pull requests than the param
# TODO: more requirments?
# returns a boolean
def is_repo_valid( node, total_pull_num ):
    if( node["pullRequests"]["totalCount"] > total_pull_num ):
        return True
    return False

# Saves all comments on pull requests in a given repository to a database
# Takes in only the owner of a repository and the name
def get_comments( repo_owner, repo_name, client ):
   
    end_cursor = ""
    end_cursor_string = ""
    hasNextPage = True
    index = 0
    
    while( hasNextPage and index < 4):
        query = setup_pull_query( repo_owner, repo_name, end_cursor_string)
        query_data = run_query( query )

        print(json.dumps(query_data, indent=2))

        pull_request_nodes = query_data['data']['repository']['pullRequests']['nodes']

        index = 0
        for node in pull_request_nodes:
            get_pull_comments( node, client )
            get_review_comments( node, client )
            print("Pull Request: " + str(index) )
            index += 1

        # if there is a next page, update the endcursor string and continue loop
        if( query_data["data"]["repository"]["pullRequests"]["pageInfo"]["hasNextPage"] ):
            end_cursor = query_data["data"]["repository"]["pullRequests"]["pageInfo"]["endCursor"]
            end_cursor_string = f', after:"{end_cursor}"'
        else:
            hasNextPage = False
        index += 1
        time.sleep(.5)

# function that get the comments from a specific pull request
def get_pull_comments( node, client ):
    
    dt_string = now.strftime("%d:%m:%Y_%H:%M:%S")
    database = client[ pull_database_name + dt_string ]
    
    member_collection = database[ "MEMBER" ]
    owner_collection = database[ "OWNER" ]
    collaborator_collection = database[ "COLLABORATOR" ]
    contributor_collection = database[ "CONTRIBUTOR" ]
    first_contributor_collection = database[ "FIRST_TIME_CONTRIBUTOR" ]
    firsttimer_collection = database[ "FIRST_TIMER" ]
    none_collection = database[ "NONE" ]
    all_collection = database[ "ALL" ]
    
    list_of_comments = []

    try:
        comment_edges = node['comments']['edges']

        index = 0
        for edge in comment_edges:
            bodyText = edge['node']['bodyText'].replace( "\n", "" )
            new_comment = {'author' : edge['node']['author']['login'],
                           'bodyText' : bodyText,
                           'authorAssociation' : edge['node']['authorAssociation'] }

            list_of_comments.append( new_comment )

            if( new_comment['authorAssociation'] == "MEMBER" ): member_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "OWNER" ): owner_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "COLLABORATOR" ): collaborator_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "CONTRIBUTOR" ): contributor_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "FIRST_TIME_CONTRIBUTOR" ): first_contributor_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "FIRST_TIMER" ): first_timer_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "NONE" ): none_collection.insert_one( new_comment )

            print("comment")
                
            index += 1
    except TypeError:
        print("type error")

    if( list_of_comments ):
        all_collection.insert_many( list_of_comments )

# function that gets the review comments from a specific pull request
def get_review_comments( node, client ):
    
    dt_string = now.strftime("%d:%m:%Y_%H:%M:%S")
    database = client[ pull_database_name + dt_string ]
    
    member_collection = database[ "MEMBER" ]
    owner_collection = database[ "OWNER" ]
    collaborator_collection = database[ "COLLABORATOR" ]
    contributor_collection = database[ "CONTRIBUTOR" ]
    first_contributor_collection = database[ "FIRST_TIME_CONTRIBUTOR" ]
    firsttimer_collection = database[ "FIRST_TIMER" ]
    none_collection = database[ "NONE" ]
    all_collection = database[ "ALL" ]
    
    list_of_review_comments = []

    review_nodes = node['reviewThreads']['edges']

    try:
        index = 0
        for review_node in review_nodes:
            for comment in review_node['node']['comments']['nodes']:
                bodyText = comment['bodyText'].replace( "\n", "" )
                new_comment = {'author' : comment['author']['login'],
                               'bodyText' : bodyText,
                               'authorAssociation' : comment['authorAssociation'] }
                    

                list_of_review_comments.append( new_comment )

                if( new_comment['authorAssociation'] == "MEMBER" ): member_collection.insert_one( new_comment )
                elif( new_comment['authorAssociation'] == "OWNER" ): owner_collection.insert_one( new_comment )
                elif( new_comment['authorAssociation'] == "COLLABORATOR" ): collaborator_collection.insert_one( new_comment )
                elif( new_comment['authorAssociation'] == "CONTRIBUTOR" ): contributor_collection.insert_one( new_comment )
                elif( new_comment['authorAssociation'] == "FIRST_TIME_CONTRIBUTOR" ): first_contributor_collection.insert_one( new_comment )
                elif( new_comment['authorAssociation'] == "FIRST_TIMER" ): first_timer_collection.insert_one( new_comment )
                elif( new_comment['authorAssociation'] == "NONE" ): none_collection.insert_one( new_comment )

                print("review comment")
                    
                index += 1
    except TypeError:
        print("type error")
                        
    if( list_of_review_comments ):
        all_collection.insert_many( list_of_review_comments )

# function that adds comments to a database based on the author association
def add_to_db( comments, client ):
    database = client[ pull_database_name + dt_string ]
    dt_string = now.strftime("%d/%m/%Y_%H:%M:%S")
    
    member_collection = repo_database[ "MEMBER" ]
    owner_collection = repo_database[ "OWNER" ]
    collaborator_collection = repo_database[ "COLLABORATOR" ]
    contributer_collection = repo_database[ "CONTRIBUTOR" ]
    first_contributer_collection = repo_database[ "FIRST_TIME_CONTRIBUTOR" ]
    firsttimer_collection = repo_database[ "FIRST_TIMER" ]
    none_collection = repo_database[ "FIRST_TIMER" ]

# Defines the query to run
def setup_repo_query( query_string, end_cursor ):
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

# Defines the query to run
def setup_pull_query(owner = "", name = "", endcursor = ""):
    query = f'''
    query {{
  repository (owner:"{owner}", name:"{name}") {{
    name
    pullRequests (first:25 {endcursor})
    {{
      pageInfo {{
        endCursor
        hasNextPage
      }}
      nodes {{
        title
        number
        closed
        author {{
          login
        }}
        authorAssociation
        bodyText
        comments(first:100) {{
          edges {{
            node {{
              author {{
                login
              }}
              authorAssociation
              bodyText
            }}
          }}
        }}
        reviewThreads(first:100) {{
          edges {{
            node {{
              comments(first:100) {{
                nodes {{
                  author {{
                    login
                  }}
                  authorAssociation
                  bodyText
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

# run the query
find_repos( )

# Adds comments to a MongoDB
# client = pymongo.MongoClient("mongodb+srv://jek248:SentimentAnalysis@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority")
# db = client['testing_db']
# db_collection = db['pull_request_comments']
# db_collection.insert_one( list_of_pull_request_comments )
# db_collection.insert_one( list_of_review_thread_comments )
# client.close()
