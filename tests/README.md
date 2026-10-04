# Live SDK integration tests

The default commands and complete test map are in [`../TESTING.md`](../TESTING.md).
The platform's `scripts/testing/sdk_live_acceptance.py --run` provisions the
owned resources and invokes the live gate; see its `--help` and
`scripts/testing/README.md` for checkout paths and service prerequisites.
These tests exercise the current Python SDK through a real HTTP server, tenant
PostgreSQL and the configured storage/function services. They are not a smoke
check against arbitrary resources in a developer's existing site.

## Fixture contract

Provision a new, disposable tenant and its public cloud-member user before the
run. Both user copies must have the same ID; the login email must be verified.
Keep the backend and any required services running for the whole test process.
The fixture provisioner owns teardown of the tenant, user, S3 bucket and worker.
Tests only mutate records/files under their owned resources and remove those
records/files in `finally` blocks. Auth, Secrets, Analytics and App Settings cases
read synthetic fixture values and never alter customer credentials or settings.

Write an untracked JSON manifest and set `TARUVI_LIVE_FIXTURE_MANIFEST` to its
absolute path. Common fields are required even when running one module:

```json
{
  "kind": "taruvi-sdk-live-fixture-v1",
  "fixture_id": "sdk-live-unique-run-id",
  "disposable": true,
  "api_url": "http://127.0.0.1:8011/sites/disposable-site/",
  "app_slug": "sdk-live-app",
  "resources": {
    "user": {
      "id": "00000000-0000-0000-0000-000000000001",
      "username": "sdk-live-user",
      "email": "sdk-live-user@example.invalid"
    },
    "other_app_slug": "sdk-live-other",
    "app_settings": {"display_name": "SDK live settings", "primary_color": "#1976d2"},
    "other_app_settings": {"display_name": "SDK other settings", "primary_color": "#ff0000"},
    "secrets": {
      "shadowed_key": "sdk-live-unique-shadow",
      "site_only_key": "sdk-live-unique-site",
      "site_value": {"scope": "site", "answer": 41},
      "app_value": {"scope": "app", "answer": 42},
      "secret_type_slug": "sdk-live-json",
      "secret_type_name": "SDK live JSON",
      "tag": "sdk-live"
    },
    "analytics": {"query_slug": "sdk-live-bound-value"},
    "database": {"table_name": "sdk_live_records", "vector_table_name": "sdk_live_vectors"},
    "storage": {"bucket_slug": "sdk-live-files", "prefix": "sdk-live-unique-run-id"},
    "functions": {"function_slug": "sdk-live-echo", "output_mode": "echo"}
  }
}
```

This is a shape example, not a ready-made environment. Replace identities with
those actually created by the provisioner. Do not put passwords, authentication
tokens or real secret values in the manifest. The ownership marker is a required
operator assertion; it cannot make an ordinary/customer tenant disposable.
Module sections are required for the module selected below.

| Module | Required real fixture behavior |
| --- | --- |
| Auth | Public and tenant cloud-member identity above; verified allauth email/password login, `GET /api/users/me/` |
| Secrets | Private JSON secret type named/sluggified as above; exactly one tag on every fixture secret; site and primary-app secrets sharing `shadowed_key`, distinct site-only secret; alternate app has no override |
| Analytics | Primary-app saved query with `connection_type=internal` and SQL `SELECT CAST({{ value }} AS TEXT) AS value`; alternate app does not own that query |
| App Settings | Two apps with the stated settings subsets; settings auto-created by the platform |
| Database | Owned flat table with scalar `id`, string `name`, unique string `email`, optional string `description`; separate vector table with scalar `id`, string `name`, cosine `embedding` vector(3), and generated full-text search over `name` |
| Storage | Owned private S3-backed bucket; unique owned prefix; `file_size_limit=1024` bytes; accepts text/plain and application/octet-stream. Valid payloads fit the limit; a 2048-byte file and metadata over 2KB must fail within the partial batch |
| Functions | Owned APP Python function whose `main(params, user_data, sdk_client)` echoes caller fields, excluding reserved `request` and `__*` context injected by the runtime; broker/worker required for terminal-result cases |

## Run a module or the live gate

Supply credentials via the process environment. Do not commit an `.env` file,
print tokens or enable pytest's `--showlocals` for credentialed runs.

```bash
export TARUVI_LIVE_FIXTURE_MANIFEST=/absolute/path/to/owned-fixture.json
export TARUVI_TEST_EMAIL=sdk-live-user@example.invalid
# Set TARUVI_TEST_PASSWORD securely in the invoking environment.
export RUN_INTEGRATION_TESTS=1

python -m pytest -m integration tests/test_auth_integration.py -q
python -m pytest -m integration tests/test_secrets_integration.py -q
python -m pytest -m integration tests/test_analytics_integration.py -q
python -m pytest -m integration tests/test_app_settings_integration.py -q
python -m pytest -m integration tests/test_database_integration.py tests/test_database_search.py -q
python -m pytest -m integration tests/test_storage_integration.py -q
python -m pytest -m integration tests/test_functions_integration.py -q
python -m pytest -m integration -q
```

Resource cases may instead use an explicitly supplied `TARUVI_API_KEY`,
`TARUVI_JWT` or `TARUVI_SESSION_TOKEN` for that same fixture. Their precedence is
API key, JWT, session token, then one setup password login. The Auth cases always
require the fixture's email/password because they prove login and independent
client sessions. No test falls back to hardcoded administrator credentials or
loads a developer's `.env` file.

Only `RUN_INTEGRATION_TESTS=1` enables live requests. Missing, empty, `0`, `false`
and `off` values leave them skipped before fixture setup. Once enabled, missing
or malformed fixture configuration, login errors, unavailable services, missing
named resources and unexpected API responses fail the run. They are not accepted
as skips. Connection retries are disabled so a service failure stays clear and
fast. Run these tests as external SDK clients, outside a Taruvi function runtime.
Setup login failures omit credentials, response bodies and underlying exception
messages.

Live tests assert exact owned data, persisted lifecycle behavior and typed error
boundaries. A nonempty dict or successful HTTP status alone is insufficient.
Synchronous and asynchronous SDK paths remain independently exercised because
they have distinct generated modules and HTTP clients. Related steps share one
lifecycle case rather than duplicating shape-only tests for every parameter.
The default gate also runs `test_live_test_harness.py` in isolated subprocesses:
its controlled delivery proves opt-in behavior, sanitized setup failures and
credential selection without making external requests.

The fixture and client lifetimes follow [pytest's fixture teardown guidance](https://docs.pytest.org/en/stable/how-to/fixtures.html#safe-teardowns)
and [HTTPX's client cleanup guidance](https://www.python-httpx.org/async/).
Report live passes and default disabled skips separately. A live pass establishes
acceptance of that fixture/backend revision, not production deployment or live
third-party payment/SharePoint acceptance.

On October 4, the final shared disposable-platform gate passed **all 44 Python
live cases**, followed by eight JavaScript and six Refine cases. Evidence:
`/tmp/taruvi-sdk-owned-all-final-oct4.log`. The Python default gate separately
passed **268 tests / 44 explicitly disabled live cases**. These counts distinguish
a default skip from a separately verified real-service pass; enabled fixture
failures are not skips.
