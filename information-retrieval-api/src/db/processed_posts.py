from datetime import datetime
import logging
from typing import Dict, List, Union
from aiocache import cached, SimpleMemoryCache
from aiocache.serializers import PickleSerializer
from sqlalchemy import text
from sqlmodel import select

from db.models import ProcessedPost
from db.session import SessionLocal


cache = SimpleMemoryCache()
logger = logging.getLogger(__name__)

@cached(ttl=None, cache=SimpleMemoryCache, serializer=PickleSerializer(), key="get_all_processed_posts")
async def get_all_processed_posts() -> List[ProcessedPost]:
    """
    Fetch all processed_posts from the database
    """
    try:
        async with SessionLocal() as session:
            result = await session.exec(select(ProcessedPost))
            return result.all()
    except Exception as e:
        logger.exception("An error occurred while fetching processed_posts")
        return []


async def create_one_processed_post(id: int, content: str) -> ProcessedPost | None:
    """
    Create a processed_post in the database
    """
    try:
        async with SessionLocal() as session:
            processed_post = ProcessedPost(id=id, content=content)
            session.add(processed_post)
            await session.commit()
            await session.refresh(processed_post)
        
            # invalidate the cache
            await cache.delete('get_all_processed_posts')

            return processed_post
    except Exception as e:
        logger.exception("An error occurred while creating the processed_post")
        return None


async def create_many_processed_posts(
    processed_posts: List[Dict[str, Union[int, str]]]
) -> List[ProcessedPost]:
    """
    Create multiple processed_posts in the database
    """
    try:
        async with SessionLocal() as session:
            processed_post_objects = [ProcessedPost(**post) for post in processed_posts]
            session.add_all(processed_post_objects)
            await session.commit()
            
            # invalidate the cache
            await cache.delete('get_all_processed_posts')

            return processed_post_objects
    except Exception as e:
        logger.exception("An error occurred while creating the processed_posts")
        return []


async def delete_all_processed_posts() -> None:
    """
    Delete all processed_posts from the database and reset the auto-increment counter
    """
    logger.info("Deleting all processed_posts")

    try:
        async with SessionLocal() as session:
            await session.execute(text('TRUNCATE TABLE "Processed_Post" RESTART IDENTITY CASCADE'))
            await session.commit()

            # invalidate the cache
            await cache.delete('get_all_processed_posts')
    except Exception as e:
        logger.exception("An error occurred while deleting processed_posts")
