import logging

from ulauncher.api.client.EventListener import EventListener
from github import Github, GithubException

logger = logging.getLogger(__name__)


class PreferencesEventListener(EventListener):
    """ Handles preferences initialization event """

    def on_event(self, event, extension):
        """ Handle event """
        extension.os_notifs = event.preferences['os_notifs']
        logger.error(extension.os_notifs)
        extension.github = Github(event.preferences['access_token'])
        try:
            extension.refresh_user()
            extension.refresh_data()
        except GithubException as ex:
            logger.error(ex)
            extension.user = None


class PreferencesUpdateEventListener(EventListener):
    """ Handles Preferences Update event """

    def on_event(self, event, extension):
        """ Event handler """
        if event.id == 'access_token':
            extension.github = Github(event.new_value)
            try:
                extension.refresh_user()
                extension.refresh_data()
            except GithubException as ex:
                logger.error(ex)
                extension.user = None
