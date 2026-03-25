import logging
import re
from typing import Dict, List, Set, Tuple
import nltk
from nltk.corpus import stopwords
from db.processed_posts import create_many_processed_posts, get_all_processed_posts
from db.posts import get_all_posts
import information_retrieval.globals
from datetime import datetime
from config import MAX_DATA_COEFFICIENT
from db.models import Post, ProcessedPost

logger = logging.getLogger(__name__)


async def preprocess_documents():
    """
    Preprocesses the documents in the database and returns a list of tokens.
    """
    logger.info("Start Preprocessing")

    download_nltk_resources()

    # Get the posts and processed posts from the database
    posts = await get_all_posts()
    processed_posts = await get_all_processed_posts()

    if not processed_posts:
        # Preprocess the posts
        logger.info("no prepocessed posts in database, start preprocessing")
        processed_posts, list_of_tokens = await preprocess_and_insert_posts(posts)
    else:
        # already preprocessed
        logger.info("found preprocessed posts in database")
        list_of_tokens = await calculate_date_coefficients_and_vocabulary(
            processed_posts, posts
        )

    information_retrieval.globals._vocabulary = list_of_tokens

    logger.info("%s posts came trough the preprocessing", len(processed_posts))
    logger.info("Length of Vocabulary: %s", len(list_of_tokens))
    logger.info("Preprocessing completed")
    
def download_nltk_resources():
    """
    Download the necessary NLTK resources.
    """
    nltk.download("wordnet")
    nltk.download("stopwords")
    nltk.download("words")

def handle_tokens(term_freq_map: Dict[str, int], tokens: List[str]) -> List[str]:
    """
    Handle tokens: update term frequency map and filter out unique tokens.
    """
    # Find tokens that occur only once
    unique_tokens = [key for key, value in term_freq_map.items() if value == 1]
    tokens = [token for token in tokens if token not in unique_tokens]

    # Remove duplicates
    tokens = list(set(tokens))

    return tokens

async def preprocess_and_insert_posts(posts: List[Post]) -> Tuple[List[ProcessedPost], List[str]]:
    """
    Preprocesses the posts and inserts them into the database.
    """
    # Initialize the variables
    list_of_tokens = []
    processed_posts = []
    term_freq_map = {}

    english_words = set(nltk.corpus.words.words())
    english_words.add("korea")

    for post in posts:
        # Preprocess the post
        processed_post, tokens = preprocess_post(post, english_words)

        if not processed_post:
            continue

        # Add to processed_posts list
        processed_posts.append(processed_post)

        # Calculate the date coefficient
        information_retrieval.globals._date_coefficient[post.id] = (
            calculate_date_coefficient(post.published_on, MAX_DATA_COEFFICIENT)
        )

        set_term_freq_map(term_freq_map, tokens)

        list_of_tokens.extend(tokens)
    
    list_of_tokens = handle_tokens(term_freq_map, list_of_tokens)

    # database
    processed_posts_data = [post.model_dump() for post in processed_posts] # convert from List[ProcessedPost] to List[Dict]
    await create_many_processed_posts(processed_posts_data) # Insert the processed posts into the database

    return processed_posts, list_of_tokens


async def calculate_date_coefficients_and_vocabulary(
    processed_posts: List[ProcessedPost], posts: List[Post]
) -> List[str]:
    """
    Calculates the date coefficients and vocabulary for the processed posts.
    """
    list_of_tokens = []
    term_freq_map = {}

    # Create a dictionary mapping post IDs to posts for quick lookup
    posts_dict = {post.id: post for post in posts}

    for processed_post in processed_posts:
        # Find the corresponding post
        post = posts_dict.get(processed_post.id)

        if post:
            # Calculate the date coefficient
            information_retrieval.globals._date_coefficient[processed_post.id] = (
                calculate_date_coefficient(post.published_on, MAX_DATA_COEFFICIENT)
            )

            # Tokenize the processed post content
            tokens = processed_post.content.split()

            set_term_freq_map(term_freq_map, tokens)

            # Add the tokens to the list of tokens
            list_of_tokens.extend(tokens)
        
    list_of_tokens = handle_tokens(term_freq_map, list_of_tokens)

    return list_of_tokens


def preprocess_post(
    post: Post, english_words: Set[str]
) -> Tuple[ProcessedPost, List[str]]:
    """
    Preprocess a post.
    """
    # Remove special characters and convert to lowercase
    content = post.title.lower() + " " + post.content.lower()  # Add the title
    content = re.sub("[–!\"#$%&'()*+,-./:;<=‘>—?@[\]^_`�{|}~\n’“”]", "", content)

    # Remove posts with a low english word ratio
    threshold = 0.7
    if not is_english(content, threshold, english_words):
        return None, []

    # Remove non-english words
    content = " ".join(
        w
        for w in nltk.wordpunct_tokenize(content)
        if w.lower() in english_words or not w.isalpha()
    )

    # Tokenize the document
    tokens = nltk.wordpunct_tokenize(content)

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    tokens = [token for token in tokens if token not in stop_words]

    # Lemmatize the tokens
    lemmatizer = nltk.stem.WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    # Create the processed post
    processed_post = ProcessedPost(id=post.id, content=" ".join(tokens))

    return processed_post, tokens


def set_term_freq_map(term_freq_map: Dict[str, int], tokens: List[str]) -> None:
    """
    Set the term frequency map for a document.
    """
    for token in tokens:
        if token in term_freq_map:
            term_freq_map[token] += 1
        else:
            term_freq_map[token] = 1


def is_english(content: str, threshold: float, english_words: Set[str]) -> bool:
    """
    Determine if a document is in English based on the ratio of English words.
    """
    english_words_count = sum(1 for word in content.split() if word in english_words)
    total_words_count = len(content.split())

    if total_words_count == 0 or english_words_count == 0:  # Avoid division by zero
        return False

    return english_words_count / total_words_count >= threshold


def calculate_date_coefficient(post_date: datetime, max_coefficient: int) -> int:
    """
    Calculate the date coefficient for a document.
    """
    oldest_date = datetime(2024, 3, 12)
    newest_date = datetime(2024, 4, 12)
    days_between = (newest_date - oldest_date).days
    coefficient_per_day = (max_coefficient - 1) / days_between

    post_date = post_date.replace(
        tzinfo=None
    )  # Remove timezone info, otherwise the subtraction will fail

    days_since_oldest = (post_date - oldest_date).days
    return coefficient_per_day * days_since_oldest + 1
