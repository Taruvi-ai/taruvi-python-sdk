# Live integration tests

The complete test map and default commands are in [`../TESTING.md`](../TESTING.md).
This file documents only the opt-in live environment.

## Configure

```bash
export TARUVI_API_URL=http://localhost:8000
export TARUVI_TEST_APP_SLUG=test-app
export TARUVI_TEST_EMAIL=test@example.com
export TARUVI_TEST_PASSWORD='password-for-the-disposable-test-user'
export RUN_INTEGRATION_TESTS=1
```

The backend must expose the test site and any named resources used by the
selected module. Run one area at a time while developing:

```bash
python -m pytest -m integration tests/test_database_integration.py -q
python -m pytest -m integration tests/test_storage_integration.py -q
python -m pytest -m integration tests/test_functions_integration.py -q
```

Only `RUN_INTEGRATION_TESTS=1` enables live requests. Missing, empty, `0`,
`false`, and `off` values leave them skipped. Once enabled, missing credentials,
HTTP/connection failures during login, or a malformed login response fail setup
with an actionable message; they are not accepted as skips. The fixture omits
credentials, response bodies, and underlying exception messages from that error.

Use a disposable tenant and clean up created objects after a run; never commit
an `.env` file or include credentials in failure logs. Module-specific checks
may still skip missing named resources; report those skips separately from
passing live contracts.
