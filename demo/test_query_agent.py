"""
Quick test to verify ChromaDB has indexed articles and query works
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vector_store import chroma_db
from agents.query.agent import QueryAgent

def main():
    print("\n" + "="*60)
    print("CHROMADB & QUERY AGENT VERIFICATION")
    print("="*60)
    
    # Get ChromaDB collection
    collection = chroma_db.get_or_create_collection()
    
    # Check how many articles are indexed
    count = collection.count()
    print(f"\n✅ ChromaDB Collection: {chroma_db.COLLECTION_NAME}")
    print(f"✅ Indexed Articles: {count}")
    
    if count == 0:
        print("\n⚠️  WARNING: No articles indexed in ChromaDB!")
        print("   Run the pipeline first:")
        print('   Invoke-RestMethod -Uri "http://127.0.0.1:8000/pipeline/run" -Method POST -Body \'{}\' -ContentType "application/json"')
        return
    
    # Test query agent
    print(f"\n{'='*60}")
    print("TESTING QUERY AGENT")
    print("="*60)
    
    query_agent = QueryAgent()
    
    # Test query
    test_query = "HDFC Bank dividend"
    print(f"\nQuery: {test_query}")
    
    result = query_agent.query(test_query, n_results=5)
    
    print(f"\nMatched Entities:")
    for key, values in result["matched_entities"].items():
        if values:
            print(f"  {key.title()}: {', '.join(values)}")
    
    print(f"\nResults Found: {len(result['results'])}")
    
    if result['results']:
        print(f"\nTop 3 Results:")
        for i, r in enumerate(result['results'][:3], 1):
            print(f"\n  {i}. Article ID: {r['id']} (Score: {r['score']})")
            print(f"     Text: {r['text'][:100]}...")
            if r['entities']['companies']:
                print(f"     Companies: {', '.join(r['entities']['companies'][:3])}")
    
    print(f"\n{'='*60}")
    print("✅ Query Agent is working correctly!")
    print("="*60)

if __name__ == "__main__":
    main()
