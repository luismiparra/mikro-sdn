# Network design

mikro-sdn implements one specific design. This page describes it: how addresses are allocated,
how the WireGuard backbone is built, how BGP is filtered, and how VXLAN and internet transit work.
All examples use the bundled lab (`config/`).

- [Addressing plan](#addressing-plan)
- [The WAN mesh](#the-wan-mesh)
- [`wan_order`: stable slots, ports and transit subnets](#wan_order-stable-slots-ports-and-transit-subnets)
- [BGP](#bgp)
- [VXLAN between sites](#vxlan-between-sites)
- [Internet transit and policy routing](#internet-transit-and-policy-routing)
- [Constraints and limits](#constraints-and-limits)

---

## Addressing plan

Each site declares three blocks in the inventory. Everything else is derived from them
(`mikro_shared.prepare_sdn`):

```yaml
subnetv4:      "10.21.0.0/16"                        # IPv4, exactly a /16
subnetv6:      "2001:db8:10:0:10:21:0:0/96"        # IPv6 routed, exactly a /96
subnetv6slaac: "2001:db8:10:8800::/53"              # IPv6 for SLAAC, exactly a /53
gateway_number: 1                                     # host number of every gateway
```

The convention used in the lab embeds the IPv4 `/16` in the IPv6 `/96`
(`10.21.0.0` ↔ `…:10:21:0:0`), which makes addresses easy to read. It is a convention, not a
requirement.

### Index → subnet

The `/16` is cut into `/24`s, the `/96` into `/112`s and the `/53` into `/64`s. **Index *N*** is
the same number everywhere:

| Index *N* | IPv4 (`/24`) | IPv6 (`/112`) | IPv6 SLAAC (`/64`) | Used by |
|-----------|--------------|---------------|--------------------|---------|
| VLAN id (1–249) | `10.21.N.0/24`, gateway `.1` | `…:10:21:N:0/112`, gateway `::1` | `2001:db8:10:8800+N::/64` | VLAN *N* of the `lan` configlet |
| `wg-vpn[].subnet` | `10.21.N.0/24`, server `.1`, clients `.2`… | `…:10:21:N:0/112` | – | Remote-access VPN servers |
| 250 | `10.21.250.0/24` → 64 × `/30` | `…:10:21:fa:0/112` → 64 × `/127` | – | WAN transit links |

(*N* is written in hex in IPv6: VLAN 1 → `:1:`, VPN subnet 100 → `:64:`, transit 250 → `:fa:`.)

Example for `lab-mikro1` (`10.21.0.0/16`, `gateway_number: 1`, pool 100–250):

| What | Address |
|------|---------|
| VLAN 1 `1safe` gateway | `10.21.1.1/24`, `2001:db8:10:0:10:21:1:1/112` |
| VLAN 1 DHCP pool | `10.21.1.100 – 10.21.1.250` |
| VLAN 2 `2dmz` SLAAC prefix | `2001:db8:10:8802::/64` (router `::1`) |
| `mgmt_vpn` (`subnet: 100`) server / first client | `10.21.100.1/24` / `10.21.100.2` |
| Transit pool | `10.21.250.0/30`, `.4/30`, … `.252/30` |
| Loopback (VXLAN VTEP) | `10.0.0.1/32` (`10.0.0.<site_id>`) |

### Rules that follow from this

- VLAN ids and VPN `subnet` indexes must be **below 250** and must not collide with each other.
- Two sites must never share a `/16`, `/96` or `/53`.
- `site_id` must be unique and between 1 and 254: it's the loopback's last octet and part of
  every VXLAN VNI.
- Site blocks don't have to be in `10.0.0.0/8`, but parts of the design assume it: the edge BGP
  filters (`10.0.0.0/8` prepends), the loopbacks (`10.0.0.x`), the DNS fallback NAT
  (`src 10.0.0.0/8`) and the web portal's client lookup. Staying inside `10.0.0.0/8` is the
  supported setup.

## The WAN mesh

The `wan` configlet builds the backbone (`mikro_wan.py`). The links are:

- **core ↔ core**, between every pair of enabled cores (full mesh),
- **edge → core**, from every enabled edge to every enabled core,
- **external_edge → core**, from every external Linux peer to every enabled core.

Edges never connect to other edges. Their traffic to another edge goes through a core.

Each link is its own WireGuard interface on each end, named after both devices:

```
/interface/wireguard        int_w_lab-mikro4_main_to_lab-mikro1_main
/interface/wireguard/peers  int_wg_peer_lab-mikro4_main_to_lab-mikro1_main
/ip/address                 10.24.250.1/30   (ip_wg_10.24.250.1_30)
/ipv6/address               2001:db8:10:0:10:24:fa:0/127
/routing/bgp/connection     bgp_v4_lab-mikro1_main__lab-mikro4_main  (+ bgp_v6_…)
```

Properties of every link:

- A **private key per end and a preshared key per link**, generated once and kept in
  `SECRETS/secrets.json`. Keys don't rotate by themselves, see
  [secrets](secrets-and-outputs.md#key-lifecycle).
- `allowed-address=0.0.0.0/0,::/0`: what is reachable through the tunnel is decided by BGP, not by
  WireGuard.
- `persistent-keepalive=10s` and the MTU from `wg_mtu` (1280 in the lab, safe on every path).
- Firewall rules on both ends that accept the WireGuard UDP port, BGP and BFD from the transit
  peer.
- All main interfaces go to the interface list `list_wireguard_main`, which BFD and the firewall
  use.

### Who connects to whom

- **core ↔ core**: both ends have the other's `external_endpoint` as endpoint.
- **edge → core**: only the edge has an endpoint. The core side is a *responder*, so edges can sit
  behind NAT and dynamic IPs. Every 6 hours the edge moves its local listen port to a random port
  in a range derived from the core's `site_id`
  (`script_PORT_RANDOM_wg_peer_…`), which helps against stale NAT mappings and carrier
  throttling.
- **external_edge → core**: like an edge. The host's listen port can be pinned with
  `external_wg_main_port`.

### Dynamic endpoints

If a device's `external_endpoint` is a DNS name that changes (home connection with DDNS), set
`external_ddns: true` on it. Its peers then get a scheduler
(`script_DDNS_wg_peer_…`, every 30 min) that re-resolves the name and updates the peer's endpoint
address when it changed.

## `wan_order`: stable slots, ports and transit subnets

Every device has a fixed `wan_order` (0, 1, 2, …). On a device, each peer takes a **slot**: the
peer's position in the `wan_order` sequence with the device itself left out:

```
slot of peer B on device A  =  wan_order(B) − 1   if wan_order(B) > wan_order(A)
                               wan_order(B)       otherwise
```

The slot fixes, on that end of the link:

- the **WireGuard listen port**: `51820 + slot`,
- the **transit subnet**: `/30` number *slot* of the transit pool (and the matching `/127`).

The transit subnet of a link comes from the pool of one end only: the edge for edge → core links,
and the core with the lower `wan_order` for core ↔ core links.

See the result with the port report (read-only, no secrets needed):

```console
$ python 1-mikro-auto/mikro_ports.py
lab-mikro1  (wan_order 0)
  peer             slot  listen  peer port  transit v4
  lab-mikro2          0   51820      51820  10.21.250.1/30
  lab-mikro3          1   51821      51820  10.21.250.5/30
  lab-mikro4          2   51822      51820  10.24.250.2/30
  …
$ python 1-mikro-auto/mikro_ports.py lab-mikro4 csv     # one device, as CSV
```

> [!IMPORTANT]
> **`wan_order` is permanent.** Changing it on a deployed device moves the ports and transit
> addresses on both ends of all its links. Adding a device with a new, higher `wan_order` doesn't
> touch existing links. Removing a device leaves a gap: don't reuse its number.
>
> A device without `wan_order` gets one automatically (after the highest pinned one, by name) and
> a warning tells you which number to write into its file. Pin it before the first push.
> Two devices with the same `wan_order` stop the run.

Up to 64 slots exist per device (the transit pool has 64 subnets), so a core can have at most 64
links.

## BGP

Every MikroTik device runs eBGP with its own AS (`as`, e.g. `65110`) over every link, with
separate IPv4 and IPv6 sessions. With `api_version >= 720` a BGP instance
(`bgp_instance_main_<device>`, router-id = `mgmt_int`) is created and the connections refer to it.
With `use_bfd: true` on both ends, BFD watches the session.

Routes are controlled with routing filters (`/routing/filter/rule`):

| Filter chain | Rule | Used as |
|--------------|------|---------|
| `filter_v4_<location>` | accept the site's own `subnetv4` and loopback | what an **edge** advertises, and what a core accepts **from** that edge |
| `filter_v6_<location>` | accept the site's own `subnetv6` and `subnetv6slaac` | same for IPv6 |
| `filter_v4_any` / `filter_v6_any` | accept `10.0.0.0/8` (IPv6: any) with **2** extra AS-path prepends | what cores advertise and normally accept |
| `filter_v4_any_priority` / `_v6_` | same with **1** prepend | accepted from a core with `core_priority: true` |
| `filter_external_v4_<location>` | accept `allow_out_prefix_v4` + loopback | what a core accepts from an external peer |

Effects:

- **Edges only originate their own site.** A misconfigured edge can't attract other sites'
  traffic.
- **Cores carry everything** and are the transit between edges.
- **`core_priority: true`** on a core makes the routes learned through it shorter, so the rest of
  the network prefers it. Use it for the core with the best connectivity.
- **`ipv6_advertise_static: true`** also redistributes the device's static IPv6 routes.

### Trusting backbone traffic: `backbone_untrusted`

By default every router accepts forwarded traffic arriving from its WAN WireGuard interfaces
(`fw_v4_forward_wgmain_in_…`), which makes the backbone a trusted zone. With `backbone_untrusted: true`
on a device that blanket rule is not created, and traffic from the backbone is filtered by your
firewall rules like any other.

## VXLAN between sites

With `enable_vxlan: true` on two or more devices, each VLAN of each site becomes a VXLAN segment
that the other VXLAN-enabled sites can join:

- The loopback `10.0.0.<site_id>/32` is enabled and used as the VTEP. Loopbacks reach each other
  through BGP.
- **VNI = `<site_id><vlan id>`**: VLAN 2 of site 4 is VNI `42`.
- Each site creates a local VXLAN for each of its VLANs (bridged into that VLAN) and a remote VXLAN
  for each VLAN of the other sites, with VTEPs pointing to their loopbacks.
- With `enable_vxlan_to_vlan: true`, each remote segment is also bridged into a **local VLAN
  `3<VNI>`** (remote VNI 42 → local VLAN 342), tagged on the trunk ports. A switch on any site can
  then reach a VLAN of another site.
- VXLAN MTU is `wg_mtu − 50` (VXLAN overhead). The firewall accepts VXLAN (UDP 4789) only from
  the transit subnets of the other VXLAN sites.

## Internet transit and policy routing

The `internet` configlet sets up two mechanisms.

**1. Send selected hosts out through a core.** A core with `core_internet_transit: true` is an
internet exit for the others. On every other device:

- a routing table `internet_vpn` with a default route through the transit core's WAN link
  (`ip_route_internet_vpn`),
- mangle rules that mark traffic **from** `ACL4_HOSTS_VPN_EXIT` (static list, from your
  firewall files) and `ACL4_PORTAL_VPN` (managed by the [web portal](tools/web-portal.md))
  to non-private destinations with routing mark `internet_vpn`.

So a host on any site can browse "from" the transit core's location, either permanently (address
list in the repo) or self-service (web portal).

**2. Choose the exit core per host, with failover.** For every core a device has a WAN link to,
it gets a routing table `core_transit_<core>` with a default route through that link, and a
mangle rule that marks traffic from the address list **`ACL4_EXIT_VIA_<core>`** to non-private
destinations into that table. Put a host in `ACL4_EXIT_VIA_lab-mikro2` (in your firewall files)
and its internet traffic leaves through `lab-mikro2`. A netwatch probe pings the link every 10 s
and disables the mangle rule while the core is unreachable, so the host falls back to the local
internet.

Independently, the `netwatch` configlet NATs DNS queries to `dns1_fallback`/`dns2_fallback`
while `dns1`/`dns2` are unreachable.

## Constraints and limits

| Limit | Value | Why |
|-------|-------|-----|
| Prefix sizes | `/16`, `/96`, `/53`, exactly | subnet derivation is positional |
| VLAN id, VPN `subnet` | < 250 | index 250 is the transit pool |
| `site_id` | 1–254, unique | loopback octet, VNI, edge port ranges |
| Links per device | 64 | transit subnets per pool |
| WireGuard ports in use | 51820 … 51820+63 | `51820 + slot` |
| VPN clients per tunnel | `number_client − 2` (peers `.2` … `.number_client−1`), ≤ 240 recommended | one `/24` per tunnel |
| Extra service IPs per VLAN (`ipv4_vip_pool`) | 62 | `/26` maximum |
| RouterOS | 7.x; `api_version` switches syntax at 7.15/7.16, 7.17, 7.19, 7.20 | API differences |
