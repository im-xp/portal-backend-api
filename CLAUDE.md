# Portal Backend API — Claude Code Context

FastAPI backend for the pop-up city portal. **Legacy / reference** in IMXP's stack — kept for migration context. The active backend for new work is `edgeos-monorepo/backend/`.

Repo on GitHub: `im-xp/portal-backend-api` (an IMXP-owned copy of the SimpleFi-authored open-source `EdgeOS_API`).

## What this repo is

The original FastAPI codebase that `edgeos-monorepo/backend/` evolved from. Open-source provenance: SimpleFi (p2p planes) + EdgeCity + Esmeralda. IMXP runs the upstream stack and contributed/forks features here.

Pop-up city domain — applications, attendees, citizens, payments, passes, popups, products, groups, coupons, achievements, check-in, world-builders, organizations.

## Top-level layout

| Path | Purpose |
|---|---|
| `main.py` | FastAPI entrypoint |
| `app/api/` | REST modules: `applications/`, `attendees/`, `citizens/`, `payments/`, `popup_city/`, `products/`, `groups/`, `check_in/`, `coupon_codes/`, `email_logs/`, `webhooks/`, `account_clusters/`, `access_tokens/`, `authorized_third_party_apps/`, `achievements/`, `world_builders/`, `organizations/`, `product_segments/`, `common/` |
| `app/core/` | Auth, config, common dependencies |
| `app/processes/` | Background jobs: `abandoned_cart.py`, `auto_approval.py`, `send_prearrival_emails.py`, `send_reminder_emails.py`, `send_scheduled_emails.py` |
| `app/data/` | Data access layer / seed data |
| `docs/` | Repo-local docs |
| `tests/` | Pytest suite |
| `scripts/` | Operational scripts |
| `Dockerfile`, `docker-compose.yml`, `Procfile` | Container + deploy config |
| `init.sql` | DB bootstrap |

## When to read this repo

- Tracing legacy behavior that IMXP customers still hit (where the production deploy of this codebase, vs. EdgeOS, is the live one).
- Understanding why a payment / application flow in EdgeOS was designed a certain way — answers often live here as the original implementation.
- Reference for the open-source upstream.

## When NOT to edit this repo

- New feature work → `edgeos-monorepo/backend/`.
- Patching prod issues → check first whether the affected endpoint is served by this repo or by `edgeos-monorepo/backend/`. Don't fix in the wrong place.

## Running locally (per README)

`docker compose up` brings up FastAPI + Postgres + a NocoDB UI for browsing the DB. OpenAPI docs at the running service's `/docs`.

## Out of scope

- Frontend / portal pages → `portal-frontend` (consumer of this API in legacy deploys), or `edgeos-monorepo/portal` (consumer of the new backend).
- Operator dashboard → `portal-dashboard`.
- Customer-profile pipeline → `pat-profile-cloud`.
