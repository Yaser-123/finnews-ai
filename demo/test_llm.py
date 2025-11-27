import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set Gemini API key
os.environ["GEMINI_API_KEY"] = "AIzaSyD6KUbq38AcTKJZUI3OmoS6JkAY4e-DOMk"

from agents.llm.agent import LLMAgent


def print_separator(title: str = "", char: str = "=", width: int = 80):
    """Print a formatted separator."""
    print("\n" + char * width)
    if title:
        print(f"{title:^{width}}")
        print(char * width)


def test_expand_query():
    """Test query expansion functionality."""
    print_separator("Test 1: Query Expansion", "=")
    
    test_queries = [
        {"query": "HDFC Bank news"},
        {"query": "RBI policy changes"},
        {"query": "banking sector update"}
    ]
    
    agent = LLMAgent()
    
    for query_dict in test_queries:
        print(f"\n📝 Original Query: {query_dict['query']}")
        result = agent.expand_query(query_dict)
        print(f"✨ Expanded Query:\n   {result['expanded']}")


def test_summarize_article():
    """Test article summarization functionality."""
    print_separator("Test 2: Article Summarization", "=")
    
    test_articles = [
        {
            "id": 1,
            "text": "HDFC Bank announces 15% dividend payout for shareholders in the current financial year, marking strong performance driven by retail lending growth and improved asset quality.",
            "sentiment": {"label": "positive", "score": 0.95}
        },
        {
            "id": 2,
            "text": "Banking sector faces severe challenges as rising NPAs and credit defaults threaten financial stability. Analysts warn of potential liquidity crunch.",
            "sentiment": {"label": "negative", "score": 0.96}
        },
        {
            "id": 3,
            "text": "RBI maintains repo rate at current levels, citing balanced approach to inflation and growth targets. Monetary policy committee votes 5-1 in favor.",
            "sentiment": {"label": "neutral", "score": 0.79}
        }
    ]
    
    agent = LLMAgent()
    
    for article in test_articles:
        result = agent.summarize_article(article)
        sentiment = result['sentiment']
        sentiment_label = sentiment.get('label', 'unknown').upper()
        sentiment_score = sentiment.get('score', 0.0)
        
        print(f"\n📰 Article ID {result['id']} ({sentiment_label}, {sentiment_score:.2f}):")
        print(f"   Original: {article['text'][:80]}...")
        print(f"   Summary: {result['summary']}")


def test_interpret_regulation():
    """Test regulatory interpretation functionality."""
    print_separator("Test 3: Regulatory Interpretation", "=")
    
    test_regulations = [
        "RBI raises repo rate by 25 basis points to control inflation",
        "SEBI introduces new disclosure norms for mutual fund houses",
        "Government reduces corporate tax rate from 30% to 22% for manufacturing firms"
    ]
    
    agent = LLMAgent()
    
    for i, reg_text in enumerate(test_regulations, 1):
        print(f"\n🏛️ Regulation {i}:")
        print(f"   Text: {reg_text}")
        
        result = agent.interpret_regulation(reg_text)
        
        print(f"\n   📊 Analysis:")
        print(f"   • Impact: {result['impact']}")
        print(f"   • Affected Sectors: {', '.join(result['affected_sectors'])}")
        print(f"   • Risk Level: {result['risk_level']}")
        print(f"   • Explanation: {result['explanation']}")


def main():
    """Run all LLM agent tests."""
    print_separator("FinNews AI - LLM Agent Test Suite (Gemini 2.5 Flash)", "=")
    
    print("\n🔧 Initializing LLMAgent with Gemini 2.5 Flash...")
    try:
        agent = LLMAgent()
        print("✅ LLMAgent initialized successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure GEMINI_API_KEY is set correctly")
        return
    
    # Run all tests
    try:
        test_expand_query()
        test_summarize_article()
        test_interpret_regulation()
        
        # Summary
        print_separator("✅ All Tests Completed Successfully!", "=")
        print("\n📊 Summary:")
        print("   - Query expansion: ✅ PASSED")
        print("   - Article summarization: ✅ PASSED")
        print("   - Regulatory interpretation: ✅ PASSED")
        print()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")


if __name__ == "__main__":
    main()
