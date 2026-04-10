import logging
import os
import requests

from sqlalchemy.orm import Session

from app.models import Article
from app.services.embedding import search_articles

logger = logging.getLogger(__name__)

def OPENAI_API_KEY():
    return os.getenv("OPENAI_API_KEY", "")

def OPENAI_BASE_URL():
    return os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

def OPENAI_MODEL():
    return os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def build_prompt(query: str, articles: list[dict]) -> str:
    """Build a prompt instructing the LLM to answer using only the provided article context."""
    context = ""
    for i, article in enumerate(articles, 1):
        context += f"[{i}] {article['title']}\n{article['snippet']}\nSource: {article['url']}\n\n"

    return f"""You are a helpful assistant. Answer the user's question using ONLY the context provided below.
If the context does not contain enough information to answer, say so clearly.
Always cite the sources you used by referencing their numbers like [1], [2] etc.

Context:
{context}

Question: {query}

Answer:"""


def call_llm(prompt: str) -> str:
    """Send the prompt to the configured LLM API and return the generated answer."""
    response = requests.post(
        f"{OPENAI_BASE_URL()}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY()}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL(),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def rag_search(query: str, db: Session, top_k: int = 5) -> dict:
    """
    Perform a RAG search: retrieve relevant articles and generate an answer.
    Falls back to top article summary if no LLM is configured.
    """
    # Step 1: retrieve the most relevant articles
    results = search_articles(query, top_k, db=db)

    if not results:
        return {
            "query": query,
            "answer": "No relevant articles found for your query.",
            "sources": [],
            "confidence": 0.0,
        }

    # Step 2: fetch full content from SQLite for the top results
    sources = []
    for r in results:
        article = db.query(Article).filter(Article.id == r["id"]).first()
        if article:
            r["snippet"] = article.content[:1000]
        sources.append({
            "title": r["title"],
            "url": r["url"],
            "score": r["score"],
        })

    confidence = results[0]["score"]

    # Step 3: if no LLM key, return summary of top article
    if not OPENAI_API_KEY():
        logger.info("No LLM key configured, returning fallback summary")
        top = results[0]
        return {
            "query": query,
            "answer": f"Based on the top result: {top['title']}\n\n{top['snippet']}",
            "sources": sources,
            "confidence": confidence,
        }

    # Step 4: build prompt and call LLM
    try:
        prompt = build_prompt(query, results)
        answer = call_llm(prompt)
        logger.info("LLM answer generated successfully")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        top = results[0]
        answer = f"Based on the top result: {top['title']}\n\n{top['snippet']}"

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }
