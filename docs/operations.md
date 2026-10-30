# Operations

Day-2 tasks. Every change follows the same loop:

```
edit config  →  generate (mode config)  →  review proposals / docs  →  dry run  →  push  →  commit
```

- [Run modes cheat sheet](#run-modes-cheat-sheet)
- [Add a site](#add-a-site)
- [Remove or decommission a site](#remove-or-decommission-a-site)
- [Change a firewall rule](#change-a-firewall-rule)
- [Add a VLAN, a port, a DHCP lease](#add-a-vlan-a-port-a-dhcp-lease)
- [Remote-access VPN users](#remote-access-vpn-users)
- [Onboard a new router through the management VPN](#onboard-a-new-router-through-the-management-vpn)
- [Self-healing: boot hook and watchdog](#self-healing-boot-hook-and-watchdog)
- [Scheduled runs](#scheduled-runs)
- [Things you should not change](#things-you-should-not-change)

---

## Run modes cheat sheet

| I want to… | `control.yml` | Command |
|------------|---------------|---------|
| see what config would be generated | `mode: config` | `python 1-mikro-auto/mikro_main.py` |
| see what would change on the routers | `mode: global`, `dry_run: true` | `python 1-mikro-auto/mikro_main.py` → `web/Changes.md` |
| push everything | `mode: global`, `dry_run: false` | `python 1-mikro-auto/mikro_main.py` |
| push only the firewall | `mode: firewall`, `dry_run: false` | `python 1-mikro-auto/mikro_main.py` |
| push one device | `mode: global` | `python 1-mikro-auto/mikro_main.py <device>` |
| push one device through its alternative address | `mode: global` | `python 1-mikro-auto/mikro_main.py <device> aux` (uses `mgmt_aux`) |
| see the WAN ports/transit plan | – | `python 1-mikro-auto/mikro_ports.py [device] [csv]` |

## Add a site

1. Pick values that are free and that you'll **never change**: `wan_order` (next number after
   the highest one in use), `site_id`, `as`, `location`, and the `/16`, `/96` and `/53` blocks.
2. Create `config/inventory/<name>.yml` from a device of the same role.
3. If it has the `dhcp` configlet, create `config/dhcp/ipv4/<name>/v4.yml`. For device-specific
   firewall rules (internet NAT!), create `config/firewall/<name>/`.
4. Add the site's networks to the address lists that need them (e.g. `ACL4_NETS_SITES`,
   `ACL4_HOSTS_MGMT`) in `config/firewall/global/1-adlv4_global.yml`.
5. Generate (`mode: config`) and check `mikro_ports.py <name>`: the new device gets one slot on
   each core, and nothing existing moves.
6. Prepare the router ([getting started §4](getting-started.md#4-prepare-the-router)), or
   [onboard it through the management VPN](#onboard-a-new-router-through-the-management-vpn).
7. Dry run, then push **all** devices: the cores need their side of the new links.

## Remove or decommission a site

- **Wipe it first** (optional): set `clean_config: true` and push that device. Everything
  removable is deleted, and objects protected by `LOCALSTRING` stay.
- **Remove it from the network**: delete its inventory file (and its `dhcp/` and `firewall/`
  folders), then push all devices. The other routers remove their links to it.
- Keep its `wan_order`, `site_id` and subnets **unused**. Reusing them later is safe only once no
  device refers to the old site.
- Optionally remove its links from `SECRETS/secrets.json` (`<name>_main__…` entries).

## Change a firewall rule

1. Edit the rule in `config/firewall/global/…` (all devices) or `config/firewall/<device>/…`.
2. To move a rule, change its file's numeric prefix, its `order`, or its `posi`, see
   [rule order](configuration/config-files.md#rule-order).
3. Generate and read `secrets/proposed/<device>_fw.yml`.
4. `mode: firewall` + dry run, then push. Firewall-only runs are fast and don't touch anything
   else.

Renaming a rule's comment = deleting the old rule and adding a new one at the end. That matters
for `top` rules, whose position comes from when they were added.

## Add a VLAN, a port, a DHCP lease

- **VLAN**: add an entry to `lan.vlans` with a free `id` (< 250, not used by a VPN `subnet`).
  Its gateway, pools, DHCP servers and bridge VLAN entries are generated. Add firewall rules for
  it.
- **Access port**: add `{port: 'ether5', vlan: '3'}` to `lan.access_ports`. **Trunk**: add the
  port to `lan.trunk_ports`.
- **Static lease**: add it to `config/dhcp/ipv4/<device>/v4.yml` with `server: dhcpV4_<vlan name>`.

## Remote-access VPN users

- Generate client files: set `save_wg_files: true` on the device, generate, then hand out
  `SECRETS/vpnconfig/<device>_<vpn>/*_<n>.conf` or the `.png` QR code. Set it back to `false`
  afterwards: writing QR codes is slow.
- **More clients**: increase `number_client`.
- **Disable a client**: add its number to `disabled_peers` and push. The key is kept, so you can
  re-enable it later.
- **Revoke everything**: change the VPN's `id` (new keys) and redistribute the files.

## Onboard a new router through the management VPN

A brand-new router at a remote site can be brought into management without opening anything on
its WAN. It dials into a core's management VPN as a client:

1. On a core, have a `wg-vpn` entry with `mgmt_vpn: true` (the lab's `lab-mikro1` has
   `mgmt_vpn`, port 30001, subnet 100), set `save_wg_files: true`, set `MGMT_HOSTS` to the
   addresses that manage routers (e.g. the automation host on the management VPN), and generate.
2. Take an unused client number *n* and the script `SECRETS/mgmt_export/mikro_mgmt_<n>.txt`. It
   contains, ready to paste into the new router's terminal:
   - certificate imports (`<domain>.crt/.key`, `radius.<domain>.crt/.key`, `<ORG_NAME>_CA.crt`).
     Upload those files first, or delete the lines,
   - an address list + input rule allowing `MGMT_HOSTS`,
   - the WireGuard interface, the peer pointing to the core's `external_endpoint` and port, and
     the client address `10.<site>.100.<n>`,
   - a scheduler that resets the client's listen port every 30 minutes (helps behind NAT).

   Every object's comment starts with your first `LOCALSTRING`, so later pushes to the new router
   never remove its management tunnel.
3. Create the API user on the new router ([getting started §4](getting-started.md#4-prepare-the-router)).
4. Set the new device's `mgmt_int` to its management VPN address (`10.<site>.100.<n>`), add its
   inventory file, and push it.

## Self-healing: boot hook and watchdog

Two optional schedulers of the `autoupdate` configlet:

- **Boot hook** (`BOOT_UPDATE_URL`): 5 minutes after every boot the router calls
  `http://<portal>/router_boot_update`. The [web portal](tools/web-portal.md) checks the caller is
  a known router (`mgmt_int` inside `mgmt_allow_subnet`) and launches
  `mikro_main.py <that router>`. A router that was reset or rolled back gets its config back by
  itself.
- **Watchdog** (`MGMT_CHECK_HOSTS`): every hour the router pings those hosts and reboots when none
  answers. It recovers routers whose tunnels got stuck. Choose the hosts carefully: if they're
  down, every router reboots every hour.

## Scheduled runs

Running a full push periodically (cron, systemd timer or CI) keeps routers converged and undoes
manual drift:

```cron
*/30 * * * *  cd /opt/mikro-sdn && .venv/bin/python 1-mikro-auto/mikro_main.py >> /var/log/mikro-sdn.log 2>&1
```

`run_1_mikro_auto: false` in `control.yml` pauses it without touching cron. For Git-driven pushes,
see [CI/CD](ci-cd.md).

## Things you should not change

| Field | Why |
|-------|-----|
| `wan_order` | Moves listen ports and transit addresses on both ends of every link of the device. |
| `site_id` | Changes the loopback, every VXLAN VNI and edge port ranges. |
| `subnetv4` / `subnetv6` | Re-addresses the whole site, including links whose transit comes from its pool. |
| `name` | Every link, interface, comment and key of the device is named after it: a rename is a remove + add, and generates new keys. |
| VPN `id` | Generates new keys for the VPN; every client needs a new file. |
| `location` | Renames BGP filter chains and VPN file names. |
