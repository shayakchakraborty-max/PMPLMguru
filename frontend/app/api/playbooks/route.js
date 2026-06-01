// frontend/app/api/playbooks/route.js
// Proxies the Industry Playbook Engine to the backend brain (Railway).
//   GET  -> /playbooks/meta   (30 sector cards, section contract, tiers)
//   POST -> /playbook         (body: { key | business_type | description }) -> full 13-part playbook
// Never returns a raw 500 — upstream failures are wrapped in a 200 with an error field.

export const runtime = "nodejs";
export const maxDuration = 60;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET() {
  if (!BRAIN) {
    return Response.json(
      { error: "BRAIN_URL environment variable is not set in Vercel. Add it under Project Settings -> Environment Variables." },
      { status: 200 }
    );
  }
  try {
    const r = await fetch(`${BRAIN}/playbooks/meta`, { headers: { "Content-Type": "application/json" } });
    const data = await r.json();
    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json(
      { error: `Could not reach the brain (${e.message}). It may be waking up — wait ~30s and retry.` },
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
  try {
    const r = await fetch(`${BRAIN}/playbook`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        key: body.key || "",
        business_type: body.business_type || "",
        description: body.description || "",
      }),
    });
    const data = await r.json();
    return Response.json(data, { status: 200 });
  } catch (e) {
    return Response.json(
      { error: `Playbook fetch failed (${e.message}). The backend may be waking up — wait ~30s and retry.` },
      { status: 200 }
    );
  }
}
