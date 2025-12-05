"""
Process all remaining articles through the complete pipeline:
- Entity extraction
- Sentiment analysis
- ChromaDB indexing
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text as sql_text
from agents.entity.agent import EntityAgent
from agents.sentiment.agent import SentimentAgent
from vector_store.chroma_db import get_or_create_collection
from sentence_transformers import SentenceTransformer

async def process_all_articles():
    print("\n" + "="*70)
    print("🚀 STEP 4: PROCESSING ALL ARTICLES")
    print("="*70)
    
    # Initialize
    init_db()
    entity_agent = EntityAgent()
    sentiment_agent = SentimentAgent()
    embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    collection = get_or_create_collection()
    
    session = await get_session()
    
    async with session:
        # Get articles that haven't been processed
        result = await session.execute(sql_text("""
            SELECT a.id, a.text
            FROM articles a
            LEFT JOIN entities e ON a.id = e.article_id
            WHERE e.id IS NULL
            ORDER BY a.id
        """))
        
        unprocessed = result.fetchall()
        total_unprocessed = len(unprocessed)
        
        print(f"\n📊 Status:")
        print(f"   Unprocessed articles: {total_unprocessed}")
        
        if total_unprocessed == 0:
            print(f"\n✅ All articles already processed!")
            return
        
        print(f"\n🔄 Processing articles in batches of 50...")
        
        processed_count = 0
        batch_size = 50
        
        for i in range(0, total_unprocessed, batch_size):
            batch = unprocessed[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_unprocessed + batch_size - 1) // batch_size
            
            print(f"\n   Batch {batch_num}/{total_batches} ({len(batch)} articles)...")
            
            for article_id, text in batch:
                try:
                    # Extract entities
                    entities_result = entity_agent.extract_entities(text)
                    
                    # Insert entities
                    await session.execute(sql_text("""
                        INSERT INTO entities (article_id, companies, sectors, regulators, events)
                        VALUES (:article_id, :companies, :sectors, :regulators, :events)
                    """), {
                        "article_id": article_id,
                        "companies": entities_result.get('companies', []),
                        "sectors": entities_result.get('sectors', []),
                        "regulators": entities_result.get('regulators', []),
                        "events": entities_result.get('events', [])
                    })
                    
                    # Analyze sentiment
                    sentiment_result = sentiment_agent.analyze(text)
                    
                    # Insert sentiment
                    await session.execute(sql_text("""
                        INSERT INTO sentiment (article_id, label, score)
                        VALUES (:article_id, :label, :score)
                    """), {
                        "article_id": article_id,
                        "label": sentiment_result.get('label', 'neutral'),
                        "score": sentiment_result.get('score', 0.0)
                    })
                    
                    # Generate embedding
                    embedding = embedding_model.encode(text).tolist()
                    
                    # Index in ChromaDB
                    collection.add(
                        ids=[str(article_id)],
                        embeddings=[embedding],
                        documents=[text],
                        metadatas=[{
                            'article_id': article_id,
                            'companies': str(entities_result.get('companies', [])),
                            'sectors': str(entities_result.get('sectors', [])),
                            'regulators': str(entities_result.get('regulators', [])),
                            'events': str(entities_result.get('events', [])),
                            'sentiment': sentiment_result.get('label', 'neutral'),
                            'sentiment_score': sentiment_result.get('score', 0.0)
                        }]
                    )
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"      ❌ Error processing article {article_id}: {str(e)}")
            
            # Commit batch
            await session.commit()
            print(f"   ✅ Batch {batch_num} complete: {processed_count}/{total_unprocessed} total processed")
    
    print(f"\n📊 Final Statistics:")
    
    session = await get_session()
    async with session:
        result = await session.execute(sql_text("SELECT COUNT(*) FROM articles"))
        total_articles = result.scalar()
        
        result = await session.execute(sql_text("SELECT COUNT(*) FROM entities"))
        total_entities = result.scalar()
        
        result = await session.execute(sql_text("SELECT COUNT(*) FROM sentiment"))
        total_sentiment = result.scalar()
        
        print(f"   Total articles: {total_articles}")
        print(f"   With entities: {total_entities} ({total_entities/total_articles*100:.1f}%)")
        print(f"   With sentiment: {total_sentiment} ({total_sentiment/total_articles*100:.1f}%)")
        
        chroma_count = collection.count()
        print(f"   Indexed in ChromaDB: {chroma_count} ({chroma_count/total_articles*100:.1f}%)")
    
    print(f"\n{'='*70}")
    print(f"✅ ALL ARTICLES PROCESSED!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(process_all_articles())
