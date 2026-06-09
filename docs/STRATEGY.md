# AI-Powered Consulting Platform for Indian MSMEs

> Curated, version-controlled copy of the platform strategy & architecture blueprint
> (originally authored as `AI-Powered Consulting Platform for Indian MSMEs.docx`).
> This markdown is the source of truth going forward; the `.docx` is kept only as the
> original artifact. All bracketed `[n]` markers refer to the **Sources** section at the end.

---

## Implementation status — blueprint vs. what is actually built

This repo is a **working MVP of the product layer**, not yet the full target architecture
described below. The table is the honest mapping of vision → code as of 2026-06-09.

| Blueprint pillar | Status | Where it lives in this repo |
|---|---|---|
| Target-segment coverage (mfg clusters, GST traders, services, medium ent.) | ✅ Built | `backend/industry_playbooks.py` (30 types), `backend/msme_agents.py` (BUSINESS_TAXONOMY), `backend/industry_experts.py` |
| Diagnostic-first, Big 3/4 method blend | ✅ Built | `backend/live_brain.py` (`/consult`): scorecard, benchmark, SWOT, roadmap, diagnosis, recs |
| Report-quality deliverable + citations + exec summary | ✅ Built | `live_brain` envelope + Board Pack (frontend `/ceo`, `/consulting`) |
| KPI dashboards (mfg / trade / services) | ✅ Built | `backend/monitor.py`, frontend `/monitor`, `/ceo` |
| PMO action tracker (owners / due dates / KPI linkage) | ✅ Built | `live_brain.build_pmo` (`/pmo`), interactive sprint board |
| Lender / investor-ready packs | ✅ Built | `msme_agents` investor_readiness + Board Pack export |
| Government-scheme navigator | ✅ Built (beyond doc) | `backend/gov_schemes.py` (26 schemes), `/schemes` |
| RAG over owner documents | ⚠️ Partial | `backend/doc_store.py` — **keyless TF-IDF**, not Qdrant/pgvector + BGE rerank |
| Tiered model router | ⚠️ Partial | `backend/llm_stack.py` — Groq→Gemini→HF free providers; not the 3-tier open-weight stack |
| Multi-agent orchestration | ⚠️ Procedural | 20 agents in `msme_agents.py` + consult engine; **not** durable LangGraph/LlamaIndex graphs |
| Process maps / value-stream maps | ❌ Not built | doc recommends PM4Py / bpmn.io |
| Process mining from event logs | ❌ Not built | — |
| Governance infra (DPDP tenant isolation, Presidio PII, NeMo guardrails, signed audit) | ❌ Not built | compliance *content* exists (`compliance_for`, `gov_schemes`); infra controls do not |
| Embedded BI (Superset / Metabase) | ❌ Not built | dashboards are bespoke React, not embedded BI |
| Observability / eval (Langfuse, Ragas, DeepEval) | ❌ Not built | — |

**Architecture note for this codebase:** the backend is a deterministic, template-driven
`http.server` (philosophy: always-works, sub-second, never 500), with an LLM only used to
*polish* a guaranteed-valid deterministic envelope (`GROQ_API_KEY` on Railway → `engine=groq:groq`).
That is a deliberate divergence from the blueprint's heavyweight open-weight GPU stack — it trades
top-end model quality for zero-cost, zero-key reliability appropriate to the current stage.
The blueprint below remains the **north-star target**; the gaps marked ⚠️/❌ are the build backlog.

---

## Executive summary

India's MSME base is large enough, fragmented enough, and under-served enough to justify a
purpose-built AI consulting platform rather than a generic "business copilot." The Ministry of
MSME's 2025–26 annual report states the sector contributes ~31.1% of India's GDP and >48.5% of
exports; MoSPI's ASUSE 2023–24 shows 7.34 crore unincorporated non-agricultural establishments and
>12 crore workers, growing to 7.92 crore establishments in ASUSE 2025. Formalisation remains
incomplete: SIDBI's 2025 survey notes 35% of surveyed MSMEs were still unregistered even after large
Udyam / Udyam Assist gains. [1]

