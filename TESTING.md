# SDK testing

The Python SDK uses pytest, pytest-asyncio, and httpx.MockTransport. Tests are
organized by what they prove: unit tests exercise the SDK boundary without a
network, and integration tests are explicitly opted in for a real Taruvi
environment.

## Commands

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q                         # unit tests; integration tests skip
python -m pytest tests/test_http_clients.py -q
python -m pytest tests/test_database_edges.py tests/test_vector_transport.py -q
python -m pytest tests/test_live_test_harness.py -q
python -m pytest tests/test_module_contracts.py tests/test_sync_async_parity.py -q
python -m pytest -m integration -q           # live tests only, when enabled
RUN_INTEGRATION_TESTS=1 python -m pytest -m integration -q
python -m pytest --cov=taruvi --cov-report=term-missing
python -m pytest --cov=taruvi --cov-report=html
```

The terminal summary reports passes, failures, and skips separately. Open
`htmlcov/index.html` after the HTML coverage command. A default run skips live
tests; those skips are not evidence that the deployed API works.

Set `TARUVI_API_URL`, `TARUVI_TEST_APP_SLUG`, and the credentials documented in
`tests/README.md` before running live tests. Live tests are marked
`integration` and are skipped unless `RUN_INTEGRATION_TESTS` is exactly `1`. Values
such as `0`, `false`, and `off` leave live tests disabled. When explicitly enabled,
missing credentials or a failed/malformed login fail the run with a sanitized
setup error instead of turning the configured backend failure into a skip. They
must use a disposable test site and function/table names; do not put tokens in
the repository or in command output.

## Test map

| Area | Primary tests | Contract covered |
| --- | --- | --- |
| Import, factory, config, auth | `test_imports.py`, `test_client_factory.py`, `test_credentials.py`, `test_auth_manager.py` | lazy imports, sync/async selection, credential precedence, auth lifecycle |
| Transport and errors | `test_http_clients.py`, `test_retry_safety.py`, `test_errors.py` | httpx response parsing, typed errors, headers, retry safety, sync/async parity |
| Query and database | `test_utils.py`, `test_aggregations*.py`, `test_database_edges.py`, `test_database_search.py` | encoded query builders and high-risk query operations |
| Vector/hybrid transport | `test_vector_transport.py` | public sync/async builders through actual HTTPX request handling: JSON-body POST for vector/hybrid, scalar GET fallback, site prefix, filters, controls, scores, validation errors, and delete refusal |
| Live-test gating | `test_live_test_harness.py` | isolated pytest subprocesses exercise the actual collection hook and login fixture; a controlled transport makes external requests impossible |
| Modules and sync/async parity | `test_module_contracts.py`, `test_sync_async_parity.py` | module routes/payloads, public method parity, generated sync behavior |
| Feature integrations | `test_*_integration.py` | live database, storage, functions, secrets, analytics, and app/settings contracts |

Use parametrization for equivalent sync/async or status/operator families and
assert stable API contracts. Keep transport tests deterministic and use the
live suite for integration behavior that mocks cannot prove.

On October 3, 2026 the default gate passed **248 tests, with 74 live tests
skipped**. The vector transport slice passed 30 tests. Nine harness regressions
failed before the gate and error handling changes. These figures do not claim
that the 74 live workflows ran. Several module-specific live tests still skip
missing remote resources; they need separately owned disposable fixtures before
being treated as release acceptance.

The vector transport cases verify request and response contracts, not database
ranking or index behavior. The platform repository separately owns
`cloud_site/data/tests/test_python_sdk_search.py`, which runs the pinned SDK
against its in-process Django WSGI application and real PostgreSQL/pgvector with
a disposable tenant. Do not point the SDK live tests at that test database or a
developer's ordinary organization.

The October 3 POST-query audit reproduced 12 failing sync/async cases before
repair: overlapping filters lost conditions, flat lists lost their JSON values,
a record ID disappeared from a vector read, and a 1,536-dimension count still
used a 23 KB URL. Those cases now pass through actual HTTPX request encoding;
ordinary GET paths remain covered. A separate scratch check fed the emitted
bodies through the current platform `DataQueryRequest` and typed filter parser
and confirmed the AND tree and comma-containing/typed list elements survive.
This parser check does not prove SQL ranking or a deployed route. The automatic
POST behavior requires the matching backend feature and does not fall back to
GET when that route is absent. Vector/hybrid `count()` fetches the bounded
candidate window without `page` or `page_size`, preserving the builder's page
for later reads; a one-row count request would undercount pure-vector results
because that backend total describes the returned page.

## Automated gate

CI now includes pull requests and pushes on `beta` as well as the existing
branches. The publish workflow runs pytest before tagging or uploading instead
of skipping tests. Both workflows disable credentialed integration tests
explicitly. Black formatting was repaired in ten files with unchanged Python
ASTs; the full local gate remains **242 passed / 74 live skipped**, and Black
and Ruff pass. Existing strict mypy findings remain advisory in CI; this does
not claim that the type-check backlog is resolved. No workflow was dispatched
or package published during this review.

Six sync/async transport regressions failed before database record-ID encoding
was corrected. They exercise actual HTTPX URLs for GET/PATCH/DELETE, including
reserved query, fragment, slash and percent characters; these checks prove
request identity preservation, not that every text ID is addressable by the
backend. The complete default gate now passes **248 tests / 74 live skipped**.
