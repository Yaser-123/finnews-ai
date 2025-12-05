"""Clear ChromaDB collection to force re-indexing"""
import chromadb

client = chromadb.PersistentClient(path='./chroma_db')
try:
    client.delete_collection('finnews_articles')
    print('✅ ChromaDB collection deleted - ready for re-indexing')
except Exception as e:
    print(f'Collection may not exist: {e}')
