"""
Real-time RSS/HTTP news ingestion module.

Fetches articles from RSS feeds, normalizes them, and generates
deterministic IDs for deduplication.

Features:
- Multi-source RSS feed support (6+ feeds)
- Concurrent feed fetching with async/await
- Deterministic ID generation for deduplication
- Error-resilient (continues on individual feed failures)
- Age-based filtering
"""

import os
import hashlib
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
import asyncio

import httpx
import feedparser
from dotenv import load_dotenv

from ingest.utils import clean_html, normalize_title, compute_hash

load_dotenv()

logger = logging.getLogger(__name__)

# Premium RSS feeds (12 sources for comprehensive financial news coverage)
DEFAULT_FEEDS = [
    # Moneycontrol (3 feeds)
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    # Economic Times (2 feeds)
    "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    "https://economictimes.indiatimes.com/industry/banking/finance/rssfeeds/13358259.cms",
    # Livemint (2 feeds)
    "https://www.livemint.com/rss/money",
    "https://www.livemint.com/rss/markets",
    # NDTV Profit
    "https://www.ndtvprofit.com/rss/business",
    # Financial Times India
    "https://www.ft.com/rss/world/asia-pacific/india",
    # CNBC TV18
    "https://www.cnbctv18.com/rss/business.xml",
    # Google News (2 feeds)
    "https://news.google.com/rss/search?q=indian+banking+sector&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=RBI+policy+india&hl=en-IN&gl=IN&ceid=IN:en",
]


def get_configured_feeds() -> List[str]:
    """
    Get RSS feed URLs from environment or use defaults.
    
    Returns:
        List of RSS feed URLs
    """
    env_feeds = os.getenv("RSS_FEEDS", "")
    
    if env_feeds:
        # Parse comma-separated feed URLs
        feeds = [f.strip() for f in env_feeds.split(",") if f.strip()]
        logger.info(f"Using {len(feeds)} feeds from RSS_FEEDS env var")
        return feeds
    
    logger.info(f"Using {len(DEFAULT_FEEDS)} default feeds")
    return DEFAULT_FEEDS


def generate_article_id(feed_url: str, guid: str, published: str) -> int:
    """
    Generate deterministic article ID using SHA-1 hash.
    
    Args:
        feed_url: Source feed URL
        guid: Entry GUID or unique identifier
        published: Published timestamp in ISO format
    
    Returns:
        Integer ID (15 hex digits converted to int)
    """
    # Create unique string combining feed, guid, and timestamp
    unique_str = f"{feed_url}|{guid}|{published}"
    
    # Generate SHA-1 hash
    hash_obj = hashlib.sha1(unique_str.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Convert first 15 hex digits to int (stays within safe int range)
    article_id = int(hash_hex[:15], 16)
    
    return article_id


def normalize_entry(feed_url: str, entry: Any) -> Optional[Dict[str, Any]]:
    """
    Normalize RSS feed entry to article dict with HTML cleanup and hash.
    
    Args:
        feed_url: Source feed URL
        entry: feedparser entry object
    
    Returns:
        Article dict with id, title, text, source, published_at, hash
        or None if entry is invalid
    """
    try:
        # Extract GUID (prefer id, fallback to link or title)
        guid = entry.get('id', '') or entry.get('link', '') or entry.get('title', '')
        if not guid:
            logger.warning(f"Entry missing GUID from {feed_url}")
            return None
        
        # Extract and clean title
        title = entry.get('title', '').strip()
        if not title:
            logger.warning(f"Entry missing title: {guid}")
            return None
        
        title_clean = clean_html(title)
        if not title_clean:
            return None
        
        # Extract content (prefer summary, fallback to description or content)
        summary = ""
        if hasattr(entry, 'summary'):
            summary = entry.summary
        elif hasattr(entry, 'description'):
            summary = entry.description
        elif hasattr(entry, 'content') and entry.content:
            summary = entry.content[0].get('value', '')
        
        # Clean HTML from summary
        summary_clean = clean_html(summary)
        
        # Combine title and summary for text
        text = f"{title_clean}. {summary_clean}".strip() if summary_clean else title_clean
        
        # Generate content hash for deduplication
        content_hash = compute_hash(normalize_title(title_clean))
        
        # Extract published timestamp
        published_dt = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                # Create timezone-aware datetime for ID generation
                published_dt_utc = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                # Convert to naive datetime for PostgreSQL (TIMESTAMP WITHOUT TIME ZONE)
                published_dt = published_dt_utc.replace(tzinfo=None)
            except Exception as e:
                logger.warning(f"Failed to parse published date: {e}")
        
        # Use current time if no published date
        if not published_dt:
            published_dt = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Generate deterministic ID using ISO format
        published_iso = published_dt.isoformat()
        article_id = generate_article_id(feed_url, guid, published_iso)
        
        return {
            "id": article_id,
            "title": title_clean,
            "text": text,
            "source": feed_url,
            "published_at": published_dt,  # Naive datetime for PostgreSQL
            "guid": guid,
            "hash": content_hash
        }
    
    except Exception as e:
        logger.error(f"Failed to normalize entry from {feed_url}: {str(e)}")
        return None


async def fetch_feed(session: httpx.AsyncClient, feed_url: str) -> List[Dict[str, Any]]:
    """
    Fetch and parse a single RSS feed.
    
    Handles errors gracefully and continues processing other feeds.
    
    Args:
        session: httpx async client session
        feed_url: RSS feed URL
    
    Returns:
        List of normalized article dicts (empty list on failure)
    """
    try:
        # Extract domain for logging
        domain = feed_url.split('/')[2] if len(feed_url.split('/')) > 2 else feed_url
        logger.info(f"📡 Fetching feed: {domain}")
        
        # Fetch feed with timeout and user-agent (some sites block bots)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = await session.get(
            feed_url,
            timeout=10.0,
            follow_redirects=True,
            headers=headers
        )
        response.raise_for_status()
        
        # Parse feed
        feed = feedparser.parse(response.text)
        
        # Check for feed errors
        if hasattr(feed, 'bozo') and feed.bozo:
            logger.warning(f"⚠️  Feed parsing warning for {domain}: {feed.get('bozo_exception', 'Unknown')}")
        
        # Normalize entries
        articles = []
        for entry in feed.entries:
            article = normalize_entry(feed_url, entry)
            if article:
                articles.append(article)
        
        logger.info(f"✅ Fetched {len(articles)} articles from {domain}")
        return articles
    
    except httpx.TimeoutException:
        logger.error(f"❌ Timeout (10s) fetching feed: {feed_url}")
        return []
    except httpx.HTTPError as e:
        logger.error(f"❌ HTTP error fetching feed {feed_url}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching feed {feed_url}: {str(e)}")
        return []


