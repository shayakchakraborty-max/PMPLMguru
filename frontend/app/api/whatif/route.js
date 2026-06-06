// frontend/app/api/whatif/route.js
// What-if simulator: POST tweaked numbers -> recomputed scorecard + value-at-stake + benchmark.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 15;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body;
  try { body = await req.json(); } catch { return Response.json({ error: "Invalid JSON body" }, { status: 200 }); }
  try {
    const r = await fetch(`${BRAIN}/whatif`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Simulate failed (${e.message}).` }, { status: 200 });
  }
}
