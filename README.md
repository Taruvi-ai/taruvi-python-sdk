# Taruvi Python SDK

Official Python SDK for TaruviBase.

[![PyPI](https://img.shields.io/pypi/v/taruvi?label=pypi)](https://pypi.org/project/taruvi/) [![Python versions](https://img.shields.io/pypi/pyversions/taruvi)](https://pypi.org/project/taruvi/) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/Taruvi-ai/taruvi-python-sdk/blob/main/LICENSE)

## Install

```bash
pip install taruvi
```

Requires Python 3.10 or newer.

## Quickstart

Generate an API key on your app's **Settings → Connect** page, then:

```python
import os
from taruvi import Client

with Client(
    api_url=os.environ["TARUVI_SITE_URL"],
    app_slug=os.environ["TARUVI_APP_SLUG"],
    api_key=os.environ["TARUVI_API_KEY"],
    mode="sync",
) as client:
    tasks = client.database.from_("tasks").page_size(20).execute()
```

Pass `mode="sync"` or `mode="async"` explicitly in reusable code. When `mode` is omitted, the client uses async mode inside a running event loop and sync mode otherwise.

The client exposes `auth`, `database`, `storage`, `functions`, `secrets`, `policy`, `app`, `settings`, `users` and `analytics`, in both sync and async modes.

## Learn more

[SDK docs](https://docs.taruvibase.com/docs/build/python) · [Documentation](https://docs.taruvibase.com/) · [Website](https://taruvibase.com/)

The full SDK reference, covering authentication, every module, sync vs async, configuration, errors and development setup, is in [docs/reference.md](https://github.com/Taruvi-ai/taruvi-python-sdk/blob/main/docs/reference.md).

## Contributing

See [CONTRIBUTING.md](https://github.com/Taruvi-ai/taruvi-python-sdk/blob/main/CONTRIBUTING.md) and [CHANGELOG.md](https://github.com/Taruvi-ai/taruvi-python-sdk/blob/main/CHANGELOG.md). Report bugs in [GitHub Issues](https://github.com/Taruvi-ai/taruvi-python-sdk/issues), and email security reports to support@taruvibase.com instead of opening a public issue.

## License

MIT, see [LICENSE](https://github.com/Taruvi-ai/taruvi-python-sdk/blob/main/LICENSE).
