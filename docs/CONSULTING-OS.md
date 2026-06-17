# ConsultingOS — Best-in-Class Architecture Review & Curated Build Plan

> A curated, opinionated response to the "World-Class AI-Native Consulting Operating System on AWS"
> master brief. This document does three things: (1) **reviews what exists today** in this repo,
> (2) **curates the best-in-class target** from the brief, and (3) **challenges the assumptions** and
> recommends a pragmatic sequence — because the brief, taken literally, is a multi-year, multi-team,
> high-burn program and building all nine layers at once is the fastest way to ship nothing.
>
> Companion to [STRATEGY.md](STRATEGY.md) (the India-MSME market thesis). This doc is the *platform*
> architecture and roadmap.

---

## 0. The one decision that matters most

The brief says: *"This is McKinsey + Bain + Palantir + ServiceNow + Salesforce + Notion + Celonis + AI."*
That is a **$100M+ platform** and a horizontal "operating system for consulting firms globally."

We are not that, and we should not pretend to be — yet. We have something more valuable for the next
18 months: a **working, deterministic, India-MSME consulting engine** that already produces board-ready,
cited output with zero LLM dependency for its core, deployed and live. The winning move is **not** to
rip that up and chase the nine-layer AWS vision. It is to **treat the deterministic engine as the
guaranteed-quality core and grow the AWS-native, agentic layers around it, demand-first.**

> **Curation verdict:** Adopt the brief's *capability model, AI-workforce taxonomy, digital-twin, RAG and
> governed-learning ideas*. Defer the *heavy infra* (Neptune, AgentCore, Temporal, desktop process-mining)
> until a paying-customer signal justifies each one. Keep the India-MSME wedge as the beachhead; "global
> consulting-firm OS" is the expansion, not the MVP.

---

## 1. Current state — what is actually built (2026-06)

A deployed, deterministic platform: Python `http.server` backend (Railway) + Next.js 14 frontend (Vercel),
Groq used only to *polish* a guaranteed-valid deterministic envelope.

| Brief concept | What exists today | Module / page |
|---|---|---|
| Consulting capability model (packs → lines → workflows) | ✅ **16 towers · 94 service lines · 210 workflows**, each mapped to an AI advisor + live agent | `consulting_catalog.py`, `/catalog` |
| AI consulting workforce | ✅ **26 live agents / 20 AI advisor personas** (CEO/CFO/COO/CRO/CHRO/Tax/Legal/O2C/P2P/R2R/Risk/Tech/ESG/Marketing/Org…) | `msme_agents.py`, `/advisor` |
| AI Managing Partner / orchestration | ⚠️ **Procedural orchestrator** — routes + staffs ≤6-agent team + curates one Big-4 report | `orchestrator.py`, `/engage` |
| Engagement digital twin | ⚠️ **Partial** — per-engagement report + threads (localStorage), scorecard, RAID-ish registers | `live_brain.py`, `/engage`, `/ceo` |
| RAG intelligence layer | ⚠️ **Keyless TF-IDF + web search**, not vector/hybrid/graph | `doc_store.py`, `live_brain.py` |
| Knowledge graph | ❌ Not built | — |
| Process mining | ⚠️ **Value-stream/process-map generation**, not event-log mining | `process_map.py`, `/process` |
| Billing intelligence / timesheets | ❌ Not built | — |
| Industry overlays | ✅ **30 playbooks + 13-sector/39-segment market intelligence** | `industry_playbooks.py`, `market_intel.py`, `/market` |
| Executive command center | ✅ CEO Office + Monitor (KPI/compliance/alerts) | `/ceo`, `/monitor` |
| Government schemes / compliance | ✅ 26 schemes + India compliance map | `gov_schemes.py`, `/schemes` |
| Demo / situations library | ✅ 30 sample engagements across 19 sectors | `situations.py`, `/engage` |
| Self-evolving brain (governed learning) | ⚠️ Learning log (JSONL), no governance workflow | `live_brain.py` |
| MCP tool ecosystem | ❌ Not built (no SAP/Salesforce/Tally connectors) | — |
| Model layer | ⚠️ Groq→Gemini→HF free router (not Bedrock) | `llm_stack.py` |
| AWS-native infra | ❌ Railway + Vercel (not Bedrock/Neptune/AgentCore) | — |

