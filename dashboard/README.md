# Nova Money Scout Dashboard

A loopback-only operator dashboard for Nova Money Scout.

## Required environment

Set these values in the current PowerShell session or a deployment-only environment file that is excluded from Git:

```powershell
$env:NOVA_DASHBOARD_USERNAME = "operator"
$env:NOVA_DASHBOARD_PASSWORD = "<long-random-password>"
$env:NOVA_DASHBOARD_ALLOWED_HOSTS = "localhost,127.0.0.1,[::1]"
$env:NOVA_DASHBOARD_ALLOWED_ORIGINS = "http://127.0.0.1:8788,http://localhost:8788"
```

Generate and store the password with a password manager. The application intentionally returns HTTP 503 when credentials are missing.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --requirement requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8788
```

Open `http://127.0.0.1:8788` and sign in with the configured credentials.

Do not bind this dashboard to `0.0.0.0`, expose it through router port forwarding, or publish it through an unauthenticated tunnel.

## Safety boundary

The dashboard can adjust local opportunity priority and operate local review workflows. It must not publish, purchase, send outreach, create accounts, use credentials, or modify live assets without the separate approval controls documented by the project.
