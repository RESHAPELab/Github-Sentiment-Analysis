import os
import requests
from pymongo import MongoClient
from Config import GITHUB_AUTHORIZATION_KEY, MONGO_CLIENT_STRING

def create_resources(client, project_folder_dir="") -> None:
    """
    Creates the resources folder at the projects root directory
    """
    try:
        os.chdir(project_folder_dir)
        os.mkdir("resources")
    except FileExistsError:
        print("[WORKING] Resources file already created")

    author_info_db = client["AUTHOR_INFO_BY_REPO"]

def main() -> None:
    client = MongoClient(MONGO_CLIENT_STRING)

    project_folder_dir = os.getcwd()[:-3]
    print(f"[WORKING] Project Directory: {project_folder_dir}")

    # Creates the resources folder which will contain all the csv's
    # from the database
    create_resources(client, project_folder_dir)
    print(os.getcwd())
    
if __name__ == "__main__":
    main()