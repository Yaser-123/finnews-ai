import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.sentiment.agent import SentimentAgent


# Sample test articles with different sentiments
test_articles = [
    {
        "id": 1,
        "text": "HDFC Bank reports strong quarterly results with 20% growth in net profit, exceeding analyst expectations."
    },
    {
        "id": 2,
        "text": "Banking sector faces severe challenges as rising NPAs and credit defaults threaten financial stability."
    },
    {
        "id": 3,
        "text": "RBI maintains repo rate at current levels, citing balanced approach to inflation and growth targets."
    },
    {
        "id": 4,
        "text": "Stock markets crash as investor confidence plummets amid global economic uncertainty and recession fears."
    },
    {
        "id": 5,
        "text": "Company announces dividend payout of 15% for shareholders after successful year of operations."
    },
    {
        "id": 6,
        "text": "Analysts maintain neutral outlook on banking stocks with mixed signals from economic indicators."
    }
]


def print_separator(title="", char="=", width=80):
    """Print a formatted separator."""
    print("\n" + char * width)
    if title:
        print(f"{title:^{width}}")
        print(char * width)


def main():
    print_separator("FinNews AI - Sentiment Analysis Test")
    
    print("\n🔧 Initializing SentimentAgent (loading FinBERT model)...")
    try:
        agent = SentimentAgent()
        print("✅ SentimentAgent initialized successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure transformers and torch are installed")
        return
    
    print(f"\n📊 Analyzing sentiment for {len(test_articles)} articles...\n")
    
    # Run sentiment analysis
    results = agent.run(test_articles)
    
    # Display results
    print_separator("Sentiment Analysis Results", "-")
    print()
    
    # Count sentiment distribution
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    
    for article in results:
        article_id = article["id"]
        text = article["text"]
        sentiment = article["sentiment"]
        label = sentiment["label"]
        score = sentiment["score"]
        
        # Color coding for terminal output
        emoji = {
            "positive": "😊 ✅",
            "negative": "😟 ❌",
            "neutral": "😐 ➖"
        }
        
        print(f"ID {article_id}: {emoji.get(label, '')} {label.upper()} (confidence: {score:.4f})")
        print(f"   Text: {text[:80]}{'...' if len(text) > 80 else ''}")
        print()
        
        sentiment_counts[label] += 1
    
    # Summary
    print_separator("Summary Statistics", "-")
    print()
    print(f"📈 Sentiment Distribution:")
    print(f"   Positive: {sentiment_counts['positive']} articles")
    print(f"   Negative: {sentiment_counts['negative']} articles")
    print(f"   Neutral:  {sentiment_counts['neutral']} articles")
    print()
    print(f"✅ Total articles analyzed: {len(results)}")
    
    print_separator()


if __name__ == "__main__":
    main()
