"""Explicitly opted-in live tests against an owned, disposable fixture."""

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def live_manifest():
    """Read resource identities; never infer a developer's site or credentials."""
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.fail("Live fixture requested without RUN_INTEGRATION_TESTS=1.", pytrace=False)
    filename = os.getenv("TARUVI_LIVE_FIXTURE_MANIFEST")
    if not filename:
        pytest.fail("Live integration requires TARUVI_LIVE_FIXTURE_MANIFEST.", pytrace=False)
    problem = None
    try:
        manifest = json.loads(Path(filename).read_text())
    except (OSError, ValueError):
        problem = "Live fixture manifest must be a readable JSON file."
    if problem:
        pytest.fail(problem, pytrace=False)
    if not isinstance(manifest, dict):
        pytest.fail("Live fixture manifest must be a JSON object.", pytrace=False)
    if (
        manifest.get("kind") != "taruvi-sdk-live-fixture-v1"
        or manifest.get("disposable") is not True
        or not isinstance(manifest.get("fixture_id"), str)
        or not manifest["fixture_id"].startswith("sdk-live-")
    ):
        pytest.fail(
            "Live fixture manifest must identify an owned disposable SDK fixture.", pytrace=False
        )
    api_url = manifest.get("api_url")
    app_slug = manifest.get("app_slug")
    if not isinstance(api_url, str) or not isinstance(app_slug, str) or not app_slug:
        pytest.fail("Live fixture manifest requires api_url and app_slug.", pytrace=False)
    parsed = urlsplit(api_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        pytest.fail(
            "Live fixture api_url must be HTTP(S), without embedded credentials.", pytrace=False
        )
    if parsed.query or parsed.fragment or not isinstance(manifest.get("resources"), dict):
        pytest.fail(
            "Live fixture requires resources and an api_url without query/fragment.", pytrace=False
        )
    return manifest


@pytest.fixture(scope="session")
def live_resources(live_manifest):
    return live_manifest["resources"]


@pytest.fixture(scope="session")
def test_config(live_manifest):
    if os.getenv("TARUVI_FUNCTION_RUNTIME") == "true":
        pytest.fail(
            "Live integration must run as an external SDK client, outside a function runtime.",
            pytrace=False,
        )
    return {
        "api_url": live_manifest["api_url"].rstrip("/"),
        "app_slug": live_manifest["app_slug"],
        "username": os.getenv("TARUVI_TEST_EMAIL"),
        "password": os.getenv("TARUVI_TEST_PASSWORD"),
    }


@pytest.fixture(scope="session")
def login_credentials(test_config):
    if not test_config["username"] or not test_config["password"]:
        pytest.fail(
            "Live authentication requires TARUVI_TEST_EMAIL and TARUVI_TEST_PASSWORD "
            "for the disposable fixture user.",
            pytrace=False,
        )
    return test_config["username"], test_config["password"]


@pytest.fixture(scope="session")
def fresh_jwt_token(test_config, login_credentials):
    """One setup login; unexpected backend failures fail without leaking secrets."""
    import httpx

    email, password = login_credentials
    failure = None
    try:
        response = httpx.post(
            f"{test_config['api_url']}/_allauth/app/v1/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        failure = f"Live integration login returned HTTP {error.response.status_code}."
    except httpx.HTTPError as error:
        failure = f"Live integration login could not complete ({type(error).__name__})."
    if failure:
        pytest.fail(failure, pytrace=False)
    invalid_json = False
    try:
        data = response.json()
    except ValueError:
        invalid_json = True
    if invalid_json:
        pytest.fail("Live integration login returned invalid JSON.", pytrace=False)
    meta = data.get("meta") if isinstance(data, dict) else None
    token = meta.get("access_token") if isinstance(meta, dict) else None
    if not isinstance(token, str) or not token:
        pytest.fail("Live integration login response is missing meta.access_token.", pytrace=False)
    return token


@pytest.fixture(scope="session")
def live_auth(request, test_config):
    """Resource cases may use any SDK-supported credential, supplied explicitly."""
    for name, token_type in (
        ("TARUVI_API_KEY", "api_key"),
        ("TARUVI_JWT", "jwt"),
        ("TARUVI_SESSION_TOKEN", "session_token"),
    ):
        token = os.getenv(name)
        if token:
            return token, token_type
    return request.getfixturevalue("fresh_jwt_token"), "jwt"


def client_options(test_config):
    return {
        "api_url": test_config["api_url"],
        "app_slug": test_config["app_slug"],
        "api_key": None,
        "jwt": None,
        "session_token": None,
        "username": None,
        "password": None,
        "_env_file": None,
        "max_retries": 0,
        "timeout": 30,
    }


@pytest.fixture
async def anonymous_async_client(test_config):
    from taruvi import Client

    async with Client(mode="async", **client_options(test_config)) as client:
        yield client


@pytest.fixture
async def async_client(anonymous_async_client, live_auth):
    token, token_type = live_auth
    async with anonymous_async_client.auth.signInWithToken(token, token_type) as client:
        yield client


@pytest.fixture
def anonymous_sync_client(test_config):
    from taruvi import Client

    with Client(mode="sync", **client_options(test_config)) as client:
        yield client


@pytest.fixture
def sync_client(anonymous_sync_client, live_auth):
    token, token_type = live_auth
    with anonymous_sync_client.auth.signInWithToken(token, token_type) as client:
        yield client


@pytest.fixture
def unauth_test_config(monkeypatch):
    """Factory tests never depend on a live fixture or developer configuration."""
    monkeypatch.setenv("TARUVI_TEST_MODE", "true")
    for name in ("JWT", "API_KEY", "SESSION_TOKEN", "USERNAME", "PASSWORD"):
        monkeypatch.delenv(f"TARUVI_{name}", raising=False)
    return {
        "api_url": "https://example.invalid",
        "app_slug": "test-app",
        "api_key": None,
        "username": None,
        "password": None,
        "jwt": None,
    }


@pytest.fixture
async def async_functions_module(async_client):
    return async_client.functions


@pytest.fixture
def sync_functions_module(sync_client):
    return sync_client.functions


@pytest.fixture
async def async_database_module(async_client):
    return async_client.database


@pytest.fixture
def sync_database_module(sync_client):
    return sync_client.database


@pytest.fixture
async def async_storage_module(async_client):
    return async_client.storage


@pytest.fixture
def sync_storage_module(sync_client):
    return sync_client.storage


@pytest.fixture
async def async_secrets_module(async_client):
    return async_client.secrets


@pytest.fixture
def sync_secrets_module(sync_client):
    return sync_client.secrets


@pytest.fixture
async def async_analytics_module(async_client):
    return async_client.analytics


@pytest.fixture
def sync_analytics_module(sync_client):
    return sync_client.analytics


@pytest.fixture
async def async_app_module(async_client):
    return async_client.app


@pytest.fixture
def sync_app_module(sync_client):
    return sync_client.app


@pytest.fixture
def generate_unique_id():
    from uuid import uuid4

    return lambda: uuid4().hex[:12]


@pytest.fixture
def test_function_name(live_resources):
    return live_resources["functions"]["function_slug"]


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: requires an owned disposable live backend fixture"
    )


def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        skip = pytest.mark.skip(reason="Set RUN_INTEGRATION_TESTS=1 to enable owned live fixtures.")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)
