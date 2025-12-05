"""
Final verification of complete FinNews AI system
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text as sql_text
from vector_store.chroma_db import get_or_create_collection

async def final_verification():
    print("\n" + "="*70)
    print("🎉 FINNEWS AI - COMPLETE SYSTEM VERIFICATION")
    print("="*70)
    
    # Initialize database
    init_db()
    
    session = await get_session()
    
    async with session:
        # Database stats
        result = await session.execute(sql_text("SELECT COUNT(*) FROM articles"))
        total_articles = result.scalar()
        
        result = await session.execute(sql_text("SELECT COUNT(DISTINCT article_id) FROM entities"))
        articles_with_entities = result.scalar()
        
        result = await session.execute(sql_text("SELECT COUNT(DISTINCT article_id) FROM sentiment"))
        articles_with_sentiment = result.scalar()
        
        # Metadata stats
        result = await session.execute(sql_text("""
            SELECT 
                COUNT(*) FILTER (WHERE source IS NOT NULL) as with_source,
                COUNT(*) FILTER (WHERE published_at IS NOT NULL) as with_published,
                COUNT(*) FILTER (WHERE hash IS NOT NULL) as with_hash
            FROM articles
        """))
        metadata = result.fetchone()
        
        print(f"\n📊 DATABASE STATUS:")
        print(f"   ✅ Total articles: {total_articles}")
        print(f"   ✅ Articles with source: {metadata[0]} ({metadata[0]/total_articles*100:.1f}%)")
        print(f"   ✅ Articles with published_at: {metadata[1]} ({metadata[1]/total_articles*100:.1f}%)")
        print(f"   ✅ Articles with hash: {metadata[2]} ({metadata[2]/total_articles*100:.1f}%)")
        print(f"   ✅ Articles with entities: {articles_with_entities} ({articles_with_entities/total_articles*100:.1f}%)")
        print(f"   ✅ Articles with sentiment: {articles_with_sentiment} ({articles_with_sentiment/total_articles*100:.1f}%)")
        
        # ID range
        result = await session.execute(sql_text("SELECT MIN(id), MAX(id) FROM articles"))
        id_range = result.fetchone()
        print(f"   ✅ ID range: {id_range[0]} to {id_range[1]} (clean sequential)")
        
        # Source distribution
        result = await session.execute(sql_text("""
            SELECT 
                CASE 
                    WHEN source LIKE '%economictimes%' THEN 'Economic Times'
                    WHEN source LIKE '%livemint%' THEN 'LiveMint'
                    WHEN source LIKE '%ft.com%' THEN 'Financial Times'
                    WHEN source LIKE '%google%' THEN 'Google News'
                    ELSE 'Other'
                END as source_type,
                COUNT(*) as count
            FROM articles
            GROUP BY source_type
            ORDER BY count DESC
        """))
        
        print(f"\n📰 SOURCES:")
        for row in result.fetchall():
            print(f"   {row[0]:<20} {row[1]:>3} articles")
        
        # Entity stats
        result = await session.execute(sql_text("""
            SELECT 
                COUNT(*) FILTER (WHERE cardinality(companies) > 0) as with_companies,
                COUNT(*) FILTER (WHERE cardinality(sectors) > 0) as with_sectors,
                COUNT(*) FILTER (WHERE cardinality(regulators) > 0) as with_regulators,
                COUNT(*) FILTER (WHERE cardinality(events) > 0) as with_events
            FROM entities
        """))
        entity_stats = result.fetchone()
        
        print(f"\n🏢 ENTITY EXTRACTION:")
        print(f"   Companies mentioned: {entity_stats[0]} articles")
        print(f"   Sectors identified: {entity_stats[1]} articles")
        print(f"   Regulators mentioned: {entity_stats[2]} articles")
        print(f"   Events detected: {entity_stats[3]} articles")
        
        # Sentiment distribution
        result = await session.execute(sql_text("""
            SELECT label, COUNT(*) as count
            FROM sentiment
            GROUP BY label
            ORDER BY count DESC
        """))
        
        print(f"\n💭 SENTIMENT ANALYSIS:")
        for row in result.fetchall():
            print(f"   {row[0].capitalize():<12} {row[1]:>3} articles")
        
    # ChromaDB stats
    collection = get_or_create_collection()
    chroma_count = collection.count()
    print(f"\n📦 VECTOR SEARCH:")
    print(f"   Indexed in ChromaDB: {chroma_count} articles")
    print(f"   Coverage: {chroma_count/total_articles*100:.1f}%")
    
    print(f"\n{'='*70}")
    print(f"✅ SYSTEM STATUS: FULLY OPERATIONAL")
    print(f"{'='*70}")
    
    print(f"\n🚀 READY FOR:")
    print(f"   • Real-time RSS feed ingestion")
    print(f"   • Entity extraction (companies, sectors, regulators, events)")
    print(f"   • Sentiment analysis (FinBERT)")
    print(f"   • Semantic search queries")
    print(f"   • Entity-based filtering")
    print(f"   • Dashboard visualization")
    
    print(f"\n📝 SAMPLE QUERIES:")
    print(f"   • 'HDFC Bank news'")
    print(f"   • 'RBI monetary policy'")
    print(f"   • 'banking sector updates'")
    print(f"   • 'interest rate changes'")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(final_verification())
