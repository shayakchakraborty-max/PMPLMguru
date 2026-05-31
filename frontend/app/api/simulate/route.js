// frontend/app/api/simulate/route.js
// Proxies the situation simulator to the backend brain (Railway).
//   POST { situation } -> matched situation + agent crew + end-to-end plan
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
  if (!(body.situation || body.idea || body.description)) {
    return Response.json({ error: "Please describe your business situation." }, { status: 200 });
  }
  try {
    const r = await fetch(`${BRAIN}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ situation: body.situation || body.idea || body.description, data: body.data || {} }),
    });
    const data = await r.json();
    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json(
      { error: `Simulation failed (${e.message}). The backend may be waking up — wait ~30s and retry.` },
      { status: 200 }
    );
  }
}
