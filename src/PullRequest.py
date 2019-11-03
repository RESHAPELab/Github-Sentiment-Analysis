import requests

class PullRequest(GithubScraper):
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

    def setup_single_pull_request_query(self, owner="", name="", pull_request_number=1, comment_range=10):
        """
        Setups a query to gather exactly one pull request on a given repository

        Parameters
        ----------
        owner : string
            Owner of the GitHub Repository
        name : string
            Name of the GitHub Repository
        pull_request_number : int
            Number of the pull request (default: 1)
        comment_range : int
            How many comments to gather (default: 10)

        Returns
        -------
        json
            Query that will be used with the GraphQL API
        """
        query = f"""
        query {{
            repository(owner: {owner}, name: {name}) {{
                pullRequest: issueOrPullRequest(number: {pull_request_number}) {{
                    __typename
                    ... onPullRequest {{
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
        }}
        """

        return query

    def get_comments_from_pull_request(self, query_data=None):
        """
        Parses through the gathered query data

        Parameters
        ----------
        query_data : json
            Query data that was gathered from the GitHub GraphQL API (default: None)

        Returns
        -------
        dict
            A dictionary object containing all the comments from the query

        Raises
        ------
        Exception
            Raises an error if the query data is invalid/None
        KeyError
            Raises a KeyError if the query data did not have any comments in it
        """
        if query_data is None:
            raise Exception(f"ERROR: Invalid query data\n{query_data}")
        else:
            try:
                comment_edges = query_data["data"]["repository"]["pullRequest"]["comments"]["edges"]
                dict_of_comments = {"comment": []}
                for edge in comment_edges:
                    comment = {"author": edge["node"]["author"]["login"], "bodyText": edge["node"]["bodyText"]}
                    dict_of_comments["comment"].append(comment)
            except KeyError:
                dict_of_comments = dict()

        return dict_of_comments

    def get_comments_from_review_threads(self, query_data=None):
        """
        Parses through the gathered query data

        Parameters
        ----------
        query_data : json
            Query data that was gathered from the GitHub GraphQL API (default: None)

        Returns
        -------
        dict
            A dictionary object containing all the comments from the query

        Raises
        ------
        Exception
            Raises an error if the query data is invalid/None
        KeyError
            Raises a KeyError if the query data did not have any comments in it
        """
        if query_data is None:
            raise Exception(f"ERROR: Invalid query data\n{query_data}")
        else:
            try:
                review_nodes = query_data["data"]["repository"]["pullRequest"]["reviewThreads"]["edges"]
                dict_of_comments = {"comment": []}
                for review_node in review_nodes:
                    for comment in review_node["node"]["comments"]["nodes"]:
                        comment = {"author": comment["author"]["login"], "bodyText": comment["bodyText"]}
                        dict_of_comments["comment"].append(comment)
            except KeyError:
                dict_of_comments = dict()
        
        return dict_of_comments