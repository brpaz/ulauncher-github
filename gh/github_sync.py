import logging
import time
from github import Github
from gh.cache import Cache

logger = logging.getLogger(__name__)


class GitHubDataSync(object):
    """ Syncs the data from GitHub """

    def __init__(self, github_client: Github, cache: Cache):
        self.github_client = github_client
        self.cache = cache

    def execute(self):
        """" Executes the sync process with GitHub"""
        self.fetch_repos()
        time.sleep(2)
        self.fetch_gists()
        time.sleep(2)
        self.fetch_starred()

    def fetch_repos(self):
        """ Fetch user repositories """

        logger.info("Fetching user repos from GitHub")

        repos = self.github_client.get_user().get_repos(sort="updated",
                                                        direction="desc")

        # need to iterate all repos to force the PaginatesList to get all the results
        repo_data = []
        for repo in repos:
            repo_data.append({
                'name': repo.name,
                'fullname': repo.full_name,
                'description': repo.description,
                'url': repo.html_url,
                'stars': repo.stargazers_count
            })

            time.sleep(0.1)

        self.cache.store_repos_cache(repo_data)

    def fetch_gists(self):
        """ Fetch user gists """

        logger.info("Fetching user gists from GitHub")

        gists_data = []
        gists = self.github_client.get_user().get_gists()

        for gist in gists:
            gists_data.append({
                'description':
                gist.description,
                'url':
                gist.html_url,
                'filename':
                list(gist.files.values())[0].filename
                if list(gist.files.values()) else ""
            })

            time.sleep(0.1)

        self.cache.store_gists_cache(gists_data)

    def fetch_starred(self):
        """ Fetch starred repos """

        logger.info("Fetching starred repos from GitHub")

        repo_data = []

        repos = self.github_client.get_user().get_starred()
        for repo in repos:
            repo_data.append({
                'name': repo.name,
                'fullname': repo.full_name,
                'description': repo.description,
                'url': repo.html_url,
                'stars': repo.stargazers_count
            })

            time.sleep(0.1)

        self.cache.store_starred_repos(repo_data)
