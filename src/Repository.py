import time
import requests
import datetime
from pymongo import MongoClient
from GithubScraper import GithubScraper
class Repository(GithubScraper):

    # DEFAULT CONSTANTS
    DEFAULT_MIN_STARS = 100
    DEFAULT_MAX_STARS = 1000
    DEFAULT_PR_NUMBER = 100
    LAST_NINETY_DAYS = 90
    LAST_FOUR_YEARS = 365 * 4

    def __init__(self, github_auth_key="", mongo_username="", mongo_password=""):
        """
        Initialization constructor

        Parameters
        ----------
        github_auth_key : string
            Github Authorization Key used to interact with the GraphQL API
        mongo_username : string
            MongoDB username used to interact with MongoDB
        mongo_password : string
            MongoDB password used to interact with MongoDB
            
        """
        super().__init__(github_auth_key, mongo_username, mongo_password)

    def __search_filter(self, min_stars=self.DEFAULT_MIN_STARS, max_stars=self.DEFAULT_MAX_STARS,
                        last_activity=self.LAST_NINETY_DAYS, date_created=self.LAST_FOUR_YEARS):
        """
        Creates a query filter used to search for certain repositories using the GraphQL API

        Parameters
        ----------
        min_stars : int
            Starting range for minimum amount of stars a repository must have (default: 100)
        max_stars : int
            Ending range for maximum amount of stars a repository must have (default: 1000)
        last_activity : int
            Number of days within the last __ days (default: 90)
        date_created : int
            Number of days within the last __ days (default: 365 * 4 (Four Years))

        """
        date_last_active = datetime.datetime.now() - datetime.timedelta(days=last_activity)
        date_created = datetime.datetime.now() - datetime.timedelta(days=date_created)
        stars = f'{min_stars}..{max_stars}'
        search_filter = f"""is:public archived:false fork:false 
                            stars:{stars} pushed:20{date_last_active:%y-%m-%d}..* created:20{date_created:%y-%m-%d}..*"""
        return search_filter

    def find_repos(self, min_stars=self.DEFAULT_MIN_STARS, max_stars=self.DEFAULT_MAX_STARS,
                   last_activity=self.LAST_NINETY_DAYS, date_created=self.LAST_FOUR_YEARS):
        """
        Finds and collects repositories that fits our filter based on the parameters
        given

        Parameters
        ----------
        min_stars : int
            The minimum amount of stars that a repository must have (default: 100)
        max_stars : int
            The maximum amount of stars that a repository must have (default: 1000)
        last_activity : int
            The range of days a repository was last active (default: 90)
        date_created : int
            The range of days a repository was created (default: 365 * 4 (four years))

        """ 
        # Creates a search filter used to search for GitHub repos
        print("Creating search filter...")
        search_filter = search_filter(min_stars, max_stars, last_activity, date_created)

        # Creating connection to MongoDB Client
        print("Creating connection to MongoDB Client...")
        client = MongoClient(self.get_mongo_client_string())
        repo_database_name = input("Enter database name: ")
        repo_database = client[repo_database_name]
        repo_collection_name = input("Enter collection name: ")
        db_repo_collection = repo_database[repo_collection_name]

        end_cursor = ""
        end_cursor_string = ""
        hasNextPage = True
        index = 0

        while(hasNextPage):
            # Creates a query for each page and runs the query to get the data
            query = self.setup_repo_query(search_filter, end_cursor_string)
            query_data = self.run_query(query)

            # Checks if repository is valid
            repo_checker(query_data, db_repo_collection, self.DEFAULT_PR_NUMBER, client)

            hasNextPage = query_data["data"]["search"]["pageInfo"]["hasNextPage"]

            # Checks if there is a next page
            if(hasNextPage):
                end_cursor = query_data["data"]["search"]["pageInfo"]["endCursor"]
                end_cursor_string = f', after:"{end_cursor}'
            
            index += 1
            time.sleep(.5)

    def repo_checker(self, query_data, db_repo_collection, total_pull_num, client):
        """
        Parses through the query data and insert into the database repository collection

        Parameters
        ----------
        query_data : json
            Data pulled from GitHub GraphQL API.
        db_repo_collection : json
            A collection of MongoDB documents for repositories.
        total_pull_num : int
            The total amount of pull requests a repository must have.
        client : MongoDB client
            A client connection to the MongoDB database
        """
        repository_nodes = query_data["data"]["search"]["nodes"]
        dict_of_repos = {"repository": []}
        list_of_repos = list()

        index = 0

        # Iterates through each repo node
        for node in repository_nodes:
            if(is_repo_valid(node, total_pull_num)):
                repo_owner = node["owner"]["login"]
                repo_name = node["name"]

                # Save comments from each valid repository in MongoDB
                get_comments(repo_owner, repo_name, client)

                # Appends the data of valid repository
                valid_repo = {"name": node["name"],
                                      "owner": node["owner"]["login"],
                                      "contributers": node["contributors"]["totalCount"],
                                      "stars": node["stargazers"]["totalCount"],
                                      "forks": node["forks"],
                                      "commits": node["commits"]["target"]["history"]["totalCount"],
                                      "pullRequests": node["pullRequests"]["totalCount"]}

                list_of_repos.append(valid_repo)
                print(f"{index}: {valid_repo['name']}")
                index += 1
        
        db_repo_collection.insert_many(list_of_repos)

    def is_repo_valid(self, repository, total_pull_num):
        """
        Checks the total amount of pullRequests to see if it has the required
        amount of pull requests.

        Parameters
        ----------
        repository : json
            A json object that contains the information about the repository.
        total_pull_num : int
            The total number of pull requests a repository must have.

        Returns
        -------
        boolean
            Returns true, if the total amount of pull requests is met.
        """
        return repository["pullRequests"]["totalCount"] >= total_pull_num

    def get_comments(self, repo_owner, repo_name, client):
        pass

    def setup_repo_query(self, query_string, end_cursor):
        """
        Takes in a search filter and page cursor and creates a query that contains
        all the valid repositories on that page.

        Parameters
        ----------
        query_string : string
            A github search filter used to find repositories with certain requirements.
        end_cursor : string
            A page cursor that iterates through the different pages if there are multiple
            results.

        Returns
        -------
        json
            A json object containing all the data gathered from the GitHub GraphQL
            API.

        """
        query = f"""
        query {{
            rateLimit {{
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
        }}"""

        return query

