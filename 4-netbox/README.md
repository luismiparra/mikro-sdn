# 4-netbox

One-way sync of the inventory and the generated addressing into NetBox (regions, sites, ASNs,
roles, devices, VLANs, interfaces, prefixes, IP addresses, IP ranges), with tag-based ownership.

```bash
NETBOX_DRYRUN=1 python 4-netbox/netbox_main.py   # log only
python 4-netbox/netbox_main.py
```

| File | Role |
|------|------|
| `netbox_main.py` | Entry point: builds every object list and syncs them in dependency order, prints the report. |
| `netbox_inventory.py` | Inventory → regions, sites, ASNs, roles, devices (with live serial), VLANs, prefixes. |
| `netbox_intended.py` | Generated proposals → interfaces, IP addresses, IP ranges. |
| `netbox_api.py` | Generic tag-aware create/update/delete in bulk, static objects (tags, RIR, site groups). |
| `netbox_get.py` | Cached lookups by slug/name. |
| `netbox_shared.py` | Settings, inventory loader, subnet helpers. |
| `netbox_external_api.py` | Reads serial numbers from the routers (REST). |
| `data/device_type/` | Extra MikroTik device-type definitions to import into NetBox. |

Full documentation: [docs/tools/netbox.md](../docs/tools/netbox.md).
