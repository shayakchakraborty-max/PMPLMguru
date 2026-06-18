// Proxies the document blob store (S3 at deploy / local fallback).
//   POST { owner, scope, filename, content_base64, content_type } -> { key, url }
//   GET  ?owner=&key=  -> document (local) or presigned url (s3)
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body; try { body = await req.json(); } catch { return Response.json({ error: "bad json" }, { status: 200 }); }
  try {
    const r = await fetch(`${BRAIN}/blob`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) { return Response.json({ error: `Upload failed (${e.message}).` }, { status: 200 }); }
}

export async function GET(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  const { searchParams } = new URL(req.url);
  const owner = encodeURIComponent(searchParams.get("owner") || "demo");
  const key = encodeURIComponent(searchParams.get("key") || "");
  try {
    const r = await fetch(`${BRAIN}/blob?owner=${owner}&key=${key}`, { headers: { "Content-Type": "application/json" } });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) { return Response.json({ error: `Fetch failed (${e.message}).` }, { status: 200 }); }
}