The strongest initial wedge is **not "all MSMEs."** It is digitally active small and lower-medium
enterprises in manufacturing, trade and operationally intensive services that already leave enough
data exhaust to support defensible diagnosis and measurable outcomes. SIDBI found the most common
challenges were access to credit, competition, technology adoption, regulatory compliance,
infrastructure, delayed payments and labour availability — with sector differences that matter
commercially. >90% of surveyed MSMEs accept digital payments but only ~18% had used digital lending:
the data layer exists before the advisory layer fully does. [2]

The product thesis: combine the structured problem-solving and executive storytelling of **McKinsey,
BCG, Bain** with the implementation depth, compliance breadth and PMO discipline of **Deloitte, EY,
KPMG, PwC** — and *productise the method, not the billable pyramid.* [3]

Recommended architecture: an **India-first, open-weight, multi-agent system** with three model tiers
(large reasoner used sparingly; default analyst tier; specialist models for OCR / translation /
embeddings / rerank / process mining). Practical stack: LangGraph or LlamaIndex orchestration;
Qdrant or pgvector retrieval; BGE-M3 or multilingual E5 embeddings; BGE rerankers or ColBERT-style
late interaction; Surya / Tesseract / OCRmyPDF ingestion; Superset / Metabase dashboards;
AI4Bharat IndicTrans2 + Sarvam open models for Indian languages. [4]

Cost outlook is favourable if inference is routed intelligently and long-form generation is async.
IndiaAI's price calculator exposes heavily subsidised GPU rates (≈₹24/hr 1×L4, ₹45/hr L40S,
₹81/hr A100 80GB, ₹100/hr H100 NVL, ₹117/hr H100 SXM; block storage ₹1.1/GB/mo, object ₹0.78/GB/mo) —
a pilot footprint can run in the low single-digit lakhs/month, subject to eligibility. [5]

Strategic conclusion: **sell an AI-native consulting operating system, not a chatbot.** Start with a
tightly scoped MVP that ingests data, runs structured diagnostics, produces report-quality cited
outputs, generates dashboards and process maps, and tracks action plans to outcomes. [6]

---

## Indian MSME opportunity and target segments

Do not treat all MSMEs as one market. The universe spans informal micro units, formal small firms,
cluster manufacturers, traders, digitally active service businesses and emerging medium enterprises.
NITI Aayog notes ~51% of MSMEs are rural, 49% urban. The MSME classification was revised w.e.f.
1 April 2025, signalling a policy push to support *scaling* enterprises, not only subsistence units. [7]

Commercial segmentation lens: **data readiness × pain intensity × willingness to pay.** First three
segments: export-oriented / cluster manufacturers; GST-heavy traders & distributors; operationally
intensive services (hotels, healthcare, logistics, IT/ITeS). SIDBI's work distinguishes which
problems dominate by sector and flags persistent skilled-labour shortages (defence equipment,
readymade garments, hotels, tiles & sanitaryware). [8]

### Who to target first

| Target segment | Why attractive now | Typical pain pattern | Initial product module |
|---|---|---|---|
| Export-oriented light manufacturing clusters | High process complexity, working-capital stress, quality pressure, need for dashboards & SOPs | Quote-to-cash delays, yield loss, inventory, procurement variance, scheduling, cost-out, export readiness, certification | Operations diagnostic, plant KPI cockpit, process/value-stream maps, savings tracker |
| GST-heavy traders & distributors | Large digital exhaust (invoices, payments, inventory); faster cycles than mfg | Gross-margin leakage, receivables, credit control, pricing discipline, assortment, supplier concentration, delayed payments | Commercial dashboard, working-capital optimiser, collection playbooks, route-to-market |
| Hospitality / healthcare / logistics / IT-ITeS | Service ops create measurable throughput & utilisation KPIs; fast value | Capacity utilisation, turnaround time, manpower productivity, demand forecasting, SOP standardisation, CX | Service ops cockpit, staffing & utilisation planner, PMO action tracker |
| Women-led / newly formalised small firms | Under-served, high trust need, want structured support not bespoke fees | Registration, finance access, vendor onboarding, market discovery, compliance fear, weak systems | Guided self-serve diagnostic, compliance navigator, lender-ready report, growth checklist |
| Medium enterprises entering transformation | NITI flags them as under-leveraged growth engines | Multi-plant data fragmentation, functional silos, PMO weakness, board-reporting gap, ERP underuse | Transformation office, executive dashboard, initiative governance, benchmark packs |

