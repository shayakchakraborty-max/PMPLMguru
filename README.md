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

## Strategy & vision

See **[docs/STRATEGY.md](docs/STRATEGY.md)** — the full platform blueprint (market & target
segments, Big 3/4 positioning, target architecture & toolchain, agent operating model,
deliverables, economics, pricing and governance), with an up-front **implementation-status table**
mapping the blueprint to what is actually built in this repo today.

See **[docs/CONSULTING-OS.md](docs/CONSULTING-OS.md)** — the best-in-class architecture review of the
nine-layer "AI-Native ConsultingOS on AWS" vision: current-vs-target map, challenged assumptions,
the 20 architecture outputs in curated form, and a pragmatic MVP → Phase 2 → Enterprise roadmap that
bridges today's deterministic engine to the AWS-native, agentic target.

## Architecture

- **Brain (backend)** — Python service in `backend/` (all agents, reports, blueprint,
  ERP workspace). Container-ready (`backend/Dockerfile`, `ThreadingHTTPServer` binds
  `0.0.0.0:$PORT`). Pure-Python and deterministic — no LLM keys required. Persists the
  engagement digital twin to **Postgres** when `DATABASE_URL` is set (JSONL fallback otherwise).
- **Frontend** — Next.js 14 standalone app in `frontend/` (`frontend/Dockerfile`). Talks to the
  brain via the `BRAIN_URL` environment variable (server-side `/api/*` proxies).
- **Deploy target: AWS** — both services on **App Runner** (or ECS Fargate) + **RDS/Aurora
  Postgres**. See [DEPLOY.md](DEPLOY.md).

## Run locally

```bash
# backend
cd backend && pip install -r requirements.txt && python main.py   # http://localhost:8000

# frontend (separate terminal)
cd frontend && npm install --legacy-peer-deps
BRAIN_URL=http://localhost:8000 npm run dev                        # http://localhost:3000
```

## Deploy

See **[DEPLOY.md](DEPLOY.md)** — full AWS runbook. Both services ship production
`Dockerfile`s and App Runner `apprunner.yaml` source configs; `deploy/aws-deploy.sh`
builds + pushes both images to ECR. Deploy the brain first, then set the web's `BRAIN_URL`
to the brain's URL (`https://`, no trailing slash). Set `DATABASE_URL` on the brain for the
Postgres twin store.

Health check: `https://<brain>/health` should return `"msme_agents": {"total": 20, ...}`.
