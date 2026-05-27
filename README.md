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
pytest --cov=app --cov-fail-under=85
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
bound to the caller's tenant id (derived from the verified token). Reads go
through `scope.query(Model)`, which adds the tenant filter; single-row fetches
go through `scope.get_owned(Model, id)`, which returns the row only if it
belongs to the caller's tenant; writes go through `scope.add`, which stamps the
tenant id. Tests assert that a user from one tenant cannot read or mutate
another tenant's rows for every resource.

## Billing

Checkout creates a Stripe subscription session in test mode. The webhook
handler verifies the Stripe signature, records each event id in
`processed_events` under a unique constraint, and applies the subscription
state implied by the event type. A replayed event is detected by its id and is
not applied twice, so duplicate deliveries do not double-apply a transition.

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
