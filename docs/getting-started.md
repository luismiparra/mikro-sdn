# Getting started

This guide takes you from a fresh clone to a first real push on **one lab router**, in four
stages. Every stage is safe to stop at.

1. [Install](#1-install)
2. [Generate the bundled lab offline](#2-generate-the-bundled-lab-offline): no router needed.
3. [Describe your own router](#3-describe-your-own-router)
4. [Prepare the router](#4-prepare-the-router)
5. [Dry run against the router](#5-dry-run-against-the-router): reads the router, writes nothing.
6. [First real push](#6-first-real-push)

> [!IMPORTANT]
> Use a lab router (a spare hAP, or a [CHR](https://help.mikrotik.com/docs/display/ROS/Cloud+Hosted+Router%2C+CHR)
> VM) for your first runs. A push makes the router match the repository and **removes** whatever
> the repository doesn't describe, see [Safety model](concepts.md#safety-model).

---

## 1. Install

Requirements on the machine that runs the automation:

| | |
|---|---|
| Python | 3.10 or newer (tested on 3.12) |
| WireGuard tools | the `wg` command, used to generate keys: `brew install wireguard-tools` / `sudo apt install wireguard-tools` |
| Network access | API-SSL (TCP 8729) to every router's `mgmt_int` or `mgmt_ext` address |

```bash
git clone https://github.com/luismiparra/mikro-sdn.git
cd mikro-sdn
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Always run the scripts **from the repository root**: templates and paths are resolved from the
current directory.

## 2. Generate the bundled lab offline

```bash
cp .env.example .env              # settings, every variable is in docs/configuration/environment.md
cp -r secrets.example secrets     # private files (RADIUS users, WiFi profile) the lab uses
.venv/bin/python 1-mikro-auto/mikro_main.py
```

`control/control.yml` ships with `mikro_auto_mode: 'config'`: the generator builds the
configuration of every device and writes it to disk, and **never opens a connection**. You should
see a banner per stage and a table of devices × configlets.

What to look at:

| File | What it is |
|------|------------|
| `secrets/proposed/<device>_global.yml` | Everything except firewall that would be pushed to the device, in push order. |
| `secrets/proposed/<device>_fw.yml` | Firewall filter, NAT, mangle rules and address lists, in push order. |
| `web/<device>.html` / `.md` | The same, as readable tables per RouterOS path (keys hidden). |
| `web/Global.html`, `web/bind_A.txt`, `web/bind_PTR.txt` | All devices, and DNS records for every interface address. |
| `secrets/secrets.json` | **Private keys** generated for every WireGuard link and VPN. Keep it, back it up, never commit it. |
| `secrets/external_export/` | WireGuard and FRR configs for the external Linux peers of the lab. |

Ready-made output of this step is in [`examples/generated-output/`](../examples/generated-output/).

Two other offline helpers:

```bash
.venv/bin/python 1-mikro-auto/mikro_ports.py              # listen ports + transit IPs of every mesh link
.venv/bin/python 1-mikro-auto/mikro_ports.py lab-mikro4   # one device
.venv/bin/python -m pytest                                # the test suite (needs requirements-dev.txt)
```

## 3. Describe your own router

Start from a copy of the lab so the firewall and general files come along:

```bash
cp -r config my-network
rm my-network/inventory/*.yml
rm -r my-network/dhcp/ipv4/lab-mikro* my-network/firewall/lab-mikro1
```

Create `my-network/inventory/site1.yml` from
[`config/inventory/lab-mikro1.yml`](../config/inventory/lab-mikro1.yml) and edit at least:

| Field | Set it to |
|-------|-----------|
| `name` | The router's name. It becomes `/system identity` and prefixes many objects. |
| `role` and the top-level key | `core` for your first router (`core:` list). |
| `wan_order`, `site_id` | `0` and `1`. Must be unique per device and never change later. |
| `mgmt_int` / `mgmt_ext` | The address the automation uses to reach the router (tried in that order). |
| `external_endpoint` | Public IP or DNS name of the router (WireGuard peers and VPN clients connect to it). |
| `api_version` | RouterOS version without dots: 7.16 → `716`, 7.20 → `720`. |
| `subnetv4` / `subnetv6` / `subnetv6slaac` | A free `/16`, `/96` and `/53` for the site, see [addressing plan](network-design.md#addressing-plan). |
| `domain`, `dns1`, `dns2`, `ntp1`, `location` | Your values (`location` must be unique per device). |
| `configlet` | Start small, e.g. `["general", "fw", "lan", "dhcp"]`, and add more once that works. |
| `lan` | The ports of *your* hardware: which are trunks and which are access ports. |
| `push_config` / `push_clean` | `true`. |

Every field is explained in the [inventory reference](configuration/inventory.md). Then:

- Review `my-network/general/core/general.yml`. It sets SNMP, time zone, NTP, services, logging
  and NetFlow targets. **Change the SNMP community**, the time zone and the syslog/NetFlow
  addresses, or remove what you don't want.
- Review `my-network/firewall/global/`. These are the **lab's** firewall rules, a reasonable
  starting point but tied to the lab's address lists. Read
  [config files](configuration/config-files.md) and edit `1-adlv4_global.yml` (address lists)
  first. In particular **`ACL4_HOSTS_MGMT` must contain the address of the machine running
  the automation**, otherwise the first firewall push locks it out.
- Add the site's internet NAT in `my-network/firewall/site1/0-inet` (the global files have no
  source NAT), see the [example](configuration/config-files.md#the-lab-firewall-file-by-file).
- Create `my-network/dhcp/ipv4/site1/v4.yml` if you use the `dhcp` configlet. It holds the static
  leases; with none yet it must still contain the key: `/ip/dhcp-server/lease: []`.

Point `.env` at the new folder and generate offline again:

```bash
sed -i.bak 's/^CONFIG=.*/CONFIG="my-network"/' .env
.venv/bin/python 1-mikro-auto/mikro_main.py
```

Read `secrets/proposed/site1_global.yml` and `site1_fw.yml` until you're happy with them.

## 4. Prepare the router

On the router (RouterOS 7, terminal or WinBox):

```routeros
# 1. A full-rights user for the automation, and a read-only one for monitoring
/user add name=automation group=full password="<strong password>"
/user add name=monitor group=read password="<another password>"

# 2. API over TLS. The client only negotiates anonymous (ADH) ciphers: leave the
#    api-ssl service WITHOUT a certificate.
/ip service set api-ssl disabled=no port=8729 certificate=none
```

Put the credentials in `.env` (`MIKRO_USER`, `MIKRO_PASSWORD`, `MIKRO_READ_USER`,
`MIKRO_READ_PASSWORD`).

**Protect what the automation should not touch.** The first push removes every object in the
managed paths that isn't in the generated config, *unless its comment starts with one of the
`LOCALSTRING` prefixes* (`local_auto_` by default). Before pushing, comment:

```routeros
# examples: your WAN address, your default route, the rule that lets you in
/ip address set [find address="203.0.113.10/24"] comment="local_auto_wan_ip"
/ip route set [find dst-address="0.0.0.0/0" !dynamic] comment="local_auto_default_route"
/ip firewall filter set [find comment="defconf: accept established,related,untracked"] comment="local_auto_keep_established"
```

The managed paths are the ones in [`clean_routes.yml`](configuration/config-files.md#clean_routesyml)
plus the firewall (filter, NAT, mangle and address lists). DHCP clients, users, certificates and
system settings are not removed.

Also make sure that:

- Interface `ether1` is your internet uplink (the `internet` configlet adds `ether1` to
  `list_internet`), or adapt the generated config.
- Every certificate the config refers to exists on the router: `general.yml` sets
  `www-ssl certificate: '<domain>.crt'`. Import yours, or create a self-signed one with that name
  (`/certificate add name=example.int.crt common-name=example.int` then `sign`).

## 5. Dry run against the router

Edit `control/control.yml`:

```yaml
run_1_mikro_auto: true
mikro_auto_dry_run: true      # read the router, never write
mikro_auto_mode: 'global'     # 'firewall' = only firewall, 'global' = everything
```

Run it:

```bash
.venv/bin/python 1-mikro-auto/mikro_main.py
```

The automation logs in, reads the running config of every managed path, and writes
`web/Changes.md` / `Changes.html` with every **ADD**, **UPDATE** and **REMOVE** it would do (keys
and passwords masked). Read the REMOVE lines carefully: each one is something on the router that
the repository doesn't describe. Protect it with a `LOCALSTRING` comment, or add it to your config,
and run the dry run again until the list is what you expect.

> Running `mikro_main.py <device-name>` pushes a single device, but only the full run (no argument)
> writes `Changes.md`. With a one-device config folder the full run is just as fast.

## 6. First real push

Keep a way back in: physical/serial access or MAC-WinBox. Optionally take an export first
(`/export file=before-mikro-sdn`). Then set `mikro_auto_dry_run: false` and run again:

```bash
.venv/bin/python 1-mikro-auto/mikro_main.py
```

The run cleans and pushes the device and prints a *Push result* table (removed, updated, warnings,
errors). Run it a second time: a converged router shows nothing to update.

Set `mikro_auto_dry_run` back to `true` when you're not actively pushing.

## Where to go next

- Add a second router and get a WireGuard + BGP link between them: [Network design](network-design.md)
  and [Operations → add a site](operations.md#add-a-site).
- Turn on more configlets one by one: [Configlets](configlets.md).
- Run pushes from Git: [CI/CD](ci-cd.md).
