# SDK testing

The Python SDK uses pytest, pytest-asyncio, and httpx.MockTransport. Tests are
organized by what they prove: unit tests exercise the SDK boundary without a
network, and integration tests are explicitly opted in for a real Taruvi
environment.

## Commands

```bash
python -m pip install '.[dev]'
python -m pytest -q                         # unit tests; integration tests skip
python -m pytest tests/test_http_clients.py -q
python -m pytest tests/test_database_edges.py -q
python -m pytest -m integration -q           # live tests only, when enabled
RUN_INTEGRATION_TESTS=1 python -m pytest -m integration -q
python -m pytest --cov=taruvi --cov-report=term-missing
```

Set `TARUVI_API_URL`, `TARUVI_TEST_APP_SLUG`, and the credentials documented in
`tests/README.md` before running live tests. Live tests are marked
`integration` and are skipped unless `RUN_INTEGRATION_TESTS=1` is present. They
must use a disposable test site and function/table names; do not put tokens in
the repository or in command output.

## Test map

| Area | Primary tests | Contract covered |
| --- | --- | --- |
| Import, factory, config, auth | `test_imports.py`, `test_client_factory.py`, `test_credentials.py`, `test_auth_manager.py` | lazy imports, sync/async selection, credential precedence, auth lifecycle |
| Transport and errors | `test_http_clients.py`, `test_retry_safety.py`, `test_errors.py` | httpx response parsing, typed errors, headers, retry safety, sync/async parity |
| Query and database | `test_utils.py`, `test_aggregations*.py`, `test_database_edges.py`, `test_database_search.py` | encoded query builders and high-risk query operations |
| Feature integrations | `test_*_integration.py` | live database, storage, functions, secrets, analytics, and app/settings contracts |

Use parametrization for equivalent sync/async or status/operator families and
assert stable API contracts. Keep transport tests deterministic and use the
live suite for integration behavior that mocks cannot prove.
