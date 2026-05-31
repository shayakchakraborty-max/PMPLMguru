"use client";
import { useEffect, useState } from "react";

/* ============================================================
   Business Studio — one idea in, a complete research-grade report:
   deep due diligence, market study (TAM/SAM/SOM), product lifecycle,
   PM method, tech stack, financials, GTM, roadmap. Stunning + PDF +
   one-click into the preloaded PM workspace copilot.
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
      if (d.error) setErr(d.error);
      else setDoc(d);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white text-slate-900">
      {/* Hero / input */}
      <header className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white print:hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
          <a href="/auto" className="text-xs text-white/60 hover:text-white">← Home</a>
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mt-3 mb-3">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> Business Studio · research-grade · India-aware
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight">Your idea → a complete plan</h1>
          <p className="text-sm sm:text-lg text-white/70 mt-3 max-w-2xl">
            One input. Deep due diligence, market study (TAM/SAM/SOM), product lifecycle, the right PM
            method, tech stack, ₹ financials, GTM and roadmap — then open your preloaded PM workspace.
          </p>
          <div className="mt-5 flex flex-col sm:flex-row gap-3">
            <input value={idea} onChange={(e) => setIdea(e.target.value)} onKeyDown={(e) => e.key === "Enter" && generate()}
              placeholder="e.g. AI logistics SaaS for Tier-2 kirana distribution in India with GST + UPI"
              className="flex-1 rounded-xl px-4 py-3 text-sm text-slate-900 focus:outline-none" />
            <button onClick={() => generate()} disabled={loading}
              className="px-6 py-3 rounded-xl font-black bg-white text-slate-900 hover:bg-emerald-300 transition disabled:opacity-50">
              {loading ? "Researching…" : "Generate →"}
            </button>
          </div>
          <p className="text-[11px] text-white/50 mt-2">Tip: mention India (or a city / GST / UPI) for ₹ figures and Indian compliance & funding.</p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {err && <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 text-sm mb-6">{err}</div>}
        {loading && <Skeleton />}

        {doc && (
          <div id="doc">
            {/* Doc header */}
            <div className="flex items-start justify-between gap-4 flex-wrap border-b pb-5 mb-6">
              <div>
                <div className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Research-grade business report</div>
                <h2 className="text-2xl font-black mt-1">{doc.idea}</h2>
                <div className="flex flex-wrap gap-2 mt-3">
                  <Tag>{doc.geo === "India" ? "🇮🇳 India" : "🌐 " + doc.geo}</Tag>
                  <Tag>{doc.industry}</Tag>
                  <Tag>PM: {doc.methodology}</Tag>
                  <Tag>Currency {doc.currency}</Tag>
                </div>
              </div>
              <div className="flex gap-2 print:hidden">
                <a href={`/erp?idea=${encodeURIComponent(doc.idea)}`}
                  className="px-4 py-2 rounded-lg bg-violet-600 text-white text-sm font-bold hover:bg-violet-700">🗂️ Open PM Workspace</a>
                <button onClick={() => typeof window !== "undefined" && window.print()}
                  className="px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-bold hover:bg-slate-800">⬇ Download PDF</button>
              </div>
            </div>

            {/* Sections */}
            <div className="space-y-6">
              {doc.sections?.map((s) => (
                <section key={s.id} className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm break-inside-avoid">
                  <h3 className="flex items-center gap-2 text-lg font-black text-slate-900 mb-2">{s.icon} {s.title}</h3>
                  {s.summary && <p className="text-sm text-slate-600 mb-3">{s.summary}</p>}

                  {/* TAM/SAM/SOM (or any) metric tiles */}
                  {s.metrics?.length > 0 && (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-3">
                      {s.metrics.map((m, i) => (
                        <div key={i} className="bg-gradient-to-br from-indigo-50 to-white border border-indigo-100 rounded-xl p-4 text-center">
                          <div className="text-[11px] font-bold text-indigo-600 uppercase">{m.label}</div>
                          <div className="text-2xl font-black text-slate-900 mt-1">{m.value}</div>
                          <div className="text-[10px] text-slate-400 mt-1">{m.note}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Table */}
                  {s.table && (
                    <div className="overflow-x-auto mb-3">
                      <table className="w-full text-sm">
                        <thead><tr className="bg-slate-100 text-left">
                          {s.table.headers.map((h) => <th key={h} className="p-2 font-bold whitespace-nowrap">{h}</th>)}
                        </tr></thead>
                        <tbody>
                          {s.table.rows.map((row, i) => (
                            <tr key={i} className="border-t align-top">
                              {row.map((cell, j) => <td key={j} className={`p-2 ${j === 0 ? "font-semibold" : ""}`}>{cell}</td>)}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Points */}
                  {s.points?.length > 0 && (
                    <ul className="space-y-1.5">
                      {s.points.map((p, i) => (
                        <li key={i} className="flex gap-2 text-sm text-slate-700"><span className="text-indigo-400 mt-0.5">▸</span><span>{p}</span></li>
                      ))}
                    </ul>
                  )}
                </section>
              ))}
            </div>

            {/* Workspace handoff */}
            <a href={`/erp?idea=${encodeURIComponent(doc.idea)}`}
              className="mt-6 block text-center rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white p-6 hover:opacity-90 transition print:hidden">
              <div className="text-lg font-black">🗂️ Open your PM Workspace Copilot →</div>
              <div className="text-sm text-white/80 mt-1">Preloaded modules (methodology, tech stack, backlog, sprints, risks, compliance, KPIs, SOPs) + how all 20 AI agents help this project</div>
            </a>

            <p className="text-xs text-slate-400 mt-6 text-center">
              Generated by PMGuru · India-aware, citation-backed · verify statutory items with a CA/CS before acting.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

function Tag({ children }) {
  return <span className="text-[11px] font-bold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full">{children}</span>;
}

function Skeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="bg-white rounded-2xl border border-slate-200 p-6 animate-pulse">
          <div className="h-5 w-1/3 bg-slate-100 rounded" />
          <div className="h-3 w-full bg-slate-100 rounded mt-3" />
          <div className="h-3 w-5/6 bg-slate-100 rounded mt-2" />
        </div>
      ))}
    </div>
  );
}
