import logging
import time
import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "RAGSearchBot/1.0"}

TAGS = ["python", "machinelearning", "webdev"]


class DevtoScraper:
    """Fetches articles from the Dev.to public API."""

    def fetch(self, limit: int = 30) -> list[dict]:
        """Fetch up to `limit` articles per tag from Dev.to."""
        articles = []
        for tag in TAGS:
            url = f"https://dev.to/api/articles?tag={tag}&per_page={limit}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Skipping tag '{tag}': HTTP {response.status_code}")
                continue
            for item in response.json():
                articles.append({
                    "source": "devto",
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("description", "")[:2000],
                    "author": item.get("user", {}).get("name", ""),
                })
            time.sleep(0.3)
        return articles
