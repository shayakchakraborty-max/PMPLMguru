// frontend/app/api/agents/route.js
// Proxies the research-grade MSME agent layer to the Render backend brain.
//   GET  -> /agents/meta   (registry, ERP/Notion model, taxonomy, citations)
//   POST -> /agents/run    (body: { agent, description, data? }) -> audit-ready envelope
// Never returns a raw 500 — upstream failures are wrapped in a 200 with an error field.

export const runtime = "nodejs";
export const maxDuration = 60;

const BRAIN = (process.env.BRAIN_URL || "").replace(/\/$/, "");

export async function GET() {
  if (!BRAIN) {
    return Response.json(
      { error: "BRAIN_URL environment variable is not set in Vercel. Add it under Project Settings -> Environment Variables." },
      { status: 200 }
    );
  }
  try {
    const r = await fetch(`${BRAIN}/agents/meta`, { headers: { "Content-Type": "application/json" } });
    const data = await r.json();
    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json(
      { error: `Could not reach the brain (${e.message}). Render may be sleeping — wait ~30s and retry.` },
      { status: 200 }
    );
  }
}

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
  if (!body.agent) {
    return Response.json({ error: "Please choose an agent." }, { status: 200 });
  }
  try {
    const r = await fetch(`${BRAIN}/agents/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent: body.agent,
        description: body.description || "",
        data: body.data || {},
      }),
    });
    const data = await r.json();
    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json(
      { error: `Agent run failed (${e.message}). Render may be sleeping — wait ~30s and retry.` },
      { status: 200 }
    );
  }
}
