"""Exercise the real opt-in hooks and login fixture in isolated pytest runs.

The child uses this repository's conftest unchanged, with only HTTP delivery
replaced. No case can reach a running backend or use developer credentials.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_live_case(tmp_path, *, opt_in, outcome="success", credentials=True):
    harness = Path(__file__).with_name("conftest.py").read_text()
    transport = '''
@pytest.fixture(scope="session", autouse=True)
def controlled_login_transport():
    import httpx
    from unittest.mock import patch

    def login(url, **kwargs):
        outcome = os.environ["HARNESS_LOGIN_OUTCOME"]
        if outcome == "connect":
            raise httpx.ConnectError("transport-test-do-not-print-credentials")
        response = {"meta": {"access_token": "fixture-access-token"}}
        if outcome == "missing_token":
            response = {"meta": {}}
        if outcome == "invalid_json":
            return httpx.Response(200, content=b"not-json", request=httpx.Request("POST", url))
        status = int(outcome) if outcome.isdigit() else 200
        return httpx.Response(status, json=response, request=httpx.Request("POST", url))

    with patch("httpx.post", side_effect=login):
        yield
'''
    (tmp_path / "conftest.py").write_text(harness + transport)
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "test_live.py").write_text('''
import pytest
pytestmark = pytest.mark.integration

def test_live(fresh_jwt_token):
    assert fresh_jwt_token == "fixture-access-token"
''')
    env = {key: value for key, value in os.environ.items() if not key.startswith("TARUVI_")}
    env.update({
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "TARUVI_API_URL": "https://disposable.invalid",
        "HARNESS_LOGIN_OUTCOME": outcome,
    })
    if credentials:
        env.update(TARUVI_TEST_EMAIL="fixture@example.invalid", TARUVI_TEST_PASSWORD="private-fixture-password")
    env.pop("RUN_INTEGRATION_TESTS", None)
    if opt_in is not None:
        env["RUN_INTEGRATION_TESTS"] = opt_in
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--confcutdir", str(tmp_path)],
        cwd=tmp_path, env=env, text=True, capture_output=True, timeout=20, check=False,
    )


@pytest.mark.parametrize("opt_in", [None, "", "0", "false", "off"])
def test_live_tests_stay_disabled_without_the_exact_opt_in(tmp_path, opt_in):
    result = run_live_case(tmp_path, opt_in=opt_in)
    assert result.returncode == 0, result.stdout
    assert "1 skipped" in result.stdout


def test_explicit_opt_in_runs_a_configured_live_case(tmp_path):
    result = run_live_case(tmp_path, opt_in="1")
    assert result.returncode == 0, result.stdout
    assert "1 passed" in result.stdout


@pytest.mark.parametrize("outcome", ["401", "503", "connect", "missing_token", "invalid_json"])
def test_configured_login_failure_is_a_failure_not_a_skip(tmp_path, outcome):
    result = run_live_case(tmp_path, opt_in="1", outcome=outcome)
    assert result.returncode == 1, result.stdout
    assert "1 error" in result.stdout
    assert "Live integration login" in result.stdout
    assert "private-fixture-password" not in result.stdout
    assert "transport-test-do-not-print-credentials" not in result.stdout


def test_explicit_live_run_requires_credentials(tmp_path):
    result = run_live_case(tmp_path, opt_in="1", credentials=False)
    assert result.returncode == 1, result.stdout
    assert "TARUVI_TEST_EMAIL" in result.stdout
    assert "TARUVI_TEST_PASSWORD" in result.stdout
