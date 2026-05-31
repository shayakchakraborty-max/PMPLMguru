# Deploying PMGuru

Two pieces:

- **Brain (backend)** — the Python service in `backend/` (all the AI agents, reports,
  blueprint, ERP workspace). Long-running web server; needs an always-on host.
- **Frontend** — the Next.js app in `frontend/`, deployed on **Vercel**. It talks to
  the brain through the `BRAIN_URL` environment variable.

The brain is container-ready (`backend/Dockerfile`, binds `0.0.0.0:$PORT`, single
dependency). Below are two always-on hosts — pick one. **Railway is the simplest.**

---

## Option A — Railway (recommended, easiest)

1. Go to <https://railway.app> → **New Project → Deploy from GitHub repo** → pick
   `shayakchakraborty-max/PMPLMguru`.
2. Open the service → **Settings**:
   - **Root Directory**: `backend`
   - Railway auto-detects `backend/railway.json` and builds the **Dockerfile**.
   - No env vars are required (the agents are pure-Python; `GROQ/GEMINI` keys are
     optional and only used by legacy LLM polish).
3. **Deploy**. When it's live, open **Settings → Networking → Generate Domain** to get
   a public URL like `https://pmguru-brain-production.up.railway.app`.
4. Verify: open `https://<that-domain>/health` — you should see
   `"msme_agents": {"total": 20, ...}`.
5. **Point the frontend at it** (see "Wire the frontend" below).

Railway's usage-based plan stays always-on, so there are no cold starts.

---

## Option B — Fly.io (always-on, free allowance)

Prereqs: install the CLI (`brew install flyctl`) and `fly auth login`.

```bash
cd backend
fly launch --copy-config --no-deploy   # uses fly.toml + Dockerfile; pick an app name/region
fly deploy
fly status                              # confirm 1 machine running
```

`fly.toml` sets `min_machines_running = 1` and `auto_stop_machines = false`, so it
stays awake. Your URL is `https://<app-name>.fly.dev`. Verify `/health` as above.

---

## Wire the frontend (Vercel) to the brain

1. Vercel → your project → **Settings → Environment Variables**:
   - `BRAIN_URL` = the new brain URL (e.g. `https://pmguru-brain-production.up.railway.app`)
   - **No trailing slash.**
2. Vercel → **Settings → General → Root Directory** = `frontend` (if not already).
3. **Redeploy** the frontend (Deployments → ⋯ → Redeploy, uncheck "use existing cache").
4. Open `/advisor` — the 20 agents should load. Also check `/blueprint`, `/erp`,
   `/report`, `/consulting`.

---

## Sanity checklist if something is "not working"

- `https://<brain>/health` returns JSON with `"msme_agents"` → brain is current.
- Vercel `BRAIN_URL` exactly matches the brain URL (no trailing slash).
- Frontend redeployed **after** setting `BRAIN_URL`.
- The Advisor now auto-retries and shows a clear message if the brain is unreachable.
