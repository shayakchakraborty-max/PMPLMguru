"use client";
import { useEffect, useMemo, useState } from "react";

/* ============================================================
   PMGuru Advisor — 20 research-grade MSME AI agents
   Two modes (Startup / Existing Business), business-type filter,
   responsive mobile + desktop, audit-ready report rendering.
   ============================================================ */

const CATEGORY_STYLE = {
  "Strategy & Growth":    { grad: "from-indigo-600 to-purple-600", chip: "bg-indigo-100 text-indigo-700", ring: "hover:border-indigo-400" },
  "Finance & Compliance": { grad: "from-emerald-600 to-teal-600",  chip: "bg-emerald-100 text-emerald-700", ring: "hover:border-emerald-400" },
  "Operations":           { grad: "from-blue-600 to-sky-600",      chip: "bg-blue-100 text-blue-700",      ring: "hover:border-blue-400" },
  "Risk & Diligence":     { grad: "from-rose-600 to-amber-600",    chip: "bg-rose-100 text-rose-700",      ring: "hover:border-rose-400" },
  "Workspace":            { grad: "from-violet-600 to-pink-600",   chip: "bg-violet-100 text-violet-700",  ring: "hover:border-violet-400" },
  "Sustainability":       { grad: "from-green-600 to-lime-600",    chip: "bg-green-100 text-green-700",    ring: "hover:border-green-400" },
  "Technology & Cyber":   { grad: "from-cyan-600 to-blue-700",     chip: "bg-cyan-100 text-cyan-700",      ring: "hover:border-cyan-400" },
};
const CATEGORY_ORDER = ["Strategy & Growth", "Finance & Compliance", "Operations", "Risk & Diligence", "Technology & Cyber", "Sustainability", "Workspace"];

const SECTOR_LABELS = {
  manufacturing: "Manufacturing", retail: "Retail", wholesale: "Wholesale & Distribution",
  import: "Import", export: "Export", import_export_hybrid: "Import-Export Hybrid",
  agro_rural: "Agro & Rural", food_bev: "Food & Beverage", logistics: "Logistics & Supply Chain",
  construction: "Construction & Infrastructure", technology: "Technology & AI", professional_services: "Professional Services",
  healthcare: "Healthcare & Pharma", education: "Education & Training", media_creative: "Media & Creative",
  tourism: "Tourism & Hospitality", real_estate: "Real Estate & Property",
};
const SECTOR_KEYS = Object.keys(SECTOR_LABELS);

const SEV = {
  Critical: { chip: "bg-rose-100 text-rose-700 border-rose-200", dot: "bg-rose-500" },
  High:     { chip: "bg-amber-100 text-amber-700 border-amber-200", dot: "bg-amber-500" },
  Medium:   { chip: "bg-sky-100 text-sky-700 border-sky-200", dot: "bg-sky-500" },
  Low:      { chip: "bg-slate-100 text-slate-600 border-slate-200", dot: "bg-slate-400" },
};

/* ---- Structured inputs the agents actually read (scenario.data) ---- */
const FIELD_LIB = {
  turnover_cr:      { label: "Annual turnover (₹ cr)", type: "number", ph: "8" },
  revenue_cr:       { label: "Annual revenue (₹ cr)", type: "number", ph: "10" },
  receivables_cr:   { label: "Receivables outstanding (₹ cr)", type: "number", ph: "2" },
  dso_days:         { label: "DSO (days)", type: "number", ph: "75" },
  bank_balance:     { label: "Bank balance (₹ cr)", type: "number", ph: "0.5" },
  on_einvoice:      { label: "Already on e-invoicing?", type: "bool" },
  itc_mismatch:     { label: "ITC mismatches in GSTR-2B?", type: "bool" },
  cash_crunch:      { label: "Facing a cash crunch?", type: "bool" },
  gstin:            { label: "GSTIN", type: "text", ph: "27ABCDE1234F1Z5" },
  headcount:        { label: "Number of employees", type: "number", ph: "24" },
  dead_stock_value: { label: "Dead stock value (₹ lakh)", type: "number", ph: "3" },
  stockouts:        { label: "Frequent stockouts?", type: "bool" },
  current_system:   { label: "Current system", type: "text", ph: "spreadsheets / Tally" },
  volume:           { label: "Monthly volume (invoices / SKUs / users)", type: "text", ph: "500 invoices, 1200 SKUs" },
  stage:            { label: "Fundraise stage", type: "select", options: ["pre-seed", "seed", "series a", "early"] },
  dpiit:            { label: "DPIIT-recognised startup?", type: "bool" },
  cap_table:        { label: "Cap table ready?", type: "bool" },
  financials:       { label: "3-yr financials available?", type: "bool" },
  metrics:          { label: "Metrics pack ready?", type: "bool" },
  data_room:        { label: "Data room exists?", type: "bool" },
  purpose:          { label: "Diligence purpose", type: "select", options: ["investment", "acquisition", "lending"] },
  destination:      { label: "Export destination", type: "text", ph: "UAE" },
  iec:              { label: "Have IEC code?", type: "bool" },
  hsn:              { label: "Product HSN code", type: "text", ph: "0904" },
  category:         { label: "Market category", type: "text", ph: "B2B logistics SaaS" },
  geography:        { label: "Geography", type: "text", ph: "Tier-2 India" },
  price:            { label: "Annual price point (₹)", type: "number", ph: "120000" },
  competitors:      { label: "Competitors (comma-separated)", type: "list", ph: "Acme, Beta, Cstore" },
  problem:          { label: "Product problem", type: "text", ph: "onboarding drop-off" },
  metric:           { label: "Success metric", type: "text", ph: "activation rate" },
  outlets:          { label: "Number of outlets", type: "number", ph: "200" },
  cycle_days:       { label: "Current cycle time (days)", type: "number", ph: "6" },
  target_days:      { label: "Target cycle time (days)", type: "number", ph: "2" },
  process:          { label: "Process to document", type: "text", ph: "batch-expiry handling" },
  contract_type:    { label: "Contract type", type: "select", options: ["distributor", "vendor", "employment", "nda", "lease", "saas", "service"] },
  horizon:          { label: "Planning horizon", type: "text", ph: "this quarter" },
};

