"""
Pytest configuration for UI tests.
"""
import pytest
import os


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the FastAPI application."""
    return os.getenv("BASE_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="function")
def page(playwright):
    """Create a new browser page for each test."""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
    browser.close()
