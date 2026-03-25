from datetime import datetime
import logging
import requests
import os
import time as t
from helper import append_to_csv
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from config import (
    GNEWS_API_KEY,
    GROUND_DATASET_START_DATE,
    GROUND_DATASET_END_DATE,
    GNEWS_FILE_PATH,
)

logger = logging.getLogger(__name__)


def get_gnews_data(
    api_key: str, begin_date: datetime, end_date: datetime, page: int = 1
):
    """
    Get news articles from GNews API.
    """
    url = "https://gnews.io/api/v4/search"
    params = {
        "apikey": api_key,
        "from": begin_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "q": "korea",
        # "country": "us",
        # "lang": "en",
        "max": 100,  # this is the maximum
        "expand": "content",
        "sortby": "publishedAt",  # "relevance", "publishedAt
        "page": page,
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()["articles"]
    else:
        return None


def crawl_gnews_data() -> None:
    """
    Crawl news articles from GNews API and save them to a CSV file.
    """

    logger.info("Crawling GNews data...")
    logger.info("Begin date: %s", GROUND_DATASET_START_DATE)
    logger.info("End date: %s", GROUND_DATASET_END_DATE)

    if os.path.exists(GNEWS_FILE_PATH):
        os.remove(GNEWS_FILE_PATH)

    page = 1
    total_articles = 0
    while True:
        articles = get_gnews_data(
            api_key=GNEWS_API_KEY,
            begin_date=GROUND_DATASET_START_DATE,
            end_date=GROUND_DATASET_END_DATE,
            page=page,
        )
        if not articles:
            break

        data = []
        for article in articles:
            data.append(
                {
                    "title": article["title"],
                    "content": article["content"],
                    "published_on": article["publishedAt"],
                    "link": article["source"]["url"],
                    "source": article["source"]["name"],
                }
            )

        append_to_csv(GNEWS_FILE_PATH, data)

        total_articles += len(data)
        page += 1

        # Pause for 0.2 second to avoid exceeding the rate limit of 6 requests per second
        t.sleep(0.2)

    logger.info("Total articles retrieved: %s", total_articles)


if __name__ == "__main__":
    crawl_gnews_data()
