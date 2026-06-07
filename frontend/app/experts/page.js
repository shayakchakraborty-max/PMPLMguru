"use client";

/* Industry Expert Agents — pick a top India MSME business type (or describe one)
   and get an expert brief: market size, export solutions, regulatory & financial
   compliance, growth, risks and benchmarks. Backend /api/experts. */

import { useEffect, useState } from "react";

const POT = { "Very High": "bg-emerald-600", High: "bg-emerald-500", "Medium–High": "bg-teal-500", Medium: "bg-amber-500", "Low–Medium": "bg-amber-400", Low: "bg-slate-400", Core: "bg-indigo-600", Enabler: "bg-sky-500", Growing: "bg-teal-500" };

export default function ExpertsPage() {
  const [types, setTypes] = useState([]);
  const [desc, setDesc] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [brief, setBrief] = useState(null);

  useEffect(() => {
    fetch("/api/experts").then((r) => r.json()).then((d) => { if (d.types) setTypes(d.types); }).catch(() => {});
  }, []);

  async function run(body) {
    setErr(""); setLoading(true); setBrief(null);
    try {
      const r = await fetch("/api/experts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const d = await r.json();
      if (d.error) setErr(d.error); else setBrief(d);
      setTimeout(() => document.getElementById("brief")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <a href="/auto" className="font-black tracking-tight text-sm sm:text-base">Indian MSME Consulting <span className="text-indigo-600">· Powered by AI</span></a>
          <div className="flex items-center gap-1 text-sm">
            <a href="/ceo" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">CEO Office</a>
            <a href="/schemes" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Schemes</a>
          </div>
        </div>
      </nav>

      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 sm:py-14">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> Industry Expert Agents · India's top MSME sectors
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">Talk to an industry expert.</h1>
          <p className="text-slate-300 mt-3 max-w-2xl">Pick your business type for an expert brief: <b>market size</b>, <b>export solutions</b>, <b>regulatory</b> & <b>financial compliance</b>, growth and risks — India-specific.</p>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 sm:p-5 mt-6 flex flex-col sm:flex-row gap-2">
            <input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Or describe your business — e.g. spice export house in Kochi"
              className="flex-1 bg-white/10 border border-white/15 rounded-xl px-4 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            <button onClick={() => desc.trim() ? run({ description: desc }) : setErr("Type a business or pick one below.")} disabled={loading}
              className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl font-black hover:opacity-90 transition disabled:opacity-50">
              {loading ? "Briefing…" : "Get expert brief →"}
            </button>
          </div>
          {err && <p className="text-rose-300 text-sm mt-2">{err}</p>}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Type grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {types.map((t) => (
            <button key={t.key} onClick={() => run({ key: t.key })}
              className="bg-white rounded-xl border border-slate-200 p-4 text-left hover:border-indigo-400 hover:shadow-md transition">
              <div className="text-2xl">{t.icon}</div>
              <div className="font-black text-sm mt-1.5 leading-tight">{t.name}</div>
              <div className="mt-2"><span className={`text-[10px] text-white px-1.5 py-0.5 rounded ${POT[t.export_potential] || "bg-slate-400"}`}>Export: {t.export_potential}</span></div>
            </button>
          ))}
        </div>

        <div id="brief" className="mt-8">
          {loading && <div className="text-center text-slate-500 py-16 animate-pulse">Your industry expert is preparing the brief…</div>}
          {brief && <Brief b={brief} />}
        </div>
      </main>

      <footer className="border-t border-slate-200 text-center text-xs text-slate-400 py-10 px-4">
        Industry Expert Agents · Indian MSME Consulting · Powered by AI · market figures indicative — verify with latest IBEF/ministry data; confirm compliance with a CA/CS.
      </footer>
    </div>
  );
}

function Brief({ b }) {
  const ms = b.market_size || {};
  const ex = b.export_solutions || {};
  const fin = b.financial_compliance || {};
  const mi = b.market_intelligence;
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-6">
        <div className="text-3xl">{b.icon}</div>
        <h2 className="text-2xl font-black mt-1">{b.name}</h2>
        {b.one_liner && <p className="text-slate-300 text-sm mt-1">{b.one_liner}</p>}
      </div>

      <div className="p-5 sm:p-7 space-y-7">
        {/* Market size */}
        <Sec icon="📈" title="Market Size (India)">
          <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
            <p className="font-bold text-slate-900">{ms.india_size}</p>
            <div className="flex flex-wrap gap-2 mt-2 text-xs">
              {ms.cagr && <span className="bg-white border border-slate-200 px-2 py-1 rounded-full font-semibold">CAGR {ms.cagr}</span>}
              {ms.segments && <span className="bg-white border border-slate-200 px-2 py-1 rounded-full">{ms.segments}</span>}
            </div>
            {ms.drivers?.length > 0 && (
              <ul className="grid sm:grid-cols-2 gap-1.5 mt-3">
                {ms.drivers.map((d, i) => <li key={i} className="text-sm flex gap-2"><span className="text-indigo-500">▲</span>{d}</li>)}
              </ul>
            )}
          </div>
          {mi?.narrative && (
            <div className="mt-3 text-sm text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3">
              <span className="text-[10px] font-bold uppercase tracking-wide text-indigo-600">{mi.engine?.startsWith("groq") ? "AI market read" : "Market read"}</span>
              <p className="mt-1">{mi.narrative}</p>
            </div>
          )}
        </Sec>

        {/* Export */}
        <Sec icon="🌏" title="Export Solutions">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className={`text-xs text-white px-2 py-1 rounded-full font-bold ${POT[ex.potential] || "bg-slate-400"}`}>Export potential: {ex.potential}</span>
            {ex.target_markets?.map((m) => <span key={m} className="text-xs bg-slate-100 px-2 py-1 rounded-full">{m}</span>)}
          </div>
          <p className="text-sm text-slate-600">{ex.note}</p>
          {ex.schemes?.length > 0 && (
            <div className="mt-3 space-y-2">
              {ex.schemes.map((s, i) => (
                <div key={i} className="border border-emerald-100 bg-emerald-50 rounded-lg p-3 text-sm">
                  <a href={s.portal} target="_blank" rel="noopener noreferrer" className="font-bold text-emerald-800 hover:underline">{s.name} ↗</a>
                  <div className="text-slate-600 text-xs mt-0.5">{s.benefit}</div>
                </div>
              ))}
            </div>
          )}
        </Sec>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Regulatory */}
          <Sec icon="⚖️" title="Regulatory Compliance">
            <div className="space-y-2">
              {b.regulatory_compliance?.map((r, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-[9px] mt-0.5 bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded font-bold">{r.tier || "•"}</span>
                  <div>
                    {r.url ? <a href={r.url} target="_blank" rel="noopener noreferrer" className="font-semibold hover:underline">{r.title}</a> : <span className="font-semibold">{r.title}</span>}
                    {r.authority && <span className="text-xs text-slate-400"> · {r.authority}</span>}
                  </div>
                </div>
              ))}
            </div>
          </Sec>

          {/* Financial */}
          <Sec icon="🧾" title="Financial Compliance">
            <ul className="space-y-1.5 text-sm">
              {Object.entries(fin).map(([k, v]) => v && (
                <li key={k} className="flex gap-2"><span className="text-indigo-500">•</span><span>{v}</span></li>
              ))}
            </ul>
          </Sec>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Growth */}
          {b.growth_opportunities?.length > 0 && (
            <Sec icon="🚀" title="Growth Opportunities">
              <ul className="space-y-1.5 text-sm">{b.growth_opportunities.map((g, i) => <li key={i} className="flex gap-2"><span className="text-emerald-500">▲</span>{g}</li>)}</ul>
            </Sec>
          )}
          {/* Risks */}
          {b.common_risks?.length > 0 && (
            <Sec icon="🛡️" title="Common Risks">
              <ul className="space-y-1.5 text-sm">{b.common_risks.map((r, i) => <li key={i} className="flex gap-2"><span className="text-rose-500">⚠</span>{r}</li>)}</ul>
            </Sec>
          )}
        </div>

        {/* Benchmarks */}
        {b.benchmarks && (
          <Sec icon="📊" title="Benchmarks">
            <div className="flex flex-wrap gap-2 text-sm">
              <span className="bg-slate-100 px-3 py-1.5 rounded-lg"><b>Gross margin:</b> {b.benchmarks.gross_margin}</span>
              <span className="bg-slate-100 px-3 py-1.5 rounded-lg"><b>Net margin:</b> {b.benchmarks.net_margin}</span>
            </div>
            {b.benchmarks.unit_economics?.length > 0 && (
              <ul className="mt-2 space-y-1 text-sm text-slate-600">{b.benchmarks.unit_economics.map((u, i) => <li key={i}>• {u}</li>)}</ul>
            )}
          </Sec>
        )}

        <div className="flex flex-wrap gap-2 pt-2">
          <a href={b.playbook_link} className="px-5 py-2.5 bg-slate-900 text-white rounded-xl font-bold text-sm hover:bg-slate-800 transition">Full sector playbook →</a>
          <a href="/ceo" className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 transition">Run a CEO engagement →</a>
        </div>
        <p className="text-xs text-slate-400 border-t border-slate-200 pt-3">{b.disclaimer}</p>
      </div>
    </div>
  );
}

function Sec({ icon, title, children }) {
  return (
    <div>
      <h3 className="flex items-center gap-2 text-sm font-black text-slate-800 uppercase tracking-wide mb-3"><span>{icon}</span>{title}</h3>
      {children}
    </div>
  );
}
