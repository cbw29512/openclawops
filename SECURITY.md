# Security Policy

OpenClawOps is a public source snapshot of a local supervised-automation workspace. Do not use public issues, pull requests, screenshots, or recordings to disclose credentials, tokens, account sessions, local reports, private network details, payment information, or an exploitable vulnerability.

## Supported code

Security and policy-drift fixes are applied to the current `main` branch. The project does not maintain parallel supported release branches.

## Reporting a vulnerability

Use one of these private channels:

1. Open a private GitHub security advisory when that option is available.
2. Email `divclass01@gmail.com` with the subject `OpenClawOps security report`.

Include:

- the affected file and commit
- safe reproduction steps
- expected and observed behavior
- potential impact
- any suggested mitigation

Never include real credentials, API keys, cookies, browser sessions, account tokens, payment methods, affiliate credentials, email credentials, deployment secrets, or unrelated personal/employer infrastructure.

## Current trust boundary

OpenClawOps assumes:

- the dashboard binds to `127.0.0.1`
- the workspace runs on a trusted local machine
- local reports and registries may contain sensitive operational context
- Boost and Bury change local priority only
- external actions remain disabled without Chris's explicit approval
- the repository is a May 2026 pre-reinstall snapshot, not proof that the runtime is currently active
- repository CI performs static validation and dependency auditing only

## In-scope reports

- bypassing the Chris approval boundary
- enabling publishing, spending, outreach, credentials, Git writes, or live changes without approval
- expanding Dashboard v1 writes beyond `data/opportunity_index.json`
- unsafe command construction in local voting or dashboard routes
- path traversal or arbitrary local file access
- script or template injection in the dashboard
- leaking private reports, credentials, tokens, or sessions
- weakening saved quality, trust, or public-page gates without detection
- CI changes that execute operational PowerShell, scheduled tasks, Ollama, OpenClaw, publishing, or external actions
- discrepancies that make a stale snapshot appear currently active

## Out of scope

- attacks against GitHub, FastAPI, Uvicorn, Jinja2, PowerShell, Ollama, OpenClaw, or other third-party services themselves
- denial-of-service testing against a restored local workspace
- social engineering or physical access
- findings that require unrelated home, employer, or production infrastructure
- automated scan output without reproducible impact
- requests to enable autonomous publishing, spending, outreach, credentials, Git writes, or destructive execution

## Safety rule

Do not expose the preserved dashboard publicly or resume scheduled automation solely from this repository. Re-verify the restored machine, policies, paths, dependencies, secrets handling, and approval controls before running operational workflows.
