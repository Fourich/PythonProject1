import requests
from bs4 import BeautifulSoup


DEPARTMENTS_URL = 'https://omgtu.ru/general_information/the-structure/the-department-of-university.php'
FACULTIES_URL = 'https://omgtu.ru/general_information/faculties/'


def get_list_from_site(url):
    page = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    page.encoding = page.apparent_encoding

    soup = BeautifulSoup(page.text, "html.parser")
    page_content = soup.find('div', id='pagecontent')

    items = []
    if page_content:
        list_block = page_content.find('ul')
        if list_block:
            for link in list_block.find_all('a'):
                name = ' '.join(link.text.split())
                if name:
                    items.append(name)

    return items


def get_departments():
    return get_list_from_site(DEPARTMENTS_URL)


def get_faculties():
    return get_list_from_site(FACULTIES_URL)
