# Nova Money Scout Dashboard

Local-only dashboard for Nova Money Scout.

## Run

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8788 --reload

Open:

http://127.0.0.1:8788

## Safety

Dashboard v1 can Boost/Bury local opportunity priority only.

It does not publish, sell, outreach, spend, commit, push, create accounts, use credentials, change affiliate links, or modify live sites.
