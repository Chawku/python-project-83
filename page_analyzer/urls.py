from urllib.parse import urlparse

import validators


def validate_url(url_string):
    if not validators.url(url_string):
        return False, "Некорректный URL"
    return True, None


def normalize_url(url_string):
    parsed_url = urlparse(url_string)
    return f'{parsed_url.scheme}://{parsed_url.netloc}'
