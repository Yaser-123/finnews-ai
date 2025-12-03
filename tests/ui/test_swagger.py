"""
Test Swagger UI and API documentation endpoints.

Verifies that Swagger UI loads correctly and all required API endpoints are visible.
"""
import pytest
from playwright.sync_api import Page, expect


def test_swagger_ui_loads(page: Page, base_url: str):
    """Test that Swagger UI page loads successfully."""
    page.goto(f"{base_url}/docs")
    page.wait_for_load_state("networkidle")
    
    # Check for FastAPI docs title or swagger-ui elements
    content = page.content()
    assert "swagger" in content.lower() or "docs" in page.title().lower()


def test_swagger_endpoints_visible(page: Page, base_url: str):
    """Test that required API endpoints appear in Swagger UI."""
    page.goto(f"{base_url}/docs")
    page.wait_for_load_state("networkidle")
    
    # Check that OpenAPI endpoints are present in page content
    content = page.content()
    assert "/stats/overview" in content
    assert "/pipeline/query" in content


def test_swagger_interactive_docs(page: Page, base_url: str):
    """Test that Swagger interactive documentation is functional."""
    page.goto(f"{base_url}/docs")
    page.wait_for_load_state("networkidle")
    
    # Verify OpenAPI spec is loaded
    content = page.content()
    assert "openapi" in content.lower() or "swagger" in content.lower()
