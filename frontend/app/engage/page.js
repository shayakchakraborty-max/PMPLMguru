"use client";

/* Engage — the Managing-Partner super-agent. Describe any India-MSME situation (or
   pick a sample), fill an ERP-style intake, and one orchestrated AI team (routed +
   cross-cutting agents) returns a curated, Big-4-style engagement report. Each run is
   its own thread (localStorage). Wired to /api/orchestrate + /api/situations. */

import { useEffect, useMemo, useState } from "react";

const TIERS = ["Tier-1", "Tier-2", "Tier-3"];
const SEV = {
  Critical: "bg-rose-100 text-rose-700 border-rose-200",
  High: "bg-orange-100 text-orange-700 border-orange-200",
  Medium: "bg-amber-100 text-amber-700 border-amber-200",
  Low: "bg-slate-100 text-slate-600 border-slate-200",
};
const POSTURE = {
  Critical: "from-rose-600 to-red-700", Elevated: "from-orange-500 to-rose-600",
  Watch: "from-amber-500 to-orange-600", Stable: "from-emerald-600 to-teal-700",
};
const LS = "pmguru_engagements";

function ownerId() { return "demo-firm"; } // prototype: shared firm tenant

export default function EngagePage() {
  const [threads, setThreads] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [activeReport, setActiveReport] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [form, setForm] = useState({ company: "", sector: "", turnover_cr: "", headcount: "", city_tier: "Tier-2", description: "", top_challenges: "" });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [sits, setSits] = useState(null);
  const [filter, setFilter] = useState("All");

  async function loadServer() {
    try {
      const r = await fetch(`/api/twin?owner=${encodeURIComponent(ownerId())}`, { cache: "no-store" });
      const d = await r.json();
      if (!d.error) {
        if (Array.isArray(d.engagements)) setThreads(d.engagements.map((e) => ({ ...e, report: null })));
        if (d.portfolio) setPortfolio(d.portfolio);
        return d;
      }
    } catch {}
    // offline fallback to localStorage cache
    try { setThreads(JSON.parse(localStorage.getItem(LS) || "[]")); } catch {}
    return null;
  }

  useEffect(() => {
    loadServer();
    (async () => {
      try { const r = await fetch("/api/situations", { cache: "no-store" }); const d = await r.json(); if (!d.error) setSits(d); } catch {}
    })();
    try {
      const pf = JSON.parse(localStorage.getItem("pmguru_prefill") || "null");
      if (pf?.description) { localStorage.removeItem("pmguru_prefill"); runEngagement({ description: pf.description, intake: pf.intake || {} }); }
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const active = useMemo(() => (activeId ? { id: activeId, report: activeReport } : null), [activeId, activeReport]);

  async function openThread(t) {
    setActiveId(t.id);
    if (t.report) { setActiveReport(t.report); }
    else {
      setActiveReport(null);
      try {
        const r = await fetch(`/api/twin?owner=${encodeURIComponent(ownerId())}&id=${encodeURIComponent(t.id)}`, { cache: "no-store" });
        const d = await r.json();
        setActiveReport(d.report || null);
      } catch { setActiveReport(null); }
    }
    setTimeout(() => document.getElementById("report")?.scrollIntoView({ behavior: "smooth" }), 60);
  }

  async function runEngagement(custom) {
    const intake = custom?.intake || {
      company: form.company, sector: form.sector, turnover_cr: form.turnover_cr,
      headcount: form.headcount, city_tier: form.city_tier, top_challenges: form.top_challenges,
    };
    const description = (custom?.description ?? form.description).trim();
    if (!description) { setErr("Describe the business / situation first."); return; }
    setErr(""); setLoading(true); setActiveId(null); setActiveReport(null);
    try {
      const r = await fetch("/api/orchestrate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ description, intake, owner: ownerId(), deep: true }) });
      const d = await r.json();
      if (d.error) { setErr(d.error); setLoading(false); return; }
      const id = d.twin_id || `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      const thread = { id, title: d.title, sector: d.sector, posture: d.diagnosis?.posture, ts: Math.floor(Date.now() / 1000), report: d };
      setThreads((prev) => [thread, ...prev.filter((t) => t.id !== id)].slice(0, 50));
      setActiveId(id); setActiveReport(d);
      loadServer();  // refresh portfolio + server list (keeps report cached locally)
      setTimeout(() => document.getElementById("report")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  function runSituation(s) {
    setForm((f) => ({ ...f, company: s.intake?.company || "", sector: s.sector, turnover_cr: s.intake?.turnover_cr || "", headcount: s.intake?.headcount || "", city_tier: s.intake?.city_tier || "Tier-2", description: s.description, top_challenges: s.intake?.top_challenges || "" }));
    runEngagement({ description: s.description, intake: s.intake });
  }

  function newEngagement() { setActiveId(null); setActiveReport(null); setErr(""); window.scrollTo({ top: 0, behavior: "smooth" }); }
  function delThread(id, e) {
    e.stopPropagation();
    setThreads((prev) => prev.filter((t) => t.id !== id));
    if (activeId === id) { setActiveId(null); setActiveReport(null); }
    fetch("/api/twin", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "delete", owner: ownerId(), id }) }).then(() => loadServer()).catch(() => {});
  }

  const sectors = sits ? ["All", ...sits.sectors] : ["All"];
  const visibleSits = sits ? sits.situations.filter((s) => filter === "All" || s.sector === filter) : [];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <style>{`@media print { .no-print { display:none !important } #report { break-inside: avoid } }`}</style>

      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200 no-print">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <a href="/auto" className="font-black tracking-tight text-sm sm:text-base">Indian MSME Consulting <span className="text-indigo-600">· Powered by AI</span></a>
          <div className="flex items-center gap-1 text-sm">
            <a href="/catalog" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Services</a>
            <a href="/ceo" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">CEO Office</a>
            <a href="/advisor" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Advisors</a>
          </div>
        </div>
      </nav>

      <div className="max-w-[1400px] mx-auto flex">
        {/* Threads sidebar */}
        <aside className="hidden lg:block w-64 shrink-0 border-r border-slate-200 min-h-[calc(100vh-3.5rem)] p-3 no-print">
          <button onClick={newEngagement} className="w-full px-3 py-2.5 rounded-xl bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-500 mb-3">+ New engagement</button>

          {portfolio?.total_engagements > 0 && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 mb-3">
              <div className="text-[10px] uppercase tracking-wide text-slate-400 font-bold mb-1.5">Portfolio</div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black">{portfolio.total_engagements}</span>
                <span className="text-[11px] text-slate-500">engagements</span>
              </div>
              {portfolio.at_risk > 0 && <div className="text-[11px] text-rose-600 font-semibold mt-0.5">{portfolio.at_risk} at risk (Critical/Elevated)</div>}
              <div className="flex gap-1 mt-2">
                {["Critical", "Elevated", "Watch", "Stable"].map((p) => {
                  const n = portfolio.posture_mix?.[p] || 0; if (!n) return null;
                  const c = { Critical: "bg-rose-500", Elevated: "bg-orange-500", Watch: "bg-amber-500", Stable: "bg-emerald-500" }[p];
                  return <span key={p} title={`${p}: ${n}`} className={`h-1.5 rounded-full ${c}`} style={{ flex: n }} />;
                })}
              </div>
            </div>
          )}

          <div className="text-[10px] uppercase tracking-wide text-slate-400 font-bold px-1 mb-1">Engagement threads</div>
          {threads.length === 0 && <div className="text-xs text-slate-400 px-1 py-2">No engagements yet. Run one →</div>}
          <div className="space-y-1">
            {threads.map((t) => (
              <button key={t.id} onClick={() => openThread(t)}
                className={`w-full text-left px-2.5 py-2 rounded-lg text-sm group ${activeId === t.id ? "bg-indigo-50 border border-indigo-200" : "hover:bg-slate-100 border border-transparent"}`}>
                <div className="flex items-center justify-between gap-1">
                  <span className="font-semibold truncate">{t.title}</span>
                  <span onClick={(e) => delThread(t.id, e)} className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-500 text-xs">✕</span>
                </div>
                <div className="text-[10px] text-slate-400">{t.sector}{t.posture ? ` · ${t.posture}` : ""} · {t.ts ? new Date(t.ts * 1000).toLocaleDateString() : ""}</div>
              </button>
            ))}
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 min-w-0">
          {/* Intake */}
          {!active && (
            <div className="no-print">
              <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-14">
                  <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-5">
                    <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> AI-Native Engagement OS · staff · run · deliver · bill
                  </div>
                  <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">Run the whole engagement with an AI team.</h1>
                  <p className="text-slate-300 mt-4 max-w-2xl">Scope an engagement and the Managing-Partner agent staffs the team (Senior Partner → Junior Consultant), assembles the multi-disciplinary AI workstreams, and returns a research-grade report <b>plus</b> a full Engagement 360 — workplan, per-role task lists with AI support, hours and billing. AI agents do the heavy lifting; your people review and sign off.</p>

                  {/* ERP-style intake */}
                  <div className="bg-white/5 border border-white/10 rounded-2xl p-4 sm:p-5 mt-7 space-y-3">
                    <div className="text-[11px] uppercase tracking-wide text-slate-400 font-bold">Engagement intake</div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} placeholder="Company"
                        className="col-span-2 bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
                      <input value={form.sector} onChange={(e) => setForm({ ...form, sector: e.target.value })} placeholder="Sector"
                        className="bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
                      <select value={form.city_tier} onChange={(e) => setForm({ ...form, city_tier: e.target.value })}
                        className="bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-indigo-400 [&>option]:text-slate-900">
                        {TIERS.map((t) => <option key={t}>{t}</option>)}
                      </select>
                      <input value={form.turnover_cr} onChange={(e) => setForm({ ...form, turnover_cr: e.target.value })} placeholder="Turnover (₹ cr)"
                        className="bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
                      <input value={form.headcount} onChange={(e) => setForm({ ...form, headcount: e.target.value })} placeholder="Headcount"
                        className="bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
                      <input value={form.top_challenges} onChange={(e) => setForm({ ...form, top_challenges: e.target.value })} placeholder="Top challenges"
                        className="col-span-2 bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
                    </div>
                    <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3}
                      placeholder="Describe the situation in detail — what's happening, what's the pain, what would success look like…"
                      className="w-full bg-white/10 border border-white/15 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
                    <div className="flex items-center gap-3 flex-wrap">
                      <button onClick={() => runEngagement()} disabled={loading}
                        className="px-6 py-3 rounded-xl bg-indigo-500 hover:bg-indigo-400 font-black text-sm disabled:opacity-50">
                        {loading ? "Convening the engagement team…" : "Run the engagement →"}
                      </button>
                      <span className="text-[11px] text-slate-400">Research-grade · India-aware (₹, GST/Udyam) · curated from multiple specialist agents</span>
                    </div>
                    {err && <p className="text-rose-300 text-sm font-semibold">{err}</p>}
                  </div>
                </div>
              </header>

              {/* Situations gallery */}
              <section className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
                <div className="flex items-end justify-between flex-wrap gap-2 mb-4">
                  <div>
                    <h2 className="text-2xl font-black tracking-tight">Sample engagements</h2>
                    <p className="text-sm text-slate-500">{sits ? `${sits.count} real MSME situations across ${sits.sectors.length} sectors — one click runs a full engagement.` : "Loading sample engagements…"}</p>
                  </div>
                </div>
                <div className="flex gap-1.5 overflow-x-auto pb-2 mb-4">
                  {sectors.map((s) => (
                    <button key={s} onClick={() => setFilter(s)} className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold border ${filter === s ? "bg-indigo-600 text-white border-indigo-600" : "bg-white text-slate-600 border-slate-200 hover:border-indigo-300"}`}>{s}</button>
                  ))}
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {visibleSits.map((s) => (
                    <button key={s.id} onClick={() => runSituation(s)} disabled={loading}
                      className="text-left bg-white rounded-2xl border border-slate-200 p-4 hover:border-indigo-400 hover:shadow-md transition disabled:opacity-50">
                      <div className="flex items-center justify-between">
                        <span className="text-2xl">{s.icon}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">{s.lens}</span>
                      </div>
                      <div className="font-black text-sm mt-2 leading-tight">{s.title}</div>
                      <div className="text-[11px] text-indigo-600 font-semibold mt-0.5">{s.sector}</div>
                      <p className="text-[12px] text-slate-500 mt-1.5 line-clamp-3">{s.description}</p>
                      <div className="text-[11px] text-indigo-600 font-bold mt-2">Run engagement →</div>
                    </button>
                  ))}
                </div>
              </section>
            </div>
          )}

          {loading && !active && (
            <div className="text-center text-slate-500 py-10 no-print">
              <div className="inline-block w-8 h-8 border-[3px] border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-3" />
              <p className="font-semibold">Your Managing Partner is staffing the case and running the workstreams…</p>
            </div>
          )}

          {active && !active.report && (
            <div className="text-center text-slate-500 py-16">
              <div className="inline-block w-7 h-7 border-[3px] border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-3" />
              <p className="font-semibold">Loading engagement…</p>
            </div>
          )}
          {active && active.report && <Report d={active.report} engagementKey={active.id} onBack={newEngagement} />}
        </main>
      </div>
    </div>
  );
}

const PHASE_TINT = { mobilize: "bg-slate-100 text-slate-600", diagnose: "bg-indigo-100 text-indigo-700", design: "bg-violet-100 text-violet-700", validate: "bg-amber-100 text-amber-700", deliver: "bg-emerald-100 text-emerald-700" };
const POSTURE_BADGE = { Critical: "bg-rose-500", Elevated: "bg-orange-500", Watch: "bg-amber-500", Stable: "bg-emerald-500" };
const NAV = [["scope", "Scope"], ["summary", "Summary"], ["diagnosis", "Diagnosis"], ["timeline", "Timeline"], ["team", "Team"], ["findings", "Findings"], ["recommendations", "Recommendations"], ["risks", "Risks"], ["workplan", "Workplan"], ["billing", "Billing"], ["meetings", "Meetings"], ["deliverables", "Deliverables"]];

function Report({ d, engagementKey, onBack }) {
  const grad = POSTURE[d.diagnosis?.posture] || POSTURE.Stable;
  const e = d.delivery?.economics || {};
  const dl = d.delivery || {};
  const et = d.engagement_type;
  const teamSize = (dl.team || []).filter((m) => !m.client_side).length;
  const stats = [
    ["Engagement value", e.tm_fee_label || "—"],
    ["Duration", e.duration_weeks ? `${e.duration_weeks} wks` : "—"],
    ["Team", teamSize ? `${teamSize}` : "—"],
    ["AI-led", dl.ai_leverage_pct != null ? `${dl.ai_leverage_pct}%` : "—"],
    ["Workstreams", d.workstreams?.length || 0],
    ["Risks", `${d.diagnosis?.critical_risks || 0}C / ${d.diagnosis?.high_risks || 0}H`],
  ];
  return (
    <div id="report" className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-7">
      <div className="flex items-center justify-between no-print">
        <button onClick={onBack} className="text-sm font-semibold text-slate-500 hover:text-slate-900">← New engagement</button>
        <button onClick={() => window.print()} className="px-4 py-2 rounded-xl border border-slate-300 text-sm font-semibold hover:bg-white">Print / Save PDF</button>
      </div>

      {/* Dossier header */}
      <div className={`rounded-3xl p-6 sm:p-7 text-white bg-gradient-to-br ${grad} shadow-lg`}>
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider opacity-80">Engagement 360 · {et?.name || d.routed_to?.tower || "Advisory"}</div>
            <h1 className="text-2xl sm:text-4xl font-black tracking-tight mt-1">{d.title}</h1>
            <div className="flex flex-wrap items-center gap-2 mt-2 text-[12px]">
              <span className="bg-white/20 px-2.5 py-1 rounded-full font-semibold">{d.sector}</span>
              {d.routed_to && <span className="bg-white/20 px-2.5 py-1 rounded-full font-semibold">{d.routed_to.icon} {d.routed_to.tower}</span>}
              <span className="opacity-70">#{d.engagement_id}</span>
            </div>
          </div>
          <div className="text-right">
            <div className="inline-flex items-center gap-1.5 bg-white/15 px-3 py-1.5 rounded-full text-sm font-bold">
              <span className={`w-2.5 h-2.5 rounded-full ${POSTURE_BADGE[d.diagnosis?.posture] || "bg-white"}`} /> {d.diagnosis?.posture} risk posture
            </div>
          </div>
        </div>
        {/* metric strip */}
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mt-5">
          {stats.map(([k, v], i) => (
            <div key={i} className="bg-white/10 rounded-xl px-3 py-2">
              <div className="text-[9px] uppercase tracking-wide opacity-70 font-bold">{k}</div>
              <div className="text-base font-black leading-tight mt-0.5">{v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Sticky section nav */}
      <div className="sticky top-14 z-20 bg-slate-50/90 backdrop-blur -mx-4 px-4 py-2 border-y border-slate-200 no-print overflow-x-auto">
        <div className="flex gap-1 min-w-max">
          {NAV.map(([id, label]) => (
            <a key={id} href={`#${id}`} className="px-2.5 py-1 rounded-lg text-[12px] font-semibold text-slate-500 hover:bg-white hover:text-indigo-600">{label}</a>
          ))}
        </div>
      </div>

      {/* Scope & objective */}
      <Section id="scope" title="Scope & objective" icon="🎯">
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <p className="text-[15px] text-slate-800 font-medium">{et?.objective || d.business_context}</p>
          {et && (
            <div className="grid sm:grid-cols-2 gap-4 mt-4">
              <div>
                <div className="text-[11px] uppercase tracking-wide text-slate-400 font-bold mb-1.5">Expected deliverables</div>
                <ul className="space-y-1 text-[13px]">{(et.deliverables || []).map((x, i) => <li key={i} className="flex gap-1.5"><span className="text-indigo-500">▸</span>{x}</li>)}</ul>
              </div>
              <div>
                <div className="text-[11px] uppercase tracking-wide text-slate-400 font-bold mb-1.5">Value levers</div>
                <div className="flex flex-wrap gap-1.5">{(et.value_levers || []).map((x, i) => <span key={i} className="text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-100 px-2 py-1 rounded-lg font-semibold">{x}</span>)}</div>
              </div>
            </div>
          )}
        </div>
      </Section>

      {/* Executive summary + partner brief */}
      <Section id="summary" title="Executive summary" icon="📌">
        {d.managing_partner_brief?.narrative && (
          <div className="bg-gradient-to-br from-indigo-50 to-violet-50 rounded-2xl border-l-4 border-indigo-500 p-4 mb-3">
            <div className="text-[11px] font-bold uppercase tracking-wide text-indigo-600 mb-1">🤝 Managing Partner’s brief</div>
            <p className="text-[15px] leading-relaxed text-slate-800 font-medium">“{d.managing_partner_brief.narrative}”</p>
          </div>
        )}
        <p className="text-[15px] leading-relaxed text-slate-700">{d.executive_summary}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {d.agents_engaged?.map((a, i) => (
            <span key={i} className="text-[11px] bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-1 rounded-lg font-semibold">{a.advisor || a.name}</span>
          ))}
        </div>
      </Section>

      {/* Diagnosis + KPI infographics */}
      <Section id="diagnosis" title="Diagnosis & KPIs" icon="📊">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {(d.kpis || []).slice(0, 8).map((k, i) => (
            <div key={i} className="bg-white rounded-2xl border border-slate-200 p-3">
              <div className="text-[11px] text-slate-400 font-semibold leading-tight">{k.kpi}</div>
              <div className="text-lg font-black text-indigo-600 mt-1">{k.target}</div>
            </div>
          ))}
        </div>
      </Section>

      {/* Project timeline */}
      {dl.timeline?.bars?.length > 0 && (
        <Section id="timeline" title="Project timeline" icon="📅">
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <div className="text-[11px] text-slate-400 mb-3">{dl.timeline.total_weeks}-week plan · {dl.timeline.bars.length} phases</div>
            <div className="space-y-2">
              {dl.timeline.bars.map((b, i) => {
                const tint = ["bg-slate-400", "bg-indigo-500", "bg-violet-500", "bg-amber-500", "bg-emerald-500"][i] || "bg-slate-400";
                return (
                  <div key={i} className="flex items-center gap-2 text-[12px]">
                    <span className="w-20 shrink-0 font-semibold">{b.phase}</span>
                    <div className="flex-1 bg-slate-100 rounded-full h-5 relative">
                      <div className={`${tint} h-5 rounded-full absolute flex items-center justify-end pr-2`} style={{ left: `${((b.start_week - 1) / dl.timeline.total_weeks) * 100}%`, width: `${(b.weeks / dl.timeline.total_weeks) * 100}%` }}>
                        <span className="text-[9px] font-bold text-white/90">{b.weeks}w</span>
                      </div>
                    </div>
                    <span className="w-20 shrink-0 text-right text-slate-400">Wk {b.start_week}{b.weeks > 1 ? `–${b.end_week}` : ""}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </Section>
      )}

      {/* Engagement team */}
      {dl.team?.length > 0 && (
        <Section id="team" title="Engagement team" icon="👔">
          <div className="overflow-x-auto bg-white rounded-2xl border border-slate-200">
            <table className="w-full text-sm">
              <thead><tr className="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2.5 font-bold">Role</th><th className="px-3 py-2.5 font-bold">AI advisor</th><th className="px-3 py-2.5 font-bold text-right">Hours</th><th className="px-3 py-2.5 font-bold text-right">Rate</th><th className="px-3 py-2.5 font-bold">Mandate</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {dl.team.map((m, i) => (
                  <tr key={i} className={m.client_side ? "bg-amber-50/40" : ""}>
                    <td className="px-3 py-2.5 font-semibold whitespace-nowrap">{m.role}{m.client_side && <span className="ml-1 text-[9px] text-amber-600">client</span>}</td>
                    <td className="px-3 py-2.5 text-[12px] text-violet-700">{m.ai_advisor || "—"}</td>
                    <td className="px-3 py-2.5 text-right tabular-nums">{m.allocated_hours || "—"}</td>
                    <td className="px-3 py-2.5 text-right tabular-nums text-slate-500">{m.rate_per_hour ? `₹${m.rate_per_hour.toLocaleString()}` : "—"}</td>
                    <td className="px-3 py-2.5 text-[12px] text-slate-500 max-w-xs">{m.mandate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Workstream findings */}
      <Section id="findings" title="Workstream findings" icon="🧩">
        <div className="grid sm:grid-cols-2 gap-3">
          {d.workstreams?.map((w, i) => (
            <div key={i} className="bg-white rounded-2xl border border-slate-200 p-4">
              <div className="font-black text-sm">{w.advisor || w.name}</div>
              <div className="text-[11px] text-slate-400 font-semibold">{w.name}</div>
              <p className="text-[12px] text-slate-600 mt-2 leading-relaxed">{w.context}</p>
              {w.headline_reco && <div className="mt-2 text-[12px]"><b className="text-emerald-700">Move:</b> {w.headline_reco}</div>}
              {w.top_risk && <div className="mt-1 text-[12px]"><b className="text-rose-700">Watch:</b> {w.top_risk}</div>}
            </div>
          ))}
        </div>
      </Section>

      {/* Recommendations */}
      <Section id="recommendations" title="Prioritised recommendations" icon="✅">
        <ol className="space-y-2">
          {d.recommendations?.map((r, i) => (
            <li key={i} className="flex gap-3 bg-white rounded-xl border border-slate-200 p-3">
              <span className="shrink-0 w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-black flex items-center justify-center">{i + 1}</span>
              <div>
                <div className="text-sm text-slate-800">{r.text}</div>
                {r.advisor && <div className="text-[10px] text-slate-400 font-semibold mt-0.5">via {r.advisor}</div>}
              </div>
            </li>
          ))}
        </ol>
      </Section>

      {/* Risk register */}
      <Section id="risks" title="Risk register (RAID)" icon="⚠️">
        <div className="overflow-x-auto bg-white rounded-2xl border border-slate-200">
          <table className="w-full text-sm">
            <thead><tr className="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500">
              <th className="px-3 py-2.5 font-bold">Risk</th><th className="px-3 py-2.5 font-bold">Severity</th><th className="px-3 py-2.5 font-bold">Control</th><th className="px-3 py-2.5 font-bold">Owner</th>
            </tr></thead>
            <tbody className="divide-y divide-slate-100">
              {d.risks?.map((r, i) => (
                <tr key={i}>
                  <td className="px-3 py-2.5 font-semibold max-w-xs">{r.risk}</td>
                  <td className="px-3 py-2.5"><span className={`text-[11px] px-2 py-0.5 rounded border font-bold ${SEV[r.severity] || SEV.Low}`}>{r.severity}</span></td>
                  <td className="px-3 py-2.5 text-[12px] text-slate-600 max-w-xs">{r.control}</td>
                  <td className="px-3 py-2.5 text-[12px] text-slate-500">{r.owner}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* AI-supported workplan */}
      {dl.workplan?.length > 0 && <Workplan dl={dl} />}

      {/* Hours & billing */}
      {e.total_hours != null && <Billing e={e} />}

      {/* Meetings + MoM */}
      <Meetings engagementKey={engagementKey} />

      {/* AI deliverables */}
      <div id="deliverables"><DeckGen report={d} /></div>

      {/* Appendix */}
      <Section title="Sources & citations" icon="📚">
        <div className="flex flex-wrap gap-1.5">
          {d.citations?.map((c, i) => (
            <span key={i} className="text-[11px] bg-white border border-slate-200 px-2 py-1 rounded-lg" title={c.ref || ""}>
              {c.title || c.key}{c.tier && <span className="ml-1 text-[9px] font-bold text-indigo-500">[{c.tier}]</span>}
            </span>
          ))}
        </div>
      </Section>

      <p className="text-[11px] text-slate-400 border-t border-slate-200 pt-4">{d.disclaimer}</p>
    </div>
  );
}

function Workplan({ dl }) {
  const billable = (dl.roles || []).filter((r) => r.billable);
  const [role, setRole] = useState("all");
  const roleTitle = (k) => (dl.roles || []).find((r) => r.key === k)?.title || k;
  const tasks = role === "all" ? dl.workplan : (dl.workplan || []).filter((t) => t.owner_role === role);
  return (
    <Section id="workplan" title="AI-supported workplan" icon="🗂️">
      <div className="flex items-center gap-2 flex-wrap mb-3 no-print">
        <span className="text-[11px] font-bold text-slate-500">View as:</span>
        <button onClick={() => setRole("all")} className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border ${role === "all" ? "bg-slate-900 text-white border-slate-900" : "bg-white border-slate-200"}`}>Whole team</button>
        {billable.map((r) => {
          const n = (dl.by_role_tasks?.[r.key] || []).length; if (!n) return null;
          return <button key={r.key} onClick={() => setRole(r.key)} className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border ${role === r.key ? "bg-indigo-600 text-white border-indigo-600" : "bg-white border-slate-200 hover:border-indigo-300"}`}>{r.title} ({n})</button>;
        })}
      </div>
      <div className="space-y-2">
        {tasks.map((t) => (
          <div key={t.id} className="bg-white rounded-xl border border-slate-200 p-3">
            <div className="flex items-start gap-2 flex-wrap">
              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${PHASE_TINT[t.phase] || "bg-slate-100"}`}>{t.phase}</span>
              <span className="font-bold text-sm flex-1 min-w-[180px]">{t.title}</span>
              <span className="text-[10px] text-slate-400 font-semibold">{roleTitle(t.owner_role)} · {t.est_hours}h</span>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">{t.ai_automation_pct}% AI</span>
            </div>
            <div className="text-[12px] text-slate-600 mt-1.5">🤖 {t.ai_support}</div>
            <div className="flex items-center gap-2 mt-2 text-[11px]">
              {t.ai_agent && <a href={`/advisor?agent=${t.ai_agent}`} className="px-2 py-0.5 rounded bg-violet-100 text-violet-700 font-semibold hover:bg-violet-200">▶ Run {t.ai_agent}</a>}
              <span className="text-slate-400">Deliverable: {t.deliverable}</span>
              {t.approver_role && <span className="ml-auto text-slate-400">✍ sign-off: {roleTitle(t.approver_role)}</span>}
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

function Billing({ e }) {
  return (
    <Section id="billing" title="Hours & billing" icon="💳">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
        {[["Total effort", `${e.total_hours} hrs`], ["Duration", `${e.duration_weeks} wks`], ["T&M fee", e.tm_fee_label], ["Fixed fee", e.fixed_fee_label], ["Blended", `${e.blended_rate_label}/hr`]].map(([k, v], i) => (
          <div key={i} className="bg-white rounded-2xl border border-slate-200 p-3"><div className="text-[10px] uppercase tracking-wide text-slate-400 font-bold">{k}</div><div className="text-lg font-black mt-0.5">{v}</div></div>
        ))}
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="px-3 py-2 bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500 font-bold">Effort & cost by role</div>
          <table className="w-full text-sm"><tbody className="divide-y divide-slate-100">
            {(e.by_role || []).map((r, i) => (
              <tr key={i}><td className="px-3 py-2 font-semibold">{r.role}</td><td className="px-3 py-2 text-right tabular-nums text-slate-500">{r.hours}h × ₹{r.rate_per_hour.toLocaleString()}</td><td className="px-3 py-2 text-right tabular-nums font-bold">{r.amount_label}</td></tr>
            ))}
            <tr className="bg-slate-900 text-white font-bold"><td className="px-3 py-2">Total (T&amp;M)</td><td className="px-3 py-2 text-right">{e.total_hours}h</td><td className="px-3 py-2 text-right">{e.tm_fee_label}</td></tr>
          </tbody></table>
        </div>
        <div className="space-y-3">
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-2">Fee options</div>
            <ul className="text-sm space-y-1.5">
              <li className="flex justify-between"><span>Time &amp; Materials</span><b>{e.tm_fee_label}</b></li>
              <li className="flex justify-between"><span>Fixed Fee</span><b>{e.fixed_fee_label}</b></li>
              <li className="flex justify-between"><span>Monthly Retainer</span><b>{e.monthly_retainer_label}</b></li>
              <li className="flex justify-between text-slate-500"><span>Blended rate</span><b>{e.blended_rate_label}/hr</b></li>
            </ul>
            <div className="flex flex-wrap gap-1.5 mt-2">{(e.fee_models || []).map((f, i) => <span key={i} className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-semibold">{f}</span>)}</div>
          </div>
          <p className="text-[11px] text-slate-400">{e.note}</p>
        </div>
      </div>
    </Section>
  );
}

function MeetingPlanner({ engagementKey, onScheduled }) {
  const [purpose, setPurpose] = useState("");
  const [attendees, setAttendees] = useState("");
  const [plan, setPlan] = useState(null);
  const [slot, setSlot] = useState("");
  const [busy, setBusy] = useState("");
  const [result, setResult] = useState(null);

  async function propose() {
    if (!purpose.trim()) return;
    setBusy("propose"); setPlan(null); setResult(null);
    try {
      const r = await fetch("/api/meetings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "propose", purpose, attendees }) });
      const d = await r.json(); setPlan(d); setSlot(d.proposed_slots?.[0] || "");
    } catch {} finally { setBusy(""); }
  }
  async function schedule() {
    setBusy("schedule");
    try {
      const r = await fetch("/api/meetings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "schedule", owner: ownerId(), engagement_id: engagementKey, title: plan.title, type: plan.type, attendees, agenda: plan.agenda, duration_min: plan.duration_min, slot }) });
      const d = await r.json(); setResult(d); setPlan(null); onScheduled?.();
    } catch {} finally { setBusy(""); }
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 no-print">
      <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-2">📆 Plan a meeting (AI · MS 365, human-in-the-loop)</div>
      <div className="flex gap-2 flex-wrap">
        <input value={purpose} onChange={(e) => setPurpose(e.target.value)} placeholder="Purpose (e.g. O2C diagnostic with CFO)" className="flex-1 min-w-[200px] border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
        <input value={attendees} onChange={(e) => setAttendees(e.target.value)} placeholder="Attendees (emails)" className="flex-1 min-w-[160px] border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
        <button onClick={propose} disabled={!!busy} className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-500 disabled:opacity-50">{busy === "propose" ? "Drafting…" : "AI: draft agenda & slots"}</button>
      </div>
      {plan?.ok && (
        <div className="mt-3 bg-slate-50 rounded-xl p-3">
          <div className="font-bold text-sm">{plan.title}</div>
          <ul className="text-[12px] text-slate-600 mt-1 list-disc pl-5">{plan.agenda.map((a, i) => <li key={i}>{a}</li>)}</ul>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <select value={slot} onChange={(e) => setSlot(e.target.value)} className="border border-slate-200 rounded-lg px-2 py-1.5 text-sm">
              {plan.proposed_slots.map((s) => <option key={s} value={s}>{new Date(s).toLocaleString()}</option>)}
            </select>
            <button onClick={schedule} disabled={busy === "schedule"} className="px-4 py-1.5 rounded-lg bg-emerald-600 text-white font-bold text-sm hover:bg-emerald-500 disabled:opacity-50">{busy === "schedule" ? "Scheduling…" : "✓ Approve & schedule"}</button>
          </div>
        </div>
      )}
      {result?.ok && (
        <div className="mt-2 text-[12px] font-semibold text-emerald-700">
          {result.backend === "msgraph" ? <>✓ Teams invite sent · <a className="underline" href={result.invite?.join_url} target="_blank" rel="noreferrer">join link</a></> : "✓ Meeting scheduled (draft invite — connect MS 365 at deploy to auto-send Teams invite)."}
        </div>
      )}
    </div>
  );
}

function Meetings({ engagementKey }) {
  const [data, setData] = useState(null);
  const [form, setForm] = useState({ title: "", date: "", type: "Client site visit", attendees: "", transcript: "" });
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const recRef = useState({ rec: null, chunks: [] })[0];
  const TYPES = ["Client site visit", "SME workshop", "Steering committee", "Kickoff", "Working session", "Interview", "Internal"];

  async function load() {
    try { const r = await fetch(`/api/meetings?owner=${encodeURIComponent(ownerId())}&engagement_id=${encodeURIComponent(engagementKey || "")}`, { cache: "no-store" }); const d = await r.json(); if (!d.error) setData(d); } catch {}
  }
  useEffect(() => { load(); }, [engagementKey]); // eslint-disable-line

  async function capture() {
    if (!form.transcript.trim()) return;
    setBusy(true);
    try {
      await fetch("/api/meetings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "add", owner: ownerId(), engagement_id: engagementKey, ...form }) });
      setForm({ title: "", date: "", type: form.type, attendees: "", transcript: "" }); load();
    } catch {}
    finally { setBusy(false); }
  }

  // Browser recording -> store audio blob (transcription via AWS Transcribe at deploy)
  async function toggleRec() {
    if (recording) { recRef.rec?.stop(); setRecording(false); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream); recRef.rec = rec; recRef.chunks = [];
      rec.ondataavailable = (e) => recRef.chunks.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(recRef.chunks, { type: "audio/webm" });
        const b64 = await new Promise((res) => { const r = new FileReader(); r.onload = () => res(String(r.result).split(",")[1] || ""); r.readAsDataURL(blob); });
        const up = await fetch("/api/blob", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ owner: ownerId(), scope: "recording", filename: `meeting-${Date.now()}.webm`, content_base64: b64, content_type: "audio/webm" }) }).then((r) => r.json());
        setForm((f) => ({ ...f, transcript: f.transcript + (f.transcript ? "\n" : "") + `[recording stored: ${up.key || "audio"} — transcription via AWS Transcribe at deploy]` }));
      };
      rec.start(); setRecording(true);
    } catch { alert("Microphone unavailable — paste the notes/transcript instead."); }
  }

  const reg = data?.registers;
  return (
    <section id="meetings" className="border-t-2 border-slate-200 pt-8 mt-8 space-y-5 scroll-mt-28">
      <div>
        <h2 className="text-2xl font-black tracking-tight">🎙️ Client &amp; SME meetings</h2>
        <p className="text-sm text-slate-500 mt-1">Plan &amp; schedule via MS 365 (AI proposes, you approve), keep the recording on or paste notes — AI writes the minutes and rolls them into the engagement.</p>
      </div>

      <MeetingPlanner engagementKey={engagementKey} onScheduled={load} />

      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-2 no-print">
          <div className="flex gap-2">
            <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Meeting title" className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
            <input value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} placeholder="Date" className="w-28 border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
          </div>
          <div className="flex gap-2">
            <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm">{TYPES.map((t) => <option key={t}>{t}</option>)}</select>
            <input value={form.attendees} onChange={(e) => setForm({ ...form, attendees: e.target.value })} placeholder="Attendees (CFO, SME…)" className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
          </div>
          <textarea value={form.transcript} onChange={(e) => setForm({ ...form, transcript: e.target.value })} rows={5} placeholder="Paste notes / transcript, or hit Record…" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
          <div className="flex items-center gap-2">
            <button onClick={toggleRec} className={`px-3 py-2 rounded-lg font-bold text-sm ${recording ? "bg-rose-600 text-white animate-pulse" : "bg-white border border-slate-300"}`}>{recording ? "⏺ Stop recording" : "🎙️ Record"}</button>
            <button onClick={capture} disabled={busy} className="flex-1 px-3 py-2 rounded-lg bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-500 disabled:opacity-50">{busy ? "AI writing minutes…" : "Capture & write minutes (AI)"}</button>
          </div>
        </div>

        {/* Registers rolled from meetings */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4">
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-2">Registers (from all meetings)</div>
          {!reg || (reg.action_items.length + reg.decisions.length + reg.risks_issues.length) === 0 ? (
            <p className="text-[12px] text-slate-400">Capture a meeting to populate decisions, actions and risks.</p>
          ) : (
            <div className="space-y-2 text-[12px] max-h-56 overflow-y-auto">
              {reg.action_items.length > 0 && <div><b className="text-indigo-700">Actions</b>{reg.action_items.slice(0, 8).map((a, i) => <div key={i} className="flex justify-between border-b border-slate-50 py-0.5"><span>{a.action}</span><span className="text-slate-400 shrink-0 ml-2">{a.owner}{a.due ? ` · ${a.due}` : ""}</span></div>)}</div>}
              {reg.decisions.length > 0 && <div className="pt-1"><b className="text-emerald-700">Decisions</b>{reg.decisions.slice(0, 5).map((d, i) => <div key={i} className="py-0.5">• {d.decision}</div>)}</div>}
              {reg.risks_issues.length > 0 && <div className="pt-1"><b className="text-rose-700">Risks/Issues</b>{reg.risks_issues.slice(0, 5).map((r, i) => <div key={i} className="py-0.5">• {r.risk}</div>)}</div>}
            </div>
          )}
        </div>
      </div>

      {/* Past meetings with MoM */}
      {data?.meetings?.length > 0 && (
        <div className="space-y-2">
          {data.meetings.map((m) => {
            const mom = m.mom || {};
            return (
              <div key={m.id} className="bg-white rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between flex-wrap gap-1">
                  <div className="font-black text-sm">{m.title} <span className="text-[10px] font-semibold text-slate-400">· {m.type}{m.date ? ` · ${m.date}` : ""}</span></div>
                  <span className="text-[10px] text-slate-400">{(m.attendees || []).join(", ")} · {m.engine === "groq" ? "AI (Groq)" : "AI"}</span>
                </div>
                {mom.summary && <p className="text-[12px] text-slate-600 mt-1.5"><b>Summary:</b> {mom.summary}</p>}
                <div className="grid sm:grid-cols-3 gap-3 mt-2 text-[12px]">
                  <div><b className="text-emerald-700">Decisions</b>{(mom.decisions || []).map((d, i) => <div key={i}>• {d}</div>) || null}{(!mom.decisions || mom.decisions.length === 0) && <div className="text-slate-300">—</div>}</div>
                  <div><b className="text-indigo-700">Action items</b>{(mom.action_items || []).map((a, i) => <div key={i}>• {a.action} <span className="text-slate-400">[{a.owner}{a.due ? `, ${a.due}` : ""}]</span></div>)}{(!mom.action_items || mom.action_items.length === 0) && <div className="text-slate-300">—</div>}</div>
                  <div><b className="text-rose-700">Risks/Issues</b>{(mom.risks_issues || []).map((r, i) => <div key={i}>• {r}</div>)}{(!mom.risks_issues || mom.risks_issues.length === 0) && <div className="text-slate-300">—</div>}</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function DeckGen({ report }) {
  const [out, setOut] = useState(null);
  const [busy, setBusy] = useState("");
  async function gen(kind) {
    setBusy(kind); setOut(null);
    try {
      const r = await fetch("/api/deliverable", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ report, kind }) });
      setOut(await r.json());
    } catch (e) { setOut({ error: e.message }); }
    finally { setBusy(""); }
  }
  function download() {
    if (!out?.markdown) return;
    const blob = new Blob([out.markdown], { type: "text/markdown" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = `${(report.title || "engagement").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}-${out.kind}.md`; a.click();
  }
  async function pptx() {
    setBusy("pptx"); setOut(null);
    try {
      const r = await fetch("/api/deliverable", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ report, kind: "pptx" }) });
      const d = await r.json();
      if (d.pptx_base64) {
        const bytes = Uint8Array.from(atob(d.pptx_base64), (c) => c.charCodeAt(0));
        const a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([bytes], { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" }));
        a.download = d.filename || "engagement_deck.pptx"; a.click();
        setOut({ kind: "pptx", slides: d.slide_count ? Array.from({ length: d.slide_count }, (_, i) => ({ n: i + 1, title: "Slide " + (i + 1) })) : null, _downloaded: true });
      } else { setOut(d); }
    } catch (e) { setOut({ error: e.message }); }
    finally { setBusy(""); }
  }
  return (
    <section className="bg-gradient-to-br from-violet-50 to-indigo-50 border border-indigo-100 rounded-2xl p-5 mt-8">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-lg font-black tracking-tight">📑 AI deliverables</h3>
          <p className="text-[13px] text-slate-500">On completion, the AI drafts a board-ready deck or an executive memo in top-firm format.</p>
        </div>
        <div className="flex gap-2 no-print">
          <button onClick={() => gen("deck")} disabled={!!busy} className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-500 disabled:opacity-50">{busy === "deck" ? "Drafting…" : "Generate board deck"}</button>
          <button onClick={() => gen("memo")} disabled={!!busy} className="px-4 py-2 rounded-xl border border-slate-300 bg-white font-semibold text-sm hover:border-indigo-300 disabled:opacity-50">{busy === "memo" ? "Drafting…" : "Exec memo"}</button>
          <button onClick={pptx} disabled={!!busy} className="px-4 py-2 rounded-xl border border-slate-300 bg-white font-semibold text-sm hover:border-indigo-300 disabled:opacity-50">{busy === "pptx" ? "Building…" : "⬇ PPTX"}</button>
          {out?.markdown && <button onClick={download} className="px-4 py-2 rounded-xl border border-slate-300 bg-white font-semibold text-sm hover:border-indigo-300">⬇ .md</button>}
        </div>
      </div>
      {out?.error && <p className="text-rose-600 text-sm mt-3">{out.error}</p>}
      {out?._downloaded && <p className="text-emerald-600 text-sm mt-3 font-semibold">✓ PPTX downloaded ({out.slides?.length} slides).</p>}
      {out?.note && <p className="text-[12px] text-amber-600 mt-3">{out.note}</p>}
      {out?.slides && (
        <div className="mt-4 grid sm:grid-cols-2 gap-2">
          {out.slides.map((s) => (
            <div key={s.n} className="bg-white rounded-xl border border-slate-200 p-3">
              <div className="text-[10px] font-black text-slate-300">SLIDE {s.n}</div>
              <div className="font-bold text-[13px] leading-snug">{s.title}</div>
            </div>
          ))}
        </div>
      )}
      {out?.markdown && !out?.slides && (
        <pre className="mt-4 bg-white border border-slate-200 rounded-xl p-3 text-[12px] whitespace-pre-wrap max-h-72 overflow-y-auto">{out.markdown}</pre>
      )}
      {out?.formats_pending && <p className="text-[11px] text-slate-400 mt-2">Download as Markdown today; native {out.formats_pending.join(", ")} export at deploy.</p>}
    </section>
  );
}

function Section({ title, icon, children, id }) {
  return (
    <section id={id} className={id ? "scroll-mt-28" : ""}>
      <h3 className="text-lg font-black tracking-tight flex items-center gap-2 mb-3"><span>{icon}</span>{title}</h3>
      {children}
    </section>
  );
}
