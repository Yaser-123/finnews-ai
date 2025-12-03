"""
Analysis API Routes

Endpoints for price impact analysis and backtesting.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from analysis.impact_model import impact_model
from analysis.helpers import get_sentiment_events, get_supported_symbols
from analysis.visualizations import generate_impact_chart

router = APIRouter()


class PriceImpactResponse(BaseModel):
    """Price impact backtest response model."""
    status: str = Field(..., description="Status: success, insufficient_data, or error")
    symbol: str = Field(..., description="Stock ticker symbol")
    message: Optional[str] = Field(None, description="Error or info message")
    event_count: int = Field(..., description="Number of sentiment events analyzed")
    backtest_date: Optional[str] = Field(None, description="Timestamp of backtest")
    price_data_range: Optional[Dict[str, Any]] = Field(None, description="Price data date range")
    summary: Optional[Dict[str, Any]] = Field(None, description="Aggregated metrics")
    events: Optional[List[Dict[str, Any]]] = Field(None, description="Per-event results")
    chart_path: Optional[str] = Field(None, description="Path to generated chart")


@router.get(
    "/price-impact/{symbol}",
    response_model=PriceImpactResponse,
    summary="Run Price Impact Backtest",
    description="Analyze historical price impact of sentiment events for a given stock symbol.",
    tags=["Analysis"]
)
async def get_price_impact(
    symbol: str = Path(..., description="Stock ticker symbol (e.g., HDFCBANK, RELIANCE)"),
    min_score: float = Query(0.7, ge=0.0, le=1.0, description="Minimum sentiment score threshold"),
    days_back: int = Query(180, ge=30, le=730, description="Days to look back for events"),
    generate_chart: bool = Query(False, description="Generate visualization chart")
) -> PriceImpactResponse:
    """
    Run price impact backtest for a stock symbol.
    
    **Process:**
    1. Retrieve sentiment events from database
    2. Download historical price data via yfinance
    3. Compute forward returns (1d, 3d, 7d) for each event
    4. Aggregate metrics by sentiment label
    5. Optionally generate visualization chart
    
    **Returns:**
    - Summary metrics (avg_return, winrate, count) for positive/negative sentiment
    - Per-event results with forward returns
    - Chart path if generate_chart=true
    
    **Example Response:**
    ```json
    {
      "status": "success",
      "symbol": "HDFCBANK",
      "event_count": 15,
      "summary": {
        "positive": {
          "1d": {"avg_return": 0.0234, "winrate": 0.67, "count": 9},
          "3d": {"avg_return": 0.0456, "winrate": 0.78, "count": 9},
          "7d": {"avg_return": 0.0789, "winrate": 0.89, "count": 9}
        },
        "negative": {
          "1d": {"avg_return": -0.0156, "winrate": 0.33, "count": 6},
          "3d": {"avg_return": -0.0234, "winrate": 0.50, "count": 6},
          "7d": {"avg_return": -0.0312, "winrate": 0.50, "count": 6}
        }
      }
    }
    ```
    """
    try:
        # Retrieve sentiment events
        events = await get_sentiment_events(symbol, min_score, days_back)
        
        if not events:
            return PriceImpactResponse(
                status="insufficient_data",
                symbol=symbol,
                message=f"No sentiment events found for {symbol} in the last {days_back} days",
                event_count=0
            )
        
        # Run backtest
        result = await impact_model.run_backtest(symbol, events)
        
        # Generate chart if requested
        chart_path = None
        if generate_chart and result.get('status') == 'success':
            chart_path = await generate_impact_chart(symbol, result)
        
        return PriceImpactResponse(
            status=result.get('status', 'error'),
            symbol=result.get('symbol', symbol),
            message=result.get('message'),
            event_count=result.get('event_count', len(events)),
            backtest_date=result.get('backtest_date'),
            price_data_range=result.get('price_data_range'),
            summary=result.get('summary'),
            events=result.get('events'),
            chart_path=chart_path
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running price impact backtest: {str(e)}"
        )


@router.get(
    "/supported-symbols",
    summary="Get Supported Stock Symbols",
    description="Returns list of stock symbols that have sentiment data available for analysis.",
    tags=["Analysis"]
)
async def get_symbols() -> Dict[str, Any]:
    """
    Get list of stock symbols with available sentiment data.
    
    **Returns:**
    - List of supported symbols
    - Count of unique symbols
    
    **Example Response:**
    ```json
    {
      "symbols": ["HDFCBANK", "RELIANCE", "TCS", "INFY", "ICICIBANK"],
      "count": 5,
      "updated_at": "2025-12-03T10:30:00"
    }
    ```
    """
    try:
        symbols = await get_supported_symbols(limit=100)
        
        return {
            "symbols": symbols,
            "count": len(symbols),
            "updated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving supported symbols: {str(e)}"
        )
