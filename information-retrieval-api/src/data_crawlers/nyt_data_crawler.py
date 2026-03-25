# NOTE: not used in the final project, but kept for reference
import logging
import os
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import asyncio
from helper import append_to_csv
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from config import (
    NYT_API_KEY,
    GROUND_DATASET_START_DATE,
    GROUND_DATASET_END_DATE,
    NYT_FILE_PATH,
)

logger = logging.getLogger(__name__)


async def crawl_nyt_data() -> None:
    """
    Crawl news articles from New York Times and save them to a CSV file.
    """

    logger.info("Crawling New York Times data...")
    logger.info("Begin date: %s", GROUND_DATASET_START_DATE)
    logger.info("End date: %s", GROUND_DATASET_END_DATE)

    if os.path.exists(NYT_FILE_PATH):
        os.remove(NYT_FILE_PATH)

    driver = login_nyt()

    # because there is a limit of 10 articles per page, we need to loop through all pages
    page = 1
    total_articles = 0
    while True:
        articles = get_articles(
            api_key=NYT_API_KEY,
            begin_date=GROUND_DATASET_START_DATE,
            end_date=GROUND_DATASET_END_DATE,
            query="korea",
            page=page,
        )
        if not articles:
            break

        data = []
        for article in articles:
            full_text = get_full_article(article["web_url"], driver)
            published_on = datetime.fromisoformat(article["pub_date"])

            data.append(
                {
                    "title": article["headline"]["main"],
                    "content": full_text,
                    "published_on": published_on,
                    "link": article["web_url"],
                    "source": "New York Times",
                }
            )

        append_to_csv(NYT_FILE_PATH, data)

        total_articles += len(data)
        page += 1

    logger.info("Total articles retrieved: %s", total_articles)
    driver.quit()


def get_articles(
    api_key: date, begin_date: date, end_date: date, query: str, page: int = 1
):
    """
    Get news articles from New York Times API.
    """
    url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    params = {
        "q": query,
        "begin_date": begin_date,
        "end_date": end_date,
        "api-key": api_key,
        "page": page,
    }

    # limit of 1 request per minute and 500 per day
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()["response"]["docs"]
    else:
        return None


def get_full_article(url, driver):
    """
    Get the full text of a news article from New York Times.
    """
    # Use the provided webdriver to access the logged-in session
    driver.get(url)

    # Wait up to 10 seconds for the body tag to appear
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "articleBody"))
        )
    except TimeoutException:
        logger.warning(
            "TimeoutException: Element with tag name 'articleBody' not found on %s",
            url,
        )
        return None

    soup = BeautifulSoup(
        driver.page_source, "html.parser"
    )  # Parse the HTML from the webdriver

    article_body = soup.find("section", {"name": "articleBody"})

    if article_body:
        full_text = " ".join([p.get_text() for p in article_body.find_all("p")])
        unwanted_text = "Open this article in the New York Times Audio app on iOS. Subscribe to The Times to read as many articles as you like."
        full_text = full_text.replace(unwanted_text, "")
        return full_text
    else:
        return None


def login_nyt():
    """
    Log in to New York Times and return the webdriver.
    """
    chrome_options = Options()

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://myaccount.nytimes.com/auth/login")

    # uncomment this for automatic login, but i got blocked by NYT for too many requests
    """
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    email_input = driver.find_element("name", "email")
    email_input.clear()
    email_input.send_keys(os.getenv("NYT_EMAIL"))

    # If there's a login button you can click it like this:
    continue_button = driver.find_element(By.XPATH, '//button[normalize-space()="Continue"]')
    continue_button.click()

    # Wait up to 10 seconds for the password field to appear
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))

    # If there's a password field, you can fill it in a similar way:
    password_input = driver.find_element("name", "password")
    password_input.clear()
    password_input.send_keys(os.getenv("NYT_PASSWORD"))

    continue_button = driver.find_element(By.XPATH, '//button[normalize-space()="Log In"]')
    continue_button.click()
    """

    # Pause the script until the user presses Enter
    input("Press Enter after you have completed the verification...")

    return driver


if __name__ == "__main__":
    asyncio.run(crawl_nyt_data())
