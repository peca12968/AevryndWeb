interface Env {
  DB: D1Database;
}

interface StatsRequest {
  sessionId?: unknown;
  viewId?: unknown;
}

const ONLINE_WINDOW_MS = 70_000;
const SESSION_RETENTION_MS = 24 * 60 * 60 * 1000;
const ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), {
  status,
  headers: {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
  },
});

const readStats = async (db: D1Database, now: number) => {
  const cutoff = now - ONLINE_WINDOW_MS;
  const [onlineRow, viewsRow] = await Promise.all([
    db.prepare('SELECT COUNT(*) AS count FROM online_sessions WHERE last_seen >= ?').bind(cutoff).first<{ count: number }>(),
    db.prepare('SELECT COUNT(*) AS count FROM page_views').first<{ count: number }>(),
  ]);

  return {
    online: Number(onlineRow?.count ?? 0),
    totalViews: Number(viewsRow?.count ?? 0),
  };
};

const updateStats = async (request: Request, env: Env) => {
  let body: StatsRequest;
  try {
    body = await request.json<StatsRequest>();
  } catch {
    return json({ error: 'Invalid JSON body.' }, 400);
  }

  if (typeof body.sessionId !== 'string' || !ID_PATTERN.test(body.sessionId)) {
    return json({ error: 'Invalid session ID.' }, 400);
  }
  if (body.viewId !== undefined && (typeof body.viewId !== 'string' || !ID_PATTERN.test(body.viewId))) {
    return json({ error: 'Invalid view ID.' }, 400);
  }

  const now = Date.now();
  const statements = [
    env.DB.prepare(`
      INSERT INTO online_sessions (session_id, last_seen)
      VALUES (?, ?)
      ON CONFLICT(session_id) DO UPDATE SET last_seen = excluded.last_seen
    `).bind(body.sessionId, now),
    env.DB.prepare('DELETE FROM online_sessions WHERE last_seen < ?').bind(now - SESSION_RETENTION_MS),
  ];

  if (typeof body.viewId === 'string') {
    statements.push(
      env.DB.prepare('INSERT OR IGNORE INTO page_views (view_id, session_id, viewed_at) VALUES (?, ?, ?)')
        .bind(body.viewId, body.sessionId, now),
    );
  }

  await env.DB.batch(statements);
  return json(await readStats(env.DB, now));
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname !== '/api/stats') return json({ error: 'Not found.' }, 404);

    if (request.method === 'GET') return json(await readStats(env.DB, Date.now()));
    if (request.method === 'POST') return updateStats(request, env);
    return new Response(null, { status: 405, headers: { allow: 'GET, POST' } });
  },
} satisfies ExportedHandler<Env>;
