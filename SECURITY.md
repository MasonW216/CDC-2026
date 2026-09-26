# Security Policy

## Scope

StormRoute is a student competition prototype. It stores no user accounts, no
personal data, and no credentials. The security surface is small but not empty:
the service calls external weather, alert, and routing APIs, and it loads a
serialized model artifact from disk.

## Reporting a vulnerability

Open a private security advisory through the repository's **Security → Advisories**
tab, or contact a maintainer directly. Please do not open a public issue for an
unpatched vulnerability.

Include what you did, what happened, and what you expected. We will acknowledge
within a few days during the competition period.

## Secrets

- Never commit `.env`, API tokens, or deployment credentials. `.env` is ignored
  and `detect-private-key` runs as a pre-commit hook.
- `.env.example` holds names and placeholders only.
- Real values belong in Codespaces secrets or repository environment secrets.
- If a secret is ever committed, rotate it first and rewrite history second.
  Assume any pushed secret is compromised.

## Known risk areas

| Area | Risk | Mitigation |
|---|---|---|
| Model artifact | `joblib` deserialization executes code from the file | Load only artifacts this repository produced; the manifest records a checksum |
| External APIs | Untrusted response bodies parsed into the service | Validate every response through Pydantic; enforce timeouts |
| Routing/weather keys | Leakage through logs or error responses | Structured logging redacts configuration; errors never echo request headers |
| CORS | Overly broad browser access | Origins are an explicit allowlist, never `*` |

## Dependencies

Dependabot runs weekly for pip, npm, and GitHub Actions. Secret scanning and
dependency alerts are enabled on the repository.
