"""
Test stats overview API endpoint.

Verifies the /stats/overview endpoint returns correct JSON structure
with all required fields for dashboard analytics.
"""
import requests
import pytest


def test_stats_overview_api(base_url: str):
    """Test that stats overview API returns valid JSON with required fields."""
    res = requests.get(f"{base_url}/stats/overview")
    assert res.status_code == 200
    
    data = res.json()
    assert "total_articles" in data
    assert "unique_clusters" in data
    assert "sentiment" in data
    assert "updated_at" in data


def test_stats_overview_sentiment_structure(base_url: str):
    """Test that sentiment data has correct structure."""
    res = requests.get(f"{base_url}/stats/overview")
    assert res.status_code == 200
    
    data = res.json()
    sentiment = data.get("sentiment", {})
    
    # Check sentiment categories
    assert "positive" in sentiment
    assert "negative" in sentiment
    assert "neutral" in sentiment


def test_stats_overview_impact_model(base_url: str):
    """Test that impact_model field is present in stats."""
    res = requests.get(f"{base_url}/stats/overview")
    assert res.status_code == 200
    
    data = res.json()
    assert "impact_model" in data
    
    impact_model = data["impact_model"]
    assert "supported_symbols" in impact_model
    assert "symbol_count" in impact_model
    assert "last_run" in impact_model


def test_stats_overview_top_companies(base_url: str):
    """Test that top companies list is included."""
    res = requests.get(f"{base_url}/stats/overview")
    assert res.status_code == 200
    
    data = res.json()
    assert "top_companies" in data
    assert isinstance(data["top_companies"], list)
