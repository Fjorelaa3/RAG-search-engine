import html
import time
import requests


HEADERS = {"User-Agent": "RAGSearchBot/1.0"}
HN_BASE = "https://hacker-news.firebaseio.com/v0"


class HackerNewsScraper:
    """Fetches top stories from the Hacker News Firebase API."""

    def fetch(self, limit: int = 30) -> list[dict]:
        """Fetch up to `limit` stories from Hacker News."""
        ids_response = requests.get(f"{HN_BASE}/topstories.json", headers=HEADERS, timeout=10)
        if ids_response.status_code != 200:
            print(f"Could not fetch HN story IDs: HTTP {ids_response.status_code}")
            return []

        story_ids = ids_response.json()[:limit]
        articles = []

        for story_id in story_ids:
            item_response = requests.get(f"{HN_BASE}/item/{story_id}.json", headers=HEADERS, timeout=10)
            if item_response.status_code != 200:
                continue
            item = item_response.json()
            if not item or not item.get("text"):
                continue
            articles.append({
                "source": "hackernews",
                "title": item.get("title", ""),
                "url": item.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                "content": html.unescape(item.get("text", ""))[:2000],
                "author": item.get("by", ""),
            })
            time.sleep(0.2)

        return articles
