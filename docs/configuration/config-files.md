# Config files

Besides the inventory, the `$CONFIG` folder holds plain RouterOS objects written as YAML:

```
config/
├── inventory/                 one file per device, see inventory.md
├── firewall/
│   ├── global/                firewall for every device with the "fw" configlet
│   └── <device>/              extra firewall for one device (optional)
├── general/
│   ├── core/                  baseline for cores  ("general" configlet)
│   └── edge/                  baseline for edges
├── dhcp/ipv4/<device>/        static DHCP leases   ("dhcp" configlet)
└── clean_routes.yml           RouterOS paths the clean step manages
```

- [File format](#file-format)
- [Firewall files](#firewall-files)
- [Rule order](#rule-order)
- [Config file order](#config-file-order)
- [General files](#general-files)
- [DHCP lease files](#dhcp-lease-files)
- [`clean_routes.yml`](#clean_routesyml)
- [The lab firewall, file by file](#the-lab-firewall-file-by-file)

---

## File format

Every file is a YAML mapping of **RouterOS path → list of objects**. A file may contain several
paths:

```yaml
/ip/firewall/filter:
- comment: "v4_input_accept_tcp_mgmt"        # identity of the object, see below
  order: top                   # firewall only: top | bot | posi
  chain: input
  src_address_list: ACL4_HOSTS_MGMT
  dst_port: '21,22,23,80,443,8291,8728,8729,2000'
  protocol: tcp
  action: 'accept'

/ip/firewall/nat:
- comment: "dnat_web"
  order: top
  chain: dstnat
  ...
```

Object fields are RouterOS property names. Write them with underscores (`dst_address`) or dashes
(`dst-address`); both work. Quote values RouterOS treats as strings (`'false'`, `'80,443'`).

Special keys, consumed by the automation and not sent to the router:

| Key | Meaning |
|-----|---------|
| `comment` | The object's identity. Unique per path. Objects are matched, updated and cleaned by it. Required unless `use_set` is `true`. |
| `use_set` | `true`: don't add/remove, just **set** the object: a singleton (`/ip/dns`, `/snmp`), an object found by `name` (`/ip/service`), or one by `numbers`. Use `"false"`/`false` for normal objects. |
| `order` | Firewall only: `top`, `bot` or `posi`, see [rule order](#rule-order). |
| `posi` | Firewall only, with `order: posi`: target position (0-based). |
| `vlan_src` | `/system/logging/action` and `/ip/traffic-flow/target`: replaced by the gateway IPv4 of that VLAN, as the source address. |

When two objects in the same path share a comment, the first one wins and a warning is logged.

## Firewall files

The `fw` configlet loads every file of `firewall/global/`, then every file of
`firewall/<device name>/` if that folder exists (otherwise a warning: *No specific FW config*).
Supported paths: `/ip/firewall/filter|nat|mangle|address-list` and the same under `/ipv6/`.

### Address lists

An address list is written once with all its addresses. The comment is the list name:

```yaml
/ip/firewall/address-list:
- comment: "ACL4_HOSTS_MGMT"
  address:
  - '127.0.0.1'
  - '10.21.100.0/24'      # management VPN
  - '203.0.113.17'         # a jump host
```

Each address becomes its own entry with list `ACL4_HOSTS_MGMT` and comment
`ACL4_HOSTS_MGMT_<address>`. Removing an address from the file removes that entry on the
next push.

Rules then refer to lists with `src_address_list` / `dst_address_list` (prefix `!` to negate).
The lab follows a naming convention: `ACL4_NETS_*` for networks, `ACL4_HOSTS_*` for hosts, and
`ACL4_`/`ACL6_` for the address family.

### Rules created by configlets

Several configlets add their own firewall rules: WireGuard ports, BGP/BFD on transit links, VPN
access, DHCP, VXLAN, DNS fallback NAT, internet marks. They come **after** the rules of your files
in the push order and use the same comment-based identity. You don't need to write them.

## Rule order

RouterOS evaluates firewall rules top to bottom, so the order matters. The push handles it in
three passes:

| `order` | Behaviour |
|---------|-----------|
| `top` | Normal rules. A missing rule is **appended** at the end, in the order the files are read. An existing rule is updated in place and keeps its position. |
| `bot` | Rules that must stay **last** (e.g. a final log-and-drop). On every push they're removed and appended again at the end, after all `top` rules. |
| `posi` | Rules that must sit at a fixed index. They're first handled like `top`, then **moved** to position `posi`, one after another in reading order. |

Typical layout: put fast-path rules (accept established/related, drop invalid) as `posi: '0'`,
`'1'`, … so they stay first even when new rules are appended. Put your accepts as `top` and the
final drop as `bot`.

> Moves are applied one after another, so a later move can shift a rule moved earlier. Rules with
> the same or close `posi` in different files end up in an order that depends on which file is
> read first, which is why the file order is fixed (next section).

## Config file order

The files of `firewall/global/`, `firewall/<device>/`, `general/<role>/` and
`dhcp/ipv4/<device>/` are read in a fixed order, the same on every machine:

1. files whose name starts with a number and a dash, by that **number** (`1-`, `2-`, … `10-`, `100-`),
2. then the others, by name.

```
1-adlv4_global.yml
1-adlv6_global.yml
2-fwv4_contrack.yml
...
10-fw4_webapp.yml
100-fwv4_log_and_drop.yml
v4.yml
```

That order **is** the order of the rules on the device (`top` rules are appended in it, `posi`
moves happen in it). To place a rule earlier or later, change its file's numeric prefix or its
`posi`. Files with the same prefix are ordered by name. The inventory folder is read in plain
name order.

## General files

`general/<role>/` (every file, in the order above) is the static baseline of the `general`
configlet. A core gets `general/core/`, an edge `general/edge/`. Mostly singletons with `use_set`:

```yaml
/ip/dns:
- use_set: "true"
  allow_remote_requests: "no"

/ip/service:
- use_set: "true"
  name: "api-ssl"            # found by name, then set
  disabled: 'false'
  port: '8729'

/system/ntp/client/servers:
- comment: "ntp-pool"          # a normal, comment-identified object
  use_set: "false"
  address: "pool.ntp.org"
```

A few paths are filled in by the code:

| Path | Filled with |
|------|-------------|
| `/system/identity` | `name` = device name |
| `/snmp` | `location` = device `location` |
| `/ip/traffic-flow/target`, `/system/logging/action` | `src-address` = gateway of `vlan_src` |
| `/ip/traffic-flow/target`, `/system/logging` | added when missing, otherwise set by `numbers` |

**Before using the lab's `general.yml`, review it:** SNMP community (`change_me_snmp_community`),
time zone (`Etc/UTC`), NTP server, syslog target (`10.21.3.10`), NetFlow/IPFIX collector
(`10.21.3.30`), the `www-ssl` certificate name (`<domain>.crt` must exist on the router) and the
BFD settings.

## DHCP lease files

`dhcp/ipv4/<device>/*.yml`: static leases for the `dhcp` configlet. The folder must exist when the
configlet is enabled:

```yaml
/ip/dhcp-server/lease:
- comment: printer_office
  address: 10.21.1.20
  mac-address: 02:00:00:00:00:01
  server: dhcpV4_1safe          # dhcpV4_<vlan name>
```

With no leases yet, write `/ip/dhcp-server/lease: []`.

## `clean_routes.yml`

The list of RouterOS paths (besides the firewall) whose objects are **removed when they aren't in
the proposal**, see the [safety model](../concepts.md#safety-model):

```yaml
- /interface/bridge
- /interface/list
- /interface/vlan
- /interface/vxlan
- /ip/address
- /ip/route
- /routing/bgp/connection
- /system/scheduler
...
```

Remove a path from the list to stop the automation from cleaning it (it will still add and update
what it generates there). Add a path to make the automation authoritative for it. On devices with
`api_version < 720`, `/routing/bgp/instance` is skipped.

## The lab firewall, file by file

The files in [`config/firewall/global/`](../../config/firewall/global/) are a complete,
opinionated policy. Adapt them:

| File | Content |
|------|---------|
| `1-adlv4_global.yml`, `1-adlv6_global.yml` | Address lists: private nets, site nets, management hosts (`ACL4_HOSTS_MGMT`), DNS, VPN users… **Edit first.** |
| `2-fwv4_contrack.yml`, `2-fwv6_contrack.yml` | FastTrack and accept established/related on input and forward (`posi`, kept at the top). |
| `3-fwv4_bans.yml`, `3-fwv6_bans.yml` | Log and drop hosts in the ban lists (`posi`). |
| `4-fwv4_queue.yml`, `4-fwv6_queue.yml` | Mangle priority marks for QoS. |
| `5-fwv4_icmp.yml`, `5-fwv6_icmp.yml` | ICMP / ICMPv6 policy for the router and forwarded traffic. |
| `6-fwv4_mgmt.yml`, `6-fwv6_mgmt.yml` | Management access to the router (from `ACL4_HOSTS_MGMT` and the management VPN). |
| `7-fwv4_uservpn.yml` | Example: VPN users reaching a storage server. |
| `7-fwv6_from_inet_global.yml` | Inbound IPv6 from the internet to published servers and WireGuard. |
| `8-fwv4_internet.yml`, `8-fwv6_internet.yml` | LAN → internet, MSS clamping. |
| `9-fwv4_general.yml`, `9-fwv6_general.yml` | Inter-site and service rules (safe VLAN, DMZ, NTP, logging, DNS…). |
| `10-fw4_webapp.yml` | DNS redirect for clients that turned the filter off in the [web portal](../tools/web-portal.md). |
| `100-fwv4_log_and_drop.yml`, `100-fwv6_log_and_drop.yml` | Final log-and-drop rules (`bot`). |

There is **no source NAT** in the global files: internet NAT depends on each site's uplink, so put
it in the device folder, e.g. `config/firewall/<device>/0-inet`:

```yaml
/ip/firewall/nat:
- comment: "v4_nat_srcnat_masquerade_internet"
  order: top
  chain: srcnat
  out_interface: 'ether1'
  src_address_list: ACL4_NETS_PRIVATE
  dst_address_list: '!ACL4_NETS_PRIVATE'
  action: 'masquerade'
```

[`config/firewall/lab-mikro1/2-fwv4_int_dnat`](../../config/firewall/lab-mikro1/2-fwv4_int_dnat)
is an example of device-specific rules (internal DNAT).
