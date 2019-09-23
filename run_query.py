# Script that prints all comments left on pull requests in a repository into a .cvs file for analysis

import requests
import json
import csv
from config import GITHUB_AUTHORIZATION_KEY

headers = {"Authorization": GITHUB_AUTHORIZATION_KEY}

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
       author {{ login }}
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
                 author {{login}}
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
}}
""".format(owner="astropy", name="astropy", pull_number="5")

# Funtion that uses requests.post to make the API call
def run_query(query):
  request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
  if request.status_code == 200:
      return request.json()

def get_comments_from_review_threads(query_data):
  list_of_review_nodes = query_data['data']['repository']['pullRequest']['reviewThreads']['edges']
  list_of_comments = list()
  for node in list_of_review_nodes:
    for comment in node['node']['comments']['nodes']:
      list_of_comments.append(tuple([comment['author']['login'], comment['bodyText']]))

  return list_of_comments

def write_comments_to_csv(list_of_comments):
  with open('review_thread_comments.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file, delimiter=',')
    for comment in list_of_comments:
      writer.writerow([comment])
    csv_file.close()


# Executes the query
query_data = run_query(query)
print(json.dumps(query_data, indent=2))
write_comments_to_csv(get_comments_from_review_threads(query_data))

# Saves one comment and prints to console
# TODO: save all comments to a .cvs file
# outside_index = 0;
# inside_index = 0;

# comment = result["data"]["repository"]["pullRequest"]["reviewThreads"]["edges"][outside_index]["node"]["comments"]["nodes"][inside_index]["bodyText"] # Drill down the dictionary
# print("{} \n".format(comment))
