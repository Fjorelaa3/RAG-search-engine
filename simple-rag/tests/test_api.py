import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base, Article, get_db

# Create a separate file-based test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Use test database instead of production database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables and seed test data before each test, clean up after."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Add a sample article for testing
    article = Article(
        id="test-id-123",
        source="wikipedia",
        title="Machine learning",
        url="https://en.wikipedia.org/wiki/Machine_learning",
        content="Machine learning is a field of artificial intelligence.",
        author="Wikipedia",
    )
    db.add(article)
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health():
    """Health endpoint returns 200 and status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_article_list():
    """Article list returns correct pagination structure."""
    response = client.get("/articles")
    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


def test_article_not_found():
    """Requesting unknown article ID returns 404."""
    response = client.get("/articles/non-existent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"


def test_stats():
    """Stats endpoint returns total and by_source breakdown."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_source" in data
    assert "wikipedia" in data["by_source"]


def test_search_returns_results():
    """Search returns non-empty results for a known query."""
    response = client.post("/search", json={"query": "machine learning", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0


def test_rag_search_fallback():
    """RAG search returns valid structure without LLM key."""
    response = client.post("/rag-search", json={"query": "machine learning", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "sources" in data
    assert "confidence" in data
