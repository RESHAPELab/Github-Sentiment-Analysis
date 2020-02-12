from pymongo import MongoClient
import pprint
import csv
import requests
import json
import time
import datetime

MONGO_CLIENT_STRING = "mongodb+srv://jek248:SentimentAnalysis@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority"

CORE = 101
PERIPHERY = 202

client = MongoClient( MONGO_CLIENT_STRING )

headers = {"Authorization": "token cada15847aab7e8a14fdc38216c5e618e89ed708"}

# Defines the query to run
def setup_query(owner = "", name = "", pull_request_number = 1, comment_range = 10):
    query = f'''
    query {{
        repository(owner: "{owner}", name: "{name}") {{
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
                    authorAssociation
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

# Saves all comments on pull requests in a given repository to a database
# Takes in only the owner of a repository and the name
def mine_comments( repo_owner, repo_name, pr_number, number_of_pr ):

        query = setup_query( repo_owner, repo_name, pr_number )
        query_data = run_query( query )

        # print(json.dumps(query_data, indent=2))

        pull_request = query_data['data']['repository']['pullRequest']

        if( number_of_pr == 1 ): database = client['TESTING_ONE']
        else: database = client['TESTING_MANY']

        print(f"[WORKING] Gathering Comments for PR")
        get_pull_comments( pull_request, database )
        print(f"[WORKING] Gathering Review Comments for PR")
        get_review_comments( pull_request, database )

def get_pull_comments( pull_request, database ):

    member_collection = database[ "MEMBER" ]
    owner_collection = database[ "OWNER" ]
    collaborator_collection = database[ "COLLABORATOR" ]
    contributor_collection = database[ "CONTRIBUTOR" ]
    first_contributor_collection = database[ "FIRST_TIME_CONTRIBUTOR" ]
    firsttimer_collection = database[ "FIRST_TIMER" ]
    none_collection = database[ "NONE" ]
    all_collection = database[ "ALL" ]
    pr_author_collection = database[ "PR_AUTHOR" ]
    
    list_of_comments = []
    pr_author = pull_request['author']['login']

    try:
        comment_edges = pull_request['comments']['edges']

        index = 0
        for edge in comment_edges:
            bodyText = edge['node']['bodyText']
            bodyText = bodyText.replace( "\n", " " )
            bodyText = bodyText.replace( ",", " " )
            new_comment = {'author' : edge['node']['author']['login'],
                           'bodyText' : bodyText,
                           'authorAssociation' : edge['node']['authorAssociation'] }

            list_of_comments.append( new_comment )

            if( new_comment['author'] == pr_author ): pr_author_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "MEMBER" ): member_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "OWNER" ): owner_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "COLLABORATOR" ): collaborator_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "CONTRIBUTOR" ): contributor_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "FIRST_TIME_CONTRIBUTOR" ): first_contributor_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "FIRST_TIMER" ): first_timer_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "NONE" ): none_collection.insert_one( new_comment )

            print("[SUCCESS] Added single comment into database")
                
            index += 1
    except TypeError:
        print("type error")

    if( list_of_comments ):
        all_collection.insert_many( list_of_comments )
        print("[SUCCESS] Added all comments into database \n")

def get_review_comments( pull_request, database ):

    member_collection = database[ "MEMBER" ]
    owner_collection = database[ "OWNER" ]
    collaborator_collection = database[ "COLLABORATOR" ]
    contributor_collection = database[ "CONTRIBUTOR" ]
    first_contributor_collection = database[ "FIRST_TIME_CONTRIBUTOR" ]
    firsttimer_collection = database[ "FIRST_TIMER" ]
    none_collection = database[ "NONE" ]
    all_collection = database[ "ALL" ]
    pr_author_collection = database[ "PR_AUTHOR" ]
    
    list_of_comments = []
    pr_author = pull_request['author']['login']

    try:
        comment_edges = pull_request['comments']['edges']

        index = 0
        for edge in comment_edges:
            bodyText = edge['node']['bodyText']
            bodyText = bodyText.replace( "\n", " " )
            bodyText = bodyText.replace( ",", " " )
            new_comment = {'author' : edge['node']['author']['login'],
                           'bodyText' : bodyText,
                           'authorAssociation' : edge['node']['authorAssociation'] }

            list_of_comments.append( new_comment )

            if( new_comment['author'] == pr_author ): pr_author_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "MEMBER" ): member_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "OWNER" ): owner_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "COLLABORATOR" ): collaborator_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "CONTRIBUTOR" ): contributor_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "FIRST_TIME_CONTRIBUTOR" ): first_contributor_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "FIRST_TIMER" ): first_timer_collection.insert_one( new_comment )
            elif( new_comment['authorAssociation'] == "NONE" ): none_collection.insert_one( new_comment )

            print("[SUCCESS] Added single comment into database ")
                
            index += 1
    except TypeError:
        print("type error")

    if( list_of_comments ):
        all_collection.insert_many( list_of_comments )
    print("[SUCCESS] Added all comments into database \n")

# Funtion that uses requests.post to make the API call
def run_query(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
            raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

repo_db = client[ 'ALL_PRS_BY_REPO' ]
repo_collections = repo_db.list_collection_names()

info_db = client[ 'AUTHOR_INFO_BY_REPO' ]
info_collections = info_db.list_collection_names()

collect = info_collections[2]

#for collect in repo_collections:
if True:

    repo = collect.split("/")
    owner = repo[0]
    repo_name = repo[1]
    
    count = info_db[collect].count_documents())
    print(f"[WORKING] Gathering documents from: {collect}")
    for info_doc in info_db[collect].find():
            author = info_doc['author']
            number_of_prs = info_doc['total_for_repo']
                
            print(f"[WORKING] Gathering PRs for author: {author}")
            for repo_doc in repo_db[collect].find({'author.login':author}):
                    pr_number = repo_doc['number']
                    mine_comments( owner, repo_name, pr_number, number_of_prs )
