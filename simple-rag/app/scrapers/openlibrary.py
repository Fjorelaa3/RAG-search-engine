import logging
import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "RAGSearchBot/1.0"}


class OpenLibraryScraper:
    """Fetches book metadata from the OpenLibrary search API."""

    def fetch(self, query: str = "machine learning", limit: int = 20) -> list[dict]:
        """Fetch up to `limit` books from OpenLibrary for a given query."""
        url = f"https://openlibrary.org/search.json?q={query.replace(' ', '+')}&limit={limit}"
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            logger.warning(f"Could not fetch OpenLibrary books: HTTP {response.status_code}")
            return []

        docs = response.json().get("docs", [])
        articles = []

        for doc in docs:
            subjects = doc.get("subject", [])
            title = doc.get("title", "")
            authors = ", ".join(doc.get("author_name", [])[:2])
            if subjects:
                content = f"Subjects: {', '.join(subjects[:10])}"
            elif title:
                content = f"Book: {title} by {authors}"
            else:
                continue
            articles.append({
                "source": "openlibrary",
                "title": doc.get("title", ""),
                "url": f"https://openlibrary.org{doc.get('key', '')}",
                "content": content[:2000],
                "author": ", ".join(doc.get("author_name", [])[:2]),
            })

        return articles
