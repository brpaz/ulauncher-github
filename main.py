""" GitHub Ulauncher Extension """
import json
import logging
import os
import re
from threading import Thread, Timer

from github import Github, GithubException
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ExtensionCustomAction import \
    ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RenderResultListAction import \
    RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.event import (ItemEnterEvent, KeywordQueryEvent,
                                        PreferencesEvent,
                                        PreferencesUpdateEvent)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.config import CACHE_DIR

LOGGER = logging.getLogger(__name__)

FETCH_INTERVAL = 86400


class GitHubExtension(Extension):
    """ Main Extension class """
    def __init__(self):
        LOGGER.info('Initializing GitHub Extension')
        super(GitHubExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent,
                       PreferencesUpdateEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

        self.github = None
        self.user = None
        self.repos_cache_file = os.path.join(CACHE_DIR,
                                             'github_repos_cache.json')
        self.repos_starred_cache_file = os.path.join(
            CACHE_DIR, 'github_repos_starred_cache.json')
        self.gists_cache_file = os.path.join(CACHE_DIR,
                                             'github_gists_cache.json')

        self.init_cache()

    def init_cache(self):
        """ Initializes cache files """
        if not os.path.exists(self.repos_cache_file):
            with open(self.repos_cache_file, 'w') as outfile:
                json.dump([], outfile)

        if not os.path.exists(self.repos_starred_cache_file):
            with open(self.repos_starred_cache_file, 'w') as outfile:
                json.dump([], outfile)

        if not os.path.exists(self.gists_cache_file):
            with open(self.gists_cache_file, 'w') as outfile:
                json.dump([], outfile)

    def refresh_cache(self):
        """ Spawns a new Thread and refresh the local cached data """
        th = Thread(target=self.fetch_data_from_github)
        th.daemon = True
        th.start()

    def fetch_data_from_github(self):
        """
        Fetch user repositories, gists and other data from GitHub.
        This should re run in a separate thread.
        """

        self.fetch_repos()
        self.fetch_gists()
        self.fetch_starred()

        timer = Timer(FETCH_INTERVAL, self.fetch_data_from_github)
        timer.daemon = True
        timer.start()

    def fetch_repos(self):
        """ Fetch user repositories """

        LOGGER.info("Fetching user repos from GitHub")

        repos = self.github.get_user().get_repos(sort="updated",
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

        with open(self.repos_cache_file, 'w') as outfile:
            json.dump(repo_data, outfile)

    def fetch_gists(self):
        """ Fetch user gists """

        LOGGER.info("Fetching user gists from GitHub")

        gists_data = []
        gists = self.github.get_user().get_gists()

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

        with open(self.gists_cache_file, 'w') as outfile:
            json.dump(gists_data, outfile)

    def fetch_starred(self):
        """ Fetch starred repos """

        LOGGER.info("Fetching starred repos from GitHub")

        repo_data = []

        repos = self.github.get_user().get_starred()
        for repo in repos:
            repo_data.append({
                'name': repo.name,
                'fullname': repo.full_name,
                'description': repo.description,
                'url': repo.html_url,
                'stars': repo.stargazers_count
            })

        with open(self.repos_starred_cache_file, 'w') as outfile:
            json.dump(repo_data, outfile)

    def show_menu(self, keyword):
        """
        Show the main extension menu,
        when the user types the extension keyword without arguments
        """

        return RenderResultListAction([
            ExtensionResultItem(icon='images/icon.png',
                                name="My Account",
                                description="Access your profile page",
                                on_enter=SetUserQueryAction("%s account " %
                                                            keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Organizations",
                                description="List your GitHub Organizations",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s orgs " %
                                                            keyword)),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Repositories",
                description=
                "List the GitHub repositories that you are a member of",
                highlightable=False,
                on_enter=SetUserQueryAction("%s repos " % keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Starred Repos",
                                description="List your Starred Repos",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s starred " %
                                                            keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Gists",
                                description="List your created Gists",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s gists " %
                                                            keyword)),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Search public repos",
                description="Search on Public GitHub repositories",
                highlightable=False,
                on_enter=SetUserQueryAction("%s search " % keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Search Users",
                                description="Search GitHub users",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s users " %
                                                            keyword)),
            ExtensionResultItem(
                icon='images/icon.png',
                name="GitHub Status",
                description="Opens the GitHub status page",
                highlightable=False,
                on_enter=OpenUrlAction("https://www.githubstatus.com")),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Refresh Cache",
                description=
                "Refreshes the local cache. This might some time to process.",
                highlightable=False,
                on_enter=ExtensionCustomAction({"action": "refresh_cache"}))
        ])

    def account_menu(self):
        """ Show your menu with links for GitHub pages """

        # Authenticate the user, if its not already authenticated.
        if self.user is None:
            self.user = self.github.get_user()

        return RenderResultListAction([
            ExtensionResultItem(icon='images/icon.png',
                                name="Logged in as %s (%s)" %
                                (self.user.name, self.user.login),
                                highlightable=False,
                                on_enter=OpenUrlAction(self.user.html_url)),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Profile",
                description="Open your User Profile page on GitHub website",
                highlightable=False,
                on_enter=OpenUrlAction("https://github.com/%s" %
                                       self.user.login)),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Repos",
                description="Open your Repositories page on GitHub website",
                highlightable=False,
                on_enter=OpenUrlAction(
                    "https://github.com/%s?tab=repositories" %
                    self.user.login)),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Starred Repos",
                description=
                "Open your Starred repositories page on GitHub website",
                highlightable=False,
                on_enter=OpenUrlAction("https://github.com/%s?tab=stars" %
                                       self.user.login)),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Gists",
                description="Open your Gists",
                highlightable=False,
                on_enter=OpenUrlAction("https://gist.github.com")),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Pull Requests",
                description="Open your Pull requests page on GitHub website",
                highlightable=False,
                on_enter=OpenUrlAction("https://github.com/pulls")),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Issues",
                description="Open your Issues page on GitHub website",
                highlightable=False,
                on_enter=OpenUrlAction("https://github.com/issues")),
            ExtensionResultItem(
                icon='images/icon.png',
                name="Access tokens",
                description="Manage your personal access tokens",
                highlightable=False,
                on_enter=OpenUrlAction("https://github.com/settings/tokens")),
        ])

    def user_repos(self, query):
        """ List the repos owned by the user """

        with open(self.repos_cache_file) as cache_file:
            repos = json.load(cache_file)

        items = []
        for repo in repos:

            if query and query.lower() not in repo['fullname'].lower():
                continue

            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=repo['fullname'],
                                    description=repo['description'] or "",
                                    highlightable=not query,
                                    on_enter=OpenUrlAction(repo['url']),
                                    on_alt_enter=CopyToClipboardAction(
                                        repo['url'])))

        return RenderResultListAction(items[:8])

    def user_gists(self, query):
        """ List user gists"""

        query = query.lower()
        gists = []
        with open(self.gists_cache_file) as cache_file:
            gists = json.load(cache_file)

        items = []
        for gist in gists:

            desc = gist['description'] or ""

            if query and (query not in desc.lower()
                          and query not in gist['filename'].lower()):
                continue

            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=gist['filename'],
                                    description=desc,
                                    highlightable=not query,
                                    on_enter=OpenUrlAction(gist['url']),
                                    on_alt_enter=CopyToClipboardAction(
                                        gist['url'])))

        return RenderResultListAction(items[:8])

    def search_public_repos(self, query):
        """ Search public repos """

        if not query or len(query) < 3:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Please keep typing your search query',
                    description='Minimum 3 chars',
                    highlightable=False,
                    on_enter=HideWindowAction())
            ])

        repos = self.github.search_repositories(query=query)[:8]

        items = []

        for repo in repos:
            items.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name="%s (%s stars)" % (repo.name, repo.stargazers_count),
                    description=repo.description,
                    on_enter=OpenUrlAction(repo.html_url),
                    on_alt_enter=CopyToClipboardAction(repo.html_url)))

        return RenderResultListAction(items)

    def search_users(self, query):
        """ Search GitHub users """

        if not query or len(query) < 3:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Please keep typing your search query',
                    description='Minimum 3 chars',
                    highlightable=False,
                    on_enter=HideWindowAction())
            ])

        users = self.github.search_users(query=query,
                                         sort="followers",
                                         order="desc")[:8]

        items = []

        for user in users:
            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=user.name,
                                    on_enter=OpenUrlAction(user.html_url),
                                    on_alt_enter=CopyToClipboardAction(
                                        user.html_url)))

        return RenderResultListAction(items)

    def user_orgs(self, query):
        """ List the Organizations the user belongs to"""

        orgs = self.github.get_user().get_orgs()

        items = []
        for org in orgs:

            if query and query.lower() not in org.name.lower():
                continue

            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=org.name,
                                    highlightable=not query,
                                    on_enter=OpenUrlAction(org.html_url),
                                    on_alt_enter=CopyToClipboardAction(
                                        org.html_url)))

        return RenderResultListAction(items[:8])

    def user_starred_repos(self, query):
        """ List the repositories the user has starred"""

        with open(self.repos_starred_cache_file) as cache_file:
            repos = json.load(cache_file)

        items = []
        for repo in repos:

            if query and query.lower() not in repo['name'].lower():
                continue

            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=repo['name'],
                                    description=repo['description'],
                                    on_enter=OpenUrlAction(repo['url']),
                                    on_alt_enter=CopyToClipboardAction(
                                        repo['url'])))

        return RenderResultListAction(items[:8])