For the first 18 months, **do not** prioritise the most informal micro segment as primary revenue —
low digital exhaust, lower ACVs, assisted onboarding. The early base is the **"missing middle":**
firms formal enough to provide digital records but too small to buy meaningful MBB / Big 4 support at
normal rates. [9][10]

---

## Competitive benchmark and positioning

Answer the client's practical question — *"Why not hire a consultant, a CA firm, or a BI vendor?"* —
because each alternative gives only one slice. Big 3 are strongest at framing problems, executive
narratives and prioritising high-value transformation levers. Big 4 are broader operationally (tax,
risk, controls, functional design, private-business, deals, implementation). [11]

### What the platform should emulate

| Capability | Big 3 pattern | Big 4 pattern | What the platform does |
|---|---|---|---|
| Problem framing | Hypothesis-driven issue trees, executive narrative, prioritised recs | Function-by-function decomposition, implementation pathways | Start every engagement with a decision-oriented diagnostic + quantified opportunity tree |
| Operations | Cross-functional value creation, top-mgmt sponsorship, transformation design | PMO, control points, SOPs, process documentation | Current-state analyses, future-state process maps, initiative charters, weekly benefit tracking |
| Finance & performance | Profit pools, pricing & portfolio choices | Controls, reporting, compliance, stakeholder dashboards | CFO-grade unit economics, working-capital, pricing & action dashboards |
| AI & data | Analytics/AI embedded in transformation | System integration, controls, governance, auditability | AI insight + source-linked evidence, audit logs, policy controls |
| Client interaction | High-touch advisory | Advisory + execution support | Product-led self-serve, assisted review, managed PMO as distinct service levels |

### What the pricing evidence actually says

Public top-firm pricing is opaque; what exists is a patchwork. One ITAT order records historical
BCG India hourly rates: ₹6,500 (Consultant), ₹10,000 (Project Leader), ₹12,000 (Manager), ₹17,500
(Officer). Public Indian contract award notices show large-firm assignments routinely in crores —
e.g. a Deloitte technical-support proposal ₹4,69,85,000; KPMG ₹12,57,09,648 incl. GST; an EY study
₹40,66,666. Directional, not generalisable, but enough to prove the gap an MSME-facing product can
exploit. Position as the **lowest-cost way to buy the parts of consulting MSMEs value most:** fast
diagnosis, quantified recs, dashboarding, process standardisation, PMO discipline, compliance
awareness, decision-ready reporting. [12][22]

---

## Architecture and toolchain

The architecture must be opinionated — not an LLM wrapper around documents but a fact-finding,
synthesis and execution system. Core pattern: **secure ingestion → structured business model →
retrieval layer → routed model serving → multi-agent orchestration → deliverable generation →
dashboard embedding → closed-loop PMO tracking.** Orchestration via LangGraph / LlamaIndex /
Haystack (controlled agent workflows, retrieval, memory, routing, human oversight). [13][14]

### Recommended model stack

| Role in stack | Best-fit choices | Why |
|---|---|---|
| Heavy reasoning / final synthesis | Qwen3 flagship; Sarvam-105B; DeepSeek-R1 | Sparingly for board-level synthesis, scenarios, complex root-cause, cross-workstream arbitration |
| Default analyst model | Sarvam-30B; Mistral Small 3.x/4; Llama 3.3 70B; mid Qwen3 | Day-to-day report writing, evidence synthesis, dashboard commentary, draft PMO updates |
| Indic language support | Sarvam open; AI4Bharat; IndicTrans2; Sarvam Translate | Indian-language docs, shop-floor artefacts, bilingual reporting |
| OCR / document understanding | Surya; Tesseract; OCRmyPDF | Invoices, scanned process sheets, inspection records, plant docs |
| Embeddings | BGE-M3; multilingual E5 large instruct | Strong multilingual retrieval defaults for longer docs |
| Reranking / late interaction | BGE reranker v2 m3; ColBERTv2-class | Precision when citing exact evidence / choosing among near-duplicate chunks |

