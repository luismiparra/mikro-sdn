# Inventory reference

The inventory is the folder `$CONFIG/inventory/`. It holds **one YAML file per device** (any name
ending in `.yml`/`.yaml`, read in name order). Each file has a top-level key equal to the device's
role, with a list containing the device:

```yaml
core:              # or: edge / external_edge
- name: "lab-mikro1"
  role: "core"     # keep it equal to the top-level key
  ...
```

Complete, working examples: [`config/inventory/`](../../config/inventory/), with cores
`lab-mikro1..3`, edges `lab-mikro4..6` and external peers `externalhost1..2`.

**Required?**: ✅ = always read, a missing key stops the run with a `KeyError`; a configlet name =
required when that configlet is enabled; – = optional.

- [Identity and placement](#identity-and-placement)
- [Push control](#push-control)
- [Management and endpoints](#management-and-endpoints)
- [Routing (WAN / BGP)](#routing-wan--bgp)
- [Addressing](#addressing)
- [Services (DHCP, DNS, NTP, probes)](#services-dhcp-dns-ntp-probes)
- [Features](#features)
- [`configlet`](#configlet)
- [`wg-vpn`: remote-access VPNs](#wg-vpn-remote-access-vpns)
- [`lan`: ports and VLANs](#lan-ports-and-vlans)
- [`netbox`](#netbox)
- [external_edge devices](#external_edge-devices)
- [Full example](#full-example)

---

## Identity and placement

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Unique device name. Becomes `/system identity`, and is part of WireGuard interface names, comments and file names. Keep it short, using `[a-z0-9-]`. |
| `role` | `core` \| `edge` \| `external_edge` | ✅ | See [roles](../concepts.md#roles). Same value as the file's top-level key. |
| `wan_order` | int ≥ 0 | – (warned) | Fixed position in the WAN mesh, which sets ports and transit subnets. **Unique and permanent**, see [wan_order](../network-design.md#wan_order-stable-slots-ports-and-transit-subnets). Assigned automatically, with a warning, when missing. |
| `site_id` | int 1–254 | ✅ | Unique site number: loopback `10.0.0.<site_id>`, VXLAN VNI prefix, edge port ranges. |
| `location` | string | ✅ | Unique short site name. SNMP location, name of the BGP filter chains (`filter_v4_<location>`), VPN client file names, NetBox site. |
| `description` | string | – | Free text (NetBox). |
| `api_version` | int | ✅ (`core`/`edge`) | RouterOS version without dots: 7.16 → `716`, 7.20 → `720`. Switches syntax: `is_responder` (715–716) vs `responder` (≥ 717), BGP `address_families` (≥ 719), BGP instances (≥ 720), VXLAN VTEP syntax (716–717). |
| `enabled` | bool | ✅ | Part of the WAN mesh, the port report and monitoring. `false` takes the device out of the mesh but it is still generated. |
| `monitoring` | bool | monitoring tool | Collect metrics from it (`2-mikro-monitoring`). |
| `device_model` | – | – | Unused. Use `netbox.device.device_model`. |

## Push control

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `push_config` | bool | ✅ | Add/update objects on the device. `false` = generate and document only. |
| `push_clean` | bool | ✅ | Remove objects that aren't in the proposal. `false` = add/update only. |
| `clean_config` | bool | ✅ | **Wipe mode**: the proposal is empty, so the clean step removes everything removable. Decommissioning only. |

## Management and endpoints

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mgmt_int` | IP / host | ✅ | Primary management address. The API-SSL connection is tried here first. Also the BGP router-id, the REST target of the monitoring/portal, and how the portal recognizes a router calling the boot hook. |
| `mgmt_ext` | IP / host | ✅ | Fallback management address (e.g. public DNS name), tried when `mgmt_int` fails. |
| `mgmt_aux` | IP / host | – | Alternative address used only with `mikro_main.py <device> <anything>` (migrations). The old spelling `mtmt_aux` is still read. |
| `external_endpoint` | IP / host | `wan`, `wg_vpn` | Public address peers and VPN clients connect to. For edges it is only needed by `wg_vpn`. |
| `external_ddns` | bool | `wan` | `external_endpoint` is a DNS name whose IP changes; peers re-resolve it every 30 min. |

## Routing (WAN / BGP)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `as` | string | `wan` | BGP AS number of the device, e.g. `'65110'`. Use a private ASN, unique per device. |
| `use_bfd` | bool | `wan` | BFD on BGP sessions (only when both ends have it). |
| `core_priority` | bool | `wan` | Routes through this core get one AS-path prepend instead of two, so it's preferred. See [BGP](../network-design.md#bgp). |
| `backbone_untrusted` | bool | `wan` | `true`: don't trust forwarded traffic coming from the backbone, so your firewall decides. |
| `ipv6_advertise_static` | bool | – | IPv6 sessions redistribute `connected,static` instead of only connected routes. |
| `core_internet_transit` | bool | `wan`, `internet` | This core is an internet exit for the other sites. See [internet transit](../network-design.md#internet-transit-and-policy-routing). |
| `wg_mtu` | string | `wan`, `wg_vpn`, `lan` (VXLAN) | MTU of the WireGuard interfaces, e.g. `'1280'`. VXLAN uses `wg_mtu − 50`. |

## Addressing

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subnetv4` | IPv4 `/16` | ✅ | The site's IPv4 block. |
| `subnetv6` | IPv6 `/96` | ✅ | The site's routed IPv6 block. |
| `subnetv6slaac` | IPv6 `/53` | ✅ | The site's SLAAC block (one `/64` per VLAN). |
| `gateway_number` | int | `lan`, `wg_vpn` | Host number of every gateway (`1` → `10.x.y.1`). |
| `disable-ipv6` | `"yes"` \| `"no"` | ✅ (`global` push) | Sets `/ipv6/settings disable-ipv6`. |

How these are cut into VLAN, VPN and transit subnets: [addressing plan](../network-design.md#addressing-plan).

## Services (DHCP, DNS, NTP, probes)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | string | `lan`, `radius_server`, docs | DHCP search domain. Zone of the generated PTR records, and default certificate name `radius.<domain>.crt`. |
| `dns1`, `dns2` | IP | `lan`, `netwatch`, `wg_vpn` | DNS servers handed out by DHCP and to VPN clients. |
| `dns1_fallback`, `dns2_fallback` | IP | `netwatch` | Where DNS queries to `dns1`/`dns2` are NATed while those are down. |
| `ntp1` | IP | `lan` | NTP server handed out by DHCP. |
| `dhcp_pool_start`, `dhcp_pool_end` | int | `lan` | Host range of every VLAN's DHCP pool (e.g. 100–250). |
| `lease-time` | string | `lan` | DHCP lease time, e.g. `"1d"`. |
| `internet_icmp_check1`, `internet_icmp_check2` | IP | `netwatch` | Internet probes (netwatch ICMP every 30 s). |
| `mqtt_netwatch_monitor` | bool | – | Publish netwatch RTTs over MQTT (needs `MQTT_SERVER`, see [environment](environment.md)). |

## Features

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enable_vxlan` | bool | `lan` | Join the inter-site VXLAN fabric. See [VXLAN](../network-design.md#vxlan-between-sites). |
| `enable_vxlan_to_vlan` | bool | `lan` (with VXLAN) | Bridge remote VXLAN segments into local VLANs `3<VNI>`. |
| `save_wg_files` | bool | `wg_vpn` | Write client `.conf` + QR `.png` files (and onboarding scripts) to `SECRETS/vpnconfig/`. |
| `wifi_profile` | string | `wifi` | Name of the WiFi profile file: `SECRETS/<wifi_profile>.yml`. |
| `radius_core` | bool | `wifi` | `true`: use the cores' user-manager as RADIUS (over the WAN links); `false`: use the servers of the WiFi profile. |

## `configlet`

List of enabled feature modules, in any order:

```yaml
configlet:
  - "general"
  - "autoupdate"
  - "internet"
  - "wan"
  - "fw"
  - "netwatch"
  - "radius_server"
  - "wg_vpn"
  - "lan"
  - "dhcp"
  - "wifi"        # needs "lan" as well
```

What each one creates: [Configlets](../configlets.md). An `external_edge` only uses `wan`.

## `wg-vpn`: remote-access VPNs

Used by the `wg_vpn` configlet. One entry per VPN server on this device:

```yaml
wg-vpn:
  - id: 1                       # unique per device; keys are stored as <device>_wgvpn_<id>
    name: mgmt_vpn              # interface int_w_vpn_<name>
    admin: true                 # clients get full access (input + forward accept)
    mgmt_vpn: true              # management VPN: protected objects + onboarding scripts
    persistent_keepalive_enable: true
    persistent_keepalive_seconds: '25'
    allowed_ips: '0.0.0.0/0, ::/0'   # AllowedIPs written into the client files
    disabled_peers: [2, 3]      # client numbers created but disabled
    subnet: 100                 # address index: 10.x.100.0/24 and …:10:x:64:0/112
    number_client: 10           # creates clients 2 … 9
    port: 30001                 # UDP listen port (opened in the firewall)
```

| Field | Description |
|-------|-------------|
| `id` | Key of the tunnel's secrets. Changing it generates new keys. |
| `name` | Interface `int_w_vpn_<name>`, and folder `<device>_<name>` of the client files. |
| `admin` | `true`: firewall accepts everything from this tunnel (input and forward) and the interface joins `list_wg_vpn_admins`. `false`: it joins `list_wg_vpn_default` and your firewall rules decide. |
| `mgmt_vpn` | Prefixes the tunnel's objects with the first `LOCALSTRING` value, so a push never removes them. It also opens input from the tunnel and, with `save_wg_files`, writes an onboarding script per client to `SECRETS/mgmt_export/`, see [onboarding](../operations.md#onboard-a-new-router-through-the-management-vpn). |
| `persistent_keepalive_enable`, `persistent_keepalive_seconds` | Keepalive on server peers and client files. |
| `allowed_ips` | What clients route into the tunnel (full tunnel `0.0.0.0/0, ::/0` or split). |
| `disabled_peers` | Client numbers to disable without losing their keys. |
| `subnet` | Index of the tunnel's `/24` / `/112` (< 250, not a VLAN id). Server `.1`, clients `.2` and up. |
| `number_client` | Clients `2 … number_client − 1` are created. |
| `port` | WireGuard listen port. Unique per device. |

## `lan`: ports and VLANs

Used by the `lan` configlet:

```yaml
lan:
  safe_ports: ['ether2']        # access ports in VLAN 1
  trunk_ports: ['ether3']       # trunks carrying every VLAN
  trunk_ports_isolated: []     # trunks that are always isolated (native VLAN 999)
  isolated_trunk: true         # native VLAN of trunk_ports: 999 (true) or 1 (false)
  access_ports:                 # access ports in any VLAN
    - port: 'ether4'
      vlan: '2'
  vlans:
    - id: 1
      name: 1safe
      ipv6: true
      ipv6slaac: false
      ipv4_vip_pool: ['10.21.91.0/29']
      ipv6_vip_pool: []
```

| Field | Description |
|-------|-------------|
| `safe_ports` | Ports added untagged to VLAN 1. May be empty/null. |
| `access_ports` | `{port, vlan}` pairs: untagged ports in that VLAN. |
| `trunk_ports` | Ports tagged in every VLAN. Their native VLAN depends on `isolated_trunk`. |
| `isolated_trunk` | `true`: trunk native VLAN is **999** (`isolated`, no IP), so untagged frames go nowhere. `false`: native VLAN 1, untagged = VLAN 1. |
| `trunk_ports_isolated` | Trunks that always use native VLAN 999, whatever `isolated_trunk` says. |

The older misspelled keys `issolated_trunk` and `trunk_ports_issolated` are still accepted.
| `vlans` | The site's VLANs, see below. |

The configlet creates one VLAN-filtering bridge **`bridge-vlans`** (bridge pvid 999) with all those
ports, and the interface list `list_inside` with all VLAN interfaces. Ports that aren't listed
are not touched.

Each **VLAN**:

| Field | Description |
|-------|-------------|
| `id` | VLAN id **and** address index: VLAN 3 → `10.x.3.0/24`. 1–249. |
| `name` | Interface name and part of every comment. The lab uses `<id><name>` (`1safe`, `2dmz`, …). |
| `ipv6` | Add the routed IPv6 gateway address (`/112`) to the VLAN. (The DHCPv6 server and its pool are created for every VLAN.) |
| `ipv6slaac` | Add the SLAAC `/64` gateway address, which RouterOS advertises to clients by default. |
| `ipv4_vip_pool` | Extra IPv4 subnets whose **every host address** is added to the VLAN interface (e.g. as DNAT targets or service IPs). Max `/26`. Empty or null for none. |
| `ipv6_vip_pool` | Same for IPv6. |

## `netbox`

Only read by the [NetBox sync](../tools/netbox.md):

```yaml
netbox:
  device:
    device_model: mikrotik-chr     # NetBox device-type slug; "mikrotik-chr" reads the serial from /system/license
  organization:
    region: "LAB"                 # NetBox region
    site_group: site_lab             # NetBox site group
```

## external_edge devices

A Linux peer ([details](../tools/external-peers.md)) uses a subset of fields plus three of its own:

| Field | Description |
|-------|-------------|
| `external_wg_main_port` | Fixed WireGuard listen port on the host (instead of `51820 + slot`). |
| `allow_out_prefix_v4` | IPv4 prefix(es) the cores accept from this peer, e.g. `"10.91.222.200/32"`. |
| `allow_out_prefix_v6` | IPv6 prefix(es) the cores accept from this peer. |

Plus `name`, `role`, `wan_order`, `site_id`, `location`, `enabled`, `as`, `use_bfd`, `wg_mtu`,
`backbone_untrusted`, `mgmt_int`, `subnetv4`, `subnetv6`, `subnetv6slaac` and `configlet: ["wan"]`. See
[`config/inventory/externalhost1.yml`](../../config/inventory/externalhost1.yml).

## Full example

[`config/inventory/lab-mikro1.yml`](../../config/inventory/lab-mikro1.yml) (a core with every
configlet and three VPNs) and
[`config/inventory/lab-mikro4.yml`](../../config/inventory/lab-mikro4.yml) (an edge with
`external_ddns`, VXLAN and `radius_core`).
