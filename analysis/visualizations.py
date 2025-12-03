"""
Visualization module for price impact analysis.

Generates charts showing sentiment events overlaid on price movements.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
import yfinance as yf


# Create reports directory if it doesn't exist
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def plot_price_impact(
    symbol: str,
    price_data: pd.DataFrame,
    events: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> str:
    """
    Generate price impact visualization.
    
    Args:
        symbol: Stock ticker symbol
        price_data: OHLC price DataFrame from yfinance
        events: List of sentiment events with returns
        output_path: Optional custom output path
    
    Returns:
        Path to saved PNG file
    """
    if output_path is None:
        output_path = REPORTS_DIR / f"impact_{symbol}.png"
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    fig.suptitle(f'{symbol} - Price Impact Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Price chart with sentiment events
    ax1.plot(price_data.index, price_data['Close'], label='Close Price', color='#2E86AB', linewidth=1.5)
    
    # Overlay sentiment events
    positive_events = [e for e in events if e['sentiment_label'] == 'POSITIVE']
    negative_events = [e for e in events if e['sentiment_label'] == 'NEGATIVE']
    neutral_events = [e for e in events if e['sentiment_label'] == 'NEUTRAL']
    
    # Get prices at event dates
    for event in positive_events:
        event_date = pd.Timestamp(event['timestamp'].date())
        if event_date in price_data.index:
            price = price_data.loc[event_date, 'Close']
            ax1.scatter(event_date, price, color='#06D6A0', s=100, marker='^', 
                       alpha=0.7, edgecolors='black', linewidth=0.5, zorder=5)
    
    for event in negative_events:
        event_date = pd.Timestamp(event['timestamp'].date())
        if event_date in price_data.index:
            price = price_data.loc[event_date, 'Close']
            ax1.scatter(event_date, price, color='#EF476F', s=100, marker='v', 
                       alpha=0.7, edgecolors='black', linewidth=0.5, zorder=5)
    
    for event in neutral_events:
        event_date = pd.Timestamp(event['timestamp'].date())
        if event_date in price_data.index:
            price = price_data.loc[event_date, 'Close']
            ax1.scatter(event_date, price, color='#FFD166', s=80, marker='o', 
                       alpha=0.6, edgecolors='black', linewidth=0.5, zorder=5)
    
    ax1.set_ylabel('Price (₹)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(['Price', 'Positive Sentiment', 'Negative Sentiment', 'Neutral Sentiment'], 
               loc='upper left', framealpha=0.9)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 2: Forward returns distribution
    returns_1d = [e['returns']['return_1d'] for e in events if e['returns']['return_1d'] is not None]
    
    if returns_1d:
        colors = []
        for e in events:
            if e['returns']['return_1d'] is not None:
                if e['sentiment_label'] == 'POSITIVE':
                    colors.append('#06D6A0')
                elif e['sentiment_label'] == 'NEGATIVE':
                    colors.append('#EF476F')
                else:
                    colors.append('#FFD166')
        
        bars = ax2.bar(range(len(returns_1d)), [r * 100 for r in returns_1d], color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax2.set_ylabel('1-Day Forward Return (%)', fontsize=11, fontweight='bold')
        ax2.set_xlabel('Event Index', fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return str(output_path)


async def generate_impact_chart(
    symbol: str,
    backtest_result: Dict[str, Any]
) -> Optional[str]:
    """
    Generate impact chart from backtest result.
    
    Args:
        symbol: Stock ticker symbol
        backtest_result: Result from impact_model.run_backtest()
    
    Returns:
        Path to generated chart or None if failed
    """
    if backtest_result.get('status') != 'success':
        return None
    
    try:
        # Extract events and price data range
        events = backtest_result.get('events', [])
        price_range = backtest_result.get('price_data_range', {})
        
        if not events:
            return None
        
        # Download price data again for visualization
        start_date = datetime.fromisoformat(price_range['start'])
        end_date = datetime.fromisoformat(price_range['end'])
        
        ticker = yf.Ticker(symbol)
        price_data = ticker.history(start=start_date, end=end_date)
        
        if price_data.empty:
            return None
        
        # Generate chart
        chart_path = plot_price_impact(symbol, price_data, events)
        
        return chart_path
    
    except Exception as e:
        print(f"Error generating chart for {symbol}: {e}")
        return None
