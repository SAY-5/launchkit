# LaunchKit

A multi-tenant SaaS starter. It ships the pieces a new product needs on day one:
account sign-up, organization-scoped data, Stripe billing, and one working
in-product feature. The backend is FastAPI on Postgres; the frontend is Next.js
with TypeScript.

## What is included

- Email and password auth with bcrypt hashing and JWT access tokens.
- A tenant (organization) model where every row is scoped to a tenant.
- A data-access guard that injects the tenant filter and checks row ownership,
  so isolation is enforced server-side rather than by convention.
- Stripe Checkout for upgrades and a webhook handler that drives subscription
  state and deduplicates replayed events.
- A "summarize a note" feature backed by a provider interface. A deterministic
  fake provider runs locally and in CI with no network calls; a real provider
  can be plugged in behind the same interface.
- Next.js pages: landing, sign-up, sign-in, dashboard, billing, and the feature.
- docker-compose for Postgres, the API, and the web app.

## Layout

```
backend/   FastAPI app, models, services, tests
web/        Next.js app, lib, unit tests, Playwright e2e
docker-compose.yml
.env.example
```

## Running locally

Copy the environment template and start the stack:

```bash
cp .env.example .env
docker compose up --build
```

The web app is at http://localhost:3000 and the API at http://localhost:8000.

### Backend tests

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
ruff check app tests
mypy app
pytest --cov=app --cov-fail-under=90
```

### Frontend tests

```bash
cd web
npm ci
npm run lint
npm run typecheck
npm run test
```

## Tenant isolation

Routes never receive a raw database session. They receive a `TenantScope`
bound to the caller's tenant id (derived from the verified token):

- `scope.query(Model)` adds the tenant filter to the select.
- `scope.require_owned(Model, id)` returns a row only if it belongs to the
  caller's tenant; a cross-tenant id reads as a missing row (404).
- `scope.add(obj)` stamps the tenant id and rejects an object carrying another.
- `scope.save(obj)` re-checks ownership before committing a mutation, so a write
  can never escape the caller's tenant.

Each method also asserts the model carries a `tenant_id` column, so a
non-scoped model cannot be passed in by mistake. Tests drive every note
operation (read, update, delete, summarize) across a tenant boundary and assert
the API rejects the cross-tenant attempt, so isolation is proven at the API
rather than assumed by convention.

## Billing

Checkout creates a Stripe subscription session in test mode. The webhook
handler verifies the Stripe signature and applies the subscription state
implied by the event type: `checkout.session.completed` activates,
`invoice.payment_failed` moves to past_due, `customer.subscription.updated`
carries its own status, and `customer.subscription.deleted` cancels.

Idempotency has two layers. Each event id is checked against `processed_events`
before any mutation, and the column carries a unique constraint so a concurrent
duplicate that slips past the check fails on insert and is reported as a
duplicate. A replayed delivery therefore never double-applies a transition; a
test replays the same event twice and asserts a single state change and a single
recorded event id.

## Benchmark

`backend/bench/bench_notes_list.py` seeds two tenants with 2000 notes each and
times 200 authenticated requests to the tenant-scoped list endpoint. On a local
run it reports a median of about 16.7 ms and a p95 of about 37.7 ms; the exact
numbers depend on the machine. The `bench-regress` CI job runs a reference pass
and a current pass on the same runner and fails if the current median exceeds
the reference by more than 30 percent, which catches a structural regression in
the hot path.

```bash
cd backend
python -m bench.bench_notes_list --notes 2000 --iterations 200
python -m bench.check_regression
```

## Configuration

All configuration is read from environment variables; see `.env.example`. No
secrets are committed. The provider mode defaults to `fake`.

## How this differs

LaunchKit is a zero-to-one SaaS starter: FastAPI, Next.js, Postgres, Stripe,
and tenant isolation in one repository, aimed at getting a first customer signed
up and billed. It is not a subscription manager. `subscription-portal`, for
example, is a Django application for managing existing subscriptions; LaunchKit
is the upstream starter you build a product on. The angle here is tenant
isolation treated as a security boundary, enforced at the data-access layer,
plus idempotent Stripe webhook handling.

## License

MIT. See [LICENSE](LICENSE).
