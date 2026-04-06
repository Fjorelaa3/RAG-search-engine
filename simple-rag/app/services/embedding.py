import logging
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.models import Article

logger = logging.getLogger(__name__)

# Load the model once at module level, not inside a function
# loads when the app starts, not on every request
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# saves data to disk so it survives restarts
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="articles")

def embed_all_articles(db: Session) -> None:
    """Embed all articles from SQLite and store them in ChromaDB."""
    articles = db.query(Article).all()
    logger.info(f"Found {len(articles)} articles to embed")

    skipped = 0
    processed = 0

    for article in articles:
        # Check if already embedded — skip if so
        existing = collection.get(ids=[article.id])
        if existing["ids"]:
            skipped += 1
            continue

        # Combine title and content for richer embedding
        text = f"{article.title}. {article.content}"

        # Convert text to a list of numbers
        embedding = MODEL.encode(text).tolist()

        # Store in ChromaDB with metadata for retrieval later
        collection.add(
            ids=[article.id],
            embeddings=[embedding],
            metadatas=[{
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "author": article.author or "",
            }],
            documents=[article.content[:500]],
        )
        processed += 1

    logger.info(f"Embedded {processed} new articles, skipped {skipped} already indexed")

def search_articles(
    query: str,
    top_k: int = 5,
    source: str | None = None,
    date_from: str | None = None,
    db=None,
) -> list[dict[str, Any]]:
    """Search for articles semantically similar to the query, with optional filters."""
    # Convert the search query to an embedding
    query_embedding = MODEL.encode(query).tolist()

    # Fetch more results than needed so we have enough after filtering
    fetch_k = top_k * 4 if (source or date_from) else top_k

    # Find the most similar articles in ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(fetch_k, collection.count()),
    )

    # Package results into a clean list of dicts, applying filters
    articles = []
    for i in range(len(results["ids"][0])):
        article = {
            "id": results["ids"][0][i],
            "title": results["metadatas"][0][i]["title"],
            "url": results["metadatas"][0][i]["url"],
            "source": results["metadatas"][0][i]["source"],
            "author": results["metadatas"][0][i]["author"],
            "snippet": results["documents"][0][i],
            "score": 1 - results["distances"][0][i],
        }

        # Apply source filter
        if source and article["source"] != source:
            continue

        # Apply date filter using scraped_at from SQLite
        if date_from and db:
            from app.models import Article as ArticleModel
            from datetime import datetime
            db_article = db.query(ArticleModel).filter(ArticleModel.id == article["id"]).first()
            if db_article:
                cutoff = datetime.fromisoformat(date_from)
                if db_article.scraped_at < cutoff:
                    continue

        articles.append(article)
        if len(articles) == top_k:
            break

    return articles