Practical recommendation: a **tiered router** — small/cheap for extraction/classification/routing/
checklists; mid-sized default analyst; large reasoner only for final synthesis, contentious
decisions and major deliverables. That keeps cost low enough for MSME pricing while preserving
top-end output quality. [15]

### Retrieval and knowledge architecture

RAG is not one thing — at least four modes are needed:

| Retrieval mode | Best use | Recommended pattern |
|---|---|---|
| Baseline grounded | Standard policy / document Q&A | Dense embeddings + metadata filters |
| Hybrid business | Policies + transactional data + doc corpus | Dense + sparse/keyword fusion with reranking |
| Adaptive | Unsure if retrieval needed / first pass enough | Self-reflective / agentic retrieval loops |
| Cross-lingual | Docs and questions in different Indian languages | Translation-assisted or multilingual embeddings, standardised answer language |

Grounded in: the original RAG paper; HyDE (zero-shot dense retrieval); Self-RAG (adaptive retrieval);
Qdrant / Milvus server-side hybrid & multi-vector search; BGE-M3 (dense/sparse/multi-vector). [16]

### Vector database options

| Option | When to choose | Upside | Trade-off |
|---|---|---|---|
| pgvector | MVP, SQL-first, tight coupling with operational data | Vectors in Postgres, joins, ACID, simplicity | Less specialised at large retrieval scale |
| Qdrant | Production RAG where relevance tuning matters | Mature hybrid queries, custom scoring, multitenancy | Another infra component |
| Milvus | Large-scale / multi-vector-heavy | Built for scale, strong ANN & multi-vector | More infra weight than an MVP needs |
| Weaviate | Want an integrated AI database layer | Built-in vector + hybrid, RAG ergonomics | Heavier if product is very SQL-centric |
| Chroma | Local prototyping / fast iteration | Minimal friction, easy start | Not first choice for serious multi-tenant prod |

Recommendation: **pgvector** for the earliest MVP if the team is Postgres-strong and wants lean;
**Qdrant** for the first hardened production release once multi-tenancy / hybrid / tuning matter. [17]

### Data, BI and process toolchain

| Layer | Recommended tools | Role |
|---|---|---|
| Connectors / ingestion | Airbyte + custom connectors | Pull ERP, CRM, accounting, ticketing, e-commerce, files into a governed pipeline |
| Transformation / semantics | dbt Core, Postgres, DuckDB, ClickHouse | Reusable metrics, cost models, KPI marts, benchmark dimensions |
| Orchestration | LangGraph, LlamaIndex Workflows, Haystack | Deterministic + agentic flows with checkpoints |
| Deliverable generation | Markdown/HTML report engine, PPTX/doc renderer, Mermaid, Apache ECharts | Report-quality docs, diagrams, interactive visuals |
| BI / embedded dashboards | Superset (internal/advanced), Metabase (simple embedded) | Live dashboards, drill-down, metric comments |
| Process mining / mapping | PM4Py, bpmn.io, Camunda Modeler | Infer current-state from logs, render future-state |
| Observability / evaluation | Langfuse, OpenTelemetry, Ragas, DeepEval | Trace runs, latency, cost, relevance, hallucination risk |
| Guardrails / privacy | NeMo Guardrails, Presidio | Enforce output policy, redact/anonymise sensitive data |

[18]

---

## Agent operating model

Mental model: **a consulting pyramid rendered as software.** A single *engagement director* owns the
problem statement and quality bar; multiple *workstream leads* specialise by function; *specialist
sub-agents* handle data, retrieval, benchmarking, deliverable generation, QA and PMO. LangGraph's
durable execution + human-in-the-loop control fits because consulting work is long-running, iterative
and needs explicit approval gates. [19]

### Recommended roles

