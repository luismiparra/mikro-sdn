# 1-mikro-auto: the automation engine

Generates the configuration of every router from the inventory, then cleans and pushes it through
the RouterOS API. Run everything **from the repository root**.

```bash
python 1-mikro-auto/mikro_main.py                 # full run, as control/control.yml says
python 1-mikro-auto/mikro_main.py lab-mikro4      # generate all, clean + push one device
python 1-mikro-auto/mikro_main.py lab-mikro4 aux  # same, through the device's mgmt_aux address
TARGET_DEVICE=lab-mikro4 python 1-mikro-auto/mikro_main.py
python 1-mikro-auto/mikro_ports.py [device] [csv] # read-only WAN port / transit report
```

Documentation: [concepts](../docs/concepts.md) · [network design](../docs/network-design.md) ·
[configlets](../docs/configlets.md) · [inventory](../docs/configuration/inventory.md) ·
[environment](../docs/configuration/environment.md).

## Modules

| File | Role |
|------|------|
| `mikro_main.py` | Entry point. Reads `control.yml`, runs `generate_config()`, then `clean_and_push()` per device in a thread pool (30 workers), then writes the docs. |
| `mikro_shared.py` | Inventory and config-file loading (fixed file order, `wan_order` assignment), subnet derivation (`prepare_sdn`), API login (API-SSL 8729), generic add/update/clean against the running config, `create_files()`. |
| `mikro_wan.py` | WireGuard + BGP mesh: link pairs, slots (`wan_pairs`, `conn_slot`), interfaces, peers, transit IPs, BGP connections and filters, BFD, DDNS and port schedulers, external peers. |
| `mikro_lan.py` | Bridge, VLANs, ports, gateways, pools, DHCP/DHCPv6, service IPs, VXLAN. |
| `mikro_fw.py` | Firewall clean and push: address lists, `top`/`bot`/`posi` ordering. |
| `mikro_wg.py` | Remote-access WireGuard VPNs, client files, QR codes, onboarding scripts. |
| `mikro_internet.py` | Internet routing table, policy routing marks, per-core transit with failover. |
| `mikro_netwatch.py` | DNS fallback, internet probes, optional MQTT broker. |
| `mikro_autoupdate.py` | Housekeeping schedulers, optional boot hook and watchdog. |
| `mikro_radius_server.py` | RouterOS user-manager users and RADIUS clients. |
| `mikro_wifi.py` | Legacy wireless interfaces, security profiles, RADIUS, MAC ACL. |
| `mikro_docs.py` | Markdown/HTML pages, BIND snippets, change log, external peer files. |
| `mikro_ports.py` | Read-only report of listen ports and transit IPs of the mesh. |
| `mikro_log.py` | Console/CI log formatting and summary tables, see [CI log format](../docs/ci-cd.md#ci-log-format). |

## Adding a configlet

1. Create `mikro_<name>.py` with `load_config(device)` (or `(device, inventory)`) returning a list
   of dicts. Each dict has `resource` (RouterOS path), a unique `comment` (or `use_set: True`) and
   the RouterOS properties.
2. Call it from `generate_config()` in `mikro_main.py` under `if '<name>' in device['configlet']`.
3. If the configlet owns a new RouterOS path, add the path to `clean_routes.yml` so stale objects
   are removed.
4. Add unit tests in `tests/unit/` and document the configlet in `docs/configlets.md`.
