"""
Vector Store Module

Provides centralized ChromaDB configuration and utilities.
"""

from .chroma_db import (
    CHROMA_PATH,
    COLLECTION_NAME,
    get_client,
    get_or_create_collection,
    reset_collection,
    list_collections,
    get_collection_count
)

__all__ = [
    "CHROMA_PATH",
    "COLLECTION_NAME",
    "get_client",
    "get_or_create_collection",
    "reset_collection",
    "list_collections",
    "get_collection_count"
]