**Honest headline:** we have a strong **Layer 1 (Consulting ERP/capability model)**, a credible **Layer 2
(AI workforce)** and a working **Layer 9 (Executive Intelligence)**. Layers 3–8 (vector-RAG, knowledge
graph, process mining, MCP, durable orchestration, governed learning) are partial-to-absent. That is the
real map.

---

## 2. The nine-layer target — curated, with verdicts

| # | Layer (brief) | Curated verdict | First concrete step |
|---|---|---|---|
| 1 | Consulting ERP | **Have it; deepen it.** Promote the digital twin to a real persisted entity. | Move engagements from localStorage → Aurora/Postgres |
| 2 | AI Agent Workforce | **Have it; upgrade reasoning.** Keep deterministic generators as the floor; add an LLM "reasoning pass" per agent behind a flag. | Bedrock Claude reasoning pass on top of the envelope |
| 3 | RAG Intelligence | **Highest-ROI upgrade.** Swap TF-IDF → pgvector hybrid + reranker + citation/trust scoring. | `doc_store` → pgvector + BGE rerank (see STRATEGY.md) |
| 4 | Knowledge Graph (Neptune) | **Defer.** A graph with no corpus is theatre. Earn it. | Metadata graph in Postgres first; Neptune at >10k artifacts |
| 5 | Process Mining | **Reframe.** True event-log mining needs system access most MSMEs can't give. Keep value-stream synthesis; add log-based mining only for ERP-connected clients. | Optional CSV/event-log ingestion → PM4Py later |
| 6 | MCP Tool Layer | **Selective, demand-first.** Tally + Zoho + Gmail + Google Sheets are the MSME-relevant four. SAP/Oracle are enterprise-expansion. | One MCP connector (Tally or Zoho Books) end-to-end |
| 7 | LangGraph Orchestration | **Adopt the pattern, not the lock-in.** Our procedural orchestrator already does route→staff→curate. Move to a durable graph when engagements span days/human gates. | Re-express `orchestrator.select_workstreams` as a graph |
| 8 | Continuous Learning | **Build the governance, not the retraining.** No uncontrolled fine-tuning. Versioned, human-approved knowledge base. | Approval workflow on the learning log |
| 9 | Executive Intelligence | **Have it.** CEO Office + Monitor + portfolio dashboard. | Portfolio analytics across persisted engagements |

---

## 3. Challenging the brief (where it is wrong or premature)

A best-in-class team's job is to disagree well. Five challenges:

1. **"Automate 60–80% of consulting."** Anchor-high and misleading. The defensible claim is *automate
   60–80% of the **analysis, drafting, benchmarking and PMO admin***, with **100% human sign-off on
   recommendations**. Selling "80% automation" to consulting buyers triggers trust collapse on the first
   hallucination. Sell **leverage and speed with evidence**, not headcount replacement.

2. **AWS-everything from day one is a cost and speed trap.** Bedrock + Neptune + AgentCore + Temporal +
   OpenSearch + Kinesis is a large monthly bill and a large surface area before product-market fit. Our
   current stack (Railway + Vercel + Groq) runs near-zero and ships daily. **Migrate to AWS when
   enterprise security/procurement demands it (SOC2, VPC, data residency), not before.** Design
   cloud-agnostic; the data model and agents shouldn't care.

3. **Desktop process-mining for billing is a privacy and adoption landmine.** Capturing "login activity,
   application activity, document editing, emails" for billing is surveillance-grade telemetry. For MSMEs
   and Indian privacy norms (DPDP), this kills adoption. **Replace with lightweight, opt-in activity
   capture inside the platform** (AI sessions, deliverables, tasks) — bill on platform-native events, not
   keystroke surveillance.

4. **Knowledge Graph before content is backwards.** Neptune is the answer to a question we don't have yet
   (cross-engagement entity reasoning at scale). With a few hundred artifacts, hybrid vector RAG + Postgres
   metadata beats a graph on every dimension that matters. **Earn the graph.**

