// frontend/app/api/studio/route.js
// Proxies the unified Business Studio report to the backend brain (Railway).
//   POST { idea } -> consolidated research-grade report (DD, market, PLM, PM method, ...)
// Never returns a raw 500 — upstream failures are wrapped in a 200 with an error field.

export const runtime = "nodejs";
export const maxDuration = 120;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function POST(req) {
  if (!BRAIN) {
    return Response.json({ error: "BRAIN_URL environment variable is not set in Vercel." }, { status: 200 });
  }
  let body;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON in request body" }, { status: 200 });
  }
  if (!(body.idea || body.description)) {
    return Response.json({ error: "Please enter your business idea." }, { status: 200 });
  }
  try {
    const r = await fetch(`${BRAIN}/studio`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea: body.idea || body.description }),
    });
    const data = await r.json();
    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json(
      { error: `Studio generation failed (${e.message}). The backend may be waking up — wait ~30s and retry.` },
      { status: 200 }
    );
  }
}