| Agent | Core responsibilities | Key tools | Memory pattern | Escalation rule |
|---|---|---|---|---|
| Engagement director | Define problem, workplan, route tasks, arbitrate recs, own final narrative | Orchestrator, planner, model router, benchmark library | Engagement + exec-summary memory | When workstreams conflict materially, or impact high & evidence weak |
| Research & benchmark | Source-backed facts, policies, public benchmarks, competitor scans | Web/KB retrieval, citation tools, benchmark datasets | Long-term benchmark memory | When source quality mixed or current facts missing |
| Finance & working-capital | Margin bridge, pricing, receivables, cash cycle, lender readiness | SQL, spreadsheets, dashboards, metric store | Structured fact tables, financial ratios | When data won't reconcile or legal interpretation needed |
| Operations & lean | Process diagnosis, throughput, bottlenecks, root cause, VSM, SOPs | PM4Py, BPMN, simulation, KPI mart | Process memory, sequence patterns | When event logs incomplete or site walkthrough essential |
| Commercial growth | Funnel, segmentation, channel mix, pricing & promo logic | CRM connectors, SQL, analytics, benchmark packs | Commercial metrics memory | When market sizing / competitor evidence thin |
| Risk & compliance | Checklists, control mapping, consent/retention logic, policy warnings | Regulatory KB, rules engine, guardrails | Policy memory with validity dates | On any PII, sector-rule uncertainty, or legal-risk rec |
| Deliverable architect | Reports, decks, charts, process maps, dashboards | Template engine, Mermaid, ECharts, BI embedding | Template memory, style guide | When story/visuals don't match evidence |
| QA & citation verifier | Challenge claims, test groundedness, verify provenance, strip unsupported | Ragas/eval, retrieval cross-check, red-team prompts | Short-lived review memory | Blocking if any uncited high-stakes claim remains |
| PMO & execution | Owners, milestones, KPIs, benefit tracking | OpenProject / task system, dashboards | Initiative memory by workstream | If milestones slip or benefits diverge from plan |

### Prompting principles

1. Every agent separates **facts → assumptions → hypotheses → options → recommendation**, in that order.
2. Major claims carry source references or explicit "model inference" labels.
3. Numbers trace back to raw tables or cited sources, never generated freely.
4. Default to **structured output:** issue trees, tables, KPI dictionaries, process steps, risks, owner lists.
5. No agent except the engagement director presents a final recommendation without a QA pass.

Compact system instruction for workstream agents: *"Act as a consulting workstream lead. Be
hypothesis-driven but evidence-bound. Distinguish fact from assumption. Quantify where possible.
Provide options, not just conclusions. Refuse to overclaim. If source coverage or confidence is weak,
state that clearly and trigger escalation."*

### Memory and escalation design

Four memory stores: **engagement state** (live workflow state); **client knowledge base** (tenant's
docs/metrics/process corpus); **benchmark library** (cross-client de-identified KPI ranges, templates,
sector playbooks); **initiative memory** (post-recommendation outcomes — owners, deadlines, realised
savings, blockers).

Rule-based escalation minimum set: legal/regulatory advice unsupported by an official source;
recommendations on incomplete / non-reconciling data; claimed savings/EBITDA/working-capital release
above a client threshold; suspected prompt injection, tool misuse or exfiltration; answers exposing
personal or third-party confidential data; internal-vs-external benchmark conflicts that change the
recommendation materially.

---

## Product scope, deliverables, roadmap and economics

The best MVP is the smallest set that proves the **commercial loop:** ingest data → diagnose →
produce management-quality deliverables → track execution → show value.

### Prioritised MVP

| Priority | Feature | Why it belongs |
|---|---|---|
| Must | Secure workspace with tenant isolation | Trust + enterprise saleability |
| Must | Connectors: spreadsheets, PDFs, e-mail uploads, accounting exports, CSVs, basic ERP/CRM | Without evidence ingestion the platform is generic |
| Must | Structured diagnostic engine (finance, operations, commercial) | The core consulting logic |
| Must | Report generator with citations + executive summary | Output must feel like a real deliverable |
| Must | KPI dashboard templates (manufacturing, trade, services) | Daily utility beyond one-off reports |
| Must | Process maps + value-stream map generation | Differentiates from ordinary BI / chatbots |
| Must | PMO action tracker (owners, due dates, KPI linkage) | Recommendations without execution tracking don't retain revenue |
| Should | Indic translation + bilingual reporting | Important for adoption, not day-one for every client |
| Should | Benchmark packs by sector & cluster | Raises perceived consulting sophistication |
| Should | Lender-ready & investor-ready pack generation | Strong monetisation for formalising MSMEs |
| Later | Scenario modelling, simulation, what-if optimisation | Valuable once clean pipelines exist |
| Later | Expert marketplace / assisted review network | Powerful, but only after self-serve core proves value |

