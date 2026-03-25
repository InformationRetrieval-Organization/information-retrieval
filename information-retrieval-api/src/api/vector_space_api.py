from fastapi import APIRouter
from typing import List
import nltk
from information_retrieval.vector_space_model import search_vector_space_model
from db.posts import get_all_posts
from db.models import Post

router = APIRouter()

@router.get(
    "/search/vector-space",
    responses={
        429: {"description": "Too Many Requests"},
    },
)
async def search_vector_space(q: str) -> List[Post]:
    """
    Search the Vector Space Model for the given query.<br>
    Example usage: http://127.0.0.1:8000/search/vector-space?q=your_search_term
    """
    query = q
    
    lemmatizer = nltk.stem.WordNetLemmatizer()
    lemmatized_query = list()
    
    for word in query.split():
        word = lemmatizer.lemmatize(word.lower())
        lemmatized_query.append(word)
                
    # Add synonyms to the list
    add_synonyms(lemmatized_query)
    
    id_list = await search_vector_space_model(lemmatized_query)
        
    posts = await get_all_posts()
    filtered_posts = [post for post in posts if post.id in id_list]
    filtered_posts = sorted(filtered_posts, key=lambda x: id_list.index(x.id))
        
    return filtered_posts

def add_synonyms(lemmatized_query):
    synonyms = {
        'ppp': 'people power party',
        'dp': 'democratic party',
        'people power party': 'ppp',
        'democratic party': 'dp'
    }
    for word in lemmatized_query:
        if word in synonyms:
            lemmatized_query.append(synonyms[word])