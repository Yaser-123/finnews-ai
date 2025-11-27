"""
Real-time news ingestion module for FinNews AI.
"""

from .realtime import fetch_all, fetch_feed, normalize_entry, DEFAULT_FEEDS

__all__ = ["fetch_all", "fetch_feed", "normalize_entry", "DEFAULT_FEEDS"]
