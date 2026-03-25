from datetime import datetime
import logging
import requests
import asyncio
import os
from bs4 import BeautifulSoup
import sys
from helper import append_to_csv
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import time
from concurrent.futures import as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from config import (
    GUARDIAN_API_KEY,
    GROUND_DATASET_START_DATE,
    GROUND_DATASET_END_DATE,
    GUARDIAN_FILE_PATH,
)

GUARDIAN_API_URL = "https://content.guardianapis.com/search"
QUERY_PARAMS = {
    "api-key": GUARDIAN_API_KEY,
    "from-date": GROUND_DATASET_START_DATE.strftime("%Y-%m-%d"),  # YYYY-MM-DD
    "to-date": GROUND_DATASET_END_DATE.strftime("%Y-%m-%d"),  # YYYY-MM-DD
    "use-date": "published",
    "order-by": "newest",
    "page-size": 10,  # this is the maximum
    "q": "korea",
}

logger = logging.getLogger(__name__)


def get_guardian_data(page: int):
    """
    Get news articles from The Guardian API.
    """

    params = QUERY_PARAMS.copy()
    params["page"] = page
    return requests.get(GUARDIAN_API_URL, params=params)


def fetch_page_data(page: int):
    """
    Fetch news articles from a page of The Guardian API.
    """

    response = get_guardian_data(page)

    if response.status_code == 200:
        data = response.json()
        if not data["response"]["results"]:
            return [], 0

        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            articles = list(
                executor.map(fetch_article_data, data["response"]["results"])
            )

        return articles, data["response"]["pages"]
    else:
        return [], 0


def get_full_article(url):
    """
    Get the full text of a news article from The Guardian.
    """

    response = requests.get(url)
    if response.status_code != 200:
        logger.warning("Failed to get page: %s", url)
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    article_body = soup.find("div", {"id": "maincontent"})

    return (
        " ".join([p.get_text() for p in article_body.find_all("p")])
        if article_body
        else None
    )


def fetch_article_data(result):
    """
    Fetch data of a news article from The Guardian API.
    """

    article_url = result["webUrl"]
    full_text = get_full_article(article_url)
    return {
        "title": result["webTitle"],
        "content": full_text,
        "published_on": result["webPublicationDate"],
        "link": article_url,
        "source": "The Guardian",
    }


async def crawl_guardian_data() -> None:
    """
    Crawl news articles from The Guardian API and save them to a CSV file.
    """

    start_time = time.time()

    logger.info("Crawling The Guardian data...")
    logger.info("Begin date: %s", GROUND_DATASET_START_DATE)
    logger.info("End date: %s", GROUND_DATASET_END_DATE)

    if os.path.exists(GUARDIAN_FILE_PATH):
        os.remove(GUARDIAN_FILE_PATH)

    # synchronous call to get the first page
    articles, total_pages = fetch_page_data(1)
    if total_pages == 0:
        logger.warning("Failed to get the total number of pages")
        return

    total_articles = len(articles)

    # asynchronous call to get the rest of the pages
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = {
            executor.submit(fetch_page_data, page) for page in range(2, total_pages + 1)
        }
        for future in as_completed(futures):
            page_articles, _ = future.result()
            if not page_articles:
                break

            articles.extend(page_articles)
            total_articles += len(page_articles)

    # Sort the articles by published date, newest on top
    articles.sort(key=lambda article: article["published_on"], reverse=True)

    # Append the articles to the CSV file
    append_to_csv(GUARDIAN_FILE_PATH, articles)

    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info("Total articles retrieved: %s", total_articles)
    logger.info("Elapsed time: %s seconds", elapsed_time)


if __name__ == "__main__":
    asyncio.run(crawl_guardian_data())
