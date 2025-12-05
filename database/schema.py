"""
Database schema for FinNews AI using SQLAlchemy.

Tables:
- articles: Raw financial news articles
- dedup_clusters: Deduplication results with cluster information
- entities: Extracted financial entities (companies, sectors, regulators, etc.)
- sentiment: Sentiment analysis results
- query_logs: Query history with expansion and result counts
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, DateTime, ARRAY, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Article(Base):
    """Raw financial news articles."""
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("hash", name="uq_article_hash"),
    )
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    source = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    hash = Column(String, nullable=True, index=True)


class DedupCluster(Base):
    """Deduplication results with cluster information."""
    __tablename__ = "dedup_clusters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, nullable=False)
    cluster_main_id = Column(Integer, nullable=True)
    merged_ids = Column(ARRAY(Integer), nullable=True)
    similarity_score = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())


class Entity(Base):
    """Extracted financial entities from articles."""
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, nullable=False)
    companies = Column(ARRAY(Text), nullable=True)
    sectors = Column(ARRAY(Text), nullable=True)
    regulators = Column(ARRAY(Text), nullable=True)
    people = Column(ARRAY(Text), nullable=True)
    events = Column(ARRAY(Text), nullable=True)
    stocks = Column(JSON, nullable=True)  # [{"symbol": "HDFCBANK", "confidence": 1.0, "type": "direct"}]
    created_at = Column(DateTime, nullable=False, default=func.now())


class Sentiment(Base):
    """Sentiment analysis results."""
    __tablename__ = "sentiment"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, nullable=False)
    label = Column(Text, nullable=False)  # positive, negative, neutral
    score = Column(Float, nullable=False)  # confidence score 0.0-1.0
    created_at = Column(DateTime, nullable=False, default=func.now())


class QueryLog(Base):
    """Query history with expansion and result counts."""
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    expanded_query = Column(Text, nullable=True)
    result_count = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
