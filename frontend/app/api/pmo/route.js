// frontend/app/api/pmo/route.js
// Proxies the AI PMO generator: POST an engagement -> PM workspace (OKRs, sprints, tasks).
export const runtime = "nodejs";
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body;
  try { body = await req.json(); } catch { return Response.json({ error: "Invalid JSON body" }, { status: 200 }); }
  try {
    const r = await fetch(`${BRAIN}/pmo`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ engagement: body }) });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `PMO build failed (${e.message}).` }, { status: 200 });
  }
}
