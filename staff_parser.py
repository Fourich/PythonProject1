import asyncio
from urllib.parse import urljoin

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup

import site_parser


BASE_URL = "https://omgtu.ru"
STAFF_LINK_TEXTS = {"Состав кафедры", "Состав секции", "Состав"}


async def fetch_soup(url, session, semaphore):
    async with semaphore:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(url, timeout=timeout) as response:
            response.raise_for_status()
            html = await response.text()
            return BeautifulSoup(html, "html.parser")


async def get_department_links(session, semaphore):
    soup = await fetch_soup(site_parser.DEPARTMENTS_URL, session, semaphore)
    return [urljoin(BASE_URL, link.get("href")) for link in soup.select("#pagecontent ul a")]


async def get_department_info(department_url, session, semaphore):
    soup = await fetch_soup(department_url, session, semaphore)

    title_tag = soup.find("title")
    department_name = title_tag.text.strip() if title_tag else "Название не найдено"

    breadcrumbs = soup.select(".main__breadcrumbs .breadcrumbs__item")
    breadcrumbs_text = [" ".join(item.text.split()) for item in breadcrumbs if item.text.strip()]

    faculty_name = "Факультет не указан"
    ignored_items = {"Об университете", "Факультеты", "Институты", "Кафедры"}

    for item in reversed(breadcrumbs_text):
        if item not in ignored_items and not item.lower().startswith("кафедра"):
            faculty_name = item
            break

    faculty_fixes = {
        "Кафедра «Автоматизированные системы обработки информации и управления» (АСОИУ)": "Факультет информационных технологий и компьютерных систем",
    }

    if faculty_name.lower() in ["факультеты", "институты", "кафедры", "факультет не указан"]:
        faculty_name = faculty_fixes.get(department_name, faculty_name)

    staff_url = None
    for link in soup.select(".sidebar-menu__list a"):
        if link.text.strip() in STAFF_LINK_TEXTS:
            staff_url = urljoin(BASE_URL, link.get("href"))
            break

    return faculty_name, department_name, staff_url


async def get_staff_names(staff_url, session, semaphore):
    soup = await fetch_soup(staff_url, session, semaphore)

    names = []
    for fio in soup.select("#pagecontent a[target='_blank']"):
        name = " ".join(fio.text.split()).title()
        if name:
            names.append(name)

    return names


async def process_department(department_url, session, semaphore, target_letter):
    faculty_name, department_name, staff_url = await get_department_info(department_url, session, semaphore)

    if not staff_url:
        return []

    staff_names = await get_staff_names(staff_url, session, semaphore)

    result = []
    for name in staff_names:
        if name.upper().startswith(target_letter.upper()):
            result.append([faculty_name, department_name, name])

    return result


async def parse_staff(target_letter):
    semaphore = asyncio.Semaphore(10)

    async with aiohttp.ClientSession() as session:
        department_urls = await get_department_links(session, semaphore)
        tasks = [process_department(url, session, semaphore, target_letter) for url in department_urls]
        results = await asyncio.gather(*tasks)

    rows = []
    for department_rows in results:
        rows.extend(department_rows)

    df = pd.DataFrame(rows, columns=["Факультет", "Кафедра", "ФИО"])
    df.insert(0, "№", range(1, len(df) + 1))
    return df


def get_staff_by_letter(target_letter="Б"):
    return asyncio.run(parse_staff(target_letter))
