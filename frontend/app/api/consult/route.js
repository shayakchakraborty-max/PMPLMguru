// frontend/app/api/consult/route.js
// Proxies the AI-native consulting brain to the backend (Railway).
//   GET  -> /consult/meta  (intake form schema + sectors + modes)
//   POST -> /consult       (structured intake) -> customised engagement
// Long maxDuration: live LLM + web search can take 10-30s. Never returns a raw 500.

export const runtime = "nodejs";
export const maxDuration = 60;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET() {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  try {
    const r = await fetch(`${BRAIN}/consult/meta`, { headers: { "Content-Type": "application/json" } });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Could not reach the brain (${e.message}). It may be waking up — retry in ~30s.` }, { status: 200 });
  }
}

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body;
  try { body = await req.json(); } catch { return Response.json({ error: "Invalid JSON body" }, { status: 200 }); }
  if (!body.description) return Response.json({ error: "Please describe your business." }, { status: 200 });
  try {
    const r = await fetch(`${BRAIN}/consult`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Engagement failed (${e.message}). The backend may be waking up — retry in ~30s.` }, { status: 200 });
  }
}
