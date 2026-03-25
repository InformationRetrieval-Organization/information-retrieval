import logging
from typing import List
from matplotlib.ticker import MaxNLocator
import requests
import json
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from config import (
    GROUND_DATASET_START_DATE,
    GROUND_DATASET_END_DATE,
    GROUND_DATASET_FILE_PATH,
    EVAL_MEASURES_IMAGE_PATH,
    EVAL_TEMP_RELEVANCE_IMAGE_PATH,
    EVAL_MEASURES_CSV_PATH,
)

logger = logging.getLogger(__name__)

base_url = "http://127.0.0.1:8000"
boolean_api_url = f"{base_url}/search/boolean"
vector_space_url = f"{base_url}/search/vector-space"

# TODO: mark the relevant documents for each query manually
# https://github.com/InformationRetrieval-Organization/InformationRetrievalSystem/issues/8
vector_queries = [
    "political corruption scandals",
    "election 2024 turnout",
    "democratic party",
    "women rights people power party",
]

boolean_queries = [
    [{"operator": "AND", "value": "political"}, {"operator": "AND", "value": "corruption"}, {"operator": "OR", "value": "scandals"}],
    [{"operator": "AND", "value": "election"}, {"operator": "OR", "value": "2024"}, {"operator": "OR", "value": "turnout"}],
    [{"operator": "AND", "value": "democratic"}, {"operator": "OR", "value": "party"}],
    [
        {"operator": "AND", "value": "women"},
        {"operator": "AND", "value": "rights"},
        {"operator": "OR", "value": "people"},
        {"operator": "OR", "value": "power"},
        {"operator": "AND", "value": "party"},
    ],
]


def evaluate_search_model(relevant_docs: List[int], retrieved_docs: List[int]) -> tuple:
    """
    Calculate recall, precision, and F1 score.

    Args:
        relevant_docs (List): List of relevant documents
        retrieved_docs (List): List of retrieved documents

    Returns:
        tuple: recall, precision, and F1 score
    """
    relevant_retrieved_docs = set(relevant_docs).intersection(set(retrieved_docs))

    true_positives = len(relevant_retrieved_docs)
    false_positives = len(retrieved_docs) - true_positives
    false_negatives = len(relevant_docs) - true_positives

    recall = true_positives / (true_positives + false_negatives) if relevant_docs else 0
    precision = (
        true_positives / (true_positives + false_positives) if retrieved_docs else 0
    )
    f1 = (
        2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    )

    return recall, precision, f1


def call_boolean_api(query) -> List[dict]:
    """
    Call Boolean API
    TODO: whats with OR and NOT operators?
    """
    url = f"{boolean_api_url}"

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(query), headers=headers)
    response.raise_for_status()

    return response.json()


def call_vector_space_api(query: str) -> List[dict]:
    """
    Call Vector Space API
    """
    query_string = "+".join(query.split())
    url = f"{vector_space_url}?q={query_string}"
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def calculate_temporal_relevance(
    retrieved_docs: List[dict], start_date: datetime, end_date: datetime
) -> dict:
    """
    Calculate temporal relevance.
    Temporal relevance is the number of documents retrieved for each day in the specified date range.

    Args:
        retrieved_docs (List): List of retrieved documents
        start_date (str): Start date in the format 'YYYY-MM-DD'
        end_date (str): End date in the format 'YYYY-MM-DD'

    Returns:
        dict: Number of documents retrieved for each day (date + count)
    """

    # dict with 1 day intervall in the daterange from start_date to end_date
    date_counts = {
        str(start_date + timedelta(days=i)): 0
        for i in range((end_date - start_date).days + 1)
    }

    for doc in retrieved_docs:
        date_time_str = doc["published_on"]

        # convert to datetime object and reset time
        date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%SZ")
        date = date_time_obj.replace(second=0, minute=0, hour=0)
        date = date.strftime("%Y-%m-%d %H:%M:%S")

        if date in date_counts:
            date_counts[date] += 1

    # cut off the time part of the date, because we dont need it
    date_counts = {datetime.strptime(date, "%Y-%m-%d %H:%M:%S").date(): count for date, count in date_counts.items()}
    
    return date_counts


def get_relevant_docs(query: str, ground_truth_df: pd.DataFrame) -> List[int]:
    """
    Get relevant documents for a given query from the ground truth DataFrame.

    Args:
        query (str): Query string
        ground_truth_df (pd.DataFrame): Ground truth DataFrame

    Returns:
        List: List of relevant documents
    """
    # give me only the id and titel column rows
    relevant_docs = ground_truth_df[[query, "id"]]
    
    relevant_docs = relevant_docs[relevant_docs[query] == True][
        "id"
    ].tolist()

    return relevant_docs

