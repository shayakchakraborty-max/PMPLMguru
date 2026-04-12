const BRAIN = process.env.BRAIN_URL || "http://localhost:8000";
export async function POST(req) {
  const body = await req.json();
  try {
    const r = await fetch(`${BRAIN}/pipeline/prototype`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return Response.json(await r.json());
  } catch (e) {
    return Response.json({ error: e.message }, { status: 500 });
  }
}
