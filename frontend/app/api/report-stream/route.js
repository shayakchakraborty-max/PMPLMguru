// frontend/app/api/report-stream/route.js
// Streams the consulting report from the backend to the browser via Server-Sent Events.
// The backend sends one SSE per section; we proxy them straight through.

export const runtime = "nodejs";
export const maxDuration = 60;

let BRAIN = (process.env.BRAIN_URL || "").trim().replace(/\/$/, "");
if (BRAIN && !/^https?:\/\//i.test(BRAIN)) BRAIN = "https://" + BRAIN;

export async function POST(req) {
  if (!BRAIN) {
    return new Response(
      `data: ${JSON.stringify({ type: "error", error: "BRAIN_URL not set in Vercel env" })}\n\n`,
      { status: 200, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response(
      `data: ${JSON.stringify({ type: "error", error: "Invalid JSON body" })}\n\n`,
      { status: 200, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  const upstream = await fetch(`${BRAIN}/report/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(
      `data: ${JSON.stringify({ type: "error", error: `Backend returned HTTP ${upstream.status}` })}\n\n`,
      { status: 200, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  // Pipe the upstream SSE stream to the client unchanged
  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
