import validators
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def validate_url(url: str) -> list:
    """Validates url and returns list with url errors if happens"""

    errors = []
    if not url:
        errors.append('URL обязателен')
    if len(url) > 255:
        errors.append('URL превышает 255 символов')
    if not validators.url(url) or (validators.url(url) and errors):
        errors.append('Некорректный URL')
    return errors


def normalize_url(url: str) -> str:
    """Returns normalized URL: https://example.ru"""

    parsed_url = urlparse(url)
    return parsed_url._replace(
        path='',
        params='',
        query='',
        fragment=''
    ).geturl()


def parse_page(page_text: str) -> dict:
    """Getting h1, title and description from page content"""

    checks = {}
    soup = BeautifulSoup(page_text, 'html.parser')
    checks['h1'] = soup.h1.get_text().strip() if soup.h1 else ''
    checks['title'] = soup.title.string if soup.title else ''
    all_metas = soup.find_all('meta')
    for meta in all_metas:
        if meta.get('name') == 'description':
            checks['description'] = meta.get('content', '')
    return checks