const AGENT_FIELDS = {
  gst_compliance:     ["turnover_cr", "on_einvoice", "itc_mismatch", "gstin"],
  cfo_finance:        ["revenue_cr", "receivables_cr", "dso_days", "cash_crunch", "bank_balance"],
  msme_due_diligence: ["purpose", "financials", "cap_table", "dpiit", "data_room"],
  erp_consultant:     ["current_system", "volume"],
  investor_readiness: ["stage", "dpiit", "cap_table", "financials", "metrics"],
  inventory_agent:    ["dead_stock_value", "stockouts"],
  export_compliance:  ["destination", "iec", "hsn"],
  ceo_copilot:        ["horizon"],
  coo_operations:     ["cycle_days", "target_days"],
  risk_audit:         [],
  sop_agent:          ["process"],
  hr_payroll:         ["headcount"],
  market_research:    ["category", "geography", "price"],
  competitor_intel:   ["competitors"],
  product_manager:    ["problem", "metric"],
  notion_workspace:   [],
  sales_gtm:          ["outlets"],
  procurement_agent:  [],
  customer_support:   [],
  legal_contracts:    ["contract_type"],
};

/* ---- Demo scenarios (one click → fill form + run) ---- */
const DEMO_SAMPLES = {
  startup: [
    { label: "AI/SaaS seed due diligence", agent: "msme_due_diligence", sector: "technology", subtype: "AI Startups",
      description: "Investor evaluating an AI/SaaS startup before a Rs.5 cr seed cheque; needs red flags and which government benefits it qualifies for.",
      data: { purpose: "investment", financials: true, cap_table: true, dpiit: true, data_room: false } },
    { label: "Investor readiness (seed)", agent: "investor_readiness", sector: "technology", subtype: "SaaS",
      description: "AI/SaaS startup founder preparing for a seed raise; needs a clean data room and to verify government benefits.",
      data: { stage: "seed", dpiit: true, cap_table: false, financials: true, metrics: false } },
    { label: "Market sizing (TAM/SAM/SOM)", agent: "market_research", sector: "technology", subtype: "SaaS",
      description: "Founder wants the TAM for a B2B logistics SaaS in Tier-2 India.",
      data: { category: "B2B logistics SaaS", geography: "Tier-2 India", price: 120000 } },
    { label: "Product roadmap (PRD + RICE)", agent: "product_manager", sector: "technology", subtype: "SaaS",
      description: "SaaS founder needs a prioritized 90-day roadmap and a PRD for the MVP.",
      data: { problem: "onboarding drop-off", metric: "week-1 activation rate" } },
    { label: "GST setup for new SaaS", agent: "gst_compliance", sector: "technology", subtype: "SaaS",
      description: "New SaaS business setting up GST and invoicing correctly from day one.",
      data: { turnover_cr: 2, on_einvoice: false, itc_mismatch: false } },
  ],
  existing: [
    { label: "Wholesaler cash crunch", agent: "cfo_finance", sector: "wholesale", subtype: "FMCG",
      description: "FMCG wholesaler with Rs.10 cr revenue and Rs.2 cr stuck in receivables, facing a cash crunch before the GST payment.",
      data: { revenue_cr: 10, receivables_cr: 2, cash_crunch: true } },
    { label: "EU exporter ESG / CBAM", agent: "sustainability_esg", sector: "manufacturing", subtype: "Auto Parts",
      description: "Steel auto-parts manufacturer exporting to the EU; buyers are asking for embedded-carbon (CBAM) data and a decarbonisation plan.",
      data: {} },
    { label: "D2C data protection (DPDP)", agent: "cyber_dpdp", sector: "retail", subtype: "E-commerce/D2C",
      description: "D2C brand holding lakhs of customer records with no consent notice, no MFA and no breach plan, worried about DPDP.",
      data: {} },
    { label: "Pharma inventory & expiry", agent: "inventory_agent", sector: "healthcare", subtype: "Pharmacies",
      description: "Pharma distributor with batch expiry risk, Rs.3 lakh dead stock and frequent stockouts.",
      data: { dead_stock_value: 3, stockouts: true } },
    { label: "Factory crossing 20 staff (payroll)", agent: "hr_payroll", sector: "manufacturing", subtype: "Auto Parts",
      description: "Factory crossing 20 employees must start EPF compliance and set up compliant payroll.",
      data: { headcount: 24 } },
    { label: "Electronics importer (customs + BIS)", agent: "export_compliance", sector: "import", subtype: "Electronics/Mobile",
      description: "Electronics importer filing Bill of Entry at customs, unsure about BIS certification and IGST credit.",
      data: { destination: "China", iec: true, hsn: "8517" } },
    { label: "Spice exporter (RoDTEP + IEC)", agent: "export_compliance", sector: "export", subtype: "Spices/Tea/Coffee",
      description: "Spice exporter to UAE unsure about RoDTEP, IEC and export documentation.",
      data: { destination: "UAE", iec: true, hsn: "0904" } },
    { label: "Distributor beat plan (200 outlets)", agent: "sales_gtm", sector: "wholesale", subtype: "FMCG",
      description: "Distributor needs a salesman beat plan for 200 outlets with secondary-sales visibility.",
      data: { outlets: 200 } },
    { label: "ERP for a manufacturer", agent: "erp_consultant", sector: "manufacturing", subtype: "Machinery",
      description: "Manufacturer on spreadsheets wants an ERP for BOM, production and GST.",
      data: { current_system: "spreadsheets", volume: "300 invoices, 800 SKUs" } },
    { label: "Where can fraud happen? (risk audit)", agent: "risk_audit", sector: "retail", subtype: "Supermarket/Hypermarket",
      description: "Owner wants to know where cash and inventory fraud could happen and what controls to put in place.",
      data: {} },
  ],
};

