import uuid 
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./articles.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Article(Base):
    """Shows a scraped article stored in SQLite"""

    __tablename__ = "articles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    """Open a db session,yield it and then close it when done"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Created all tables in the db if they don't exist yet""" 
    Base.metadata.create_all(bind=engine)  