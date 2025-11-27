"""
Utility functions for RSS feed processing and cleanup.

Provides HTML cleaning, text normalization, and hashing for deduplication.
"""

import re
import hashlib
from typing import Optional


def clean_html(text: str) -> str:
    """
    Remove HTML tags and junk formatting from RSS feeds.
    
    Args:
        text: Raw text with potential HTML
        
    Returns:
        Cleaned text without HTML tags
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r"<.*?>", "", text)
    
    # Replace common HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&apos;", "'")
    
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    
    return text.strip()


def normalize_title(text: str) -> str:
    """
    Normalize titles for duplicate comparison.
    
    Converts to lowercase, removes punctuation, and normalizes whitespace.
    
    Args:
        text: Original title text
        
    Returns:
        Normalized title for comparison
    """
    # Clean HTML first
    text = clean_html(text).lower()
    
    # Remove all non-alphanumeric characters except spaces
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    
    return text.strip()


def compute_hash(text: str) -> str:
    """
    Generate stable MD5 hash for deduplication.
    
    Args:
        text: Text to hash (typically normalized title)
        
    Returns:
        MD5 hash as hexadecimal string
    """
    if not text:
        return ""
    
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL for logging.
    
    Args:
        url: Full URL
        
    Returns:
        Domain name or None
    """
    try:
        parts = url.split('//')
        if len(parts) > 1:
            domain = parts[1].split('/')[0]
            return domain
        return url.split('/')[0]
    except Exception:
        return None


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


if __name__ == "__main__":
    # Test utilities
    print("RSS Utility Functions Test")
    print("=" * 60)
    
    # Test HTML cleaning
    html_text = '<p>HDFC Bank <a href="link">climbs</a> &nbsp; to new high</p>'
    clean_text = clean_html(html_text)
    print(f"\nHTML Cleaning:")
    print(f"  Original: {html_text}")
    print(f"  Cleaned:  {clean_text}")
    
    # Test normalization
    title1 = "HDFC Bank climbs to new high!"
    title2 = "HDFC Bank climbs to new high."
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    print(f"\nTitle Normalization:")
    print(f"  Title 1: {title1}")
    print(f"  Norm 1:  {norm1}")
    print(f"  Title 2: {title2}")
    print(f"  Norm 2:  {norm2}")
    print(f"  Same?    {norm1 == norm2}")
    
    # Test hashing
    hash1 = compute_hash(norm1)
    hash2 = compute_hash(norm2)
    print(f"\nHashing:")
    print(f"  Hash 1: {hash1}")
    print(f"  Hash 2: {hash2}")
    print(f"  Same?   {hash1 == hash2}")
