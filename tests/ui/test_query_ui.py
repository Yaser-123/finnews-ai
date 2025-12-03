"""
Test query API endpoint for NLP agent.

Verifies that the /pipeline/query endpoint processes queries correctly
and returns expected JSON structure with entity matching and results.
"""
import requests
import pytest


def test_query_endpoint_basic(base_url: str):
    """Test basic query endpoint with simple query."""
    query = {"query": "HDFC Bank news"}
    res = requests.post(f"{base_url}/pipeline/query", json=query)
    assert res.status_code == 200
    
    data = res.json()
    assert "matched_entities" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_query_endpoint_with_entities(base_url: str):
    """Test query with entity extraction."""
    query = {"query": "RBI policy changes"}
    res = requests.post(f"{base_url}/pipeline/query", json=query)
    assert res.status_code == 200
    
    data = res.json()
    matched = data.get("matched_entities", {})
    
    # Check entity categories exist
    assert isinstance(matched, dict)
    assert "results" in data


def test_query_endpoint_result_structure(base_url: str):
    """Test that query results have proper structure."""
    query = {"query": "banking sector update"}
    res = requests.post(f"{base_url}/pipeline/query", json=query)
    assert res.status_code == 200
    
    data = res.json()
    results = data.get("results", [])
    
    if len(results) > 0:
        first_result = results[0]
        # Verify result has expected fields
        assert "id" in first_result or "article_id" in first_result
        assert "text" in first_result or "content" in first_result


def test_query_endpoint_empty_query(base_url: str):
    """Test handling of empty query."""
    query = {"query": ""}
    res = requests.post(f"{base_url}/pipeline/query", json=query)
    
    # Should either return 200 with empty results or 400/422
    assert res.status_code in [200, 400, 422]


def test_query_endpoint_invalid_json(base_url: str):
    """Test handling of invalid JSON payload."""
    res = requests.post(
        f"{base_url}/pipeline/query",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    # Should return validation error
    assert res.status_code in [400, 422]
