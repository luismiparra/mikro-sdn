# 2-mikro-monitoring

Polls every router (REST API) and writes WireGuard, netwatch, DHCP and RADIUS metrics to
InfluxDB 2.

```bash
python 2-mikro-monitoring/mon_main.py
```

| File | Role |
|------|------|
| `mon_main.py` | Entry point: loops over monitored devices, sends the global metrics. |
| `mon_monitors.py` | Per-device checks: ping, WireGuard peers, netwatch, DHCP, user-manager sessions. |
| `mon_shared.py` | InfluxDB writer, REST helpers, inventory loader, RouterOS duration parser. |

Full documentation: [docs/tools/monitoring.md](../docs/tools/monitoring.md).
