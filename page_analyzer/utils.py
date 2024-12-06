import requests
from bs4 import BeautifulSoup


def check_url(url):
    try:
        req = requests.get(url)
        status_code = req.status_code
        if status_code != 200:
            raise requests.RequestException
    except requests.RequestException:
        return None, None, None, None, status_code

    html_content = req.text
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

    return h1, title, content, status_code
