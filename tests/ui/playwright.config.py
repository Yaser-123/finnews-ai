"""
Playwright configuration for UI tests.

Defines base URL and pytest configuration options.
"""
import os


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--base-url",
        action="store",
        default=BASE_URL,
        help="Base URL for the FastAPI application"
    )


def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async test"
    )
