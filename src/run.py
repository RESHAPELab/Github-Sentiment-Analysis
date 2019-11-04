from Config import GITHUB_AUTHORIZATION_KEY, MONGO_USER, MONGO_PASSWORD
from PullRequest import *
from Repository import *
import requests
import pymongo

if __name__ == "__main__":
    pr_scraper = PullRequest(GITHUB_AUTHORIZATION_KEY, MONGO_USER, MONGO_PASSWORD)
    repo_scraper = Repository(GITHUB_AUTHORIZATION_KEY, MONGO_USER, MONGO_PASSWORD)
    
    # Gather pull_request information
    pr_query = pr_scraper.setup_single_pull_request_query("astropy", "astropy")
    pr_query_data = pr_scraper.run_query(pr_query)
    pr_comments = pr_scraper.get_comments_from_pull_request(pr_query_data)
    pr_review_thread_comments = pr_scraper.get_comments_from_review_threads(pr_query_data)
    
    # Gather repository information
