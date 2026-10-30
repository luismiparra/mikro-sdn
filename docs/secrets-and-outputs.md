# Secrets and outputs

The automation reads and writes two folders outside the repository's tracked files:

- **`SECRETS`**: private. Generated keys, the proposals (which contain private keys), VPN client
  files, and the input files you provide (RADIUS users, WiFi). **Never commit it**, back it up.
- **`WEB`**: shareable documentation of the generated config, with keys hidden.

Both are listed in `.gitignore` under their default names (`secrets/`, `web/`).

---

## `SECRETS` layout

```
secrets/
├── secrets.json                 ← generated: every WireGuard private/public/preshared key
├── radius_users.yml             ← you: user-manager users          (radius_server)
├── radius_routers.yml           ← you: RADIUS clients              (radius_server)
├── <wifi_profile>.yml           ← you: WiFi profile, e.g. wifi.yml (wifi)
├── mac_addr.yml                 ← you: WiFi MAC access list        (wifi)
├── proposed/
│   ├── <device>_global.json|yml ← generated: non-firewall config to push
│   └── <device>_fw.json|yml     ← generated: firewall config to push
├── old_proposed/                ← the previous proposals (moved before each generation)
├── vpnconfig/<device>_<vpn>/    ← generated: VPN client .conf + QR .png (save_wg_files)
├── mgmt_export/                 ← generated: router onboarding scripts (management VPN)
├── external/external.json|yml   ← generated: the external peers' side of every link
└── external_export/             ← generated: wg_<host>_<link>.conf and frr_<host>.conf
```

Start with `cp -r secrets.example secrets`: the templates in
[`secrets.example/`](../secrets.example/) show the format of every file you provide.

### `secrets.json`

A flat JSON object holding:

- per WAN link `<a>_main__<b>_main`: both ends' key pairs and the preshared key,
- per VPN `<device>_wgvpn_<id>`: the server key pair, the preshared key and every client's key pair.

Keys are created the first time a link or VPN appears and **reused on every later run**. That's
what keeps tunnels stable. If this file is lost, the next run creates new keys for everything:
every WAN link has to be pushed again on both ends and every VPN client needs a new
configuration.

> Restoring from a backup is safe: copy `secrets.json` into an empty `SECRETS` folder and run.
> (Earlier versions overwrote `secrets.json` when the `external/` subfolder was missing. That's
> fixed.)

### Key lifecycle

| Goal | How |
|------|-----|
| Rotate one WAN link | Remove the link's entry from `secrets.json`, then push **both** devices. |
| Rotate one VPN | Remove `<device>_wgvpn_<id>` (or change the VPN's `id`), push, redistribute client files. |
| Revoke one VPN client | Add its number to `disabled_peers` (keeps the key) or rotate the VPN. |
| Add VPN clients | Raise `number_client`. New clients get keys; existing ones are untouched. |

### Proposals

`proposed/<device>_global.*` and `_fw.*` are exactly what the push will apply, in order. The `.yml`
files are for reading and diffing; the `.json` files are what the push loads. They contain private
keys. To see what changed between two generations:

```bash
diff secrets/old_proposed/lab-mikro1_fw.yml secrets/proposed/lab-mikro1_fw.yml
```

(`old_proposed/` keeps only the `.json`; regenerate twice, or keep the YAML in your own history,
to diff YAML.)

## `WEB` outputs

| File | Content |
|------|---------|
| `<device>.md` / `.html` | The device's proposal as one table per RouterOS path (keys, passwords and secrets hidden). |
| `Global.md` / `.html` | All devices in one page. |
| `bind_A.txt` | `A` records `<interface>-<device>` for every interface address. |
| `bind_PTR.txt` | `PTR` records in the zone of each device's `domain`. |
| `Changes.md` / `.html` | The log of the last full run: every ADD / UPDATE / REMOVE, or would-be in a dry run, with secrets masked. |
| `style.css` | Stylesheet of the HTML pages (`templates/css1.j2`). |

The HTML pages are static and can be served by any web server. In production they're
published to an internal web server from CI. Examples:
[`examples/generated-output/`](../examples/generated-output/).

## Backups

Back up `SECRETS` (at least `secrets.json` and the files you wrote by hand) somewhere encrypted.
Anyone with `secrets.json` can impersonate any router of the backbone and decrypt its traffic.
See [Security](security.md).
