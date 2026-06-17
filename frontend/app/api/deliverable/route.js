// Proxies AI deliverable generation (board deck / exec memo).
//   POST { report, kind:"deck"|"memo" }
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 45;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function POST(req) {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  let body; try { body = await req.json(); } catch { return Response.json({ error: "bad json" }, { status: 200 }); }
  try {
    const r = await fetch(`${BRAIN}/deliverable`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Deliverable failed (${e.message}).` }, { status: 200 });
  }
}
