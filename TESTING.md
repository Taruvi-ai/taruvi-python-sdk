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
python scripts/check_sdk_types.py          # strict source + public Client contracts
python -m ruff check src/ tests/
python -m black --check src/ tests/
python -m build
python -m twine check dist/*
python scripts/check_sdk_types.py --wheel dist/*.whl
```

The terminal summary reports passes, failures, and skips separately. Open
`htmlcov/index.html` after the HTML coverage command. A default run skips live
tests; those skips are not evidence that the deployed API works.

Set `TARUVI_LIVE_FIXTURE_MANIFEST` and the fixture credentials documented in
`tests/README.md` before running live tests. The manifest supplies the owned
site/app; URL or app environment defaults do not select an existing site. Live tests are marked
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
| Function and policy wire | `test_functions_transport.py`, `typing/functions_contract.py` | Actual sync/async HTTPX request loop, backend-generated invocation/envelope fixtures, protobuf-generated policy metadata, canonical invocation pages, supported filters and static return typing |
| SDK declarations and packaging | `typing/client_contract.py`, `typing/client_contract_invalid.py`, `scripts/check_sdk_types.py` | Public factory inference, all lazy module properties, mode-preserving authentication, await/context-manager contracts, packaged `py.typed`, and isolated installed-wheel consumers |
| Feature integrations | `test_*_integration.py` | live database, storage, functions, secrets, analytics, and app/settings contracts |

Use parametrization for equivalent sync/async or status/operator families and
assert stable API contracts. Keep transport tests deterministic and use the
live suite for integration behavior that mocks cannot prove.

The final October 4 default gate passed **268 tests, with 44 explicitly gated
live cases skipped**. The current strict public source gate checked **42 files
(SDK source and two consumer probes)** and required **12 expected
negative-consumer diagnostics**. Its log is
`/tmp/taruvi-python-final-public-types-oct4.log`. The rebuilt final wheel also
passes the isolated installed-consumer gate with all 12 required diagnostics,
its `py.typed` marker and lazy imports verified:
`/tmp/taruvi-python-installed-final-types-oct4.log`. Build and Twine checks pass.

The final shared owned-platform run passed **all 44 Python live cases**, followed
by eight JavaScript and six Refine live cases, in
`/tmp/taruvi-sdk-owned-all-cleanup-final-oct4.log`. Python's selected live run took 8.29
seconds. It used actual socket HTTP, tenant PostgreSQL/pgvector, Redis, MinIO and
a separate Celery worker; the provisioner removed its owned processes and
containers. Enabled missing resources, login failures and unexpected API errors
fail the run rather than becoming skips. This is local acceptance of these
source revisions and fixture configuration, not production deployment or
external payment/SharePoint acceptance.

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

CI runs on pull requests and pushes to the supported branches, including `beta`.
Pytest, Ruff, Black, strict whole-source mypy, and public-client declaration
checks are required. The package build also requires an installed-wheel consumer
check. The publish workflow requires pytest and the same source/type gates,
then builds and checks the wheel before tagging or uploading. Both workflows
explicitly disable credentialed integration tests. No workflow was dispatched
or package published during this review.

The type checker and formatters target the package's minimum supported Python
version, 3.10. `NotRequired` and `Self` use `typing_extensions` on Python 3.10.
Source types have no imported-module suppression; the former Function-only
command `scripts/check_function_types.py` now delegates to the full SDK gate.
The wheel probe creates a temporary virtual environment, installs the wheel
and its dependencies, removes source import overrides, confirms the packaged
`py.typed` marker, and checks the public factory from that installation. It
requires package-index access for the isolated dependency installation.

The probe verifies that explicit `mode="sync"` returns a blocking client and
`mode="async"` returns an asynchronous client. Auto-detection has a conservative
union type because the event-loop state is only known at runtime. Token login
and sign-out return a mode-preserving client synchronously in both modes;
password login and resource calls follow the client's mode. Incorrect awaits,
missing awaits, mismatched context managers, and assuming auto-detection is
synchronous must fail type checking. JSON data types remain annotations rather
than additional runtime response validation.

Six sync/async transport regressions failed before database record-ID encoding
was corrected. They exercise actual HTTPX URLs for GET/PATCH/DELETE, including
reserved query, fragment, slash and percent characters. These checks prove
request identity preservation, not that every text ID is addressable by the
backend.

## Function response review

The Functions transport fixture `tests/fixtures/function-wire.json` was generated
on October 3 from the platform's `FunctionInvocationRecordSerializer`,
`TaskResultSerializer`, and `AppDataResponse`, using unsaved synthetic models and
explicit task-result context. It contains numeric function/invocation IDs,
nullable anonymous callers, a missing retained task result, synchronous `False`,
synchronous `None` normalization, queued-but-already-completed metadata, and a
list record without heavy logs. The transport checks retain actual module,
HTTP client and request-loop code and substitute only HTTPX's transport.

Both public execute annotations now describe `FunctionExecutionResponse`, not
an invocation record. Invocation state is nested under nullable `task_result`;
there is no top-level invocation status/result. The global result lookup keeps
its own `data` envelope. Function lists retain limit/offset; global invocation
lists use page/page_size. Their legacy aliases translate aligned offsets and
reject ambiguous offsets or unsupported status filters before transport.

Run the focused source and static gates:

```bash
.venv/bin/pytest tests/test_functions_transport.py tests/test_module_contracts.py tests/test_sync_async_parity.py
.venv/bin/python scripts/check_sdk_types.py
```

The static gate checks the whole SDK and public Client factory, including
Function responses, authentication, lazy API properties, and mode-sensitive
await/context contracts. The live Functions suite remains opt-in. Its eight
cases cover sync and async client modes, direct and queued execution with actual
terminal worker results, matching invocation/detail/catalog identity, and the
missing-task PENDING envelope versus a missing-function 404. All eight passed
within the final owned HTTP run. The APP fixture echoes caller fields after
excluding reserved context injected by the platform. No customer function,
production worker, external provider or published package was exercised.


The policy fixture `tests/fixtures/policy-wire.json` was generated from the
platform environment's `cerbos.response.v1.response_pb2.CheckResourcesResponse`
using `MessageToDict(..., preserving_proto_field_name=True)`, exactly as the
platform endpoint serializes it. Sync and async transport cases preserve
`request_id`, `cerbos_call_id`, `validation_errors`, resource `policy_version`,
and the `EFFECT_ALLOW` enum spelling through the actual SDK request loop.
Public-client consumer probes also type-check the optional metadata fields;
six assertion errors reproduced the incorrect camelCase declarations before
correction. The SDK has no protobuf/Cerbos dependency from these tests.
