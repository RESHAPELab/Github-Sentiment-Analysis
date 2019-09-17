# An example to get the remaining rate limit using the Github GraphQL API.

import requests

headers = {"Authorization": "token 9ed12876c3de6a527ab64ed3897ef159711b9f72"}


def run_query(query): # A simple function to use requests.post to make the API call. Note the json= section.
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


# The GraphQL query (with a few aditional bits included) itself defined as a multi-line string.
query = """
query{
  repository(owner: astropy, name: astropy) {
    pullRequest: issueOrPullRequest(number:5) {
      __typename
      ... on PullRequest {
        reviewThreads(first: 100) {
          edges {
            node {
              comments(first: 10) {
                nodes {
                  pullRequestReview {
                    id
                  }
                  bodyText
                  viewerDidAuthor
                  authorAssociation
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

result = run_query(query) # Execute the query

outside_index = 0
while True:
    try:

        inside_index = 0
        while True:
            try:
                remaining_rate_limit = result["data"]["repository"]["pullRequest"]["reviewThreads"]["edges"][outside_index]["node"]["comments"]["nodes"][inside_index]["bodyText"] # Drill down the dictionary
                print("Remaining rate limit - {}".format(remaining_rate_limit))
                inside_index += 1
            except IndexError:
                print("do i reach 1")
                break


        outside_index += 1
    except IndexError:
        print("do i reach 2")
        break
