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
        "username": os.getenv("TARUVI_TEST_EMAIL", os.getenv("TARUVI_USERNAME")),
        "password": os.getenv("TARUVI_TEST_PASSWORD", os.getenv("TARUVI_PASSWORD")),
    }


@pytest.fixture(scope="session")
def fresh_jwt_token(test_config):
    """
    Generate a fresh JWT token by logging in to the backend.
    This ensures tests always use a valid, non-expired token.
    """
    import httpx
    
    username = test_config.get("username")
    password = test_config.get("password")
    
    if not username or not password:
        pytest.skip("Username/password not configured - cannot generate JWT token")
    
    # Login to get fresh token using allauth endpoint
    try:
        api_url = test_config['api_url'].rstrip('/')
        response = httpx.post(
            f"{api_url}/_allauth/app/v1/auth/login",
            json={"email": username, "password": password},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        # Response structure: {"meta": {"access_token": "..."}}
        token = data.get("meta", {}).get("access_token")
        if not token:
            pytest.skip("No access token in login response")
        return token
    except Exception as e:
        pytest.skip(f"Cannot generate JWT token: {str(e)}")


@pytest.fixture
def unauth_test_config(monkeypatch):
    """
    Test configuration without authentication.

    Enables test mode to disable .env file loading and clears auth environment variables.
    Use this fixture for tests that need unauthenticated clients.
    """
    # Enable test mode to disable .env file loading in TaruviConfig
    monkeypatch.setenv('TARUVI_TEST_MODE', 'true')

    # Clear auth environment variables
    monkeypatch.delenv('TARUVI_JWT', raising=False)
    monkeypatch.delenv('TARUVI_API_KEY', raising=False)
    monkeypatch.delenv('TARUVI_SESSION_TOKEN', raising=False)
    monkeypatch.delenv('TARUVI_USERNAME', raising=False)
    monkeypatch.delenv('TARUVI_PASSWORD', raising=False)

    return {
        "api_url": os.getenv("TARUVI_API_URL", "http://localhost:8000"),
        "app_slug": os.getenv("TARUVI_TEST_APP_SLUG", "test-app"),
        "api_key": None,
        "username": None,
        "password": None,
        "jwt": None,
    }


# ============================================================================
# Real Client Fixtures (NO MOCKS)
# ============================================================================

@pytest.fixture
async def async_client(test_config, fresh_jwt_token):
    """
    Real async Taruvi client for integration tests.
    Makes ACTUAL API calls to the backend.

    Uses fresh JWT token generated at test session start.
    """
    from taruvi import Client

    # Create base client
    base_client = Client(
        api_url=test_config["api_url"],
        app_slug=test_config["app_slug"],
        mode="async"
    )

    # Authenticate with fresh JWT token
    client = base_client.auth.signInWithToken(
        token=fresh_jwt_token,
        token_type='jwt'
    )

    yield client

    # Cleanup
    await client._http_client.close()


@pytest.fixture
def sync_client(test_config, fresh_jwt_token):
    """
    Real sync Taruvi client for integration tests.
    Makes ACTUAL API calls to the backend.

    Uses fresh JWT token generated at test session start.
    """
    from taruvi import Client

    # Create base client
    base_client = Client(
        api_url=test_config["api_url"],
        app_slug=test_config["app_slug"],
        mode="sync"
    )

    # Authenticate with fresh JWT token
    client = base_client.auth.signInWithToken(
        token=fresh_jwt_token,
        token_type='jwt'
    )

    yield client

    # Cleanup
    client._http_client.close()


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


@pytest.fixture
async def async_analytics_module(async_client):
    """
    Real Analytics module for async integration tests.
    All operations hit the actual backend.
    """
    return async_client.analytics


@pytest.fixture
def sync_analytics_module(sync_client):
    """
    Real Analytics module for sync integration tests.
    All operations hit the actual backend.
    """
    return sync_client.analytics


# Auth module is accessed via client.auth - no separate fixtures needed


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
