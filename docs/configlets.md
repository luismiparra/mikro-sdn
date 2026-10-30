# Configlets

A configlet is a feature module enabled per device through the inventory's `configlet` list. This
page lists what each one puts on the router, which inventory fields and files it reads, and its
caveats. Comment names are given so you can find the objects on the router or in
`SECRETS/proposed/`.

| Configlet | Module | Reads |
|-----------|--------|-------|
| [`general`](#general) | `mikro_shared.load_config` | `config/general/<role>/` |
| [`fw`](#fw) | `mikro_shared.load_config` | `config/firewall/global/`, `config/firewall/<device>/` |
| [`lan`](#lan) | `mikro_lan.py` | `lan`, addressing, DHCP fields, other devices (VXLAN) |
| [`dhcp`](#dhcp) | `mikro_shared.load_config_by_device` | `config/dhcp/ipv4/<device>/` |
| [`wan`](#wan) | `mikro_wan.py` | the whole inventory, `SECRETS/secrets.json` |
| [`wg_vpn`](#wg_vpn) | `mikro_wg.py` | `wg-vpn`, `SECRETS/secrets.json` |
| [`internet`](#internet) | `mikro_internet.py` | role, `core_internet_transit`, the WAN links |
| [`netwatch`](#netwatch) | `mikro_netwatch.py` | DNS and probe fields, `MQTT_*` |
| [`autoupdate`](#autoupdate) | `mikro_autoupdate.py` | `BOOT_UPDATE_URL`, `MGMT_CHECK_HOSTS` |
| [`radius_server`](#radius_server) | `mikro_radius_server.py` | `SECRETS/radius_users.yml`, `radius_routers.yml` |
| [`wifi`](#wifi) | `mikro_wifi.py` | `SECRETS/<wifi_profile>.yml`, `SECRETS/mac_addr.yml` |

---

## `general`

Loads every file of `config/general/<role>/` as-is: services, DNS, SNMP, clock, NTP, cloud/DDNS,
logging, traffic-flow, BFD, identity. Mostly `use_set` singletons. See
[general files](configuration/config-files.md#general-files) for the fields filled in by code and
what to review before use.

## `fw`

Loads the global and per-device firewall files. Format, address lists and ordering:
[firewall files](configuration/config-files.md#firewall-files).

## `lan`

Builds the site's switching and L3 edge:

| Objects | Comments |
|---------|----------|
| Loopback `10.0.0.<site_id>/32` on `lo` (enabled only with VXLAN) | `ip_lo_10.0.0.<site_id>` |
| Bridge `bridge-vlans` (VLAN filtering, pvid 999) | `bridge-vlans` |
| Interface list `list_inside` + one member per VLAN | `int_list_inside`, `list_item_int_v_<vlan>` |
| VLAN interface per VLAN, plus `isolated` (999) | `vlan_<name>`, `vlan_isolated` |
| Bridge ports: trunks, safe ports, access ports | `int_br_TRUNK_<port>`, `int_br_1SAFE_access_<port>`, `int_br_vlan_<vlan>_access_<port>` |
| Bridge VLAN table (tagged/untagged per port) | `int_br_vlan_<id>` |
| IPv4 gateway, IPv6 gateway (`ipv6`), SLAAC address (`ipv6slaac`) | `ip_<vlan>_<address>`, `…_slaac` |
| Extra service IPs (`ipv4_vip_pool`, `ipv6_vip_pool`) | `ip_VIP_<vlan>_<ip>`, `ipv6_VIP_<vlan>_<ip>` |
| IPv4 and IPv6 pools, DHCP and DHCPv6 servers, DHCP networks (gateway, DNS, NTP, domain) | `pool_<subnet>`, `dhcpV4_<vlan>`, `dhcpV6_<vlan>` |
| Firewall: accept DHCP/DHCPv6 on each VLAN | `fw_in_dhcp_…` |
| VXLAN (with `enable_vxlan`): local and remote VXLANs, VTEPs, bridge ports, firewall, optional local VLANs `3<VNI>` | `vxlan_local_…`, `vxlan_remote_…`, `vtep_…` |

Physical ports not listed in `lan` are left alone. Details of the fields:
[`lan`](configuration/inventory.md#lan-ports-and-vlans); VXLAN:
[network design](network-design.md#vxlan-between-sites).

## `dhcp`

Static leases from `config/dhcp/ipv4/<device>/`. The folder must exist when the configlet is
enabled. Format: [DHCP lease files](configuration/config-files.md#dhcp-lease-files).

## `wan`

The backbone: for every link of the device (see [the WAN mesh](network-design.md#the-wan-mesh)):

- interface lists `list_wireguard_main`, `list_external_wireguard_main`,
- WireGuard interface + peer (`int_w_<a>_main_to_<b>_main`, `int_wg_peer_…`),
- IPv4 `/30` and IPv6 `/127` transit addresses (`ip_wg_<ip>_<prefix>`),
- BGP instance (≥ 7.20), BGP IPv4 and IPv6 connections (`bgp_v4_…`, `bgp_v6_…`), routing filters,
- firewall: WireGuard port, BGP and BFD from the peer, forward from the backbone (unless
  `backbone_untrusted`),
- schedulers: DDNS re-resolve (`script_DDNS_wg_peer_…`, with `external_ddns`) and, on edges, the
  listen-port randomizer (`script_PORT_RANDOM_wg_peer_…`),
- a netwatch probe per link (with MQTT RTT publishing if enabled).

Keys are generated on first use and stored in `SECRETS/secrets.json`. It also writes the external
peers' files, see [external peers](tools/external-peers.md).

## `wg_vpn`

For every entry of `wg-vpn` (see [the reference](configuration/inventory.md#wg-vpn-remote-access-vpns)):

- interface lists `list_wg_vpn_admins` and `list_wg_vpn_default`,
- WireGuard interface `int_w_vpn_<name>` on `port`, server address `.1` (IPv4 and IPv6),
- one peer per client (`peer_wgvpn_<name>_<n>`) with its `/32` and `/128`, preshared key, optional
  keepalive, disabled when listed in `disabled_peers`,
- firewall: accept the UDP port; full input/forward accept for `admin` tunnels, input accept for
  `mgmt_vpn` tunnels,
- with `save_wg_files: true`: client files `SECRETS/vpnconfig/<device>_<name>/<MGMT|ADM|USR>_<location>_<n>.conf`
  plus a QR code `.png`, and for management VPNs a RouterOS onboarding script per client in
  `SECRETS/mgmt_export/mikro_mgmt_<n>.txt`.

Objects of `mgmt_vpn` tunnels are prefixed with the first `LOCALSTRING` value, so a push never
removes your management path.

## `internet`

On devices that are not themselves an internet transit (every edge, and cores with
`core_internet_transit: false`):

- routing table `internet_vpn`, routing rules, a default route through the transit core when one
  exists (`ip_route_internet_vpn`),
- mangle marks for `ACL4_HOSTS_VPN_EXIT` and `ACL4_PORTAL_VPN` to non-private destinations.

On every device:

- interface list `list_internet` with `ether1`,
- for each core it has a link to: routing table, rule and route `core_transit_<core>`, mangle mark
  for `ACL4_EXIT_VIA_<core>`, and a netwatch probe that disables the mark when the link is down.

See [internet transit](network-design.md#internet-transit-and-policy-routing). **Assumes the uplink
is `ether1`.**

## `netwatch`

- DNS fallback: NAT rules `NAT_FALLBACK_DNS_1/2` (DNS from `10.0.0.0/8` to `dns1`/`dns2` →
  `dns1_fallback`/`dns2_fallback`), enabled by netwatch (`netwatch_dns1/2`, 10 s) only while the
  primary is down.
- TCP probes of DNS (`netwatch_tcp_dns_1/2`) and ICMP probes of `internet_icmp_check1/2`
  (`netwatch_internet1/2`), every 30 s.
- With `mqtt_netwatch_monitor: true` and `MQTT_SERVER` set: the broker `auto_mqtt_broker_1`, and
  the probes publish their average RTT to `mikrotik/rtt-avg/<device>/<target>`.

## `autoupdate`

System schedulers:

| Scheduler | When | What |
|-----------|------|------|
| `script_autoupdate` | daily 03:10, **created disabled** | Check for and install RouterOS updates. Enable it on the router if you want it. |
| `script_clean_usermanagersessions` | at boot and daily | Clear user-manager sessions. |
| `script_enable_all_wireguard_interfaces` | at boot and daily | Re-enable every WireGuard interface (RouterOS disables one on a port clash). |
| `script_boot_get_config` | 5 min after boot | Fetch `BOOT_UPDATE_URL` so the portal pushes this router's config. Only when `BOOT_UPDATE_URL` is set. |
| `script_auto_reboot_if_mgmt_lost` | hourly | Ping every `MGMT_CHECK_HOSTS` host 20 times; reboot when none answers. Only when `MGMT_CHECK_HOSTS` is set. |

## `radius_server`

Turns the router into a RADIUS server with RouterOS **user-manager** (the package must be
installed):

- enables user-manager with certificate `RADIUS_CERTIFICATE` (default `radius.<domain>.crt`),
- one user per entry of `SECRETS/radius_users.yml` (`radius_user_<user>`),
- one RADIUS client (NAS) per entry of `SECRETS/radius_routers.yml` (`radius_router_<name>_<ip>`).

Formats: [`secrets.example/`](../secrets.example/). Typically enabled on cores, with edges using
`radius_core: true`.

## `wifi`

For routers with the **legacy wireless package** (`/interface/wireless`). Requires `lan`.

- RADIUS clients: the user-manager of every core over the WAN links (`radius_core: true`, secret
  `RADIUS_SECRET`) or the servers listed in the WiFi profile,
- security profiles and wireless interfaces copied 1:1 from `SECRETS/<wifi_profile>.yml`,
- wireless interfaces added to `list_inside` and to the bridge in their `vlan_id`,
- MAC access list from `SECRETS/mac_addr.yml`.

The profile format is in [`secrets.example/wifi.yml`](../secrets.example/wifi.yml). The newer
`/interface/wifi` (wifiwave2) package isn't supported.
