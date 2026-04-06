import logging
import time
import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "RAGSearchBot/1.0"}

TOPICS = [
    "Artificial_intelligence",
    "Machine_learning",
    "Deep_learning",
    "Neural_network",
    "Natural_language_processing",
    "Computer_vision",
    "Data_science",
    "Reinforcement_learning",
    "Transformer_(machine_learning_model)",
    "Large_language_model",
]


class WikipediaScraper:
    """Fetches article summaries from the Wikipedia REST API."""

    def fetch(self, limit: int = 10) -> list[dict]:
        """Fetch up to `limit` articles from Wikipedia."""
        articles = []
        for slug in TOPICS[:limit]:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Skipping {slug}: HTTP {response.status_code}")
                continue
            data = response.json()
            articles.append({
                "source": "wikipedia",
                "title": data.get("title", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "content": data.get("extract", "")[:2000],
                "author": "Wikipedia",
            })
            time.sleep(0.5) 
        return articles
