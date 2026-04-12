# 🤖 PMGuru v7 — Autonomous PM + Product Lifecycle Platform

> **Vision:** Enter an idea → AI generates plan → You approve → 8 self-improving AI agents autonomously execute the entire product lifecycle and ship a working prototype.

## 🏗️ Architecture (Cutting-Edge 2026 Stack)

| Layer | Tech | Role |
|---|---|---|
| **Frontend** | Next.js 14 + React 18 + Tailwind | Beautiful approval/dashboard UI |
| **Backend Brain** | FastAPI (Python) | Hosts the agent orchestration |
| **Orchestration** | LangGraph-style state machine | Sequential phase execution with state passing |
| **Agent Roles** | CrewAI-style definitions | 8 specialized agents with role/goal/backstory/tools |
| **Smart Routing** | LiteLLM-style router | Auto-picks Groq/Gemini/HF, with fallback |
| **Memory** | Self-improving JSON store | Lessons learned feed back into agent prompts |
| **Simulations** | Pre-deployment test suite | Each agent verified before deploy |
| **Deployment** | Vercel (frontend) + Render (backend) | Both have free tiers |

## 🤖 The 8 AI Agents

| Phase | Agent | Methods | Deliverables |
|---|---|---|---|
| 1 Discovery | Strategist | Lean, Agile, SAFe | Vision, OKRs, personas, market sizing |
| 2 Ideation | Strategist | Lean, JTBD | RICE-prioritized features |
| 3 Definition | Business Analyst | PMBOK, BABOK | User stories, AC, PRD |
| 4 Design | UX Designer | Design Thinking | User flows, wireframes, design system |
| 5 Development | Scrum Master | Scrum, Kanban, XP | Sprint plan, tasks, velocity |
| 6 Testing | QA Lead | XP, Shift-Left | Test strategy, quality gates |
| 7 Launch | DevOps Engineer | DevOps, SRE | CI/CD, infra, monitoring |
| 8 Iterate | Stakeholder Comms | PMBOK, ADKAR | Launch comms, status reports |

Plus: **Risk Manager** (cross-cutting on phases 3 & 7).

## 🧠 Self-Improvement Loop

After each run, the memory store logs performance metrics. Agents pull "lessons learned" from previous runs into their system prompts on subsequent executions, creating a feedback loop that improves output quality over time.

## 🚀 Deployment Steps

### Part A: Backend Brain (FastAPI on Render)

1. **Push to GitHub:** Upload this entire folder to a new repo `pmguru-v7`
2. **Sign up at [render.com](https://render.com)** (free tier)
3. **New Web Service** → Connect GitHub repo
4. **Settings:**
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `python main.py`
   - Plan: **Free**
5. **Add environment variables** in Render dashboard:
   - `GROQ_API_KEY` — get from [console.groq.com](https://console.groq.com) (free, fastest)
   - `GEMINI_API_KEY` — get from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (free, generous)
   - `HF_API_KEY` — get from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) (optional fallback)
6. **Deploy** → Copy your URL: `https://pmguru-brain-xxxx.onrender.com`
7. **Verify:** Visit `/health` endpoint — should return `{"status":"ok",...}`
8. **Test simulations:** Visit `/simulations` — runs all 8 agents through their pre-deployment tests

### Part B: Frontend (Next.js on Vercel)

1. **Import same repo** at [vercel.com/new](https://vercel.com/new)
2. **Settings:**
   - Root directory: `frontend`
   - Framework: Next.js (auto-detected)
   - Install command: `npm install --legacy-peer-deps`
3. **Add environment variable:**
   - `BRAIN_URL` = your Render URL from Part A (e.g. `https://pmguru-brain-xxxx.onrender.com`)
4. **Deploy** → Live in ~90 seconds

### Part C: Use It! 🎉

1. Visit your Vercel URL → click **"🚀 Launch Autopilot"**
2. Enter your product idea in detail
3. Click **"🧠 Generate Project Plan"** → Strategist creates initial plan
4. Review the plan and the 8-agent pipeline
5. Click **"✅ Approve & Execute All 8 Agents"**
6. Watch agents work sequentially (~90 seconds total)
7. Get full report + downloadable working prototype HTML

## 🧪 Run Simulations Locally

```bash
cd backend
pip install -r requirements.txt
export GROQ_API_KEY=gsk_xxx
python main.py
# Then in another terminal:
curl http://localhost:8000/simulations
```

## 📂 Project Structure

```
pmguru-v7/
├── backend/                          # FastAPI Brain Server
│   ├── main.py                       # API endpoints
│   ├── agents/
│   │   ├── definitions.py            # CrewAI-style agent specs + simulations
│   │   └── router.py                 # LiteLLM smart router (Groq/Gemini/HF)
│   ├── graph/
│   │   └── workflow.py               # LangGraph-style 8-phase orchestrator
│   ├── memory/
│   │   └── store.py                  # Self-improvement memory + sim runner
│   ├── requirements.txt
│   ├── Dockerfile
│   └── render.yaml                   # Render deployment config
└── frontend/                         # Next.js UI
    ├── app/
    │   ├── page.js                   # Landing page
    │   ├── auto/page.js              # Main autopilot UI with approval flow
    │   └── api/
    │       ├── pipeline/route.js     # Proxy to brain /pipeline/*
    │       └── prototype/route.js    # Proxy to brain /pipeline/prototype
    ├── package.json
    └── next.config.js
```

## 🎯 Key Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /pipeline/plan` | Generate initial plan for approval |
| `POST /pipeline/execute` | Run all 8 agents sequentially |
| `POST /pipeline/prototype` | Generate working HTML prototype |
| `GET /simulations` | Run pre-deployment agent tests |
| `GET /memory/stats` | View self-improvement metrics |
| `GET /agents` | List all agents and their roles |

## 🔮 What Makes v7 Different

1. **Approval gate** — User reviews plan before agents execute (true human-in-the-loop)
2. **Sequential state passing** — Each agent sees outputs of previous agents
3. **Smart provider routing** — Uses cheapest/fastest free LLM for each task type
4. **Self-improvement** — Memory of past runs feeds into future agent prompts
5. **Simulations** — Agents are tested before deployment, not in production
6. **Working prototype** — Not just a plan, an actual downloadable HTML MVP
7. **Production architecture** — Clean separation of concerns, scalable, observable

## 💰 Total Cost

**$0/month** on free tiers (Render free + Vercel free + Groq free + Gemini free).

---

Built with ❤️ by Shayak. Powered by Groq, Gemini, and the open-source AI ecosystem.
