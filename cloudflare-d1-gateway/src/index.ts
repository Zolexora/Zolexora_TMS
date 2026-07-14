/**
 * Minimal authenticated proxy in front of D1.
 *
 * This deliberately contains almost no business logic. All validation,
 * dimension resolution, permission checks, and audit logging live in the
 * FastAPI backend (on Render); this Worker's only job is:
 *
 *   1. Check the bearer token matches GATEWAY_TOKEN.
 *   2. Run the parameterized SQL it's given against the D1 binding.
 *   3. Return the rows/meta.
 *
 * This mirrors Cloudflare's own documented pattern for reaching D1 from a
 * non-Worker app (e.g. a Rails/Django/FastAPI backend hosted elsewhere):
 * https://developers.cloudflare.com/d1/tutorials/build-an-api-to-access-d1/
 * Their built-in Admin REST API for D1 is explicitly rate-limited and
 * meant for administrative/ad-hoc use, not hot-path application traffic,
 * which is why this thin Worker exists instead of calling that API
 * directly from FastAPI.
 *
 * SECURITY MODEL: whoever holds GATEWAY_TOKEN has full read/write access to
 * every table in this D1 database. Treat this Worker's URL + token as
 * sensitive as a database connection string -- never expose either to a
 * browser or to any client other than the FastAPI backend.
 */
import { Hono } from 'hono';

interface Env {
  DB: D1Database;
  GATEWAY_TOKEN: string;
}

interface StatementInput {
  sql: string;
  params?: unknown[];
}

const app = new Hono<{ Bindings: Env }>();

app.get('/gateway/health', (c) => c.json({ status: 'ok' }));

app.use('/gateway/*', async (c, next) => {
  if (c.req.path === '/gateway/health') return next();
  const auth = c.req.header('authorization') || '';
  const expected = `Bearer ${c.env.GATEWAY_TOKEN}`;
  if (!c.env.GATEWAY_TOKEN || auth !== expected) {
    return c.json({ error: 'Unauthorized', message: 'Invalid or missing gateway token' }, 401);
  }
  await next();
});

function toD1Result(result: D1Result<unknown>) {
  return {
    results: (result.results ?? []) as Record<string, unknown>[],
    meta: {
      last_row_id: result.meta?.last_row_id ?? null,
      changes: result.meta?.changes ?? 0,
      rows_read: result.meta?.rows_read ?? 0,
      rows_written: result.meta?.rows_written ?? 0,
    },
  };
}

app.post('/gateway/query', async (c) => {
  const body = await c.req.json<StatementInput>();
  if (!body || typeof body.sql !== 'string') {
    return c.json({ error: 'Bad Request', message: 'sql is required' }, 400);
  }
  try {
    const stmt = c.env.DB.prepare(body.sql).bind(...(body.params ?? []));
    const result = await stmt.all();
    return c.json(toD1Result(result));
  } catch (err) {
    return c.json({ error: 'D1 Error', message: err instanceof Error ? err.message : String(err) }, 500);
  }
});

app.post('/gateway/batch', async (c) => {
  const body = await c.req.json<{ statements: StatementInput[] }>();
  if (!body || !Array.isArray(body.statements) || body.statements.length === 0) {
    return c.json({ error: 'Bad Request', message: 'statements must be a non-empty array' }, 400);
  }
  try {
    const prepared = body.statements.map((s) => c.env.DB.prepare(s.sql).bind(...(s.params ?? [])));
    const results = await c.env.DB.batch(prepared);
    return c.json({ results: results.map(toD1Result) });
  } catch (err) {
    return c.json({ error: 'D1 Error', message: err instanceof Error ? err.message : String(err) }, 500);
  }
});

app.notFound((c) => c.json({ error: 'Not Found', message: 'Unknown gateway route' }, 404));

export default app;
