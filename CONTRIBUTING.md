# Contributing

Thanks for your interest! Issues, questions and pull requests are welcome.

## Before you start

- Read [Concepts](docs/concepts.md) and [Network design](docs/network-design.md): the project
  implements one specific design, and changes should fit it or make it configurable.
- For larger changes, open an issue first to discuss the approach.

## Development setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

No router is needed: the tests use in-memory doubles, see [Testing](docs/testing.md).

## Pull requests

1. **Tests**: add or update tests for the change (unit tests in `tests/unit/`, cross-module flows in
   `tests/functional/`). The whole suite must pass with coverage ≥ 95%. Don't delete or weaken a
   test to make it pass. If a test describes a known bug, keep it as
   `@pytest.mark.xfail(strict=True, reason="BUG: …")`.
2. **Docs**: document every new configlet, inventory field, environment variable or behaviour change
   in `docs/` in the same pull request.
3. **Style**: match the surrounding code (module-level settings from `os.environ.get`, list of
   dicts per configlet, comments explaining *why*).
4. **No real data**: never commit real addresses, hostnames, MAC addresses, keys or passwords. Use
   the lab ranges, `example.int`, `2001:db8::/32`, `192.0.2.0/24`, `203.0.113.0/24` and
   `02:00:00:…` MACs.
5. **Safety**: changes that make the clean step remove more, or that write to routers in a dry run,
   need a clear explanation and tests.

## Reporting bugs

Include the RouterOS version, the relevant inventory snippet (sanitized), the command you ran and
the log output (`DEBUGMODE=1`). For security issues, see [Security](docs/security.md#reporting-a-vulnerability).
