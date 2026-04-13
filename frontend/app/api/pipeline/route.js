// frontend/app/api/pipeline/route.js
// Proxies PM planning and PLM execution requests to the Render backend brain.
// Never returns a raw 500 - wraps every upstream failure in a 200 with an error field
// so the UI can show a friendly message instead of "Server returned 500".

export const runtime = "nodejs";
export const maxDuration = 300;

const BRAIN = (process.env.BRAIN_URL || "").replace(/\/$/, "");

export async function POST(req) {
  if (!BRAIN) {
    return Response.json(
      { error: "BRAIN_URL environment variable is not set in Vercel. Add it under Project Settings -> Environment Variables." },
      { status: 200 }
    );
  }

  let body;
  try {
    body = await req.json();
  } catch (e) {
    return Response.json({ error: "Invalid JSON in request body" }, { status: 200 });
  }

  // stage: "pm" -> /pm/plan, "plm" -> /plm/execute
  const stage = body.stage || "pm";
  const endpoint = stage === "plm" ? "/plm/execute" : "/pm/plan";
  const url = `${BRAIN}${endpoint}`;

  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea: body.idea, pm_plan: body.pm_plan || null }),
    });

    const text = await r.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { error: `Backend returned non-JSON (HTTP ${r.status}): ${text.slice(0, 500)}` };
    }

    if (!r.ok) {
      return Response.json(
        { error: `Backend ${endpoint} returned HTTP ${r.status}`, detail: data },
        { status: 200 }
      );
    }

    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json(
      { error: `Failed to reach backend at ${url}. It may be sleeping (Render free tier) - wait 30s and retry. Detail: ${e.message}` },
      { status: 200 }
    );
  }
}

export async function GET() {
  if (!BRAIN) {
    return Response.json({ error: "BRAIN_URL not set" }, { status: 200 });
  }
  try {
    const r = await fetch(`${BRAIN}/health`);
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: e.message }, { status: 200 });
  }
}