function coerce(key, raw) {
  const f = FIELD_LIB[key];
  if (!f) return raw;
  if (f.type === "number") return raw === "" || raw == null ? undefined : Number(raw);
  if (f.type === "bool") return !!raw;
  if (f.type === "list") return String(raw || "").split(",").map((s) => s.trim()).filter(Boolean);
  return raw === "" ? undefined : raw;
}

export default function AdvisorPage() {
  const [meta, setMeta] = useState(null);
  const [metaErr, setMetaErr] = useState("");
  const [mode, setMode] = useState("startup");
  const [sector, setSector] = useState("");
  const [subtype, setSubtype] = useState("");
  const [search, setSearch] = useState("");
  const [active, setActive] = useState(null); // active agent key
  const [desc, setDesc] = useState("");
  const [form, setForm] = useState({}); // structured scenario.data
  const [running, setRunning] = useState(false);
  const [report, setReport] = useState(null);
  const [runErr, setRunErr] = useState("");

  const [retrying, setRetrying] = useState(false);

  // Load the agent registry. The backend can be waking up and
  // take ~30s to wake on the first request, so we auto-retry a few times before
  // surfacing a clear, actionable error.
  async function loadMeta(attempt = 0) {
    setMetaErr(""); setRetrying(attempt > 0);
    try {
      const r = await fetch("/api/agents", { cache: "no-store" });
      const d = await r.json();
      if (d && d.agents && Object.keys(d.agents).length) {
        setMeta(d); setRetrying(false); return;
      }
      // Reachable but stale/old backend (no agents) or an error payload
      const why = d?.error
        ? `Backend reachable but returned: "${d.error}". It is likely running an older build without the agent layer.`
        : "Backend reachable but returned no agents (older build).";
      if (attempt < 3) { setTimeout(() => loadMeta(attempt + 1), 4000); return; }
      setMetaErr(why);
    } catch (e) {
      if (attempt < 3) { setTimeout(() => loadMeta(attempt + 1), 4000); return; }
      setMetaErr(`Could not reach the backend (${e.message}).`);
    } finally {
      setRetrying(false);
    }
  }

  useEffect(() => { loadMeta(0); /* eslint-disable-next-line */ }, []);

  // Deep-link: /advisor?agent=<key> pre-opens that consultant (used by the
  // Practice Areas on the landing page). Runs once after meta loads.
  const [deepLinked, setDeepLinked] = useState(false);
  useEffect(() => {
    if (!meta || deepLinked) return;
    const want = new URLSearchParams(window.location.search).get("agent");
    const a = want && (meta.agents || {})[want];
    if (a) {
      if (a.modes && !a.modes.includes(mode) && a.modes[0]) setMode(a.modes[0]);
      openAgent(want, a);
    }
    setDeepLinked(true);
    /* eslint-disable-next-line */
  }, [meta]);

  const agents = meta?.agents || {};
  const taxonomy = meta?.business_taxonomy || {};

  const visibleAgents = useMemo(() => {
    const q = search.trim().toLowerCase();
    return Object.entries(agents)
      .filter(([, a]) => (a.modes || []).includes(mode))
      .filter(([, a]) => !q || `${a.name} ${a.purpose}`.toLowerCase().includes(q))
      .sort((a, b) => a[1].name.localeCompare(b[1].name));
  }, [agents, mode, search]);

  const byCategory = useMemo(() => {
    const groups = {};
    for (const [key, a] of visibleAgents) {
      const c = a.category || "Other";
      (groups[c] = groups[c] || []).push([key, a]);
    }
    return groups;
  }, [visibleAgents]);

  function openAgent(key, a) {
    setActive(key);
    setReport(null);
    setRunErr("");
    setForm({});
    const subtypeLabel = subtype ? `${subtype} ` : (sector ? `${SECTOR_LABELS[sector]} ` : "");
    const framing = mode === "startup"
      ? `I am starting a new ${subtypeLabel}business in India. `
      : `I run an existing ${subtypeLabel}business in India. `;
    setDesc(`${framing}${a.example_scenario || ""}`.trim());
    setTimeout(() => document.getElementById("scenario-panel")?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
  }

  // One-click demo: set mode/filters/agent/form, then run.
  async function applySample(s) {
    if (s.sector) setSector(s.sector);
    setSubtype(s.subtype || "");
    setActive(s.agent);
    setDesc(s.description);
    setForm(s.data || {});
    setReport(null); setRunErr(""); setRunning(true);
    try {
      const r = await fetch("/api/agents", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent: s.agent, description: s.description, data: s.data || {} }),
      });
      const d = await r.json();
      if (d.error) setRunErr(d.error);
      else if (d.status === "error") setRunErr(d.error || "Agent error");
      else setReport(d);
      setTimeout(() => document.getElementById("report")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (e) { setRunErr(e.message); }
    finally { setRunning(false); }
  }

  async function run() {
    if (!active) return;
    setRunning(true); setReport(null); setRunErr("");
    // Coerce structured fields into scenario.data
    const data = {};
    for (const key of (AGENT_FIELDS[active] || [])) {
      const v = coerce(key, form[key]);
      if (v !== undefined && v !== "" && !(Array.isArray(v) && v.length === 0)) data[key] = v;
    }
    try {
      const r = await fetch("/api/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent: active, description: desc, data }),
      });
      const d = await r.json();
      if (d.error) setRunErr(d.error);
      else if (d.status === "error") setRunErr(d.error || "Agent error");
      else setReport(d);
      setTimeout(() => document.getElementById("report")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (e) {
      setRunErr(e.message);
    } finally {
      setRunning(false);
    }
  }

  function setField(key, val) { setForm((f) => ({ ...f, [key]: val })); }

  const activeAgent = active ? agents[active] : null;
  const activeStyle = activeAgent ? (CATEGORY_STYLE[activeAgent.category] || CATEGORY_STYLE["Operations"]) : null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white text-slate-900">
      {/* ---------- Hero ---------- */}
      <header className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] sm:text-xs font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            Indian MSME Consulting · Powered by AI · {meta ? `${meta.live_count}/${meta.total_count}` : "20"} research-grade AI agents · India MSME
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            An AI consulting team for<br className="hidden sm:block" />
            <span className="bg-gradient-to-r from-indigo-400 to-emerald-300 bg-clip-text text-transparent"> every Indian business</span>
          </h1>
          <p className="text-sm sm:text-lg text-slate-300 mt-4 max-w-2xl">
            Pick your situation, choose a specialist agent, and get an audit-ready report — citation-backed,
            with ERP & Notion actions, risks, KPIs and a step-by-step plan.
          </p>

          {/* Mode toggle */}
          <div className="mt-7 inline-flex bg-white/10 rounded-2xl p-1 w-full sm:w-auto">
            <ModeBtn active={mode === "startup"} onClick={() => { setMode("startup"); setActive(null); setReport(null); }}
              emoji="🚀" title="New Startup" sub="Validate & launch" />
            <ModeBtn active={mode === "existing"} onClick={() => { setMode("existing"); setActive(null); setReport(null); }}
              emoji="🏢" title="Existing Business" sub="Run & scale" />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {metaErr && (
          <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-xl p-5 text-sm mb-6">
            <div className="font-black mb-1">Couldn't load the AI agents</div>
            <p className="text-amber-800">{metaErr}</p>
            <ul className="list-disc pl-5 mt-2 space-y-0.5 text-amber-800">
              <li>The backend may be waking up (free tier sleeps ~30s) — wait a moment and retry.</li>
              <li>Or the backend needs to be redeployed to the latest version.</li>
            </ul>
            <button onClick={() => loadMeta(0)} disabled={retrying}
              className="mt-3 px-4 py-2 rounded-lg bg-amber-600 text-white font-bold hover:bg-amber-700 disabled:opacity-50">
              {retrying ? "Retrying…" : "Retry"}
            </button>
          </div>
        )}
        {!meta && !metaErr && (
          <div>
            <div className="text-center text-slate-500 text-sm mb-4">{retrying ? "Waking up the backend…" : "Loading agents…"}</div>
            <SkeletonGrid />
          </div>
        )}

        {/* ---------- Filters ---------- */}
        {meta && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5 mb-8 sticky top-2 z-20">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Select label="Sector" value={sector}
                onChange={(v) => { setSector(v); setSubtype(""); }}
                options={[["", "All sectors"], ...SECTOR_KEYS.map((k) => [k, SECTOR_LABELS[k]])]} />
              <Select label="Business type" value={subtype} disabled={!sector}
                onChange={setSubtype}
                options={[["", sector ? "All types" : "Choose a sector first"], ...((taxonomy[sector] || []).map((t) => [t, t]))]} />
              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wide mb-1">Search agents</label>
                <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="e.g. GST, cash, export, hiring…"
                  className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-3">
              {visibleAgents.length} agents for <b className="text-slate-600">{mode === "startup" ? "new startups" : "existing businesses"}</b>
              {sector ? <> · sector: <b className="text-slate-600">{SECTOR_LABELS[sector]}</b></> : null}
            </p>
          </div>
        )}

        {/* ---------- Demo samples ---------- */}
        {meta && (
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-black uppercase tracking-wide text-slate-700">⚡ Try a demo</span>
              <span className="text-xs text-slate-400">one click → fills the form & runs the agent</span>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1">
              {(DEMO_SAMPLES[mode] || []).map((s, i) => (
                <button key={i} onClick={() => applySample(s)} disabled={running}
                  className="shrink-0 text-xs font-bold bg-white border border-slate-300 hover:border-indigo-400 hover:bg-indigo-50 text-slate-700 rounded-full px-3.5 py-2 transition disabled:opacity-50">
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ---------- Agent grid ---------- */}
        {meta && CATEGORY_ORDER.filter((c) => byCategory[c]?.length).map((cat) => (
          <section key={cat} className="mb-8">
            <div className="flex items-center gap-2 mb-3">
              <span className={`inline-block w-2.5 h-2.5 rounded-full bg-gradient-to-r ${CATEGORY_STYLE[cat].grad}`} />
              <h2 className="text-sm font-black uppercase tracking-wide text-slate-700">{cat}</h2>
              <span className="text-xs text-slate-400">({byCategory[cat].length})</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {byCategory[cat].map(([key, a]) => (
                <AgentCard key={key} a={a} cat={cat} active={active === key} onClick={() => openAgent(key, a)} />
              ))}
            </div>
          </section>
        ))}

        {/* ---------- Scenario panel ---------- */}
        {activeAgent && (
          <div id="scenario-panel" className="bg-white rounded-2xl border-2 border-slate-200 shadow-md overflow-hidden mb-8">
            <div className={`bg-gradient-to-r ${activeStyle.grad} text-white p-5`}>
              <div className="flex items-center gap-3">
                <span className="text-3xl">{activeAgent.icon}</span>
                <div>
                  <div className="font-black text-lg">{activeAgent.name}</div>
                  <div className="text-xs opacity-80">{activeAgent.category}</div>
                </div>
              </div>
              <p className="text-sm opacity-90 mt-3">{activeAgent.purpose}</p>
            </div>
            <div className="p-5">
              <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wide mb-1">Describe your situation</label>
              <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={4}
                className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                placeholder="Tell the agent about your business, numbers and the decision you face…" />

              {/* Structured inputs — feed real data to the agent for sharper, audit-ready analysis */}
              {(AGENT_FIELDS[active] || []).length > 0 && (
                <div className="mt-4">
                  <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mb-2">
                    Details for {activeAgent.name} <span className="text-slate-400 normal-case font-normal">(optional — improves accuracy)</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {(AGENT_FIELDS[active] || []).map((key) => (
                      <Field key={key} fieldKey={key} value={form[key]} onChange={(v) => setField(key, v)} />
                    ))}
                  </div>
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3 mt-4">
                <button onClick={run} disabled={running || !desc.trim()}
                  className={`flex-1 px-6 py-3.5 rounded-xl font-black text-white text-base transition bg-gradient-to-r ${activeStyle.grad} disabled:opacity-50`}>
                  {running ? "Analysing…" : `Run ${activeAgent.name} →`}
                </button>
                <button onClick={() => { setActive(null); setReport(null); }}
                  className="px-5 py-3.5 rounded-xl font-bold text-slate-600 border border-slate-300 hover:bg-slate-50">
                  Cancel
                </button>
              </div>
              {runErr && <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-3 text-sm mt-3">{runErr}</div>}
            </div>
          </div>
        )}

        {/* ---------- Report ---------- */}
        {report && <Report report={report} style={activeStyle} />}
      </main>

      <footer className="text-center text-xs text-slate-400 py-10 px-4">
        Indian MSME Consulting · Powered by AI · citation-backed, audit-ready outputs · works on mobile & desktop · template-driven (no LLM dependency)
      </footer>
    </div>
  );
}

/* ============================ Report ============================ */
function Report({ report, style }) {
  const o = report.output || {};
  const cls = report.classification || {};
  const grad = style?.grad || "from-slate-700 to-slate-900";

  return (
    <div id="report" className="bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
      {/* Report hero */}
      <div className={`bg-gradient-to-r ${grad} text-white p-6 sm:p-8`}>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="text-xs font-bold opacity-80 uppercase tracking-wide">Audit-ready report</div>
            <h2 className="text-2xl sm:text-3xl font-black mt-1">{report.icon} {report.name}</h2>
          </div>
          <button onClick={() => typeof window !== "undefined" && window.print()}
            className="bg-white/15 hover:bg-white/25 text-white text-sm font-bold px-4 py-2 rounded-lg print:hidden">
            ⬇ Save / Print
          </button>
        </div>
        <div className="flex flex-wrap gap-2 mt-4">
          {cls.industry && <Pill>{cls.industry.replace(/_/g, " ")}</Pill>}
          {cls.size && <Pill>{cls.size}</Pill>}
          {cls.trade_role && cls.trade_role !== "domestic" && <Pill>{cls.trade_role.replace(/_/g, " ")}</Pill>}
          {cls.is_startup && <Pill>startup</Pill>}
          {cls.is_tech && <Pill>tech</Pill>}
          {cls.is_ai && <Pill>AI</Pill>}
          {report.envelope_complete && <Pill>✓ complete</Pill>}
        </div>
      </div>

      <div className="p-5 sm:p-8 space-y-8">
        {/* Deeper agent brain — research-grade, RAG + free-LLM grounded */}
        {report.intelligence && <IntelligenceBlock intel={report.intelligence} />}

        {/* Context */}
        <Section icon="📌" title="Business context"><p className="text-slate-700 leading-relaxed">{o.business_context}</p></Section>

        {/* Government incentives — highlighted when present */}
        {o.government_incentives?.length > 0 && (
          <Section icon="🇮🇳" title="Government incentives & benefits">
            <div className="grid sm:grid-cols-2 gap-3">
              {o.government_incentives.map((g, i) => (
                <div key={i} className="border border-emerald-200 bg-emerald-50 rounded-xl p-4">
                  <div className="font-black text-emerald-800 text-sm">{g.benefit}</div>
                  <div className="text-sm text-slate-700 mt-1">{g.value}</div>
                  <div className="text-xs text-slate-500 mt-2"><b>Eligibility:</b> {g.eligibility}</div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* KPIs at a glance */}
        {o.kpis_to_monitor?.length > 0 && (
          <Section icon="📊" title="KPIs to monitor">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {o.kpis_to_monitor.map((k, i) => (
                <div key={i} className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                  <div className="text-[11px] font-bold text-slate-500 uppercase">{k.kpi}</div>
                  <div className="text-lg font-black text-slate-800 mt-1">{String(k.target)}</div>
                  <div className="text-[11px] text-slate-400 mt-1">now: {String(k.current)} · {k.source}</div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Risks */}
        {o.risks?.length > 0 && (
          <Section icon="⚠️" title="Risks & controls">
            <div className="space-y-3">
              {o.risks.map((r, i) => {
                const s = SEV[r.severity] || SEV.Medium;
                return (
                  <div key={i} className="border border-slate-200 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                      <span className={`mt-1 w-2.5 h-2.5 rounded-full shrink-0 ${s.dot}`} />
                      <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`text-[10px] font-black px-2 py-0.5 rounded-full border ${s.chip}`}>{r.severity}</span>
                          {r.likelihood && <span className="text-[10px] text-slate-400">likelihood: {r.likelihood}</span>}
                        </div>
                        <div className="font-semibold text-slate-800 text-sm mt-1.5">{r.risk}</div>
                        {r.control && <div className="text-sm text-slate-600 mt-1"><b className="text-slate-500">Control:</b> {r.control}</div>}
                        {r.owner && <div className="text-xs text-slate-400 mt-1">Owner: {r.owner}</div>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Section>
        )}

        {/* Recommendations */}
        {o.recommendations?.length > 0 && (
          <Section icon="✅" title="Recommendations">
            <ol className="space-y-2.5">
              {o.recommendations.map((r, i) => (
                <li key={i} className="flex gap-3">
                  <span className="shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 font-black text-xs flex items-center justify-center">{i + 1}</span>
                  <span className="text-sm text-slate-700">{r}</span>
                </li>
              ))}
            </ol>
          </Section>
        )}

        {/* Action plan timeline */}
        {o.action_plan?.length > 0 && (
          <Section icon="🗺️" title="Action plan">
            <div className="space-y-0">
              {o.action_plan.map((a, i) => (
                <div key={i} className="flex gap-4 pb-4 last:pb-0">
                  <div className="flex flex-col items-center">
                    <span className="w-3 h-3 rounded-full bg-indigo-500" />
                    {i < o.action_plan.length - 1 && <span className="w-0.5 flex-1 bg-slate-200 my-1" />}
                  </div>
                  <div className="pb-2">
                    <div className="text-sm font-semibold text-slate-800">{a.step}</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {a.owner} · {a.timeline}{a.system && a.system !== "—" ? ` · ${a.system}` : ""}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* ERP + Notion impact */}
        <div className="grid md:grid-cols-2 gap-6">
          {o.erp_impact?.length > 0 && (
            <Section icon="🗄️" title="ERP impact">
              <ul className="space-y-2">
                {o.erp_impact.map((e, i) => (
                  <li key={i} className="text-sm">
                    <span className="inline-block text-[10px] font-black px-2 py-0.5 rounded bg-blue-100 text-blue-700 mr-2 align-middle">{e.module}</span>
                    <span className="text-slate-700">{e.change}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}
          {o.notion_update?.length > 0 && (
            <Section icon="🗂️" title="Notion workspace updates">
              <ul className="space-y-2">
                {o.notion_update.map((n, i) => (
                  <li key={i} className="text-sm">
                    <span className="inline-block text-[10px] font-black px-2 py-0.5 rounded bg-violet-100 text-violet-700 mr-2 align-middle">{n.database}</span>
                    <span className="text-slate-700">{n.entry || (Array.isArray(n.entries) ? n.entries.join(", ") : "")}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}
        </div>

        {/* Compliance impact */}
        {o.compliance_impact && (
          <Section icon="⚖️" title="Compliance impact">
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-slate-700">{o.compliance_impact}</div>
          </Section>
        )}

        {/* Assumptions + required data + questions (collapsible details) */}
        <div className="grid md:grid-cols-2 gap-6">
          {o.required_data?.length > 0 && (
            <Section icon="📥" title="Data the agent needs">
              <ul className="space-y-1.5">
                {o.required_data.map((d, i) => (
                  <li key={i} className="text-sm flex items-start gap-2">
                    <span>{d.have ? "✅" : "⬜"}</span>
                    <span className="text-slate-700">{d.item}{d.why ? <span className="text-slate-400"> — {d.why}</span> : null}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}
          {o.clarifying_questions?.length > 0 && (
            <Section icon="❓" title="Clarifying questions">
              <ul className="space-y-1.5 list-disc pl-5">
                {o.clarifying_questions.map((q, i) => <li key={i} className="text-sm text-slate-700">{q}</li>)}
              </ul>
            </Section>
          )}
        </div>

        {o.assumptions?.length > 0 && (
          <Section icon="🧩" title="Assumptions">
            <ul className="space-y-1.5 list-disc pl-5">
              {o.assumptions.map((a, i) => <li key={i} className="text-sm text-slate-600">{a}</li>)}
            </ul>
          </Section>
        )}

        {/* Human approval */}
        {o.human_approval_points?.length > 0 && (
          <Section icon="🙋" title="Human approval points">
            <ul className="space-y-1.5">
              {o.human_approval_points.map((h, i) => (
                <li key={i} className="text-sm text-slate-700 flex gap-2"><span>🔒</span><span>{h}</span></li>
              ))}
            </ul>
          </Section>
        )}

        {/* Citations */}
        {o.citations?.length > 0 && (
          <Section icon="📚" title="Sources & citations">
            <div className="grid sm:grid-cols-2 gap-3">
              {o.citations.map((c, i) => (
                <div key={i} className="border border-slate-200 rounded-xl p-3">
                  <div className="flex items-center gap-2">
                    <span className={`text-[9px] font-black px-1.5 py-0.5 rounded ${c.tier === "A" ? "bg-emerald-100 text-emerald-700" : c.tier === "B" ? "bg-sky-100 text-sky-700" : "bg-slate-100 text-slate-500"}`}>
                      Tier {c.tier}
                    </span>
                    <span className="font-bold text-sm text-slate-800">{c.title}</span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">{c.ref}</div>
                  <div className="text-[11px] text-slate-400 mt-1">{c.authority}{c.url ? ` · ${c.url}` : ""}</div>
                </div>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}

/* ============================ Bits ============================ */
function ModeBtn({ active, onClick, emoji, title, sub }) {
  return (
    <button onClick={onClick}
      className={`flex-1 sm:flex-none flex items-center gap-3 px-4 sm:px-6 py-3 rounded-xl transition text-left ${active ? "bg-white text-slate-900 shadow" : "text-white/80 hover:text-white"}`}>
      <span className="text-2xl">{emoji}</span>
      <span>
        <span className="block font-black text-sm leading-tight">{title}</span>
        <span className={`block text-[11px] ${active ? "text-slate-500" : "text-white/60"}`}>{sub}</span>
      </span>
    </button>
  );
}

function AgentCard({ a, cat, active, onClick }) {
  const st = CATEGORY_STYLE[cat] || CATEGORY_STYLE["Operations"];
  return (
    <button onClick={onClick}
      className={`text-left bg-white rounded-2xl border-2 p-4 transition shadow-sm hover:shadow-md ${active ? "border-indigo-500 ring-2 ring-indigo-200" : `border-slate-200 ${st.ring}`}`}>
      <div className="flex items-center gap-2.5">
        <span className="text-2xl">{a.icon}</span>
        <span className="font-black text-sm text-slate-800 leading-tight">{a.name}</span>
      </div>
      <p className="text-xs text-slate-500 mt-2 line-clamp-3">{a.purpose}</p>
      <span className={`inline-block mt-3 text-[10px] font-bold px-2 py-0.5 rounded-full ${st.chip}`}>{cat}</span>
    </button>
  );
}

function Field({ fieldKey, value, onChange }) {
  const f = FIELD_LIB[fieldKey];
  if (!f) return null;
  if (f.type === "bool") {
    return (
      <label className="flex items-center gap-2.5 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 cursor-pointer">
        <input type="checkbox" checked={!!value} onChange={(e) => onChange(e.target.checked)} className="w-4 h-4 accent-indigo-600" />
        <span className="text-sm text-slate-700">{f.label}</span>
      </label>
    );
  }
  if (f.type === "select") {
    return (
      <div>
        <label className="block text-[11px] font-bold text-slate-500 mb-1">{f.label}</label>
        <select value={value ?? ""} onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400">
          <option value="">—</option>
          {f.options.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      </div>
    );
  }
  return (
    <div>
      <label className="block text-[11px] font-bold text-slate-500 mb-1">{f.label}</label>
      <input type={f.type === "number" ? "number" : "text"} value={value ?? ""} placeholder={f.ph || ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
    </div>
  );
}

function Select({ label, value, onChange, options, disabled }) {
  return (
    <div>
      <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wide mb-1">{label}</label>
      <select value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm bg-white disabled:bg-slate-100 disabled:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-400">
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </div>
  );
}

function IntelligenceBlock({ intel }) {
  const b = intel.ai_brief;
  const ai = intel.engine?.startsWith("groq");
  return (
    <div className="rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50 to-violet-50 p-5 sm:p-6">
      <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
        <h3 className="flex items-center gap-2 text-sm font-black text-indigo-900 uppercase tracking-wide">
          🧠 AI Intelligence Brief
        </h3>
        <div className="flex items-center gap-1.5 text-[10px] font-bold">
          <span className={`px-2 py-0.5 rounded-full ${ai ? "bg-indigo-600 text-white" : "bg-slate-200 text-slate-600"}`}>{ai ? "AI-synthesised" : "deterministic"}</span>
          {intel.grounded && <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">RAG + web grounded</span>}
        </div>
      </div>

      {b ? (
        <div className="space-y-4">
          {b.headline && <p className="text-lg font-black text-slate-900">{b.headline}</p>}
          {b.situation && <p className="text-sm text-slate-700 leading-relaxed">{b.situation}</p>}
          {b.key_insights?.length > 0 && (
            <div>
              <div className="text-xs font-bold uppercase tracking-wide text-indigo-700 mb-1.5">Key insights</div>
              <ul className="space-y-1">{b.key_insights.map((k, i) => <li key={i} className="text-sm flex gap-2"><span className="text-indigo-500">◆</span><span>{k}</span></li>)}</ul>
            </div>
          )}
          {b.prioritized_actions?.length > 0 && (
            <div>
              <div className="text-xs font-bold uppercase tracking-wide text-indigo-700 mb-1.5">Prioritised actions</div>
              <div className="space-y-2">
                {b.prioritized_actions.map((a, i) => (
                  <div key={i} className="bg-white rounded-lg border border-slate-200 p-3">
                    <div className="text-sm font-semibold">{a.action}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">Impact: {a.impact} · Effort: {a.effort}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {b.watch_outs?.length > 0 && (
            <div>
              <div className="text-xs font-bold uppercase tracking-wide text-rose-600 mb-1.5">Watch-outs</div>
              <ul className="space-y-1">{b.watch_outs.map((w, i) => <li key={i} className="text-sm flex gap-2"><span className="text-rose-500">⚠</span><span>{w}</span></li>)}</ul>
            </div>
          )}
        </div>
      ) : (
        <p className="text-sm text-slate-600">Grounded research attached below. (Add a free LLM key on the backend for an AI-synthesised narrative.)</p>
      )}

      {(intel.sources?.length > 0 || intel.doc_evidence?.length > 0) && (
        <details className="mt-4 text-xs">
          <summary className="cursor-pointer text-indigo-700 font-semibold">Evidence & sources ({(intel.sources?.length || 0) + (intel.doc_evidence?.length || 0)})</summary>
          <div className="mt-2 space-y-1.5">
            {intel.doc_evidence?.map((d, i) => (
              <div key={`d${i}`} className="text-slate-600"><span className="font-bold text-emerald-700">[Your doc]</span> {d.source}: {d.snippet}</div>
            ))}
            {intel.sources?.map((s, i) => (
              <div key={`s${i}`} className="text-slate-600">
                <span className="font-bold text-indigo-700">[{s.source || "Web"}]</span>{" "}
                {s.url ? <a href={s.url} target="_blank" rel="noopener noreferrer" className="hover:underline">{s.title}</a> : s.title}: {s.snippet}
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

function Section({ icon, title, children }) {
  return (
    <div>
      <h3 className="flex items-center gap-2 text-sm font-black text-slate-800 uppercase tracking-wide mb-3">
        <span>{icon}</span>{title}
      </h3>
      {children}
    </div>
  );
}

function Pill({ children }) {
  return <span className="text-[11px] font-bold bg-white/15 text-white px-2.5 py-1 rounded-full">{children}</span>;
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-white rounded-2xl border border-slate-200 p-4 animate-pulse">
          <div className="h-6 w-2/3 bg-slate-100 rounded" />
          <div className="h-3 w-full bg-slate-100 rounded mt-3" />
          <div className="h-3 w-4/5 bg-slate-100 rounded mt-2" />
        </div>
      ))}
    </div>
  );
}
