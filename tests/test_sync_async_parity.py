"""Keep generated sync and async module APIs aligned."""

import inspect

import pytest

from taruvi._async.modules.analytics import AsyncAnalyticsModule
from taruvi._async.modules.app import AsyncAppModule
from taruvi._async.modules.database import AsyncDatabaseModule, AsyncQueryBuilder
from taruvi._async.modules.functions import AsyncFunctionsModule
from taruvi._async.modules.policy import AsyncPolicyModule
from taruvi._async.modules.secrets import AsyncSecretsModule
from taruvi._async.modules.settings import AsyncSettingsModule
from taruvi._async.modules.storage import AsyncStorageQueryBuilder
from taruvi._async.modules.users import AsyncUsersModule
from taruvi._sync.modules.analytics import AnalyticsModule
from taruvi._sync.modules.app import AppModule
from taruvi._sync.modules.database import DatabaseModule, QueryBuilder
from taruvi._sync.modules.functions import FunctionsModule
from taruvi._sync.modules.policy import PolicyModule
from taruvi._sync.modules.secrets import SecretsModule
from taruvi._sync.modules.settings import SettingsModule
from taruvi._sync.modules.storage import StorageQueryBuilder
from taruvi._sync.modules.users import UsersModule


@pytest.mark.parametrize(
    ("async_type", "sync_type"),
    [
        (AsyncAnalyticsModule, AnalyticsModule),
        (AsyncAppModule, AppModule),
        (AsyncFunctionsModule, FunctionsModule),
        (AsyncDatabaseModule, DatabaseModule),
        (AsyncPolicyModule, PolicyModule),
        (AsyncSecretsModule, SecretsModule),
        (AsyncSettingsModule, SettingsModule),
        (AsyncStorageQueryBuilder, StorageQueryBuilder),
        (AsyncUsersModule, UsersModule),
        (AsyncQueryBuilder, QueryBuilder),
    ],
)
def test_generated_sync_and_async_modules_expose_the_same_public_methods(async_type, sync_type):
    async_methods = {
        name
        for name, value in inspect.getmembers(async_type, inspect.isfunction)
        if not name.startswith("_")
    }
    sync_methods = {
        name
        for name, value in inspect.getmembers(sync_type, inspect.isfunction)
        if not name.startswith("_")
    }

    assert async_methods == sync_methods
