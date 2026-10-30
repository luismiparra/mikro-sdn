# Environment and control

All tools read their settings from environment variables. Each script calls `load_dotenv()`, so a
`.env` file in the **current directory** (run from the repository root) is loaded automatically.
Variables that are already set in the environment win over `.env`. Start from
[`.env.example`](../../.env.example).

- [Automation (`1-mikro-auto`)](#automation-1-mikro-auto)
- [Monitoring (`2-mikro-monitoring`)](#monitoring-2-mikro-monitoring)
- [Web portal (`3-mikro-webportal`)](#web-portal-3-mikro-webportal)
- [NetBox (`4-netbox`)](#netbox-4-netbox)
- [`control/control.yml`](#controlcontrolyml)

---

## Automation (`1-mikro-auto`)

### Required

| Variable | Example | Description |
|----------|---------|-------------|
| `CONFIG` | `config` | Config folder: `inventory/`, `firewall/`, `general/`, `dhcp/`, `clean_routes.yml`. |
| `CONTROLPATH` | `control` | Folder containing `control.yml`. |
| `SECRETS` | `secrets` | Private working folder: keys, proposals, VPN files. See [secrets and outputs](../secrets-and-outputs.md). |
| `WEB` | `web` | Output folder of the generated documentation. |
| `LOCALSTRING` | `'["local_auto_", "auto_webapp_"]'` | JSON list of protected comment substrings. The first one prefixes the management VPN objects. See [safety model](../concepts.md#safety-model). |
| `MIKRO_USER` / `MIKRO_PASSWORD` | | API user with full rights on every router (only needed when connecting). |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUGMODE` | empty | Any non-empty value: debug logs, and errors **pause for Enter** instead of exiting. Leave empty in CI and cron. |
| `TARGET_DEVICE` | empty | Push only this device (same as passing it as the first argument). |
| `ORG_NAME` | `mikro-sdn` | Name in the generated pages' title and in the WireGuard/FRR file headers. |
| `RADIUS_SECRET` | empty | Shared secret of the RADIUS servers (`wifi` configlet). The old misspelled `RAIUS_SECRET` is still read. |
| `RADIUS_CERTIFICATE` | `radius.<domain>.crt` | Certificate the user-manager uses (`radius_server` configlet). Must already be imported on the router. |
| `MQTT_SERVER` | empty | MQTT broker for netwatch RTT metrics on devices with `mqtt_netwatch_monitor: true`. Empty: no broker is configured and a warning is logged. |
| `MQTT_PORT` | `1883` | Broker port. |
| `MQTT_USER` / `MQTT_PASSWORD` | empty | Broker credentials. |
| `BOOT_UPDATE_URL` | empty | URL every router fetches 5 minutes after booting (scheduler `script_boot_get_config`), normally the web portal's `http://<portal>/router_boot_update`. Empty: the scheduler isn't created. |
| `MGMT_CHECK_HOSTS` | empty | JSON list, e.g. `'["10.21.1.1", "10.22.1.1"]'`. Every hour each router pings them and **reboots when none answers** (scheduler `script_auto_reboot_if_mgmt_lost`). Empty: no watchdog. Only use addresses that are reachable whenever the router is healthy. |
| `MGMT_HOSTS` | `[]` | JSON list of management hosts the [onboarding script](../operations.md#onboard-a-new-router-through-the-management-vpn) of a new router allows in. |
| `GITHUB_ACTIONS`, `GITHUB_STEP_SUMMARY` | set by GitHub | Turn on GitHub annotations and the job summary tables, see [CI logs](../ci-cd.md#ci-log-format). |

> `MGMT_CHECK_HOSTS`, `BOOT_UPDATE_URL` and `MQTT_SERVER` were hard-coded in earlier versions.
> They're now opt-in: with the defaults, routers never call an unknown URL nor reboot by
> themselves.

## Monitoring (`2-mikro-monitoring`)

| Variable | Description |
|----------|-------------|
| `INVENTORY` | Inventory folder to read, e.g. `config/inventory`. |
| `MIKRO_READ_USER` / `MIKRO_READ_PASSWORD` | Read-only router user (REST API). |
| `INFLUX_URL` | InfluxDB 2 URL, e.g. `http://localhost:8086`. |
| `INFLUX_API_KEY` | InfluxDB token with write access to the bucket. |
| `INFLUX_ORG`, `INFLUX_BUCKET` | Organization and bucket. |
| `DEBUGMODE` | Accepted, currently no effect on the log level. |

## Web portal (`3-mikro-webportal`)

| Variable | Description |
|----------|-------------|
| `CONFIG`, `CONTROLPATH` | Same as the automation (inventory and `control.yml`). |
| `MIKRO_USER` / `MIKRO_PASSWORD` | User the portal edits address lists with (REST API). |
| `MAIN_AUTO_PY_EXEC` | Script launched by `/router_boot_update`, normally `1-mikro-auto/mikro_main.py`. |
| `ORG_NAME` | Name in the page title and header. |
| `PORTAL_HOME_URL` | Optional link in the header and footer. |
| `DEBUGMODE` | Non-empty: start Flask's development server on `0.0.0.0:8080` when the module is imported. |

## NetBox (`4-netbox`)

| Variable | Description |
|----------|-------------|
| `NETBOX_URL`, `NETBOX_TOKEN` | NetBox API URL and a token with write access. |
| `NETBOX_TAG` | Tag marking the objects this tool owns. Only tagged objects are updated or deleted. Use a different tag per environment (`MSDN-LAB`, `MSDN-PROD`). |
| `NETBOX_DRYRUN` | `1`/`true`/`yes`: log what would be created, updated or deleted, write nothing. |
| `CONFIG`, `SECRETS` | Inventory and proposals (IP addresses are taken from the generated proposals, so run the automation first). |
| `MIKRO_READ_USER` / `MIKRO_READ_PASSWORD` | Used to read device serial numbers over REST. |

## `control/control.yml`

The run switch of the automation. It's in the repository so a commit can change what CI does.

```yaml
#run_1_mikro_auto TRUE = AUTOMATION ENABLED       FALSE = DO NOT EXEC AUTOMATION
run_1_mikro_auto: true
#mikro_auto_dry_run TRUE = SIMULATE PUSH AND CLEAN       FALSE = REAL PUSH AND CLEAN
mikro_auto_dry_run: true
#Define mode "config" (just generate config, never connects to a device) or "global" or "firewall"
mikro_auto_mode: 'config'
#RouterUpdate vars
webapp_host: '10.21.100.200'
mgmt_allow_subnet: '10.21.100.0/24'
```

| Key | Used by | Description |
|-----|---------|-------------|
| `run_1_mikro_auto` | automation | `false`: a full run does nothing (logs *MIKRO AUTO DISABLED*). A run for a named device still happens. |
| `mikro_auto_dry_run` | automation | `true`: connect and read, but write nothing; produces `WEB/Changes.md`. |
| `mikro_auto_mode` | automation | `config` (generate only, offline), `firewall` (clean/push firewall only) or `global` (everything). |
| `mgmt_allow_subnet` | web portal | Only routers whose `mgmt_int` is in this subnet may trigger `/router_boot_update`. |
| `webapp_host` | – | Informational (address of the portal host). |

The shipped values are the safe ones: `config` mode and dry run on. See
[modes](../concepts.md#modes-dry-run-and-single-device-runs).