5. **"Operating system for consulting firms globally" dilutes the wedge.** The brief's secondary
   "industry overlays" are actually our **primary** market (India MSME). Two ICPs — global Big-4 firms AND
   Indian MSMEs — need opposite products (multi-tenant case management vs. self-serve advisory). **Pick the
   MSME wedge; the firm-facing OS is a later platform play once the engine is proven.**

---

## 4. The 20 required outputs — curated answers

Condensed, decision-useful versions (not 200 pages of slideware).

1. **Product Vision.** The AI-native advisory engine that gives every Indian MSME a Big-4-grade
   consulting team on demand — evidence-backed, India-aware, board-ready — and becomes, over time, the
   operating system on which advisory firms run their MSME practices.
2. **Business Architecture.** Three revenue surfaces: (a) self-serve advisory (₹ subscription, the
   `/engage` + `/advisor` flow), (b) managed engagements (human-in-loop, the catalog + orchestrator),
   (c) embedded/white-label for CA firms & lenders (the API + MCP). Capability-pack pricing, not seats.
3. **Consulting Capability Framework.** ✅ Already built: 16 towers → 94 service lines → 210 workflows,
   each with an owning AI advisor (`consulting_catalog.py`). This is the spine.
4. **AI Workforce Design.** ✅ 26 live agents in three tiers (leadership/consulting/specialist) + the
   Managing-Partner orchestrator. Each agent = audit-ready 14-key envelope. **Next:** per-agent reasoning
   pass + memory + escalation rules per the brief's agent spec.
5. **AWS Architecture (target).** Aurora PostgreSQL (twin + pgvector), S3 (artifacts), Bedrock (Claude +
   Nova), OpenSearch (hybrid), Step Functions (durable orchestration), Cognito/IAM/KMS/WAF, CloudWatch +
   OTel. **Adopt incrementally; cloud-agnostic data model.**
6. **Bedrock Architecture.** Bedrock as the model gateway behind `llm_stack` (one interface, swap Groq→
   Bedrock per-tenant); Knowledge Bases for managed RAG; Guardrails for PII/claims. Keep the deterministic
   fallback so a Bedrock outage never 500s an engagement.
7. **AgentCore Architecture.** **Defer.** Our orchestrator covers MVP. Revisit when agents need
   long-running, resumable, tool-using sessions with managed memory.
8. **RAG Design.** Four modes (baseline grounded, hybrid business, adaptive, cross-lingual) per
   STRATEGY.md §Retrieval. **Path:** TF-IDF → pgvector hybrid + BGE-M3 + reranker + citation/trust score +
   hallucination guard. The single highest-ROI engineering upgrade.
9. **Knowledge Graph Design.** Start as a **Postgres metadata graph** (engagement↔client↔sector↔
   deliverable↔agent↔citation). Promote to Neptune only at scale. Entities and edges defined now so the
   later migration is mechanical.
10. **MCP Architecture.** Thin MCP servers, demand-first order: **Tally → Zoho Books → Google Sheets →
    Gmail → SAP/Oracle**. Each connector feeds the digital twin's financial/process profile.
11. **LangGraph Design.** Re-express the engagement as a graph: `intake → classify → route → staff →
    [parallel workstreams] → curate → human-gate → deliver → learn`. Today procedural; make it durable
    when human gates and multi-day runs appear.
12. **Process Mining Design.** Two tracks: (a) **synthesis** (have it — value-stream maps from sector
    models, `/process`); (b) **mining** (opt-in event-log/CSV ingestion → PM4Py) for ERP-connected
    clients only.
13. **Data Model.** The twin is the aggregate root. Core entities: Client, Engagement, Stakeholder,
    Workstream, AgentRun, Finding, Recommendation, Risk, Action, KPI, Deliverable, Citation, Benchmark,
    Scheme, Compliance. **Move off localStorage → Postgres** is the first platform task.
