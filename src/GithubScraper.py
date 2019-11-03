import requests

class GithubScraper:
    GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
    HTTP_OK_RESPONSE = 200

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
        self.__AUTH_KEY = github_auth_key
        self.__MONGO_USER = mongo_username
        self.__MONGO_PASSWORD = mongo_password
        self.__HEADERS = {"Authorization": self.__AUTH_KEY}

    def get_auth_key(self):
        """
        Retrieves GitHub API Key from Config.py used to interact with the GraphQL Endpoint

        Returns
        -------
        string
            Github Authorization Key
        """
        return self.__AUTH_KEY

    def get_mongo_username(self):
        """
        Retrieves MongoDB username stored in Config.py used to interact with the MongoDB database

        Returns
        -------
        string
            MongoDB username stored in Config.py used to interact with the MongoDB datbase
        """
        return self.__MONGO_USER

    def get_mongo_password(self):
        """
        Retrieves MongoDB password stored in Config.py used to interact with the MongoDB database

        Returns
        -------
        string
            MongoDB password stored in Config.py used to interact with the MongoDB database
        """
        return self.__MONGO_PASSWORD

    def run_query(self, query):
        """
        Sends a request to the GraphQL Endpoint based on a given query

        Parameters
        ----------
        query : string
            GraphQL query string used to gather information

        Returns
        -------
        json
            Returns the data gathered from GitHub in the form of a JSON object

        Raises
        ------
        Exception
            Raises an exception if the query failed to run/if the HTTP_OK_RESPONSE was not received
        
        """
        request = requests.post(GITHUB_GRAPHQL_ENDPOINT, json={'query': query}, headers=self.__HEADERS)
        if request.status_code == HTTP_OK_RESPONSE:
            return request.json
        else:
            raise Exception(f'ERROR [{request.status_code}]: Query failed to run...\n{query}')