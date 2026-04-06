"""
Setup script - run this once after cloning to populate the database and embeddings.
Usage: python setup.py
"""
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run full setup: initialize DB, scrape articles, and generate embeddings."""
    from app.models import SessionLocal, init_db
    from app.services.ingestion import scrape_and_load
    from app.services.embedding import embed_all_articles

    logger.info("Step 1/3: Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        logger.info("Step 2/3: Scraping articles from all sources...")
        scrape_and_load(db)

        logger.info("Step 3/3: Generating embeddings...")
        embed_all_articles(db)

        total = db.query(__import__('app.models', fromlist=['Article']).Article).count()
        logger.info(f"Setup complete. {total} articles ready.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
