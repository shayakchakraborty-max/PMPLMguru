"use client";

/* CEO Office — the single executive command center.
   One business description -> /api/consult -> an executive view assembling
   Business Health, Cash Position, Key Risks, Growth Opportunities, Strategic
   Priorities and AI Recommendations. Reuses the working consult brain. */

import { useState } from "react";
import { DEMO_BUSINESSES } from "../lib/demos";

const STAGES = ["Discover", "Diagnose", "Analyze", "Recommend", "Roadmap", "Execute", "Monitor"];

// One-click sample per business type — for the demo version.
const DEMOS = DEMO_BUSINESSES.map((d) => ({
  key: d.key, icon: d.icon, label: d.label,
  body: { description: d.description, top_challenges: d.top_challenges, turnover_cr: d.turnover_cr, city_tier: d.city_tier },
}));

const SEV = { Critical: "bg-red-100 text-red-700 border-red-200", High: "bg-orange-100 text-orange-700 border-orange-200", Medium: "bg-amber-100 text-amber-700 border-amber-200", Low: "bg-slate-100 text-slate-600 border-slate-200" };
const PRI = { High: "bg-rose-600", Medium: "bg-amber-500", Low: "bg-slate-400" };

export default function CeoOffice() {
  const [desc, setDesc] = useState("");
  const [turnover, setTurnover] = useState("");
  const [challenges, setChallenges] = useState("");
  const [tier, setTier] = useState("Tier-2");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [eng, setEng] = useState(null);
  const [need, setNeed] = useState("");
  const [routing, setRouting] = useState(false);
  const [route, setRoute] = useState(null);

  async function routeNeed() {
    if (!need.trim()) return;
    setRouting(true); setRoute(null);
    try {
      const r = await fetch("/api/catalog", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: need }) });
      setRoute(await r.json());
    } catch (e) { setRoute({ error: e.message }); }
    finally { setRouting(false); }
  }

  async function run(custom) {
    const body = custom || { description: desc, top_challenges: challenges, turnover_cr: turnover, city_tier: tier };
    if (!body.description?.trim()) { setErr("Please describe your business first."); return; }
    setErr(""); setLoading(true); setEng(null);
    try {
      const r = await fetch("/api/consult", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: "existing", ...body }) });
      const d = await r.json();
      if (d.error) setErr(d.error);
      else setEng(d);
      setTimeout(() => document.getElementById("cmd")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  const sc = eng?.scorecard;
  const vas = eng?.value_at_stake;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Nav */}
      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <a href="/auto" className="font-black tracking-tight text-sm sm:text-base">Indian MSME Consulting <span className="text-indigo-600">· Powered by AI</span></a>
          <div className="flex items-center gap-1 text-sm">
            <a href="/catalog" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Services</a>
            <a href="/playbooks" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Engagement</a>
            <a href="/advisor" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Advisors</a>
          </div>
        </div>
      </nav>

      {/* Hero / input */}
      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> CEO Office · Executive Command Center
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">Your whole business, on one screen.</h1>
          <p className="text-slate-300 mt-4 max-w-2xl">Describe your business once. Your AI consulting team returns a CEO-level command center — health, cash, risks, opportunities and the moves that matter.</p>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 sm:p-5 mt-7 space-y-3">
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={2}
              placeholder="e.g. 8-store kirana retail chain in Pune, GST registered, 22 staff…"
              className="w-full bg-white/10 border border-white/15 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <input value={turnover} onChange={(e) => setTurnover(e.target.value)} placeholder="Turnover (₹ cr)"
                className="bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
              <select value={tier} onChange={(e) => setTier(e.target.value)}
                className="bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-indigo-400 [&>option]:text-slate-900">
                <option>Tier-1</option><option>Tier-2</option><option>Tier-3</option>
              </select>
              <input value={challenges} onChange={(e) => setChallenges(e.target.value)} placeholder="Top challenges"
                className="col-span-2 sm:col-span-1 bg-white/10 border border-white/15 rounded-xl px-3 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            </div>
            <button onClick={() => run()} disabled={loading}
              className="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl font-black hover:opacity-90 transition disabled:opacity-50">
              {loading ? "Convening your team…" : "Open my CEO Office →"}
            </button>
            {err && <p className="text-rose-300 text-sm">{err}</p>}
            <div className="pt-1">
              <div className="text-[11px] uppercase tracking-wide text-slate-400 mb-2">Or try a sample business — every sector</div>
              <div className="flex flex-wrap gap-1.5">
                {DEMOS.map((d) => (
                  <button key={d.key} onClick={() => run(d.body)} disabled={loading}
                    className="px-2.5 py-1.5 bg-white/10 border border-white/15 rounded-lg hover:bg-white/20 hover:border-indigo-400 transition text-xs font-semibold flex items-center gap-1">
                    <span>{d.icon}</span>{d.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Command center */}
      <main id="cmd" className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        {loading && <div className="text-center text-slate-500 py-20 animate-pulse">Your Managing Partner is assembling the engagement…</div>}

        {!loading && !eng && (
          <div className="py-10">
            <div className="text-center text-slate-400 mb-8">
              <div className="text-5xl mb-3">🏛️</div>
              <p>Run an engagement above to populate your command center — or jump straight to the right specialist below.</p>
            </div>

            {/* Find-my-advisor router (wired to the consulting catalog) */}
            <div className="max-w-2xl mx-auto bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
              <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-2">Have a specific problem? Route it to the right advisor</div>
              <div className="flex flex-col sm:flex-row gap-2">
                <input value={need} onChange={(e) => setNeed(e.target.value)} onKeyDown={(e) => e.key === "Enter" && routeNeed()}
                  placeholder="e.g. receivables are stretched and collections are a mess…"
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-400" />
                <button onClick={routeNeed} disabled={routing}
                  className="px-5 py-3 rounded-xl bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-500 disabled:opacity-50">
                  {routing ? "Routing…" : "Find advisor →"}
                </button>
              </div>
              {route && route.matched && (
                <div className="mt-3 bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-sm">
                  <span className="text-slate-500">Routed to</span> <b>{route.tower.icon} {route.tower.name}</b> → <b>{route.service_line}</b>
                  {route.workflow && <> → <span className="text-indigo-600">{route.workflow}</span></>}
                  <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                    <span className="text-[12px]">{route.tower.ai_advisor}</span>
                    {route.agent_live && <a href={`/advisor?agent=${route.agent}`} className="ml-auto px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-bold text-[12px] hover:bg-indigo-500">Open advisor →</a>}
                  </div>
                </div>
              )}
              {route && !route.matched && !route.error && <div className="mt-3 text-amber-600 text-sm">Try naming the function (finance, receivables, procurement, tax, risk, marketing, HR…).</div>}
              {route?.error && <div className="mt-3 text-rose-600 text-sm">{route.error}</div>}
              <a href="/catalog" className="inline-block mt-3 text-[13px] font-semibold text-indigo-600 hover:underline">Or browse all 16 consulting towers · 90+ service lines →</a>
            </div>
          </div>
        )}

        {eng && (
          <div className="space-y-5">
            {/* lifecycle ribbon */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] font-bold">
              {STAGES.map((s, i) => (
                <div key={s} className="flex items-center gap-1.5 shrink-0">
                  <span className={`px-2.5 py-1 rounded-full ${i < 6 ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-400"}`}>{i < 6 ? "✓ " : ""}{s}</span>
                  {i < STAGES.length - 1 && <span className="text-slate-300">→</span>}
                </div>
              ))}
            </div>

            {/* context line */}
            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <span className="font-bold text-slate-700">{eng.sector_name}</span>
              <span>· engagement {eng.engagement_id}</span>
              <span>· {eng.engine?.startsWith("groq") ? "AI-enhanced" : "deterministic"}</span>
            </div>

            {/* TOP ROW: Health + Cash */}
            <div className="grid lg:grid-cols-3 gap-5">
              {/* Business Health */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 lg:col-span-2">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs font-bold uppercase tracking-wide text-slate-400">Business Health</div>
                    <div className="flex items-end gap-3 mt-1">
                      <div className="text-5xl font-black">{sc?.grade}</div>
                      <div className="text-slate-500 mb-1.5 text-sm">{sc?.overall}/100 overall</div>
                    </div>
                  </div>
                  <GradeRing overall={sc?.overall || 0} grade={sc?.grade} />
                </div>
                <div className="grid sm:grid-cols-2 gap-x-6 gap-y-3 mt-5">
                  {(sc?.scores || []).map((s) => (
                    <div key={s.key}>
                      <div className="flex justify-between text-[13px] mb-1">
                        <span className="font-semibold">{s.icon} {s.label}</span>
                        <span className="text-slate-500">{s.score}</span>
                      </div>
                      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${s.score >= 60 ? "bg-emerald-500" : s.score >= 45 ? "bg-amber-500" : "bg-rose-500"}`} style={{ width: `${s.score}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cash Position */}
              <div className="bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-2xl p-6">
                <div className="text-xs font-bold uppercase tracking-wide opacity-80">Cash Position · Value at Stake</div>
                <div className="mt-3 space-y-3">
                  <div>
                    <div className="text-3xl font-black">{vas?.cash_release_label || "—"}</div>
                    <div className="text-xs opacity-80">one-off cash you can release</div>
                  </div>
                  <div>
                    <div className="text-2xl font-black">{vas?.annual_uplift_label || "—"}</div>
                    <div className="text-xs opacity-80">annual profit uplift on the table</div>
                  </div>
                </div>
                <div className="mt-4 space-y-2 border-t border-white/20 pt-3">
                  {(vas?.levers || []).slice(0, 3).map((l, i) => (
                    <div key={i} className="text-[12px]">
                      <span className="font-bold">{l.value_label}</span> — {l.lever}
                    </div>
                  ))}
                  {(!vas?.levers || !vas.levers.length) && <div className="text-[12px] opacity-80">Add turnover / margin / DSO figures for a quantified case.</div>}
                </div>
              </div>
            </div>

            {/* SECOND ROW: Priorities + Risks + Opportunities */}
            <div className="grid lg:grid-cols-3 gap-5">
              <Panel title="Strategic Priorities" icon="🎯">
                <ol className="space-y-3">
                  {(eng.tailored_recommendations || []).slice(0, 5).map((r, i) => (
                    <li key={i} className="text-sm">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] text-white px-1.5 py-0.5 rounded font-bold ${PRI[r.priority] || PRI.Low}`}>{r.priority || "Med"}</span>
                        <span className="font-bold">{r.title}</span>
                      </div>
                      {r.why && <p className="text-xs text-slate-500 mt-1">{r.why}</p>}
                    </li>
                  ))}
                </ol>
              </Panel>

              <Panel title="Key Risks" icon="🛡️">
                <ul className="space-y-2.5">
                  {(eng.risks || []).slice(0, 5).map((r, i) => (
                    <li key={i} className="text-sm">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-bold mr-1.5 ${SEV[r.severity] || SEV.Low}`}>{r.severity || "—"}</span>
                      <span>{r.risk}</span>
                    </li>
                  ))}
                </ul>
              </Panel>

              <Panel title="Growth Opportunities" icon="🚀">
                <ul className="space-y-2.5">
                  {(eng.opportunities || []).slice(0, 5).map((o, i) => (
                    <li key={i} className="text-sm flex gap-2"><span className="text-emerald-500">▲</span><span>{typeof o === "string" ? o : o.title || JSON.stringify(o)}</span></li>
                  ))}
                </ul>
              </Panel>
            </div>

            {/* AI Recommendations / diagnosis */}
            <div className="grid lg:grid-cols-3 gap-5">
              <div className="lg:col-span-2">
                <Panel title="AI Recommendations" icon="🧠">
                  <p className="text-sm text-slate-700 leading-relaxed">{eng.diagnosis}</p>
                  {(eng.quick_wins || []).length > 0 && (
                    <div className="mt-4">
                      <div className="text-xs font-bold uppercase tracking-wide text-slate-400 mb-2">Quick wins</div>
                      <ul className="space-y-1.5">
                        {eng.quick_wins.map((q, i) => <li key={i} className="text-sm flex gap-2"><span className="text-indigo-500">⚡</span><span>{q}</span></li>)}
                      </ul>
                    </div>
                  )}
                </Panel>
              </div>
              <Panel title="Top KPIs to Track" icon="📊">
                <ul className="space-y-2.5">
                  {(eng.kpis || []).slice(0, 5).map((k, i) => (
                    <li key={i} className="text-sm"><span className="font-bold">{k.kpi}</span> <span className="text-slate-500">→ {k.target}</span></li>
                  ))}
                </ul>
              </Panel>
            </div>

            {/* CTA strip */}
            <div className="bg-slate-900 text-white rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <div className="font-black text-lg">Go deeper on this engagement</div>
                <div className="text-sm text-slate-300">Full DD report, SWOT, 12-month roadmap, board pack and AI PMO.</div>
              </div>
              <div className="flex gap-2 shrink-0 flex-wrap">
                <a href="/playbooks" className="px-5 py-3 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl font-bold hover:opacity-90 transition">Open full engagement →</a>
                <a href="/catalog" className="px-5 py-3 bg-white/10 border border-white/20 rounded-xl font-bold hover:bg-white/20 transition">All services</a>
                <a href="/advisor" className="px-5 py-3 bg-white/10 border border-white/20 rounded-xl font-bold hover:bg-white/20 transition">Advisors</a>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 text-center text-xs text-slate-400 py-10 px-4">
        CEO Office · Indian MSME Consulting · Powered by AI · figures are planning estimates — verify statutory & financial items with a CA / CS before acting.
      </footer>
    </div>
  );
}

function Panel({ title, icon, children }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <div className="text-xs font-bold uppercase tracking-wide text-slate-400 mb-3">{icon} {title}</div>
      {children}
    </div>
  );
}

function GradeRing({ overall, grade }) {
  const r = 26, c = 2 * Math.PI * r, off = c - (overall / 100) * c;
  const col = overall >= 60 ? "#10b981" : overall >= 45 ? "#f59e0b" : "#f43f5e";
  return (
    <svg width="72" height="72" viewBox="0 0 72 72" className="shrink-0">
      <circle cx="36" cy="36" r={r} fill="none" stroke="#f1f5f9" strokeWidth="8" />
      <circle cx="36" cy="36" r={r} fill="none" stroke={col} strokeWidth="8" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={off} transform="rotate(-90 36 36)" />
      <text x="36" y="42" textAnchor="middle" fontSize="20" fontWeight="800" fill={col}>{grade}</text>
    </svg>
  );
}
