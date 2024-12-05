from urllib.parse import urlparse
import validators
import requests
from bs4 import BeautifulSoup


def validate_url(url):
    return validators.url(url)


def extract_url_data(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def fetch_url_content(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    h1 = soup.find('h1')
    title = soup.find('title')
    description = soup.find('meta', attrs={'name': 'description'})
    return response.status_code, h1.text if h1 else '', title.text if title else '', description['content'] if description else ''
