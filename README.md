# AffiForge

An affiliate content workspace for researching topics, planning articles, reviewing drafts,
publishing to WordPress, and tracking reported commissions by post and network.

## Run the local demo

From this repository's root, with Docker and Docker Compose v2 installed:

```sh
cp affiforge/.env.example affiforge/.env
docker compose --env-file affiforge/.env -f affiforge/infra/docker-compose.yml up --build --wait
```

Open [http://localhost:3000](http://localhost:3000), create an account, and connect a demo
site such as `https://example.com`. The demo uses local research examples and simulates
publishing. Dashboard totals come from records entered in that installation.

## Deploy

The [production runbook](affiforge/docs/PRODUCTION.md) covers domains, secrets, migrations,
provider setup, and database backups. The Compose stack includes Next.js, FastAPI,
PostgreSQL, Redis, and Caddy.

## Verify locally

```sh
cd affiforge
python -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m pytest

cd frontend
npm ci
npm run lint
npm run typecheck
npm run build
```
