# NetBox sync (`4-netbox`)

Publishes the network described by the inventory, and the addresses the automation generated, to
[NetBox](https://netbox.dev/) as DCIM and IPAM objects. The repository stays the source of truth:
NetBox is a read-only view of it (one-way sync).

## What is synced

In dependency order (`netbox_main.build_netbox`):

| NetBox object | From |
|---------------|------|
| Tags | `NETBOX_TAG` (ownership) and `MSDN-GLOBAL` (shared objects) |
| RIR | a private RIR for the RFC 1918 / ULA space |
| Site groups | `site_prod`, `site_lab` (referenced by `netbox.organization.site_group`) |
| Regions | `netbox.organization.region` |
| ASNs | `as` |
| Sites | `location`, `site_id`, `description` |
| Device roles | `role` |
| Devices | `name`, role, site, device type (`netbox.device.device_model` = device-type slug), serial (read live from the router) |
| VLANs | `lan.vlans` |
| Interfaces | VLANs, WireGuard interfaces and others found in the proposals |
| Prefixes | the site blocks and every derived VLAN, VPN, transit prefix |
| IP addresses | every address in the device's generated proposal, with DNS name `<interface>-<device>.<domain>.` |
| IP ranges | DHCP pools |

**Ownership**: every object created gets the `NETBOX_TAG` tag. Only objects carrying that tag
are updated or deleted. Objects you create by hand in NetBox are never touched, and an object
with the same key but without the tag is left alone (warning). Use one tag per environment
(`MSDN-LAB`, `MSDN-PROD`) to sync several inventories into one NetBox.

At the end it prints a table of created / updated / deleted / unchanged per endpoint.

## Setup

1. NetBox 3.x or newer, and an API token with write permissions.
2. Import the device types you reference. MikroTik definitions are in the
   [NetBox device-type library](https://github.com/netbox-community/devicetype-library); four
   extra ones are in [`4-netbox/data/device_type/`](../../4-netbox/data/device_type/). Create a
   `mikrotik-chr` type for virtual routers.
3. `.env` (see [environment](../configuration/environment.md#netbox-4-netbox)):

   ```bash
   NETBOX_URL="http://netbox.example.int:8000"
   NETBOX_TOKEN="..."
   NETBOX_TAG="MSDN-LAB"
   NETBOX_DRYRUN=1            # first run: only log
   MIKRO_READ_USER="monitor"  # to read serial numbers
   MIKRO_READ_PASSWORD="..."
   ```

4. Run the automation first (any mode, `config` is enough): addresses and interfaces are read
   from `SECRETS/proposed/`.
5. Run the sync, check the report, then set `NETBOX_DRYRUN=` (empty) and run again:

   ```bash
   .venv/bin/python 4-netbox/netbox_main.py
   ```

Serial numbers are read over REST from `/system/routerboard`, or `/system/license` for
`mikrotik-chr`. Unreachable routers get serial `none`.

## Known issues

See [testing → known bugs](../testing.md#known-bugs): WireGuard VPN prefixes are skipped for
devices without LAN VLANs, and some prefixes can be generated twice.
