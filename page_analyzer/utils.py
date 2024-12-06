import requests
from bs4 import BeautifulSoup
from flask import flash, get_flashed_messages
import validators
from urllib.parse import urlparse


def is_valid_url(url_string):
    return validators.url(url_string)


def normalize_url(url_string):
    url_string = urlparse(url_string)
    return f'{url_string.scheme}://{url_string.netloc}'


def make_request(url):
    try:
        req = requests.request("GET", url)
        status_code = req.status_code
        if status_code != 200:
            raise requests.RequestException
        return req
    except requests.RequestException:
        return None


def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    h1 = soup.find('h1')
    h1 = h1.text if h1 else ''
    title = soup.find('title')
    title = title.text if title else ''
    attrs = {'name': 'description'}
    meta_description_tag = soup.find('meta', attrs=attrs)
    content = ''
    if meta_description_tag:
        content = meta_description_tag.get("content")
        content = content if content else ''
    return {'h1': h1, 'title': title, 'content': content}


def get_messages():
    return get_flashed_messages(with_categories=True)


def flash_message(message, category):
    flash(message, category)
