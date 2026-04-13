// frontend/app/api/pipeline/route.js
// Proxies PM planning and PLM execution requests to the Render backend brain.
// Auto-fallback: tries v9.1 paths first, falls back to legacy /pipeline/* paths on 404.
// Never returns a raw 500 - always wraps upstream failures in a 200 with an error field.

export const runtime = "nodejs";
export const maxDuration = 300;

const BRAIN = (process.env.BRAIN_URL || "").replace(/\/$/, "");

const ENDPOINTS = {
  pm: ["/pm/plan", "/pipeline/plan", "/plan"],
  plm: ["/plm/execute", "/pipeline/execute", "/execute"],
  workspace: ["/workspace/seed", "/workspace/create"],
};

async function tryBackend(paths, payload) {
  let lastError = null;
  for (const path of paths) {
    const url = `${BRAIN}${path}`;
    try {
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const text = await r.text();

      if (r.status === 404) {
        lastError = `${path} -> 404`;
        continue;
      }

      let data;
      try {
        data = JSON.parse(text);
      } catch {
        lastError = `${path} -> non-JSON (HTTP ${r.status}): ${text.slice(0, 200)}`;
        continue;
      }

      if (!r.ok) {
        return { ok: false, error: `Backend ${path} returned HTTP ${r.status}`, detail: data };
      }

      return { ok: true, data, used: path };
    } catch (e) {
      lastError = `${path} -> ${e.message}`;
      continue;
    }
  }
  return {
    ok: false,
    error: `All backend endpoints failed. Last error: ${lastError}. Render may be sleeping (wait 30s) or the backend wasn't updated. Check ${BRAIN}/health to see which version is running.`,
  };
}

export async function POST(req) {
  if (!BRAIN) {
    return Response.json(
      { error: "BRAIN_URL environment variable is not set in Vercel. Add it under Project Settings -> Environment Variables." },
      { status: 200 }
    );
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON in request body" }, { status: 200 });
  }

  const stage = body.stage || "pm";
  const paths = ENDPOINTS[stage] || ENDPOINTS.pm;
  const payload = { idea: body.idea, pm_plan: body.pm_plan || null };

  const result = await tryBackend(paths, payload);

  if (!result.ok) {
    return Response.json({ error: result.error, detail: result.detail }, { status: 200 });
  }

  return Response.json(result.data, { status: 200 });
}

export async function GET() {
  if (!BRAIN) {
    return Response.json({ error: "BRAIN_URL not set" }, { status: 200 });
  }
  try {
    const r = await fetch(`${BRAIN}/health`);
    const data = await r.json();
    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json({ error: e.message }, { status: 200 });
  }
}
