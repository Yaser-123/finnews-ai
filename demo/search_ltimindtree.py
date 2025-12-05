"""
Search for LTIMindtree articles in the database
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text as sql_text

async def search_ltimindtree():
    print("\n" + "="*70)
    print("🔍 SEARCHING FOR LTIMINDTREE ARTICLES")
    print("="*70)
    
    init_db()
    session = await get_session()
    
    async with session:
        # Search for LTIMindtree in article text
        result = await session.execute(sql_text("""
            SELECT 
                a.id,
                a.text,
                a.source,
                a.published_at,
                e.companies,
                e.sectors,
                s.label as sentiment,
                s.score as sentiment_score
            FROM articles a
            LEFT JOIN entities e ON a.id = e.article_id
            LEFT JOIN sentiment s ON a.id = s.article_id
            WHERE LOWER(a.text) LIKE '%ltimindtree%'
               OR LOWER(a.text) LIKE '%lti mindtree%'
            ORDER BY a.published_at DESC
            LIMIT 10
        """))
        
        articles = result.fetchall()
        
        if not articles:
            print(f"\n❌ No articles found containing 'LTIMindtree'")
            print(f"\nLet's check what tech companies we have:")
            
            result = await session.execute(sql_text("""
                SELECT DISTINCT unnest(companies) as company
                FROM entities
                WHERE cardinality(companies) > 0
                  AND unnest(companies) LIKE '%Tech%' 
                     OR unnest(companies) LIKE '%IT%'
                     OR unnest(companies) LIKE '%Infosys%'
                     OR unnest(companies) LIKE '%TCS%'
                     OR unnest(companies) LIKE '%Wipro%'
                ORDER BY company
                LIMIT 20
            """))
            
            tech_companies = result.fetchall()
            if tech_companies:
                print(f"\n📊 Tech/IT companies found:")
                for row in tech_companies:
                    print(f"   • {row[0]}")
            
        else:
            print(f"\n✅ Found {len(articles)} article(s) about LTIMindtree:")
            
            for i, row in enumerate(articles, 1):
                article_id = row[0]
                text = row[1]
                source = row[2]
                published = row[3]
                companies = row[4]
                sectors = row[5]
                sentiment = row[6]
                sentiment_score = row[7]
                
                print(f"\n{'='*70}")
                print(f"Article {i} (ID: {article_id})")
                print(f"{'='*70}")
                print(f"Published: {published}")
                print(f"Source: {source[:60]}...")
                print(f"\nText:\n{text[:300]}...")
                
                if companies:
                    print(f"\n Companies: {', '.join(companies[:5])}")
                if sectors:
                    print(f"Sectors: {', '.join(sectors[:5])}")
                if sentiment:
                    print(f"Sentiment: {sentiment} ({sentiment_score:.2f})")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(search_ltimindtree())
