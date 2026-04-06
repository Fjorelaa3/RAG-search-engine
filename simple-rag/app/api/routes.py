import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Article, get_db
from app.schemas import ArticleOut, ArticleList, SearchRequest, SearchResponse, SearchResult, RagResponse
from app.services.embedding import search_articles
from app.services.rag import rag_search

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
def health_check():
    """Check if the API is running."""
    return {"status": "ok"}

@router.get("/articles", response_model=ArticleList)
def list_articles(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Return a paginated list of articles."""
    total = db.query(Article).count()
    articles = (
        db.query(Article)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ArticleList(articles=articles, total=total, page=page, page_size=page_size)


@router.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(article_id: str, db: Session = Depends(get_db)):
    """Return a single article by ID."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Return article counts grouped by source."""
    results = (
        db.query(Article.source, func.count(Article.id))
        .group_by(Article.source)
        .all()
    )
    return {
        "total": db.query(Article).count(),
        "by_source": {source: count for source, count in results}
    }


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """Search articles semantically."""
    raw_results = search_articles(request.query, request.top_k)
    results = [SearchResult(**r) for r in raw_results]
    return SearchResponse(query=request.query, results=results)

@router.post("/rag-search", response_model=RagResponse)
def rag_search_endpoint(request: SearchRequest, db: Session = Depends(get_db)):
    """Answer a question using RAG — retrieval + AI generation."""
    return rag_search(request.query, db, request.top_k)
