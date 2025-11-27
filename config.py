"""
Centralized configuration management for FinNews AI.

Loads environment variables and provides type-safe settings.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # RSS Feed Configuration
    RSS_FEED_LIST: List[str] = []
    
    # Ingestion Settings
    INGEST_INTERVAL: int = int(os.getenv("INGEST_INTERVAL", "60"))
    AUTO_START_SCHEDULER: bool = os.getenv("AUTO_START_SCHEDULER", "false").lower() == "true"
    MAX_AGE_HOURS: int = int(os.getenv("MAX_AGE_HOURS", "168"))
    
    def __init__(self):
        """Initialize settings and parse RSS_FEEDS."""
        # Parse RSS_FEEDS from comma-separated string
        rss_feeds_str = os.getenv("RSS_FEEDS", "")
        
        if rss_feeds_str:
            # Split by comma and strip whitespace
            self.RSS_FEED_LIST = [
                feed.strip() 
                for feed in rss_feeds_str.split(",") 
                if feed.strip()
            ]
        else:
            # Use default verified working feeds (12 sources)
            self.RSS_FEED_LIST = [
                # Economic Times (3 feeds)
                "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
                "https://economictimes.indiatimes.com/industry/banking/finance/rssfeeds/13358259.cms",
                "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
                # Livemint (2 feeds)
                "https://www.livemint.com/rss/money",
                "https://www.livemint.com/rss/markets",
                # NDTV (main RSS)
                "https://www.ndtv.com/rss",
                # Financial Times India
                "https://www.ft.com/rss/world/asia-pacific/india",
                # CNBC TV18 (corrected)
                "https://www.cnbctv18.com/rss/",
                # Google News (4 feeds for comprehensive coverage)
                "https://news.google.com/rss/search?q=indian+banking+sector&hl=en-IN&gl=IN&ceid=IN:en",
                "https://news.google.com/rss/search?q=RBI+policy+india&hl=en-IN&gl=IN&ceid=IN:en",
                "https://news.google.com/rss/search?q=indian+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
                "https://news.google.com/rss/search?q=india+economy&hl=en-IN&gl=IN&ceid=IN:en",
            ]
    
    def get_feed_count(self) -> int:
        """Get the number of configured RSS feeds."""
        return len(self.RSS_FEED_LIST)
    
    def validate(self) -> bool:
        """
        Validate required settings.
        
        Returns:
            True if all required settings are present
        """
        if not self.DATABASE_URL:
            print("⚠️  Warning: DATABASE_URL not configured")
            return False
        
        if not self.GEMINI_API_KEY:
            print("⚠️  Warning: GEMINI_API_KEY not configured")
            return False
        
        if not self.RSS_FEED_LIST:
            print("⚠️  Warning: No RSS feeds configured")
            return False
        
        return True


# Global settings instance
settings = Settings()


# For backwards compatibility and convenience
def get_rss_feeds() -> List[str]:
    """
    Get configured RSS feed URLs.
    
    Returns:
        List of RSS feed URLs
    """
    return settings.RSS_FEED_LIST


def get_database_url() -> str:
    """Get database URL."""
    return settings.DATABASE_URL


def get_gemini_api_key() -> str:
    """Get Gemini API key."""
    return settings.GEMINI_API_KEY


if __name__ == "__main__":
    # Test configuration
    print("FinNews AI Configuration")
    print("=" * 60)
    print(f"Database URL: {'✅ Configured' if settings.DATABASE_URL else '❌ Missing'}")
    print(f"Gemini API Key: {'✅ Configured' if settings.GEMINI_API_KEY else '❌ Missing'}")
    print(f"\nRSS Feeds ({settings.get_feed_count()}):")
    for i, feed in enumerate(settings.RSS_FEED_LIST, 1):
        print(f"  {i}. {feed}")
    print(f"\nIngestion Settings:")
    print(f"  Interval: {settings.INGEST_INTERVAL}s")
    print(f"  Auto-start: {settings.AUTO_START_SCHEDULER}")
    print(f"  Max age: {settings.MAX_AGE_HOURS}h")
    print(f"\nValidation: {'✅ Passed' if settings.validate() else '❌ Failed'}")
