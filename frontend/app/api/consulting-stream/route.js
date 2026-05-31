export const runtime = "nodejs";
export const maxDuration = 60;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function POST(req) {
  if (!BRAIN) {
    return new Response(`data: ${JSON.stringify({ type: "error", error: "BRAIN_URL not set" })}\n\n`, { status: 200, headers: { "Content-Type": "text/event-stream" } });
  }
  let body;
  try { body = await req.json(); } catch {
    return new Response(`data: ${JSON.stringify({ type: "error", error: "Invalid JSON" })}\n\n`, { status: 200, headers: { "Content-Type": "text/event-stream" } });
  }
  const upstream = await fetch(`${BRAIN}/consulting/stream`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!upstream.ok || !upstream.body) {
    return new Response(`data: ${JSON.stringify({ type: "error", error: `Backend HTTP ${upstream.status}` })}\n\n`, { status: 200, headers: { "Content-Type": "text/event-stream" } });
  }
  return new Response(upstream.body, {
    status: 200,
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", "Connection": "keep-alive", "X-Accel-Buffering": "no" },
  });
}
