// frontend/app/api/situations/route.js
// Proxies the engagement-situations library (one-click demos).
//   GET -> /situations
export const runtime = "nodejs";
export const dynamic = "force-dynamic";   // GET-only routes are statically cached at build otherwise
export const maxDuration = 30;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function GET() {
  if (!BRAIN) return Response.json({ error: "BRAIN_URL not set in Vercel." }, { status: 200 });
  try {
    const r = await fetch(`${BRAIN}/situations`, { headers: { "Content-Type": "application/json" } });
    return Response.json(await r.json(), { status: 200 });
  } catch (e) {
    return Response.json({ error: `Could not reach the brain (${e.message}).` }, { status: 200 });
  }
}
