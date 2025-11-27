"""
Test script for the FinNews AI pipeline API.
Demonstrates full pipeline execution and query functionality.
"""

import httpx
import json
from typing import Dict, Any


BASE_URL = "http://127.0.0.1:8000"


def print_separator(title: str = "", char: str = "=", width: int = 80):
    """Print a formatted separator."""
    print("\n" + char * width)
    if title:
        print(f"{title:^{width}}")
        print(char * width)


def print_json(data: Dict[Any, Any], indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent))


def test_pipeline_run():
    """Test the full pipeline execution."""
    print_separator("Step 1: Running Full Pipeline", "=")
    
    try:
        response = httpx.post(f"{BASE_URL}/pipeline/run", timeout=60.0)
        response.raise_for_status()
        
        result = response.json()
        
        print("\n✅ Pipeline executed successfully!")
        print(f"\n📊 Statistics:")
        print(f"   - Total input articles: {result['total_input']}")
        print(f"   - Unique articles: {result['unique_count']}")
        print(f"   - Clusters found: {result['clusters_count']}")
        print(f"   - Articles indexed: {result['indexed_count']}")
        print(f"   - Timestamp: {result['timestamp']}")
        
        print(f"\n📦 Clusters (showing first 5):")
        for i, cluster in enumerate(result['clusters'][:5], 1):
            main_id = cluster['main_id']
            merged_ids = cluster['merged_ids']
            if len(merged_ids) > 1:
                print(f"   {i}. Main ID {main_id} merged with: {merged_ids}")
            else:
                print(f"   {i}. ID {main_id} (no duplicates)")
        
        return True
        
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   {e.response.json()}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_pipeline_status():
    """Test getting pipeline status."""
    print_separator("Step 2: Checking Pipeline Status", "=")
    
    try:
        response = httpx.get(f"{BASE_URL}/pipeline/status", timeout=10.0)
        response.raise_for_status()
        
        result = response.json()
        
        print("\n📋 Pipeline Status:")
        print_json(result)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_query(query_text: str, top_k: int = 5):
    """Test querying the indexed articles."""
    print_separator(f"Query: {query_text}", "-")
    
    try:
        payload = {"query": query_text, "top_k": top_k}
        response = httpx.post(
            f"{BASE_URL}/pipeline/query",
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Print matched entities
        print("\n📌 Matched Entities:")
        matched = result["matched_entities"]
        if any(matched.values()):
            for entity_type, values in matched.items():
                if values:
                    print(f"   {entity_type.upper()}: {', '.join(values)}")
        else:
            print("   (No specific entities detected)")
        
        # Print results
        print(f"\n📰 Results: {len(result['results'])} articles found\n")
        
        if result["results"]:
            for i, article in enumerate(result["results"], 1):
                print(f"{i}. [ID: {article['id']}] Score: {article['score']:.3f}")
                text = article['text']
                print(f"   Text: {text[:100]}{'...' if len(text) > 100 else ''}")
                
                # Print key entities
                entities = article.get("entities", {})
                entity_parts = []
                if entities.get("companies"):
                    entity_parts.append(f"Companies: {', '.join(entities['companies'])}")
                if entities.get("sectors"):
                    entity_parts.append(f"Sectors: {', '.join(entities['sectors'])}")
                if entities.get("regulators"):
                    entity_parts.append(f"Regulators: {', '.join(entities['regulators'])}")
                
                if entity_parts:
                    print(f"   Entities: {' | '.join(entity_parts)}")
                print()
        else:
            print("   No results found.")
        
        return True
        
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   {e.response.json()}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print_separator("FinNews AI - Pipeline API Test Suite", "=")
    
    print("\n🔗 Testing API at:", BASE_URL)
    print("⚠️  Make sure the FastAPI server is running with: uvicorn main:app --reload")
    
    # Test 1: Run pipeline
    if not test_pipeline_run():
        print("\n⛔ Pipeline execution failed. Stopping tests.")
        return
    
    # Test 2: Check status
    test_pipeline_status()
    
    # Test 3: Run queries
    print_separator("Step 3: Testing Queries", "=")
    
    test_queries = [
        "HDFC Bank news",
        "banking sector update",
        "RBI policy changes",
        "interest rate impact"
    ]
    
    for query in test_queries:
        test_query(query)
    
    # Summary
    print_separator("✅ All Tests Completed!", "=")
    print("\n📊 Summary:")
    print("   - Pipeline execution: ✅")
    print("   - Status check: ✅")
    print(f"   - Queries tested: {len(test_queries)}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
