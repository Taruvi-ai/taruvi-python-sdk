"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import MagicMock, AsyncMock

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def mock_config():
    """Mock TaruviConfig."""
    config = MagicMock()
    config.api_url = "https://api.example.com"
    config.api_key = "test_key"
    config.site_slug = "test-site"
    config.app_slug = "test-app"
    config.headers = {
        "Authorization": "Bearer test_key",
        "Content-Type": "application/json",
        "X-Site-Slug": "test-site"
    }
    return config


@pytest.fixture
def mock_async_http():
    """Mock async HTTP client."""
    http = MagicMock()
    http.get = AsyncMock()
    http.post = AsyncMock()
    http.put = AsyncMock()
    http.delete = AsyncMock()
    http.client = MagicMock()
    http.client.get = AsyncMock()
    http.client.post = AsyncMock()
    return http


@pytest.fixture
def mock_sync_http():
    """Mock sync HTTP client."""
    http = MagicMock()
    http.client = MagicMock()
    return http


@pytest.fixture
def mock_async_client(mock_config, mock_async_http):
    """Mock async Client."""
    client = MagicMock()
    client._config = mock_config
    client._http_client = mock_async_http
    return client


@pytest.fixture
def mock_sync_client(mock_config, mock_sync_http):
    """Mock sync Client."""
    client = MagicMock()
    client._config = mock_config
    client._http = mock_sync_http
    return client
