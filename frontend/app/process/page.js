"use client";

/* Process & Value-Stream Copilot — the consulting-firm engagement, auto-filled.
   Describe a business -> /api/process -> an Engagement Team (Partner..Consultants)
   that maps the end-to-end process as SCOR swimlanes, builds a value-stream map in
   the blueprint format (Step | Cycle | Wait | First-pass yield | Main waste | AI
   action), and hands you a bottleneck -> AI-action plan. Deterministic backend
   (+ optional Groq partner brief). Mirrors docs/STRATEGY.md. */

import { useState } from "react";
import { DEMO_BUSINESSES } from "../lib/demos";

const DEMOS = DEMO_BUSINESSES.map((d) => ({ key: d.key, icon: d.icon, label: d.label, description: d.description }));

const LANE = {
  Plan: { c: "indigo", dot: "bg-indigo-500", chip: "bg-indigo-50 text-indigo-700 border-indigo-200", bar: "bg-indigo-500" },
  Source: { c: "amber", dot: "bg-amber-500", chip: "bg-amber-50 text-amber-700 border-amber-200", bar: "bg-amber-500" },
  Make: { c: "violet", dot: "bg-violet-500", chip: "bg-violet-50 text-violet-700 border-violet-200", bar: "bg-violet-500" },
  Deliver: { c: "sky", dot: "bg-sky-500", chip: "bg-sky-50 text-sky-700 border-sky-200", bar: "bg-sky-500" },
  Service: { c: "emerald", dot: "bg-emerald-500", chip: "bg-emerald-50 text-emerald-700 border-emerald-200", bar: "bg-emerald-500" },
};
const TONE = {
  emerald: "from-emerald-500 to-emerald-600", amber: "from-amber-500 to-amber-600",
  rose: "from-rose-500 to-rose-600", indigo: "from-indigo-500 to-indigo-600",
};
const EFFORT = { Low: "bg-emerald-100 text-emerald-700", Medium: "bg-amber-100 text-amber-700", High: "bg-rose-100 text-rose-700" };
const ROLE_RING = ["ring-indigo-300", "ring-violet-300", "ring-sky-300", "ring-amber-300", "ring-emerald-300"];

