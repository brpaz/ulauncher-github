import logging

from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from gh.constants import ISSUE_FILTER_ASSIGNED, ISSUE_FILTER_CREATED, PR_FILTER_ASSIGNED, PR_FILTER_CREATED

logger = logging.getLogger(__name__)


class KeywordQueryEventListener(EventListener):
    """ Listen to Input events """

    def on_event(self, event: KeywordQueryEvent, extension: Extension):
        """ Handles event """

        query = event.get_argument() or ""
        keyword_id = self.get_keyword_id(extension.preferences,
                                         event.get_keyword())

        if keyword_id == "kw_gists":
            return extension.user_gists(query)

        if keyword_id == "kw_user_repos":
            return extension.user_repos(query)

        if keyword_id == "kw_user_organizations":
            return extension.user_orgs(query)

        if keyword_id == "kw_public_repos":
            return extension.search_public_repos(query)

        if keyword_id == "kw_public_users":
            return extension.search_users(query)

        if keyword_id == "kw_user_starred_repos":
            return extension.user_starred_repos(query)

        if keyword_id == "kw_issues_assigned":
            return extension.user_issues(query, ISSUE_FILTER_ASSIGNED)

        if keyword_id == "kw_issues_created":
            return extension.user_issues(query, ISSUE_FILTER_CREATED)

        if keyword_id == "kw_notifications":
            return extension.user_notifications(query)

        if keyword_id == "kw_user_pulls_created":
            return extension.user_pull_requests(query, PR_FILTER_CREATED)

        if keyword_id == "kw_user_pulls_assigned":
            return extension.user_pull_requests(query, PR_FILTER_ASSIGNED)

        if keyword_id == "kw_docs":
            return extension.search_documentation(query)

        if keyword_id == "kw_account":
            return extension.user_account()

        return extension.show_options()

    def get_keyword_id(self, preferences: dict, keyword: str) -> str:
        """ Returns the keyword ID from the keyword name """
        kw_id = None
        for key, value in preferences.items():
            if value == keyword:
                kw_id = key
                break

        return kw_id
