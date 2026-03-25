from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
import nltk
from information_retrieval.boolean_model import search_boolean_model
from db.posts import get_all_posts
from db.models import Post

router = APIRouter()

class Item(BaseModel):
    operator: str
    value: str

@router.post(
    "/search/boolean",
    responses={
        429: {"description": "Too Many Requests"},
    },
)
async def search_boolean(items: List[Item]) -> List[Post]:
    """
    Search the Boolean Model for the given query.<br>
    Example usage: http://127.0.0.1:8000/search/boolean
    """
    operator_value_list = []
    lemmatizer = nltk.stem.WordNetLemmatizer()

    for item in items:
        word = lemmatizer.lemmatize(item.value.lower())
        operator_value_list.append((item.operator, word.lower()))

    id_list = search_boolean_model(operator_value_list)

    posts = await get_all_posts()
    filtered_posts = [post for post in posts if post.id in id_list]

    # Sort posts based on time
    filtered_posts.sort(key=lambda x: x.published_on, reverse=True)

    return filtered_posts