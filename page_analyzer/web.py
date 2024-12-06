import requests
from bs4 import BeautifulSoup


def fetch_page_data(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    return {
        'status_code': response.status_code,
        'h1': (soup.find('h1').text if soup.find('h1') else ''),
        'title': (soup.find('title').text if soup.find('title') else ''),
        'content': (soup.find('meta', attrs={'name': 'description'}).get('content', '') if soup.find('meta', attrs={'name': 'description'}) else '')
    }
