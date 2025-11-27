"""
WebSocket API Module

Provides real-time alert broadcasting capabilities.
"""

from .alerts import alert_manager, AlertManager

__all__ = ["alert_manager", "AlertManager"]