### Sample report outline

1. **Executive summary** — current situation, quantified problem, top recs, benefit range, next 90 days.
2. **Company snapshot** — business model, product/service mix, customer mix, footprint, seasonality.
3. **Diagnostic findings** — finance, operations, commercial, organisation, risk/compliance.
4. **Benchmark view** — internal trend, peer/public benchmarks, gap analysis.
5. **Root-cause tree** — where value leaks and why.
6. **Recommendation portfolio** — initiatives ranked by effort, impact, payback, dependency.
7. **Implementation roadmap** — owner, milestone, KPI, risk, decision required.
8. **Appendix** — methodology, assumptions, citations, KPI dictionary, data-quality notes.

The advantage is not a new report format — it's making this conservative format **repeatable, fast and evidence-linked.**

### Dashboard mock-up — MSME Transformation Cockpit

```
┌──────────────────┬──────────────────┬──────────────────────┬──────────────────┐
│ Revenue MTD      │ Gross Margin     │ Cash Conversion Cycle│ OTIF / Service   │
│ ₹ 1.82 Cr        │ 24.6%            │ 71 days              │ 87%              │
│ vs Plan: -6%     │ vs Plan: -1.8 pt │ vs Target: +14 days  │ vs Target: -8 pt │
└──────────────────┴──────────────────┴──────────────────────┴──────────────────┘
┌────────────────────────────┬──────────────────────────────────────────────────┐
│ Margin Bridge              │ Receivables Ageing                                │
│ Price / Mix / Discount/Cost│ 0-30 | 31-60 | 61-90 | 90+ days                   │
└────────────────────────────┴──────────────────────────────────────────────────┘
┌────────────────────────────┬──────────────────────────────────────────────────┐
│ Production / Throughput    │ Initiative Tracker                                │
│ Yield | OEE | Rework | TAT │ Owner | Due date | Status | Benefit realised      │
└────────────────────────────┴──────────────────────────────────────────────────┘
Narrative panel:
- Three drivers explain 82% of the EBITDA gap.
- Largest immediate lever: collections on top 20 overdue customers.
- Plant 2 rework spike linked to vendor batch variance and line handoff delay.
```

### Sample value-stream map template

Value-stream mapping traces the material and information flows required to move order → delivery —
well-suited to Indian MSMEs shortening cycle time and releasing working capital. [20]

| Step | Cycle time | Waiting time | First-pass yield | Main waste | AI-generated action |
|---|---|---|---|---|---|
| Quotation | 0.5 day | 1 day | 95% | Slow approvals, inconsistent price book | Auto-price guardrails, approval workflow |
| Planning | 0.5 day | 2 days | 90% | Material uncertainty | Vendor lead-time dashboard, reorder logic |
| Production | 2 days | 1 day | 88% | Changeovers, rework | Bottleneck analysis, SOP update |
| QC / Dispatch | 0.5 day | 1 day | 92% | Paperwork errors | Digital checklist, scan-based verification |
| Invoicing / Collection | 0.25 day | 14 days | 99% | Receivable slippage | Ageing triggers, collection prioritisation |

### Economics and cost estimates

Using IndiaAI's 12-month reserved prices as a GPU basis (≈₹24/hr 1×L4, ₹45/hr L40S, ₹81/hr A100 80GB,
₹117/hr H100 SXM; block storage ₹1.1/GB/mo, object ₹0.78/GB/mo): [21]

| Stage | Indicative GPU footprint | GPU cost basis | Illustrative total monthly run cost |
|---|---|---|---|
| Pilot MVP | 2×L4 (analyst + retrieval) | ~₹34.6k/mo | ~₹1.0–2.0 lakh/mo |
| Early production | 2×L40S + 1×L4 (routing/specialist) | ~₹82.1k/mo | ~₹2.0–4.5 lakh/mo |
| Enterprise / high concurrency | 2×H100 SXM + 2×L4 (support) | ~₹2.03 lakh/mo | ~₹4.5–8.5 lakh/mo |

