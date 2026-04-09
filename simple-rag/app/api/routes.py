import csv
import io
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Article, get_db
from app.schemas import ArticleOut, ArticleList, SearchRequest, SearchResponse, SearchResult, RagResponse
from app.services.embedding import search_articles, embed_all_articles
from app.services.ingestion import scrape_and_load
from app.services.rag import rag_search

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
def health_check():
    """Check if the API is running."""
    return {"status": "ok"}

@router.get("/articles", response_model=ArticleList)
def list_articles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
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
def search(
    request: SearchRequest,
    source: str | None = None,
    date_from: str | None = None,
    db: Session = Depends(get_db),
):
    """Search articles semantically with optional source and date filters."""
    raw_results = search_articles(request.query, request.top_k, source=source, date_from=date_from, db=db)
    results = [SearchResult(**r) for r in raw_results]
    return SearchResponse(query=request.query, results=results)

@router.post("/rag-search", response_model=RagResponse)
def rag_search_endpoint(request: SearchRequest, db: Session = Depends(get_db)):
    """Answer a question using RAG — retrieval + AI generation."""
    return rag_search(request.query, db, request.top_k)

@router.post("/ingest")
def trigger_ingest(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger scraping and embedding in the background."""
    def run():
        scrape_and_load(db)
        embed_all_articles(db)

    background_tasks.add_task(run)
    return {"status": "ingestion started"}


@router.get("/export")
def export_articles(format: str = "csv", db: Session = Depends(get_db)):
    """Export all articles as CSV or JSONL download."""
    articles = db.query(Article).all()

    if format == "jsonl":
        def jsonl_generator():
            import json
            for article in articles:
                yield json.dumps({
                    "id": article.id,
                    "source": article.source,
                    "title": article.title,
                    "url": article.url,
                    "content": article.content,
                    "author": article.author,
                    "scraped_at": article.scraped_at.isoformat(),
                }) + "\n"
        return StreamingResponse(
            jsonl_generator(),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=articles.jsonl"}
        )

    # Default: CSV
    def csv_generator():
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "source", "title", "url", "author", "scraped_at"])
        writer.writeheader()
        yield output.getvalue()
        for article in articles:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["id", "source", "title", "url", "author", "scraped_at"])
            writer.writerow({
                "id": article.id,
                "source": article.source,
                "title": article.title,
                "url": article.url,
                "author": article.author,
                "scraped_at": article.scraped_at.isoformat(),
            })
            yield output.getvalue()

    return StreamingResponse(
        csv_generator(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=articles.csv"}
    )
