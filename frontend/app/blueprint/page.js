"use client";
import { useEffect, useState } from "react";

/* ============================================================
   Startup Blueprint — one-click consolidated, India-aware plan.
   Reads ?idea= (or sessionStorage) and renders a polished,
   downloadable document. Mobile + desktop.
   ============================================================ */

export default function BlueprintPage() {
  const [idea, setIdea] = useState("");
  const [bp, setBp] = useState(null);
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
    if (!text) { setErr("Please enter your startup idea."); return; }
    setLoading(true); setErr(""); setBp(null);
    try {
      const r = await fetch("/api/blueprint", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea: text }),
      });
      const d = await r.json();
      if (d.error) setErr(d.error);
      else setBp(d);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white text-slate-900">
      {/* Hero */}
      <header className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white print:hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
          <a href="/auto" className="text-xs text-white/60 hover:text-white">← Home</a>
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mt-3 mb-3">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> Startup Blueprint · India-aware
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">Your startup, end to end</h1>
          <p className="text-sm text-white/70 mt-2 max-w-2xl">
            Market, model, product, GTM, financials (₹), compliance & registration, funding & government
            incentives, risk, a 90-day plan and a scaling playbook — in one document.
          </p>
          <div className="mt-5 flex flex-col sm:flex-row gap-3">
            <input value={idea} onChange={(e) => setIdea(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && generate()}
              placeholder="e.g. AI logistics SaaS for Tier-2 kirana distribution in India with GST + UPI"
              className="flex-1 rounded-xl px-4 py-3 text-sm text-slate-900 focus:outline-none" />
            <button onClick={() => generate()} disabled={loading}
              className="px-6 py-3 rounded-xl font-black bg-white text-slate-900 hover:bg-emerald-300 transition disabled:opacity-50">
              {loading ? "Generating…" : "Generate Blueprint →"}
            </button>
          </div>
          <p className="text-[11px] text-white/50 mt-2">Tip: mention India (or a city / GST / UPI) for ₹ figures and Indian compliance & funding.</p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {err && <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 text-sm mb-6">{err}</div>}
        {loading && <Skeleton />}

        {bp && (
          <div id="doc">
            {/* Doc header */}
            <div className="flex items-start justify-between gap-4 flex-wrap border-b pb-5 mb-6">
              <div>
                <div className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Startup Blueprint</div>
                <h2 className="text-2xl font-black mt-1">{bp.idea}</h2>
                <div className="flex flex-wrap gap-2 mt-3">
                  <Tag>{bp.geo === "India" ? "🇮🇳 India" : "🌐 " + bp.geo}</Tag>
                  <Tag>{bp.industry}</Tag>
                  <Tag>Methodology: {bp.methodology}</Tag>
                  <Tag>Currency {bp.currency}</Tag>
                  {bp.agents_used?.length ? <Tag>{bp.agents_used.length} agents consulted</Tag> : null}
                </div>
              </div>
              <button onClick={() => typeof window !== "undefined" && window.print()}
                className="bg-slate-900 text-white text-sm font-bold px-4 py-2 rounded-lg print:hidden hover:bg-slate-800">
                ⬇ Save / Print PDF
              </button>
            </div>

            {/* Sections */}
            <div className="space-y-6">
              {bp.sections?.map((s) => (
                <section key={s.id} className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm break-inside-avoid">
                  <h3 className="flex items-center gap-2 text-lg font-black text-slate-900 mb-2">
                    <span>{s.icon}</span>{s.title}
                  </h3>
                  {s.summary && <p className="text-sm text-slate-600 mb-3">{s.summary}</p>}
                  {s.table && (
                    <div className="overflow-x-auto mb-3">
                      <table className="w-full text-sm">
                        <thead><tr className="bg-slate-100 text-left">
                          {s.table.headers.map((h) => <th key={h} className="p-2 font-bold">{h}</th>)}
                        </tr></thead>
                        <tbody>
                          {s.table.rows.map((row, i) => (
                            <tr key={i} className="border-t">
                              {row.map((cell, j) => <td key={j} className={`p-2 ${j === 2 ? "font-bold text-emerald-700" : ""}`}>{cell}</td>)}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  {s.points?.length > 0 && (
                    <ul className="space-y-1.5">
                      {s.points.map((p, i) => (
                        <li key={i} className="flex gap-2 text-sm text-slate-700">
                          <span className="text-indigo-400 mt-0.5">▸</span><span>{p}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              ))}

              {/* 90-day plan */}
              {bp.ninety_day_plan?.length > 0 && (
                <section className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm break-inside-avoid">
                  <h3 className="flex items-center gap-2 text-lg font-black text-slate-900 mb-3">🗺️ First 90 Days</h3>
                  <div className="space-y-0">
                    {bp.ninety_day_plan.map((a, i) => (
                      <div key={i} className="flex gap-4 pb-3 last:pb-0">
                        <div className="flex flex-col items-center">
                          <span className="w-3 h-3 rounded-full bg-indigo-500" />
                          {i < bp.ninety_day_plan.length - 1 && <span className="w-0.5 flex-1 bg-slate-200 my-1" />}
                        </div>
                        <div>
                          <div className="text-sm font-semibold text-slate-800">{a.step}</div>
                          <div className="text-xs text-slate-500">{a.owner} · {a.timeline} · {a.agent}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>

            <p className="text-xs text-slate-400 mt-8 text-center">
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
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-white rounded-2xl border border-slate-200 p-6 animate-pulse">
          <div className="h-5 w-1/3 bg-slate-100 rounded" />
          <div className="h-3 w-full bg-slate-100 rounded mt-3" />
          <div className="h-3 w-5/6 bg-slate-100 rounded mt-2" />
          <div className="h-3 w-2/3 bg-slate-100 rounded mt-2" />
        </div>
      ))}
    </div>
  );
}
