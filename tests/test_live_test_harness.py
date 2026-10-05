"""Exercise live opt-in, fixture ownership and login failures without a network."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_live_case(
    tmp_path,
    *,
    opt_in,
    outcome="success",
    credentials=True,
    manifest_kind="valid",
    token_type=None,
    marked=True,
):
    harness = Path(__file__).with_name("conftest.py").read_text()
    transport = """
@pytest.fixture(scope="session", autouse=True)
def controlled_login_transport():
    import httpx
    from unittest.mock import patch

    def login(url, **kwargs):
        Path("login-called").write_text("called")
        outcome = os.environ["HARNESS_LOGIN_OUTCOME"]
        if outcome == "connect":
            raise httpx.ConnectError("transport-test-do-not-print-credentials")
        response = {"meta": {"access_token": "fixture-access-token"}}
        if outcome == "missing_token":
            response = {"meta": {}}
        if outcome == "invalid_json":
            return httpx.Response(200, content=b"not-json", request=httpx.Request("POST", url))
        status = int(outcome) if outcome.isdigit() else 200
        if status >= 400:
            response = {"message": "private-fixture-password"}
        return httpx.Response(status, json=response, request=httpx.Request("POST", url))

    with patch("httpx.post", side_effect=login):
        yield
"""
    (tmp_path / "conftest.py").write_text(harness + transport)
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "test_live.py").write_text("""import os

import pytest

pytestmark = pytest.mark.integration

def test_live(live_auth):
    token_type = os.environ.get("HARNESS_TOKEN_TYPE", "jwt")
    expected = "explicit-fixture-token" if "HARNESS_TOKEN_TYPE" in os.environ else "fixture-access-token"
    assert live_auth == (expected, token_type)
""")
    if not marked:
        test_file = tmp_path / "test_live.py"
        test_file.write_text(
            test_file.read_text().replace("pytestmark = pytest.mark.integration", "")
        )
    env = {key: value for key, value in os.environ.items() if not key.startswith("TARUVI_")}
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", HARNESS_LOGIN_OUTCOME=outcome)
    if credentials:
        env.update(
            TARUVI_TEST_EMAIL="fixture@example.invalid",
            TARUVI_TEST_PASSWORD="private-fixture-password",
        )
    if token_type:
        env[f"TARUVI_{token_type.upper()}"] = "explicit-fixture-token"
        env["HARNESS_TOKEN_TYPE"] = token_type
    if manifest_kind != "missing":
        fixture = {
            "kind": "taruvi-sdk-live-fixture-v1",
            "fixture_id": "sdk-live-harness",
            "disposable": manifest_kind != "not_disposable",
            "api_url": "https://disposable.invalid/sites/fixture/",
            "app_slug": "fixture-app",
            "resources": {},
        }
        if manifest_kind == "embedded_password":
            fixture["api_url"] = "https://user:private-fixture-password@disposable.invalid"
        filename = tmp_path / "manifest.json"
        filename.write_text("not-json" if manifest_kind == "invalid_json" else json.dumps(fixture))
        env["TARUVI_LIVE_FIXTURE_MANIFEST"] = str(filename)
    env.pop("RUN_INTEGRATION_TESTS", None)
    if opt_in is not None:
        env["RUN_INTEGRATION_TESTS"] = opt_in
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--confcutdir",
            str(tmp_path),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    return result, (tmp_path / "login-called").exists()


@pytest.mark.parametrize("opt_in", [None, "", "0", "false", "off"])
def test_live_tests_stay_disabled_without_the_exact_opt_in(tmp_path, opt_in):
    result, called = run_live_case(tmp_path, opt_in=opt_in, manifest_kind="missing")
    assert result.returncode == 0, result.stdout
    assert "1 skipped" in result.stdout
    assert called is False


def test_explicit_opt_in_runs_a_configured_live_case(tmp_path):
    result, called = run_live_case(tmp_path, opt_in="1")
    assert result.returncode == 0, result.stdout
    assert "1 passed" in result.stdout
    assert called is True


@pytest.mark.parametrize("outcome", ["401", "503", "connect", "missing_token", "invalid_json"])
def test_configured_login_failure_is_a_failure_not_a_skip(tmp_path, outcome):
    result, called = run_live_case(tmp_path, opt_in="1", outcome=outcome)
    assert result.returncode == 1, result.stdout
    assert "1 error" in result.stdout
    assert "Live integration login" in result.stdout
    assert "private-fixture-password" not in result.stdout
    assert "transport-test-do-not-print-credentials" not in result.stdout
    assert called is True


def test_explicit_live_run_requires_credentials_or_a_token(tmp_path):
    result, called = run_live_case(tmp_path, opt_in="1", credentials=False)
    assert result.returncode == 1, result.stdout
    assert "TARUVI_TEST_EMAIL" in result.stdout
    assert "TARUVI_TEST_PASSWORD" in result.stdout
    assert called is False


@pytest.mark.parametrize(
    "manifest_kind", ["missing", "invalid_json", "not_disposable", "embedded_password"]
)
def test_live_run_refuses_missing_or_unsafe_fixture_before_login(tmp_path, manifest_kind):
    result, called = run_live_case(tmp_path, opt_in="1", manifest_kind=manifest_kind)
    assert result.returncode == 1, result.stdout
    assert "1 error" in result.stdout
    assert called is False
    assert "private-fixture-password" not in result.stdout


@pytest.mark.parametrize("token_type", ["api_key", "jwt", "session_token"])
def test_explicit_token_supports_resource_cases_without_repeated_login(tmp_path, token_type):
    result, called = run_live_case(tmp_path, opt_in="1", token_type=token_type, credentials=False)
    assert result.returncode == 0, result.stdout
    assert "1 passed" in result.stdout
    assert called is False


def test_unmarked_live_fixture_cannot_send_requests_without_opt_in(tmp_path):
    result, called = run_live_case(tmp_path, opt_in=None, marked=False)
    assert result.returncode == 1, result.stdout
    assert "Live fixture requested without RUN_INTEGRATION_TESTS=1" in result.stdout
    assert called is False
