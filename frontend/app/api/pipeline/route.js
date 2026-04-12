const BRAIN = process.env.BRAIN_URL || "http://localhost:8000";
export async function POST(req) {
  const { idea, action } = await req.json();
  const endpoint = action === "execute" ? "/pipeline/execute" : "/pipeline/plan";
  try {
    const r = await fetch(`${BRAIN}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea }),
    });
    const data = await r.json();
    return Response.json(data);
  } catch (e) {
    return Response.json({ error: e.message }, { status: 500 });
  }
}
