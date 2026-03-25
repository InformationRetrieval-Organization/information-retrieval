import logging
import asyncio
from collections import Counter
from db.processed_posts import get_all_processed_posts 
from information_retrieval.linked_list import LinkedList
import information_retrieval.globals 
import pandas as pd
import os
from config import INVERTED_INDEX_FILE_PATH
from config import FASTAPI_ENV

logger = logging.getLogger(__name__)

async def build_boolean_model():
    """
    Build the Boolean Model
    """
    logger.info("Building Boolean Model")
    delete_old_csv() # Delete the old csv file if it exists
    
    # Get all posts content
    posts = await get_all_processed_posts()
    posts = [(post.id, post.content) for post in posts]

    # Build per-document token stats in parallel, then merge into globals.
    # This avoids repeated insert checks for duplicate words inside a document.
    tokenized_posts = await asyncio.gather(
        *(asyncio.to_thread(_tokenize_post, post_id, content) for post_id, content in posts)
    )

    for post_id, term_counts, unique_terms in tokenized_posts:
        information_retrieval.globals._all_doc_ids.add(post_id)

        for word, count in term_counts.items():
            information_retrieval.globals._term_frequency[word] = (
                information_retrieval.globals._term_frequency.get(word, 0) + count
            )

        for word in unique_terms:
            posting_list = information_retrieval.globals._inverted_index.get(word)
            if posting_list is None:
                information_retrieval.globals._inverted_index[word] = LinkedList(post_id)
            else:
                posting_list.insertSorted(post_id)
    
    # Create a DataFrame to store the search results
    create_csv()
    logger.info("Boolean Model Built")
    
def search_boolean_model(query):
    logger.info("Searching Boolean Model")
    id_set = set(information_retrieval.globals._all_doc_ids)

    # First sort tokens by frequency
    try:
        sorted_query = sorted(query, key=lambda word: information_retrieval.globals._term_frequency[word[1]])
    except KeyError:
        sorted_query = query  
    
    for entry in sorted_query:
        # Call different functions based on the operator
        if entry[0] == "AND":
            id_set = _and_processing(entry[1], id_set)
        elif entry[0] == "OR": 
            id_set = _or_processing(entry[1], id_set)
        elif entry[0] == "NOT":
            id_set = _not_processing(entry[1], id_set)
            
    logger.info("Boolean Model Searched")
    return list(id_set)

def _and_processing(word, id_set):
    try:
        ids_of_index = set(information_retrieval.globals._inverted_index[word])
        id_set = id_set.intersection(ids_of_index)
    except KeyError:
        id_set = set() # If the word is not in the index, then the result is empty
    return id_set

def _or_processing(word, id_set):
    try:
        ids_of_index = set(information_retrieval.globals._inverted_index[word])
        id_set = id_set.union(ids_of_index)
    except KeyError:
        pass   # If the word is not in the index, it is not necessary to add it
    return id_set

def _not_processing(word, id_set):
    try:
        ids_of_index = set(information_retrieval.globals._inverted_index[word])
        id_set = id_set.difference(ids_of_index)
    except KeyError:
        pass    # If the word is not in the index, it is not necessary to remove it
    return id_set

def create_csv():
    if FASTAPI_ENV != "development": # only create the csv file in development mode
        return
    
    data = []
    for key, values in information_retrieval.globals._inverted_index.items():
        for value in values:
            data.append({"Key": key, "Value": value})
    
    df = pd.DataFrame(data, columns=['Key', 'Value'])
    df.to_csv(INVERTED_INDEX_FILE_PATH, index=False)

def delete_old_csv():
    if os.path.exists(INVERTED_INDEX_FILE_PATH):
        os.remove(INVERTED_INDEX_FILE_PATH)


def _tokenize_post(post_id: int, content: str):
    words = content.split()
    term_counts = Counter(words)
    unique_terms = set(term_counts.keys())
    return post_id, term_counts, unique_terms
