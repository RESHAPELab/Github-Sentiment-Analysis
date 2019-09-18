# Script that prints all comments left on pull requests in a repository into a .cvs file for analysis

import requests

# REMOVE PERSONAL TOKEN BEFORE PUSHING TO REPO
headers = {"Authorization": "INSERT PERSONAL TOKEN HERE"}

# Funtion that uses requests.post to make the API call
def run_query(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


# The GraphQL query defined as a multi-line string with format
# Needs: owner, repo name, and pull_number
query = """
query{{
 repository(owner: {owner}, name: {name}) {{
   pullRequest: issueOrPullRequest(number: {pull_number}) {{
     __typename
     ... on PullRequest {{
       title
       number
       closed
       author {{
         login
       }}
       bodyText
       comments(first: 10) {{
         edges{{
           node {{
             bodyText
           }}
         }}
       }}
       reviewThreads(first: 100) {{
         edges {{
           node {{
             comments(first: 10) {{
               nodes {{
                 bodyText
                 viewerDidAuthor
                 authorAssociation
               }}
             }}
           }}
         }}
       }}
     }}
   }}
 }}
}}
""".format(owner="astropy", name="astropy", pull_number="5")

# Executes the query
result = run_query(query)

# Saves one comment and prints to console
# TODO: save all comments to a .cvs file
outside_index = 0;
inside_index = 0;

comment = result#["data"]["repository"]["pullRequest"]["reviewThreads"]["edges"][outside_index]["node"]["comments"]["nodes"][inside_index]["bodyText"] # Drill down the dictionary
print("{} \n".format(comment))
