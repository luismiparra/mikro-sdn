# secrets.example

Templates of the files the automation reads from the `SECRETS` directory. Copy this folder and
edit the values:

```bash
cp -r secrets.example secrets
```

`secrets/` is in `.gitignore`: never commit it. The automation also writes into it (generated keys
in `secrets.json`, the proposed config, VPN client files), see
[docs/secrets-and-outputs.md](../docs/secrets-and-outputs.md).
