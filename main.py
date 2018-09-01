import logging
import re
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from github import Github, GithubException
from cache import Cache

LOGGER = logging.getLogger(__name__)

USER_REPOS_CACHE_KEY = 'user_repos'
USER_REPOS_CACHE_TTL = 1800
USER_GISTS_CACHE_KEY = 'user_gists'
USER_GISTS_CACHE_TTL = 1800
USER_ORGANIZATIONS_CACHE_KEY = 'user_orgs'
USER_ORGANIZATIONS_CACHE_TTL = 3600
USER_STARRED_REPOS_CACHE_KEY = 'user_starred_repos'
USER_STARRED_REPOS_CACHE_TTL = 3600


class GitHubExtension(Extension):
    """ Main Extension class """

    def __init__(self):
        LOGGER.info('Initializing GitHub Extension')
        super(GitHubExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent,
                       PreferencesUpdateEventListener())
        self.githubApi = None
        self.user = None

    def show_menu(self):
        """ Show the main extension menu, when the user types the extension keyword without arguments """

        keyword = self.preferences["kw"]

        return RenderResultListAction([
            ExtensionResultItem(icon='images/icon.png',
                                name="My Account",
                                description="Access your profile info and common pages like your Issues, Pull Requests etc.",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s account" % keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Organizations",
                                description="List your GitHub Organizations",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s orgs" % keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Repositories",
                                description="List the GitHub repositories that you are a member of",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s repos" % keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Starred Repos",
                                description="List your Starred Repos",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s starred" % keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Gists",
                                description="List your created Gists",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s gists" % keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Search public repos",
                                description="Search on Public GitHub repositories",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s search " % keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Search Users",
                                description="Search GitHub users",
                                highlightable=False,
                                on_enter=SetUserQueryAction("%s users " % keyword)),
            ExtensionResultItem(icon='images/icon.png',
                                name="GitHub Status",
                                description="Opens the GitHub status page",
                                highlightable=False,
                                on_enter=OpenUrlAction("https://status.github.com"))
        ])

    def account_menu(self, query):
        """ Show your menu with links for GitHub pages """

        # Authenticate the user, if its not already authenticated.
        if self.user is None:
            self.user = self.githubApi.get_user()

        return RenderResultListAction([
            ExtensionResultItem(icon='images/icon.png',
                                name="Logged in as %s (%s)" % (
                                    self.user.name, self.user.login),
                                highlightable=False,
                                on_enter=OpenUrlAction(self.user.html_url)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Profile",
                                description="Open your User Profile page on GitHub website",
                                highlightable=False,
                                on_enter=OpenUrlAction("https://github.com/%s" % self.user.login)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Repos",
                                description="Open your Repositories page on GitHub website",
                                highlightable=False,
                                on_enter=OpenUrlAction("https://github.com/%s?tab=repositories" % self.user.login)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Starred Repos",
                                description="Open your Starred repositories page on GitHub website",
                                highlightable=False,
                                on_enter=OpenUrlAction("https://github.com/%s?tab=stars" % self.user.login)),
            ExtensionResultItem(icon='images/icon.png',
                                name="Gists",
                                description="Open your Gists",
                                highlightable=False,
                                on_enter=OpenUrlAction("https://gist.github.com")),
            ExtensionResultItem(icon='images/icon.png',
                                name="Pull Requests",
                                description="Open your Pull requests page on GitHub website",
                                highlightable=False,
                                on_enter=OpenUrlAction("https://github.com/pulls")),
            ExtensionResultItem(icon='images/icon.png',
                                name="Issues",
                                description="Open your Issues page on GitHub website",
                                highlightable=False,
                                on_enter=OpenUrlAction("https://github.com/issues"))
        ])

    def user_repos(self, query):
        """ List the repos owned by the user """

        repos = Cache.get(USER_REPOS_CACHE_KEY)

        if repos is None:
            repos = self.githubApi.get_user().get_repos(
                sort="updated", direction="desc")

            Cache.set(USER_REPOS_CACHE_KEY, repos, USER_REPOS_CACHE_TTL)

        items = []
        for repo in repos:

            if query and query.lower() not in repo.name.lower():
                continue

            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name=repo.name,
                description=repo.description,
                on_enter=OpenUrlAction(repo.html_url)
            ))

        return RenderResultListAction(items[:8])

    def user_gists(self, query):
        """ List user gists"""

        query = query.lower()
        gists = Cache.get(USER_GISTS_CACHE_KEY)

        if gists is None:
            gists = self.githubApi.get_user().get_gists()

            Cache.set(USER_GISTS_CACHE_KEY, gists, USER_GISTS_CACHE_TTL)

        items = []
        for gist in gists:

            files = gist.files.values()
            desc = ""

            if gist.description is not None:
                desc = gist.description

            if query and query not in desc.lower() or query not in files[0].filename:
                continue

            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name=files[0].filename.encode('utf-8'),
                description=desc,
                on_enter=OpenUrlAction(gist.html_url)
            ))

        return RenderResultListAction(items[:8])

    def search_public_repos(self, query):
        """ Search public repos """

        if not query or len(query) < 3:
            return RenderResultListAction([ExtensionResultItem(
                icon='images/icon.png',
                name='Please keep typing your search query',
                description='Minimum 3 chars',
                highlightable=False,
                on_enter=HideWindowAction()
            )])

        repos = self.githubApi.search_repositories(query=query)[:8]

        items = []

        for repo in repos:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name="%s (%s stars)" % (
                    repo.name.encode('utf-8'), repo.stargazers_count),
                description=repo.description.encode('utf-8'),
                on_enter=OpenUrlAction(repo.html_url)
            ))

        return RenderResultListAction(items)

    def search_users(self, query):
        """ Search GitHub users """

        if not query or len(query) < 3:
            return RenderResultListAction([ExtensionResultItem(
                icon='images/icon.png',
                name='Please keep typing your search query',
                description='Minimum 3 chars',
                highlightable=False,
                on_enter=HideWindowAction()
            )])

        users = self.githubApi.search_users(
            query=query, sort="followers", order="desc")[:8]

        items = []

        for user in users:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name=user.name,
                on_enter=OpenUrlAction(user.html_url)
            ))

        return RenderResultListAction(items)

    def user_orgs(self, query):
        """ List the Organizations the user belongs to"""

        orgs = Cache.get(USER_ORGANIZATIONS_CACHE_KEY)

        if orgs is None:
            orgs = self.githubApi.get_user().get_orgs()

            Cache.set(USER_ORGANIZATIONS_CACHE_KEY,
                      orgs, USER_ORGANIZATIONS_CACHE_TTL)

        items = []
        for org in orgs:

            if query and query.lower() not in org.name.lower():
                continue

            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name=org.name,
                on_enter=OpenUrlAction(org.html_url)
            ))

        return RenderResultListAction(items[:8])

    def user_starred_repos(self, query):
        """ List the repositories the user has starred"""

        repos = Cache.get(USER_STARRED_REPOS_CACHE_KEY)

        if repos is None:
            repos = self.githubApi.get_user().get_starred()

            Cache.set(USER_STARRED_REPOS_CACHE_KEY,
                      repos, USER_STARRED_REPOS_CACHE_TTL)

        items = []
        for repo in repos:

            if query and query.lower() not in repo.name.lower():
                continue

            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name=repo.name,
                description=repo.description,
                on_enter=OpenUrlAction(repo.html_url)
            ))

        return RenderResultListAction(items[:8])


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):

        query = event.get_argument()

        if query is None:
            return extension.show_menu()

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
                return extension.account_menu(account[0].strip())

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

            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name='Please select a valid option',
                                    highlightable=False,
                                    on_enter=HideWindowAction())
            ])

        except GithubException as e:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name='An error ocurred when connecting to GitHub',
                                    description=str(e),
                                    highlightable=False,
                                    on_enter=HideWindowAction())
            ])


class PreferencesEventListener(EventListener):
    def on_event(self, event, extension):
        extension.githubApi = Github(event.preferences['access_token'])
        Cache.purge()
        try:
            extension.user = extension.githubApi.get_user()
        except GithubException as e:
            LOGGER.error(e)
            extension.user = None


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event, extension):
        if event.id == 'access_token':
            extension.githubApi = Github(event.new_value)
            Cache.purge()
            try:
                extension.user = extension.githubApi.get_user()
            except GithubException as e:
                LOGGER.error(e)
                extension.user = None


if __name__ == '__main__':
    GitHubExtension().run()
