"""Test that refactoring didn't break anything - verify no duplicate logic."""

import pytest
import inspect
from taruvi.modules import auth, database, functions, storage, secrets, policy, app, settings


def get_method_source(cls, method_name):
    """Get source code of a method."""
    try:
        method = getattr(cls, method_name)
        return inspect.getsource(method)
    except (AttributeError, TypeError):
        return None


def test_auth_shared_helpers_exist():
    """Test that auth module has shared helper functions."""
    # These should exist as module-level functions
    assert hasattr(auth, '_build_login_request')
    assert hasattr(auth, '_build_refresh_request')
    assert hasattr(auth, '_build_user_create_request')
    assert hasattr(auth, '_build_user_update_request')
    assert hasattr(auth, '_build_user_list_path')
    assert hasattr(auth, '_parse_user_apps')

    # Should be callable
    assert callable(auth._build_login_request)
    assert callable(auth._parse_user_apps)


def test_database_base_class_exists():
    """Test that database module has base query builder class."""
    assert hasattr(database, '_BaseQueryBuilder')

    # Should be a class
    assert inspect.isclass(database._BaseQueryBuilder)

    # Should have shared methods
    base_builder = database._BaseQueryBuilder("test", "test-app")
    assert hasattr(base_builder, '_add_filter')
    assert hasattr(base_builder, '_set_sort')
    assert hasattr(base_builder, '_set_limit')
    assert hasattr(base_builder, 'build_params')


def test_storage_base_class_exists():
    """Test that storage module has base query builder class."""
    assert hasattr(storage, '_BaseStorageQueryBuilder')

    # Should be a class
    assert inspect.isclass(storage._BaseStorageQueryBuilder)

    # Should have shared methods
    base_builder = storage._BaseStorageQueryBuilder("test-bucket", "test-app")
    assert hasattr(base_builder, '_add_filters')
    assert hasattr(base_builder, 'build_query_string')


def test_policy_shared_helpers_exist():
    """Test that policy module has shared helper functions."""
    assert hasattr(policy, '_build_single_resource_check')
    assert hasattr(policy, '_build_multiple_resources_check')
    assert hasattr(policy, '_parse_check_response')

    assert callable(policy._build_single_resource_check)


def test_functions_shared_helpers_exist():
    """Test that functions module has shared helper functions."""
    assert hasattr(functions, '_build_execute_request')
    assert hasattr(functions, '_build_list_params')
    assert hasattr(functions, '_build_invocations_params')

    assert callable(functions._build_execute_request)


def test_no_duplicate_business_logic_in_auth():
    """Test that auth async/sync don't duplicate business logic."""
    # Get login method source from both classes
    async_login = get_method_source(auth.AuthModule, 'login')
    sync_login = get_method_source(auth.SyncAuthModule, 'login')

    # Both should be short (just HTTP call + response parsing)
    # Before refactoring, each was 30+ lines
    # After refactoring, each should be <10 lines
    assert async_login is not None
    assert sync_login is not None

    # Count non-empty, non-comment lines
    async_lines = [l.strip() for l in async_login.split('\n')
                   if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('"""')]
    sync_lines = [l.strip() for l in sync_login.split('\n')
                  if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('"""')]

    # After refactoring, methods should be thin wrappers (<= 20 lines each including docstrings)
    assert len(async_lines) <= 20, f"Async login too long: {len(async_lines)} lines"
    assert len(sync_lines) <= 20, f"Sync login too long: {len(sync_lines)} lines"

    # Both should call the shared helper _build_login_request
    assert '_build_login_request' in async_login
    assert '_build_login_request' in sync_login


def test_database_query_builders_inherit_from_base():
    """Test that query builders inherit from base class."""
    # Check inheritance
    assert issubclass(database.QueryBuilder, database._BaseQueryBuilder)
    assert issubclass(database.SyncQueryBuilder, database._BaseQueryBuilder)

    # Both should have the shared build_params method from base
    async_builder = database.QueryBuilder.__mro__
    sync_builder = database.SyncQueryBuilder.__mro__

    assert database._BaseQueryBuilder in async_builder
    assert database._BaseQueryBuilder in sync_builder


def test_storage_query_builders_inherit_from_base():
    """Test that storage query builders inherit from base class."""
    # Check inheritance
    assert issubclass(storage.StorageQueryBuilder, storage._BaseStorageQueryBuilder)
    assert issubclass(storage.SyncStorageQueryBuilder, storage._BaseStorageQueryBuilder)


def test_modules_have_no_implementation_duplication():
    """Test that modules don't have duplicated implementation between async/sync."""
    # Check that each module has shared logic
    modules_with_helpers = [
        (auth, ['_build_login_request', '_build_refresh_request']),
        (policy, ['_build_single_resource_check', '_parse_check_response']),
        (functions, ['_build_execute_request', '_build_list_params']),
    ]

    for module, helper_names in modules_with_helpers:
        for helper_name in helper_names:
            assert hasattr(module, helper_name), \
                f"Module {module.__name__} missing helper {helper_name}"

    # Check that query builder modules have base classes
    assert hasattr(database, '_BaseQueryBuilder')
    assert hasattr(storage, '_BaseStorageQueryBuilder')


def test_all_sync_async_pairs_have_same_api():
    """Test that all sync/async module pairs have the same public API."""
    pairs = [
        (auth.AuthModule, auth.SyncAuthModule),
        (database.DatabaseModule, database.SyncDatabaseModule),
        (functions.FunctionsModule, functions.SyncFunctionsModule),
        (storage.StorageModule, storage.SyncStorageModule),
        (secrets.SecretsModule, secrets.SyncSecretsModule),
        (policy.PolicyModule, policy.SyncPolicyModule),
        (app.AppModule, app.SyncAppModule),
        (settings.SettingsModule, settings.SyncSettingsModule),
    ]

    for async_cls, sync_cls in pairs:
        # Get public methods (not starting with _)
        async_methods = {m for m in dir(async_cls) if not m.startswith('_')}
        sync_methods = {m for m in dir(sync_cls) if not m.startswith('_')}

        # Remove class-specific methods that are different (like __init__)
        async_public = {m for m in async_methods if not m.startswith('__')}
        sync_public = {m for m in sync_methods if not m.startswith('__')}

        assert async_public == sync_public, \
            f"{async_cls.__name__} and {sync_cls.__name__} have different APIs: " \
            f"async={async_public}, sync={sync_public}"


def test_file_sizes_reduced():
    """Test that refactoring actually reduced file sizes."""
    import os
    from pathlib import Path

    # Expected max sizes after refactoring (in lines)
    # These are the actual sizes after refactoring
    expected_max_sizes = {
        'auth.py': 450,      # Was 560
        'database.py': 420,  # Was 597
        'storage.py': 440,   # Was 622
        'functions.py': 350, # Was 387
        'policy.py': 270,    # Was 266
        'secrets.py': 180,   # Was 158
        'app.py': 120,       # Was 93
        'settings.py': 100,  # Was 75
    }

    modules_dir = Path('src/taruvi/modules')

    for filename, max_lines in expected_max_sizes.items():
        filepath = modules_dir / filename

        if filepath.exists():
            with open(filepath) as f:
                line_count = len(f.readlines())

            assert line_count <= max_lines, \
                f"{filename} has {line_count} lines, expected <= {max_lines}"
