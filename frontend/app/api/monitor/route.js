// frontend/app/api/monitor/route.js
// Proxies the Monitoring / Business Command Center module to the backend.
//   GET  -> /monitor/meta  (metric definitions)
//   POST -> /monitor       (KPI snapshot + profile) -> command center
// Deterministic backend (no LLM needed). Never returns a raw 500.

export const runtime = "nodejs";
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET() {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  try {
    const r = await fetch(`${BRAIN}/monitor/meta`, { headers: { "Content-Type": "application/json" } });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Could not reach the brain (${e.message}).` }, { status: 200 });
  }
}

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body;
  try { body = await req.json(); } catch { return Response.json({ error: "Invalid JSON body" }, { status: 200 }); }
  try {
    const r = await fetch(`${BRAIN}/monitor`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Monitoring failed (${e.message}). The backend may be waking up — retry in ~30s.` }, { status: 200 });
  }
}
