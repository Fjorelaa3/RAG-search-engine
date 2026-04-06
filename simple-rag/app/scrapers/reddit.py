import logging
import time
import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "RAGSearchBot/1.0"}

SUBREDDITS = ["MachineLearning", "learnprogramming", "Python"]


class RedditScraper:
    """Fetches top posts from Reddit subreddits using the native JSON feed."""

    def fetch(self, limit: int = 25) -> list[dict]:
        """Fetch up to `limit` posts per subreddit from Reddit."""
        articles = []
        for sub in SUBREDDITS:
            url = f"https://www.reddit.com/r/{sub}/top.json?limit={limit}&t=month"
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Skipping r/{sub}: HTTP {response.status_code}")
                continue
            posts = response.json().get("data", {}).get("children", [])
            for post in posts:
                data = post.get("data", {})
                body = data.get("selftext", "").strip()
                if not body or body == "[removed]":
                    continue
                articles.append({
                    "source": "reddit",
                    "title": data.get("title", ""),
                    "url": f"https://reddit.com{data.get('permalink', '')}",
                    "content": body[:2000],
                    "author": data.get("author", ""),
                })
            time.sleep(1.0)
        return articles
