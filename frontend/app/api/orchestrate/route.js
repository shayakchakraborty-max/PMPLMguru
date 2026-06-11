// frontend/app/api/orchestrate/route.js
// Proxies the Managing-Partner super-agent.
//   POST -> /orchestrate  (problem + ERP intake) -> curated Big-4 engagement
// Deterministic core (+ optional Groq partner brief). Never returns a raw 500.

export const runtime = "nodejs";
export const maxDuration = 60;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body;
  try { body = await req.json(); } catch { return Response.json({ error: "Invalid JSON body" }, { status: 200 }); }
  try {
    const r = await fetch(`${BRAIN}/orchestrate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Engagement failed (${e.message}). The backend may be waking up — retry in ~30s.` }, { status: 200 });
  }
}