Totals are illustrative platform models (assume ordinary non-GPU cloud costs on top, and most
workloads routed to cheaper tiers). Build cost (assumption-based planning, not market quotes):
serious MVP **₹1.2–2.7 cr** over ~4–6 months; hardened production v1 **₹3.8–7.9 cr** over 9–12 months.

### Pricing and monetisation for MSMEs

| Offer | Price band | Included | Why it works |
|---|---|---|---|
| Self-serve diagnostic workspace | ₹15,000–35,000/mo | Uploads, dashboards, report drafts, compliance checklists, process maps | Affordable for digitally active small firms; low-friction entry |
| Assisted growth tier | ₹60,000–1,50,000/mo | Monthly review, benchmark pack, custom dashboards, action tracker, bilingual deliverables | Recurring advisory value without full consulting fees |
| Transformation sprint | ₹3–10 lakh / 8–12 wk sprint | Deep diagnostic, initiative design, PMO setup, management deck, weekly steering | Clear alternative to expensive consulting projects |
| PMO / execution office | ₹1–4 lakh/mo | Initiative tracking, KPI monitoring, weekly risk review, board-pack updates | Retains revenue after the strategic report |
| Outcome-linked overlay | 2–10% of validated savings/WC release (capped) | Used selectively where benefits measurable & governance strong | Aligns incentives; never replaces a base fee |

Anchor pricing below visible consulting-market pain while keeping healthy gross margin — a new
category of **productised advice with measurable operational follow-through.** [22]

---

## Governance, compliance and implementation risk

Safest default for Indian deployment: **India-first hosting, India-resident logs, explicit per-tenant
governance.** India's regime is the **DPDP Act 2023 + DPDP Rules 2025** (Rules notified 14 Nov 2025;
clear consent notices required; consent managers must be Indian companies; obligations phased — some
immediate, Rule 4 after one year, a large block 18 months after publication). As of 9 June 2026 India
is in an **active transition period**, not steady state. [23]

Additional constraints: **CERT-In's 2022 directions** require enabling and securely retaining logs for
a rolling 180 days within Indian jurisdiction; **RBI's** payment-system data localisation requires
payment-system data be stored only in India. Any product ingesting bank statements / payment data
should be **Indian-region deployed with Indian log retention from day one.** [24]

Security posture (boring, explicit, enterprise-friendly): tenant isolation at application/retrieval/
storage layers; per-tenant encryption keys where justified; default PII anonymisation/masking before
RAG indexing; document- and row-level access controls; signed audit trails for every model/tool
action; red-team & regression testing of prompts/agents; no unrestricted tool use by generation
agents; human approval gates for final legal/financial/restructuring recommendations. Maps onto
Presidio (PII detection/anonymisation), NeMo Guardrails (I/O control), Langfuse + OpenTelemetry
(traceability). [25]

### Key risks and mitigation

| Risk | Why it matters | Mitigation |
|---|---|---|
| Hallucinated business advice | Wrong recs damage trust immediately | Strict citation policy, QA agent, high-stakes escalation, eval framework, human sign-off |
| Poor source data quality | MSMEs have messy, partial, contradictory data | Data-quality scoring, reconciliation checks, confidence labels, guided data requests |
| Low adoption after first report | Advisory products fail when implementation does | PMO layer, weekly tracking, embedded dashboards, owner-based action plans |
| Prompt injection / data leakage | RAG + tool use can expose client data | Guardrails, tool allow-lists, tenant isolation, retrieval filtering, audit logs |
| Compliance drift | Indian rules evolving, sectoral overlays vary | Regulatory KB with validity dates, legal-review workflow, India-first deployment |
| Cost blowout | Large-model inference can erase SMB economics | Router-based serving, async deliverables, tiered models, cache & batch generation |
| Over-promising vs top firms | Clients may expect impossible custom judgement | Position as productised consulting OS with optional human experts, not a universal replacement |
| IndiaAI dependency risk | Subsidised compute attractive but eligibility-gated | Keep cloud-agnostic option; use IndiaAI where eligible, don't require it |

