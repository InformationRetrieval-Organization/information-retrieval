from datetime import datetime, timezone
import logging
from typing import Dict, List, Union
from aiocache import cached, SimpleMemoryCache
from aiocache.serializers import PickleSerializer
from sqlalchemy import text
from sqlmodel import select

from db.models import Post
from db.session import SessionLocal


cache = SimpleMemoryCache()
logger = logging.getLogger(__name__)


def _normalize_published_on(value: datetime) -> datetime:
    """
    Convert timezone-aware datetimes to naive UTC for TIMESTAMP WITHOUT TIME ZONE columns.
    """
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    return value

@cached(ttl=None, cache=SimpleMemoryCache, serializer=PickleSerializer(), key="get_all_posts")
async def get_all_posts() -> List[Post]:
    """
    Fetch all posts from the database
    """
    try:
        async with SessionLocal() as session:
            result = await session.exec(select(Post))
            return result.all()
    except Exception as e:
        logger.exception("An error occurred while fetching posts")
        return []


async def create_many_posts(
    posts: List[Dict[str, Union[str, datetime]]]
) -> List[Post]:
    """
    Create multiple posts in the database
    """
    try:
        async with SessionLocal() as session:
            normalized_posts = []
            for post in posts:
                normalized_post = dict(post)
                published_on = normalized_post.get("published_on")
                if isinstance(published_on, datetime):
                    normalized_post["published_on"] = _normalize_published_on(published_on)
                normalized_posts.append(normalized_post)

            post_objects = [Post(**post) for post in normalized_posts]
            session.add_all(post_objects)
            await session.commit()

            # invalidate the cache
            await cache.delete('get_all_posts')

            return post_objects
    except Exception as e:
        logger.exception("An error occurred while creating the posts")
        return []


async def create_one_post(
    title: str,
    content: str,
    published_on: datetime,
    link: str,
    source: str,
) -> Post | None:
    """
    Create a post in the database
    """
    try:
        async with SessionLocal() as session:
            post = Post(
                title=title,
                content=content,
                published_on=_normalize_published_on(published_on),
                link=link,
                source=source,
            )
            session.add(post)
            await session.commit()
            await session.refresh(post)

            # invalidate the cache
            await cache.delete('get_all_posts')

            return post
    except Exception as e:
        logger.exception("An error occurred while creating the post")
        return None


async def delete_all_posts() -> None:
    """
    Delete all posts from the database and reset the auto-increment counter
    """
    logger.info("Deleting all posts")

    try:
        async with SessionLocal() as session:
            await session.execute(text('TRUNCATE TABLE "Post" RESTART IDENTITY CASCADE'))
            await session.commit()

            # invalidate the cache
            await cache.delete('get_all_posts')
    except Exception as e:
        logger.exception("An error occurred while deleting posts")
