# pull-request-comments-script

Simple python scripts that pulls data from GitHub using its v4 graphQL API.
For purposes of observing and researching the Sentiment Analysis of pull request comments left on popular GitHub repositories.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

```
python
```
Install
```
pip install requests, pymongo
```

### get_pull_requests.py

This script when given a repository owner and name will iterate through and save all comments from a given number of pull requests to a MongoDB.

### get_repos.py

This script will iterate through and save all repositories with given constraints to a MongoDB.

## Authors

* **Joshua Kruse** - [GitHub](https://github.com/JoshEKruse)
* **Champ Foronda** - [GitHub](https://github.com/cforonda)

## Acknowledgments

* **Igor Steinmacher, PHD.** - *Advisor* [Profile](https://www.igor.pro.br/)

