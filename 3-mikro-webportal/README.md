# 3-mikro-webportal

Flask portal: lets each user toggle the DNS filter and the VPN internet exit for their own IP, and
lets routers request a config push after booting (`/router_boot_update`).

```bash
DEBUGMODE=1 python 3-mikro-webportal/app.py        # development server on :8080
cd 3-mikro-webportal && gunicorn app:application   # production (WSGI)
```

| File | Role |
|------|------|
| `app.py` | Routes, client/site lookup, address-list toggles, boot hook. |
| `web_shared.py` | Inventory and `control.yml` loading, RouterOS REST helpers (GET/PUT/PATCH/DELETE). |
| `templates/`, `static/` | Pages and stylesheet. Branding comes from `ORG_NAME` / `PORTAL_HOME_URL`. |

Full documentation, including the security caveats (no authentication): [docs/tools/web-portal.md](../docs/tools/web-portal.md).
