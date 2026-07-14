# ZolexoraERP Lite -- Production Architecture

This is a rewrite of the original Cloudflare Workers/Hono/D1 backend onto:

- **FastAPI (Python)**, hosted on **Render** -- owns 100% of the business logic.
- **Supabase** -- Postgres for masters data, and Supabase Auth for identity.
- **Cloudflare D1** -- transactional/operational data (ledger entries, audit logs, import jobs), reached through a small proxy Worker.
- **Frontend** -- the original React/Vite/Tailwind app, adapted to call the new backend and sign in via Supabase Auth.

```
frontend/                 React app (Vite). Deploy the built static output anywhere
                           (Cloudflare Pages is a natural fit since you're already on Cloudflare).
backend-fastapi/          The FastAPI app. Deploy this to Render. This is the only
                           service that talks to both databases and holds business logic.
cloudflare-d1-gateway/     A small Cloudflare Worker. Its only job is to execute
                           parameterized SQL against D1 on FastAPI's behalf.
supabase/migrations/       Postgres schema for masters data (run in the Supabase SQL editor
                           or via the Supabase CLI).
```

## Why this split (and one change from a literal reading of the brief)

Masters (companies, sites, clients, managers, vehicles, P&L groups, chart of
accounts, financial years/periods) live in Supabase Postgres, alongside
Supabase Auth -- a natural pairing since access-control data (who can see
which company) sits next to identity anyway.

Transactional data (entry batches, ledger lines, audit logs, import jobs)
stays in Cloudflare D1, per the brief.

