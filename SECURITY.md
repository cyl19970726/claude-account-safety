# Security Policy

## Reporting

Please report security issues privately via GitHub Security Advisories:

https://github.com/cyl19970726/claude-account-safety/security/advisories/new

Do not open a public issue containing:

- passwords, API keys, tokens, cookies;
- subscription URLs or node UUIDs;
- personal account or KYC information;
- unredacted logs with IPs/hostnames.

## Scope

In scope:

- `scripts/*.py` and installers;
- secret scanning / redaction logic;
- unsafe file handling or destructive behavior;
- supply-chain issues in the skill package.

Out of scope:

- Anthropic account recovery or ban appeals;
- third-party proxy/provider behavior;
- browser fingerprinting or device-identity evasion.

## Supported versions

Only the latest release is supported.

## Secret handling

This project expects secrets to stay in a password manager or OS secret store. The repository must contain only references such as `op://`, `env:`, or `keychain://`. `scripts/secret_check.py` runs before install/package and rejects high-confidence secrets.
