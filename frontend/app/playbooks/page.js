"use client";
import { useEffect, useMemo, useState } from "react";

/* ============================================================
   Consulting Command Center — Industry Playbook Engine
   30 priority Indian-MSME business types, each a 13-part
   research-grade operating blueprint. Advisory-first.
   ============================================================ */

const TIER_STYLE = {
  1: { label: "Tier 1 · Highest priority", grad: "from-indigo-500 to-violet-600", chip: "bg-indigo-500/15 text-indigo-300 border-indigo-500/30" },
  2: { label: "Tier 2 · High priority",    grad: "from-sky-500 to-cyan-600",     chip: "bg-sky-500/15 text-sky-300 border-sky-500/30" },
  3: { label: "Tier 3 · Broad coverage",   grad: "from-emerald-500 to-teal-600", chip: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
};

const SEV = {
  Critical: "bg-rose-500/20 text-rose-300 border-rose-500/40",
  High:     "bg-amber-500/20 text-amber-300 border-amber-500/40",
  Medium:   "bg-sky-500/20 text-sky-300 border-sky-500/40",
  Low:      "bg-slate-500/20 text-slate-300 border-slate-500/40",
};
const IMPACT = { High: "text-emerald-300", Medium: "text-amber-300", Low: "text-slate-400" };
const TIER_BADGE = { A: "bg-emerald-500/15 text-emerald-300", B: "bg-amber-500/15 text-amber-300", C: "bg-slate-500/15 text-slate-300" };

function Section({ id, icon, title, children }) {
  return (
    <section id={id} className="scroll-mt-24">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">{icon}</span>
        <h3 className="text-base font-bold text-white">{title}</h3>
      </div>
      <div className="rounded-2xl border border-slate-700/60 bg-slate-800/40 p-4 md:p-5">{children}</div>
    </section>
  );
}

const Chip = ({ children, cls = "" }) => (
  <span className={`inline-block text-[11px] px-2 py-0.5 rounded-full border ${cls || "bg-slate-700/40 text-slate-300 border-slate-600/50"}`}>{children}</span>
);

export default function PlaybooksPage() {
  const [meta, setMeta] = useState(null);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [activeKey, setActiveKey] = useState(null);
  const [pb, setPb] = useState(null);
  const [loading, setLoading] = useState(false);
  const [matchText, setMatchText] = useState("");

  useEffect(() => {
    fetch("/api/playbooks")
      .then((r) => r.json())
      .then((d) => { if (d.error) setErr(d.error); else setMeta(d); })
      .catch((e) => setErr(String(e)));
  }, []);

  const grouped = useMemo(() => {
    const list = (meta?.playbooks || []).filter((c) =>
      !q.trim() || (c.name + " " + (c.one_liner || "")).toLowerCase().includes(q.toLowerCase())
    );
    return { 1: list.filter((c) => c.tier === 1), 2: list.filter((c) => c.tier === 2), 3: list.filter((c) => c.tier === 3) };
  }, [meta, q]);

  async function open(body, key) {
    setLoading(true); setPb(null); setActiveKey(key || null);
    try {
      const r = await fetch("/api/playbooks", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      const d = await r.json();
      if (d.error) setErr(d.error);
      else { setPb(d.playbook); setActiveKey(d.matched_key); window.scrollTo({ top: 0, behavior: "smooth" }); }
    } catch (e) { setErr(String(e)); }
    setLoading(false);
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      {/* Header */}
      <div className="border-b border-slate-800 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-6">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
            <a href="/auto" className="hover:text-slate-200">← Command Center</a>
            <span>/</span><span className="text-slate-300">Industry Playbooks</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Industry Playbook Engine
          </h1>
          <p className="text-slate-400 mt-1 max-w-3xl text-sm md:text-base">
            Research-grade operating blueprints for {meta?.total || 30} priority Indian-MSME business types — each a
            13-part advisory pack: operating model, value chain, bottlenecks, AI-automation map, KPI tree,
            risk model, ₹ profitability, growth playbook & digital-maturity ladder. Every claim traceable to Indian statute.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-6 py-6">
        {err && (
          <div className="mb-4 rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-200 px-4 py-3 text-sm">{err}</div>
        )}

        {/* Free-text matcher */}
        <div className="mb-6 rounded-2xl border border-slate-700/60 bg-slate-900/60 p-4">
          <label className="text-sm font-semibold text-white">Describe your business → get its playbook</label>
          <div className="flex flex-col sm:flex-row gap-2 mt-2">
            <input
              value={matchText} onChange={(e) => setMatchText(e.target.value)}
              placeholder="e.g. multi-branch pharmacy chain in Pune with a distribution arm"
              className="flex-1 rounded-xl bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              onKeyDown={(e) => e.key === "Enter" && matchText.trim() && open({ description: matchText }, null)}
            />
            <button
              onClick={() => matchText.trim() && open({ description: matchText }, null)}
              className="rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 px-5 py-2 text-sm font-semibold text-white hover:opacity-90"
            >Match playbook</button>
          </div>
        </div>

        {/* Detail view */}
        {(loading || pb) && (
          <div className="mb-8">
            {loading && <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-8 text-center text-slate-400 animate-pulse">Building playbook…</div>}
            {pb && <PlaybookView pb={pb} onClose={() => { setPb(null); setActiveKey(null); }} />}
          </div>
        )}

        {/* Sector grid */}
        {!pb && (
          <>
            <input
              value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter sectors…"
              className="mb-5 w-full sm:w-72 rounded-xl bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            {[1, 2, 3].map((t) => (
              grouped[t].length > 0 && (
                <div key={t} className="mb-8">
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${TIER_STYLE[t].chip}`}>{TIER_STYLE[t].label}</span>
                    <span className="text-xs text-slate-500">{grouped[t].length} sectors</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {grouped[t].map((c) => (
                      <button key={c.key} onClick={() => open({ key: c.key }, c.key)}
                        className="text-left rounded-2xl border border-slate-700/60 bg-slate-900/50 p-4 hover:border-indigo-500/60 hover:bg-slate-800/60 transition group">
                        <div className="flex items-start gap-3">
                          <div className={`h-10 w-10 shrink-0 rounded-xl bg-gradient-to-br ${TIER_STYLE[t].grad} grid place-items-center text-lg`}>{c.icon}</div>
                          <div className="min-w-0">
                            <div className="font-semibold text-white group-hover:text-indigo-300 truncate">{c.name}</div>
                            <div className="text-xs text-slate-400 line-clamp-2 mt-0.5">{c.one_liner}</div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )
            ))}
            {!meta && !err && <div className="text-slate-500 text-sm">Loading playbooks…</div>}
          </>
        )}
      </div>
    </div>
  );
}

/* ---------------- Full playbook renderer ---------------- */
function PlaybookView({ pb, onClose }) {
  const t = pb.tier || 3;
  const style = TIER_STYLE[t] || TIER_STYLE[3];
  return (
    <div className="rounded-3xl border border-slate-700/60 bg-slate-900/70 overflow-hidden">
      {/* banner */}
      <div className={`bg-gradient-to-r ${style.grad} px-5 md:px-7 py-5`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-2xl bg-white/15 grid place-items-center text-2xl">{pb.icon}</div>
            <div>
              <div className="text-xs text-white/80">{pb.tier_label}</div>
              <h2 className="text-xl md:text-2xl font-extrabold text-white">{pb.name}</h2>
              <p className="text-white/90 text-sm mt-0.5 max-w-2xl">{pb.one_liner}</p>
            </div>
          </div>
          <div className="flex gap-2 shrink-0">
            <button onClick={() => window.print()} className="rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs px-3 py-1.5">Print / PDF</button>
            <button onClick={onClose} className="rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs px-3 py-1.5">← All sectors</button>
          </div>
        </div>
      </div>

      {/* section nav */}
      <div className="flex flex-wrap gap-1.5 px-5 md:px-7 py-3 border-b border-slate-800 bg-slate-900/80 sticky top-0 z-10">
        {(pb.sections || []).map((s) => (
          <a key={s.key} href={`#${s.key}`} className="text-[11px] px-2 py-1 rounded-md bg-slate-800 text-slate-300 hover:bg-indigo-600 hover:text-white">{s.icon} {s.label}</a>
        ))}
      </div>

      <div className="p-5 md:p-7 space-y-7">
        {/* Operating model */}
        <Section id="operating_model" icon="🧩" title="Operating Model">
          <p className="text-sm text-slate-300 mb-4">{pb.operating_model?.summary}</p>
          <div className="grid md:grid-cols-3 gap-4">
            <Col title="Revenue streams" items={pb.operating_model?.revenue_streams} accent="text-emerald-300" />
            <Col title="Cost structure" items={pb.operating_model?.cost_structure} accent="text-rose-300" />
            <Col title="Value drivers" items={pb.operating_model?.value_drivers} accent="text-indigo-300" />
          </div>
        </Section>

        {/* Workflow architecture */}
        <Section id="workflow_architecture" icon="🔗" title="Workflow Architecture">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            {(pb.workflow_architecture?.value_chain || []).map((v, i, arr) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-xs px-2.5 py-1 rounded-lg bg-indigo-500/15 text-indigo-200 border border-indigo-500/30">{v}</span>
                {i < arr.length - 1 && <span className="text-slate-600">→</span>}
              </div>
            ))}
          </div>
          <div className="grid md:grid-cols-2 gap-3">
            {(pb.workflow_architecture?.core_processes || []).map((p, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="font-semibold text-white text-sm">{p.process}</div>
                <div className="text-xs text-slate-400 mt-1">{p.description}</div>
              </div>
            ))}
          </div>
        </Section>

        {/* Department structure */}
        <Section id="department_structure" icon="🏛️" title="Department Structure">
          <div className="grid md:grid-cols-2 gap-3">
            {(pb.department_structure || []).map((d, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="font-semibold text-white text-sm">{d.dept}</div>
                <div className="text-xs text-slate-400 mt-1">{d.mandate}</div>
                <div className="flex flex-wrap gap-1 mt-2">{(d.key_roles || []).map((r, j) => <Chip key={j}>{r}</Chip>)}</div>
              </div>
            ))}
          </div>
        </Section>

        {/* Bottlenecks */}
        <Section id="operational_bottlenecks" icon="🚧" title="Operational Bottlenecks">
          <div className="space-y-2">
            {(pb.operational_bottlenecks || []).map((b, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="font-semibold text-white text-sm">{b.bottleneck}</div>
                <div className="grid sm:grid-cols-3 gap-2 mt-2 text-xs">
                  <div><span className="text-slate-500">Symptom: </span><span className="text-slate-300">{b.symptom}</span></div>
                  <div><span className="text-slate-500">Impact: </span><span className="text-amber-300">{b.impact}</span></div>
                  <div><span className="text-slate-500">Root cause: </span><span className="text-slate-300">{b.root_cause}</span></div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* AI automation */}
        <Section id="ai_automation_opportunities" icon="🤖" title="AI Automation Opportunities">
          <div className="grid md:grid-cols-2 gap-3">
            {(pb.ai_automation_opportunities || []).map((o, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="text-sm text-white">{o.opportunity}</div>
                <div className="flex items-center gap-2 mt-2 text-xs">
                  {o.agent ? <a href={`/advisor?agent=${o.agent}`} className="px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-200 border border-violet-500/40 hover:bg-violet-500/30">🤖 {o.agent}</a> : <Chip>manual</Chip>}
                  <span className="text-slate-500">Effort <b className={IMPACT[o.effort]}>{o.effort}</b></span>
                  <span className="text-slate-500">Impact <b className={IMPACT[o.impact]}>{o.impact}</b></span>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Frameworks */}
        <Section id="consulting_frameworks" icon="📐" title="Consulting Frameworks">
          <div className="grid md:grid-cols-2 gap-3">
            {(pb.consulting_frameworks || []).map((f, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="font-semibold text-indigo-300 text-sm">{f.framework}</div>
                <div className="text-xs text-slate-400 mt-1">{f.use}</div>
              </div>
            ))}
          </div>
        </Section>

        {/* Risk model */}
        <Section id="risk_model" icon="⚠️" title="Risk Model">
          <div className="space-y-2">
            {(pb.risk_model || []).map((r, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="flex items-center justify-between gap-2">
                  <div className="font-semibold text-white text-sm">{r.risk}</div>
                  <div className="flex gap-1 shrink-0">
                    <Chip cls={SEV[r.severity]}>{r.severity}</Chip>
                    <Chip>{r.likelihood} likelihood</Chip>
                  </div>
                </div>
                <div className="text-xs text-slate-400 mt-1"><span className="text-slate-500">Control: </span>{r.control}</div>
              </div>
            ))}
          </div>
        </Section>

        {/* KPI tree */}
        <Section id="kpi_structure" icon="📊" title="KPI Structure">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="text-slate-400 text-left border-b border-slate-700">
                <th className="py-2 pr-3">KPI</th><th className="py-2 pr-3">Definition</th>
                <th className="py-2 pr-3 text-emerald-300">Healthy</th><th className="py-2 pr-3 text-amber-300">Watch</th><th className="py-2 text-rose-300">Critical</th>
              </tr></thead>
              <tbody>
                {(pb.kpi_structure || []).map((k, i) => (
                  <tr key={i} className="border-b border-slate-800">
                    <td className="py-2 pr-3 font-medium text-white">{k.kpi}</td>
                    <td className="py-2 pr-3 text-slate-400">{k.definition}</td>
                    <td className="py-2 pr-3 text-emerald-300">{k.healthy}</td>
                    <td className="py-2 pr-3 text-amber-300">{k.watch}</td>
                    <td className="py-2 text-rose-300">{k.critical}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        {/* Profitability */}
        <Section id="profitability_analysis" icon="💰" title="Profitability Analysis (₹)">
          <div className="grid sm:grid-cols-2 gap-3 mb-4">
            <div className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
              <div className="text-xs text-slate-500">Typical gross margin</div>
              <div className="text-lg font-bold text-emerald-300">{pb.profitability_analysis?.typical_gross_margin}</div>
            </div>
            <div className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
              <div className="text-xs text-slate-500">Typical net margin</div>
              <div className="text-lg font-bold text-indigo-300">{pb.profitability_analysis?.typical_net_margin}</div>
            </div>
          </div>
          <Col title="Unit economics" items={pb.profitability_analysis?.unit_economics} accent="text-slate-200" />
          <p className="text-xs text-slate-400 mt-3"><span className="text-slate-500">Working capital: </span>{pb.profitability_analysis?.working_capital_notes}</p>
          <div className="mt-3"><Col title="Profit levers" items={pb.profitability_analysis?.levers} accent="text-emerald-300" /></div>
        </Section>

        {/* PM workflows */}
        <Section id="pm_workflows" icon="🗂️" title="PM Workflows">
          <div className="space-y-2">
            {(pb.pm_workflows || []).map((p, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-white text-sm">{p.initiative}</div>
                  <Chip>{p.cadence}</Chip>
                </div>
                <ol className="mt-2 flex flex-wrap gap-2 text-xs text-slate-300">
                  {(p.milestones || []).map((m, j) => <li key={j} className="px-2 py-0.5 rounded bg-slate-700/40">{j + 1}. {m}</li>)}
                </ol>
              </div>
            ))}
          </div>
        </Section>

        {/* Lifecycle */}
        <Section id="product_service_lifecycle" icon="🔄" title="Product / Service Lifecycle">
          <div className="grid md:grid-cols-2 gap-3">
            {(pb.product_service_lifecycle || []).map((p, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="font-semibold text-white text-sm">{i + 1}. {p.phase}</div>
                <ul className="mt-1 text-xs text-slate-400 list-disc list-inside space-y-0.5">
                  {(p.key_activities || []).map((a, j) => <li key={j}>{a}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </Section>

        {/* Growth playbook */}
        <Section id="growth_playbook" icon="🚀" title="Growth Playbook">
          <div className="grid md:grid-cols-3 gap-3">
            {(pb.growth_playbook?.stages || []).map((s, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="font-semibold text-white text-sm">{s.stage}</div>
                <div className="text-xs text-indigo-300 mb-1">{s.focus}</div>
                <ul className="text-xs text-slate-400 list-disc list-inside space-y-0.5">
                  {(s.plays || []).map((p, j) => <li key={j}>{p}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </Section>

        {/* Digital maturity ladder */}
        <Section id="digital_maturity_model" icon="📶" title="Digital Maturity Model">
          <div className="space-y-2">
            {(pb.digital_maturity_model || []).map((m, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50 flex gap-3">
                <div className="h-8 w-8 shrink-0 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 grid place-items-center text-sm font-bold text-white">{m.level}</div>
                <div className="min-w-0">
                  <div className="font-semibold text-white text-sm">{m.name}</div>
                  <div className="flex flex-wrap gap-1 mt-1">{(m.signals || []).map((s, j) => <Chip key={j}>{s}</Chip>)}</div>
                  <div className="text-xs text-emerald-300 mt-1">→ Next: {m.next_step}</div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Compliance + citations */}
        <Section id="compliance" icon="🏛️" title="Compliance & Citations">
          <div className="mb-3">
            <div className="text-xs text-slate-500 mb-1">Binding compliance</div>
            <div className="flex flex-wrap gap-1.5">
              {(pb.compliance_resolved || []).map((c, i) => (
                <Chip key={i} cls={TIER_BADGE[c.tier] || ""}>{c.title}</Chip>
              ))}
            </div>
          </div>
          <div className="text-xs text-slate-500 mb-1">Sources</div>
          <div className="space-y-1">
            {(pb.citations_resolved || []).map((c, i) => (
              <div key={i} className="text-xs text-slate-400 flex items-start gap-2">
                <span className={`px-1.5 rounded ${TIER_BADGE[c.tier] || ""}`}>{c.tier}</span>
                <span><b className="text-slate-300">{c.title}</b>{c.ref ? ` — ${c.ref}` : ""}{c.authority ? ` (${c.authority})` : ""}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </div>
  );
}

function Col({ title, items, accent }) {
  return (
    <div>
      <div className="text-xs font-semibold text-slate-400 mb-1.5">{title}</div>
      <ul className="space-y-1">
        {(items || []).map((it, i) => (
          <li key={i} className={`text-xs ${accent} flex gap-1.5`}><span className="text-slate-600">•</span><span className="text-slate-300">{it}</span></li>
        ))}
      </ul>
    </div>
  );
}
