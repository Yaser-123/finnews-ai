"""
Demo data for FinNews AI pipeline testing.
Contains sample financial news articles covering various topics.
"""

from typing import List, Dict, Any


def get_demo_articles() -> List[Dict[str, Any]]:
    """
    Get demo articles for testing the pipeline.
    
    Returns:
        List of article dicts with id and text fields
    """
    articles = [
        {
            "id": 1,
            "text": "HDFC Bank announces 15% dividend payout for shareholders in the current financial year, marking strong performance."
        },
        {
            "id": 2,
            "text": "HDFC Bank reports strong quarterly results with 20% growth in net profit driven by retail lending."
        },
        {
            "id": 3,
            "text": "RBI announces repo rate hike by 25 basis points to control inflation in the Indian economy."
        },
        {
            "id": 4,
            "text": "Reserve Bank of India increases repo rate by 25 bps to tackle rising inflation pressures."
        },
        {
            "id": 5,
            "text": "Banking sector faces challenges as interest rates continue to rise across major economies worldwide."
        },
        {
            "id": 6,
            "text": "ICICI Bank and Axis Bank report improved loan portfolio performance in Q3 2024 with reduced NPAs."
        },
        {
            "id": 7,
            "text": "RBI introduces new guidelines for digital lending platforms to protect consumer interests and ensure transparency."
        },
        {
            "id": 8,
            "text": "Technology sector shows strong growth with major investments in AI and cloud computing infrastructure."
        },
        {
            "id": 9,
            "text": "Interest rate hikes impact mortgage lending and consumer borrowing across financial institutions."
        },
        {
            "id": 10,
            "text": "SEBI announces new regulations for mutual fund disclosure and transparency requirements for investors."
        },
        {
            "id": 11,
            "text": "Reliance Industries reports record quarterly profit driven by strong performance in technology and petrochemicals."
        },
        {
            "id": 12,
            "text": "State Bank of India launches new digital banking services with enhanced security features for customers."
        },
        {
            "id": 13,
            "text": "Banking sector consolidation continues as mergers reshape the competitive landscape in Indian finance."
        },
        {
            "id": 14,
            "text": "HDFC Bank expands digital payment infrastructure with new UPI features and merchant partnerships."
        },
        {
            "id": 15,
            "text": "Technology companies like TCS and Infosys report strong demand for cloud and AI consulting services."
        },
        {
            "id": 16,
            "text": "RBI monetary policy committee maintains cautious stance on inflation targeting and economic growth."
        },
        {
            "id": 17,
            "text": "ICICI Bank introduces green financing initiative for sustainable projects and renewable energy investments."
        },
        {
            "id": 18,
            "text": "Interest rate fluctuations create opportunities and challenges for fixed income investors in bond markets."
        },
        {
            "id": 19,
            "text": "Axis Bank focuses on retail banking expansion with increased branch network in tier-2 and tier-3 cities."
        },
        {
            "id": 20,
            "text": "Financial technology startups see increased funding as digital payments adoption accelerates across India."
        }
    ]
    
    return articles
