// frontend/app/api/prototype/route.js
// Proxies prototype generation to the Render backend brain.

export const runtime = "nodejs";
export const maxDuration = 300;

const BRAIN = (process.env.BRAIN_URL || "").replace(/\/$/, "");

export async function POST(req) {
  if (!BRAIN) {
    return Response.json({ error: "BRAIN_URL not set in Vercel environment" }, { status: 200 });
  }
  let body;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON in request body" }, { status: 200 });
  }
  try {
    const r = await fetch(`${BRAIN}/plm/prototype`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea: body.idea }),
    });
    const text = await r.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { error: `Backend returned non-JSON: ${text.slice(0, 500)}` };
    }
    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json(
      { error: `Failed to reach backend. Render free tier may be sleeping - wait 30s and retry. Detail: ${e.message}` },
      { status: 200 }
    );
  }
}
