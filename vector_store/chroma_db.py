"""
ChromaDB Vector Store Configuration

Centralized module for ChromaDB persistence and collection management.
Ensures consistent collection naming and persistent storage across all agents.
"""

import os
import chromadb
from chromadb.config import Settings

# Project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Persistent ChromaDB storage path
CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")

# Standardized collection name used across all agents
COLLECTION_NAME = "finnews_articles"

# Singleton client instance
_client = None


def get_client() -> chromadb.Client:
    """
    Get or create a persistent ChromaDB client.
    
    Returns:
        chromadb.Client: Persistent ChromaDB client instance
    """
    global _client
    
    if _client is None:
        # Ensure the chroma_db directory exists
        os.makedirs(CHROMA_PATH, exist_ok=True)
        
        # Create persistent client
        _client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    
    return _client


def get_or_create_collection(collection_name: str = COLLECTION_NAME):
    """
    Get or create a ChromaDB collection with the specified name.
    
    Args:
        collection_name: Name of the collection (defaults to COLLECTION_NAME)
        
    Returns:
        chromadb.Collection: The ChromaDB collection instance
    """
    client = get_client()
    return client.get_or_create_collection(name=collection_name)


def reset_collection(collection_name: str = COLLECTION_NAME):
    """
    Delete and recreate a collection (useful for testing).
    
    Args:
        collection_name: Name of the collection to reset
    """
    client = get_client()
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass  # Collection might not exist
    return client.get_or_create_collection(name=collection_name)


def list_collections():
    """
    List all collections in the ChromaDB instance.
    
    Returns:
        List of collection names
    """
    client = get_client()
    collections = client.list_collections()
    return [col.name for col in collections]


def get_collection_count(collection_name: str = COLLECTION_NAME) -> int:
    """
    Get the number of documents in a collection.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Number of documents in the collection
    """
    collection = get_or_create_collection(collection_name)
    return collection.count()
