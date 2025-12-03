"""
Test WebSocket alerts endpoint (optional).

Verifies that WebSocket connection for real-time alerts works correctly.
Only runs if WebSocket server is available.
"""
import asyncio
import pytest
import websockets
import json

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.asyncio(loop_scope="function")
async def test_websocket_alerts_connection(base_url: str):
    """Test WebSocket connection to alerts endpoint."""
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{ws_url}/ws/alerts"
    
    try:
        async with websockets.connect(ws_url) as ws:
            # Try to receive a message within timeout
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            
            # Verify message structure
            assert isinstance(data, dict)
            # Common alert fields
            if "type" in data:
                assert data["type"] in ["alert", "notification", "update"]
    
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        pytest.skip("WebSocket server not available or no messages sent")


@pytest.mark.asyncio(loop_scope="function")
async def test_websocket_alerts_message_format(base_url: str):
    """Test that WebSocket alert messages have expected format."""
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{ws_url}/ws/alerts"
    
    try:
        async with websockets.connect(ws_url) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            
            # Check for common alert fields
            assert isinstance(data, dict)
            # At least one of these fields should be present
            has_expected_field = any(
                field in data 
                for field in ["type", "article_id", "message", "timestamp", "severity"]
            )
            assert has_expected_field
    
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        pytest.skip("WebSocket server not available")
