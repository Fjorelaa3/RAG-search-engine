from datetime import datetime
from pydantic import BaseModel, Field


class ArticleOut(BaseModel):
    """Schema for returning a single article."""
    id: str
    source: str
    title: str
    url: str
    content: str
    author: str | None
    scraped_at: datetime

    model_config = {"from_attributes": True}


class ArticleList(BaseModel):
    """Schema for returning a paginated list of articles."""
    articles: list[ArticleOut]
    total: int
    page: int
    page_size: int


class SearchRequest(BaseModel):
    """Schema for incoming search requests."""
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    """Schema for a single search result."""
    id: str
    title: str
    url: str
    source: str
    author: str | None
    snippet: str
    score: float


class SearchResponse(BaseModel):
    """Schema for returning search results."""
    query: str
    results: list[SearchResult]
