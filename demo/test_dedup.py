import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.dedup.agent import DeduplicationAgent


# Sample test articles
test_articles = [
    {
        "id": 1,
        "text": "RBI announces repo rate hike by 25 basis points to control inflation in the Indian economy."
    },
    {
        "id": 2,
        "text": "Reserve Bank of India increases repo rate by 25 bps to tackle rising inflation."
    },
    {
        "id": 3,
        "text": "HDFC Bank reports strong quarterly results with 20% growth in net profit."
    }
]


def main():
    print("=" * 60)
    print("Testing DeduplicationAgent")
    print("=" * 60)
    
    # Initialize agent
    agent = DeduplicationAgent(threshold=0.80)
    
    print(f"\nInput: {len(test_articles)} articles")
    for article in test_articles:
        print(f"  - ID {article['id']}: {article['text'][:60]}...")
    
    # Run deduplication
    result = agent.run(test_articles)
    
    print(f"\n{'=' * 60}")
    print("Results:")
    print("=" * 60)
    
    print(f"\nUnique articles: {len(result['unique_articles'])}")
    for article in result["unique_articles"]:
        print(f"  - ID {article['id']}: {article['text'][:60]}...")
    
    print(f"\nClusters: {len(result['clusters'])}")
    for cluster in result["clusters"]:
        main_id = cluster["main_id"]
        merged_ids = cluster["merged_ids"]
        if len(merged_ids) > 1:
            print(f"  - Main ID {main_id} merged with: {merged_ids}")
        else:
            print(f"  - ID {main_id} (no duplicates)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
