"use client";
import { useEffect, useState } from "react";

/* ============================================================
   Situation Simulator — describe a real business situation; the
   engine matches it against 100+/type scale-wise scenarios, runs the
   recommended AI agent crew, and returns an end-to-end grow-in-India +
   scale-internationally plan. Free-LLM synthesis when keys are set.
   ============================================================ */

const EXAMPLES = [
  "New food company dealing with dried garlic, turmeric, chilli, tomato, beetroot — grow in India then export internationally",
  "Bootstrapped D2C skincare brand scaling from one city to pan-India",
  "Pharma distributor going from ₹5 cr to ₹50 cr across 3 states",
  "Engineering MSME wanting to start exporting auto components to the Gulf",
];

export default function SimulatePage() {
  const [situation, setSituation] = useState("");
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    let seed = "";
    try {
      const u = new URL(window.location.href);
      seed = u.searchParams.get("situation") || u.searchParams.get("idea") || "";
    } catch {}
    if (seed) { setSituation(seed); run(seed); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function run(seed) {
    const text = (seed ?? situation).trim();
    if (!text) { setErr("Please describe your situation."); return; }
    setLoading(true); setErr(""); setRes(null);
    try {
      const r = await fetch("/api/simulate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ situation: text }),
      });
      const d = await r.json();
      if (d.error) setErr(d.error); else setRes(d);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white print:hidden">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-9">
          <a href="/auto" className="text-xs text-white/60 hover:text-white">← Home</a>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight mt-3">Situation Simulator</h1>
          <p className="text-sm text-white/70 mt-1 max-w-2xl">Describe your situation. The engine matches 100+ scale-wise scenarios for your business type and runs the right AI agent crew — end to end, India to international.</p>
          <textarea value={situation} onChange={(e) => setSituation(e.target.value)} rows={3}
            placeholder="e.g. New food company dealing with dried garlic, turmeric, chilli — grow in India then export internationally"
            className="w-full mt-4 rounded-xl px-4 py-3 text-sm text-slate-900 focus:outline-none" />
          <div className="flex flex-wrap items-center gap-2 mt-3">
            <button onClick={() => run()} disabled={loading}
              className="px-6 py-3 rounded-xl font-black bg-white text-slate-900 hover:bg-emerald-300 transition disabled:opacity-50">
              {loading ? "Simulating…" : "Simulate →"}
            </button>
            {EXAMPLES.map((ex, i) => (
              <button key={i} onClick={() => { setSituation(ex); run(ex); }} disabled={loading}
                className="text-[11px] bg-white/10 hover:bg-white/20 text-white/90 rounded-full px-3 py-1.5">{ex.slice(0, 42)}…</button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6">
        {err && <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 text-sm mb-6">{err}</div>}
        {loading && <div className="text-center text-slate-400 py-16 text-sm animate-pulse">Matching scenarios and running the agent crew…</div>}

        {res && (
          <div className="space-y-5">
            {/* Header */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <div className="flex flex-wrap gap-2 mb-3">
                <Tag>{res.business_type?.replace(/_/g, " ")}</Tag>
                <Tag>{res.stage}</Tag>
                <Tag>{res.library_size_for_type} scenarios for this type</Tag>
                <Tag>{res.total_situations}+ total simulated</Tag>
                <Tag>{res.llm_available ? `AI synthesis: ${res.llm_provider || "free-LLM"}` : "deterministic"}</Tag>
              </div>
              <p className="text-sm text-slate-800 leading-relaxed">{res.exec_summary}</p>
            </div>

            {/* Crew */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <h3 className="font-black text-slate-900 mb-3">🤝 Agent crew on this situation</h3>
              <div className="flex flex-wrap gap-2">
                {res.crew?.map((c) => (
                  <span key={c.agent} className="inline-flex items-center gap-1.5 text-sm font-bold bg-indigo-50 text-indigo-700 border border-indigo-100 rounded-full px-3 py-1.5">
                    {c.icon} {c.name}
                  </span>
                ))}
              </div>
            </div>

            {/* Two-column plan */}
            <div className="grid md:grid-cols-2 gap-5">
              <PlanCard title="🇮🇳 Grow in India" color="emerald" items={res.plan?.india_growth} />
              <PlanCard title="🌐 Scale internationally" color="indigo" items={res.plan?.international_scaleup} />
            </div>

            {/* Matched scenarios */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <h3 className="font-black text-slate-900 mb-3">🎯 Matched scenarios (from {res.library_size_for_type} for {res.business_type?.replace(/_/g, " ")})</h3>
              <ul className="space-y-1.5">
                {res.matched_situations?.map((s, i) => (
                  <li key={i} className="text-sm text-slate-600 flex gap-2"><span className="text-indigo-400">▸</span><span>{s}</span></li>
                ))}
              </ul>
            </div>

            {/* Deeper dive */}
            <a href={`/studio?idea=${encodeURIComponent(res.situation)}`}
              className="block text-center rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white p-5 font-black hover:opacity-90 transition">
              📑 Get the full research-grade report (TAM/SAM/SOM, ₹ & $ financials, PLM) →
            </a>
          </div>
        )}
      </main>
    </div>
  );
}

function PlanCard({ title, color, items }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
      <h3 className={`font-black text-${color}-700 mb-3`}>{title}</h3>
      <ul className="space-y-2">
        {(items || []).map((p, i) => (
          <li key={i} className="text-sm text-slate-700 flex gap-2"><span className={`mt-1.5 w-1.5 h-1.5 rounded-full bg-${color}-500 shrink-0`} /><span>{p}</span></li>
        ))}
        {(!items || !items.length) && <li className="text-sm text-slate-400">—</li>}
      </ul>
    </div>
  );
}

function Tag({ children }) {
  return <span className="text-[11px] font-bold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full">{children}</span>;
}
