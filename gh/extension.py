import logging
import requests
import gi
import time
from threading import Thread, Timer

from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RenderResultListAction import \
    RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import \
    ExtensionCustomAction
from ulauncher.api.shared.event import (ItemEnterEvent, KeywordQueryEvent,
                                        PreferencesEvent,
                                        PreferencesUpdateEvent)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.config import CACHE_DIR

from gh.listeners.query import KeywordQueryEventListener
from gh.listeners.preferences import PreferencesEventListener, PreferencesUpdateEventListener
from gh.listeners.custom import ItemEnterEventListener
from gh.cache import Cache
from gh.actions import REFRESH_DATA
from gh.github_sync import GitHubDataSync
from gh.constants import ISSUE_FILTER_CREATED, ISSUE_FILTER_ASSIGNED, \
    PR_FILTER_CREATED, PR_FILTER_ASSIGNED, DOCS_BASE_URL
from github.AuthenticatedUser import AuthenticatedUser
from github import GithubException, Github

from datetime import datetime, timedelta

from gh.utils import remove_html

gi.require_version('Notify', '0.7')

from gi.repository import Notify  # noqa

logger = logging.getLogger(__name__)

FETCH_INTERVAL = 86400
GITHUB_NOTIFICATIONS_MINIMUM_DAYS = 15  # Only return new notications in the last X days
MAX_LIST_ITEMS = 8


