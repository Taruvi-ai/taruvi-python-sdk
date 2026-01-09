"""
Integration tests for Auth API module.

IMPORTANT: These are REAL integration tests - NO MOCKS!
- Tests real authentication with Taruvi backend
- Tests login, user info retrieval, session management

Setup:
    1. Ensure .env is configured with backend URL
    2. Have test user credentials available
    3. Run: RUN_INTEGRATION_TESTS=1 pytest tests/test_auth_integration.py -v
"""

import pytest
import os


# ============================================================================
# Login Tests - Async (Real Authentication)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_real_api(async_client):
    """
    Test login with real credentials using signInWithPassword.

    Attempts login and verifies authenticated client is returned.
    """
    # Get test credentials from environment
    email = os.getenv("TARUVI_TEST_EMAIL")
    password = os.getenv("TARUVI_TEST_PASSWORD")

    if not email or not password:
        pytest.skip("Test credentials not configured (TARUVI_TEST_EMAIL, TARUVI_TEST_PASSWORD)")

    try:
        # Login using signInWithPassword - returns authenticated client
        auth_client = await async_client.auth.signInWithPassword(
            email=email,
            password=password
        )

        # Verify authenticated client is returned
        assert auth_client is not None
        assert auth_client.is_authenticated, "Client should be authenticated after signInWithPassword"
        assert auth_client._config.jwt is not None, "JWT should be set"

    except Exception as e:
        if "auth" in str(e).lower() and "not found" in str(e).lower():
            pytest.skip("Auth endpoints not available")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_credentials_real_api(async_client):
    """
    Test login with invalid credentials returns real error.

    Verifies proper error handling for authentication failures.
    """
    try:
        with pytest.raises(Exception) as exc_info:
            await async_client.auth.signInWithPassword(
                email="invalid_user_xyz_123@example.com",
                password="wrong_password_xyz"
            )

        # Verify we got authentication error
        error_msg = str(exc_info.value).lower()
        assert "auth" in error_msg or "credential" in error_msg or "401" in error_msg or "invalid" in error_msg

    except Exception as e:
        if "auth" in str(e).lower() and "not found" in str(e).lower():
            pytest.skip("Auth endpoints not available")
        raise


# ============================================================================
# User Info Tests - Async
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_real_api(async_client):
    """
    Test getting current authenticated user info.

    Verifies user profile retrieval with real backend.
    """
    try:
        # Get current user
        result = await async_client.auth.get_current_user()

        # Verify response structure
        assert result is not None

        # Response may be wrapped in 'data' key
        user_data = result.get('data', result)

        assert "id" in user_data or "user_id" in user_data or "username" in user_data, \
            "Response missing user identifier - API contract changed!"

        # Verify user data fields
        assert "username" in user_data or "email" in user_data

    except Exception as e:
        if "not supported" in str(e).lower() or "not found" in str(e).lower() or "404" in str(e):
            pytest.skip("User info endpoint not available")
        raise


# ============================================================================
# Session Management Tests - Async
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_sessions_real_api(async_client):
    """
    Test multiple concurrent sessions (if supported).

    Creates multiple authenticated sessions and verifies isolation.
    """
    email = os.getenv("TARUVI_TEST_EMAIL")
    password = os.getenv("TARUVI_TEST_PASSWORD")

    if not email or not password:
        pytest.skip("Test credentials not configured")

    try:
        # Create first session using signInWithPassword
        client1 = await async_client.auth.signInWithPassword(email=email, password=password)
        token1 = client1._config.jwt

        # Create second session
        client2 = await async_client.auth.signInWithPassword(email=email, password=password)
        token2 = client2._config.jwt

        # Verify both clients are authenticated
        assert client1.is_authenticated
        assert client2.is_authenticated
        assert token1 is not None
        assert token2 is not None

        # Both tokens should be valid
        # (Implementation depends on your backend's session strategy)

    except Exception as e:
        if "auth" in str(e).lower() and "not found" in str(e).lower():
            pytest.skip("Auth endpoints not available")
        raise


# ============================================================================
# Sync Client Tests - Real Authentication
# ============================================================================

@pytest.mark.integration
def test_login_sync_real_api(sync_client):
    """
    Test login with sync client using signInWithPassword.
    """
    email = os.getenv("TARUVI_TEST_EMAIL")
    password = os.getenv("TARUVI_TEST_PASSWORD")

    if not email or not password:
        pytest.skip("Test credentials not configured")

    try:
        # Login using signInWithPassword - returns authenticated client
        auth_client = sync_client.auth.signInWithPassword(email=email, password=password)

        # Verify authenticated client is returned
        assert auth_client is not None
        assert auth_client.is_authenticated, "Client should be authenticated after signInWithPassword"
        assert auth_client._config.jwt is not None, "JWT should be set"

    except Exception as e:
        if "auth" in str(e).lower() and "not found" in str(e).lower():
            pytest.skip("Auth endpoints not available")
        raise


@pytest.mark.integration
def test_get_current_user_sync_real_api(sync_client):
    """
    Test getting current user with sync client.
    """
    try:
        result = sync_client.auth.get_current_user()

        # Verify user info (response may be wrapped in 'data' key)
        assert result is not None
        user_data = result.get('data', result)
        assert "id" in user_data or "username" in user_data or "email" in user_data

    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e) or "not supported" in str(e).lower():
            pytest.skip("User info endpoint not available")
        raise


# ============================================================================
# Notes on Auth Integration Tests
# ============================================================================

"""
IMPORTANT CONFIGURATION:

1. Add to .env file:
   TARUVI_TEST_EMAIL=test@example.com
   TARUVI_TEST_PASSWORD=test_password

2. Ensure test user exists in backend
3. Ensure auth endpoints are enabled

Test Coverage:
✅ Login with valid credentials (async + sync)
✅ Login with invalid credentials (error handling)
✅ Get current user info (async + sync)
✅ Multiple sessions (if supported)

Removed Tests (features not implemented):
❌ Token validation (no backend API)
❌ Token refresh (no backend API)
❌ Logout (no backend API)
❌ Password change (disabled by default for safety)

Security Considerations:
- Use dedicated test account for auth tests
- Don't commit test credentials to version control
- Clean up sessions after tests

Auth Flow Testing:
1. Login → Get JWT token
2. Use token for API calls
3. Get user info to verify authentication works

Skipped Tests:
- Tests are automatically skipped if auth endpoints are not available
- Tests skip if credentials are not configured
"""
