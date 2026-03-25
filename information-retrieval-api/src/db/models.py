from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Post(SQLModel, table=True):
    __tablename__ = "Post"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: Optional[str] = None
    published_on: datetime = Field(default_factory=datetime.utcnow)
    link: Optional[str] = None
    source: Optional[str] = None


class ProcessedPost(SQLModel, table=True):
    __tablename__ = "Processed_Post"

    id: int = Field(primary_key=True)
    content: Optional[str] = None
