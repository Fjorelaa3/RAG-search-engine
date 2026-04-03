import xml.etree.ElementTree as ET
import requests


HEADERS = {"User-Agent": "RAGSearchBot/1.0"}
ARXIV_NS = "http://www.w3.org/2005/Atom"


class ArxivScraper:
    """Fetches research paper summaries from the arXiv API."""

    def fetch(self, category: str = "cs.AI", max_results: int = 50) -> list[dict]:
        """Fetch up to `max_results` papers from arXiv for a given category."""
        url = f"https://export.arxiv.org/api/query?search_query=cat:{category}&max_results={max_results}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"Could not fetch arXiv papers: HTTP {response.status_code}")
            return []

        root = ET.fromstring(response.content)
        articles = []

        for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
            title = entry.findtext(f"{{{ARXIV_NS}}}title", "").strip()
            summary = entry.findtext(f"{{{ARXIV_NS}}}summary", "").strip()
            link_elem = entry.find(f"{{{ARXIV_NS}}}id")
            url = link_elem.text.strip() if link_elem is not None else ""
            authors = [
                a.findtext(f"{{{ARXIV_NS}}}name", "")
                for a in entry.findall(f"{{{ARXIV_NS}}}author")
            ]
            articles.append({
                "source": "arxiv",
                "title": title,
                "url": url,
                "content": summary[:2000],
                "author": ", ".join(authors[:3]),
            })

        return articles
