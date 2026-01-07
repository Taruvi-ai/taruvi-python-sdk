"""Test that all SDK modules and classes can be imported."""

import pytest


def test_import_main_client():
    """Test importing unified Client."""
    from taruvi import Client
    assert Client is not None
    assert callable(Client)


def test_import_auth_manager():
    """Test importing AuthManager (new in auth refactoring)."""
    from taruvi import AuthManager
    assert AuthManager is not None
    assert AuthManager.__name__ == 'AuthManager'


def test_import_not_authenticated_error():
    """Test importing NotAuthenticatedError exception."""
    from taruvi import NotAuthenticatedError
    from taruvi.exceptions import NotAuthenticatedError as DirectImport
    assert NotAuthenticatedError is not None
    assert NotAuthenticatedError is DirectImport


def test_syncclient_removed():
    """Test that SyncClient is no longer exported (breaking change in v0.2.0)."""
    with pytest.raises(ImportError):
        from taruvi import SyncClient  # noqa: F401


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


def test_no_import_errors():
    """Test that importing the package doesn't raise errors."""
    try:
        import taruvi
        assert True
    except ImportError as e:
        pytest.fail(f"Import error: {e}")