export default function ProcessPage() {
  const [desc, setDesc] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState(null);
  const [open, setOpen] = useState({}); // expanded stage ids

  async function run(custom) {
    const description = (custom ?? desc).trim();
    if (!description) { setErr("Describe your business first — the copilot fills in the rest."); return; }
    if (custom) setDesc(custom);
    setErr(""); setLoading(true); setRes(null); setOpen({});
    try {
      const r = await fetch("/api/process", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description, deep: true }),
      });
      const d = await r.json();
      if (d.error) setErr(d.error); else setRes(d);
      setTimeout(() => document.getElementById("res")?.scrollIntoView({ behavior: "smooth", block: "start" }), 90);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  const vsm = res?.value_stream_map;
  const totals = vsm?.totals;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <style>{`@media print { nav, .no-print { display:none !important } .print-block { break-inside: avoid } }`}</style>

      {/* Nav */}
      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200 no-print">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <a href="/auto" className="font-black tracking-tight text-sm sm:text-base">Indian MSME Consulting <span className="text-indigo-600">· Powered by AI</span></a>
          <div className="flex items-center gap-1 text-sm">
            <a href="/ceo" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">CEO Office</a>
            <a href="/advisor" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Advisors</a>
            <a href="/schemes" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Schemes</a>
          </div>
        </div>
      </nav>

      {/* Hero / copilot input */}
      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> Process &amp; Value-Stream Copilot · a full engagement team, auto-filled
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            Map your business end-to-end.<br /><span className="text-indigo-300">See exactly where time &amp; cash leak.</span>
          </h1>
          <p className="text-slate-300 mt-4 max-w-2xl">
            Describe your business once. A consulting-firm team — Engagement Partner, Director, Manager,
            Senior Consultant and Consultants — builds your process map, a value-stream map (cycle time,
            waiting, first-pass yield, waste) and an AI-driven fix plan. Like the big firms, productised.
          </p>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 sm:p-5 mt-7 space-y-3">
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={2}
              placeholder="e.g. 8-store kirana grocery chain in Pune, GST registered, 22 staff…"
              className="w-full bg-white/10 border border-white/15 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            <div className="flex flex-wrap items-center gap-2">
              <button onClick={() => run()} disabled={loading}
                className="px-5 py-2.5 rounded-xl bg-indigo-500 hover:bg-indigo-400 font-bold text-sm disabled:opacity-50 transition">
                {loading ? "Mapping your value stream…" : "Map my business →"}
              </button>
              <span className="text-[11px] text-slate-400">Deterministic + AI · sub-second · India-aware (₹, GST/Udyam)</span>
            </div>
            {err && <div className="text-rose-300 text-sm font-semibold">{err}</div>}
            <div className="pt-1">
              <div className="text-[11px] uppercase tracking-wide text-slate-400 font-bold mb-2">Or try one click ↓</div>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {DEMOS.map((d) => (
                  <button key={d.key} onClick={() => run(d.description)} disabled={loading}
                    className="shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/10 text-xs font-semibold disabled:opacity-50 transition">
                    <span>{d.icon}</span>{d.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </header>

      {loading && (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-16 text-center text-slate-500">
          <div className="inline-block w-8 h-8 border-3 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-3" />
          <p className="font-semibold">The engagement team is mapping your process & value stream…</p>
        </div>
      )}

      {res && (
        <main id="res" className="max-w-7xl mx-auto px-4 sm:px-6 py-10 space-y-12">
          {/* Title + print */}
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-3">
                <span className="text-3xl">{res.icon}</span>
                <h2 className="text-2xl sm:text-3xl font-black tracking-tight">{res.business}</h2>
              </div>
              <p className="text-slate-500 mt-1 text-sm">{res.summary?.headline}</p>
            </div>
            <button onClick={() => window.print()} className="no-print px-4 py-2 rounded-xl border border-slate-300 text-sm font-semibold hover:bg-white">Print / Save PDF</button>
          </div>

          {/* Partner brief */}
          {res.partner_brief?.narrative && (
            <div className="print-block bg-gradient-to-br from-indigo-600 to-violet-700 text-white rounded-2xl p-6 shadow-lg">
              <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wide text-indigo-100 mb-2">
                <span>🤝</span> Engagement Partner brief
                <span className="ml-auto bg-white/15 px-2 py-0.5 rounded-full normal-case">{res.partner_brief.engine}</span>
              </div>
              <p className="text-lg leading-relaxed font-medium">“{res.partner_brief.narrative}”</p>
            </div>
          )}

          {/* Headline metrics */}
          <section className="print-block">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {res.summary?.metrics?.map((m, i) => (
                <div key={i} className={`rounded-2xl p-4 text-white bg-gradient-to-br ${TONE[m.tone] || TONE.indigo} shadow`}>
                  <div className="text-3xl font-black leading-none">{m.value}<span className="text-base font-bold opacity-80 ml-1">{m.unit}</span></div>
                  <div className="text-xs font-semibold opacity-90 mt-2">{m.label}</div>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-slate-400 mt-2">Biggest source of waste detected: <b className="text-slate-600">{res.summary?.biggest_waste}</b>. Figures are illustrative sector planning estimates — validate on a site walk-through.</p>
          </section>

          {/* Engagement team */}
          <section className="print-block">
            <SectionTitle icon="👔" title="Your engagement team" sub="The big-firm pyramid, rendered as an AI copilot — each role owns part of the work and tells you what they see." />
            <div className="grid md:grid-cols-5 gap-3">
              {res.engagement_team?.map((m, i) => (
                <div key={i} className={`bg-white rounded-2xl border border-slate-200 p-4 ring-1 ${ROLE_RING[i] || "ring-slate-200"} flex flex-col`}>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{m.avatar}</span>
                    <span className="text-[10px] font-black text-slate-400">L{m.level}</span>
                  </div>
                  <div className="font-black text-sm mt-2 leading-tight">{m.role}</div>
                  <div className="text-[11px] text-indigo-600 font-semibold">{m.title}</div>
                  <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">{m.mandate}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {m.owns?.map((o, j) => <span key={j} className="text-[9px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-semibold">{o}</span>)}
                  </div>
                  <div className="mt-auto pt-3">
                    <div className="bg-slate-50 border border-slate-100 rounded-lg p-2 text-[11px] text-slate-600 leading-relaxed">
                      <span className="font-bold text-slate-700">💬 {m.role.split(" ").pop()}:</span> {m.copilot_note}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Process map — swimlane flow */}
          <section className="print-block">
            <SectionTitle icon="🗺️" title="Process map" sub="The end-to-end value chain as SCOR swimlanes (Plan → Source → Make → Deliver → Service). Red = bottleneck. Click any stage for sub-steps." />
            <div className="flex flex-wrap items-center gap-3 mb-3 text-[11px] font-semibold">
              {Object.keys(LANE).map((l) => (
                <span key={l} className="inline-flex items-center gap-1.5"><span className={`w-2.5 h-2.5 rounded-full ${LANE[l].dot}`} />{l}</span>
              ))}
              <span className="inline-flex items-center gap-1.5 ml-2"><span className="w-2.5 h-2.5 rounded-full bg-rose-500 ring-2 ring-rose-200" />Bottleneck</span>
            </div>
            <div className="overflow-x-auto pb-2">
              <div className="flex items-stretch gap-1 min-w-max">
                {res.process_map?.stages?.map((s, i) => {
                  const L = LANE[s.lane] || LANE.Make;
                  const isOpen = open[s.id];
                  return (
                    <div key={s.id} className="flex items-stretch">
                      <button onClick={() => setOpen((o) => ({ ...o, [s.id]: !o[s.id] }))}
                        className={`text-left w-52 rounded-xl border p-3 bg-white hover:shadow-md transition ${s.is_bottleneck ? "border-rose-300 ring-2 ring-rose-100" : "border-slate-200"}`}>
                        <div className="flex items-center justify-between">
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${L.chip}`}>{s.lane}</span>
                          <span className="text-[10px] font-black text-slate-300">#{i + 1}</span>
                        </div>
                        <div className="font-bold text-xs mt-2 leading-snug">{s.short}</div>
                        <div className="text-[10px] text-slate-400 mt-1">👤 {s.owner_role}</div>
                        {s.is_bottleneck && <div className="text-[10px] font-bold text-rose-600 mt-1">⚠ Bottleneck</div>}
                        <div className="text-[10px] text-indigo-500 font-semibold mt-1">{isOpen ? "− hide" : "+ sub-steps"}</div>
                        {isOpen && (
                          <div className="mt-2 space-y-1 border-t border-slate-100 pt-2">
                            {s.substeps?.map((ss, j) => <div key={j} className="text-[10px] text-slate-600 leading-snug">• {ss}</div>)}
                            {s.bottleneck && (
                              <div className="mt-1.5 bg-rose-50 border border-rose-100 rounded p-1.5">
                                <div className="text-[10px] font-bold text-rose-700">{s.bottleneck.title}</div>
                                <div className="text-[9px] text-rose-600 mt-0.5">Root cause: {s.bottleneck.root_cause}</div>
                              </div>
                            )}
                          </div>
                        )}
                      </button>
                      {i < res.process_map.stages.length - 1 && <div className="flex items-center px-0.5 text-slate-300 font-black">→</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          {/* Value stream map */}
          <section className="print-block">
            <SectionTitle icon="📊" title="Value-stream map" sub="Where the lead time actually goes. Green = value-add processing; red = waiting. The gap is your working-capital release." />
            {/* lead-time ribbon */}
            {totals && (
              <div className="bg-white rounded-2xl border border-slate-200 p-4 mb-4">
                <div className="flex items-center justify-between text-xs font-bold mb-1.5">
                  <span className="text-emerald-600">Value-add {totals.value_add_time_days}d</span>
                  <span className="text-slate-400">Process-cycle efficiency {totals.process_cycle_efficiency_pct}%</span>
                  <span className="text-rose-600">Waiting {totals.wait_time_days}d</span>
                </div>
                <div className="h-4 rounded-full overflow-hidden flex bg-slate-100">
                  <div className="bg-emerald-500" style={{ width: `${totals.process_cycle_efficiency_pct}%` }} />
                  <div className="bg-rose-400" style={{ width: `${100 - totals.process_cycle_efficiency_pct}%` }} />
                </div>
                <div className="text-[11px] text-slate-400 mt-1.5">Total order-to-cash lead time ≈ <b className="text-slate-600">{totals.total_lead_time_days} days</b> · rolled throughput yield {totals.rolled_throughput_yield_pct}%</div>
              </div>
            )}
            <div className="overflow-x-auto bg-white rounded-2xl border border-slate-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2.5 font-bold">Step</th>
                    <th className="px-3 py-2.5 font-bold">Timeline (cycle vs wait)</th>
                    <th className="px-3 py-2.5 font-bold text-right">Cycle</th>
                    <th className="px-3 py-2.5 font-bold text-right">Wait</th>
                    <th className="px-3 py-2.5 font-bold text-right">FPY</th>
                    <th className="px-3 py-2.5 font-bold">Main waste</th>
                    <th className="px-3 py-2.5 font-bold">AI-generated action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {vsm?.rows?.map((r, i) => {
                    const span = (r.cycle_time_days + r.wait_time_days) || 1;
                    return (
                      <tr key={i} className={r.is_bottleneck ? "bg-rose-50/40" : ""}>
                        <td className="px-3 py-2.5 font-semibold align-top">
                          {r.step}
                          <span className={`ml-1.5 text-[9px] px-1 py-0.5 rounded border ${(LANE[r.lane] || LANE.Make).chip}`}>{r.lane}</span>
                          {r.is_bottleneck && <span className="ml-1 text-[9px] text-rose-600 font-bold">⚠</span>}
                        </td>
                        <td className="px-3 py-2.5 align-middle min-w-[140px]">
                          <div className="h-2.5 rounded-full overflow-hidden flex bg-slate-100">
                            <div className="bg-emerald-500" style={{ width: `${(r.cycle_time_days / span) * 100}%` }} />
                            <div className="bg-rose-400" style={{ width: `${(r.wait_time_days / span) * 100}%` }} />
                          </div>
                        </td>
                        <td className="px-3 py-2.5 text-right tabular-nums text-emerald-700">{r.cycle_time_days}d</td>
                        <td className="px-3 py-2.5 text-right tabular-nums text-rose-600">{r.wait_time_days}d</td>
                        <td className={`px-3 py-2.5 text-right tabular-nums font-semibold ${r.first_pass_yield_pct < 85 ? "text-rose-600" : "text-slate-700"}`}>{r.first_pass_yield_pct}%</td>
                        <td className="px-3 py-2.5"><span className="text-[11px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-semibold">{r.main_waste}</span></td>
                        <td className="px-3 py-2.5 text-[12px] text-slate-600 max-w-xs">{r.ai_action}{r.ai_agent && <span className="ml-1 text-[10px] text-indigo-500 font-semibold">[{r.ai_agent}]</span>}</td>
                      </tr>
                    );
                  })}
                </tbody>
                {totals && (
                  <tfoot>
                    <tr className="bg-slate-900 text-white font-bold text-[13px]">
                      <td className="px-3 py-2.5">TOTAL</td>
                      <td className="px-3 py-2.5 text-[11px] font-semibold text-slate-300">PCE {totals.process_cycle_efficiency_pct}% · RTY {totals.rolled_throughput_yield_pct}%</td>
                      <td className="px-3 py-2.5 text-right tabular-nums text-emerald-300">{totals.value_add_time_days}d</td>
                      <td className="px-3 py-2.5 text-right tabular-nums text-rose-300">{totals.wait_time_days}d</td>
                      <td className="px-3 py-2.5 text-right tabular-nums" colSpan={3}>Lead time {totals.total_lead_time_days}d</td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </section>

          {/* Action plan */}
          {res.action_plan?.length > 0 && (
            <section className="print-block">
              <SectionTitle icon="🎯" title="Bottleneck → AI action plan" sub="What the Engagement Manager puts on the 90-day roadmap, owner-assigned and trackable." />
              <div className="grid md:grid-cols-2 gap-3">
                {res.action_plan.map((a, i) => (
                  <div key={i} className="bg-white rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-bold ${(LANE[a.lane] || LANE.Make).chip}`}>{a.lane}</span>
                      <span className="font-bold text-sm">{a.bottleneck}</span>
                    </div>
                    <div className="text-[11px] text-slate-500 mb-2"><b>Root cause:</b> {a.root_cause}</div>
                    <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-2.5 text-[12px] text-indigo-900 leading-relaxed">
                      <b>AI fix:</b> {a.fix}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 mt-2.5 text-[10px]">
                      {a.agent && <span className="bg-violet-100 text-violet-700 px-1.5 py-0.5 rounded font-semibold">🤖 {a.agent}</span>}
                      <span className={`px-1.5 py-0.5 rounded font-semibold ${EFFORT[a.effort] || EFFORT.Medium}`}>Effort: {a.effort}</span>
                      <span className={`px-1.5 py-0.5 rounded font-semibold ${EFFORT[a.impact_rating] || EFFORT.High}`}>Impact: {a.impact_rating}</span>
                      <span className="ml-auto text-slate-400 font-semibold">👤 {a.owner}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* KPIs */}
          {res.kpis?.length > 0 && (
            <section className="print-block">
              <SectionTitle icon="📈" title="KPIs to watch" sub="The metrics this value stream lives or dies by." />
              <div className="overflow-x-auto bg-white rounded-2xl border border-slate-200">
                <table className="w-full text-sm">
                  <thead><tr className="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2.5 font-bold">KPI</th><th className="px-3 py-2.5 font-bold">Definition</th>
                    <th className="px-3 py-2.5 font-bold text-emerald-600">Healthy</th><th className="px-3 py-2.5 font-bold text-amber-600">Watch</th><th className="px-3 py-2.5 font-bold text-rose-600">Critical</th>
                  </tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {res.kpis.map((k, i) => (
                      <tr key={i}>
                        <td className="px-3 py-2.5 font-semibold">{k.kpi}</td>
                        <td className="px-3 py-2.5 text-[12px] text-slate-500">{k.definition}</td>
                        <td className="px-3 py-2.5 text-[12px] text-emerald-700">{k.healthy}</td>
                        <td className="px-3 py-2.5 text-[12px] text-amber-700">{k.watch}</td>
                        <td className="px-3 py-2.5 text-[12px] text-rose-700">{k.critical}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          <p className="text-[11px] text-slate-400 border-t border-slate-200 pt-4">{res.disclaimer}</p>

          {/* Cross-links */}
          <div className="no-print flex flex-wrap gap-3 pt-2">
            <a href="/ceo" className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800">Open CEO Office →</a>
            <a href="/advisor" className="px-4 py-2 rounded-xl border border-slate-300 text-sm font-semibold hover:bg-white">Run a deep agent advisory →</a>
            <a href="/schemes" className="px-4 py-2 rounded-xl border border-slate-300 text-sm font-semibold hover:bg-white">Find government schemes →</a>
          </div>
        </main>
      )}

      {!res && !loading && (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 grid md:grid-cols-3 gap-4 no-print">
          {[
            ["🗺️", "Process map", "Your value chain as SCOR swimlanes with sub-steps, owners and bottleneck flags."],
            ["📊", "Value-stream map", "Cycle time, waiting, first-pass yield and waste per step — with PCE & lead-time totals."],
            ["👔", "Engagement team", "Partner → Director → Manager → Sr Consultant → Consultants, each with a copilot view."],
          ].map(([i, t, d]) => (
            <div key={t} className="bg-white rounded-2xl border border-slate-200 p-5">
              <div className="text-3xl">{i}</div>
              <div className="font-black mt-2">{t}</div>
              <p className="text-sm text-slate-500 mt-1">{d}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SectionTitle({ icon, title, sub }) {
  return (
    <div className="mb-4">
      <h3 className="text-xl font-black tracking-tight flex items-center gap-2"><span>{icon}</span>{title}</h3>
      {sub && <p className="text-sm text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}
