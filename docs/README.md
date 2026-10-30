# mikro-sdn documentation

New here? Read **[Getting started](getting-started.md)**, then **[Concepts](concepts.md)**.

## Learn

| Page | |
|------|---|
| [Getting started](getting-started.md) | Install, generate the lab offline, prepare a router, dry run, first push. |
| [Concepts](concepts.md) | Roles, configlets, the generate → clean → push cycle, identity by comment, the safety model, run modes. |
| [Network design](network-design.md) | Addressing plan, WireGuard mesh, `wan_order`, BGP filters, VXLAN, internet transit, limits. |

## Configure

| Page | |
|------|---|
| [Inventory reference](configuration/inventory.md) | Every device field, `wg-vpn`, `lan`, VLANs, `netbox`, external peers. |
| [Config files](configuration/config-files.md) | Firewall, general and DHCP files, address lists, rule order, file order, `clean_routes.yml`. |
| [Environment and control](configuration/environment.md) | Every environment variable of every tool, and `control.yml`. |
| [Configlets](configlets.md) | What each configlet creates on the router. |

## Operate

| Page | |
|------|---|
| [Operations](operations.md) | Add/remove sites, firewall changes, VPN users, onboarding, boot hook, scheduled runs. |
| [Secrets and outputs](secrets-and-outputs.md) | `SECRETS` and `WEB` contents, key lifecycle, backups. |
| [CI/CD](ci-cd.md) | GitOps pipeline with GitHub Actions, CI log format. |
| [Security](security.md) | Trust model, known weaknesses, hardening checklist. |
| [Troubleshooting](troubleshooting.md) | Errors and what to do about them. |

## Tools

| Page | |
|------|---|
| [Monitoring](tools/monitoring.md) | InfluxDB collector: WireGuard, netwatch, DHCP, RADIUS. |
| [Web portal](tools/web-portal.md) | Self-service DNS filter / VPN toggles and the router boot hook. |
| [NetBox](tools/netbox.md) | One-way sync of sites, devices, VLANs, prefixes and IPs. |
| [External peers](tools/external-peers.md) | Linux hosts with WireGuard + FRR in the BGP backbone. |

## Develop

| Page | |
|------|---|
| [Testing](testing.md) | Test suite, doubles, known bugs. |
| [Contributing](../CONTRIBUTING.md) | How to propose changes. |
| [Changelog](../CHANGELOG.md) | What changed between public versions. |
