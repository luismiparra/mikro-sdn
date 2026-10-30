# Security policy

mikro-sdn manages router credentials and WireGuard private keys, so security reports are taken
seriously.

## Reporting a vulnerability

Please **don't open a public issue**. Use GitHub's
[private vulnerability reporting](https://github.com/luismiparra/mikro-sdn/security/advisories/new)
instead, with a description, the affected files and, if possible, steps to reproduce.

## Scope and known limitations

The trust model and the known weaknesses (anonymous-DH API-SSL, unverified REST certificates, the
unauthenticated web portal…) are documented in [docs/security.md](docs/security.md), together with a
hardening checklist. Reports that improve on them are welcome.
