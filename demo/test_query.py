import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.dedup.agent import DeduplicationAgent
from agents.entity.agent import EntityAgent
from agents.query.agent import QueryAgent


# Sample test articles covering different topics
test_articles = [
    {
        "id": 1,
        "text": "HDFC Bank announces 15% dividend payout for shareholders in the current financial year."
    },
    {
        "id": 2,
        "text": "HDFC Bank reports strong quarterly results with 20% growth in net profit."
    },
    {
        "id": 3,
        "text": "RBI announces repo rate hike by 25 basis points to control inflation in the Indian economy."
    },
    {
        "id": 4,
        "text": "Reserve Bank of India increases repo rate by 25 bps to tackle rising inflation."
    },
    {
        "id": 5,
        "text": "Banking sector faces challenges as interest rates continue to rise across major economies."
    },
    {
        "id": 6,
        "text": "ICICI Bank and Axis Bank report improved loan portfolio performance in Q3 2024."
    },
    {
        "id": 7,
        "text": "RBI introduces new guidelines for digital lending platforms to protect consumer interests."
    },
    {
        "id": 8,
        "text": "Technology sector shows strong growth with major investments in AI and cloud computing."
    },
    {
        "id": 9,
        "text": "Interest rate hikes impact mortgage lending and consumer borrowing across financial institutions."
    },
    {
        "id": 10,
        "text": "SEBI announces new regulations for mutual fund disclosure and transparency requirements."
    }
]


def print_separator(title=""):
    """Print a formatted separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"{title:^80}")
        print("=" * 80)


def print_query_results(query_text, result):
    """Pretty print query results."""
    print_separator(f"Query: {query_text}")
    
    # Print matched entities
    print("\n📌 Matched Entities:")
    matched = result["matched_entities"]
    if any(matched.values()):
        for entity_type, values in matched.items():
            if values:
                print(f"  {entity_type.upper()}: {', '.join(values)}")
    else:
        print("  (No specific entities detected)")
    
    # Print results
    print(f"\n📰 Results: {len(result['results'])} articles found\n")
    print("-" * 80)
    
    if result["results"]:
        for i, article in enumerate(result["results"], 1):
            print(f"\n{i}. [ID: {article['id']}] Score: {article['score']:.3f}")
            print(f"   Text: {article['text'][:100]}{'...' if len(article['text']) > 100 else ''}")
            
            # Print entities if present
            entities = article.get("entities", {})
            entity_summary = []
            if entities.get("companies"):
                entity_summary.append(f"Companies: {', '.join(entities['companies'])}")
            if entities.get("sectors"):
                entity_summary.append(f"Sectors: {', '.join(entities['sectors'])}")
            if entities.get("regulators"):
                entity_summary.append(f"Regulators: {', '.join(entities['regulators'])}")
            
            if entity_summary:
                print(f"   Entities: {' | '.join(entity_summary)}")
    else:
        print("  No results found.")
    
    print("\n" + "-" * 80)


def main():
    print_separator("FinNews AI - Query Agent Test")
    
    print("\n🔧 Step 1: Initializing agents...")
    dedup_agent = DeduplicationAgent(threshold=0.85)
    entity_agent = EntityAgent()
    query_agent = QueryAgent()
    print("✅ All agents initialized")
    
    print("\n🔧 Step 2: Processing articles...")
    print(f"   - Initial articles: {len(test_articles)}")
    
    # Deduplicate articles
    dedup_result = dedup_agent.run(test_articles)
    unique_articles = dedup_result["unique_articles"]
    print(f"   - After deduplication: {len(unique_articles)} unique articles")
    print(f"   - Clusters found: {len(dedup_result['clusters'])}")
    
    # Enrich with entities
    enriched_articles = entity_agent.run(unique_articles)
    print(f"   - Articles enriched with entities")
    
    print("\n🔧 Step 3: Indexing articles into vector database...")
    query_agent.index_articles(enriched_articles)
    print(f"✅ Indexed {len(enriched_articles)} articles")
    
    # Test queries
    test_queries = [
        "HDFC Bank news",
        "banking sector update",
        "RBI policy changes",
        "interest rate impact"
    ]
    
    print("\n🔧 Step 4: Testing queries...\n")
    
    for query_text in test_queries:
        result = query_agent.query(query_text, n_results=5)
        print_query_results(query_text, result)
    
    print_separator("Test Completed")
    print("\n✅ All queries executed successfully!")
    print(f"\n📊 Summary:")
    print(f"   - Total unique articles indexed: {len(enriched_articles)}")
    print(f"   - Test queries executed: {len(test_queries)}")
    print()


if __name__ == "__main__":
    main()
