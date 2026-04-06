# RAG Search Engine

A Retrieval-Augmented Generation (RAG) search engine that scrapes publicly available content from Wikipedia, Dev.to, Reddit, Hacker News, arXiv, and OpenLibrary. It indexes the content using semantic embeddings and exposes a REST API that lets users search and ask AI-powered questions about the data.

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

### 4. Run the setup script (scrape + embed — run once)

```bash
python setup.py
```

This will:
- Scrape 250+ articles from all 6 sources and save them to SQLite
- Save a CSV inspection file for each source under `data/`
- Generate semantic embeddings and store them in ChromaDB

> This step takes a few minutes on first run as it downloads the embedding model (~80MB).

### 5. Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive API docs are available at `http://localhost:8000/docs`.

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

### 2. Run the setup script first (required before Docker)

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows / source .venv/bin/activate on Mac/Linux
pip install -r requirements.txt
python setup.py
```

### 3. Build and start the container

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

> The SQLite database and ChromaDB data are mounted as volumes so they persist between container restarts.

---

## API Endpoint Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check — returns `{"status": "ok"}` |
| `GET` | `/articles` | Paginated list of articles. Query params: `page`, `page_size` |
| `GET` | `/articles/{id}` | Single article by ID. Returns 404 if not found |
| `GET` | `/stats` | Article counts grouped by source |
| `POST` | `/search` | Semantic search. Body: `{"query": "...", "top_k": 5}`. Optional query params: `source`, `date_from` |
| `POST` | `/rag-search` | AI-powered answer with source citations. Body: `{"query": "...", "top_k": 5}` |
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

---

## Optional LLM Integration

By default the `/rag-search` endpoint returns a summary of the top matching article (no API key required).

To enable AI-generated answers, configure the following environment variables:

1. Copy the example env file:

```bash
cp .env.example .env
```

2. Edit `.env` and fill in your credentials:

```
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

Any OpenAI-compatible API works (OpenAI, Groq, Together AI, etc.).

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
│   └── test_api.py          # Pytest test suite (6 tests)
├── setup.py                 # One-time setup script (scrape + embed)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Container orchestration
├── .env.example             # Environment variable template
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
