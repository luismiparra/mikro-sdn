# Monitoring (`2-mikro-monitoring`)

A collector that polls every router over the RouterOS **REST API** and writes metrics to
**InfluxDB 2** (line protocol). Run it periodically and graph the results in Grafana or the
InfluxDB UI.

## What it collects

For every inventory device with role `core`/`edge`, `enabled: true` and `monitoring: true`:

1. **Reachability**: an ICMP ping to `mgmt_int`. Unreachable devices count as `site_offline` and
   are skipped.
2. **WireGuard backbone** (`/interface/wireguard/peers`, interfaces containing `main`): a peer is
   healthy when its last handshake is under 600 s.
3. **VPN users**: peers of interfaces containing `vpn_admin` or `vpn_user` with a recent handshake.
   Name your `wg-vpn` tunnels `admin…`/`user…` to have them counted.
4. **Netwatch** (`/tool/netwatch`): every probe the automation created, with its statistics.
5. **DHCP**: number of bound leases.
6. **RADIUS**: active user-manager sessions.

### Measurements

| Measurement | Tags | Fields |
|-------------|------|--------|
| `mikro_wg_peer_status` | `host`, `role`, `name` (interface) | `healthy`, `last-handshake` (s, `-1` = never) |
| `mikro_netwatch_icmp` | `host`, `role`, `name` (probe comment), `dst_ip` | `done-tests`, `failed-tests`, `loss-count`, `loss-percent`, `rtt-avg`, `rtt-jitter`, `rtt-max`, `rtt-min`, `rtt-stdev` |
| `mikro_netwatch_tcp` | same | `done-tests`, `failed-tests`, `tcp-connect-time` |
| `mikro_netwatch_simple` | same | `done-tests`, `failed-tests` |
| `mikro_global` | – | `vpn_infra_peers`, `vpn_infra_down_peers`, `ipv4_dhcp_leases`, `sites_online`, `site_offline`, `authusers`, `vpn_users_up` |

Example lines:

```
mikro_wg_peer_status,host=lab-mikro4,role=edge,name=int_w_lab-mikro4_main_to_lab-mikro1_main healthy=True,last-handshake=7.0
mikro_global vpn_infra_peers=24,vpn_infra_down_peers=0,ipv4_dhcp_leases=41,sites_online=6,site_offline=0,authusers=3,vpn_users_up=2
```

## Setup

Router side: the REST API is served by the `www-ssl` service (HTTPS, port 443). The `general`
configlet enables it with the certificate `<domain>.crt`. Create a read-only user
(`/user add name=monitor group=read`).

Collector side, in `.env` (see [environment](../configuration/environment.md#monitoring-2-mikro-monitoring)):

```bash
INVENTORY="config/inventory"
MIKRO_READ_USER="monitor"
MIKRO_READ_PASSWORD="..."
INFLUX_URL="http://influxdb:8086"
INFLUX_API_KEY="..."
INFLUX_ORG="my-org"
INFLUX_BUCKET="network"
```

Run it from the repository root:

```bash
.venv/bin/python 2-mikro-monitoring/mon_main.py
```

The ping uses raw ICMP sockets (`icmplib`): run as root, or allow unprivileged ICMP on Linux
(`sysctl net.ipv4.ping_group_range="0 2147483647"`).

Schedule it, for example every 5 minutes:

```cron
*/5 * * * *  cd /opt/mikro-sdn && .venv/bin/python 2-mikro-monitoring/mon_main.py >/dev/null 2>&1
```

## Notes

- Devices are polled one after another. With many sites a run takes longer, so keep the interval
  above the run time.
- TLS certificates are not verified (`verify=False`), see [Security](../security.md).
- The MQTT RTT metrics of the `netwatch` configlet (`MQTT_SERVER`) are a separate, push-based path
  from the routers. They don't go through this collector.
