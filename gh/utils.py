import re


def remove_html(text):
    """ Helper function to remove HTML tags from a string"""
    regex = re.compile(r'<[^>]+>')
    return regex.sub('', text)
