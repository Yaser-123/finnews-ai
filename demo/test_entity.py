import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.entity.agent import EntityAgent
import json


# Sample test articles
test_articles = [
    {
        "id": 1,
        "text": "HDFC Bank announces 15% dividend payout for shareholders in the current financial year."
    },
    {
        "id": 2,
        "text": "RBI raises repo rate by 25 basis points to control inflation in the banking sector."
    },
    {
        "id": 3,
        "text": "Reliance Industries reports record quarterly profit driven by strong performance in technology and finance divisions."
    }
]


def print_article_analysis(article):
    """Pretty print article analysis."""
    print(f"\n{'='*70}")
    print(f"Article ID: {article['id']}")
    print(f"Text: {article['text']}")
    print(f"\n{'Entities':^70}")
    print('-'*70)
    
    entities = article.get('entities', {})
    for entity_type, values in entities.items():
        if values:
            print(f"  {entity_type.upper()}: {', '.join(values)}")
    
    print(f"\n{'Impacted Stocks':^70}")
    print('-'*70)
    
    stocks = article.get('impacted_stocks', [])
    if stocks:
        for stock in stocks:
            print(f"  {stock['symbol']:12} | Confidence: {stock['confidence']:.1f} | "
                  f"Type: {stock['type']:10} | Entity: {stock['entity']}")
    else:
        print("  No stock mappings found")


def main():
    print("="*70)
    print(f"{'Testing EntityAgent':^70}")
    print("="*70)
    
    print("\n🔧 Initializing EntityAgent...")
    try:
        agent = EntityAgent(model_name="en_core_web_sm")
        print("✅ EntityAgent initialized successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Please run: python -m spacy download en_core_web_sm")
        return
    
    print(f"\n📊 Processing {len(test_articles)} articles...\n")
    
    # Run entity extraction
    enriched_articles = agent.run(test_articles)
    
    # Display results
    for article in enriched_articles:
        print_article_analysis(article)
    
    print(f"\n{'='*70}")
    print("✅ Entity extraction completed!")
    print("="*70)
    
    # Summary statistics
    total_stocks = sum(len(a.get('impacted_stocks', [])) for a in enriched_articles)
    total_entities = sum(
        sum(len(v) for v in a.get('entities', {}).values()) 
        for a in enriched_articles
    )
    
    print(f"\n📈 Summary:")
    print(f"  Total articles processed: {len(enriched_articles)}")
    print(f"  Total entities extracted: {total_entities}")
    print(f"  Total stock mappings: {total_stocks}")
    print()


if __name__ == "__main__":
    main()
