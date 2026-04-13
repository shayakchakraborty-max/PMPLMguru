const BRAIN = process.env.BRAIN_URL || "http://localhost:8000";

export const maxDuration = 300; // 5 min

export async function POST(req) {
  const body = await req.json();
  try {
    const r = await fetch(`${BRAIN}/autopilot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(290000),
    });
    if (!r.ok) {
      const text = await r.text();
      return Response.json({ error: `Backend ${r.status}: ${text.slice(0,200)}` }, { status: 500 });
    }
    return Response.json(await r.json());
  } catch (e) {
    return Response.json({ error: e.message || "Unknown error" }, { status: 500 });
  }
}
