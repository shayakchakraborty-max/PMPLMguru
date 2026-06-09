"use client";

/* Government Schemes module — personalised Indian government scheme finder.
   Describe the business (+ a few flags) -> /api/schemes -> ranked, fit-scored
   scheme cards grouped by category. Deterministic backend, no LLM needed. */

import { useState } from "react";
import { DEMO_BUSINESSES } from "../lib/demos";

// Export-oriented sectors get is_export pre-set so the demo shows export schemes.
const EXPORT_KEYS = new Set(["manufacturing", "food_processing", "agro_business", "pharma", "textile", "export_business", "automotive", "electronics"]);
const SIZE_BY_TURNOVER = (cr) => (parseFloat(cr) <= 10 ? "micro" : parseFloat(cr) <= 50 ? "small" : "medium");
const DEMOS = DEMO_BUSINESSES.map((d) => ({
  key: d.key, icon: d.icon, label: d.label,
  body: { description: d.description, size: SIZE_BY_TURNOVER(d.turnover_cr), is_export: EXPORT_KEYS.has(d.key) },
}));

const FIT = { High: "bg-emerald-100 text-emerald-700 border-emerald-200", Medium: "bg-amber-100 text-amber-700 border-amber-200", Explore: "bg-slate-100 text-slate-600 border-slate-200" };
const CAT_ICON = { credit: "🏦", subsidy: "💸", equity: "📊", tax: "🧾", export: "🌏", quality: "🏅", market: "🛒", sector: "🏭", state: "📋" };

