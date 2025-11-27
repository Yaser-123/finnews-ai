"""
WebSocket Alert Manager for Real-Time Trading Alerts

Manages WebSocket connections and broadcasts financial alerts
triggered by sentiment analysis, LLM summaries, and entity extraction.
"""

from fastapi import WebSocket
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages WebSocket connections and broadcasts real-time alerts.
    
    Alert Levels:
    - HIGH_RISK: Negative sentiment > 0.90
    - BULLISH: Positive sentiment > 0.90
    - REGULATORY_UPDATE: RBI/policy/inflation mentions in LLM summaries
    - EARNINGS_UPDATE: Profit/growth mentions in LLM summaries
    """
    
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.alert_history: List[Dict[str, Any]] = []  # Store recent alerts for dashboard
        self.max_history = 100  # Keep last 100 alerts
        logger.info("🔔 Alert Manager initialized")
    
    async def connect(self, ws: WebSocket):
        """Accept and register a new WebSocket connection."""
        await ws.accept()
        self.connections.append(ws)
        logger.info(f"✅ New WebSocket connection (total: {len(self.connections)})")
        
        # Send welcome message
        await ws.send_json({
            "type": "connection",
            "message": "Connected to FinNews AI Real-Time Alerts",
            "active_connections": len(self.connections)
        })
    
    def disconnect(self, ws: WebSocket):
        """Remove a WebSocket connection."""
        if ws in self.connections:
            self.connections.remove(ws)
            logger.info(f"❌ WebSocket disconnected (remaining: {len(self.connections)})")
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast JSON alert to all connected clients.
        
        Args:
            message: Alert dictionary with level, article_id, headline, etc.
        """
        if not self.connections:
            logger.debug("⚠️ No active connections to broadcast to")
            return
        
        disconnected = []
        
        for ws in self.connections:
            try:
                await ws.send_json(message)
                logger.debug(f"📤 Alert broadcast: {message.get('level')} - Article {message.get('article_id')}")
            except Exception as e:
                logger.warning(f"❌ Failed to send to connection: {str(e)}")
                disconnected.append(ws)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
    
    async def send_alert(
        self, 
        level: str, 
        article_id: int, 
        headline: str = None,
        text: str = None,
        sentiment: Dict[str, Any] = None,
        entities: Dict[str, List[str]] = None,
        summary: str = None
    ):
        """
        Helper method to send a formatted alert.
        
        Args:
            level: Alert level (HIGH_RISK, BULLISH, REGULATORY_UPDATE, EARNINGS_UPDATE, ALERT)
            article_id: ID of the article
            headline: Article headline (preferred)
            text: Article text (fallback if headline not provided)
            sentiment: Sentiment dict with label and score (optional)
            entities: Extracted entities (optional)
            summary: LLM-generated summary (optional)
        """
        from datetime import datetime
        
        # Use headline if provided, otherwise use text
        display_text = headline or text or "No headline"
        
        alert = {
            "level": level,
            "article_id": article_id,
            "headline": display_text[:120] + "..." if len(display_text) > 120 else display_text,
            "sentiment": sentiment.get("label") if sentiment else None,
            "timestamp": datetime.now().isoformat()
        }
        
        if entities:
            alert["entities"] = {
                "companies": entities.get("companies", [])[:3],
                "regulators": entities.get("regulators", [])[:2],
                "sectors": entities.get("sectors", [])[:2]
            }
        
        if summary:
            alert["summary"] = summary[:200] + "..." if len(summary) > 200 else summary
        
        # Store in history for dashboard
        self.alert_history.append(alert)
        
        # Keep only last N alerts
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        
        await self.broadcast(alert)
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent alerts for dashboard display.
        
        Args:
            limit: Maximum number of alerts to return
        
        Returns:
            List of recent alert dictionaries
        """
        return self.alert_history[-limit:][::-1]  # Most recent first


# Global singleton instance
alert_manager = AlertManager()
