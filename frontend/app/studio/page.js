"use client";
import { useEffect, useState } from "react";

/* ============================================================
   Business Studio — one idea in, a Big-3-style due-diligence report:
   deep DD, market study (TAM/SAM/SOM funnel), product lifecycle, PM
   method, tech stack, dual-currency financials (₹ & $) with a chart,
   GTM and roadmap. Infographics, stunning, PDF-able, + PM workspace.
   ============================================================ */

export default function StudioPage() {
  const [idea, setIdea] = useState("");
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    let seed = "";
    try {
      const u = new URL(window.location.href);
      seed = u.searchParams.get("idea") || sessionStorage.getItem("pmguru_pending_idea") || "";
    } catch {}
    if (seed) { setIdea(seed); generate(seed); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function generate(seedIdea) {
    const text = (seedIdea ?? idea).trim();
    if (!text) { setErr("Please enter your business idea."); return; }
    setLoading(true); setErr(""); setDoc(null);
    try {
      sessionStorage.setItem("pmguru_pending_idea", text);
      const r = await fetch("/api/studio", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea: text }),
      });
      const d = await r.json();
      if (d.error) setErr(d.error); else setDoc(d);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  const market = doc?.sections?.find((s) => s.id === "market");

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      {/* Input bar */}
      <header className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white print:hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
          <a href="/auto" className="text-xs text-white/60 hover:text-white">← Home</a>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight mt-3">Business Studio</h1>
          <p className="text-sm text-white/70 mt-1 max-w-2xl">One idea → a Big-3-style due-diligence report with market study, financials (₹ & $), product lifecycle, PM method and roadmap. Then open your PM workspace.</p>
          <div className="mt-4 flex flex-col sm:flex-row gap-3">
            <input value={idea} onChange={(e) => setIdea(e.target.value)} onKeyDown={(e) => e.key === "Enter" && generate()}
              placeholder="e.g. Bootstrapped D2C ayurvedic skincare brand in India on Amazon + own site"
              className="flex-1 rounded-xl px-4 py-3 text-sm text-slate-900 focus:outline-none" />
            <button onClick={() => generate()} disabled={loading}
              className="px-6 py-3 rounded-xl font-black bg-white text-slate-900 hover:bg-emerald-300 transition disabled:opacity-50">
              {loading ? "Researching…" : "Generate report →"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-3 sm:px-6 py-6">
        {err && <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 text-sm mb-6">{err}</div>}
        {loading && <Skeleton />}

        {doc && (
          <div id="report" className="bg-white shadow-xl rounded-2xl overflow-hidden">
            {/* ---- Big-3 cover ---- */}
            <div className="relative bg-gradient-to-br from-indigo-700 via-violet-700 to-indigo-900 text-white p-8 sm:p-12">
              <div className="text-[11px] font-bold tracking-[0.2em] text-indigo-200 uppercase">Strategic Due-Diligence Report</div>
              <h2 className="text-3xl sm:text-4xl font-black mt-3 leading-tight max-w-3xl">{doc.idea}</h2>
              <div className="flex flex-wrap gap-2 mt-5">
                <Chip>{doc.geo === "India" ? "🇮🇳 India" : "🌐 " + doc.geo}</Chip>
                <Chip>{doc.industry}</Chip>
                <Chip>PM method: {doc.methodology}</Chip>
                <Chip>Currency {doc.geo === "India" ? "₹ & $" : "$"}</Chip>
              </div>
              <div className="absolute top-6 right-6 print:hidden flex gap-2">
                <a href={`/erp?idea=${encodeURIComponent(doc.idea)}`} className="px-3 py-2 rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs font-bold">🗂️ Workspace</a>
                <button onClick={() => window.print()} className="px-3 py-2 rounded-lg bg-white text-slate-900 text-xs font-bold hover:bg-emerald-300">⬇ PDF</button>
              </div>
            </div>

            {/* ---- At-a-glance KPI strip ---- */}
            {market?.metrics && (
              <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-slate-100 border-b border-slate-100">
                {market.metrics.map((m, i) => (
                  <div key={i} className="p-5 text-center">
                    <div className="text-[11px] font-bold text-indigo-600 uppercase tracking-wide">{m.label}</div>
                    <div className="text-2xl font-black text-slate-900 mt-1">{m.value}</div>
                    <div className="text-[10px] text-slate-400 mt-1">{m.note}</div>
                  </div>
                ))}
              </div>
            )}

            {/* ---- Exhibits ---- */}
            <div className="p-5 sm:p-10 space-y-10">
              {doc.sections.map((s, idx) => (
                <section key={s.id} className="break-inside-avoid">
                  <div className="flex items-baseline gap-3 border-b-2 border-slate-900 pb-2 mb-4">
                    <span className="text-[11px] font-black text-indigo-600 tracking-widest uppercase">Exhibit {idx + 1}</span>
                    <h3 className="text-xl font-black text-slate-900">{s.icon} {s.title}</h3>
                  </div>
                  {s.summary && <p className="text-sm text-slate-600 leading-relaxed mb-4">{s.summary}</p>}

                  {/* Market funnel infographic */}
                  {s.funnel && <Funnel funnel={s.funnel} />}

                  {/* Financial bar chart infographic */}
                  {s.chart && <BarChart chart={s.chart} />}

                  {/* Table */}
                  {s.table && (
                    <div className="overflow-x-auto mb-3">
                      <table className="w-full text-sm border border-slate-200">
                        <thead><tr className="bg-slate-900 text-white text-left">
                          {s.table.headers.map((h) => <th key={h} className="p-2.5 font-bold whitespace-nowrap">{h}</th>)}
                        </tr></thead>
                        <tbody>
                          {s.table.rows.map((row, i) => (
                            <tr key={i} className={`align-top ${i % 2 ? "bg-slate-50" : ""}`}>
                              {row.map((cell, j) => <td key={j} className={`p-2.5 border-t border-slate-100 ${j === 0 ? "font-semibold" : ""}`}>{cell}</td>)}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Points */}
                  {s.points?.length > 0 && (
                    <ul className="space-y-2">
                      {s.points.map((p, i) => (
                        <li key={i} className="flex gap-2.5 text-sm text-slate-700 leading-relaxed">
                          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0" /><span>{p}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              ))}
            </div>

            {/* ---- Workspace handoff ---- */}
            <a href={`/erp?idea=${encodeURIComponent(doc.idea)}`}
              className="block bg-gradient-to-r from-violet-600 to-indigo-600 text-white p-6 text-center hover:opacity-90 transition print:hidden">
              <div className="text-lg font-black">🗂️ Open your PM Workspace Copilot →</div>
              <div className="text-sm text-white/85 mt-1">Preloaded methodology, tech stack, backlog, sprints, risks, compliance, KPIs & SOPs — plus how all 20 AI agents help this project</div>
            </a>

            <p className="text-[11px] text-slate-400 px-6 py-5 text-center border-t border-slate-100">
              PMGuru · research-grade, India-aware, citation-backed · figures are planning estimates — verify statutory & financial items with a CA/CS before acting.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

/* ---- Infographics ---- */
function Funnel({ funnel }) {
  const max = Math.max(...funnel.map((f) => f.n || 0), 1);
  const colors = ["from-indigo-600 to-violet-500", "from-violet-600 to-fuchsia-500", "from-emerald-600 to-teal-500"];
  return (
    <div className="space-y-2 mb-4">
      {funnel.map((f, i) => {
        const pct = Math.max(14, Math.round(((f.n || 0) / max) * 100));
        return (
          <div key={i} className="flex items-center gap-3">
            <span className="w-12 text-xs font-black text-slate-500 shrink-0">{f.label}</span>
            <div className="flex-1 bg-slate-100 rounded-lg overflow-hidden">
              <div className={`h-10 rounded-lg bg-gradient-to-r ${colors[i % 3]} flex items-center px-3 text-white text-sm font-black`} style={{ width: pct + "%" }}>
                {f.value}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function BarChart({ chart }) {
  const max = Math.max(...chart.values.map((v) => Math.abs(v) || 0), 1);
  return (
    <div className="border border-slate-200 rounded-xl p-4 mb-3">
      <div className="flex items-end gap-4 h-44">
        {chart.values.map((v, i) => {
          const h = Math.max(8, Math.round((Math.abs(v) / max) * 100));
          return (
            <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
              <div className="text-[10px] font-bold text-slate-600 mb-1 text-center leading-tight">{chart.display?.[i]}</div>
              <div className="w-full max-w-[90px] rounded-t-lg bg-gradient-to-t from-emerald-600 to-teal-400" style={{ height: h + "%" }} />
            </div>
          );
        })}
      </div>
      <div className="flex gap-4 mt-2">
        {chart.labels.map((l, i) => <div key={i} className="flex-1 text-center text-xs font-bold text-slate-500">{l}</div>)}
      </div>
    </div>
  );
}

function Chip({ children }) {
  return <span className="text-[11px] font-bold bg-white/15 text-white px-2.5 py-1 rounded-full">{children}</span>;
}

function Skeleton() {
  return (
    <div className="bg-white rounded-2xl shadow-xl p-8 animate-pulse">
      <div className="h-8 w-2/3 bg-slate-100 rounded" />
      <div className="grid grid-cols-4 gap-3 mt-6">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-16 bg-slate-100 rounded" />)}</div>
      <div className="h-3 w-full bg-slate-100 rounded mt-6" />
      <div className="h-3 w-5/6 bg-slate-100 rounded mt-2" />
    </div>
  );
}
