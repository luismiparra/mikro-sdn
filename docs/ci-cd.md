# CI/CD (GitOps)

The automation was built to be driven from Git: a commit changes the YAML, CI runs the tests and,
when asked, pushes the result to the routers. This page shows how to set that up with GitHub
Actions, and explains the CI log format.

- [What ships in this repository](#what-ships-in-this-repository)
- [A push pipeline](#a-push-pipeline)
- [CI log format](#ci-log-format)

---

## What ships in this repository

[`.github/workflows/tests.yml`](../.github/workflows/tests.yml) runs the test suite on every push
and pull request, on GitHub-hosted runners. It needs no secrets and never contacts a router.

## A push pipeline

Pushing to routers from CI needs:

- a **self-hosted runner** that can reach every router's `mgmt_int`/`mgmt_ext` on TCP 8729
  (typically a VM inside the management network or on the management VPN),
- a **persistent `SECRETS` folder on that runner**, outside the checkout, because `secrets.json`
  must survive between runs (see [secrets](secrets-and-outputs.md)),
- the router password and other credentials as **GitHub Actions secrets**.

The workflow below is the one used in production. Tests always run first. A commit whose
message contains `#push` pushes to the routers, one containing `#netbox` syncs NetBox, and a manual
run can do either, optionally for one device.

```yaml
# .github/workflows/network.yml
name: Network automation
on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      action_type:
        description: 'Action to run'
        required: true
        default: '#push'
        type: choice
        options: ['#push', '#netbox']
      target_device:
        description: 'Only this device (optional)'
        required: false
        type: string

jobs:
  # Nothing reaches a router unless the whole suite passes with coverage >= 95%
  tests:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements-dev.txt
      - run: python3 -m pytest

  push-to-devices:
    needs: tests
    if: contains(github.event.head_commit.message, '#push') || inputs.action_type == '#push'
    runs-on: self-hosted
    concurrency: network-push            # never two pushes at the same time
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt   # the runner also needs wireguard-tools
      - name: 🚀 Push config to MikroTik devices
        env:
          CONFIG: "config"
          CONTROLPATH: "control"
          SECRETS: "/srv/mikro-sdn/secrets"   # persistent, outside the checkout
          WEB: "/var/www/html/network"        # generated docs, served internally
          LOCALSTRING: '["local_auto_", "auto_webapp_"]'
          ORG_NAME: "My Network"
          MIKRO_USER: "automation"
          MIKRO_PASSWORD: ${{ secrets.MIKRO_PASSWORD }}
          RADIUS_SECRET: ${{ secrets.RADIUS_SECRET }}
          MQTT_USER: ${{ secrets.MQTT_USER }}
          MQTT_PASSWORD: ${{ secrets.MQTT_PASSWORD }}
          TARGET_DEVICE: ${{ inputs.target_device }}
        run: python3 1-mikro-auto/mikro_main.py

  netbox:
    needs: tests
    if: contains(github.event.head_commit.message, '#netbox') || inputs.action_type == '#netbox'
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - name: 🗂️ Sync NetBox
        env:
          CONFIG: "config"
          SECRETS: "/srv/mikro-sdn/secrets"
          NETBOX_URL: "http://netbox.example.int:8000"
          NETBOX_TOKEN: ${{ secrets.NETBOX_TOKEN }}
          NETBOX_TAG: "MSDN-PROD"
          MIKRO_READ_USER: "monitor"
          MIKRO_READ_PASSWORD: ${{ secrets.MIKRO_READ_PASSWORD }}
        run: python3 4-netbox/netbox_main.py
```

How it's used day to day:

- Edit YAML, commit **without** a tag: tests run, nothing is pushed.
- Set `mikro_auto_dry_run: true` in `control.yml`, commit with `#push`: the job logs every
  would-be change and writes `Changes.html` to `WEB`. Review it.
- Set `mikro_auto_dry_run: false`, commit with `#push`: the change goes live.
- Emergency stop: commit `run_1_mikro_auto: false`.

Protect `main` (reviews, required checks) because a merge with `#push` changes the network.

## CI log format

`1-mikro-auto/mikro_log.py` formats the console output of `mikro_main.py` and `netbox_main.py` so CI
logs are easy to scan. It only changes how lines are shown; the log records keep their text.

- **One icon per line**, from the level (🔍 debug, 🔹 info, ⚠️ warning, ❌ error) and the action
  in the message: 🧹 clean, 🚀 push, 🔄 update, 🗑️ remove, ➕ create, ✅ OK/DONE, 🔌 connection
  error, ⏸️ disabled, 🧪 dry run, 🔎 not found, 📦 inventory, ⚙️ generate, 📝 docs, 🎯 one host.
- **Scope column**: the `<scope> -> message` prefix becomes an aligned column (`GENERAL`,
  `ONEHOST MODE`, `NETBOX` or a device name).
- **Section banners** for the stages of a run.
- **GitHub annotations**: with `GITHUB_ACTIONS=true`, warnings and errors are also emitted as
  `::warning::`/`::error::`, so they show on the run's summary page.
- **Summary tables**, printed and appended to `$GITHUB_STEP_SUMMARY`:
  - *Generated config*: devices × configlets,
  - *Push result*: removed, updated, warnings, errors and status per device,
  - *NETBOX → Sync result*: created, updated, deleted, unchanged per endpoint.

```
━━━━━━━━━━━━━━━━━━━ 📦 GENERAL · AUTOMATION LOAD INVENTORY ━━━━━━━━━━━━━━━━━━━
🎯 ONEHOST MODE   │ START ONE HOST - >lab-mikro4
🧹 lab-mikro4     │ Start clean
✅ lab-mikro4     │ OK clean
🚀 lab-mikro4     │ Start push
🔄 lab-mikro4     │ A_Update needed at /interface/wireguard/peers -> endpoint_address ...
✅ lab-mikro4     │ OK push
🔹 ONEHOST MODE   │ Push result
                  │ ┌────────────┬────────────┬────────────┬─────────────┬───────────┬────────┐
                  │ │ Device     │ 🗑️ Removed │ 🔄 Updated │ ⚠️ Warnings │ ❌ Errors │ Status │
                  │ ├────────────┼────────────┼────────────┼─────────────┼───────────┼────────┤
                  │ │ lab-mikro4 │ 0          │ 1          │ 0           │ 0         │ ✅ ok  │
                  │ └────────────┴────────────┴────────────┴─────────────┴───────────┴────────┘
```

To recognize a new kind of line, add a `(kind, icon, regex)` entry to `KINDS` in `mikro_log.py` (the
first match wins). To count it in the push table, add a column in `device_report`.
