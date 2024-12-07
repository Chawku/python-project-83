from bs4 import BeautifulSoup


def extract_page_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    h1 = soup.find('h1').text if soup.find('h1') else ''
    title = soup.find('title').text if soup.find('title') else ''
    meta_description_tag = soup.find('meta', attrs={'name': 'description'})
    content = meta_description_tag.get("content") if meta_description_tag else ''
    
    return {
        'h1': h1,
        'title': title,
        'content': content
    }
