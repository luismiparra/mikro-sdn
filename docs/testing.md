# Testing

The project has a pytest suite of unit and functional tests with a **95% coverage gate**. No test
talks to a real router, InfluxDB, NetBox or the network: every external system is replaced by an
in-memory double. The suite runs in CI on every push
([`.github/workflows/tests.yml`](../.github/workflows/tests.yml)).

## Running the tests

```bash
.venv/bin/pip install -r requirements-dev.txt   # once: adds pytest and pytest-cov
.venv/bin/python -m pytest                       # whole suite + coverage report
.venv/bin/python -m pytest tests/unit            # unit tests only
.venv/bin/python -m pytest -m functional         # functional tests only
.venv/bin/python -m pytest --no-cov -k wan       # quick subset, without coverage
```

`pytest.ini` turns coverage on for every run. `.coveragerc` measures `1-mikro-auto`,
`2-mikro-monitoring`, `3-mikro-webportal` and `4-netbox`, and the run fails when total coverage
is below 95%. The report lists the missing lines of every module. The `wg` binary is not needed:
keys are faked.

## Layout

| Path | Content |
|------|---------|
| `tests/conftest.py` | Isolated environment and shared fixtures |
| `tests/fakes.py` | In-memory doubles of RouterOS (API and REST) and NetBox |
| `tests/unit/` | One file per module, each function and branch in isolation |
| `tests/functional/` | End-to-end flows over the lab configuration in `config/` |

### Isolated environment

The modules read their environment at import time and call `load_dotenv()`. `tests/conftest.py`
sets every variable the project uses **before** importing anything, so your `.env` never leaks
into the tests (`DEBUGMODE` would make `errorStop()` wait for input, and the portal start a
server). `CONFIG` points to the lab config (`config/`); `SECRETS` and `WEB` to temporary folders.

Main fixtures:

- `secrets_dir` / `web_dir`: empty temporary `SECRETS` and `WEB` folders, wired into every module.
- `lab_secrets`: `secrets_dir` with the files the lab configlets read (RADIUS, WiFi, MAC list).
- `config_dir`: point the modules at a config folder (the lab config by default).
- `device_factory`: build an inventory device with every field the configlets use.
- `fake_wg_keys` (automatic): deterministic WireGuard keys.
- The module state of `mikro_wan` and `mikro_docs` is reset before every test (automatic).

### Test doubles (`tests/fakes.py`)

- `FakeRouterOsApi`: a router. `get_resource(path)` supports `get/add/set/remove/call('move')`,
  stores keys with dashes like RouterOS, records every call (`calls`, `writes()`) and can be told
  to fail an operation (`failures={(path, "add"): error}`).
- `FakeResponse`: a `requests` response for the REST API.
- `FakeNetbox`: enough of `pynetbox.api` for the sync (`nb.<app>.<endpoint>`).

## Functional tests

- `test_mikro_pipeline.py`: loads the lab inventory and generates every device. It checks that
  both ends of every WireGuard/BGP link agree (ports, keys, transit IPs, AS numbers), then pushes
  to one fake router per device and checks:
  - every generated object is on the router,
  - `posi`/`bot` firewall ordering, and the same order whatever order the filesystem lists files in,
  - a second push changes nothing,
  - clean removes unknown objects but keeps protected ones,
  - a dry run writes nothing,
  - firewall-only mode,
  - unreachable and push-disabled devices,
  - the whole `control_automation` run with its documents.
- `test_webportal.py`: the Flask routes with the test client over the lab inventory and an
  in-memory address list per site.
- Monitoring and NetBox flows run their entry points with the external clients mocked.

## Known bugs

Bugs found while writing the tests are kept as `@pytest.mark.xfail(strict=True, reason="BUG: ...")`
tests that describe the correct behaviour. They show as `xfailed`. When a bug is fixed, its test
passes, pytest reports `XPASS(strict)` as a failure, and the mark must be removed so the test
protects the fix.

| Test | Bug |
|------|-----|
| `unit/test_mikro_fw.py::test_process_fw_rules_survives_a_failed_add` | A failed `addFWRule` doesn't restore `item['resource']`; the next line raises `KeyError` and aborts the firewall push of that device. |
| `unit/test_mikro_shared.py::test_remove_duplicates_keeps_one_copy` | `removeDuplicatesInRunning` keeps iterating a stale list after a removal and also removes the first copy, so both duplicates are deleted. |
| `unit/test_mikro_wan.py::test_create_connection_edge_to_core_with_site_id_255` | A core with `site_id` ≥ 255 leaves the edge's random port range undefined (`UnboundLocalError`). Keep `site_id` ≤ 254. |
| `unit/test_netbox_main.py::test_wg_vpn_ipv6_prefix_does_not_depend_on_the_last_vlan` | The WireGuard VPN IPv6 prefix depends on the `ipv6` flag of the last LAN VLAN (leftover loop variable). |
| `unit/test_netbox_main.py::test_wg_vpn_prefixes_are_generated_without_lan_vlans` | A device without LAN VLANs skips its WireGuard fabric and VPN prefixes. |
| `unit/test_netbox_main.py::test_vlan_without_ipv6_adds_its_prefix_once` | For a VLAN without IPv6 the IPv4 prefix is appended twice. |
| `functional/test_mikro_pipeline.py::test_generation_twice_in_the_same_process` | `mikro_wan` keeps the mesh in module globals, so a second generation in the same process skips every link. Latent: the CLI runs one generation per process. |

Fixed since the first public version (now regular tests): a dry run wrote the MQTT broker to the
router; `create_files()` overwrote `secrets.json` when `SECRETS/external/` was missing; the
management VPN onboarding script ignored `LOCALSTRING` and produced an invalid `allowed-address`.

## Writing tests

- Unit tests of `<module>.py` go to `tests/unit/test_<module>.py`. Flows across modules go to
  `tests/functional/` with `pytestmark = pytest.mark.functional`.
- Use the fixtures instead of real paths, and the fakes instead of real clients.
- Run the whole suite after every change and keep it green with coverage ≥ 95%.
