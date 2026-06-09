"use client";

/* Monitoring / Business Command Center — Stage 7 "Monitor".
   Enter this period's KPIs (current vs last period) + a profile -> /api/monitor
   returns trend tiles, a statutory compliance countdown and proactive alerts. */

import { useState } from "react";
import { DEMO_BUSINESSES } from "../lib/demos";

// Subset surfaced in the form (the backend accepts all METRICS).
const FIELDS = [
  { key: "revenue", label: "Monthly Revenue (₹ lakh)" },
  { key: "gross_margin_pct", label: "Gross Margin %" },
  { key: "net_margin_pct", label: "Net Margin %" },
  { key: "dso_days", label: "Receivable Days (DSO)" },
  { key: "collection_rate_pct", label: "Collection Rate %" },
  { key: "cash_runway_months", label: "Cash Runway (months)" },
  { key: "dead_stock_pct", label: "Dead / Slow Stock %" },
  { key: "rev_per_employee_lakh", label: "Revenue / Employee (₹L/yr)" },
];

// One sample per business type (description + KPI metrics) for the demo version.
const DEMOS = DEMO_BUSINESSES.map((d) => ({ key: d.key, icon: d.icon, label: d.label, description: d.description, metrics: d.metrics }));

const SEV = { Critical: "bg-red-100 text-red-700 border-red-200", High: "bg-orange-100 text-orange-700 border-orange-200", Medium: "bg-amber-100 text-amber-700 border-amber-200", Low: "bg-slate-100 text-slate-600 border-slate-200" };
const STATUS_DOT = { good: "bg-emerald-500", ok: "bg-slate-300", watch: "bg-amber-500", critical: "bg-rose-500" };
const URG = { overdue: "bg-red-100 text-red-700", due_soon: "bg-orange-100 text-orange-700", upcoming: "bg-amber-50 text-amber-700", scheduled: "bg-slate-100 text-slate-500" };
const WATCH_BG = { red: "from-rose-600 to-red-700", amber: "from-amber-500 to-orange-600", emerald: "from-emerald-600 to-teal-700" };