def plot_evaluation_results(results: pd.DataFrame):
    """
    Plot evaluation results.

    Args:
        results (pd.DataFrame): Evaluation results DataFrame
    """
    results = results.drop(columns=['boolean_temporal_relevance', 'vector_space_temporal_relevance'])

    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(15, 10))  # Increase figure size

    axes = results.set_index("query").plot(
        kind="bar", subplots=True,ax=axes, layout=(2, 3), legend=False
    )

    # Loop over the axes and remove the x-label
    for ax in axes.flatten():
        ax.set_ylim([0, 1])
        ax.set_ylabel("Score")

        ax.set_xticks(range(len(results)))
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, horizontalalignment='right')  # Adjust alignment

    plt.tight_layout()
    plt.savefig(EVAL_MEASURES_IMAGE_PATH)
    plt.show()

def plot_temporal_relevance(results: pd.DataFrame):
    """
    Plot temporal relevance.

    Args:
        results (pd.DataFrame): DataFrame containing temporal relevance data
    """
    num_results = len(results)
    num_cols = 2
    num_rows = num_results // num_cols + (num_results % num_cols > 0)

    fig, axs = plt.subplots(num_rows, num_cols, figsize=(10, 5*num_rows))

    for i, (index, row) in enumerate(results.iterrows()):
        boolean_temporal_relevance = row['boolean_temporal_relevance']
        vector_space_temporal_relevance = row['vector_space_temporal_relevance']
        query = row['query']

        dates_boolean = list(boolean_temporal_relevance.keys())
        counts_boolean = list(boolean_temporal_relevance.values())

        dates_vector_space = list(vector_space_temporal_relevance.keys())
        counts_vector_space = list(vector_space_temporal_relevance.values())

        ax = axs[i // num_cols, i % num_cols]

        width = 0.4  # the width of the bars

        # Plot bars for boolean_temporal_relevance
        ax.bar([i - width/2 for i in range(len(dates_boolean))], counts_boolean, width, label="Boolean", color='blue', alpha=0.5)

        # Plot bars for vector_space_temporal_relevance
        ax.bar([i + width/2 for i in range(len(dates_vector_space))], counts_vector_space, width, label="Vector Space", color='orange', alpha=0.5)
                
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of Documents")
        ax.set_title(f"query: {query}")
        ax.legend()

        # Set x-tick labels
        ax.set_xticks(range(len(dates_boolean)))
        ax.set_xticklabels(dates_boolean, rotation=45, horizontalalignment='right')

        # Reduce the number of x-axis labels
        ax.xaxis.set_major_locator(MaxNLocator(nbins=6))

    # Remove empty subplots
    if num_results % num_cols > 0:
        for j in range(num_results, num_rows*num_cols):
            fig.delaxes(axs.flatten()[j])

    plt.tight_layout()
    plt.savefig(EVAL_TEMP_RELEVANCE_IMAGE_PATH)
    plt.show()

if __name__ == "__main__":
    """
    Evaluate Boolean and Vector Space Models
    """
    logger.info("Evaluating Boolean and Vector Space Models")
    logger.info("===========================================")

    ground_truth_df = pd.read_csv(GROUND_DATASET_FILE_PATH)

    results = []

    for query in range(0,len(vector_queries)):
        logger.info("Query: %s", boolean_queries[query])
        logger.info("Query: %s", vector_queries[query])

        # Get relevant documents from ground truth
        relevant_docs = get_relevant_docs(vector_queries[query], ground_truth_df)

        # Call Boolean and Vector Space APIs
        boolean_api_response = call_boolean_api(boolean_queries[query])
        vector_space_api_response = call_vector_space_api(vector_queries[query])

        # Get retrieved documents
        boolean_retrieved_docs = sorted(
            [int(doc["id"]) for doc in boolean_api_response]
        )
        vector_space_retrieved_docs = sorted(
            [int(doc["id"]) for doc in vector_space_api_response]
        )

        # Calculate recall, precision, and F1 score
        boolean_recall, boolean_precision, boolean_f1 = evaluate_search_model(
            relevant_docs, boolean_retrieved_docs
        )
        vector_space_recall, vector_space_precision, vector_space_f1 = (
            evaluate_search_model(relevant_docs, vector_space_retrieved_docs)
        )

        # Calculate temporal relevance
        boolean_temporal_relevance = calculate_temporal_relevance(
            retrieved_docs=boolean_api_response,
            start_date=GROUND_DATASET_START_DATE,
            end_date=GROUND_DATASET_END_DATE,
        )
        vector_space_temporal_relevance = calculate_temporal_relevance(
            retrieved_docs=vector_space_api_response,
            start_date=GROUND_DATASET_START_DATE,
            end_date=GROUND_DATASET_END_DATE,
        )

        results.append(
            {
                "query": vector_queries[query],
                "boolean_recall": boolean_recall,
                "boolean_precision": boolean_precision,
                "boolean_f1": boolean_f1,
                "boolean_temporal_relevance": boolean_temporal_relevance,
                "vector_space_recall": vector_space_recall,
                "vector_space_precision": vector_space_precision,
                "vector_space_f1": vector_space_f1,
                "vector_space_temporal_relevance": vector_space_temporal_relevance,
            }
        )

    df = pd.DataFrame(results)
    logger.info("\n%s", df)
    df.describe().to_csv(EVAL_MEASURES_CSV_PATH)

    plot_evaluation_results(df)
    plot_temporal_relevance(df)
