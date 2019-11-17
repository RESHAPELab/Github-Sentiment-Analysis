import requests
from pymongo import MongoClient
import json
from Config import GITHUB_AUTHORIZATION_KEY, MONGO_CLIENT_STRING

GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
HTTP_OK_RESPONSE = 200
HEADERS = {"Authorization": GITHUB_AUTHORIZATION_KEY}
VALID_AUTHOR_ASSOCIATIONS = ["OWNER", "MEMBER", "COLLABORATOR", "CONTRIBUTER", "NONE"]

def setup_repo_query(repo_owner: str, repo_name: str, end_cursor: str = "") -> str:
    query = f"""
    query {{
    repository(owner: "{repo_owner}", name: "{repo_name}") {{
        nameWithOwner
        pullRequests(first: 100{end_cursor}) {{
        totalCount
        pageInfo {{
            endCursor
            hasNextPage
        }}
        nodes {{
            number
            author {{
            login
            }}
            authorAssociation
            bodyText
        }}
        }}
    }}
    }}
    """
    return query

def setup_count_total_pr_query(pr_author: str, end_cursor: str="") -> str:
    query = f"""
    query {{
    user(login: "{pr_author}") {{
        login
        pullRequests(first: 100 {end_cursor}) {{
        pageInfo {{
            endCursor
            hasNextPage
        }}
        totalCount
        nodes {{
            number
            baseRepository {{
            nameWithOwner
            }}
            authorAssociation
        }}
        }}
    }}
    }}
    """
    return query

def run_query(query: str) -> json:
    request = requests.post(GITHUB_GRAPHQL_ENDPOINT, json={"query": query},
                            headers=HEADERS)
    if request.status_code == HTTP_OK_RESPONSE:
        return request.json()
    else:
        raise Exception(f'ERROR [{request.status_code}]: Query failed to execute:\nRESPONSE: {request.text}')

def get_data_from_repos_in_db(client: MongoClient) -> dict:
    # Gather collection names frmo repositories database
    repo_db = client["repositories"]
    collection_names = repo_db.list_collection_names()

    # Create a query for each repo
    collection = repo_db["collect_mnst1000_mxst10000_lsact90_crtd1456_nmpll100"]

    # Grabs all the documents in the cursor to avoid a cursor timeout
    records_in_collection = [ document for document in collection.find()]

    for document in records_in_collection:
        # Variables that assist with collecting data
        end_cursor = ""
        end_cursor_string = ""
        has_next_page = True
        list_of_query_data = list()
        pull_request_data = dict()
    
        repo_name = document["name"]
        repo_owner = document["owner"]
        name_with_owner = f"{repo_owner}/{repo_name}"
        pull_request_data[name_with_owner] = list()
        print(f"\nGathering PRs from: {repo_owner}/{repo_name}")

        # Iterates through all the valid pull requests
        while has_next_page:
            query = setup_repo_query(repo_owner, repo_name, end_cursor_string)
            query_data = run_query(query)
            has_next_page = query_data["data"]["repository"]["pullRequests"]["pageInfo"]["hasNextPage"]
            if has_next_page:
                end_cursor = query_data["data"]["repository"]["pullRequests"]["pageInfo"]["endCursor"]
                end_cursor_string = f', after:"{end_cursor}"'

            # Adds the data in a dictionary of lists 
            pull_request_data[name_with_owner].extend(query_data["data"]["repository"]["pullRequests"]["nodes"])
            
        total_count = query_data["data"]["repository"]["pullRequests"]["totalCount"]

        # If we collected the PRs insert it into MongoDB
        if total_count == len(pull_request_data[name_with_owner]):
            print(f"SUCCESS: Gathered {len(pull_request_data[name_with_owner])}/{total_count} from {name_with_owner}")
        else:
            print(f"ERROR: Could not gather all PRs. Gathered only {len(list_of_query_data)}/{total_count}\n")
    
        database = client["AllPRsByRepository"]
        collections = database[name_with_owner]
        collections.insert_many(pull_request_data[name_with_owner])
    
