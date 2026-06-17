// frontend/app/api/twin/route.js
// Proxies the Engagement Digital-Twin store (server-side persistence + portfolio).
//   GET  ?owner=X            -> { engagements:[...], portfolio:{...} }
//   GET  ?owner=X&id=Y       -> { report:{...} }
//   POST { action:"delete", owner, id }
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  const { searchParams } = new URL(req.url);
  const owner = encodeURIComponent(searchParams.get("owner") || "demo");
  const id = searchParams.get("id");
  try {
    if (id) {
      const r = await fetch(`${BRAIN}/engagement?owner=${owner}&id=${encodeURIComponent(id)}`, { headers: { "Content-Type": "application/json" } });
      return Response.json(await r.json(), { status: 200 });
    }
    const [list, pf] = await Promise.all([
      fetch(`${BRAIN}/engagements?owner=${owner}`).then((r) => r.json()),
      fetch(`${BRAIN}/portfolio?owner=${owner}`).then((r) => r.json()),
    ]);
    return Response.json({ engagements: list.engagements || [], count: list.count || 0, portfolio: pf }, { status: 200 });
  } catch (e) {
    return Response.json({ error: `Could not reach the brain (${e.message}).` }, { status: 200 });
  }
}

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body;
  try { body = await req.json(); } catch { return Response.json({ error: "Invalid JSON body" }, { status: 200 }); }
  try {
    const r = await fetch(`${BRAIN}/engagements/delete`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Delete failed (${e.message}).` }, { status: 200 });
  }
}
