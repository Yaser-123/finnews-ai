"""
Test LLM API endpoints for usage tracking and health monitoring.
"""

import requests
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://127.0.0.1:8000"


def test_llm_stats():
    """Test GET /llm/stats endpoint."""
    print("\n" + "="*70)
    print("🧪 TEST 1: LLM Stats API")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/llm/stats")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"\n📊 LLM Usage Statistics:")
            print(f"   • Total Calls: {data.get('total_calls', 0)}")
            print(f"   • Total Tokens: {data.get('total_tokens', 0)}")
            print(f"   • Input Tokens: {data.get('total_input_tokens', 0)}")
            print(f"   • Output Tokens: {data.get('total_output_tokens', 0)}")
            print(f"   • Total Failures: {data.get('total_failures', 0)}")
            print(f"   • Failure Rate: {data.get('failure_rate', 0):.2%}")
            print(f"   • Avg Latency: {data.get('avg_latency_ms', 0):.2f} ms")
            print(f"   • Cost Estimation: ${data.get('cost_estimation_usd', 0):.6f}")
            print(f"   • Cost per 1M tokens: ${data.get('cost_per_1m_tokens_usd', 0):.2f}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_llm_health():
    """Test GET /llm/health endpoint."""
    print("\n" + "="*70)
    print("🧪 TEST 2: LLM Health API")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/llm/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"\n💚 LLM Health Status:")
            print(f"   • Status: {data.get('status', 'unknown').upper()}")
            print(f"   • Total Calls: {data.get('total_calls', 0)}")
            print(f"   • Total Failures: {data.get('total_failures', 0)}")
            print(f"   • Failure Rate: {data.get('failure_rate', 0):.2%}")
            print(f"   • Remaining Calls: {data.get('remaining_calls', 0)}")
            print(f"   • Message: {data.get('message', 'N/A')}")
            
            status = data.get('status', 'unknown')
            if status in ['healthy', 'degraded', 'capped']:
                print(f"\n   ✅ Valid health status: {status}")
                return True
            else:
                print(f"\n   ❌ Invalid health status: {status}")
                return False
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_openapi_schema():
    """Test that LLM endpoints are in OpenAPI schema."""
    print("\n" + "="*70)
    print("🧪 TEST 3: OpenAPI Schema Validation")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get('paths', {})
            
            print(f"✅ OpenAPI schema loaded")
            
            # Check for LLM endpoints
            llm_endpoints = [
                "/llm/stats",
                "/llm/health",
                "/llm/reset"
            ]
            
            found = []
            missing = []
            
            for endpoint in llm_endpoints:
                if endpoint in paths:
                    found.append(endpoint)
                    print(f"   ✅ {endpoint}")
                else:
                    missing.append(endpoint)
                    print(f"   ❌ {endpoint} (MISSING)")
            
            # Check for LLM tag
            tags = schema.get('tags', [])
            llm_tag_found = any(tag.get('name') == 'LLM' for tag in tags)
            
            if llm_tag_found:
                print(f"   ✅ LLM tag found in OpenAPI")
            else:
                print(f"   ⚠️  LLM tag not found (may be auto-generated)")
            
            return len(missing) == 0
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "🚀"*35)
    print("LLM API ENDPOINTS TEST SUITE")
    print("🚀"*35)
    print("\n⚠️  Make sure the server is running: uvicorn main:app --reload")
    print("   Server URL: http://127.0.0.1:8000\n")
    
    results = {
        "LLM Stats API": test_llm_stats(),
        "LLM Health API": test_llm_health(),
        "OpenAPI Schema": test_openapi_schema()
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
        print("\n🎉 ALL TESTS PASSED - LLM API Ready!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("\n" + "="*70 + "\n")
