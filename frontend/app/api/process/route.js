// frontend/app/api/process/route.js
// Proxies the Process & Value-Stream Copilot to the backend (Railway).
//   GET  -> /process/meta   (business types + lanes + team roles)
//   POST -> /process        (business description / key) -> full engagement map
// Deterministic backend core (+ optional Groq partner brief). Never returns a raw 500.

export const runtime = "nodejs";
export const maxDuration = 45;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET() {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  try {
    const r = await fetch(`${BRAIN}/process/meta`, { headers: { "Content-Type": "application/json" } });
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
    const r = await fetch(`${BRAIN}/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Process mapping failed (${e.message}). The backend may be waking up — retry in ~30s.` }, { status: 200 });
  }
}
