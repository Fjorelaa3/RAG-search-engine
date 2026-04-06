import csv
import logging
import os

from sqlalchemy.orm import Session

from app.models import Article
from app.scrapers.wikipedia import WikipediaScraper
from app.scrapers.devto import DevtoScraper
from app.scrapers.reddit import RedditScraper
from app.scrapers.hackernews import HackerNewsScraper
from app.scrapers.arxiv import ArxivScraper
from app.scrapers.openlibrary import OpenLibraryScraper

logger = logging.getLogger(__name__)


def save_to_csv(articles: list[dict], path: str) -> None:
    """Save scraped articles to a CSV file for inspection. Skips if file already exists."""
    if not articles or os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=articles[0].keys())
        writer.writeheader()
        writer.writerows(articles)
    logger.info(f"Saved {len(articles)} records to {path}")


def save_articles(db: Session, articles: list[dict]) -> int:
    """Save a list of article dicts to the database, skipping duplicates."""
    saved = 0
    seen_urls = set()
    for article in articles:
        url = article["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        existing = db.query(Article).filter(Article.url == url).first()
        if existing:
            continue
        db.add(Article(**article))
        saved += 1
    db.commit()
    return saved


def scrape_and_load(db: Session) -> None:
    """Run all scrapers and load results into the database."""
    scrapers = [
        ("Wikipedia", WikipediaScraper(), {"limit": 10}),
        ("Dev.to", DevtoScraper(), {"limit": 30}),
        ("Reddit", RedditScraper(), {"limit": 25}),
        ("HackerNews", HackerNewsScraper(), {"limit": 30}),
        ("arXiv", ArxivScraper(), {"category": "cs.AI", "max_results": 50}),
        ("OpenLibrary", OpenLibraryScraper(), {"query": "machine learning", "limit": 20}),
    ]

    for name, scraper, kwargs in scrapers:
        logger.info(f"Scraping {name}...")
        try:
            articles = scraper.fetch(**kwargs)
            # Save to CSV for inspection (only on first run, skips if file exists)
            csv_path = f"data/{name.lower().replace('.', '').replace(' ', '_')}.csv"
            save_to_csv(articles, csv_path)
            count = save_articles(db, articles)
            logger.info(f"{name}: saved {count} new articles")
        except Exception as e:
            logger.error(f"{name} failed: {e}")
            db.rollback()


if __name__ == "__main__":
    from app.models import SessionLocal, init_db
    init_db()
    db = SessionLocal()
    try:
        scrape_and_load(db)
        total = db.query(Article).count()
        logger.info(f"Total articles in database: {total}")
    finally:
        db.close()