14. **UX/UI Blueprint.** ✅ Strong already: `/market` (intelligence) → `/engage` (super-agent + threads +
    Big-4 report) → `/catalog` (services) → `/ceo` (command center) → `/advisor` (specialists). Keep the
    "intelligence → engagement → report" spine; add persisted-twin views.
15. **Security Architecture.** Today: stateless, no PII store, env-based keys. Target: Cognito auth,
    per-tenant isolation, KMS encryption, DPDP-compliant consent + retention, audit logs, Bedrock
    Guardrails. **Required before storing client data / going multi-tenant.**
16. **MVP Roadmap (next 90 days).** §5 below.
17. **Phase 2 Roadmap.** §5.
18. **Enterprise Roadmap.** §5.
19. **Competitive Analysis.** §6.
20. **Detailed Build Plan.** §5 + the per-layer "first concrete step" in §2.

---

## 5. Roadmap — bridge the engine to the OS

### MVP (next 90 days) — make the engine durable and grounded
- **Persist the digital twin**: engagements/threads → Aurora/Postgres (off localStorage). *Unlocks
  portfolio analytics, multi-device, the twin as a real entity.*
- **Real RAG**: `doc_store` TF-IDF → pgvector hybrid + reranker + citation/trust scoring.
- **Bedrock behind `llm_stack`**: one model gateway, per-tenant; deterministic fallback stays.
- **Auth + tenancy**: Cognito + per-tenant isolation (prerequisite to storing client data).
- **One MCP connector** end-to-end (Tally or Zoho Books) → auto-fills the twin's financial profile.

### Phase 2 (3–9 months) — agentic depth + governance
- **Durable orchestration**: orchestrator → Step Functions/LangGraph with human-approval gates.
- **Per-agent reasoning pass + memory + escalation** (the brief's full agent spec).
- **Governed learning**: versioned knowledge base + human approval workflow on the learning log.
- **Process mining (opt-in)**: event-log/CSV ingestion for ERP-connected clients.
- **Benchmarks engine**: cross-engagement, de-identified KPI ranges feeding every report.

### Enterprise (9–18 months) — the firm-facing OS
- **Multi-tenant case management** (the firm ICP), SOC2, VPC, data residency.
- **Knowledge graph** (Neptune) once the corpus and cross-engagement reasoning justify it.
- **Full MCP estate** (SAP/Oracle/Salesforce), billing intelligence (platform-native, opt-in).
- **Marketplace** of capability packs + a managed-expert layer.

---

## 6. Competitive analysis (curated)

| Player | What they are | Where we win (India MSME) |
|---|---|---|
| Big 3 / Big 4 | Human consulting, premium pricing | Productised, ₹-affordable, instant, India-MSME-tuned |
| Palantir / Celonis | Data/process platforms for enterprises | Advisory-native, no data-eng project, deterministic output |
| ServiceNow / Salesforce | Workflow/CRM platforms | Consulting-IP-native (frameworks, not just workflow) |
| Notion / generic AI copilots | Generic chat + docs | Domain-grounded agents, cited, compliance-aware, never a 500 |
| Indian SaaS (Zoho, Tally, Khatabook) | ERP/accounting tools | We sit *above* them as the advisory brain (and connect via MCP) |

**Our moat-in-progress:** the curated India-MSME consulting IP (catalog + 30 playbooks + 13-sector
intelligence + 26 grounded agents) and the **deterministic always-works guarantee** — a thing pure-LLM
competitors structurally cannot promise.

---

## 7. Bottom line

The brief is an excellent **north star** and a **bad literal build order**. Curated path:

1. **Keep** the deterministic engine as the quality floor and the India-MSME wedge as the beachhead.
2. **Upgrade** the three highest-ROI layers next: persisted twin (data), real RAG (grounding), Bedrock
   gateway (reasoning) — behind auth.
3. **Defer** Neptune, AgentCore, Temporal, desktop process-mining and the global firm-facing OS until a
   paying signal pulls each one in.
4. **Govern** learning and **never** sell "80% automation" — sell evidence-backed leverage with human
   sign-off.

That is how this becomes the operating system for MSME advisory — by earning each layer, not buying all
nine on day one.