async def fetch_all(feeds: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fetch and parse all RSS feeds concurrently with hash-based deduplication.
    
    Args:
        feeds: Optional list of feed URLs (uses configured feeds if None)
    
    Returns:
        List of unique normalized articles from all feeds (deduplicated by hash)
    """
    if feeds is None:
        feeds = get_configured_feeds()
    
    logger.info(f"Starting fetch for {len(feeds)} feeds...")
    
    # Create async HTTP client
    async with httpx.AsyncClient() as session:
        # Fetch all feeds concurrently
        tasks = [fetch_feed(session, feed_url) for feed_url in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Flatten results and filter out exceptions
    all_articles = []
    successful_feeds = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"❌ Feed {feeds[i]} failed with exception: {str(result)}")
        elif isinstance(result, list):
            all_articles.extend(result)
            if result:  # Count non-empty results
                successful_feeds += 1
    
    # Deduplicate by hash (content-based) and ID (feed-based)
    seen_ids: Set[int] = set()
    seen_hashes: Set[str] = set()
    deduplicated = []
    id_duplicates = 0
    hash_duplicates = 0
    
    for article in all_articles:
        # Skip if duplicate by ID
        if article['id'] in seen_ids:
            id_duplicates += 1
            continue
        
        # Skip if duplicate by content hash
        article_hash = article.get('hash', '')
        if article_hash and article_hash in seen_hashes:
            hash_duplicates += 1
            continue
        
        # Add to results
        seen_ids.add(article['id'])
        if article_hash:
            seen_hashes.add(article_hash)
        deduplicated.append(article)
    
    logger.info(f"✅ Total fetched: {len(all_articles)} articles from {successful_feeds}/{len(feeds)} feeds")
    if id_duplicates > 0:
        logger.info(f"🔄 Removed {id_duplicates} duplicate articles by ID")
    if hash_duplicates > 0:
        logger.info(f"🔄 Removed {hash_duplicates} duplicate articles by content hash")
    
    all_articles = deduplicated
    
    # Filter by age if MAX_AGE_HOURS is set
    max_age_hours = int(os.getenv("MAX_AGE_HOURS", "168"))  # Default 7 days
    if max_age_hours > 0:
        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        
        filtered = []
        for article in all_articles:
            try:
                pub_dt = datetime.fromisoformat(article["published_at"].replace('Z', '+00:00'))
                if pub_dt.timestamp() >= cutoff:
                    filtered.append(article)
            except Exception:
                # Keep article if date parsing fails
                filtered.append(article)
        
        if len(filtered) < len(all_articles):
            logger.info(f"Filtered {len(all_articles) - len(filtered)} articles older than {max_age_hours}h")
        
        all_articles = filtered
    
    return all_articles


if __name__ == "__main__":
    # Test fetch
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        articles = await fetch_all()
        print(f"\n{'='*60}")
        print(f"Fetched {len(articles)} articles")
        print(f"{'='*60}")
        
        if articles:
            print("\nSample article:")
            print(f"ID: {articles[0]['id']}")
            print(f"Title: {articles[0]['title'][:80]}...")
            print(f"Source: {articles[0]['source']}")
            print(f"Published: {articles[0]['published_at']}")
    
    asyncio.run(test())
