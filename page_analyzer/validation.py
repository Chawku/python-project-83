import validators
from urllib.parse import urlparse


def validate_url(url_string):
    if not validators.url(url_string):
        return False
    parsed_url = urlparse(url_string)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"
