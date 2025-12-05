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


class RiskMonitorResponse(BaseModel):
    """Risk monitoring response model."""
    sector: str = Field(..., description="Sector being monitored")
    risk_level: str = Field(..., description="Overall risk level: low, medium, high, critical")
    negative_count: int = Field(..., description="Number of negative articles")
    avg_sentiment_score: float = Field(..., description="Average negative sentiment score")
    high_risk_companies: List[Dict[str, Any]] = Field(..., description="Companies with multiple negative mentions")
    recent_alerts: List[Dict[str, Any]] = Field(..., description="Recent negative news articles")
    updated_at: str = Field(..., description="Timestamp of analysis")


@router.get(
    "/risk-monitor",
    response_model=RiskMonitorResponse,
    summary="Monitor Sector Risk",
    description="Track negative sentiment and risk indicators for a specific sector.",
    tags=["Analysis"]
)
async def risk_monitor(
    sector: str = Query("Banking", description="Sector to monitor (e.g., Banking, Technology, Finance)"),
    days_back: int = Query(30, ge=1, le=180, description="Days to look back"),
    min_sentiment: float = Query(0.7, ge=0.5, le=1.0, description="Minimum negative sentiment score")
) -> RiskMonitorResponse:
    """
    Monitor risk indicators for a specific sector.
    
    **Process:**
    1. Find all negative sentiment articles for the sector
    2. Calculate risk metrics and scores
    3. Identify high-risk companies
    4. Return actionable risk alerts
    
    **Risk Levels:**
    - **low**: < 5 negative articles
    - **medium**: 5-15 negative articles
    - **high**: 16-30 negative articles
    - **critical**: > 30 negative articles
    
    **Example Usage:**
    ```
    GET /analysis/risk-monitor?sector=Banking&days_back=30
    ```
    """
    try:
        from database import db
        from sqlalchemy import text
        
        # Initialize database
        db.init_db()
        session = await db.get_session()
        
        # Query negative articles - since sectors array is often empty,
        # we search in the article text as fallback
        query = text(f"""
            SELECT 
                a.id,
                a.text,
                a.published_at,
                s.score as sentiment_score,
                e.companies,
                e.sectors
            FROM articles a
            JOIN sentiment s ON a.id = s.article_id
            JOIN entities e ON a.id = e.article_id
            WHERE s.label = 'negative'
              AND s.score >= :min_sentiment
              AND a.published_at >= NOW() - INTERVAL '{days_back} days'
              AND (
                  :sector = ANY(e.sectors) OR
                  a.text ILIKE '%' || :sector || '%'
              )
            ORDER BY s.score DESC, a.published_at DESC
            LIMIT 100
        """)
        
        result = await session.execute(
            query,
            {
                "min_sentiment": min_sentiment,
                "sector": sector
            }
        )
        rows = result.fetchall()
        
        # Process results
        negative_count = len(rows)
        
        if negative_count == 0:
            return RiskMonitorResponse(
                sector=sector,
                risk_level="low",
                negative_count=0,
                avg_sentiment_score=0.0,
                high_risk_companies=[],
                recent_alerts=[],
                updated_at=datetime.now().isoformat()
            )
        
        # Calculate average sentiment score
        avg_score = sum(row.sentiment_score for row in rows) / len(rows)
        
        # Count company mentions
        company_risks = {}
        for row in rows:
            if row.companies:
                for company in row.companies:
                    if company not in company_risks:
                        company_risks[company] = {
                            "company": company,
                            "negative_count": 0,
                            "avg_score": 0.0,
                            "scores": []
                        }
                    company_risks[company]["negative_count"] += 1
                    company_risks[company]["scores"].append(row.sentiment_score)
        
        # Calculate company risk scores and sort
        high_risk_companies = []
        for company, data in company_risks.items():
            data["avg_score"] = sum(data["scores"]) / len(data["scores"])
            data.pop("scores")  # Remove raw scores
            if data["negative_count"] >= 2:  # At least 2 negative mentions
                high_risk_companies.append(data)
        
        high_risk_companies.sort(key=lambda x: (x["negative_count"], x["avg_score"]), reverse=True)
        high_risk_companies = high_risk_companies[:10]  # Top 10
        
        # Recent alerts (top 20)
        recent_alerts = []
        for row in rows[:20]:
            recent_alerts.append({
                "article_id": row.id,
                "text": row.text[:200] + "..." if len(row.text) > 200 else row.text,
                "published_at": row.published_at.isoformat(),
                "sentiment_score": round(row.sentiment_score, 3),
                "companies": row.companies[:3] if row.companies else []
            })
        
        # Determine risk level
        if negative_count < 5:
            risk_level = "low"
        elif negative_count < 16:
            risk_level = "medium"
        elif negative_count < 31:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        return RiskMonitorResponse(
            sector=sector,
            risk_level=risk_level,
            negative_count=negative_count,
            avg_sentiment_score=round(avg_score, 3),
            high_risk_companies=high_risk_companies,
            recent_alerts=recent_alerts,
            updated_at=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error monitoring sector risk: {str(e)}"
        )
