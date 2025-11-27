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


def get_engine():
    """Get the database engine instance."""
    return engine


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


async def run_migrations():
    """
    Run all pending database migrations.
    
    This function runs automatically on application startup.
    Migrations are idempotent and can be run multiple times safely.
    """
    if not engine:
        logger.warning("Database not initialized. Skipping migrations.")
        return
    
    try:
        # Import migration modules
        from database.migrations.migration_001_add_hash_column import run_migration as run_001
        
        # Run migrations in order
        logger.info("🔄 Running database migrations...")
        
        success = await run_001(engine)
        
        if success:
            logger.info("✅ All migrations completed successfully")
        else:
            logger.warning("⚠️ Some migrations failed or were skipped")
    
    except Exception as e:
        logger.error(f"❌ Migration runner failed: {str(e)}")
        logger.exception(e)


async def get_session() -> AsyncSession:
    """Get a new database session."""
    if not async_session_factory:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    return async_session_factory()


# ==================== Helper Functions ====================

async def save_articles(articles: List[Dict[str, Any]]) -> int:
    """
    Ultra-fast batch UPSERT with ON CONFLICT(hash) DO NOTHING.
    
    Fast-path ingestion-only mode:
    - NO embedding, NO vectorization, NO deduplication by text
    - Only DB writes for raw article storage
    - Precheck existing hashes with single SELECT
    - Batch insert 50 items at a time
    - Automatic Neon rate-limit protection with retry
    - Full execution timers for hackathon presentation
    
    Args:
        articles: List of article dicts with:
            - id: article ID (BIGINT)
            - text: article content
            - source: RSS feed URL
            - published_at: datetime
            - hash: content hash (MD5)
    
    Returns:
        Count of newly inserted articles
    """
    if not async_session_factory:
        logger.warning("Database not initialized. Skipping article save.")
        return 0
    
    if not articles:
        logger.info("No articles to save")
        return 0
    
    try:
        import time
        import asyncio
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy import text
        
        overall_start = time.time()
        total_input = len(articles)
        
        # STEP 1: Query Neon once for existing hashes (fast precheck)
        session = await get_session()
        async with session:
            hash_list = [a.get("hash") for a in articles if a.get("hash")]
            
            if hash_list:
                precheck_start = time.time()
                result = await session.execute(
                    text("SELECT hash FROM articles WHERE hash = ANY(:hash_list)"),
                    {"hash_list": hash_list}
                )
                existing_hashes = {row[0] for row in result.fetchall()}
                precheck_ms = int((time.time() - precheck_start) * 1000)
                logger.info(f"⚡ Hash precheck: {len(hash_list)} hashes in {precheck_ms}ms")
                
                # Filter out already-seen hashes
                new_articles = [a for a in articles if a.get("hash") not in existing_hashes]
                existing_skipped = total_input - len(new_articles)
            else:
                new_articles = articles
                existing_skipped = 0
            
            if not new_articles:
                logger.info(f"💾 Neon DB Write Summary:\n   • Total input: {total_input}\n   • Existing skipped: {existing_skipped}\n   • New inserted: 0\n   • Batches: 0")
                return 0
            
            # STEP 2: Split remaining into batches of 50
            batch_size = 50
            num_batches = (len(new_articles) + batch_size - 1) // batch_size
            inserted_count = 0
            
            for batch_idx in range(0, len(new_articles), batch_size):
                batch = new_articles[batch_idx:batch_idx + batch_size]
                batch_num = (batch_idx // batch_size) + 1
                
                # Prepare batch data
                batch_data = []
                for article in batch:
                    batch_data.append({
                        "id": article.get("id"),
                        "text": article.get("text", ""),
                        "source": article.get("source"),
                        "published_at": article.get("published_at"),
                        "hash": article.get("hash")
                    })
                
                # STEP 3: Insert with ON CONFLICT DO NOTHING + rate-limit protection
                retry_count = 0
                max_retries = 1
                batch_start = time.time()
                
                while retry_count <= max_retries:
                    try:
                        # PostgreSQL UPSERT with ON CONFLICT
                        stmt = pg_insert(Article).values(batch_data)
                        stmt = stmt.on_conflict_do_nothing(index_elements=["hash"])
                        
                        await session.execute(stmt)
                        inserted_count += len(batch)
                        
                        batch_ms = int((time.time() - batch_start) * 1000)
                        logger.info(f"⚡ Batch insert: {len(batch)} items in {batch_ms}ms (batch {batch_num}/{num_batches})")
                        break  # Success
                    
                    except Exception as e:
                        error_str = str(e).lower()
                        # Check for Neon rate-limit errors (429, TooManyRequests, rate limit)
                        if any(keyword in error_str for keyword in ['too many requests', '429', 'rate limit', 'toomanyrequests']):
                            retry_count += 1
                            if retry_count <= max_retries:
                                logger.warning(f"⚠️  Neon rate limit hit, retrying in 3s... (attempt {retry_count}/{max_retries})")
                                await asyncio.sleep(3)
                            else:
                                logger.warning(f"⚠️  Skipping batch {batch_num} due to Neon rate-limit (after {max_retries} retries)")
                                break
                        else:
                            # Non-rate-limit error, re-raise
                            raise
            
            await session.commit()
            
            # STEP 4: Summary logging for hackathon presentation
            overall_ms = int((time.time() - overall_start) * 1000)
            logger.info(f"💾 Neon DB Write Summary:\n   • Total input: {total_input}\n   • Existing skipped: {existing_skipped}\n   • New inserted: {inserted_count}\n   • Batches: {num_batches}\n   • Total time: {overall_ms}ms")
            
            return inserted_count
    
    except Exception as e:
        logger.error(f"❌ Failed to save articles: {str(e)}")
        logger.exception(e)
        return 0


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


async def save_new_articles_batch(articles: List[Dict[str, Any]]) -> int:
    """
    DEPRECATED: Use save_articles() instead.
    
    This function is kept for backward compatibility but redirects to save_articles().
    
    Args:
        articles: List of article dicts with "id", "text", "source", "published_at", "hash"
    
    Returns:
        Count of newly inserted articles
    """
    return await save_articles(articles)


async def save_new_articles(articles: List[Dict[str, Any]]) -> int:
    """
    DEPRECATED: Use save_articles() instead.
    
    Legacy function kept for backward compatibility with existing code.
    
    Returns:
        Count of newly inserted articles
    """
    return await save_articles(articles)


async def close_db():
    """Close database connections."""
    if engine:
        await engine.dispose()
        logger.info("✅ Database connections closed")
