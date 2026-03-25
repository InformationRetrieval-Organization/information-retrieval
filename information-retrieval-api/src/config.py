from datetime import datetime, time
import logging
import os
import sys

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# API Keys
NYT_API_KEY = os.getenv("NYT_API_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

# File Paths
CWD = os.getcwd()
GUARDIAN_FILE_PATH = os.path.join(CWD, "files", "The Guardian.csv")
NYT_FILE_PATH = os.path.join(CWD, "files", "New York Times.csv")
GNEWS_FILE_PATH = os.path.join(CWD, "files", "GNews.csv")
GROUND_DATASET_FILE_PATH = os.path.join(CWD, "files", "ground_truth.csv")
INVERTED_INDEX_FILE_PATH = os.path.join(CWD, "files", "inverted_index.csv")
EVAL_MEASURES_IMAGE_PATH = os.path.join(CWD, "files", "evaluation_measures.png")
EVAL_TEMP_RELEVANCE_IMAGE_PATH = os.path.join(CWD, "files", "evaluation_temporal_relevance.png")
EVAL_MEASURES_CSV_PATH = os.path.join(CWD, "files", "evaluation_measures.csv")

# Crawl Dates
GROUND_DATASET_START_DATE = None
GROUND_DATASET_END_DATE = None

try:
    start_date_str = os.getenv("GROUND_DATASET_START_DATE")
    if start_date_str:
        GROUND_DATASET_START_DATE = datetime.combine(
            datetime.strptime(start_date_str, "%Y-%m-%d").date(),
            time.min,
        )
    end_date_str = os.getenv("GROUND_DATASET_END_DATE")
    if end_date_str:
        GROUND_DATASET_END_DATE = datetime.combine(
            datetime.strptime(end_date_str, "%Y-%m-%d").date(), time.max
        )
except ValueError:
    logger.warning("Please provide valid dates in the .env file.")

# Flask Environment
FASTAPI_ENV = os.getenv("FASTAPI_ENV")

# Date Coefficient
MAX_DATA_COEFFICIENT = 2.0