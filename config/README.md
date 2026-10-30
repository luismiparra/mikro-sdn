# Lab configuration

A complete example network, used by the [getting-started guide](../docs/getting-started.md), the
[generated examples](../examples/generated-output/) and the test suite. Copy it as the starting
point of your own config folder (`CONFIG`).

| Device | Role | `wan_order` | `site_id` | `mgmt_int` | AS | Site block | Notable |
|--------|------|:-----------:|:---------:|------------|----|------------|---------|
| `lab-mikro1` | core | 0 | 1 | 192.168.88.11 | 65110 | 10.21.0.0/16 | every configlet but `wifi`; three VPNs (mgmt, admin, user); VXLAN; access ports; fixed endpoint |
| `lab-mikro2` | core | 1 | 2 | 192.168.88.12 | 65120 | 10.22.0.0/16 | VXLAN, `external_ddns` |
| `lab-mikro3` | core | 2 | 3 | 192.168.88.13 | 65130 | 10.23.0.0/16 | VXLAN, `external_ddns` |
| `lab-mikro4` | edge | 3 | 4 | 192.168.88.14 | 65140 | 10.24.0.0/16 | `radius_core`, VXLAN, `external_ddns` |
| `lab-mikro5` | edge | 4 | 5 | 192.168.88.15 | 65150 | 10.25.0.0/16 | no VXLAN |
| `lab-mikro6` | edge | 5 | 6 | 192.168.88.86 | 65160 | 10.26.0.0/16 | `wifi`, `radius_server`, `push_config`/`push_clean` off |
| `externalhost1` | external_edge | 6 | 7 | 10.91.1.1 | 65300 | 10.91.0.0/16 | Linux + FRR peer |
| `externalhost2` | external_edge | 7 | 8 | 10.91.1.2 | 65302 | 10.92.0.0/16 | Linux + FRR peer |

IPv6 uses the documentation prefix `2001:db8::/32`, and domains use `example.int`. Before using
any of it on real routers, read the review notes in [config files](../docs/configuration/config-files.md)
(SNMP community, time zone, syslog/NetFlow targets, address lists).

| Path | |
|------|---|
| `inventory/` | One file per device, see the [inventory reference](../docs/configuration/inventory.md). |
| `firewall/global/` | Firewall for every device; `firewall/lab-mikro1/` has device-specific rules. |
| `general/core/`, `general/edge/` | Baseline settings per role. |
| `dhcp/ipv4/<device>/` | Static DHCP leases. |
| `clean_routes.yml` | Paths the clean step manages. |
