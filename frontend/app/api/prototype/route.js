// frontend/app/api/prototype/route.js
// Proxies prototype generation with auto-fallback between v9.1 and legacy paths.

export const runtime = "nodejs";
export const maxDuration = 300;

const BRAIN = (process.env.BRAIN_URL || "").replace(/\/$/, "");
const PROTOTYPE_PATHS = ["/plm/prototype", "/pipeline/prototype", "/prototype"];

export async function POST(req) {
  if (!BRAIN) {
    return Response.json({ error: "BRAIN_URL not set in Vercel environment" }, { status: 200 });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON in request body" }, { status: 200 });
  }

  let lastError = null;
  for (const path of PROTOTYPE_PATHS) {
    try {
      const r = await fetch(`${BRAIN}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea: body.idea }),
      });
      const text = await r.text();

      if (r.status === 404) {
        lastError = `${path} -> 404`;
        continue;
      }

      let data;
      try {
        data = JSON.parse(text);
      } catch {
        lastError = `${path} -> non-JSON: ${text.slice(0, 200)}`;
        continue;
      }
      return Response.json(data, { status: 200 });
    } catch (e) {
      lastError = `${path} -> ${e.message}`;
      continue;
    }
  }

  return Response.json(
    { error: `All prototype endpoints failed. Last: ${lastError}. Check ${BRAIN}/health.` },
    { status: 200 }
  );
}
