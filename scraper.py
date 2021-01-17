import re
from typing import SupportsRound

import dataset
import get_retries
from bs4 import BeautifulSoup
from dateutil import parser

from hashlib import md5

from tqdm import tqdm

db = dataset.connect("sqlite:///data.sqlite")

tab_incidents = db["incidents"]
tab_sources = db["sources"]
tab_chronicles = db["chronicles"]


tab_chronicles.upsert(
    {
        "iso3166_1": "DE",
        "iso3166_2": "DE-BW",
        "chronicler_name": "LEUCHTLINIE",
        "chronicler_description": "LEUCHTLINIE steht allen Menschen in Baden-Württemberg als direkte Hilfs- und Anlaufstelle zur Seite, die von rechter, rassistischer und antisemitischer Gewalt (Übergriffe auf die eigene Person durch Gewalttaten, Bedrohung, Beleidigung und Verleumdung, Pöbeleien oder wirtschaftliche Schädigung, etc.) betroffen oder Zeuge einer solchen Tat sind.",
        "chronicler_url": "https://www.leuchtlinie.de",
        "chronicle_source": "https://www.leuchtlinie.de/chronik",
    },
    ["chronicler_name"],
)


BASE_URL = "https://www.leuchtlinie.de/chronik/?page="


def fetch(url):
    html_content = get_retries.get(url, verbose=True, max_backoff=128).text
    soup = BeautifulSoup(html_content, "lxml")
    return soup


# https://stackoverflow.com/a/7160778/4028896
def is_url(s):
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return re.match(regex, s) is not None


def process_report(report, url):
    title = report.select_one(".views-field-title").get_text().strip()
    description = (
        report.select_one(".views-field-body .field-content")
        .get_text(separator="\n")
        .strip()
    )

    source = (
        report.select_one(".views-field-field-chronik-quelle")
        .get_text()
        .replace("Quelle:", "")
        .strip()
    )
    city = report.select_one(".views-field-field-chronik-stadt").get_text().strip()
    date = parser.parse(report.select_one(".date-display-single").get("content"))

    rg_id = (
        "leuchtlinie-"
        + md5((url + date.isoformat() + city + description).encode()).hexdigest()
    )

    data = dict(
        title=title, description=description, city=city, date=date, rg_id=rg_id, url=url
    )
    tab_incidents.upsert(data, ["rg_id"])

    source_data = {"rg_id": rg_id, "name": source}

    if is_url(source):
        source_data["url"] = source

    tab_sources.upsert(source_data, ["rg_id", "name"])


def process_page(page, url):
    for row in page.select("div.view-chronik div.view-content div.views-row"):
        process_report(row, url)


initial_soup = fetch(BASE_URL)

process_page(initial_soup, BASE_URL)

last_page = int(
    re.findall(r"\d+", initial_soup.select_one("li.pager-last.last a").get("href"))[0]
)

i = 1
while i <= last_page:
    url = BASE_URL + str(i)
    soup = fetch(url)
    process_page(soup, url)
    i += 1
