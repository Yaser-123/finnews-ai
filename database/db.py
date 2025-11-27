"""
Async database client for FinNews AI using SQLAlchemy + asyncpg.

Provides connection pooling and helper functions to persist:
- Articles
- Deduplication results
- Entity extraction results
- Sentiment analysis results
- Query logs
"""

import os
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, insert
from dotenv import load_dotenv
import logging

from database.schema import Base, Article, DedupCluster, Entity, Sentiment, QueryLog

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Convert postgresql:// to postgresql+asyncpg:// for async driver
# Remove sslmode and channel_binding params (not supported by asyncpg)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    # Remove unsupported parameters
    DATABASE_URL = DATABASE_URL.replace("?sslmode=require", "")
    DATABASE_URL = DATABASE_URL.replace("&sslmode=require", "")
    DATABASE_URL = DATABASE_URL.replace("&channel_binding=require", "")
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
    DATABASE_URL = DATABASE_URL.replace("?sslmode=require", "")
    DATABASE_URL = DATABASE_URL.replace("&sslmode=require", "")
    DATABASE_URL = DATABASE_URL.replace("&channel_binding=require", "")

# Create async engine
engine = None
async_session_factory = None


def init_db():
    """Initialize database engine and session factory."""
    global engine, async_session_factory
    
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set. Database operations will be skipped.")
        return
    
    try:
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,  # Set to True for SQL query logging
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
        )
        
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("✅ Database engine initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise


async def create_tables():
    """Create all tables if they don't exist."""
    if not engine:
        logger.warning("Database not initialized. Skipping table creation.")
        return
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {str(e)}")
        raise


async def get_session() -> AsyncSession:
    """Get a new database session."""
    if not async_session_factory:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    return async_session_factory()


# ==================== Helper Functions ====================

async def save_articles(articles: List[Dict[str, Any]]) -> List[int]:
    """
    Save articles to database with smart reset.
    
    Deletes only the articles with matching IDs before inserting,
    preventing IntegrityError on repeated pipeline runs.
    
    Args:
        articles: List of article dicts with "id", "text", "source", "published_at"
    
    Returns:
        List of inserted article IDs
    """
    if not async_session_factory:
        logger.warning("Database not initialized. Skipping article save.")
        return []
    
    if not articles:
        logger.info("No articles to save")
        return []
    
    try:
        session = await get_session()
        async with session:
            # Extract IDs from incoming articles
            incoming_ids = [article.get("id") for article in articles if article.get("id") is not None]
            
            if incoming_ids:
                # Smart Reset: Delete only the articles being inserted
                from sqlalchemy import delete
                delete_stmt = delete(Article).where(Article.id.in_(incoming_ids))
                result = await session.execute(delete_stmt)
                deleted_count = result.rowcount
                
                if deleted_count > 0:
                    logger.info(f"🧹 Smart Reset: Removed {deleted_count} existing demo articles")
            
            # Bulk insert new articles
            inserted_ids = []
            for article in articles:
                new_article = Article(
                    id=article.get("id"),
                    text=article.get("text", ""),
                    source=article.get("source"),
                    published_at=article.get("published_at")
                )
                session.add(new_article)
                inserted_ids.append(article.get("id"))
            
            # Commit transaction (delete + insert)
            await session.commit()
            logger.info(f"✅ Saved {len(inserted_ids)} articles to database")
            return inserted_ids
    
    except Exception as e:
        logger.error(f"❌ Failed to save articles: {str(e)}")
        return []


async def save_dedup_results(dedup_output: Dict[str, Any]) -> bool:
    """
    Save deduplication results to database.
    
    Args:
        dedup_output: Dict with "unique_articles" and "clusters"
    
    Returns:
        True if successful, False otherwise
    """
    if not async_session_factory:
        logger.warning("Database not initialized. Skipping dedup save.")
        return False
    
    try:
        session = await get_session()
        async with session:
            clusters = dedup_output.get("clusters", [])
            
            for cluster in clusters:
                main_id = cluster.get("main_id")
                merged_ids = cluster.get("merged_ids", [])
                
                for article_id in merged_ids:
                    dedup_entry = DedupCluster(
                        article_id=article_id,
                        cluster_main_id=main_id,
                        merged_ids=merged_ids
                    )
                    session.add(dedup_entry)
            
            await session.commit()
            logger.info(f"✅ Saved {len(clusters)} deduplication clusters to database")
            return True
    
    except Exception as e:
        logger.error(f"❌ Failed to save dedup results: {str(e)}")
        return False


async def save_entities(article_id: int, entities: Dict[str, Any]) -> bool:
    """
    Save extracted entities for an article.
    
    Args:
        article_id: Article ID
        entities: Dict with "companies", "sectors", "regulators", "people", "events", "impacted_stocks"
    
    Returns:
        True if successful, False otherwise
    """
    if not async_session_factory:
        logger.warning("Database not initialized. Skipping entity save.")
        return False
    
    try:
        session = await get_session()
        async with session:
            entity_entry = Entity(
                article_id=article_id,
                companies=entities.get("companies", []),
                sectors=entities.get("sectors", []),
                regulators=entities.get("regulators", []),
                people=entities.get("people", []),
                events=entities.get("events", []),
                stocks=entities.get("impacted_stocks", [])
            )
            session.add(entity_entry)
            await session.commit()
            
            logger.debug(f"✅ Saved entities for article {article_id}")
            return True
    
    except Exception as e:
        logger.error(f"❌ Failed to save entities for article {article_id}: {str(e)}")
        return False


async def save_sentiment(article_id: int, sentiment: Dict[str, Any]) -> bool:
    """
    Save sentiment analysis result for an article.
    
    Args:
        article_id: Article ID
        sentiment: Dict with "label" and "score"
    
    Returns:
        True if successful, False otherwise
    """
    if not async_session_factory:
        logger.warning("Database not initialized. Skipping sentiment save.")
        return False
    
    try:
        session = await get_session()
        async with session:
            sentiment_entry = Sentiment(
                article_id=article_id,
                label=sentiment.get("label", "neutral"),
                score=sentiment.get("score", 0.0)
            )
            session.add(sentiment_entry)
            await session.commit()
            
            logger.debug(f"✅ Saved sentiment for article {article_id}")
            return True
    
    except Exception as e:
        logger.error(f"❌ Failed to save sentiment for article {article_id}: {str(e)}")
        return False


async def save_query_log(query: str, expanded_query: Optional[str], result_count: int) -> bool:
    """
    Save query log entry.
    
    Args:
        query: Original query text
        expanded_query: LLM-expanded query (optional)
        result_count: Number of results returned
    
    Returns:
        True if successful, False otherwise
    """
    if not async_session_factory:
        logger.warning("Database not initialized. Skipping query log save.")
        return False
    
    try:
        session = await get_session()
        async with session:
            log_entry = QueryLog(
                query=query,
                expanded_query=expanded_query,
                result_count=result_count
            )
            session.add(log_entry)
            await session.commit()
            
            logger.debug(f"✅ Saved query log: {query}")
            return True
    
    except Exception as e:
        logger.error(f"❌ Failed to save query log: {str(e)}")
        return False


async def get_recent_articles(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve recent articles from database.
    
    Args:
        limit: Maximum number of articles to return
    
    Returns:
        List of article dicts
    """
    if not async_session_factory:
        logger.warning("Database not initialized. Returning empty list.")
        return []
    
    try:
        session = await get_session()
        async with session:
            result = await session.execute(
                select(Article)
                .order_by(Article.created_at.desc())
                .limit(limit)
            )
            articles = result.scalars().all()
            
            return [
                {
                    "id": article.id,
                    "text": article.text,
                    "source": article.source,
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "created_at": article.created_at.isoformat() if article.created_at else None
                }
                for article in articles
            ]
    
    except Exception as e:
        logger.error(f"❌ Failed to retrieve recent articles: {str(e)}")
        return []


async def existing_ids(ids: List[int]) -> set:
    """
    Check which article IDs already exist in the database.
    
    Args:
        ids: List of article IDs to check
    
    Returns:
        Set of IDs that already exist in the database
    """
    if not async_session_factory:
        logger.warning("Database not initialized. Returning empty set.")
        return set()
    
    if not ids:
        return set()
    
    try:
        session = await get_session()
        async with session:
            from sqlalchemy import select
            stmt = select(Article.id).where(Article.id.in_(ids))
            result = await session.execute(stmt)
            existing = {row[0] for row in result.fetchall()}
            return existing
    
    except Exception as e:
        logger.error(f"❌ Failed to check existing IDs: {str(e)}")
        return set()


async def save_new_articles(articles: List[Dict[str, Any]]) -> List[int]:
    """
    Save only new articles to database (incremental insert).
    
    Checks for existing IDs and only inserts articles that don't exist.
    
    Args:
        articles: List of article dicts with "id", "text", "source", "published_at"
    
    Returns:
        List of newly inserted article IDs
    """
    if not async_session_factory:
        logger.warning("Database not initialized. Skipping article save.")
        return []
    
    if not articles:
        logger.info("No articles to save")
        return []
    
    try:
        # Extract IDs and check which already exist
        incoming_ids = [article.get("id") for article in articles if article.get("id") is not None]
        existing = await existing_ids(incoming_ids)
        
        # Filter to new articles only
        new_articles = [a for a in articles if a.get("id") not in existing]
        
        if not new_articles:
            logger.info("No new articles to save (all already exist)")
            return []
        
        logger.info(f"Saving {len(new_articles)} new articles (skipping {len(existing)} existing)")
        
        # Insert new articles in transaction
        session = await get_session()
        async with session:
            inserted_ids = []
            
            for article in new_articles:
                new_article = Article(
                    id=article.get("id"),
                    text=article.get("text", ""),
                    source=article.get("source"),
                    published_at=article.get("published_at")
                )
                session.add(new_article)
                inserted_ids.append(article.get("id"))
            
            # Commit transaction
            await session.commit()
            logger.info(f"✅ Saved {len(inserted_ids)} new articles to database")
            return inserted_ids
    
    except Exception as e:
        logger.error(f"❌ Failed to save new articles: {str(e)}")
        return []


async def close_db():
    """Close database connections."""
    if engine:
        await engine.dispose()
        logger.info("✅ Database connections closed")
