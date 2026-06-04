// frontend/app/api/dashboard/route.js
// Proxies the founder portfolio dashboard (GET /dashboard) from the backend brain.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET() {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  try {
    const r = await fetch(`${BRAIN}/dashboard`, { headers: { "Content-Type": "application/json" }, cache: "no-store" });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Could not reach the brain (${e.message}).` }, { status: 200 });
  }
}
