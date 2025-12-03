"""
Test suite for LLM safety, rate limiting, and usage tracking.

Tests:
1. Rate limiter blocks excessive calls
2. Safety guard removes banned financial advice
3. Citations are enforced
4. Usage tracking records metrics correctly
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.llm.limiter import RateLimiter, LLMRateLimitError
from agents.llm.safety import SafetyGuard, SafetyViolationError
from agents.llm.usage import UsageTracker


def test_rate_limiter():
    """Test that rate limiter blocks excessive calls."""
    print("\n" + "="*70)
    print("🧪 TEST 1: Rate Limiter")
    print("="*70)
    
    # Create a strict rate limiter (max 5 calls)
    limiter = RateLimiter(max_calls_per_minute=5, max_calls_per_request=5)
    
    try:
        # Should allow first 5 calls
        for i in range(5):
            limiter.allow_call()
            limiter.register_call()
            print(f"   ✅ Call {i+1}/5 allowed")
        
        # 6th call should raise error
        try:
            limiter.allow_call()
            print(f"   ❌ FAIL: Rate limiter did not block 6th call")
            return False
        except LLMRateLimitError as e:
            print(f"   ✅ Call 6/5 blocked: {str(e)[:80]}...")
            return True
    
    except Exception as e:
        print(f"   ❌ Test failed: {str(e)}")
        return False


def test_safety_guard_financial_advice():
    """Test that safety guard blocks banned financial advice phrases."""
    print("\n" + "="*70)
    print("🧪 TEST 2: Safety Guard - Financial Advice Blocking")
    print("="*70)
    
    guard = SafetyGuard()
    
    # Test cases with banned phrases
    banned_texts = [
        "This stock has guaranteed returns of 50%.",
        "Buy now for sure profit!",
        "This is a risk-free investment opportunity.",
        "You will get 100% profit within a month."
    ]
    
    blocked_count = 0
    
    for text in banned_texts:
        try:
            guard.block_financial_advice(text)
            print(f"   ❌ FAIL: Did not block '{text[:50]}...'")
        except SafetyViolationError:
            print(f"   ✅ Blocked: '{text[:50]}...'")
            blocked_count += 1
    
    # Test safe text
    safe_text = "HDFC Bank reported quarterly earnings of Rs 1000 crore."
    try:
        result = guard.block_financial_advice(safe_text)
        print(f"   ✅ Allowed safe text: '{safe_text[:50]}...'")
        blocked_count += 1
    except SafetyViolationError:
        print(f"   ❌ FAIL: Blocked safe text")
    
    success = blocked_count == 5
    print(f"\n   Result: {blocked_count}/5 tests passed")
    return success


def test_citation_enforcement():
    """Test that citations are enforced in responses."""
    print("\n" + "="*70)
    print("🧪 TEST 3: Citation Enforcement")
    print("="*70)
    
    guard = SafetyGuard()
    
    # Test 1: Text without citations
    text_without = "HDFC Bank has strong fundamentals and solid growth prospects."
    sources = ["Article 123", "Article 456"]
    
    result = guard.enforce_citations(text_without, sources)
    
    if "Sources:" in result or "Article 123" in result:
        print(f"   ✅ Citations added to text without sources")
        test1_pass = True
    else:
        print(f"   ❌ FAIL: Citations not added")
        print(f"      Result: {result}")
        test1_pass = False
    
    # Test 2: Text already with citations
    text_with = "HDFC Bank reported earnings. Sources: Bloomberg, Reuters"
    result = guard.enforce_citations(text_with, sources)
    
    if "Sources:" in result or "sources:" in result.lower():
        print(f"   ✅ Existing citations preserved")
        test2_pass = True
    else:
        print(f"   ❌ FAIL: Citations removed")
        test2_pass = False
    
    # Test 3: Full sanitization with citations
    text = "HDFC Bank shows strong performance in Q3 2024."
    sanitized = guard.sanitize(text, sources=sources, strict=False)
    
    if "Sources:" in sanitized or "Note:" in sanitized:
        print(f"   ✅ Full sanitization includes citations")
        test3_pass = True
    else:
        print(f"   ❌ FAIL: Sanitization missing citations")
        print(f"      Result: {sanitized}")
        test3_pass = False
    
    success = test1_pass and test2_pass and test3_pass
    print(f"\n   Result: {'PASS' if success else 'FAIL'}")
    return success


def test_hallucination_removal():
    """Test that hallucination patterns are removed."""
    print("\n" + "="*70)
    print("🧪 TEST 4: Hallucination Removal")
    print("="*70)
    
    guard = SafetyGuard()
    
    # Text with hallucinations
    text = (
        "HDFC Bank reported strong earnings. "
        "In my opinion, this is a great sign. "
        "I think the stock will perform well. "
        "According to my analysis, the fundamentals are solid."
    )
    
    cleaned = guard.remove_hallucinations(text)
    
    hallucination_phrases = ["in my opinion", "i think", "according to my analysis"]
    removed_count = sum(1 for phrase in hallucination_phrases if phrase not in cleaned.lower())
    
    print(f"   Original: {text}")
    print(f"   Cleaned:  {cleaned}")
    print(f"   Removed {removed_count}/3 hallucination patterns")
    
    success = removed_count >= 2  # At least 2 should be removed
    print(f"\n   Result: {'PASS' if success else 'FAIL'}")
    return success


def test_usage_tracker():
    """Test that usage tracker records metrics correctly."""
    print("\n" + "="*70)
    print("🧪 TEST 5: Usage Tracker")
    print("="*70)
    
    tracker = UsageTracker()
    tracker.reset()
    
    # Record some calls
    tracker.record_call(input_tokens=100, output_tokens=50, latency=0.5)
    tracker.record_call(input_tokens=200, output_tokens=100, latency=0.8)
    tracker.record_failure()
    
    stats = tracker.get_stats()
    
    tests_passed = 0
    
    # Check total calls
    if stats["total_calls"] == 2:
        print(f"   ✅ Total calls: {stats['total_calls']}")
        tests_passed += 1
    else:
        print(f"   ❌ Total calls: Expected 2, got {stats['total_calls']}")
    
    # Check total tokens
    if stats["total_input_tokens"] == 300 and stats["total_output_tokens"] == 150:
        print(f"   ✅ Total tokens: {stats['total_tokens']} (input: {stats['total_input_tokens']}, output: {stats['total_output_tokens']})")
        tests_passed += 1
    else:
        print(f"   ❌ Token counts incorrect")
    
    # Check failures
    if stats["total_failures"] == 1:
        print(f"   ✅ Total failures: {stats['total_failures']}")
        tests_passed += 1
    else:
        print(f"   ❌ Total failures: Expected 1, got {stats['total_failures']}")
    
    # Check cost estimation
    if stats["cost_estimation_usd"] > 0:
        print(f"   ✅ Cost estimation: ${stats['cost_estimation_usd']:.6f} USD")
        tests_passed += 1
    else:
        print(f"   ❌ Cost estimation not calculated")
    
    # Check latency
    if stats["avg_latency_ms"] > 0:
        print(f"   ✅ Avg latency: {stats['avg_latency_ms']:.2f} ms")
        tests_passed += 1
    else:
        print(f"   ❌ Latency not tracked")
    
    success = tests_passed == 5
    print(f"\n   Result: {tests_passed}/5 checks passed")
    return success


def test_rate_limiter_reset():
    """Test that rate limiter allows calls after reset."""
    print("\n" + "="*70)
    print("🧪 TEST 6: Rate Limiter Request Counter Reset")
    print("="*70)
    
    limiter = RateLimiter(max_calls_per_request=3)
    
    try:
        # Use up request limit
        for i in range(3):
            limiter.allow_call()
            limiter.register_call()
        
        # Should block 4th call
        try:
            limiter.allow_call()
            print(f"   ❌ FAIL: Did not block 4th call")
            return False
        except LLMRateLimitError:
            print(f"   ✅ Blocked 4th call (limit reached)")
        
        # Reset counter
        limiter.reset_request_counter()
        print(f"   ✅ Request counter reset")
        
        # Should allow call after reset
        limiter.allow_call()
        print(f"   ✅ New call allowed after reset")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "🚀"*35)
    print("LLM SAFETY & TRACKING TEST SUITE")
    print("🚀"*35)
    
    results = {
        "Rate Limiter": test_rate_limiter(),
        "Financial Advice Blocking": test_safety_guard_financial_advice(),
        "Citation Enforcement": test_citation_enforcement(),
        "Hallucination Removal": test_hallucination_removal(),
        "Usage Tracker": test_usage_tracker(),
        "Rate Limiter Reset": test_rate_limiter_reset()
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
        print("\n🎉 ALL TESTS PASSED - LLM Safety & Tracking Ready!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Review implementation")
    
    print("\n" + "="*70 + "\n")