**The one deliberate deviation:** Cloudflare's own documentation says D1's
Admin REST API is rate-limited and meant for administrative/ad-hoc use, not
application hot-path traffic, and its own tutorial for reaching D1 from a
non-Worker backend (their example is Rails/Django -- this is that same
shape) is to put a thin authenticated Worker in front of D1. That's what
`cloudflare-d1-gateway/` is: it holds no business logic, just "does the
bearer token match, if so run this SQL." FastAPI calls it like a database
driver. If you'd rather avoid deploying a second service, `D1_ACCESS_MODE`
also supports `direct_admin_api` (calls Cloudflare's Admin API directly) --
see `app/db/d1_client.py` for the tradeoffs; batches in that mode are
sequential, not atomic.

## Architecture tradeoffs worth knowing about

- **Cross-database referential integrity is now enforced in code, not SQL.**
  Entry_Batches used to have foreign keys into Companies/sites/clients/
  vehicles/managers. Those tables now live in a different database, so D1
  can no longer check them at the SQL level -- `entries/service.py`
  resolves and validates every dimension against Postgres before writing to
  D1, but that protection only exists for writes that go through FastAPI.
  Anything writing to D1 directly (bypassing the gateway's normal callers)
  would not get it.
- **No Cloudflare Queues or Cron Triggers** (Render has no equivalent).
  Bulk CSV import is now synchronous request/response instead of
  queue-based (see "Imports" below). Scheduled maintenance should be set up
  as a Render Cron Job calling a script in `backend-fastapi/scripts/` (add
  scripts there as you need them).
- **No Cloudflare KV.** The old "is this batch already reversed" check used
  a KV flag; it's now a `reversal_batch_id` column on `Entry_Batches`
  instead (simpler, one less moving part, no behavior change).
- **Single-role-per-user**, not the old `users`/`roles`/`user_roles` join
  tables -- `UserSession.role` was always exposed as one role, never
  actually used as multi-role, so `user_profiles.role` is a plain column.

## Setup

### 1. Supabase

1. Create a project at supabase.com.
2. SQL Editor -> run `supabase/migrations/0001_masters_schema.sql`.
3. Settings -> API: copy the Project URL and anon/publishable key (frontend
   needs these).
4. Settings -> Database -> Connection string: copy the **Session pooler**
   URI (backend needs this as `SUPABASE_DB_URL`; Render web services are
   long-running, so the session pooler -- not the transaction pooler -- is
   the right choice).
5. Settings -> API -> JWT Settings tells you whether your project uses the
   newer asymmetric JWT Signing Keys (nothing further to configure -- the
   backend derives the JWKS URL automatically) or the legacy shared secret
   (if so, copy it into `SUPABASE_JWT_SECRET`).

### 2. Cloudflare D1 gateway

```
cd cloudflare-d1-gateway
npm install
wrangler d1 create zolexora-transactional     # paste the returned database_id into wrangler.toml
wrangler d1 migrations apply zolexora-transactional --remote
openssl rand -hex 32                           # generate a token
wrangler secret put GATEWAY_TOKEN              # paste the generated token
wrangler deploy                                # note the resulting workers.dev URL
```

### 3. Backend (Render)

Push `backend-fastapi/` to a repo and create a Render Blueprint from
`render.yaml`, or create a Web Service manually (Python runtime, build
command `pip install -r requirements.txt`, start command
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`). Set the environment
variables from `.env.example` (Supabase connection details, the D1 gateway
URL + the same `GATEWAY_TOKEN` you set above, and `CORS_ALLOWED_ORIGINS`
to your frontend's URL).

### 4. Frontend

```
cd frontend
cp .env.example .env     # fill in VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY / VITE_API_BASE_URL
npm install
npm run build             # outputs to dist/client -- deploy this anywhere static
```

### 5. Create your first Admin

New sign-ups auto-provision as a `Viewer` with no company access (so a
public sign-up form doesn't hand out real access). To bootstrap:

1. Sign up once through the frontend's login page.
2. In the Supabase SQL Editor:
   ```sql
   update user_profiles set role = 'Admin' where email = 'you@example.com';
   ```
3. Sign out and back in. From then on, use `PATCH /api/users/{id}/role` and
   `POST /api/users/{id}/company-access` (both Admin-only) to manage
   everyone else -- these are new endpoints added to support this
   self-service flow; the original app had no user-management API at all.

## What changed in the CSV import flow

The original `imports` module depended on a two-step R2-object-key upload
that the project's own status docs already flagged as disconnected. Rather
than re-plumb that (Render has no R2 binding), `POST /api/imports/validate`
now accepts the CSV directly as a multipart upload, groups rows by a
`batch_reference` column (like a Tally voucher with several ledger lines),
and validates each group by running it through the *same* validation
`entries/service.py` uses for manual entry (no duplicated rules) without
committing. `POST /api/imports/confirm` then commits. Validated-but-
unconfirmed imports are cached in an in-memory dict keyed by a
`validation_id` -- fine for a single Render instance; move it to a
Postgres table if this is ever scaled horizontally.

## Honest status

Everything below has been exercised: `pip install`, backend imports and
boots, a full request round-trip through `TestClient` (auth rejection,
malformed-body handling), `npm run build`/`typecheck`/`lint`/`vitest` on
the frontend, and `tsc --noEmit` on the gateway Worker. None of it has
been run against a real Supabase/Cloudflare project (this sandbox has no
network path to either), so treat first deploy as the real integration
test -- start with `/health` on the backend and the D1 gateway's
`/gateway/health`, then log in.

**Fully ported, including all the original validation/business rules:**
companies, sites, clients (list), P&L groups (including cycle-safe parent
validation), chart of accounts (including the Postgres/D1 balance merge --
see below), financial years/periods (including the close/lock/reopen state
machine), manual journal entries (including dimension resolution and the
transport-company required-fields logic), post/reverse, audit log, the
settings compatibility routes.

**Fixed while porting:** the P&L report's revenue sign bug documented in
the original `.agents/project_status` -- revenue accounts were reporting
negative because the raw `debit - credit` balance was never flipped for
credit-normal accounts. See the comment at the top of
`app/modules/reports/service.py` for the full explanation.

**New, not in the original:** `GET /api/users`, `PATCH /api/users/{id}/role`,
`POST/DELETE /api/users/{id}/company-access` -- the original had no
user-management API at all (access was presumably granted by hand in the
database); Supabase Auth's self-service sign-up makes this a hard
requirement now, not an optional nicety.

**Redesigned rather than ported:** bulk CSV import (see above).

**Matches the original's own scope, not expanded:** `managers` and
`vehicles` have no public routes (same as the original -- they're internal
lookups used only by the entries module); `clients` is list-only (same as
original).

**Not yet ported -- next up:** XLSX import (the original hadn't built this
either), the company-comparison computation, a frontend admin screen for
the new user-management endpoints (the API exists; there's no page for it
yet), and a full 1:1 port of the original's 197 backend tests (a
representative pytest suite for the highest-risk logic -- period date
math and the P&L sign fix -- is included and passing, but it is not full
parity).

### Frontend page-by-page

The original project's own status docs already flagged several pages as
UI shells with mock data, not yet wired to any backend. That didn't change
just because the backend moved -- these still need wiring to the new API:

| Page | Status |
|---|---|
| Login, Companies, Sites, Periods, P&L Groups, Accounts, Manual Entry | Wired to the new backend, working |
| **Entry History** | Wired to the new backend in this pass (was 100% mock data -- this is what the earlier part of this conversation was already fixing before the architecture change) |
| **Reports (P&L), Company Comparison, Audit Logs, Settings, Bulk Upload, Import History** | Still the original mock-data UI shells. The backend endpoints they need (`GET /api/reports/pl`, `GET /api/audit-logs`, `GET/POST /api/settings/*`, `POST /api/imports/validate` \| `/confirm`) all exist and are tested -- these pages just haven't been rewired to call them yet. Same shape of fix as Entry History; good candidates for the next pass. |

## Local development

```
# Terminal 1
cd backend-fastapi && cp .env.example .env   # fill in real values
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Terminal 2
cd frontend && cp .env.example .env
npm install
npm run dev    # proxies /api/* to localhost:8000 in dev
```
