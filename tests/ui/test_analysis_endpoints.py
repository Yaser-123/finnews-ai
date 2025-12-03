"""
Test price impact analysis endpoints.

Verifies the new analysis endpoints for historical sentiment-to-price backtesting.
"""
import requests
import pytest


def test_supported_symbols_endpoint(base_url: str):
    """Test that supported symbols endpoint returns valid response."""
    res = requests.get(f"{base_url}/analysis/supported-symbols")
    assert res.status_code == 200
    
    data = res.json()
    assert "symbols" in data
    assert "count" in data
    assert "updated_at" in data
    assert isinstance(data["symbols"], list)


def test_price_impact_endpoint_structure(base_url: str):
    """Test price impact endpoint with a sample symbol."""
    # Test with HDFCBANK as example
    res = requests.get(f"{base_url}/analysis/price-impact/HDFCBANK")
    assert res.status_code == 200
    
    data = res.json()
    assert "status" in data
    assert "symbol" in data
    assert "event_count" in data
    assert data["symbol"] == "HDFCBANK"


def test_price_impact_endpoint_with_params(base_url: str):
    """Test price impact endpoint with query parameters."""
    params = {
        "min_score": 0.8,
        "days_back": 90,
        "generate_chart": False
    }
    res = requests.get(
        f"{base_url}/analysis/price-impact/RELIANCE",
        params=params
    )
    assert res.status_code == 200
    
    data = res.json()
    assert "status" in data


def test_price_impact_invalid_symbol(base_url: str):
    """Test price impact endpoint with invalid symbol."""
    res = requests.get(f"{base_url}/analysis/price-impact/INVALID_XYZ_123")
    assert res.status_code == 200  # Should return 200 with insufficient_data status
    
    data = res.json()
    if data.get("status") == "insufficient_data":
        assert "message" in data
