# Examples

## `generated-output/`

What `mikro_main.py` writes to the `WEB` folder for the [bundled lab](../config/README.md), with
`ORG_NAME=example`, in `config` mode (no device contacted):

| File | Content |
|------|---------|
| [`lab-mikro1.md`](generated-output/lab-mikro1.md) … `lab-mikro6.md` | Each router's full proposed configuration, as one table per RouterOS path (keys hidden). `.html` versions alongside. |
| [`Global.md`](generated-output/Global.md) | All routers in one page. |
| [`bind_A.txt`](generated-output/bind_A.txt), [`bind_PTR.txt`](generated-output/bind_PTR.txt) | DNS records for every interface address. |
| [`Changes.md`](generated-output/Changes.md) | The change log. Empty here because nothing was pushed; after a dry run or push it lists every ADD / UPDATE / REMOVE. |

Regenerate it after changing the lab:

```bash
WEB=examples/generated-output ORG_NAME=example python 1-mikro-auto/mikro_main.py   # with mode: config
```

The proposals themselves (`SECRETS/proposed/*.yml`) are not included because they contain
private keys. Generate the lab to see them.
