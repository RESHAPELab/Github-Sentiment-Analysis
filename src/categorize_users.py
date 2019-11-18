import requests
import json
from pymongo import MongoClient
from timeit import default_timer as timer
from Config import GITHUB_AUTHORIZATION_KEY, MONGO_CLIENT_STRING

GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
HTTP_OK_RESPONSE = 200
HEADERS = {"Authorization": GITHUB_AUTHORIZATION_KEY}

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

def setup_user_query(pr_author: str, end_cursor: str="") -> str:
    query = f"""
    query {{
    user(login: "{pr_author}") {{
        login
        pullRequests(first: 100{end_cursor}) {{
        pageInfo {{
            endCursor
            hasNextPage
        }}
        totalCount
        nodes {{
            number
            closed
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
    # Created session to avoid timeout errors
    session = requests.Session()
    request = session.post(GITHUB_GRAPHQL_ENDPOINT, json={"query": query},
                            headers=HEADERS)
    if request.status_code == HTTP_OK_RESPONSE:
        return request.json()
    else:
        raise Exception(f'ERROR [{request.status_code}]: Query failed to execute:\nRESPONSE: {request.text}')

def collect_prs_from_repos_in_db(client: MongoClient) -> None:
    # Gather collection names frmo repositories database
    repo_db = client["repositories"]
    # collection_names = repo_db.list_collection_names()

    # Create a query for each repo
    collection = repo_db["collect_mnst1000_mxst10000_lsact90_crtd1456_nmpll100"]

    # Grabs all the documents in the cursor to avoid a cursor timeout
    documents_in_collection = [document for document in collection.find()]

    for document in documents_in_collection:
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
        print(f"[WORKING] Gathering PRs from: {repo_owner}/{repo_name}")

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
            print(f"[WORKING][SUCCESS] Gathered {len(pull_request_data[name_with_owner])}/{total_count} from {name_with_owner}\n")
        else:
            print(f"[WORKING][ERROR] Could not gather all PRs. Gathered only {len(list_of_query_data)}/{total_count}\n")

        # Inserts all the PRs in MongoDB 
        database = client["ALL_PRS_BY_REPO"]
        collections = database[name_with_owner]
        collections.insert_many(pull_request_data[name_with_owner])

def collect_author_info(client: MongoClient) -> None:
    prs_by_repo_database = client["ALL_PRS_BY_REPO"]
    collection_names = prs_by_repo_database.list_collection_names()

    author_info_db = client["AUTHOR_INFO_BY_REPO"]
    collections_already_mined = author_info_db.list_collection_names()

    collection_names.remove(collections_already_mined)

    # Iterates through each repo
    for collection_name in collection_names:
        collection = prs_by_repo_database[collection_name]
        mined_authors = set()
        author_info = list()

        # Grabs all PRs and stores in a list to avoid cursor timeout
        documents_in_collection = [document for document in collection.find({})]
        for document in documents_in_collection:
            author = document["author"]

            if author is not None:
                author_login = author["login"]
                repo_pr_count = 0

                # Assists with pagination
                end_cursor = ""
                end_cursor_string = ""
                has_next_page = True

                if author_login not in mined_authors: 
                    print(f"[WORKING] Collecting {author_login}'s author info for: {collection_name}...")
                    mined_authors.add(author_login)
                    while has_next_page:
                        # Collects user data based on author_login
                        user_query = setup_user_query(author_login, end_cursor_string)
                        user_data = run_query(user_query)

                        # Checks if there is a valid user
                        if user_data["data"]["user"] is not None and user_data["data"]["user"]["pullRequests"] is not None:
                            pull_requests = user_data["data"]["user"]["pullRequests"]["nodes"]

                            # Counts through all the pull requests
                            if pull_requests is not None:
                                for pull_request in pull_requests:
                                    if pull_request["baseRepository"]["nameWithOwner"] == collection_name:
                                        repo_pr_count += 1
                                        author_association = pull_request["authorAssociation"]

                            # Paginates
                            has_next_page = user_data["data"]["user"]["pullRequests"]["pageInfo"]["hasNextPage"]
                            if has_next_page:
                                end_cursor = user_data["data"]["user"]["pullRequests"]["pageInfo"]["endCursor"]
                                end_cursor_string = f', after:"{end_cursor}"'
                            else:
                                total_pr_count = user_data["data"]["user"]["pullRequests"]["totalCount"]
                                author_info.append({
                                    "author": author_login,
                                    "association": author_association,
                                    "total_for_repo": repo_pr_count,
                                    "total_overall": total_pr_count
                                })
                                print(f'[WORKING] Finished collecting info from {author_login}')
                        else:
                            print(f'[WORKING] {author_login} is not a valid user')
                            has_next_page = False
                
                    print(f"[WORKING] {author_login} contributed {repo_pr_count}/{total_pr_count} pull requests to: {collection_name}\n") 

        # Inserts author info into MongoDB
        collections = author_info_db[collection_name]
        collections.insert_many(author_info)

def main() -> None:    
    # Create queries from repo databse
    client = MongoClient(MONGO_CLIENT_STRING)
    ALL_PRS_BY_REPO = client["ALL_PRS_BY_REPO"]
    AUTHOR_INFO_BY_REPO = client["AUTHOR_INFO_BY_REPO"]
    
    # If database is empty gather's all the PRs for each Repo in the database
    if len(ALL_PRS_BY_REPO.list_collection_names()) == 0:
        print("[WORKING] ALL_PRS_BY_REPO collection is empty...\n[WORKING] Collecting all pull requests...")
        collect_prs_from_repos_in_db(client)
    else:
        print("[WORKING] Pull requests already mined, gathering author information...")

    # If we haven't collected all the author info for each repo
    if len(AUTHOR_INFO_BY_REPO.list_collection_names()) < len(ALL_PRS_BY_REPO.list_collection_names()):
        print("[WORKING] AUTHOR_INFO_BY_REPO collection is empty/incomplete...\n[WORKING] Collecting author information from pull requests\n")
        collect_author_info(client)
    else:
        print("[WORKING] Author information already parsed, categorizing users...")

if __name__ == "__main__":
    print("[STARTING] Running script...\n")
    start_time = timer()
    main()
    end_time = timer()
    print("\n[DONE] Script completed in: %4.3fs" % (end_time - start_time))
