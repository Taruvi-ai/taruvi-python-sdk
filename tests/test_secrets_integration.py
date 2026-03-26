"""
Integration tests for Secrets API module.
"""

import os
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_secret_real_api(async_secrets_module):
    """Test getting a secret from real backend."""
    import httpx
    
    secret_key = "TEST_SECRET_ASYNC"
    secret_value = {"host": "localhost", "port": 3306, "database": "testdb", "username": "testuser", "password": "testpass123"}
    
    api_url = os.getenv("TARUVI_API_URL", "http://localhost:8000").rstrip('/')
    email = os.getenv("TARUVI_TEST_EMAIL", "admin@example.com")
    password = os.getenv("TARUVI_TEST_PASSWORD", "admin123")
    
    login_resp = httpx.post(f"{api_url}/_allauth/app/v1/auth/login", json={"email": email, "password": password})
    if login_resp.status_code != 200:
        pytest.skip(f"Login failed: {login_resp.status_code}")
    
    token = login_resp.json()['meta']['access_token']
    
    try:
        create_resp = httpx.post(
            f"{api_url}/api/secrets/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"key": secret_key, "value": secret_value, "secret_type": "analytics-mysql"}
        )
        
        if create_resp.status_code not in [200, 201]:
            pytest.skip(f"Cannot create secret: {create_resp.status_code}")
        
        result = await async_secrets_module.get(secret_key)
        assert result is not None
        assert "value" in result
        assert result["value"] == secret_value

    except Exception as e:
        if "not found" in str(e).lower():
            pytest.skip(f"Skipping: {str(e)}")
        raise
    finally:
        try:
            httpx.delete(f"{api_url}/api/secrets/{secret_key}/", headers={"Authorization": f"Bearer {token}"})
        except:
            pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_secrets_real_api(async_secrets_module):
    """Test listing secrets."""
    try:
        # Create multiple secrets
        for i in range(3):
            secret_key = f"LIST_TEST_{unique_id}_{i}"
            await async_secrets_module.create(
                key=secret_key,
                value=f"list_value_{i}"
            )
            secret_keys.append(secret_key)

        # List secrets
        result = await async_secrets_module.list_secrets()

        # Verify structure (list_secrets returns full response with data/total)
        assert result is not None
        assert "data" in result, "Response missing 'data' field - API contract changed!"

        # Get the list of secrets
        secrets_list = result["data"]

        # Verify we have secrets
        assert len(secrets_list) > 0

        # Verify our created secrets are in the list
        secret_keys_in_list = [s.get("key") or s.get("name") for s in secrets_list]
        for secret_key in secret_keys:
            assert secret_key in secret_keys_in_list, \
                f"Created secret {secret_key} not found in list!"

    except Exception as e:
        if "permission" in str(e).lower():
            pytest.skip(f"Skipping: {str(e)}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_with_filters_real_api(async_secrets_module):
    """Test listing secrets with filters."""
    try:
        result = await async_secrets_module.list(search="TEST")
        assert result is not None
    except Exception as e:
        if "permission" in str(e).lower():
            pytest.skip(f"Skipping: {str(e)}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_get_secrets_real_api(async_secrets_module):
    """Test batch getting secrets."""
    try:
        result = await async_secrets_module.list(keys=["apitoken", "claude"])
        assert result is not None
    except Exception as e:
        if "not found" in str(e).lower():
            pytest.skip(f"Skipping: {str(e)}")
        raise


@pytest.mark.integration
def test_get_secret_sync_real_api(sync_secrets_module):
    """Test getting secret with sync client."""
    import httpx
    
    secret_key = "TEST_SECRET_SYNC"
    secret_value = {"host": "localhost", "port": 3306, "database": "testdb_sync", "username": "testuser", "password": "testpass456"}
    
    api_url = os.getenv("TARUVI_API_URL", "http://localhost:8000").rstrip('/')
    email = os.getenv("TARUVI_TEST_EMAIL", "admin@example.com")
    password = os.getenv("TARUVI_TEST_PASSWORD", "admin123")
    
    login_resp = httpx.post(f"{api_url}/_allauth/app/v1/auth/login", json={"email": email, "password": password})
    if login_resp.status_code != 200:
        pytest.skip(f"Login failed")
    
    token = login_resp.json()['meta']['access_token']

    try:
        create_resp = httpx.post(
            f"{api_url}/api/secrets/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"key": secret_key, "value": secret_value, "secret_type": "analytics-mysql"}
        )
        
        if create_resp.status_code not in [200, 201]:
            pytest.skip(f"Cannot create secret")
        
        result = sync_secrets_module.get(secret_key)
        assert result is not None
        assert "value" in result
        assert result["value"] == secret_value

    except Exception as e:
        if "not found" in str(e).lower():
            pytest.skip(f"Skipping: {str(e)}")
        raise
    finally:
        try:
            httpx.delete(f"{api_url}/api/secrets/{secret_key}/", headers={"Authorization": f"Bearer {token}"})
        except:
            pass


@pytest.mark.integration
def test_list_secrets_sync_real_api(sync_secrets_module):
    """Test listing secrets with sync client."""
    try:
        result = sync_secrets_module.list()
        assert result is not None
    except Exception as e:
        if "permission" in str(e).lower():
            pytest.skip(f"Skipping: {str(e)}")
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_nonexistent_secret_real_api(async_secrets_module):
    """Test getting non-existent secret."""
    try:
        with pytest.raises(Exception):
            await async_secrets_module.get("NONEXISTENT_SECRET_KEY_12345")
    except Exception as e:
        if "permission" in str(e).lower():
            pytest.skip(f"Skipping: {str(e)}")
        raise
