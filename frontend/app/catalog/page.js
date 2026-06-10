"use client";

/* Consulting Catalog — the AI Consulting OS service portfolio, the way a top firm
   organises expertise: Consulting Towers (L1) → Service Lines (L2) → Workflows (L3),
   each fronted by an AI advisor and delivered by a live agent. Includes a "describe
   your need" router that maps free text to the right advisor (→ /advisor?agent=).
   Reads /api/catalog (GET tree, POST resolve). Mirrors the user's taxonomy. */

import { useEffect, useMemo, useState } from "react";

const COV = {
  covered: { label: "Covered", chip: "bg-emerald-100 text-emerald-700 border-emerald-200", dot: "bg-emerald-500" },
  partial: { label: "Partial", chip: "bg-amber-100 text-amber-700 border-amber-200", dot: "bg-amber-500" },
  planned: { label: "Planned", chip: "bg-slate-100 text-slate-500 border-slate-200", dot: "bg-slate-400" },
};

export default function CatalogPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState({});
  const [q, setQ] = useState("");
  const [routing, setRouting] = useState(false);
  const [route, setRoute] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch("/api/catalog", { cache: "no-store" });
        const d = await r.json();
        if (d.error) setErr(d.error); else setData(d);
      } catch (e) { setErr(e.message); }
    })();
  }, []);

  async function resolve() {
    if (!q.trim()) return;
    setRouting(true); setRoute(null);
    try {
      const r = await fetch("/api/catalog", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: q }) });
      setRoute(await r.json());
    } catch (e) { setRoute({ error: e.message }); }
    finally { setRouting(false); }
  }

  const stats = useMemo(() => {
    if (!data?.towers) return null;
    const c = { covered: 0, partial: 0, planned: 0 };
    data.towers.forEach((t) => (c[t.coverage] = (c[t.coverage] || 0) + 1));
    return c;
  }, [data]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <a href="/auto" className="font-black tracking-tight text-sm sm:text-base">Indian MSME Consulting <span className="text-indigo-600">· Powered by AI</span></a>
          <div className="flex items-center gap-1 text-sm">
            <a href="/ceo" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">CEO Office</a>
            <a href="/advisor" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Advisors</a>
            <a href="/process" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Process Map</a>
          </div>
        </div>
      </nav>

      {/* Hero + router */}
      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> Consulting Service Portfolio · Towers → Service Lines → Workflows
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            Everything a Big-4 firm sells.<br /><span className="text-indigo-300">Delivered by AI advisors.</span>
          </h1>
          <p className="text-slate-300 mt-4 max-w-2xl">
            {data ? `${data.tower_count} consulting towers · ${data.service_line_count} service lines · ${data.workflow_count} workflows · ${data.ai_advisors?.length} AI advisors` : "Loading the full consulting service portfolio…"}
          </p>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 sm:p-5 mt-7">
            <div className="text-[11px] uppercase tracking-wide text-slate-400 font-bold mb-2">Describe your problem → we route you to the right advisor</div>
            <div className="flex flex-col sm:flex-row gap-2">
              <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && resolve()}
                placeholder="e.g. our receivables are stretched and collections are a mess…"
                className="flex-1 bg-white/10 border border-white/15 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
              <button onClick={resolve} disabled={routing} className="px-5 py-3 rounded-xl bg-indigo-500 hover:bg-indigo-400 font-bold text-sm disabled:opacity-50">
                {routing ? "Routing…" : "Find my advisor →"}
              </button>
            </div>
            {route && !route.error && route.matched && (
              <div className="mt-3 bg-indigo-600/30 border border-indigo-400/30 rounded-xl p-3 text-sm">
                <span className="opacity-80">Routed to</span> <b>{route.tower.icon} {route.tower.name}</b> → <b>{route.service_line}</b>
                {route.workflow && <> → <span className="text-indigo-200">{route.workflow}</span></>}
                <div className="mt-1.5 flex items-center gap-2">
                  <span className="text-[12px]">Advisor: <b>{route.tower.ai_advisor}</b> · agent <code className="text-indigo-200">{route.agent}</code></span>
                  {route.agent_live && <a href={`/advisor?agent=${route.agent}`} className="ml-auto px-3 py-1.5 rounded-lg bg-white text-indigo-700 font-bold text-[12px] hover:opacity-90">Open advisor →</a>}
                </div>
              </div>
            )}
            {route && !route.matched && !route.error && <div className="mt-3 text-amber-300 text-sm">No clear match — try naming the function (finance, receivables, procurement, tax, risk, HR…).</div>}
            {route?.error && <div className="mt-3 text-rose-300 text-sm">{route.error}</div>}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        {err && <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 font-semibold">{err}</div>}

        {stats && (
          <div className="flex flex-wrap items-center gap-3 mb-6 text-sm">
            <span className="font-black">Coverage:</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />{stats.covered} covered</span>
            {stats.partial > 0 && <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" />{stats.partial} partial</span>}
            {stats.planned > 0 && <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-slate-400" />{stats.planned} planned</span>}
            <span className="text-slate-400">· every tower is fronted by a live AI advisor</span>
          </div>
        )}

        {/* Towers */}
        <div className="grid md:grid-cols-2 gap-4">
          {(data?.towers || []).map((t, i) => {
            const isOpen = open[t.key];
            const cov = COV[t.coverage] || COV.planned;
            return (
              <div key={t.key} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                <button onClick={() => setOpen((o) => ({ ...o, [t.key]: !o[t.key] }))} className="w-full text-left p-5 hover:bg-slate-50 transition">
                  <div className="flex items-start gap-3">
                    <span className="text-3xl">{t.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-black text-slate-300">L1 · {String(i + 1).padStart(2, "0")}</span>
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${cov.chip}`}>{cov.label}</span>
                      </div>
                      <div className="font-black text-lg leading-tight mt-0.5">{t.name}</div>
                      <div className="text-[12px] text-indigo-600 font-semibold mt-0.5">🤖 {t.ai_advisor}</div>
                      <div className="text-[11px] text-slate-400 mt-1">{t.service_line_count} service lines · {t.workflow_count} workflows</div>
                    </div>
                    <span className="text-slate-400 font-black text-lg">{isOpen ? "−" : "+"}</span>
                  </div>
                </button>
                {isOpen && (
                  <div className="border-t border-slate-100 p-5 space-y-3 bg-slate-50/50">
                    {t.service_lines.map((s, j) => (
                      <div key={j} className="bg-white rounded-xl border border-slate-200 p-3">
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <div className="font-bold text-sm">{s.name}</div>
                          {s.agent && (
                            s.live
                              ? <a href={`/advisor?agent=${s.agent}`} className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-semibold hover:bg-indigo-200">▶ {s.agent_name}</a>
                              : <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 font-semibold">{s.agent_name || s.agent}</span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {s.workflows.map((w, k) => (
                            <span key={k} className="text-[11px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">{w}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                    {t.note && <p className="text-[11px] text-slate-400 italic">{t.note}</p>}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* AI advisor roster */}
        {data?.ai_advisors?.length > 0 && (
          <section className="mt-12">
            <h2 className="text-xl font-black tracking-tight mb-1">Your AI advisor team</h2>
            <p className="text-sm text-slate-500 mb-4">The C-suite + GBS expertise of a top firm, delivered as agents instead of large teams.</p>
            <div className="flex flex-wrap gap-2">
              {data.ai_advisors.map((a, i) => (
                <a key={i} href={a.live ? `/advisor?agent=${a.agent}` : "#"}
                  className={`px-3 py-2 rounded-xl border text-sm font-semibold ${a.live ? "bg-white border-slate-200 hover:border-indigo-400" : "bg-slate-50 border-slate-200 text-slate-400"}`}>
                  {a.advisor}
                  {a.live && <span className="ml-1.5 w-2 h-2 inline-block rounded-full bg-emerald-500 align-middle" />}
                </a>
              ))}
            </div>
          </section>
        )}

        {/* Core 12 */}
        {data?.core_12?.length > 0 && (
          <section className="mt-12">
            <h2 className="text-xl font-black tracking-tight mb-1">The 12 areas that drive most consulting revenue</h2>
            <p className="text-sm text-slate-500 mb-4">What the Big 3 + Big 4 actually sell — all live in this OS.</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {data.core_12.map((c, i) => (
                <div key={i} className="bg-white rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold flex items-center gap-2">
                  <span className="text-[10px] font-black text-slate-300">{String(i + 1).padStart(2, "0")}</span>{c.area}
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
