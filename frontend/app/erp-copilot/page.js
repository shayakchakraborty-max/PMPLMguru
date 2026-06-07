"use client";

/* ERP Copilot — an ERP *Intelligence Layer*, not a transactional ERP.
   Describe the business once; each ERP domain (Finance / Sales / Operations /
   Projects) runs its research-grade AI agent (deep brain: RAG + web + free LLM)
   and returns an advisory brief. Reuses /api/agents. */

import { useState } from "react";

const DOMAINS = [
  { key: "finance", icon: "💰", title: "Finance Copilot", agent: "cfo_finance", grad: "from-emerald-500 to-teal-600",
    advises: ["Revenue & profitability", "Cost structure", "AP / AR & cash flow", "Working capital"] },
  { key: "sales", icon: "📣", title: "Sales Copilot", agent: "sales_gtm", grad: "from-pink-500 to-rose-600",
    advises: ["Leads & pipeline", "Customers & opportunities", "Channels & distribution", "Collections"] },
  { key: "operations", icon: "⚙️", title: "Operations Copilot", agent: "coo_operations", grad: "from-amber-500 to-orange-600",
    advises: ["Procurement", "Inventory", "Production / throughput", "Logistics"] },
  { key: "projects", icon: "🗂️", title: "Projects Copilot", agent: "product_manager", grad: "from-violet-500 to-fuchsia-600",
    advises: ["Initiatives", "Tasks & owners", "Milestones", "Roadmap"] },
];

export default function ErpCopilot() {
  const [desc, setDesc] = useState("");
  const [state, setStateMap] = useState({}); // key -> {loading, brief, err, engine}

  async function runDomain(d) {
    if (!desc.trim()) { setStateMap((s) => ({ ...s, [d.key]: { err: "Describe your business first (top of page)." } })); return; }
    setStateMap((s) => ({ ...s, [d.key]: { loading: true } }));
    try {
      const r = await fetch("/api/agents", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ agent: d.agent, description: desc, deep: true }) });
      const data = await r.json();
      if (data.error) { setStateMap((s) => ({ ...s, [d.key]: { err: data.error } })); return; }
      const intel = data.intelligence || {};
      setStateMap((s) => ({ ...s, [d.key]: { brief: intel.ai_brief, sources: intel.sources || [], docs: intel.doc_evidence || [], engine: intel.engine, output: data.output } }));
    } catch (e) { setStateMap((s) => ({ ...s, [d.key]: { err: e.message } })); }
  }

  function runAll() { DOMAINS.forEach(runDomain); }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <a href="/auto" className="font-black tracking-tight text-sm sm:text-base">Indian MSME Consulting <span className="text-indigo-600">· Powered by AI</span></a>
          <div className="flex items-center gap-1 text-sm">
            <a href="/ceo" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">CEO Office</a>
            <a href="/monitor" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Monitor</a>
          </div>
        </div>
      </nav>

      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-14">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> ERP Copilot · an intelligence layer, not another ERP
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">Your ERP, with a brain.</h1>
          <p className="text-slate-300 mt-3 max-w-2xl">Not a transactional system to migrate to — an AI advisor that understands your Finance, Sales, Operations and Projects and tells you what to do. Describe your business; each copilot runs its research-grade agent.</p>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 sm:p-5 mt-6 space-y-3">
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={2}
              placeholder="e.g. textile wholesale & distribution business in Surat, ₹28 cr turnover, stretched receivables…"
              className="w-full bg-white/10 border border-white/15 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            <button onClick={runAll} className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl font-black hover:opacity-90 transition">Run full ERP review →</button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid md:grid-cols-2 gap-5">
          {DOMAINS.map((d) => {
            const st = state[d.key] || {};
            return (
              <div key={d.key} className="bg-white rounded-2xl border border-slate-200 overflow-hidden flex flex-col">
                <div className={`bg-gradient-to-r ${d.grad} text-white p-5`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2"><span className="text-2xl">{d.icon}</span><span className="font-black text-lg">{d.title}</span></div>
                    <button onClick={() => runDomain(d)} disabled={st.loading}
                      className="bg-white/20 hover:bg-white/30 text-white text-xs font-bold px-3 py-1.5 rounded-lg disabled:opacity-60">
                      {st.loading ? "Thinking…" : (st.brief || st.output ? "Re-run" : "Run advisory")}
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {d.advises.map((a) => <span key={a} className="text-[10px] bg-white/15 px-1.5 py-0.5 rounded">{a}</span>)}
                  </div>
                </div>
                <div className="p-5 flex-1">
                  {!st.loading && !st.brief && !st.output && !st.err && <p className="text-sm text-slate-400">Run the advisory to get a research-grade brief for this domain.</p>}
                  {st.loading && <p className="text-sm text-slate-400 animate-pulse">Researching {d.title.toLowerCase()}…</p>}
                  {st.err && <p className="text-sm text-rose-600">{st.err}</p>}
                  {(st.brief || st.output) && (
                    <div className="space-y-3">
                      {st.engine && <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full ${st.engine.startsWith("groq") ? "bg-indigo-600 text-white" : "bg-slate-200 text-slate-600"}`}>{st.engine.startsWith("groq") ? "AI-synthesised" : "deterministic"}</span>}
                      {st.brief ? (
                        <>
                          {st.brief.headline && <p className="font-black text-slate-900">{st.brief.headline}</p>}
                          {st.brief.situation && <p className="text-sm text-slate-700">{st.brief.situation}</p>}
                          {st.brief.prioritized_actions?.length > 0 && (
                            <ul className="space-y-1.5">
                              {st.brief.prioritized_actions.map((a, i) => (
                                <li key={i} className="text-sm"><span className="font-semibold">→ {a.action}</span> <span className="text-[11px] text-slate-500">({a.impact} impact · {a.effort} effort)</span></li>
                              ))}
                            </ul>
                          )}
                          {st.brief.watch_outs?.length > 0 && (
                            <div className="text-[12px] text-rose-600">⚠ {st.brief.watch_outs.join(" · ")}</div>
                          )}
                        </>
                      ) : (
                        <p className="text-sm text-slate-700">{st.output?.business_context || "Advisory generated — open the Advisor for the full audit-ready report."}</p>
                      )}
                      <a href={`/advisor?agent=${d.agent}`} className="inline-block text-[13px] font-bold text-indigo-600 hover:underline">Open full report in Advisor →</a>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-8 bg-white rounded-2xl border border-slate-200 p-5 text-sm text-slate-600">
          <span className="font-bold text-slate-800">Why "copilot", not ERP?</span> This layer doesn't replace your billing/inventory software or hold transactions — it reads your situation and advises, like a CFO/COO sitting beside you. Keep your existing tools; add the brain.
        </div>
      </main>

      <footer className="border-t border-slate-200 text-center text-xs text-slate-400 py-10 px-4">
        ERP Copilot · Indian MSME Consulting · Powered by AI · advisory only — not a transactional ERP · figures are planning estimates.
      </footer>
    </div>
  );
}
