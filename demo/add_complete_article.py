"""
Add a comprehensive test article with all entity types
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import save_articles, init_db, create_tables

async def add_test_article():
    # Initialize database first
    init_db()
    await create_tables()
    # Create a rich article with ALL entity types
    article = {
        "title": "HDFC Bank Reports Record Profit as RBI Approves Major Merger in Banking Sector",
        "text": """HDFC Bank Reports Record Profit as RBI Approves Major Merger in Banking Sector
        
Mumbai: In a landmark development for the Indian banking sector, HDFC Bank announced a record-breaking 25% growth in quarterly profit, coinciding with the Reserve Bank of India's approval of its proposed merger with HDFC Ltd. The announcement came as the bank declared a generous 20% dividend payout to shareholders.

The RBI's monetary policy committee, in coordination with SEBI, has given the green light for this historic merger, which is expected to create one of the largest banking entities in India. The move aligns with the central bank's vision for consolidation in the finance sector.

HDFC Bank's CEO stated that the merger will strengthen the bank's position in both retail and corporate banking segments. The bank's strong performance was driven by robust growth in the technology and insurance sectors, with significant exposure to pharma and auto industries as well.

Industry analysts predict this merger will set a precedent for future acquisitions in the Indian banking landscape, potentially triggering an IPO wave among smaller banks seeking capital infusion. The combined entity is expected to generate earnings exceeding $5 billion in the first year post-merger.

This development comes at a crucial time when the Reserve Bank of India is implementing stricter regulations on digital lending platforms and fintech companies operating in the finance and technology sectors.""",
        "source": "test_complete",
        "published_at": datetime.now(),
        "hash": f"complete_test_article_{int(datetime.now().timestamp())}"
    }
    
    # Save to database
    count = await save_articles([article])
    print(f"✅ Added comprehensive test article")
    print(f"   Articles saved: {count}")
    print(f"\nArticle preview:")
    print(f"Title: {article['title']}")
    print(f"\nExpected entities:")
    print("  Companies: HDFC Bank, HDFC Ltd")
    print("  Sectors: Banking, Finance, Technology, Insurance, Pharma, Auto")
    print("  Regulators: RBI, Reserve Bank of India, SEBI")
    print("  Events: Profit, Dividend, Merger, Acquisition, IPO, Earnings")

if __name__ == "__main__":
    asyncio.run(add_test_article())
