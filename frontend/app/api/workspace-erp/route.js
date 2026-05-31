// frontend/app/api/workspace-erp/route.js
// Proxies the ERP-styled PLM/PM workspace builder to the Render backend brain.
//   POST { idea, data? } -> { project, modules[] }
// Never returns a raw 500 — upstream failures are wrapped in a 200 with an error field.

export const runtime = "nodejs";
export const maxDuration = 60;

const BRAIN = (process.env.BRAIN_URL || "").replace(/\/$/, "");

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
    return Response.json({ error: "Please enter your project / business idea." }, { status: 200 });
  }
  try {
    const r = await fetch(`${BRAIN}/workspace/erp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea: body.idea || body.description, data: body.data || {} }),
    });
    const data = await r.json();
    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json(
      { error: `Workspace build failed (${e.message}). Render may be sleeping — wait ~30s and retry.` },
      { status: 200 }
    );
  }
}
