import os
import json


class Cache(object):

    def __init__(self, cache_dir):
        """ Class constructor"""
        self.repos_cache_file = os.path.join(cache_dir,
                                             'github_repos_cache.json')
        self.repos_starred_cache_file = os.path.join(
            cache_dir, 'github_repos_starred_cache.json')
        self.gists_cache_file = os.path.join(cache_dir,
                                             'github_gists_cache.json')
        self.__initialize_cache_files()

    def __initialize_cache_files(self):
        """ Creates the cache files on disk if they not exist yet"""
        if not os.path.exists(self.repos_cache_file):
            with open(self.repos_cache_file, 'w') as f:
                json.dump([], f)

        if not os.path.exists(self.repos_starred_cache_file):
            with open(self.repos_starred_cache_file, 'w') as f:
                json.dump([], f)

        if not os.path.exists(self.gists_cache_file):
            with open(self.gists_cache_file, 'w') as f:
                json.dump([], f)

    def store_repos_cache(self, data=[]):
        with open(self.repos_cache_file, 'w') as f:
            json.dump(data, f)

    def store_gists_cache(self, data=[]):
        with open(self.gists_cache_file, 'w') as f:
            json.dump(data, f)

    def store_starred_repos(self, data=[]):
        """ Save starred repos in the cache"""
        with open(self.repos_starred_cache_file, 'w') as f:
            json.dump(data, f)

    def get_repos(self):
        with open(self.repos_cache_file) as f:
            return json.load(f)

    def get_gists(self):
        with open(self.gists_cache_file) as f:
            return json.load(f)

    def get_starred_repos(self):
        with open(self.repos_starred_cache_file) as cache_file:
            return json.load(cache_file)
