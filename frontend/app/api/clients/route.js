// Proxies Client master data + Contracts + Billing summary.
//   GET ?view=clients|client|contracts|contract|billing&owner=&id=&client_id=
//   POST { action:"add_client"|"update_client"|"add_contract"|"contract_status"|"contract_email", ... }
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;
const GET_MAP = { clients: "/clients", client: "/client", contracts: "/contracts", contract: "/contract", billing: "/billing/summary" };
const POST_MAP = { add_client: "/clients", update_client: "/client/update", add_contract: "/contracts", contract_status: "/contract/status", contract_email: "/contract/email" };

export async function GET(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  const { searchParams } = new URL(req.url);
  const view = searchParams.get("view") || "clients";
  const owner = encodeURIComponent(searchParams.get("owner") || "demo");
  const id = searchParams.get("id"), cid = searchParams.get("client_id");
  const qs = `owner=${owner}${id ? `&id=${encodeURIComponent(id)}` : ""}${cid ? `&client_id=${encodeURIComponent(cid)}` : ""}`;
  try {
    const r = await fetch(`${BRAIN}${GET_MAP[view] || GET_MAP.clients}?${qs}`, { headers: { "Content-Type": "application/json" } });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) { return Response.json({ error: `Could not reach the brain (${e.message}).` }, { status: 200 }); }
}

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body; try { body = await req.json(); } catch { return Response.json({ error: "bad json" }, { status: 200 }); }
  const path = POST_MAP[body.action] || "/clients";
  try {
    const r = await fetch(`${BRAIN}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) { return Response.json({ error: `Action failed (${e.message}).` }, { status: 200 }); }
}
