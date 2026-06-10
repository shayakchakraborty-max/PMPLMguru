// frontend/app/api/catalog/route.js
// Proxies the Consulting Catalog (Towers L1 -> Service Lines L2 -> Workflows L3).
//   GET  -> /catalog          (full annotated tree + core_12 + ai_advisors)
//   POST -> /catalog/resolve  (free-text need -> tower / service line / agent)
// Deterministic backend. Never returns a raw 500.

export const runtime = "nodejs";
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET() {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  try {
    const r = await fetch(`${BRAIN}/catalog`, { headers: { "Content-Type": "application/json" } });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Could not reach the brain (${e.message}). It may be waking up — retry in ~30s.` }, { status: 200 });
  }
}

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body;
  try { body = await req.json(); } catch { return Response.json({ error: "Invalid JSON body" }, { status: 200 }); }
  try {
    const r = await fetch(`${BRAIN}/catalog/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Routing failed (${e.message}). The backend may be waking up — retry in ~30s.` }, { status: 200 });
  }
}
