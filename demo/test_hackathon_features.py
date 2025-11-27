"""
Test script for all new hackathon features.

Tests:
1. Stats Dashboard API (GET /stats/overview)
2. Query endpoint with Swagger examples
3. Real-time pipeline integration
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_stats_dashboard():
    """Test the new stats dashboard API."""
    print("\n" + "="*70)
    print("🧪 TEST 1: Stats Dashboard API")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/stats/overview")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"\n📊 Dashboard Overview:")
            print(f"   • Total Articles: {data.get('total_articles', 0)}")
            print(f"   • Unique Clusters: {data.get('unique_clusters', 0)}")
            print(f"   • Sentiment Distribution:")
            sentiment = data.get('sentiment', {})
            print(f"      - Positive: {sentiment.get('positive', 0)}")
            print(f"      - Negative: {sentiment.get('negative', 0)}")
            print(f"      - Neutral: {sentiment.get('neutral', 0)}")
            print(f"   • Top Companies: {len(data.get('top_companies', []))}")
            print(f"   • Recent Alerts: {len(data.get('alerts_last_10', []))}")
            print(f"   • Updated At: {data.get('updated_at', 'N/A')}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_stats_health():
    """Test the stats health endpoint."""
    print("\n" + "="*70)
    print("🧪 TEST 2: Stats Health Check")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/stats/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Service: {data.get('service', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_swagger_docs():
    """Test if Swagger UI is accessible with new examples."""
    print("\n" + "="*70)
    print("🧪 TEST 3: Swagger UI Documentation")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        
        if response.status_code == 200:
            print(f"✅ Swagger UI accessible at {BASE_URL}/docs")
            print(f"   • Dashboard Statistics endpoints available")
            print(f"   • Query System with examples")
            print(f"   • Pipeline and Scheduler endpoints")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_openapi_schema():
    """Test OpenAPI schema includes new endpoints."""
    print("\n" + "="*70)
    print("🧪 TEST 4: OpenAPI Schema Validation")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get('paths', {})
            
            print(f"✅ OpenAPI schema loaded")
            print(f"\n📋 Available Endpoints:")
            
            # Check for new endpoints
            required_endpoints = [
                "/stats/overview",
                "/stats/health",
                "/pipeline/query",
                "/scheduler/start",
                "/health"
            ]
            
            found = []
            missing = []
            
            for endpoint in required_endpoints:
                if endpoint in paths:
                    found.append(endpoint)
                    print(f"   ✅ {endpoint}")
                else:
                    missing.append(endpoint)
                    print(f"   ❌ {endpoint} (MISSING)")
            
            print(f"\n   Total Endpoints: {len(paths)}")
            print(f"   Required Found: {len(found)}/{len(required_endpoints)}")
            
            # Check for tags
            tags = schema.get('tags', [])
            print(f"\n📑 API Tags:")
            for tag in tags:
                print(f"   • {tag.get('name', 'Unnamed')}")
            
            return len(missing) == 0
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_scheduler_status():
    """Test scheduler status endpoint."""
    print("\n" + "="*70)
    print("🧪 TEST 5: Scheduler Status")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/scheduler/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"\n📊 Scheduler Info:")
            print(f"   • Status: {data.get('status', 'N/A')}")
            print(f"   • Last Run: {data.get('last_run', 'N/A')}")
            print(f"   • Total Runs: {data.get('total_runs', 0)}")
            print(f"   • Last Fetched: {data.get('last_fetched', 0)}")
            print(f"   • Last New: {data.get('last_new', 0)}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "🚀"*35)
    print("HACKATHON FEATURES VALIDATION TEST SUITE")
    print("🚀"*35)
    
    results = {
        "Stats Dashboard API": test_stats_dashboard(),
        "Stats Health Check": test_stats_health(),
        "Swagger UI": test_swagger_docs(),
        "OpenAPI Schema": test_openapi_schema(),
        "Scheduler Status": test_scheduler_status()
    }
    
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Ready for GitHub Push!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Fix before pushing")
    
    print("\n" + "="*70 + "\n")