# pylint: disable=too-many-return-statements
class KeywordQueryEventListener(EventListener):
    """ Listen to Input events """
    def on_event(self, event, extension):
        """ Handles event """

        query = event.get_argument() or ""
        keyword = event.get_keyword()

        if keyword == extension.preferences["kw_gists"]:
            return extension.user_gists(query)

        if keyword == extension.preferences["kw_repos"]:
            return extension.user_repos(query)

        if keyword == extension.preferences["kw_search"]:
            return extension.search_public_repos(query)

        if not query:
            return extension.show_menu(keyword)

        # Get the action based on the search terms
        account = re.findall(r"^account(.*)?$", query, re.IGNORECASE)
        repos = re.findall(r"^repos(.*)?$", query, re.IGNORECASE)
        users = re.findall(r"^users(.*)?$", query, re.IGNORECASE)
        orgs = re.findall(r"^orgs(.*)?$", query, re.IGNORECASE)
        search = re.findall(r"^search(.*)?$", query, re.IGNORECASE)
        starred = re.findall(r"^starred(.*)?$", query, re.IGNORECASE)
        gists = re.findall(r"^gists(.*)?$", query, re.IGNORECASE)

        try:

            if account:
                return extension.account_menu()

            if repos:
                return extension.user_repos(repos[0].strip())

            if search:
                return extension.search_public_repos(search[0].strip())

            if gists:
                return extension.user_gists(gists[0].strip())

            if orgs:
                return extension.user_orgs(orgs[0].strip())

            if users:
                return extension.search_users(users[0].strip())

            if starred:
                return extension.user_starred_repos(starred[0].strip())

            # by default search on user repos
            return extension.user_repos(query)

        except GithubException as ex:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='An error ocurred when connecting to GitHub',
                    description=str(ex),
                    highlightable=False,
                    on_enter=HideWindowAction())
            ])


class PreferencesEventListener(EventListener):
    """ Handles preferences initialization event """
    def on_event(self, event, extension):
        """ Handle event """
        extension.github = Github(event.preferences['access_token'])
        try:
            extension.user = extension.github.get_user()

            # pylint: disable=invalid-name
            t = Thread(target=extension.fetch_data_from_github)
            t.daemon = True
            t.start()

        except GithubException as ex:
            LOGGER.error(ex)
            extension.user = None


class PreferencesUpdateEventListener(EventListener):
    """ Handles Preferences Update event """
    def on_event(self, event, extension):
        """ Event handler """
        if event.id == 'access_token':
            extension.github = Github(event.new_value)
            try:
                extension.user = extension.github.get_user()

                extension.refresh_cache()
            except GithubException as ex:
                LOGGER.error(ex)
                extension.user = None


class ItemEnterEventListener(EventListener):
    """ Handles Custom ItemEnter event """
    def on_event(self, event, extension):
        """ handle function """
        data = event.get_data()
        if "action" in data and data['action'] == 'refresh_cache':
            extension.refresh_cache()


if __name__ == '__main__':
    GitHubExtension().run()
