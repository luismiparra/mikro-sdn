# Changelog

## 2026-10 — sync with the private edition + documentation

The public repository catches up with two years of fixes and features from the private network
it comes from, and gets complete documentation.

### Layout

- The engine moved from `1-mikro-sdn/` to **`1-mikro-auto/`** (same name as the private edition).
- The inventory is now **one file per device** in `config/inventory/` (was a single
  `inventory.yml`).
- New optional tools: `2-mikro-monitoring/` (InfluxDB), `3-mikro-webportal/` (Flask portal and
  boot hook), `4-netbox/` (NetBox sync).
- New `tests/` suite (unit + functional, ≥ 95% coverage) and a GitHub Actions workflow running it.
- The generated sample output moved from `docs/` to `examples/generated-output/`; `docs/` is now
  the documentation.
- `example_env` → `.env.example` (documented); new `secrets.example/`.

### Features (from the private edition)

- **Stable WAN slots**: `wan_order` pins each device's WireGuard ports and transit subnets, so
  adding a device never renumbers existing links. New `mikro_ports.py` report.
- **Deterministic config file order** (numeric prefix), so firewall order no longer depends on
  the filesystem.
- New configlets: **`wifi`**, **`radius_server`**. BGP instances for RouterOS ≥ 7.20,
  `trunk_ports_isolated`.
- MQTT RTT publishing from netwatch probes.
- Readable CI logs with icons, banners, GitHub annotations and summary tables (`mikro_log.py`).
- Many fixes to WAN generation, firewall ordering, updates, cleaning and RouterOS 7.15 – 7.20
  compatibility.

### Changes in this public edition

- Hard-coded values of the private network became settings: `ORG_NAME`, `MQTT_SERVER`,
  `MQTT_PORT`, `BOOT_UPDATE_URL`, `MGMT_CHECK_HOSTS`, `MGMT_HOSTS`, `RADIUS_CERTIFICATE`,
  `PORTAL_HOME_URL`. PTR records and NetBox DNS names use the device's `domain`. The boot hook and
  the reboot watchdog are now **opt-in**.
- Misspelled names fixed, old spellings still accepted: `RADIUS_SECRET` (`RAIUS_SECRET`),
  `isolated_trunk` / `trunk_ports_isolated` (`issolated_*`), `mgmt_aux` (`mtmt_aux`).
  Internal `proccess_*` functions renamed `process_*`.
- Neutral names: log module `mikro_log.py`, inventory field `rp_external` → `backbone_untrusted`,
  `NETBOX_TAG` (tags `MSDN-*`), firewall address lists `ACL4_*`/`ACL6_*` (portal lists
  `ACL4_PORTAL_DNS`/`ACL4_PORTAL_VPN`, exit lists `ACL4_EXIT_VIA_<core>`).
- The lab is a fully fictitious network: sites `10.21–26.0.0/16`, management `192.168.88.0/24`,
  IPv6 `2001:db8:10::/48`, firewall rules and address lists rewritten for it.
- `control/control.yml` ships in safe mode (`config` mode, dry run on).
- Requirements: `pillow` instead of `image` (which pulled in Django); unused `wireguard` removed;
  `requests` listed.

### Fixes

- A **dry run wrote the MQTT broker** to the router (`/iot/mqtt/brokers`).
- `create_files()` **overwrote `secrets.json`** with `{}` when `SECRETS/external/` was missing
  (e.g. after restoring a backup), regenerating every WireGuard key.
- The management VPN **onboarding script** hard-coded the `local_auto_` prefix (so pushes removed
  the new router's management tunnel when `LOCALSTRING` was different) and produced an invalid
  `allowed-address` with a space.

Known open bugs are listed in [docs/testing.md](docs/testing.md#known-bugs).

## 2024-07 — v0

First public version.
