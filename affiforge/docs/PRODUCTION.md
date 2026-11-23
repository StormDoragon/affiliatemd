# AffiForge production runbook

## Release scope

The workspace supports operator-provisioned accounts, optional public registration,
Reddit search, OpenAI content plans and text drafts, manual drafts, reviewed WordPress
publishing, Amazon.com affiliate links built from user-provided ASINs, and self-reported
USD commissions by post and network. Optional Stripe Checkout and the Stripe Customer
Portal manage subscriptions. Subscription status is read from Stripe when requested.
Paid-workspace entitlements, automatic affiliate-network imports, automatic payouts,
and the experimental Celery workflows are outside this release.

## Host and configuration

Use a Linux host that can run Docker Compose v2. Point a domain's DNS at the host and open
TCP 80 and 443. PostgreSQL, Redis, FastAPI and Next.js communicate over Docker networks.
Caddy serves the site over HTTPS. Use a persistent disk with enough space for the database,
Redis, and backups.

Copy `affiforge/.env.example` to `affiforge/.env` on the host. Restrict file access to the
deployment account. Set these production values before starting the stack.

| Variable | Production value |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `DEMO_MODE` | `false` |
| `ALLOW_REGISTRATION` | `false` for an invited beta |
| `APP_ORIGIN` | `https://affiliate.example.com` |
| `CADDY_SITE` | `affiliate.example.com` |
| `PUBLISH_ADDRESS` | `0.0.0.0` |
| `PUBLISH_HTTP_PORT`, `PUBLISH_HTTPS_PORT` | `80`, `443` |
| `POSTGRES_PASSWORD` | Random URL-safe password, used by PostgreSQL and its connection string |
| `JWT_SECRET_KEY` | Separate random secret of at least 32 characters |
| `CREDENTIAL_ENCRYPTION_KEY` | Fernet key, retained separately from backups |

Generate each database and session secret separately with `openssl rand -hex 32`.
For the Fernet key, run `python -c 'import secrets; print(secrets.token_urlsafe(32) + "=")'`.
Keep a protected copy of this key. Sites must be reconnected if it is lost or changed.

Define a shell helper at the repository root for the remaining commands.

```sh
compose() {
  docker compose --env-file affiforge/.env -f affiforge/infra/docker-compose.yml "$@"
}
compose config --quiet
compose up --build --wait --wait-timeout 180
compose ps -a
compose exec backend python -m src.manage create-user owner@example.com --name Owner
```

The one-shot `migrate` service runs Alembic before the backend starts. At startup, check
that it exited successfully and the long-running services are healthy. Use the same
operator command with `reset-password` to recover an account and invalidate its sessions.

## Provider setup

| Provider | Setup and verification |
| --- | --- |
| WordPress | A public HTTPS WordPress site with IPv4 DNS, REST API, and an application password for an account with `publish_posts`. Use the canonical URL and include its subdirectory if applicable. Test with a disposable post on a staging site first. |
| OpenAI | Set `OPENAI_API_KEY` for a project with `gpt-4o-mini` access. Generate a small content plan and a draft. Review factual claims, and set a project-level spend limit. |
| Reddit | Once your Reddit application has API access, set `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and an identifying `REDDIT_USER_AGENT`. Search a known discussion. |
| Stripe | Set `STRIPE_SECRET_KEY` and a comma-separated list of recurring `STRIPE_PRICE_IDS` from the same account and mode. Configure the Stripe Customer Portal. Verify Checkout, return to the dashboard, status, and cancellation with Stripe test credentials before enabling live keys. |

Keep provider secrets server-side. With no provider configured, the corresponding feature
returns an availability error. Manual drafts and reported earnings work independently.
Public registration is optional. For a beta, provision accounts via the operator command.

If a WordPress publish returns an error after submission, retry against the same connection.
AffiForge records a stable publishing slug before calling WordPress and checks it before
creating a post. If credentials changed, use **Update credentials** on the original
connection. A legacy publishing record can lack a remote URL.

## Backups and verification

Before each release and at a regular interval, dump PostgreSQL to encrypted storage.
Verify that restoration works on a separate database. Keep the Fernet key separately and
protect both assets as credentials. A backup command from the repository root:

```sh
umask 077
compose exec -T postgres pg_dump -U affiforge -d affiforge -Fc > affiforge.dump
```

Check service health and logs, then sign in, connect a staging WordPress site, publish
a reviewed disposable draft, record a test commission and confirm it appears once after
refresh. Check that signed-out users are redirected and that a second account cannot
read the first one's drafts or earnings.

```sh
curl -fsS https://affiliate.example.com/
compose exec backend python -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8000/readyz").read().decode())'
compose exec backend alembic current
compose logs --tail=100 backend frontend caddy
```

For an existing Alembic-managed PostgreSQL installation, back up before enabling the
new release. The migration preserves draft and earnings rows and stores monetary amounts
to the cent. Legacy WordPress passwords must be re-entered in **Update credentials**.
Any real credentials or reusable passwords from the earlier committed development database
should be rotated. Treat the Git history of this public repository as public.

If you keep Vercel for the frontend, build from `affiforge/frontend`. Provide a reachable
FastAPI deployment through `INTERNAL_API_URL` and set the Vercel frontend and backend to
the same canonical `APP_ORIGIN`. A frontend-only build cannot provide the workspace.
Use private connectivity between the services or an authenticated network gateway.
The included Compose deployment hosts all services together on one machine.
