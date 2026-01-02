"""Test that all SDK modules and classes can be imported."""

import pytest


def test_import_main_clients():
    """Test importing main client classes."""
    from taruvi import Client, SyncClient
    assert Client is not None
    assert SyncClient is not None


def test_import_all_async_modules():
    """Test importing all async module classes."""
    from taruvi.modules.auth import AuthModule
    from taruvi.modules.database import DatabaseModule, QueryBuilder
    from taruvi.modules.functions import FunctionsModule
    from taruvi.modules.storage import StorageModule
    from taruvi.modules.secrets import SecretsModule
    from taruvi.modules.policy import PolicyModule
    from taruvi.modules.app import AppModule
    from taruvi.modules.settings import SettingsModule

    assert AuthModule is not None
    assert DatabaseModule is not None
    assert QueryBuilder is not None
    assert FunctionsModule is not None
    assert StorageModule is not None
    assert SecretsModule is not None
    assert PolicyModule is not None
    assert AppModule is not None
    assert SettingsModule is not None


def test_import_all_sync_modules():
    """Test importing all sync module classes."""
    from taruvi.modules.auth import SyncAuthModule
    from taruvi.modules.database import SyncDatabaseModule, SyncQueryBuilder
    from taruvi.modules.functions import SyncFunctionsModule
    from taruvi.modules.storage import SyncStorageModule
    from taruvi.modules.secrets import SyncSecretsModule
    from taruvi.modules.policy import SyncPolicyModule
    from taruvi.modules.app import SyncAppModule
    from taruvi.modules.settings import SyncSettingsModule

    assert SyncAuthModule is not None
    assert SyncDatabaseModule is not None
    assert SyncQueryBuilder is not None
    assert SyncFunctionsModule is not None
    assert SyncStorageModule is not None
    assert SyncSecretsModule is not None
    assert SyncPolicyModule is not None
    assert SyncAppModule is not None
    assert SyncSettingsModule is not None


def test_import_all_models():
    """Test importing all model classes."""
    from taruvi.models.auth import TokenResponse, UserResponse, UserListResponse
    from taruvi.models.database import DatabaseRecord
    from taruvi.models.functions import FunctionResponse, FunctionExecutionResult
    from taruvi.models.storage import StorageObject, StorageListResponse
    from taruvi.models.secrets import Secret, SecretListResponse
    from taruvi.models.policy import PolicyCheckResponse, ResourceCheckRequest
    from taruvi.models.app import Role, RoleListResponse, UserApp
    from taruvi.models.settings import SiteSettings

    assert TokenResponse is not None
    assert UserResponse is not None
    assert DatabaseRecord is not None
    assert FunctionResponse is not None
    assert StorageObject is not None
    assert Secret is not None
    assert PolicyCheckResponse is not None
    assert Role is not None
    assert SiteSettings is not None


def test_no_import_errors():
    """Test that importing the package doesn't raise errors."""
    try:
        import taruvi
        assert True
    except ImportError as e:
        pytest.fail(f"Import error: {e}")
