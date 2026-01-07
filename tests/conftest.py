"""Pytest configuration and shared fixtures for integration tests."""

import os
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


# ============================================================================
# Environment Configuration
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Load test configuration from environment variables."""
    return {
        "api_url": os.getenv("TARUVI_API_URL", "http://localhost:8000"),
        "app_slug": os.getenv("TARUVI_TEST_APP_SLUG", "test-app"),
        "api_key": os.getenv("TARUVI_API_KEY"),
        "username": os.getenv("TARUVI_USERNAME"),
        "password": os.getenv("TARUVI_PASSWORD"),
        "jwt": os.getenv("TARUVI_JWT"),
    }


# ============================================================================
# Real Client Fixtures (NO MOCKS)
# ============================================================================

@pytest.fixture
async def async_client(test_config):
    """
    Real async Taruvi client for integration tests.
    Makes ACTUAL API calls to the backend.
    """
    from taruvi import Client

    # Create client with environment configuration
    client = Client(
        api_url=test_config["api_url"],
        app_slug=test_config["app_slug"],
        api_key=test_config["api_key"],
        username=test_config["username"],
        password=test_config["password"],
        jwt=test_config["jwt"],
        mode="async"
    )

    yield client

    # Cleanup: Close HTTP connections
    await client._http_client.close()


@pytest.fixture
def sync_client(test_config):
    """
    Real sync Taruvi client for integration tests.
    Makes ACTUAL API calls to the backend.
    """
    from taruvi import Client

    # Create client with environment configuration
    client = Client(
        api_url=test_config["api_url"],
        app_slug=test_config["app_slug"],
        api_key=test_config["api_key"],
        username=test_config["username"],
        password=test_config["password"],
        jwt=test_config["jwt"],
        mode="sync"
    )

    yield client

    # Cleanup: Close HTTP connections
    client._http.close()


# ============================================================================
# Module-Specific Fixtures
# ============================================================================

@pytest.fixture
async def async_functions_module(async_client):
    """
    Real Functions module for async integration tests.
    All operations hit the actual backend.
    """
    return async_client.functions


@pytest.fixture
def sync_functions_module(sync_client):
    """
    Real Functions module for sync integration tests.
    All operations hit the actual backend.
    """
    return sync_client.functions


@pytest.fixture
async def async_database_module(async_client):
    """
    Real Database module for async integration tests.
    All operations hit the actual backend.
    """
    return async_client.database


@pytest.fixture
def sync_database_module(sync_client):
    """
    Real Database module for sync integration tests.
    All operations hit the actual backend.
    """
    return sync_client.database


@pytest.fixture
async def async_storage_module(async_client):
    """
    Real Storage module for async integration tests.
    All operations hit the actual backend.
    """
    return async_client.storage


@pytest.fixture
def sync_storage_module(sync_client):
    """
    Real Storage module for sync integration tests.
    All operations hit the actual backend.
    """
    return sync_client.storage


@pytest.fixture
async def async_secrets_module(async_client):
    """
    Real Secrets module for async integration tests.
    All operations hit the actual backend.
    """
    return async_client.secrets


@pytest.fixture
def sync_secrets_module(sync_client):
    """
    Real Secrets module for sync integration tests.
    All operations hit the actual backend.
    """
    return sync_client.secrets


# ============================================================================
# Test Data Helpers
# ============================================================================

@pytest.fixture
def generate_unique_id():
    """Generate unique identifiers for test data to avoid conflicts."""
    from uuid import uuid4
    return lambda: uuid4().hex[:8]


@pytest.fixture
def test_function_name():
    """
    Provide test function name from environment.
    Falls back to default if not configured.
    """
    return os.getenv("TARUVI_TEST_FUNCTION_NAME", "test-function")


# ============================================================================
# Skip Integration Tests if Not Configured
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (requires real backend)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if RUN_INTEGRATION_TESTS is not set."""
    if not os.getenv("RUN_INTEGRATION_TESTS"):
        skip_integration = pytest.mark.skip(
            reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable."
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
