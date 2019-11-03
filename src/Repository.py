import requests
import datetime
class Repository(GithubScraper):
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

    def setup_query(query_string, end_cursor):
        pass

    def query_filter(self, min_stars=0, max_stars=10, last_activity=90, date_created=1456):
        """
        Creates a query filter used to search for certain repositories using the GraphQL API

        Parameters
        ----------
        min_stars : int
            Starting range for minimum amount of stars a repository must have (default: 0)
        max_stars : int
            Ending range for maximum amount of stars a repository must have (default: 10)
        last_activity : int
            Number of days within the last __ days (default: 90)
        date_created : int
            Number of days within the last __ days (default: 1456)
        """
        date_last_active = datetime.datetime.now() - datetime.timedelta(days=last_activity)
        date_created = datetime.datetime.now() - datetime.timedelta(days=date_created)
        stars = f'{min_stars}..{max_stars}'
        search_filter = f'is:public archived:false fork:false stars:{stars} pushed:20{date_last_active:%y-%m-%d}..* created:20{date_created:%y-%m-%d}..*'
        return search_filter
    
    def find_repos(query_string, db_collection, total_pull_num):
        pass

    def repo_checker(query_data, db_collection, total_pull_num):
        pass

    def is_repo_valid(node, total_pull_number):
        pass