"""
Price Impact Model - Historical sentiment-price backtest.

Analyzes the relationship between sentiment events and subsequent stock price movements.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import time
import asyncio
from functools import lru_cache


class PriceImpactModel:
    """Historical price impact backtest for sentiment events."""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._cache = {}
    
    def download_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Download OHLC price data with retry logic.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for data
            end_date: End date for data
        
        Returns:
            DataFrame with OHLC data or None if failed
        """
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        for attempt in range(self.max_retries):
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if data.empty:
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                        continue
                    return None
                
                # Cache successful download
                self._cache[cache_key] = data
                return data
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                print(f"Error downloading {symbol} after {self.max_retries} attempts: {e}")
                return None
        
        return None
    
    def compute_forward_returns(
        self,
        price_data: pd.DataFrame,
        event_date: datetime
    ) -> Dict[str, float]:
        """
        Compute forward returns for 1d, 3d, 7d.
        
        Args:
            price_data: OHLC price DataFrame
            event_date: Event timestamp
        
        Returns:
            Dict with return_1d, return_3d, return_7d
        """
        returns = {
            "return_1d": None,
            "return_3d": None,
            "return_7d": None
        }
        
        try:
            # Normalize event date (remove timezone and time info)
            if isinstance(event_date, pd.Timestamp):
                event_date_normalized = event_date.tz_localize(None).normalize()
            else:
                event_date_normalized = pd.Timestamp(event_date).tz_localize(None).normalize()
            
            # Normalize price_data index (remove timezone)
            price_index = price_data.index.tz_localize(None).normalize()
            
            # Find the event date in price data
            if event_date_normalized not in price_index:
                # Find nearest trading day
                future_dates = price_index[price_index >= event_date_normalized]
                if len(future_dates) == 0:
                    return returns
                event_date_normalized = future_dates[0]
            
            # Get event price
            event_idx = price_index.get_loc(event_date_normalized)
            event_price = price_data['Close'].iloc[event_idx]
            
            # Compute returns
            for days, key in [(1, 'return_1d'), (3, 'return_3d'), (7, 'return_7d')]:
                future_idx = event_idx + days
                
                if future_idx < len(price_data):
                    future_price = price_data['Close'].iloc[future_idx]
                    returns[key] = (future_price - event_price) / event_price
        
        except Exception as e:
            print(f"Error computing returns for {event_date}: {e}")
        
        return returns
    
    def compute_aggregated_metrics(
        self,
        events_with_returns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute aggregated metrics from events with returns.
        
        Args:
            events_with_returns: List of events with computed returns
        
        Returns:
            Dict with avg_return, winrate, count for positive/negative
        """
        positive_events = [e for e in events_with_returns if e['sentiment_label'] == 'POSITIVE']
        negative_events = [e for e in events_with_returns if e['sentiment_label'] == 'NEGATIVE']
        
        def calc_metrics(events: List[Dict], horizon: str) -> Dict[str, float]:
            """Calculate metrics for a specific horizon."""
            returns = [e['returns'][horizon] for e in events if e['returns'][horizon] is not None]
            
            if not returns:
                return {
                    'avg_return': 0.0,
                    'winrate': 0.0,
                    'count': 0
                }
            
            return {
                'avg_return': np.mean(returns),
                'winrate': sum(1 for r in returns if r > 0) / len(returns),
                'count': len(returns)
            }
        
        metrics = {
            'positive': {
                '1d': calc_metrics(positive_events, 'return_1d'),
                '3d': calc_metrics(positive_events, 'return_3d'),
                '7d': calc_metrics(positive_events, 'return_7d'),
                'total_count': len(positive_events)
            },
            'negative': {
                '1d': calc_metrics(negative_events, 'return_1d'),
                '3d': calc_metrics(negative_events, 'return_3d'),
                '7d': calc_metrics(negative_events, 'return_7d'),
                'total_count': len(negative_events)
            },
            'total_events': len(events_with_returns)
        }
        
        return metrics
    
    async def run_backtest(
        self,
        symbol: str,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run complete backtest for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            events: List of sentiment events with timestamp, sentiment_label, sentiment_score
        
        Returns:
            Dict with summary metrics and per-event results
        """
        if len(events) < 3:
            return {
                "status": "insufficient_data",
                "message": f"Only {len(events)} events found. Minimum 3 required for backtest.",
                "symbol": symbol,
                "event_count": len(events)
            }
        
        # Determine date range
        event_dates = [e['timestamp'] for e in events]
        start_date = min(event_dates) - timedelta(days=7)
        end_date = max(event_dates) + timedelta(days=14)
        
        # Download price data (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()
        price_data = await loop.run_in_executor(
            None,
            self.download_price_data,
            symbol,
            start_date,
            end_date
        )
        
        if price_data is None or price_data.empty:
            return {
                "status": "error",
                "message": f"Failed to download price data for {symbol}",
                "symbol": symbol,
                "event_count": len(events)
            }
        
        # Compute returns for each event
        events_with_returns = []
        for event in events:
            returns = self.compute_forward_returns(price_data, event['timestamp'])
            
            events_with_returns.append({
                **event,
                'returns': returns
            })
        
        # Compute aggregated metrics
        metrics = self.compute_aggregated_metrics(events_with_returns)
        
        return {
            "status": "success",
            "symbol": symbol,
            "backtest_date": datetime.now().isoformat(),
            "price_data_range": {
                "start": price_data.index[0].isoformat(),
                "end": price_data.index[-1].isoformat(),
                "trading_days": len(price_data)
            },
            "summary": metrics,
            "events": events_with_returns
        }


# Global singleton instance
impact_model = PriceImpactModel()
