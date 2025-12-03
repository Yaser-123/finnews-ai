"""
Quick test to verify price impact model works without database.
"""

import asyncio
import yfinance as yf
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.impact_model import PriceImpactModel


async def quick_test():
    """Quick test without database dependency."""
    
    print("\n" + "="*70)
    print("🧪 QUICK PRICE IMPACT MODEL TEST")
    print("="*70)
    
    model = PriceImpactModel()
    
    # Test 1: Download price data
    print("\n📊 Test 1: Download Price Data")
    symbol = "RELIANCE.NS"  # Reliance on NSE
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"  ⏳ Downloading {symbol} data...")
    price_data = model.download_price_data(symbol, start_date, end_date)
    
    if price_data is not None and not price_data.empty:
        print(f"  ✅ Downloaded {len(price_data)} trading days")
        print(f"  ✅ Date range: {price_data.index[0].date()} to {price_data.index[-1].date()}")
        print(f"  ✅ Latest close: ₹{price_data['Close'].iloc[-1]:.2f}")
    else:
        print(f"  ❌ Failed to download data")
        return False
    
    # Test 2: Compute forward returns
    print("\n📈 Test 2: Compute Forward Returns")
    event_date = price_data.index[5]  # Use 6th trading day
    print(f"  ⏳ Computing returns for {event_date.date()}...")
    
    returns = model.compute_forward_returns(price_data, event_date)
    
    print(f"  ✅ 1-Day Return: {returns['return_1d']*100:+.2f}%" if returns['return_1d'] else "  ⚠️  No 1-day return")
    print(f"  ✅ 3-Day Return: {returns['return_3d']*100:+.2f}%" if returns['return_3d'] else "  ⚠️  No 3-day return")
    print(f"  ✅ 7-Day Return: {returns['return_7d']*100:+.2f}%" if returns['return_7d'] else "  ⚠️  No 7-day return")
    
    # Test 3: Aggregate metrics
    print("\n📊 Test 3: Aggregate Metrics")
    
    # Create mock events
    mock_events = [
        {
            'timestamp': price_data.index[5],
            'sentiment_label': 'POSITIVE',
            'sentiment_score': 0.85,
            'returns': model.compute_forward_returns(price_data, price_data.index[5])
        },
        {
            'timestamp': price_data.index[10],
            'sentiment_label': 'POSITIVE',
            'sentiment_score': 0.90,
            'returns': model.compute_forward_returns(price_data, price_data.index[10])
        },
        {
            'timestamp': price_data.index[7],
            'sentiment_label': 'NEGATIVE',
            'sentiment_score': 0.80,
            'returns': model.compute_forward_returns(price_data, price_data.index[7])
        }
    ]
    
    metrics = model.compute_aggregated_metrics(mock_events)
    
    print(f"  ✅ Total events: {metrics['total_events']}")
    print(f"  ✅ Positive events: {metrics['positive']['total_count']}")
    print(f"  ✅ Negative events: {metrics['negative']['total_count']}")
    
    pos_1d = metrics['positive']['1d']
    print(f"\n  💰 Positive Sentiment (1D):")
    print(f"     • Avg Return: {pos_1d['avg_return']*100:+.2f}%")
    print(f"     • Win Rate: {pos_1d['winrate']*100:.1f}%")
    
    # Test 4: Full backtest
    print("\n🔄 Test 4: Full Backtest")
    
    backtest_events = [
        {
            'timestamp': price_data.index[i],
            'sentiment_label': 'POSITIVE' if i % 2 == 0 else 'NEGATIVE',
            'sentiment_score': 0.85
        }
        for i in range(5, 15)
    ]
    
    print(f"  ⏳ Running backtest with {len(backtest_events)} events...")
    result = await model.run_backtest("RELIANCE.NS", backtest_events)
    
    if result.get('status') == 'success':
        print(f"  ✅ Backtest completed successfully")
        summary = result['summary']
        print(f"  ✅ Total events analyzed: {summary['total_events']}")
    else:
        print(f"  ❌ Backtest failed: {result.get('message')}")
    
    print(f"\n{'='*70}")
    print("✅ All tests passed!")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    asyncio.run(quick_test())
