const BRAIN = process.env.BRAIN_URL || "http://localhost:8000";

export async function POST(req) {
  const body = await req.json();
  const { idea, action, pm_plan } = body;
  
  // Route to correct backend endpoint based on action
  let endpoint = "/pm/plan";
  let payload = { idea };
  
  if (action === "plm_execute") {
    endpoint = "/plm/execute";
    payload = { idea, pm_plan };
  }
  
  try {
    const r = await fetch(`${BRAIN}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return Response.json(await r.json());
  } catch (e) {
    return Response.json({ error: e.message }, { status: 500 });
  }
}