class GitHubExtension(Extension):
    """ Main Extension class """

    def __init__(self):
        logger.info('Initializing GitHub Extension')
        super(GitHubExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent,
                       PreferencesUpdateEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

        self.icon_path = 'images/icon.png'
        self.github: Github = None
        self.user: AuthenticatedUser = None
        self.cache = Cache(CACHE_DIR)

        Notify.init("Ulauncher GitHub")

    def refresh_user(self):
        """ Updates the current logged in user in the extension"""
        self.user = self.github.get_user()

    def refresh_data(self):
        """ Spawns a new Thread and refresh the local cached data """
        th = Thread(target=self.fetch_data_from_github)
        th.daemon = True
        th.start()

    def fetch_data_from_github(self):
        """
        Fetch user repositories, gists and other data from GitHub.
        This should re run in a separate thread.
        """

        sync_service = GitHubDataSync(self.github, self.cache)

        try:

            self.show_notification("Indexing GitHub data")

            start_time = time.time()

            sync_service.execute()

            execution_time = time.time() - start_time

            self.show_notification(
                "GitHub data indexed with success in {} seconds".format(
                    int(execution_time)))
        except Exception as e:
            self.show_notification(
                "An error occurred when indexing data from GitHub: {}".format(
                    e))

        timer = Timer(FETCH_INTERVAL, self.fetch_data_from_github)
        timer.daemon = True
        timer.start()

    def show_message_no_results(self, search_query):
        return RenderResultListAction([
            ExtensionResultItem(
                icon=self.icon_path,
                name='No results found that matches your search query: %s' %
                search_query,
                highlightable=False,
                on_enter=HideWindowAction())
        ])

    def show_notification(self, text: str):
        """
        Shows a notification
        Args:
          text (str): The text to display on the notification
        """
        Notify.Notification.new("Ulauncher GitHub", text).show()

    def handle_github_exception(self, e: GithubException):
        logger.error(e)
        return RenderResultListAction([
            ExtensionResultItem(
                icon=self.icon_path,
                name='An error ocurred when connecting to GitHub',
                description=str(e),
                highlightable=False,
                on_enter=HideWindowAction())
        ])

    def user_account(self):
        """ Show Information and quick shortcuts to user account actions"""
        return RenderResultListAction([
            ExtensionSmallResultItem(icon=self.icon_path,
                                     name="Logged in as %s (%s)" %
                                     (self.user.name, self.user.login),
                                     highlightable=False,
                                     on_enter=OpenUrlAction(
                                         self.user.html_url)),
            ExtensionSmallResultItem(
                icon=self.icon_path,
                name="Developer Settings",
                on_enter=OpenUrlAction("https://github.com/settings/apps")),
            ExtensionSmallResultItem(
                icon=self.icon_path,
                name="Billing Plans",
                on_enter=OpenUrlAction("https://github.com/settings/billing"))
        ])

    def search_public_repos(self, query):
        """ Search public repos """

        if not query or len(query) < 3:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=self.icon_path,
                    name='Please keep typing your search query',
                    description='Minimum 3 chars',
                    highlightable=False,
                    on_enter=HideWindowAction())
            ])

        try:
            repos = self.github.search_repositories(
                query=query)[:MAX_LIST_ITEMS]
        except GithubException as e:
            return self.handle_github_exception(e)

        items = []

        for repo in repos:
            items.append(
                ExtensionResultItem(
                    icon=self.icon_path,
                    name="%s (%s stars)" % (repo.name, repo.stargazers_count),
                    description=repo.description or "",
                    on_enter=OpenUrlAction(repo.html_url),
                    on_alt_enter=CopyToClipboardAction(repo.html_url)))

        return RenderResultListAction(items)

    def search_users(self, query):
        """ Search GitHub users """

        if not query or len(query) < 3:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=self.icon_path,
                    name='Please keep typing your search query',
                    description='Minimum 3 chars',
                    highlightable=False,
                    on_enter=HideWindowAction())
            ])

        try:
            users = self.github.search_users(query=query,
                                             sort="followers",
                                             order="desc")[:MAX_LIST_ITEMS]
        except GithubException as e:
            logger.error(e)
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=self.icon_path,
                    name='An error ocurred when connecting to GitHub',
                    description=str(e),
                    highlightable=False,
                    on_enter=HideWindowAction())
            ])

        items = []

        for user in users:
            name = ""
            if user.name:
                name = user.name
            else:
                name = user.login

            items.append(
                ExtensionResultItem(icon=self.icon_path,
                                    name=name,
                                    on_enter=OpenUrlAction(user.html_url),
                                    on_alt_enter=CopyToClipboardAction(
                                        user.html_url)))

        return RenderResultListAction(items)

    def user_repos(self, query):
        """ List the repos owned by the user """

        items = []

        repos = self.cache.get_repos()

        for repo in repos[:MAX_LIST_ITEMS]:

            if query and query.lower() not in repo['fullname'].lower():
                continue

            items.append(
                ExtensionResultItem(icon=self.icon_path,
                                    name=repo['fullname'],
                                    description=repo['description'] or "",
                                    highlightable=not query,
                                    on_enter=OpenUrlAction(repo['url']),
                                    on_alt_enter=CopyToClipboardAction(
                                        repo['url'])))

        items.append(
            ExtensionSmallResultItem(
                icon='images/icon_open.png',
                name='Open on GitHub',
                on_enter=OpenUrlAction(
                    "https://github.com/{}?tab=repositories".format(
                        self.user.login))))
        return RenderResultListAction(items)

    def user_gists(self, query):
        """ List user gists"""

        query = query.lower()
        gists = self.cache.get_gists()

        items = []
        for gist in gists[:MAX_LIST_ITEMS]:

            desc = gist['description'] or ""

            if query and (query not in desc.lower()
                          and query not in gist['filename'].lower()):
                continue

            items.append(
                ExtensionResultItem(icon=self.icon_path,
                                    name=gist['filename'],
                                    description=desc,
                                    highlightable=not query,
                                    on_enter=OpenUrlAction(gist['url']),
                                    on_alt_enter=CopyToClipboardAction(
                                        gist['url'])))

            items.append(
                ExtensionSmallResultItem(
                    icon='images/icon_open.png',
                    name='Open on GitHub',
                    on_enter=OpenUrlAction("https://gist.github.com/mine")))

        return RenderResultListAction(items)

    def user_orgs(self, query):
        """ List the Organizations the user belongs to"""

        try:
            orgs = self.github.get_user().get_orgs()
        except GithubException as e:
            return self.handle_github_exception(e)

        items = []
        for org in orgs[:8]:

            if query and query.lower() not in org.name.lower():
                continue

            items.append(
                ExtensionResultItem(icon=self.icon_path,
                                    name=org.name,
                                    highlightable=not query,
                                    on_enter=OpenUrlAction(org.html_url),
                                    on_alt_enter=CopyToClipboardAction(
                                        org.html_url)))

        return RenderResultListAction(items[:MAX_LIST_ITEMS])

    def user_starred_repos(self, query):
        """ List the repositories the user has starred"""

        items = []
        repos = self.cache.get_starred_repos()
        for repo in repos[:MAX_LIST_ITEMS]:

            if query and query.lower() not in repo['name'].lower():
                continue

            items.append(
                ExtensionResultItem(icon=self.icon_path,
                                    name=repo['name'],
                                    description=repo['description'],
                                    on_enter=OpenUrlAction(repo['url']),
                                    on_alt_enter=CopyToClipboardAction(
                                        repo['url'])))

            items.append(
                ExtensionSmallResultItem(
                    icon='images/icon_open.png',
                    name='Open on GitHub',
                    on_enter=OpenUrlAction(
                        "https://github.com/{}?tab=stars".format(
                            self.user.login))))

        return RenderResultListAction(items)

    def user_issues(self, query, filter=ISSUE_FILTER_ASSIGNED):
        """ List the issues associated to the user"""
        try:

            if filter == ISSUE_FILTER_ASSIGNED:
                search_query = "{} in:title type:issue is:open assignee:@me".format(
                    query)
                github_url = "https://github.com/issues"
            elif filter == ISSUE_FILTER_CREATED:
                search_query = "{} in:title type:issue is:open author:@me".format(
                    query)
                github_url = "https://github.com/issues/assigned"

            issues = self.github.search_issues(search_query, sort="updated")
            items = []

            if issues.totalCount == 0:
                return self.show_message_no_results(query)

            for issue in issues[:MAX_LIST_ITEMS]:
                items.append(
                    ExtensionResultItem(
                        icon=self.icon_path,
                        name=issue.title,
                        description="Last Updated: {}\nRepository: {}\n".
                        format(issue.updated_at, issue.repository.name),
                        on_enter=OpenUrlAction(issue.html_url)))

            items.append(
                ExtensionSmallResultItem(icon='images/icon_open.png',
                                         name='Open on GitHub',
                                         on_enter=OpenUrlAction(github_url)))

            return RenderResultListAction(items)
        except GithubException as e:
            return self.handle_github_exception(e)

    def user_pull_requests(self, query, filter=PR_FILTER_ASSIGNED):
        """ Lists Open Pull Requests that are assigned or created by the user"""
        try:

            if filter == PR_FILTER_ASSIGNED:
                search_query = "{} in:title type:pr is:open assignee:@me".format(
                    query)
                github_url = "https://github.com/pulls/assigned"
            elif filter == PR_FILTER_CREATED:
                search_query = "{} in:title type:pr is:open author:@me".format(
                    query)
                github_url = "https://github.com/pulls"

            prs = self.github.search_issues(search_query, sort="updated")
            items = []

            if prs.totalCount == 0:
                return self.show_message_no_results(query)
            for pr in prs[:MAX_LIST_ITEMS]:
                items.append(
                    ExtensionResultItem(
                        icon=self.icon_path,
                        name=pr.title,
                        description="Last Updated: {}\nRepository: {}".format(
                            pr.updated_at, pr.repository.name),
                        on_enter=OpenUrlAction(pr.html_url)))

            items.append(
                ExtensionSmallResultItem(icon='images/icon_open.png',
                                         name='Open on GitHub',
                                         on_enter=OpenUrlAction(github_url)))

            return RenderResultListAction(items)
        except GithubException as e:
            return self.handle_github_exception(e)

    def user_notifications(self, query):
        """ List the user notifications"""
        try:

            start_date = datetime.now() - timedelta(
                GITHUB_NOTIFICATIONS_MINIMUM_DAYS)
            notifications = self.user.get_notifications(participating=True,
                                                        since=start_date)
            items = []

            if not notifications:
                return self.show_message_not_results(query)

            for notification in notifications[:MAX_LIST_ITEMS]:
                notification_url = notification.subject.url.replace(
                    "https://api.github.com/repos", "https://github.com")

                type = notification.subject.type
                if type == "PullRequest":
                    notification_url = notification_url.replace(
                        "pulls", "pull")
                items.append(
                    ExtensionResultItem(
                        icon=self.icon_path,
                        name=notification.subject.title,
                        description="Date: {}\nType: {}\nRepository: {}".
                        format(notification.updated_at,
                               notification.subject.type,
                               notification.repository.full_name),
                        on_enter=OpenUrlAction(notification_url)))

            items.append(
                ExtensionSmallResultItem(
                    icon='images/icon_open.png',
                    name='Open on GitHub',
                    on_enter=OpenUrlAction(
                        "https://github.com/notifications")))
            return RenderResultListAction(items)
        except GithubException as e:
            return self.handdle_github_exception(e)

    def search_documentation(self, query):
        """ Search dcoumentation """
        search_url = "{}/search".format(DOCS_BASE_URL)

        r = requests.get(search_url, {
            'language': 'en',
            'version': 'dotcom',
            'query': query
        })

        if r.status_code != 200:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=self.icon_path,
                    name="Error Fetching documentation from GitHub",
                    description=  # noqa E251
                    "GitHub responded with an unexpected status code: %s" %
                    r.status_code,
                    highlightable=False,
                    on_enter=HideWindowAction())
            ])

        data = r.json()

        if len(data) == 0:
            return self.show_message_no_results(query)

        items = []
        for result in data[:MAX_LIST_ITEMS]:
            items.append(
                ExtensionResultItem(icon=self.icon_path,
                                    name=remove_html(result["title"]),
                                    description=remove_html(
                                        result["breadcrumbs"]),
                                    on_enter=OpenUrlAction("{}{}".format(
                                        DOCS_BASE_URL, result["url"]))))

        return RenderResultListAction(items)

    def show_options(self):
        """ Show some extension options"""
        return RenderResultListAction([
            ExtensionSmallResultItem(icon=self.icon_path,
                                     name="Refresh Extension Cache",
                                     highlightable=False,
                                     on_enter=ExtensionCustomAction(
                                         {"action": REFRESH_DATA}))
        ])
