"use client";

/* MSME Intelligence — the data-rich landing. Filter by sector → business type →
   an intelligence card (TAM, EBITDA, CAGR, benchmarks, risks, KPIs, ERP modules,
   recommended AI advisors) → next steps, incl. one-click "Run a full engagement"
   which hands a pre-fed sample to /engage and auto-runs it. Reads /api/market. */

import { useEffect, useMemo, useState } from "react";

const OPP = {
  "Very High": "bg-emerald-100 text-emerald-700 border-emerald-200",
  High: "bg-indigo-100 text-indigo-700 border-indigo-200",
  "Med": "bg-amber-100 text-amber-700 border-amber-200",
  "Low-Med": "bg-amber-100 text-amber-700 border-amber-200",
  Medium: "bg-amber-100 text-amber-700 border-amber-200",
  Low: "bg-slate-100 text-slate-500 border-slate-200",
};

export default function MarketPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [sector, setSector] = useState(null);
  const [card, setCard] = useState(null);
  const [loadingCard, setLoadingCard] = useState(false);
  const [q, setQ] = useState("");

  useEffect(() => {
    (async () => {
      try { const r = await fetch("/api/market", { cache: "no-store" }); const d = await r.json(); if (d.error) setErr(d.error); else setData(d); } catch (e) { setErr(e.message); }
    })();
  }, []);

  async function openCard(payload) {
    setLoadingCard(true); setCard(null);
    try {
      const r = await fetch("/api/market", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const d = await r.json();
      setCard(d);
      setTimeout(() => document.getElementById("card")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (e) { setErr(e.message); }
    finally { setLoadingCard(false); }
  }

  function runEngagement(sample) {
    try { localStorage.setItem("pmguru_prefill", JSON.stringify(sample)); } catch {}
    window.location.href = "/engage";
  }

  const segs = useMemo(() => {
    if (!data?.segments) return [];
    let s = sector ? data.segments.filter((x) => x.sector === sector.key) : data.segments;
    if (q.trim()) { const ql = q.toLowerCase(); s = s.filter((x) => x.label.toLowerCase().includes(ql)); }
    return s;
  }, [data, sector, q]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <a href="/auto" className="font-black tracking-tight text-sm sm:text-base">Indian MSME Consulting <span className="text-indigo-600">· Powered by AI</span></a>
          <div className="flex items-center gap-1 text-sm">
            <a href="/engage" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Engage</a>
            <a href="/catalog" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Services</a>
            <a href="/advisor" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Advisors</a>
          </div>
        </div>
      </nav>

      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 sm:py-14">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> MSME Intelligence · India 2026 · market data + benchmarks
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">Know your market.<br /><span className="text-indigo-300">Then run the engagement.</span></h1>
          <p className="text-slate-300 mt-4 max-w-2xl">Pick your sector and business type to see the market size, margins, benchmarks, risks and the AI advisors that fit — then go straight to a full Big-4-style engagement with one click.</p>
          <div className="mt-6 max-w-md">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search a business type… (e.g. Kirana, Auto Components, SaaS)"
              className="w-full bg-white/10 border border-white/15 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-10">
        {err && <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 font-semibold">{err}</div>}

        {/* Sector filter */}
        <section>
          <div className="flex items-end justify-between flex-wrap gap-2 mb-3">
            <h2 className="text-xl font-black tracking-tight">{data ? `${data.count} sectors` : "Loading sectors…"} — pick one to filter</h2>
            {sector && <button onClick={() => { setSector(null); setCard(null); }} className="text-sm font-semibold text-indigo-600 hover:underline">Clear filter ✕</button>}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {(data?.sectors || []).map((s) => (
              <button key={s.key} onClick={() => { setSector(s); setCard(null); setQ(""); }}
                className={`text-left bg-white rounded-2xl border p-4 transition ${sector?.key === s.key ? "border-indigo-500 ring-2 ring-indigo-100" : "border-slate-200 hover:border-indigo-300"}`}>
                <div className="flex items-center justify-between">
                  <span className="text-2xl">{s.icon}</span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${OPP[s.ai_opportunity] || OPP.Medium}`}>AI {s.ai_opportunity}</span>
                </div>
                <div className="font-black text-sm mt-2 leading-tight">{s.name}</div>
                <div className="text-[11px] text-slate-500 mt-1">TAM {s.market_value}</div>
                <div className="flex gap-2 mt-1 text-[10px] text-slate-400 font-semibold">
                  <span>EBITDA {s.ebitda}</span><span>· CAGR {s.cagr}</span>
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* Business types */}
        <section>
          <h2 className="text-xl font-black tracking-tight mb-3">
            {sector ? `${sector.icon} ${sector.name} — business types` : "All business types"} <span className="text-slate-400 font-bold text-sm">({segs.length})</span>
          </h2>
          {segs.length === 0 && <p className="text-sm text-slate-400">No business types match. Try clearing the filter or search.</p>}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {segs.map((s) => (
              <button key={s.sector + s.key} onClick={() => openCard({ business_type: s.label })}
                className="text-left bg-white rounded-2xl border border-slate-200 p-4 hover:border-indigo-400 hover:shadow-md transition">
                <div className="font-black text-sm">{s.label}</div>
                <div className="text-[11px] text-indigo-600 font-semibold capitalize">{s.sector.replace(/_/g, " ")}</div>
                <div className="flex flex-wrap gap-2 mt-2 text-[11px] text-slate-500">
                  <span className="bg-slate-100 px-1.5 py-0.5 rounded font-semibold">TAM {s.market_value}</span>
                  <span className="bg-slate-100 px-1.5 py-0.5 rounded font-semibold">Avg {s.avg_revenue}</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1.5">Top: {s.top_revenue} · {s.problems.join(", ")}</div>
                <div className="text-[11px] text-indigo-600 font-bold mt-2">View intelligence →</div>
              </button>
            ))}
          </div>
        </section>

        {loadingCard && <div className="text-center text-slate-500 py-8 animate-pulse">Pulling the intelligence card…</div>}

        {/* Intelligence card */}
        {card && !card.error && (
          <section id="card" className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-gradient-to-br from-indigo-600 to-violet-700 text-white p-6">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{card.sector.icon}</span>
                <div>
                  <h3 className="text-2xl font-black">{card.business_type}</h3>
                  <div className="text-indigo-100 text-sm">{card.sector.name} · India MSME Intelligence</div>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
                {[["Market (TAM)", card.sector.market_value], ["Avg revenue", card.sector.avg_revenue], ["Top MSME", card.sector.top_revenue], ["EBITDA", card.sector.ebitda], ["CAGR", card.sector.cagr], ["Gross margin", card.sector.gross_margin], ["Export potential", card.sector.export_potential], ["AI opportunity", card.sector.ai_opportunity]].map(([k, v], i) => (
                  <div key={i} className="bg-white/10 rounded-xl p-3">
                    <div className="text-[10px] uppercase tracking-wide text-indigo-100 font-bold">{k}</div>
                    <div className="font-black text-sm mt-0.5">{v}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 grid md:grid-cols-2 gap-6">
              <div>
                <Block title="Benchmarks (days / %)">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {[["Working capital", card.benchmarks.working_capital_days + "d"], ["Inventory", card.benchmarks.inventory_days + "d"], ["Receivables", card.benchmarks.receivable_days + "d"], ["Payables", card.benchmarks.payable_days + "d"]].map(([k, v], i) => (
                      <div key={i} className="bg-slate-50 rounded-lg px-3 py-2 flex items-center justify-between"><span className="text-slate-500 text-[12px]">{k}</span><span className="font-bold">{v}</span></div>
                    ))}
                  </div>
                </Block>
                <Block title="Key risks">
                  <div className="flex flex-wrap gap-1.5">{card.sector.key_risks.map((r, i) => <span key={i} className="text-[11px] bg-rose-50 text-rose-700 border border-rose-100 px-2 py-1 rounded-lg font-semibold">{r}</span>)}</div>
                </Block>
                <Block title="Key KPIs">
                  <div className="flex flex-wrap gap-1.5">{card.sector.key_kpis.map((k, i) => <span key={i} className="text-[11px] bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-1 rounded-lg font-semibold">{k}</span>)}</div>
                </Block>
              </div>
              <div>
                <Block title="ERP modules">
                  <div className="flex flex-wrap gap-1.5">{card.sector.erp_modules.map((m, i) => <span key={i} className="text-[11px] bg-slate-100 text-slate-600 px-2 py-1 rounded-lg font-semibold capitalize">{m}</span>)}</div>
                </Block>
                <Block title="Recommended AI advisors">
                  <div className="flex flex-wrap gap-1.5">
                    {card.recommended_agents.map((a, i) => <a key={i} href={`/advisor?agent=${a.key}`} className="text-[11px] bg-violet-50 text-violet-700 border border-violet-100 px-2 py-1 rounded-lg font-semibold hover:bg-violet-100">{a.name}</a>)}
                  </div>
                </Block>
                {card.playbook_key && (
                  <Block title="Industry playbook">
                    <a href="/playbooks" className="text-sm font-semibold text-indigo-600 hover:underline">Open the {card.playbook_key.replace(/_/g, " ")} playbook →</a>
                  </Block>
                )}
              </div>
            </div>

            {/* Next steps */}
            <div className="border-t border-slate-100 p-6 bg-slate-50">
              <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-3">Next steps</div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => runEngagement(card.sample_engagement)} className="px-5 py-3 rounded-xl bg-indigo-600 text-white font-black text-sm hover:bg-indigo-500">▶ Run a full engagement (demo)</button>
                <a href="/playbooks" className="px-5 py-3 rounded-xl border border-slate-300 bg-white font-semibold text-sm hover:border-indigo-300">See the playbook</a>
                <a href="/schemes" className="px-5 py-3 rounded-xl border border-slate-300 bg-white font-semibold text-sm hover:border-indigo-300">Find government schemes</a>
                <a href={`/advisor${card.recommended_agents[0] ? `?agent=${card.recommended_agents[0].key}` : ""}`} className="px-5 py-3 rounded-xl border border-slate-300 bg-white font-semibold text-sm hover:border-indigo-300">Talk to a specialist</a>
              </div>
              <p className="text-[11px] text-slate-400 mt-3">{card.disclaimer}</p>
            </div>
          </section>
        )}

        {/* Highest opportunity */}
        {data?.highest_opportunity && (
          <section>
            <h2 className="text-xl font-black tracking-tight mb-1">Highest-opportunity segments for AI consulting</h2>
            <p className="text-sm text-slate-500 mb-4">Where the market is biggest and the AI leverage is strongest.</p>
            <div className="grid sm:grid-cols-2 gap-2">
              {data.highest_opportunity.map((o) => (
                <div key={o.rank} className="bg-white rounded-xl border border-slate-200 px-4 py-3 flex items-center gap-3">
                  <span className="shrink-0 w-7 h-7 rounded-full bg-indigo-600 text-white text-xs font-black flex items-center justify-center">{o.rank}</span>
                  <span className="font-bold text-sm flex-1">{o.segment}</span>
                  <span className="text-sm font-semibold text-slate-500">{o.market_value}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function Block({ title, children }) {
  return (
    <div className="mb-4">
      <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-1.5">{title}</div>
      {children}
    </div>
  );
}
