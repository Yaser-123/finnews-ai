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

async def save_articles(articles: List[Dict[str, Any]]) -> List[int]:
    """
    Ultra-fast batch insert with UPSERT for real-time ingestion.
    
    Uses ON CONFLICT DO NOTHING for database-level deduplication.
    Batch size: 50 items per insert for optimal performance.
    
    Args:
        articles: List of article dicts with "id", "text", "source", "published_at", "hash"
    
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
        import time
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        
        start_time = time.time()
        batch_size = 50
        inserted_count = 0
        retry_count = 0
        max_retries = 1
        
        session = await get_session()
        async with session:
            # Split into batches of 50
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i + batch_size]
                
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
                
                # Retry logic for rate limits
                while retry_count <= max_retries:
                    try:
                        # Use PostgreSQL INSERT ... ON CONFLICT DO NOTHING
                        stmt = pg_insert(Article).values(batch_data)
                        stmt = stmt.on_conflict_do_nothing(index_elements=['hash'])
                        
                        await session.execute(stmt)
                        inserted_count += len(batch)
                        break  # Success, exit retry loop
                    
                    except Exception as e:
                        error_str = str(e).lower()
                        if 'too many requests' in error_str or '429' in error_str:
                            retry_count += 1
                            if retry_count <= max_retries:
                                logger.warning(f"⚠️  Neon rate limit hit, retrying in 3s... ({retry_count}/{max_retries})")
                                import asyncio
                                await asyncio.sleep(3)
                            else:
                                logger.error(f"❌ Rate limit exceeded, skipping batch after {max_retries} retries")
                                break
                        else:
                            # Non-rate-limit error, re-raise
                            raise
            
            await session.commit()
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"⚡ Batch insert completed in {elapsed_ms}ms ({inserted_count} articles)")
            
            return [a.get("id") for a in articles[:inserted_count]]
    
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


async def save_new_articles_batch(articles: List[Dict[str, Any]]) -> List[int]:
    """
    OPTIMIZED: Ultra-fast batch insert for real-time ingestion with deduplication.
    
    Features:
    - Single SELECT query to check existing hashes
    - In-memory deduplication before DB touch
    - Batch INSERT with ON CONFLICT DO NOTHING (50 per batch)
    - Rate limit protection with retry logic
    - Detailed logging for hackathon demo
    
    Args:
        articles: List of article dicts with "id", "text", "source", "published_at", "hash"
    
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
        import time
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy import text
        
        logger.info("🚀 Ingestion batch started")
        start_time = time.time()
        
        # STEP 1: In-memory deduplication (Upgrade #2)
        logger.info(f"📦 Fetched {len(articles)} articles")
        
        hashes_seen = set()
        unique_articles = []
        in_memory_dups = 0
        
        for article in articles:
            article_hash = article.get("hash")
            if article_hash and article_hash in hashes_seen:
                in_memory_dups += 1
                continue
            if article_hash:
                hashes_seen.add(article_hash)
            unique_articles.append(article)
        
        if in_memory_dups > 0:
            logger.info(f"🧹 Removed {in_memory_dups} duplicates (in-memory)")
        
        if not unique_articles:
            logger.info("No unique articles to save after deduplication")
            return []
        
        # STEP 2: Check existing hashes in DB with single query (Upgrade #3)
        session = await get_session()
        async with session:
            hash_list = [a.get("hash") for a in unique_articles if a.get("hash")]
            
            if hash_list:
                # Single query to get all existing hashes
                result = await session.execute(
                    text("SELECT hash FROM articles WHERE hash = ANY(:hash_list)"),
                    {"hash_list": hash_list}
                )
                existing_hashes = {row[0] for row in result.fetchall()}
                
                # Filter to truly new articles
                truly_new = [a for a in unique_articles if a.get("hash") not in existing_hashes]
                db_dups = len(unique_articles) - len(truly_new)
                
                if db_dups > 0:
                    logger.info(f"🧹 Removed {db_dups} duplicates (already in DB)")
            else:
                truly_new = unique_articles
            
            if not truly_new:
                logger.info("No new articles to save (all already in database)")
                return []
            
            logger.info(f"💾 Writing {len(truly_new)} new articles to Neon (batch size 50)")
            
            # STEP 3: Batch insert with ON CONFLICT (Upgrade #1 + #4)
            batch_size = 50
            inserted_count = 0
            inserted_ids = []
            
            for i in range(0, len(truly_new), batch_size):
                batch = truly_new[i:i + batch_size]
                
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
                
                # Rate limit protection (Upgrade #4)
                retry_count = 0
                max_retries = 1
                
                while retry_count <= max_retries:
                    try:
                        # PostgreSQL UPSERT with ON CONFLICT DO NOTHING
                        stmt = pg_insert(Article).values(batch_data)
                        stmt = stmt.on_conflict_do_nothing(index_elements=['hash'])
                        
                        await session.execute(stmt)
                        inserted_count += len(batch)
                        inserted_ids.extend([a.get("id") for a in batch])
                        break  # Success
                    
                    except Exception as e:
                        error_str = str(e).lower()
                        if 'too many requests' in error_str or '429' in error_str or 'rate limit' in error_str:
                            retry_count += 1
                            if retry_count <= max_retries:
                                logger.warning(f"⚠️  Neon rate limit hit, retrying in 3s... ({retry_count}/{max_retries})")
                                import asyncio
                                await asyncio.sleep(3)
                            else:
                                logger.error(f"❌ Rate limit exceeded, skipping batch after {max_retries} retries")
                                break
                        else:
                            raise
            
            await session.commit()
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"⚡ Batch insert completed in {elapsed_ms}ms")
            logger.info(f"✅ Saved {inserted_count} new articles to database")
            
            return inserted_ids
    
    except Exception as e:
        logger.error(f"❌ Failed to save new articles: {str(e)}")
        return []


async def save_new_articles(articles: List[Dict[str, Any]]) -> List[int]:
    """
    Legacy function - redirects to optimized batch insert.
    
    Kept for backward compatibility with existing code.
    """
    return await save_new_articles_batch(articles)


async def close_db():
    """Close database connections."""
    if engine:
        await engine.dispose()
        logger.info("✅ Database connections closed")