export default function SchemesPage() {
  const [desc, setDesc] = useState("");
  const [size, setSize] = useState("small");
  const [state, setState] = useState("");
  const [flags, setFlags] = useState({ is_export: false, is_dpiit: false, women_owned: false, sc_st_owned: false });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState(null);

  function tf(k) { setFlags((f) => ({ ...f, [k]: !f[k] })); }

  async function run(custom) {
    const body = custom || { description: desc, size, state, ...flags };
    if (!body.description?.trim()) { setErr("Describe your business first."); return; }
    setErr(""); setLoading(true); setRes(null);
    try {
      const r = await fetch("/api/schemes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const d = await r.json();
      if (d.error) setErr(d.error); else setRes(d);
      setTimeout(() => document.getElementById("res")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
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
            <a href="/advisor" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Advisors</a>
          </div>
        </div>
      </nav>

      {/* Input */}
      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> Government Schemes · personalised to your business
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">Find the government money you're leaving on the table.</h1>
          <p className="text-slate-300 mt-4 max-w-2xl">CGTMSE, MUDRA, PMEGP, Startup India, RoDTEP, ZED, PMFME, state subsidies and more — matched and ranked to your sector, size and stage.</p>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 sm:p-5 mt-7 space-y-3">
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={2}
              placeholder="e.g. textile garment manufacturer in Surat that exports to the EU…"
              className="w-full bg-white/10 border border-white/15 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            <div className="grid grid-cols-2 gap-3">
              <select value={size} onChange={(e) => setSize(e.target.value)}
                className="bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-indigo-400 [&>option]:text-slate-900">
                <option value="micro">Micro</option><option value="small">Small</option><option value="medium">Medium</option>
              </select>
              <input value={state} onChange={(e) => setState(e.target.value)} placeholder="State (optional)"
                className="bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              {[["is_export", "We export"], ["is_dpiit", "DPIIT-recognised"], ["women_owned", "Women-owned"], ["sc_st_owned", "SC/ST-owned"]].map(([k, label]) => (
                <button key={k} onClick={() => tf(k)}
                  className={`px-3 py-1.5 rounded-lg border font-semibold transition ${flags[k] ? "bg-indigo-500 border-indigo-400 text-white" : "bg-white/10 border-white/15 text-slate-300 hover:bg-white/20"}`}>
                  {flags[k] ? "✓ " : ""}{label}
                </button>
              ))}
            </div>
            <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center">
              <button onClick={() => run()} disabled={loading}
                className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl font-black hover:opacity-90 transition disabled:opacity-50">
                {loading ? "Matching schemes…" : "Find my schemes →"}
              </button>
              <div className="flex flex-wrap gap-1.5 text-xs">
                {DEMOS.map((d) => (
                  <button key={d.key} onClick={() => run(d.body)} disabled={loading}
                    className="px-2.5 py-1.5 bg-white/10 border border-white/15 rounded-lg hover:bg-white/20 hover:border-indigo-400 transition font-semibold flex items-center gap-1">
                    <span>{d.icon}</span>{d.label}</button>
                ))}
              </div>
            </div>
            {err && <p className="text-rose-300 text-sm">{err}</p>}
          </div>
        </div>
      </header>

      <main id="res" className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        {loading && <div className="text-center text-slate-500 py-20 animate-pulse">Matching you against the scheme registry…</div>}
        {!loading && !res && (
          <div className="text-center text-slate-400 py-16"><div className="text-5xl mb-3">🏛️</div><p>Describe your business above to see your personalised schemes.</p></div>
        )}

        {res && (
          <div className="space-y-6">
            {/* summary */}
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className="bg-emerald-600 text-white font-black px-3 py-1.5 rounded-full">{res.high_fit_count} high-fit</span>
              <span className="bg-white border border-slate-200 px-3 py-1.5 rounded-full font-semibold">{res.total} schemes matched</span>
              <span className="text-slate-500 text-xs">
                {res.profile?.sector?.replace("_", " ")} · {res.profile?.size} · {res.profile?.stage}{res.profile?.is_export ? " · exporter" : ""}{res.profile?.is_dpiit ? " · DPIIT" : ""}
              </span>
            </div>

            {/* top picks */}
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wide text-slate-400 mb-3">★ Top picks for you</h2>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {(res.top_picks || []).map((s) => <SchemeCard key={s.key} s={s} highlight />)}
              </div>
            </div>

            {/* by category */}
            {(res.by_category || []).map((cat) => (
              <div key={cat.key}>
                <h2 className="text-sm font-black mt-6 mb-3">{CAT_ICON[cat.key] || "📄"} {cat.label} <span className="text-slate-400 font-normal">({cat.schemes.length})</span></h2>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {cat.schemes.map((s) => <SchemeCard key={s.key} s={s} />)}
                </div>
              </div>
            ))}

            <p className="text-xs text-slate-400 border-t border-slate-200 pt-4">{res.disclaimer}</p>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 text-center text-xs text-slate-400 py-10 px-4">
        Government Schemes · Indian MSME Consulting · Powered by AI · scheme terms are indicative — verify on the official portal before applying.
      </footer>
    </div>
  );
}

function SchemeCard({ s, highlight }) {
  return (
    <div className={`bg-white rounded-2xl border p-5 flex flex-col ${highlight ? "border-indigo-200 ring-1 ring-indigo-100" : "border-slate-200"}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="font-black text-[15px] leading-tight">{s.name}</div>
        <span className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded border font-bold ${FIT[s.fit] || FIT.Explore}`}>{s.fit}</span>
      </div>
      <div className="text-[11px] text-slate-400 mt-0.5">{s.authority}</div>
      <p className="text-sm text-slate-600 mt-2">{s.one_liner}</p>
      <div className="mt-2 text-[13px] text-slate-800 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">
        <span className="font-bold">Benefit:</span> {s.benefit}
      </div>
      {s.fit_reasons?.length > 0 && (
        <ul className="mt-2.5 space-y-1">
          {s.fit_reasons.map((r, i) => <li key={i} className="text-[12px] text-slate-500 flex gap-1.5"><span className="text-indigo-500">✓</span><span>{r}</span></li>)}
        </ul>
      )}
      <details className="mt-2 text-[12px]">
        <summary className="cursor-pointer text-slate-500 font-semibold">Eligibility & how to apply</summary>
        <div className="mt-1.5 space-y-1.5 text-slate-600">
          <p><span className="font-bold">Who:</span> {s.eligibility}</p>
          <p><span className="font-bold">How:</span> {s.how_to_apply}</p>
        </div>
      </details>
      <a href={s.portal} target="_blank" rel="noopener noreferrer"
        className="mt-3 text-[13px] font-bold text-indigo-600 hover:underline">Official portal →</a>
    </div>
  );
}
