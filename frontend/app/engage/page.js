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

function ownerId() {
  try {
    let o = localStorage.getItem("pmguru_owner");
    if (!o) { o = "u-" + Math.random().toString(36).slice(2, 11); localStorage.setItem("pmguru_owner", o); }
    return o;
  } catch { return "demo"; }
}

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
                    <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> Super-Agent · one orchestrated AI team for any MSME problem
                  </div>
                  <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">Bring us your toughest problem.</h1>
                  <p className="text-slate-300 mt-4 max-w-2xl">Describe the situation and our Managing-Partner agent assembles a multi-disciplinary team — finance, operations, risk, the routed specialist and more — then curates one research-grade, Big-4-style engagement report.</p>

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
          {active && active.report && <Report d={active.report} onBack={newEngagement} />}
        </main>
      </div>
    </div>
  );
}

function Report({ d, onBack }) {
  const grad = POSTURE[d.diagnosis?.posture] || POSTURE.Stable;
  return (
    <div id="report" className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      <div className="flex items-center justify-between no-print">
        <button onClick={onBack} className="text-sm font-semibold text-slate-500 hover:text-slate-900">← New engagement</button>
        <button onClick={() => window.print()} className="px-4 py-2 rounded-xl border border-slate-300 text-sm font-semibold hover:bg-white">Print / Save PDF</button>
      </div>

      {/* Cover */}
      <div className={`rounded-3xl p-7 text-white bg-gradient-to-br ${grad} shadow-lg`}>
        <div className="text-[11px] font-bold uppercase tracking-wider opacity-80">AI Consulting OS · Engagement report</div>
        <h1 className="text-3xl sm:text-4xl font-black tracking-tight mt-1">{d.title}</h1>
        <div className="flex flex-wrap items-center gap-3 mt-3 text-sm">
          <span className="bg-white/20 px-2.5 py-1 rounded-full font-semibold">{d.sector}</span>
          <span className="bg-white/20 px-2.5 py-1 rounded-full font-semibold">Risk posture: {d.diagnosis?.posture}</span>
          <span className="bg-white/20 px-2.5 py-1 rounded-full font-semibold">{d.workstreams?.length} workstreams</span>
          <span className="opacity-70 text-[12px]">#{d.engagement_id}</span>
        </div>
        {d.routed_to && <div className="mt-3 text-[13px] opacity-90">Lead practice: <b>{d.routed_to.icon} {d.routed_to.tower}</b> · {d.routed_to.advisor}</div>}
      </div>

      {/* Managing partner brief */}
      {d.managing_partner_brief?.narrative && (
        <div className="bg-white rounded-2xl border-l-4 border-indigo-500 border-y border-r border-slate-200 p-5 shadow-sm">
          <div className="text-[11px] font-bold uppercase tracking-wide text-indigo-600 mb-1">🤝 Managing Partner’s brief</div>
          <p className="text-[15px] leading-relaxed text-slate-800 font-medium">“{d.managing_partner_brief.narrative}”</p>
        </div>
      )}

      {/* Executive summary + team */}
      <Section title="Executive summary" icon="📌">
        <p className="text-[15px] leading-relaxed text-slate-700">{d.executive_summary}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {d.agents_engaged?.map((a, i) => (
            <span key={i} className="text-[11px] bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-1 rounded-lg font-semibold">{a.advisor || a.name}</span>
          ))}
        </div>
      </Section>

      {/* Workstreams */}
      <Section title="Workstream findings" icon="🧩">
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
      <Section title="Prioritised recommendations" icon="🎯">
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
      <Section title="Risk register" icon="⚠️">
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

      {/* 90-day plan */}
      <Section title="90-day action plan" icon="🗓️">
        <div className="space-y-2">
          {d.action_plan?.map((a, i) => (
            <div key={i} className="flex items-center gap-3 bg-white rounded-xl border border-slate-200 p-2.5">
              <span className="shrink-0 text-[10px] font-bold bg-slate-100 text-slate-600 px-2 py-1 rounded">{a.timeline || "—"}</span>
              <span className="text-sm flex-1">{a.step}</span>
              <span className="text-[11px] text-slate-400 font-semibold">{a.owner}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* KPIs + citations */}
      <div className="grid sm:grid-cols-2 gap-6">
        <Section title="KPIs to monitor" icon="📊">
          <ul className="space-y-1.5">
            {d.kpis?.map((k, i) => (
              <li key={i} className="text-sm bg-white rounded-lg border border-slate-200 px-3 py-2 flex items-center justify-between">
                <span className="font-semibold">{k.kpi}</span><span className="text-slate-500 text-[12px]">→ {k.target}</span>
              </li>
            ))}
          </ul>
        </Section>
        <Section title="Sources & citations" icon="📚">
          <div className="flex flex-wrap gap-1.5">
            {d.citations?.map((c, i) => (
              <span key={i} className="text-[11px] bg-white border border-slate-200 px-2 py-1 rounded-lg" title={c.ref || ""}>
                {c.title || c.key}{c.tier && <span className="ml-1 text-[9px] font-bold text-indigo-500">[{c.tier}]</span>}
              </span>
            ))}
          </div>
        </Section>
      </div>

      <p className="text-[11px] text-slate-400 border-t border-slate-200 pt-4">{d.disclaimer}</p>
    </div>
  );
}

function Section({ title, icon, children }) {
  return (
    <section>
      <h3 className="text-lg font-black tracking-tight flex items-center gap-2 mb-3"><span>{icon}</span>{title}</h3>
      {children}
    </section>
  );
}