def parse_list_of_prs(query_data: json) -> list:
    pull_requests = query_data["data"]["repository"]["pullRequests"]["nodes"]
    valid_pull_requests = list()
    for pull_request in pull_requests:
        if pull_request["authorAssociation"] in VALID_AUTHOR_ASSOCIATIONS:
            valid_pull_requests.append(pull_request)

    return valid_pull_requests

def get_name_with_owner(query_data: json) -> str:
    return query_data["data"]["repository"]["nameWithOwner"]

def get_pr_author(query_data: json) -> list:
    return query_data["author"]["login"]

def get_pr_number(user_pr_data: json) -> int:
    if user_pr_data is not None:
        return user_pr_data["number"]

def get_author_pr_count(query_data: json, repo: str) -> list:
    user_prs = query_data["data"]["user"]["pullRequests"]
    prs_created = 0
    user_totals = user_prs["totalCount"]
    if user_prs["nodes"] is not None:
        repo_nodes = user_prs["nodes"]

        # Count each pull request contributed too
        for node in repo_nodes:
            if node["baseRepository"]["nameWithOwner"] == repo:
                prs_created += 1

    return [prs_created, user_totals]

def get_author_association(query_data: json, repo: str) -> str:
    user_nodes = query_data["data"]["user"]["pullRequests"]["nodes"]

    for node in user_nodes:
       if node["baseRepository"]["nameWithOwner"] == repo:
           return node["authorAssociation"]

def get_repo_owner(query_data: json) -> str:
    return get_name_with_owner(query_data).split("/")[0]

def get_repo_name(query_data: json) -> str:
    return get_name_with_owner(query_data).split("/")[1]

def main() -> None:    
    # Create queries from repo databse
    client = MongoClient(MONGO_CLIENT_STRING)
    
    # Gather's all the PRs for each Repo in the database
    get_data_from_repos_in_db(client)

    # print("Parsing query data...")
    # for query in queries:
    #     dict_of_repo_authors_data = dict()
    #     list_pr_author_dict = list()
    #     # Gathers the pull request from each PR author in Repository
    #     repo_query_data = run_query(query)
    #     repo_owner = get_repo_owner(repo_query_data)
    #     repo_name = get_repo_name(repo_query_data)

    #     repo_prs_data = parse_list_of_prs(repo_query_data)
    #     length_of_repo_prs_data = int(len(repo_prs_data) / 4)
    #     print(f"Gathering author info from PRs in: {repo_owner}/{repo_name}")
    #     for index in range(0, length_of_repo_prs_data):
    #         pr_author = get_pr_author(repo_prs_data[index])
    #         pr_number = get_pr_number(repo_prs_data[index])
            
    #         # Gathers important from each pull request
    #         pr_author_query = setup_count_total_pr_query(pr_author)
    #         pr_author_data = run_query(pr_author_query)
    #         pr_author_total_count = get_author_pr_count(pr_author_data, f'{repo_owner}/{repo_name}')
    #         pr_author_association = get_author_association(pr_author_data, f'{repo_owner}/{repo_name}')

    #         list_pr_author_dict.append(
    #             {
    #                 "author": pr_author,
    #                 "pr_number": pr_number,
    #                 "association": pr_author_association, 
    #                 "repo_total": pr_author_total_count[0],
    #                 "overall_total": pr_author_total_count[1]
    #             })

    #     dict_of_repo_authors_data[f'{repo_owner}/{repo_name}'] = list_pr_author_dict


    #     database = client["PRAuthorInfoByRepo"]
    #     info = database[f'{repo_owner}/{repo_name}']

    #     if list_pr_author_dict:
    #         print(f'Adding: {repo_owner}/{repo_name} into database')
    #         info.insert_many(list_pr_author_dict)


if __name__ == "__main__":
    main()
