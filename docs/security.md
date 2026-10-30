# Security

mikro-sdn holds the keys to your whole network: an admin password valid on every router and the
private key of every tunnel. This page describes the trust model, the known weaknesses and how to
harden a deployment.

## What is sensitive

| Item | Where | Impact if leaked |
|------|-------|------------------|
| `MIKRO_PASSWORD` | `.env`, CI secrets | Full control of every router. |
| `SECRETS/secrets.json` | automation host / CI runner | Impersonate any backbone router or VPN server; decrypt captured tunnel traffic. |
| `SECRETS/proposed/*`, `vpnconfig/`, `mgmt_export/`, `external_export/` | same | Contain private keys. |
| `SECRETS/radius_*.yml`, WiFi profile | same | User passwords, RADIUS secrets. |
| `RADIUS_SECRET`, `MQTT_PASSWORD`, `NETBOX_TOKEN`, `INFLUX_API_KEY` | `.env`, CI | Access to those services. |
| `WEB/` pages | web server | Topology and addressing, but no keys or passwords (masked). |

`.env`, `secrets/` and `web/` are git-ignored. Keep it that way, and check `git status` before
committing.

## Known weaknesses

| Area | Behaviour | Risk | Mitigation |
|------|-----------|------|------------|
| RouterOS API-SSL | The client negotiates **anonymous Diffie-Hellman** (ADH) ciphers, so the router presents no certificate and its identity isn't verified. | An attacker in the path to the router could intercept the session and the password. | Reach routers only over trusted paths: management VLAN, management VPN, the WireGuard backbone. Don't expose 8729 to the internet; the shipped firewall only accepts it from `ACL4_HOSTS_MGMT`. |
| REST API (monitoring, portal, NetBox serials) | HTTPS with `verify=False`. | Same as above. | Same. |
| Web portal | **No authentication.** Clients act on their own IP, and the boot hook trusts any caller whose IP is a router's `mgmt_int` inside `mgmt_allow_subnet`. | Anyone on an internal network can turn their own filter/VPN on or off, or trigger a re-push of a router. | Serve it only internally, and put it behind a reverse proxy with authentication if needed. |
| One shared admin password | The same `MIKRO_USER` on every router. | One leak gives access to every router. | A strong, rotated password stored only in CI secrets; restrict the user with `/user set address=` to the automation hosts. |
| `secrets.json` in clear text | Plain JSON on disk. | Host compromise = network compromise. | Restrict permissions (`chmod 600`), encrypt backups, keep the automation host minimal. |
| Destructive clean | A push removes what isn't in the repository. | A bad commit can take a site down. | Dry runs, branch protection, tests in CI, `LOCALSTRING` for out-of-band access, console access to cores. |
| `MGMT_CHECK_HOSTS` watchdog | Reboots routers when none of the hosts answers. | A wrong host list causes hourly reboots network-wide. | Off by default; use addresses that only fail when the router is really isolated. |
| Weak defaults in the lab config | Example SNMP community, example address lists. | Copied as-is, they open access you didn't intend. | Review `general/` and `firewall/global/1-adlv4_global.yml` before the first push. |

## Hardening checklist

- [ ] Dedicated automation host (or self-hosted CI runner) on the management network, nothing else
      on it.
- [ ] `chmod 700 secrets; chmod 600 secrets/secrets.json .env`, encrypted off-host backup of
      `SECRETS`.
- [ ] API user restricted by source address on every router:
      `/user set automation address=<automation host>/32`.
- [ ] `api` (plain) disabled, `api-ssl` reachable only from `ACL4_HOSTS_MGMT` (the shipped
      `general` and `fw` configs do this).
- [ ] SNMP community changed, or SNMP disabled.
- [ ] Out-of-band access to every core (console, LTE, or a protected `LOCALSTRING` rule).
- [ ] Branch protection on the branch CI pushes from, and tests required.
- [ ] Web portal only on internal networks.
- [ ] Rotate WireGuard keys after any suspected leak, see [key lifecycle](secrets-and-outputs.md#key-lifecycle).

## Reporting a vulnerability

See [SECURITY.md](../SECURITY.md): please use GitHub's private vulnerability reporting instead of
a public issue.