export default function MonitorPage() {
  const [desc, setDesc] = useState("");
  const [vals, setVals] = useState({}); // {key: {current, previous}}
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [cc, setCc] = useState(null);

  function setV(k, which, v) { setVals((s) => ({ ...s, [k]: { ...(s[k] || {}), [which]: v } })); }

  async function run(custom) {
    const body = custom || { description: desc, metrics: vals };
    const hasAny = custom || Object.values(vals).some((m) => m && (m.current ?? "") !== "");
    if (!hasAny) { setErr("Enter at least one KPI (current value)."); return; }
    setErr(""); setLoading(true); setCc(null);
    try {
      const r = await fetch("/api/monitor", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const d = await r.json();
      if (d.error) setErr(d.error); else setCc(d);
      setTimeout(() => document.getElementById("cc")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  function loadDemo(d) {
    setDesc(d.description); setVals(d.metrics); run({ description: d.description, metrics: d.metrics });
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

      {/* Input */}
      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-14">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> Stage 7 · Business Command Center
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">Monitor the business. Get ahead of trouble.</h1>
          <p className="text-slate-300 mt-3 max-w-2xl">Enter this period's numbers (and last period's, to see the trend). Your AI team watches KPIs, statutory deadlines and momentum — and tells you what to act on now.</p>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 sm:p-5 mt-6 space-y-3">
            <input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Business (e.g. kirana retail chain in Pune) — for the compliance calendar"
              className="w-full bg-white/10 border border-white/15 rounded-xl px-4 py-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            <div className="grid sm:grid-cols-2 gap-x-4 gap-y-2">
              <div className="hidden sm:grid grid-cols-[1fr_auto_auto] gap-2 text-[10px] uppercase tracking-wide text-slate-400 px-1">
                <span>Metric</span><span className="w-20 text-center">This period</span><span className="w-20 text-center">Last period</span>
              </div>
              <div className="hidden sm:grid grid-cols-[1fr_auto_auto] gap-2 text-[10px] uppercase tracking-wide text-slate-400 px-1">
                <span>Metric</span><span className="w-20 text-center">This period</span><span className="w-20 text-center">Last period</span>
              </div>
              {FIELDS.map((f) => (
                <div key={f.key} className="grid grid-cols-[1fr_auto_auto] gap-2 items-center">
                  <label className="text-[12px] text-slate-300">{f.label}</label>
                  <input inputMode="decimal" value={vals[f.key]?.current ?? ""} onChange={(e) => setV(f.key, "current", e.target.value)}
                    className="w-20 bg-white/10 border border-white/15 rounded-lg px-2 py-1.5 text-sm text-center focus:outline-none focus:border-indigo-400" />
                  <input inputMode="decimal" value={vals[f.key]?.previous ?? ""} onChange={(e) => setV(f.key, "previous", e.target.value)} placeholder="—"
                    className="w-20 bg-white/10 border border-white/15 rounded-lg px-2 py-1.5 text-sm text-center placeholder:text-slate-500 focus:outline-none focus:border-indigo-400" />
                </div>
              ))}
            </div>
            <button onClick={() => run()} disabled={loading}
              className="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl font-black hover:opacity-90 transition disabled:opacity-50">
              {loading ? "Scanning…" : "Open command center →"}
            </button>
            {err && <p className="text-rose-300 text-sm">{err}</p>}
            <div className="pt-1">
              <div className="text-[11px] uppercase tracking-wide text-slate-400 mb-2">Or load a sample business — every sector (pre-filled KPIs)</div>
              <div className="flex flex-wrap gap-1.5">
                {DEMOS.map((d) => (
                  <button key={d.key} onClick={() => loadDemo(d)} disabled={loading}
                    className="px-2.5 py-1.5 bg-white/10 border border-white/15 rounded-lg hover:bg-white/20 hover:border-indigo-400 transition text-xs font-semibold flex items-center gap-1">
                    <span>{d.icon}</span>{d.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main id="cc" className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        {loading && <div className="text-center text-slate-500 py-20 animate-pulse">Scanning KPIs, trends and the compliance calendar…</div>}
        {!loading && !cc && <div className="text-center text-slate-400 py-16"><div className="text-5xl mb-3">📡</div><p>Enter your numbers to open the command center.</p></div>}

        {cc && (
          <div className="space-y-6">
            {/* watch banner */}
            <div className={`rounded-2xl p-5 text-white bg-gradient-to-r ${WATCH_BG[cc.watch_level?.color] || WATCH_BG.amber} flex flex-wrap items-center justify-between gap-3`}>
              <div>
                <div className="text-xs font-bold uppercase tracking-wide opacity-80">Watch level · as of {cc.today}</div>
                <div className="text-2xl font-black">{cc.watch_level?.level}</div>
              </div>
              <div className="text-right">
                <div className="text-3xl font-black">{cc.alert_count}</div>
                <div className="text-xs opacity-80">proactive alerts</div>
              </div>
            </div>

            {/* KPI tiles */}
            {cc.kpis?.length > 0 && (
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wide text-slate-400 mb-3">KPI Trends</h2>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                  {cc.kpis.map((k) => <KpiTile key={k.key} k={k} />)}
                </div>
              </div>
            )}

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Alerts */}
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wide text-slate-400 mb-3">⚠️ Proactive Recommendations</h2>
                <div className="space-y-2.5">
                  {cc.alerts?.length ? cc.alerts.map((a, i) => (
                    <div key={i} className="bg-white rounded-xl border border-slate-200 p-4">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-bold ${SEV[a.severity] || SEV.Low}`}>{a.severity}</span>
                        <span className="font-bold text-sm">{a.title}</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">{a.detail}</p>
                      <p className="text-[13px] text-slate-800 mt-1.5"><span className="font-bold text-indigo-600">Do this:</span> {a.action}</p>
                    </div>
                  )) : <p className="text-sm text-slate-400">No alerts — you're in good shape.</p>}
                </div>
              </div>

              {/* Compliance calendar */}
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wide text-slate-400 mb-3">🗓️ Compliance Calendar</h2>
                <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
                  {cc.compliance?.map((c, i) => (
                    <div key={i} className="flex items-center justify-between gap-2 px-4 py-2.5">
                      <div>
                        <div className="text-sm font-semibold">{c.name}</div>
                        <div className="text-[11px] text-slate-400">{c.authority} · {c.cadence} · {c.due_date}</div>
                      </div>
                      <span className={`shrink-0 text-[11px] font-bold px-2 py-1 rounded ${URG[c.urgency] || URG.scheduled}`}>
                        {c.days_left < 0 ? `${-c.days_left}d overdue` : `in ${c.days_left}d`}
                      </span>
                    </div>
                  ))}
                </div>
                {cc.sector_licences?.length > 0 && (
                  <div className="mt-3 text-xs text-slate-500">
                    <span className="font-bold">Sector licences to track:</span> {cc.sector_licences.join(" · ")}
                  </div>
                )}
              </div>
            </div>

            <p className="text-xs text-slate-400 border-t border-slate-200 pt-4">{cc.disclaimer}</p>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 text-center text-xs text-slate-400 py-10 px-4">
        Business Command Center · Indian MSME Consulting · Powered by AI · statutory dates shift with notifications — confirm with your CA/CS.
      </footer>
    </div>
  );
}

function KpiTile({ k }) {
  const arrow = k.direction === "up" ? "▲" : k.direction === "down" ? "▼" : "▬";
  const momCol = k.momentum === "improving" ? "text-emerald-600" : k.momentum === "worsening" ? "text-rose-600" : "text-slate-400";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3.5">
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-slate-500 leading-tight">{k.label}</span>
        <span className={`w-2 h-2 rounded-full ${STATUS_DOT[k.status] || STATUS_DOT.ok}`} />
      </div>
      <div className="text-2xl font-black mt-1">{k.current}<span className="text-xs font-semibold text-slate-400 ml-0.5">{k.unit === "₹" ? "" : k.unit}</span></div>
      <div className={`text-[12px] font-bold ${momCol}`}>
        {arrow} {k.change_pct != null ? `${k.change_pct > 0 ? "+" : ""}${k.change_pct}%` : "—"}
        {k.target != null && <span className="text-slate-400 font-normal"> · tgt {k.target}{k.unit === "%" ? "%" : ""}</span>}
      </div>
    </div>
  );
}
