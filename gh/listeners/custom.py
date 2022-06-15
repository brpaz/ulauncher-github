from ulauncher.api.client.EventListener import EventListener
from gh.actions import REFRESH_DATA


class ItemEnterEventListener(EventListener):
    """ Handles Custom ItemEnter event """

    def on_event(self, event, extension):
        """ handle function """
        data = event.get_data()
        if data['action'] == REFRESH_DATA:
            return extension.refresh_data()
