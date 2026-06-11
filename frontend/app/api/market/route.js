// frontend/app/api/market/route.js
// Proxies the MSME Intelligence Database.
//   GET  -> /market/sectors + /market/segments (merged tree)
//   POST -> /market/lookup (business type / sector / free-text) -> intelligence card
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET() {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  try {
    const [a, b] = await Promise.all([
      fetch(`${BRAIN}/market/sectors`, { headers: { "Content-Type": "application/json" } }).then((r) => r.json()),
      fetch(`${BRAIN}/market/segments`, { headers: { "Content-Type": "application/json" } }).then((r) => r.json()),
    ]);
    return Response.json({ ...a, segments: b.segments || [], by_sector: b.by_sector || {} }, { status: 200 });
  } catch (e) {
    return Response.json({ error: `Could not reach the brain (${e.message}). It may be waking up — retry in ~30s.` }, { status: 200 });
  }
}

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body;
  try { body = await req.json(); } catch { return Response.json({ error: "Invalid JSON body" }, { status: 200 }); }
  try {
    const r = await fetch(`${BRAIN}/market/lookup`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Lookup failed (${e.message}).` }, { status: 200 });
  }
}