The platform can credibly replace substantial slices of analytics-heavy, PMO-heavy, reporting-heavy
and diagnostic-heavy consulting. It should **not** imply it autonomously replaces all
judgement-intensive legal, restructuring, tax or boardroom advisory work.

---

## Open questions and limitations

1. **Big 3 / Big 4 pricing evidence is incomplete** — visible only through procurement notices, court/
   tribunal documents and selective award disclosures. Useful directionally, not a substitute for
   direct commercial discovery. [22]
2. **IndiaAI compute is attractive but not universal** — eligibility conditions (DPIIT recognition,
   AI/ML experience, turnover/funding thresholds) mean subsidised access must be a cost advantage where
   available, **not a hard prerequisite** of the business model. [34]

**Bottom line:** build an India-hosted, open-weight, citation-first, multi-agent consulting platform
aimed first at digitally active small & medium enterprises in manufacturing, trade and operations-heavy
services. Start with diagnostics, dashboards, process mapping and PMO. Make every output board-ready,
source-linked and implementation-aware. Execute that narrow brief well, then expand from "AI consulting
assistant" to a full **AI consulting operating system for Indian MSMEs.**

---

## Sources

| # | Source |
|---|---|
| 1, 26 | Ministry of MSME Annual Report 2025-26 — https://msme.gov.in/sites/default/files/MSMEANNUALREPORT2025-26ENGLISH_0.pdf |
| 2, 8, 9, 10 | SIDBI, *Understanding Indian MSME Sector: Progress and Challenges* (13 May 2025) — https://www.sidbi.in/uploads/Understanding_Indian_MSME_sector_Progress_and_Challenges_13_05_25_Final.pdf |
| 3 | McKinsey Operations — how we help clients — https://www.mckinsey.com/capabilities/operations/how-we-help-clients |
| 4, 13, 14 | LangGraph overview — https://docs.langchain.com/oss/python/langgraph/overview |
| 5, 21 | IndiaAI price calculator — https://compute.indiaai.gov.in/indiaaipricecalculator |
| 6, 19 | LangGraph repo — https://github.com/langchain-ai/langgraph |
| 7 | NITI Aayog, *Achieving Efficiencies in MSME Sector Through Convergence of Schemes* — https://www.niti.gov.in/sites/default/files/2026-01/Achieving_Efficiencies_in_MSME_Sector_Through_Convergence_of_Schemes.pdf |
| 11 | McKinsey India overview — https://www.mckinsey.com/in/overview |
| 12, 22 | ITAT order, BCG India (ITA 1401/M/2016, 03 May 2024) — https://itat.gov.in/public/files/upload/1714714833-ITA%201401%20M%202016-BOSTON%20CONSULTING%20GROUP-sd%2003%20MAY%202024.pdf |
| 15, 28 | Qwen3 blog — https://qwenlm.github.io/blog/qwen3/ |
| 16, 30 | RAG paper — https://arxiv.org/abs/2005.11401 |
| 17 | pgvector — https://github.com/pgvector/pgvector |
| 18, 31 | Airbyte — https://github.com/airbytehq/airbyte |
| 20 | Lean.org — Value-Stream Mapping — https://www.lean.org/lexicon-terms/value-stream-mapping/ |
| 23 | DPDP Act 2023 — https://www.indiacode.nic.in/bitstream/123456789/22037/1/a2023-22.pdf |
| 24 | CERT-In Directions (28 Apr 2022) — https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf |
| 25 | Microsoft Presidio — https://github.com/microsoft/presidio |
| 27 | IndiaAI mission portal — https://indiaai.gov.in/ |
| 29 | AI4Bharat LLM — https://ai4bharat.iitm.ac.in/areas/llm |
| 32 | Langfuse docs — https://langfuse.com/docs |
| 33 | PM4Py — https://github.com/process-intelligence-solutions/pm4py |
| 34 | IndiaAI Compute login / eligibility — https://compute.indiaai.gov.in/login |
