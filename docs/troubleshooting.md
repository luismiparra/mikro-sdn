# Troubleshooting

Turn on debug logs with `DEBUGMODE=1` in `.env`. Note that in debug mode a fatal error waits for
Enter instead of exiting.

## Start-up and generation

| Symptom | Cause / fix |
|---------|-------------|
| `TypeError: the JSON object must be str… NoneType` at import | `LOCALSTRING` isn't set. Copy `.env.example` to `.env` and run from the repository root. |
| `FileNotFoundError: …/control.yml`, `templates/…` | Not running from the repository root, or `CONTROLPATH`/`CONFIG` wrong. |
| `FileNotFoundError: …/radius_users.yml`, `…/wifi.yml`, `…/mac_addr.yml` | A device uses `radius_server` or `wifi` but `SECRETS` lacks the files: `cp -r secrets.example secrets`. |
| `FileNotFoundError: …/dhcp/ipv4/<device>` | The device has the `dhcp` configlet but no lease folder. Create it with `/ip/dhcp-server/lease: []`. |
| `KeyError: 'xyz'` with a device name before it | A required inventory field is missing, see the [inventory reference](configuration/inventory.md). |
| `FileNotFoundError: 'wg'` | `wireguard-tools` not installed (needed to generate keys). |
| *No wan_order in inventory. Assigned N* | Add `wan_order: N` to that device's file before pushing, see [wan_order](network-design.md#wan_order-stable-slots-ports-and-transit-subnets). |
| *Duplicated wan_order* | Two devices share a `wan_order`; the run stops. |
| *wan slot N … out of the 64 available transit subnets* | A device has more than 64 links, or `wan_order` values are very sparse. |
| *Duplicated rule in config comment* | Two items share a comment in the same config; only the first is used. |
| *Warning No specific FW config* | Informational: there's no `config/firewall/<device>/` folder. |
| *mqtt_netwatch_monitor enabled but MQTT_SERVER not set* | Set `MQTT_SERVER` or `mqtt_netwatch_monitor: false`. |
| `IndexError` in the LAN or VPN configlet | A VLAN id or VPN `subnet` above 250, or the subnet blocks aren't exactly `/16`, `/96`, `/53`. (250 itself doesn't fail but collides with the transit pool: keep them below 250.) |

## Connecting

| Symptom | Cause / fix |
|---------|-------------|
| *CONNECTION ERROR! at IP …* | Neither `mgmt_int` nor `mgmt_ext` answered on TCP 8729. Check routing, the router's firewall (`ACL4_HOSTS_MGMT`) and `/ip service print`. |
| *Error connecting … SSL* / handshake failure | `api-ssl` has a certificate assigned. The client only speaks anonymous DH: `/ip service set api-ssl certificate=none`. |
| *invalid user name or password* | `MIKRO_USER`/`MIKRO_PASSWORD`, or the user is limited by `address=`. |
| Monitoring/portal: connection refused on 443 | `www-ssl` disabled or without a valid certificate name. |

## Pushing

| Symptom | Cause / fix |
|---------|-------------|
| *ADD cfg rule Error … unknown parameter* | The property doesn't exist in this RouterOS version (check `api_version`) or is misspelled in a YAML file. |
| *UPDATE error … certificate* | `general.yml` refers to a certificate (`<domain>.crt`) that isn't on the router. |
| *MOVE FW rule Error* | A `posi` beyond the number of rules. Lower it. |
| Every push updates the same objects | A value the router normalizes differently (`10s` vs `00:00:10`, `yes` vs `true`, `"1"` vs `1`). Write it the way `/print` shows it. |
| Something I configured by hand disappeared | It was in a managed path without a protected comment, see the [safety model](concepts.md#safety-model). Re-create it with a `LOCALSTRING` comment. |
| Ban lists empty after every push | Address-list entries without comment are cleaned, see the [safety model](concepts.md#what-is-removed). |
| Locked out after a firewall push | Your address wasn't in `ACL4_HOSTS_MGMT`. Recover through the management VPN or console, fix the list, push again. |
| Run stops with *Error detected stopping execution* | An unexpected exception while processing a device (`errorStop`). The error line above it tells which object. |

## Backbone

| Symptom | Cause / fix |
|---------|-------------|
| A WireGuard link has no handshake | Check both devices were pushed after the change, the ports from `mikro_ports.py` are open, and `external_endpoint` resolves. Edges must be able to reach the core's port. |
| BGP up but no routes | Check `as` values are unique, and the filters: an edge only advertises its own `subnetv4`/`subnetv6`. |
| Links changed ports/addresses after an inventory edit | `wan_order` changed or a device was added without one. Restore the old values. |
| Tunnels broke after moving the automation host | `secrets.json` wasn't carried over, so new keys were generated. Restore it and push again. |
