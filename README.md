# PMGuru

An AI-native consulting & operating system for Indian MSMEs and startups —
India-aware (₹, GST/Udyam/DPIIT, funding incentives), citation-backed, and deterministic.

## What's inside

- **Startup Blueprint** (`/blueprint`) — one-click, consolidated India startup plan:
  market, model, ₹ financials, compliance & registration roadmap, funding & government
  incentives, risk/DD, 90-day plan and how to scale.
- **AI Agents / Advisor** (`/advisor`) — 20 research-grade MSME copilots (CFO, GST,
  operations, inventory, procurement, HR, risk & audit, due diligence, investor
  readiness, market research, and more) across all 17 sectors incl. import/export.
  Each returns an audit-ready report with citations, ERP & Notion actions, risks and KPIs.
- **ERP Workspace** (`/erp`) — a self-explanatory, ERP-styled PLM/PM workspace
  (master data, backlog, sprints, risk register, compliance calendar, KPIs, SOPs),
  editable and exportable to Notion.
- **PM Tool** (`/pm`) + **Consulting Pro** (`/consulting`) — due-diligence report,
  workspace, lifecycle plan, and a Big-3/Big-4 style business assessment.

## Architecture

- **Brain (backend)** — Python service in `backend/` (all agents, reports, blueprint,
  ERP workspace). Container-ready (`backend/Dockerfile`, binds `0.0.0.0:$PORT`).
  Deployed on **Railway** (always-on). Pure-Python and deterministic — no LLM keys required.
- **Frontend** — Next.js 14 app in `frontend/`, deployed on **Vercel**. It talks to the
  brain via the `BRAIN_URL` environment variable.

## Run locally

```bash
# backend
cd backend && pip install -r requirements.txt && python main.py   # http://localhost:8000

# frontend (separate terminal)
cd frontend && npm install --legacy-peer-deps
BRAIN_URL=http://localhost:8000 npm run dev                        # http://localhost:3000
```

## Deploy

See **[DEPLOY.md](DEPLOY.md)** — deploy the brain on Railway (root directory `backend`,
or the root `Dockerfile`), then set `BRAIN_URL` on Vercel to the Railway URL
(with `https://`, no trailing slash) and redeploy the frontend.

Health check: `https://<brain>/health` should return `"msme_agents": {"total": 20, ...}`.
