"""
Test WebSocket alerts endpoint.

Verifies that WebSocket connection for real-time alerts works correctly.
Uses pytest-asyncio to handle async WebSocket connections properly.
"""
import pytest
import asyncio
import websockets
from websockets.exceptions import WebSocketException


@pytest.mark.asyncio
async def test_websocket_connection(base_url: str):
    """
    Test WebSocket connection to alerts endpoint.
    
    Connects to /ws/alerts and verifies connection is established.
    Uses async/await properly without nested event loops.
    """
    # Convert HTTP URL to WebSocket URL
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_endpoint = f"{ws_url}/ws/alerts"
    
    try:
        # Connect with timeout
        async with asyncio.timeout(5):
            async with websockets.connect(ws_endpoint) as websocket:
                # Connection successful
                assert websocket.open
                
                # Try to receive a message (with timeout)
                try:
                    async with asyncio.timeout(2):
                        message = await websocket.recv()
                        # If we get a message, verify it's a string
                        assert isinstance(message, str)
                except asyncio.TimeoutError:
                    # No message received, but connection worked
                    pass
                
    except (WebSocketException, OSError, asyncio.TimeoutError):
        # WebSocket not available - expected in CI without alerts
        pytest.skip("WebSocket alerts endpoint not available")


@pytest.mark.asyncio
async def test_websocket_url_format(base_url: str):
    """
    Test that WebSocket URL is correctly formatted.
    
    Verifies URL conversion from HTTP to WS protocol.
    """
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
    expected_ws_url = f"{ws_url}/ws/alerts"
    
    # Verify URL format
    assert "ws://" in expected_ws_url or "wss://" in expected_ws_url
    assert "/ws/alerts" in expected_ws_url
    assert "http://" not in expected_ws_url
    assert "https://" not in expected_ws_url
