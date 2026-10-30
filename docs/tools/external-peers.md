# External Linux peers (`external_edge`)

A Linux host (a VPS, a server in a data center, a hypervisor…) can join the BGP backbone like an
edge: it gets a WireGuard link to every core and announces its own prefixes. The automation
configures the cores' side and writes ready-to-use files for the host. It never connects to the
host itself.

## Inventory

```yaml
external_edge:
- name: "externalhost1"
  role: "external_edge"
  wan_order: 6                              # permanent, like any device
  site_id: 7
  location: "labsite200"
  enabled: True
  as: '65300'
  use_bfd: True
  wg_mtu: '1280'
  backbone_untrusted: false
  mgmt_int: "10.91.1.1"                    # BGP router-id
  mgmt_ext: "10.91.1.1"
  external_wg_main_port: 61200              # fixed listen port on the host
  allow_out_prefix_v4: "10.91.222.200/32"  # what the cores accept from it
  allow_out_prefix_v6: "2001:db8:10:0:10:91:0:0/96"
  subnetv4: "10.91.0.0/16"                 # its transit pool comes from here
  subnetv6: "2001:db8:10:0:10:91:0:0/96"
  subnetv6slaac: "2001:db8:10:a000::/53"
  configlet: ["wan"]
```

The host dials the cores (their side of the link is a responder without endpoint), so it needs
outbound UDP to the cores' `external_endpoint` and ports, and no inbound port of its own.
`external_wg_main_port` just pins its local listen port.

## Generated files

After a run, in `SECRETS/external_export/`:

- `wg_<host>_<link>.conf`, one per core: a `wg-quick` config with `Table = off` (routes come from
  BGP), the transit addresses, keys, the core's endpoint and port.
- `frr_<host>.conf`: an FRR `bgpd` configuration with every core as eBGP neighbor (IPv4 and IPv6),
  `redistribute connected`, and permissive route-maps `meshv4`/`meshv6`. Tighten them for your
  setup.

`SECRETS/external/external.json|yml` holds the same data in structured form.

## Install on the host

```bash
apt install wireguard frr
# enable bgpd in /etc/frr/daemons, then:
for f in wg_externalhost1_*.conf; do
  cp "$f" /etc/wireguard/ && systemctl enable --now "wg-quick@${f%.conf}"
done
cp frr_externalhost1.conf /etc/frr/frr.conf && systemctl restart frr
vtysh -c 'show bgp summary'
```

WireGuard interface names are limited to 15 characters on Linux. Rename the `.conf` files to
shorter names if `wg-quick` complains.

The cores only accept `allow_out_prefix_v4`/`_v6` (and the host's loopback) from it, so a
misconfigured host can't hijack other routes.
