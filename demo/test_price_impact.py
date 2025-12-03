"""
Test script for price impact analysis.

Tests the price impact backtest functionality with common Indian stock symbols.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.impact_model import impact_model
from analysis.helpers import get_sentiment_events


async def test_price_impact_analysis():
    """Test price impact analysis for multiple symbols."""
    
    print("\n" + "="*80)
    print("🧪 PRICE IMPACT ANALYSIS TEST")
    print("="*80)
    
    # Test symbols (common Indian stocks)
    test_symbols = [
        ("HDFCBANK", "HDFC Bank"),
        ("RELIANCE", "Reliance Industries"),
        ("TCS", "Tata Consultancy Services")
    ]
    
    results_summary = []
    
    for symbol, name in test_symbols:
        print(f"\n{'─'*80}")
        print(f"📊 Testing: {name} ({symbol})")
        print(f"{'─'*80}")
        
        try:
            # Get sentiment events
            print(f"  ⏳ Retrieving sentiment events...")
            events = await get_sentiment_events(symbol, min_score=0.7, days_back=180)
            
            if not events:
                print(f"  ⚠️  No sentiment events found for {symbol}")
                results_summary.append([
                    symbol,
                    name,
                    0,
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A"
                ])
                continue
            
            print(f"  ✅ Found {len(events)} sentiment events")
            
            # Run backtest
            print(f"  ⏳ Running price impact backtest...")
            result = await impact_model.run_backtest(symbol, events)
            
            if result.get('status') != 'success':
                print(f"  ❌ Backtest failed: {result.get('message', 'Unknown error')}")
                results_summary.append([
                    symbol,
                    name,
                    len(events),
                    "Failed",
                    "N/A",
                    "N/A",
                    "N/A"
                ])
                continue
            
            # Extract summary metrics
            summary = result.get('summary', {})
            positive = summary.get('positive', {})
            negative = summary.get('negative', {})
            
            # Get 1-day metrics
            pos_1d = positive.get('1d', {})
            neg_1d = negative.get('1d', {})
            
            pos_return = pos_1d.get('avg_return', 0.0)
            pos_winrate = pos_1d.get('winrate', 0.0)
            neg_return = neg_1d.get('avg_return', 0.0)
            neg_winrate = neg_1d.get('winrate', 0.0)
            
            print(f"  ✅ Backtest completed successfully")
            print(f"\n  📈 Results:")
            print(f"     • Total Events: {summary.get('total_events', 0)}")
            print(f"     • Positive Events: {positive.get('total_count', 0)}")
            print(f"     • Negative Events: {negative.get('total_count', 0)}")
            print(f"\n  💰 1-Day Forward Returns:")
            print(f"     • Positive Sentiment: {pos_return*100:+.2f}% (Winrate: {pos_winrate*100:.1f}%)")
            print(f"     • Negative Sentiment: {neg_return*100:+.2f}% (Winrate: {neg_winrate*100:.1f}%)")
            
            # Add to summary table
            results_summary.append([
                symbol,
                name,
                summary.get('total_events', 0),
                "Success",
                f"{pos_return*100:+.2f}%",
                f"{neg_return*100:+.2f}%",
                f"{(pos_return - neg_return)*100:.2f}%"
            ])
        
        except Exception as e:
            print(f"  ❌ Error testing {symbol}: {str(e)}")
            results_summary.append([
                symbol,
                name,
                0,
                "Error",
                "N/A",
                "N/A",
                "N/A"
            ])
    
    # Print summary table
    print(f"\n{'='*80}")
    print("📊 SUMMARY TABLE")
    print(f"{'='*80}\n")
    
    headers = [
        "Symbol",
        "Company Name",
        "Events",
        "Status",
        "Pos Return",
        "Neg Return",
        "Spread"
    ]
    
    print(tabulate(results_summary, headers=headers, tablefmt="grid"))
    
    print(f"\n{'='*80}")
    print("✅ Test completed!")
    print(f"{'='*80}\n")


async def test_api_endpoints():
    """Test API endpoints (requires server running)."""
    import requests
    
    print("\n" + "="*80)
    print("🧪 API ENDPOINTS TEST")
    print("="*80)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test 1: Supported symbols
    print("\n📋 Test 1: GET /analysis/supported-symbols")
    try:
        response = requests.get(f"{base_url}/analysis/supported-symbols")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status: {response.status_code}")
            print(f"  ✅ Symbols found: {data.get('count', 0)}")
            print(f"  ✅ Examples: {', '.join(data.get('symbols', [])[:5])}")
        else:
            print(f"  ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Server not running or error: {e}")
    
    # Test 2: Price impact analysis
    print("\n📊 Test 2: GET /analysis/price-impact/HDFCBANK")
    try:
        response = requests.get(
            f"{base_url}/analysis/price-impact/HDFCBANK",
            params={"min_score": 0.7, "days_back": 180}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status: {response.status_code}")
            print(f"  ✅ Backtest status: {data.get('status')}")
            print(f"  ✅ Events analyzed: {data.get('event_count', 0)}")
            
            if data.get('status') == 'success':
                summary = data.get('summary', {})
                positive = summary.get('positive', {}).get('1d', {})
                negative = summary.get('negative', {}).get('1d', {})
                
                print(f"\n  📈 1-Day Results:")
                print(f"     • Positive: {positive.get('avg_return', 0)*100:+.2f}%")
                print(f"     • Negative: {negative.get('avg_return', 0)*100:+.2f}%")
        else:
            print(f"  ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Server not running or error: {e}")
    
    # Test 3: Dashboard integration
    print("\n📊 Test 3: GET /stats/overview (impact model included)")
    try:
        response = requests.get(f"{base_url}/stats/overview")
        if response.status_code == 200:
            data = response.json()
            impact_model_data = data.get('impact_model', {})
            
            print(f"  ✅ Status: {response.status_code}")
            print(f"  ✅ Impact model included: {'Yes' if impact_model_data else 'No'}")
            
            if impact_model_data:
                print(f"\n  📊 Impact Model Summary:")
                print(f"     • Supported symbols: {impact_model_data.get('symbol_count', 0)}")
                print(f"     • Avg positive return: {impact_model_data.get('recent_avg_positive_return', 0)*100:+.2f}%")
                print(f"     • Avg negative return: {impact_model_data.get('recent_avg_negative_return', 0)*100:+.2f}%")
        else:
            print(f"  ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Server not running or error: {e}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    print("\n🚀 Starting Price Impact Analysis Tests...")
    print("=" * 80)
    
    # Run backtest tests
    asyncio.run(test_price_impact_analysis())
    
    # Run API tests
    print("\n⚠️  Note: API tests require server to be running")
    print("   Start with: uvicorn main:app --reload\n")
    
    asyncio.run(test_api_endpoints())
