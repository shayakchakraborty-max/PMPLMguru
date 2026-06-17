// Proxies the consulting-firm ERP layer (cockpit / rbac / timesheets / expenses).
//   GET  ?view=cockpit|rbac|timesheets|expenses&owner=&engagement_id=
//   POST { action:"timesheet"|"expense"|"expense_status", ...payload }
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;
const MAP = { cockpit: "/firm/cockpit", rbac: "/firm/rbac", timesheets: "/firm/timesheets", expenses: "/firm/expenses", approvals: "/firm/approvals" };

export async function GET(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  const { searchParams } = new URL(req.url);
  const view = searchParams.get("view") || "cockpit";
  const owner = encodeURIComponent(searchParams.get("owner") || "demo");
  const eid = searchParams.get("engagement_id");
  const role = searchParams.get("role");
  const qs = `owner=${owner}${eid ? `&engagement_id=${encodeURIComponent(eid)}` : ""}${role ? `&role=${encodeURIComponent(role)}` : ""}`;
  try {
    const r = await fetch(`${BRAIN}${MAP[view] || MAP.cockpit}?${qs}`, { headers: { "Content-Type": "application/json" } });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Could not reach the brain (${e.message}).` }, { status: 200 });
  }
}

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body; try { body = await req.json(); } catch { return Response.json({ error: "bad json" }, { status: 200 }); }
  const action = body.action;
  const path = action === "expense" ? "/firm/expenses"
    : action === "expense_status" ? "/firm/expenses/status"
    : action === "ocr" ? "/firm/expenses/ocr"
    : "/firm/timesheets";
  try {
    const r = await fetch(`${BRAIN}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Action failed (${e.message}).` }, { status: 200 });
  }
}
