"""
Helper functions for analysis module.

Provides database query helpers for sentiment events and stock data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from database.db import get_session
from database.schema import Sentiment, Article, Entity
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
import json


async def get_sentiment_events(
    symbol: str,
    min_score: float = 0.7,
    days_back: int = 180
) -> List[Dict[str, Any]]:
    """
    Retrieve sentiment events from database for a given stock symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'HDFCBANK', 'RELIANCE')
        min_score: Minimum sentiment score threshold (0.0 to 1.0)
        days_back: How many days back to look
    
    Returns:
        List of sentiment events with timestamp, label, score, article_id
    """
    events = []
    
    try:
        session = await get_session()
        try:
            # Calculate date threshold
            date_threshold = datetime.now() - timedelta(days=days_back)
            
            # Query: Find articles with entities matching the symbol
            # and join with sentiment data
            query = (
                select(Sentiment, Article, Entity)
                .join(Article, Sentiment.article_id == Article.id)
                .join(Entity, Entity.article_id == Article.id)
                .where(
                    and_(
                        Article.published_at >= date_threshold,
                        Sentiment.score >= min_score
                    )
                )
                .order_by(Article.published_at.desc())
            )
            
            result = await session.execute(query)
            rows = result.all()
            
            # Process results
            seen_article_ids = set()
            
            for sentiment, article, entity in rows:
                # Parse entity data
                try:
                    entity_data = json.loads(entity.entity_data) if isinstance(entity.entity_data, str) else entity.entity_data
                except:
                    entity_data = {}
                
                # Check if symbol is in impacted stocks
                impacted_stocks = entity_data.get('impacted_stocks', [])
                
                symbol_match = False
                for stock in impacted_stocks:
                    if isinstance(stock, dict) and stock.get('symbol') == symbol:
                        symbol_match = True
                        break
                    elif isinstance(stock, str) and stock == symbol:
                        symbol_match = True
                        break
                
                if symbol_match and article.id not in seen_article_ids:
                    seen_article_ids.add(article.id)
                    
                    events.append({
                        'article_id': article.id,
                        'timestamp': article.published_at,
                        'sentiment_label': sentiment.label.upper(),
                        'sentiment_score': float(sentiment.score),
                        'headline': article.title or article.text[:100]
                    })
    
        finally:
            await session.close()
    except Exception as e:
        print(f"Error retrieving sentiment events for {symbol}: {e}")
    
    return events


async def get_supported_symbols(limit: int = 50) -> List[str]:
    """
    Get list of stock symbols that have sentiment data.
    
    Args:
        limit: Maximum number of symbols to return
    
    Returns:
        List of stock symbols
    """
    symbols = []
    
    try:
        session = await get_session()
        try:
            # Query entities to find all unique stock symbols
            query = select(Entity.entity_data).limit(1000)
            result = await session.execute(query)
            rows = result.scalars().all()
            
            symbol_set = set()
            
            for entity_data in rows:
                try:
                    data = json.loads(entity_data) if isinstance(entity_data, str) else entity_data
                    impacted_stocks = data.get('impacted_stocks', [])
                    
                    for stock in impacted_stocks:
                        if isinstance(stock, dict):
                            sym = stock.get('symbol')
                            if sym:
                                symbol_set.add(sym)
                        elif isinstance(stock, str):
                            symbol_set.add(stock)
                
                except:
                    continue
                
                if len(symbol_set) >= limit:
                    break
            
            symbols = sorted(list(symbol_set))[:limit]
        finally:
            await session.close()
    
    except Exception as e:
        print(f"Error retrieving supported symbols: {e}")
    
    return symbols
