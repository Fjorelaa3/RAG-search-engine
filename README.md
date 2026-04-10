# RAG Search Engine

A Retrieval-Augmented Generation (RAG) search engine that scrapes publicly available content from Wikipedia, Dev.to, Reddit, Hacker News, arXiv, and OpenLibrary. It indexes the content using semantic embeddings and exposes a REST API that lets users search and ask AI-powered questions about the data.

---

## Live Demo

The app is deployed and accessible at:

**https://rag-search-engine.fly.dev**

- Interactive API docs (Swagger): https://rag-search-engine.fly.dev/docs
- Health check: https://rag-search-engine.fly.dev/health

> The app is hosted on Fly.io's free tier and may take 10–15 seconds to wake up on the first request after a period of inactivity.

---

## Prerequisites

- Python 3.11+
- `pip` and `venv` (included with Python)
- Docker and Docker Compose (optional, for containerised setup)

---

## Setup & Run (Plain Python)

### 1. Clone the repository

```bash
git clone https://github.com/Fjorelaa3/RAG-search-engine.git
cd RAG-search-engine/simple-rag
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
source .venv/Scripts/activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive API docs are available at `http://localhost:8000/docs`.

### 5. Trigger ingestion (scrape + embed — run once)

Once the server is running, call the `/ingest` endpoint to populate the database:

```bash
curl -X POST http://localhost:8000/ingest
```

Or click `POST /ingest → Execute` in the Swagger UI at `http://localhost:8000/docs`.

This will run in the background and:
- Scrape 250+ articles from all 6 sources and save them to SQLite
- Save a CSV inspection file for each source under `data/`
- Generate semantic embeddings and store them in ChromaDB
- Call the LLM once per article to auto-generate topic tags (e.g. `"machine learning, NLP, AI"`) — only if an LLM key is configured in `.env`

> This step takes several minutes on first run as it downloads the embedding model (~80MB) and processes all articles. If an LLM key is set, expect additional time for tag generation per article.

### 6. Run tests

```bash
pytest tests/test_api.py -v
```

---

## Setup & Run (Docker)

### 1. Clone the repository

```bash
git clone https://github.com/Fjorelaa3/RAG-search-engine.git
cd RAG-search-engine/simple-rag
```

### 2. Build and start the container

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

### 3. Trigger ingestion

```bash
curl -X POST http://localhost:8000/ingest
```

This scrapes all sources, generates embeddings, and auto-tags articles via LLM (if key is set).

> The SQLite database and ChromaDB data are mounted as volumes so they persist between container restarts.

---

## API Endpoint Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check — returns `{"status": "ok"}` |
| `GET` | `/articles` | Paginated list of articles. Query params: `page`, `page_size`, `tag` |
| `GET` | `/articles/{id}` | Single article by ID. Returns 404 if not found |
| `GET` | `/stats` | Article counts grouped by source |
| `POST` | `/search` | Semantic search. Body: `{"query": "...", "top_k": 5}`. Optional query params: `source`, `date_from` |
| `POST` | `/rag-search` | AI-powered answer with source citations. Body: `{"query": "...", "top_k": 5}` |
| `POST` | `/rag-search/stream` | Same as `/rag-search` but streams the answer token by token via SSE |
| `POST` | `/ingest` | Trigger scraping and embedding in the background |
| `GET` | `/export` | Download all articles. Query param: `format=csv` (default) or `format=jsonl` |

### Example: Semantic Search with Filter

```bash
curl -X POST "http://localhost:8000/search?source=wikipedia" \
  -H "Content-Type: application/json" \
  -d '{"query": "deep learning", "top_k": 5}'
```

### Example: RAG Search

```bash
curl -X POST http://localhost:8000/rag-search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is reinforcement learning?", "top_k": 5}'
```

### Example: Streaming RAG Search

```bash
curl -N -X POST http://localhost:8000/rag-search/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is reinforcement learning?", "top_k": 5}'
```

### Example: Filter articles by tag

```bash
curl "http://localhost:8000/articles?tag=machine+learning&page=1&page_size=5"
```

---

## Optional LLM Integration

By default the `/rag-search` endpoint returns a summary of the top matching article (no API key required).

To enable AI-generated answers, copy the example env file and choose one of the options below:

```bash
# Mac/Linux
cp .env.example .env

# Windows
copy .env.example .env
```

### Option A: OpenAI

```
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

### Option B: Ollama (local, free)

Ollama lets you run a local LLM on your own machine — no API key or cost required.

1. Install Ollama from [https://ollama.com](https://ollama.com)
2. Pull a model:

```bash
ollama pull llama3
```

3. Set these values in `.env`:

```
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3
```

The existing `call_llm()` implementation is fully compatible with Ollama's OpenAI-compatible API — no code changes needed.

Any other OpenAI-compatible API also works (Groq, Together AI, etc.).

---

## Project Structure

```
simple-rag/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # SQLAlchemy Article model and DB setup
│   ├── schemas.py           # Pydantic schemas for API I/O
│   ├── api/
│   │   └── routes.py        # All API endpoint handlers
│   ├── scrapers/
│   │   ├── wikipedia.py     # Wikipedia REST API scraper
│   │   ├── devto.py         # Dev.to public API scraper
│   │   ├── reddit.py        # Reddit JSON feed scraper
│   │   ├── hackernews.py    # Hacker News Firebase API scraper
│   │   ├── arxiv.py         # arXiv Atom feed scraper
│   │   └── openlibrary.py   # OpenLibrary search API scraper
│   └── services/
│       ├── ingestion.py     # Scrape orchestration and DB loading
│       ├── embedding.py     # Sentence embedding and semantic search
│       └── rag.py           # RAG pipeline and LLM integration
├── data/                    # CSV inspection outputs (auto-generated, not committed)
├── tests/
│   └── test_api.py          # Pytest test suite (10 tests)
├── setup.py                 # One-time setup script (scrape + embed)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Container orchestration
├── .env.example             # Environment variable template
├── fly.toml                 # Fly.io deployment configuration
└── pytest.ini               # Pytest configuration
```

---

## Data Sources

| Source | Type | Content |
|--------|------|---------|
| Wikipedia | REST API | AI/ML topic summaries |
| Dev.to | REST API | Programming articles |
| Reddit | JSON feed | Community discussions |
| Hacker News | Firebase API | Tech stories |
| arXiv | Atom/XML feed | Research paper abstracts |
| OpenLibrary | REST API | Book metadata |
