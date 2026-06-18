// Proxies meeting capture + AI minutes (MoM).
//   GET ?owner=&engagement_id=  -> meetings + rolled-up registers
//   GET ?owner=&id=             -> one meeting
//   POST { action:"add"|"analyze", owner, engagement_id, title, type, attendees, transcript, audio_key }
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 45;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  const { searchParams } = new URL(req.url);
  const owner = encodeURIComponent(searchParams.get("owner") || "demo");
  const id = searchParams.get("id"); const eid = searchParams.get("engagement_id");
  const url = id ? `${BRAIN}/meeting?owner=${owner}&id=${encodeURIComponent(id)}`
                 : `${BRAIN}/meetings?owner=${owner}${eid ? `&engagement_id=${encodeURIComponent(eid)}` : ""}`;
  try { const r = await fetch(url, { headers: { "Content-Type": "application/json" } }); return Response.json(await r.json(), { status: 200 }); }
  catch (e) { return Response.json({ error: `Could not reach the brain (${e.message}).` }, { status: 200 }); }
}

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body; try { body = await req.json(); } catch { return Response.json({ error: "bad json" }, { status: 200 }); }
  const path = body.action === "analyze" ? "/meeting/analyze"
    : body.action === "propose" ? "/meeting/propose"
    : body.action === "schedule" ? "/meeting/schedule"
    : "/meetings";
  try { const r = await fetch(`${BRAIN}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); return Response.json(await r.json(), { status: 200 }); }
  catch (e) { return Response.json({ error: `Action failed (${e.message}).` }, { status: 200 }); }
}
