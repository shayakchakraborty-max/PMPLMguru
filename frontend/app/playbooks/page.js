"use client";
import { useEffect, useMemo, useState } from "react";

/* ============================================================
   Consulting Command Center
   Tab 1 — New Engagement: structured intake FORM -> customised
           engagement (playbook + live web search + memory + LLM).
   Tab 2 — Playbook Library: the 30 static sector blueprints.
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
const PRIO = { High: "text-rose-300", Medium: "text-amber-300", Low: "text-slate-400" };
const TIER_BADGE = { A: "bg-emerald-500/15 text-emerald-300", B: "bg-amber-500/15 text-amber-300", C: "bg-slate-500/15 text-slate-300" };

const Chip = ({ children, cls = "" }) => (
  <span className={`inline-block text-[11px] px-2 py-0.5 rounded-full border ${cls || "bg-slate-700/40 text-slate-300 border-slate-600/50"}`}>{children}</span>
);
function Section({ id, icon, title, children }) {
  return (
    <section id={id} className="scroll-mt-24">
      <div className="flex items-center gap-2 mb-3"><span className="text-lg">{icon}</span><h3 className="text-base font-bold text-white">{title}</h3></div>
      <div className="rounded-2xl border border-slate-700/60 bg-slate-800/40 p-4 md:p-5">{children}</div>
    </section>
  );
}

export default function CommandCenter() {
  const [tab, setTab] = useState("engagement");
  const [meta, setMeta] = useState(null);       // consult meta: fields, playbooks, modes
  const [err, setErr] = useState("");

  // engagement form state
  const [mode, setMode] = useState("existing");
  const [form, setForm] = useState({});
  const [running, setRunning] = useState(false);
  const [engagement, setEngagement] = useState(null);

  // library state
  const [q, setQ] = useState("");
  const [pb, setPb] = useState(null);
  const [pbLoading, setPbLoading] = useState(false);

  useEffect(() => {
    fetch("/api/consult").then((r) => r.json()).then((d) => { if (d.error) setErr(d.error); else setMeta(d); }).catch((e) => setErr(String(e)));
  }, []);

  const fields = useMemo(() => (meta?.fields || []).filter((f) => (f.modes || []).includes(mode)), [meta, mode]);
  const sectors = meta?.playbooks || [];

  function setF(k, v) { setForm((p) => ({ ...p, [k]: v })); }

  async function runEngagement() {
    if (!form.description?.trim()) { setErr("Please describe your business first."); return; }
    setErr(""); setRunning(true); setEngagement(null);
    try {
      const r = await fetch("/api/consult", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, ...form }),
      });
      const d = await r.json();
      if (d.error) setErr(d.error);
      else { setEngagement(d); window.scrollTo({ top: 0, behavior: "smooth" }); }
    } catch (e) { setErr(String(e)); }
    setRunning(false);
  }

  async function openPlaybook(key) {
    setPbLoading(true); setPb(null);
    try {
      const r = await fetch("/api/playbooks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key }) });
      const d = await r.json();
      if (d.error) setErr(d.error); else { setPb(d.playbook); window.scrollTo({ top: 0, behavior: "smooth" }); }
    } catch (e) { setErr(String(e)); }
    setPbLoading(false);
  }

  const groupedSectors = useMemo(() => {
    const list = sectors.filter((c) => !q.trim() || (c.name + " " + (c.one_liner || "")).toLowerCase().includes(q.toLowerCase()));
    return { 1: list.filter((c) => c.tier === 1), 2: list.filter((c) => c.tier === 2), 3: list.filter((c) => c.tier === 3) };
  }, [sectors, q]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <div className="border-b border-slate-800 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-6">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
            <a href="/auto" className="hover:text-slate-200">← Home</a><span>/</span><span className="text-slate-300">Consulting Command Center</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">Consulting Command Center</h1>
          <p className="text-slate-400 mt-1 max-w-3xl text-sm md:text-base">
            Give the brain your specifics and it builds a <b className="text-slate-200">customised engagement</b> — grounded on your sector
            playbook, <b className="text-slate-200">live open-source research</b>, and what it has learned from past engagements. It evolves with every prompt.
          </p>
          {/* tabs */}
          <div className="flex gap-2 mt-4">
            <button onClick={() => setTab("engagement")} className={`px-4 py-2 rounded-xl text-sm font-semibold ${tab === "engagement" ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"}`}>🧠 New Engagement</button>
            <button onClick={() => setTab("library")} className={`px-4 py-2 rounded-xl text-sm font-semibold ${tab === "library" ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"}`}>📚 Playbook Library</button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-6 py-6">
        {err && <div className="mb-4 rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-200 px-4 py-3 text-sm">{err}</div>}

        {/* ============ TAB 1: ENGAGEMENT ============ */}
        {tab === "engagement" && (
          <div className="grid lg:grid-cols-5 gap-6">
            {/* FORM */}
            <div className="lg:col-span-2">
              <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-5 sticky top-4">
                <div className="flex gap-2 mb-4">
                  {(meta?.modes || [{ key: "startup", label: "New / Startup", icon: "🚀" }, { key: "existing", label: "Existing Business", icon: "🏢" }]).map((m) => (
                    <button key={m.key} onClick={() => setMode(m.key)} className={`flex-1 px-3 py-2 rounded-xl text-sm font-semibold border ${mode === m.key ? "bg-indigo-600 text-white border-indigo-500" : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"}`}>{m.icon} {m.label}</button>
                  ))}
                </div>
                <div className="space-y-3">
                  {fields.map((f) => <Field key={f.key} f={f} mode={mode} value={form[f.key] || ""} sectors={sectors} onChange={(v) => setF(f.key, v)} />)}
                </div>
                <button onClick={runEngagement} disabled={running}
                  className="mt-4 w-full rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 px-5 py-3 text-sm font-bold text-white hover:opacity-90 disabled:opacity-50">
                  {running ? "Researching & synthesising…" : "Generate consulting engagement →"}
                </button>
                <p className="text-[11px] text-slate-500 mt-2">Searches open sources live, then reasons over your inputs. 10–30s when the LLM key is set.</p>
              </div>
            </div>

            {/* RESULT */}
            <div className="lg:col-span-3">
              {running && <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-10 text-center text-slate-400 animate-pulse">Searching open sources, recalling past engagements, synthesising your engagement…</div>}
              {!running && !engagement && (
                <div className="rounded-2xl border border-dashed border-slate-700/60 bg-slate-900/40 p-10 text-center text-slate-500">
                  <div className="text-4xl mb-2">🧠</div>
                  Fill the form and the brain will build a customised, source-grounded engagement for <i>your</i> business — not a generic template.
                </div>
              )}
              {engagement && <EngagementView e={engagement} />}
            </div>
          </div>
        )}

        {/* ============ TAB 2: LIBRARY ============ */}
        {tab === "library" && (
          <>
            {pbLoading && <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-8 text-center text-slate-400 animate-pulse mb-6">Loading playbook…</div>}
            {pb && <div className="mb-8"><PlaybookView pb={pb} onClose={() => setPb(null)} /></div>}
            {!pb && (
              <>
                <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter sectors…" className="mb-5 w-full sm:w-72 rounded-xl bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500" />
                {[1, 2, 3].map((t) => groupedSectors[t]?.length > 0 && (
                  <div key={t} className="mb-8">
                    <div className="flex items-center gap-2 mb-3"><span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${TIER_STYLE[t].chip}`}>{TIER_STYLE[t].label}</span><span className="text-xs text-slate-500">{groupedSectors[t].length} sectors</span></div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {groupedSectors[t].map((c) => (
                        <button key={c.key} onClick={() => openPlaybook(c.key)} className="text-left rounded-2xl border border-slate-700/60 bg-slate-900/50 p-4 hover:border-indigo-500/60 hover:bg-slate-800/60 transition group">
                          <div className="flex items-start gap-3">
                            <div className={`h-10 w-10 shrink-0 rounded-xl bg-gradient-to-br ${TIER_STYLE[t].grad} grid place-items-center text-lg`}>{c.icon}</div>
                            <div className="min-w-0"><div className="font-semibold text-white group-hover:text-indigo-300 truncate">{c.name}</div><div className="text-xs text-slate-400 line-clamp-2 mt-0.5">{c.one_liner}</div></div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
                {!meta && !err && <div className="text-slate-500 text-sm">Loading…</div>}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/* ---------------- Form field ---------------- */
function Field({ f, mode, value, onChange, sectors }) {
  const base = "w-full rounded-xl bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500";
  let input;
  if (f.type === "textarea") input = <textarea rows={f.key === "description" ? 3 : 2} value={value} onChange={(e) => onChange(e.target.value)} placeholder={f.ph} className={base} />;
  else if (f.type === "number") input = <input type="number" value={value} onChange={(e) => onChange(e.target.value)} placeholder={f.ph} className={base} />;
  else if (f.type === "playbook") input = (
    <select value={value} onChange={(e) => onChange(e.target.value)} className={base}>
      <option value="">Auto-detect from description</option>
      {(sectors || []).map((s) => <option key={s.key} value={s.key}>{s.icon} {s.name}</option>)}
    </select>
  );
  else if (f.type === "select") {
    const opts = f.options || (mode === "startup" ? f.options_startup : f.options_existing) || [];
    input = <select value={value} onChange={(e) => onChange(e.target.value)} className={base}><option value="">Select…</option>{opts.map((o) => <option key={o} value={o}>{o}</option>)}</select>;
  } else input = <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={f.ph} className={base} />;
  return (
    <div>
      <label className="text-xs font-semibold text-slate-400">{f.label}{f.required && <span className="text-rose-400"> *</span>}</label>
      <div className="mt-1">{input}</div>
    </div>
  );
}

/* ---------------- Engagement renderer ---------------- */
function EngagementView({ e }) {
  const live = (e.engine || "").startsWith("groq");
  return (
    <div className="rounded-3xl border border-slate-700/60 bg-slate-900/70 overflow-hidden">
      <div className="bg-gradient-to-r from-indigo-600 to-violet-700 px-5 md:px-7 py-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs text-white/80 uppercase tracking-wide">{e.mode === "startup" ? "Startup engagement" : "Existing-business engagement"} · {e.sector_name}</div>
            <h2 className="text-xl md:text-2xl font-extrabold text-white mt-0.5">Your customised engagement</h2>
          </div>
          <button onClick={() => window.print()} className="rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs px-3 py-1.5 shrink-0">Print / PDF</button>
        </div>
        <div className="flex flex-wrap gap-1.5 mt-3">
          <Chip cls={live ? "bg-emerald-500/20 text-emerald-100 border-emerald-400/40" : "bg-white/15 text-white border-white/20"}>{live ? "🟢 Live LLM synthesis" : "⚙️ Deterministic engine"}</Chip>
          <Chip cls="bg-white/15 text-white border-white/20">🔎 {(e.sources || []).length} open sources</Chip>
          <Chip cls="bg-white/15 text-white border-white/20">🧠 recalled {e.recall?.used || 0}/{e.recall?.total_memory || 0} past</Chip>
          {e.learned && <Chip cls="bg-white/15 text-white border-white/20">💾 learned from this</Chip>}
          {e.playbook_link && <a href={e.playbook_link} className="text-[11px] px-2 py-0.5 rounded-full bg-white/15 text-white border border-white/20 hover:bg-white/25">📚 full playbook →</a>}
        </div>
      </div>

      <div className="p-5 md:p-7 space-y-7">
        <Section id="diag" icon="🩺" title="Diagnosis"><p className="text-sm text-slate-300 leading-relaxed">{e.diagnosis}</p></Section>

        <Section id="recs" icon="🎯" title="Tailored Recommendations">
          <div className="space-y-2">
            {(e.tailored_recommendations || []).map((r, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="flex items-center justify-between gap-2"><div className="font-semibold text-white text-sm">{r.title}</div>{r.priority && <Chip cls={SEV[r.priority]}>{r.priority}</Chip>}</div>
                {r.why && <div className="text-xs text-slate-400 mt-1"><span className="text-slate-500">Why: </span>{r.why}</div>}
                {r.how && <div className="text-xs text-slate-300 mt-0.5"><span className="text-slate-500">How: </span>{r.how}</div>}
              </div>
            ))}
          </div>
        </Section>

        {(e.quick_wins || []).length > 0 && (
          <Section id="qw" icon="⚡" title="Quick Wins (this month)">
            <ul className="space-y-1">{e.quick_wins.map((w, i) => <li key={i} className="text-sm text-emerald-300 flex gap-2"><span>✓</span><span className="text-slate-300">{w}</span></li>)}</ul>
          </Section>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          <Section id="risks" icon="⚠️" title="Risks">
            <div className="space-y-2">{(e.risks || []).map((r, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="flex items-center justify-between gap-2"><div className="text-sm text-white">{r.risk}</div><Chip cls={SEV[r.severity]}>{r.severity}</Chip></div>
                {r.control && <div className="text-xs text-slate-400 mt-1">{r.control}</div>}
              </div>))}</div>
          </Section>
          <Section id="kpis" icon="📊" title="KPIs to hit">
            <div className="space-y-2">{(e.kpis || []).map((k, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
                <div className="flex items-center justify-between gap-2"><div className="text-sm font-medium text-white">{k.kpi}</div><span className="text-xs text-emerald-300">{k.target}</span></div>
                {k.why && <div className="text-xs text-slate-500 mt-0.5">{k.why}</div>}
              </div>))}</div>
          </Section>
        </div>

        <Section id="plan" icon="🗓️" title="90-Day Action Plan">
          <div className="grid md:grid-cols-3 gap-3">{(e.action_plan_90day || []).map((p, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
              <div className="font-semibold text-indigo-300 text-sm mb-1">{p.phase}</div>
              <ul className="text-xs text-slate-300 list-disc list-inside space-y-0.5">{(p.steps || []).map((s, j) => <li key={j}>{s}</li>)}</ul>
            </div>))}</div>
        </Section>

        {(e.opportunities || []).length > 0 && (
          <Section id="opps" icon="🚀" title="Growth Opportunities">
            <div className="flex flex-wrap gap-2">{e.opportunities.map((o, i) => <Chip key={i} cls="bg-indigo-500/15 text-indigo-200 border-indigo-500/30">{o}</Chip>)}</div>
          </Section>
        )}

        {(e.sources || []).length > 0 && (
          <Section id="src" icon="🔎" title="Open-Source Research Used">
            <div className="space-y-1.5">{e.sources.map((s, i) => (
              <div key={i} className="text-xs text-slate-400">
                <span className="px-1.5 rounded bg-slate-700/50 text-slate-300 mr-1">{s.source}</span>
                {s.url ? <a href={s.url} target="_blank" rel="noreferrer" className="text-indigo-300 hover:underline">{s.title}</a> : <b className="text-slate-300">{s.title}</b>}
                {s.snippet && <span className="text-slate-500"> — {s.snippet}</span>}
              </div>))}</div>
          </Section>
        )}

        {(e.citations || []).length > 0 && (
          <Section id="cite" icon="🏛️" title="Statutory Citations">
            <div className="space-y-1">{e.citations.map((c, i) => (
              <div key={i} className="text-xs text-slate-400 flex items-start gap-2"><span className={`px-1.5 rounded ${TIER_BADGE[c.tier] || ""}`}>{c.tier}</span><span><b className="text-slate-300">{c.title}</b>{c.ref ? ` — ${c.ref}` : ""}</span></div>))}</div>
          </Section>
        )}

        {(e.recall?.notes || []).length > 0 && (
          <Section id="memory" icon="🧠" title="What the brain remembered">
            <ul className="space-y-1">{e.recall.notes.map((n, i) => <li key={i} className="text-xs text-violet-200">• {n}</li>)}</ul>
          </Section>
        )}
      </div>
    </div>
  );
}

/* ---------------- Static playbook renderer (library) ---------------- */
function PlaybookView({ pb, onClose }) {
  const t = pb.tier || 3; const style = TIER_STYLE[t] || TIER_STYLE[3];
  const Col = ({ title, items, accent }) => (
    <div><div className="text-xs font-semibold text-slate-400 mb-1.5">{title}</div>
      <ul className="space-y-1">{(items || []).map((it, i) => <li key={i} className="text-xs flex gap-1.5"><span className="text-slate-600">•</span><span className={accent}>{it}</span></li>)}</ul></div>
  );
  return (
    <div className="rounded-3xl border border-slate-700/60 bg-slate-900/70 overflow-hidden">
      <div className={`bg-gradient-to-r ${style.grad} px-5 md:px-7 py-5`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-2xl bg-white/15 grid place-items-center text-2xl">{pb.icon}</div>
            <div><div className="text-xs text-white/80">{pb.tier_label}</div><h2 className="text-xl md:text-2xl font-extrabold text-white">{pb.name}</h2><p className="text-white/90 text-sm mt-0.5 max-w-2xl">{pb.one_liner}</p></div>
          </div>
          <button onClick={onClose} className="rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs px-3 py-1.5 shrink-0">← All sectors</button>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5 px-5 md:px-7 py-3 border-b border-slate-800 bg-slate-900/80 sticky top-0 z-10">
        {(pb.sections || []).map((s) => <a key={s.key} href={`#${s.key}`} className="text-[11px] px-2 py-1 rounded-md bg-slate-800 text-slate-300 hover:bg-indigo-600 hover:text-white">{s.icon} {s.label}</a>)}
      </div>
      <div className="p-5 md:p-7 space-y-7">
        <Section id="operating_model" icon="🧩" title="Operating Model">
          <p className="text-sm text-slate-300 mb-4">{pb.operating_model?.summary}</p>
          <div className="grid md:grid-cols-3 gap-4">
            <Col title="Revenue streams" items={pb.operating_model?.revenue_streams} accent="text-slate-300" />
            <Col title="Cost structure" items={pb.operating_model?.cost_structure} accent="text-slate-300" />
            <Col title="Value drivers" items={pb.operating_model?.value_drivers} accent="text-slate-300" />
          </div>
        </Section>
        <Section id="workflow_architecture" icon="🔗" title="Workflow Architecture">
          <div className="flex flex-wrap items-center gap-2 mb-4">{(pb.workflow_architecture?.value_chain || []).map((v, i, arr) => (
            <div key={i} className="flex items-center gap-2"><span className="text-xs px-2.5 py-1 rounded-lg bg-indigo-500/15 text-indigo-200 border border-indigo-500/30">{v}</span>{i < arr.length - 1 && <span className="text-slate-600">→</span>}</div>))}</div>
          <div className="grid md:grid-cols-2 gap-3">{(pb.workflow_architecture?.core_processes || []).map((p, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="font-semibold text-white text-sm">{p.process}</div><div className="text-xs text-slate-400 mt-1">{p.description}</div></div>))}</div>
        </Section>
        <Section id="department_structure" icon="🏛️" title="Department Structure">
          <div className="grid md:grid-cols-2 gap-3">{(pb.department_structure || []).map((d, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="font-semibold text-white text-sm">{d.dept}</div><div className="text-xs text-slate-400 mt-1">{d.mandate}</div><div className="flex flex-wrap gap-1 mt-2">{(d.key_roles || []).map((r, j) => <Chip key={j}>{r}</Chip>)}</div></div>))}</div>
        </Section>
        <Section id="operational_bottlenecks" icon="🚧" title="Operational Bottlenecks">
          <div className="space-y-2">{(pb.operational_bottlenecks || []).map((b, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="font-semibold text-white text-sm">{b.bottleneck}</div>
              <div className="grid sm:grid-cols-3 gap-2 mt-2 text-xs"><div><span className="text-slate-500">Symptom: </span>{b.symptom}</div><div><span className="text-slate-500">Impact: </span><span className="text-amber-300">{b.impact}</span></div><div><span className="text-slate-500">Root cause: </span>{b.root_cause}</div></div></div>))}</div>
        </Section>
        <Section id="ai_automation_opportunities" icon="🤖" title="AI Automation Opportunities">
          <div className="grid md:grid-cols-2 gap-3">{(pb.ai_automation_opportunities || []).map((o, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="text-sm text-white">{o.opportunity}</div>
              <div className="flex items-center gap-2 mt-2 text-xs">{o.agent ? <a href={`/advisor?agent=${o.agent}`} className="px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-200 border border-violet-500/40 hover:bg-violet-500/30">🤖 {o.agent}</a> : <Chip>manual</Chip>}<span className="text-slate-500">Effort {o.effort}</span><span className="text-slate-500">Impact {o.impact}</span></div></div>))}</div>
        </Section>
        <Section id="risk_model" icon="⚠️" title="Risk Model">
          <div className="space-y-2">{(pb.risk_model || []).map((r, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="flex items-center justify-between gap-2"><div className="font-semibold text-white text-sm">{r.risk}</div><div className="flex gap-1 shrink-0"><Chip cls={SEV[r.severity]}>{r.severity}</Chip><Chip>{r.likelihood}</Chip></div></div><div className="text-xs text-slate-400 mt-1">{r.control}</div></div>))}</div>
        </Section>
        <Section id="kpi_structure" icon="📊" title="KPI Structure">
          <div className="overflow-x-auto"><table className="w-full text-xs"><thead><tr className="text-slate-400 text-left border-b border-slate-700"><th className="py-2 pr-3">KPI</th><th className="py-2 pr-3">Definition</th><th className="py-2 pr-3 text-emerald-300">Healthy</th><th className="py-2 pr-3 text-amber-300">Watch</th><th className="py-2 text-rose-300">Critical</th></tr></thead>
            <tbody>{(pb.kpi_structure || []).map((k, i) => (<tr key={i} className="border-b border-slate-800"><td className="py-2 pr-3 font-medium text-white">{k.kpi}</td><td className="py-2 pr-3 text-slate-400">{k.definition}</td><td className="py-2 pr-3 text-emerald-300">{k.healthy}</td><td className="py-2 pr-3 text-amber-300">{k.watch}</td><td className="py-2 text-rose-300">{k.critical}</td></tr>))}</tbody></table></div>
        </Section>
        <Section id="profitability_analysis" icon="💰" title="Profitability Analysis (₹)">
          <div className="grid sm:grid-cols-2 gap-3 mb-4">
            <div className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="text-xs text-slate-500">Typical gross margin</div><div className="text-lg font-bold text-emerald-300">{pb.profitability_analysis?.typical_gross_margin}</div></div>
            <div className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="text-xs text-slate-500">Typical net margin</div><div className="text-lg font-bold text-indigo-300">{pb.profitability_analysis?.typical_net_margin}</div></div>
          </div>
          <Col title="Unit economics" items={pb.profitability_analysis?.unit_economics} accent="text-slate-300" />
          <p className="text-xs text-slate-400 mt-3"><span className="text-slate-500">Working capital: </span>{pb.profitability_analysis?.working_capital_notes}</p>
          <div className="mt-3"><Col title="Profit levers" items={pb.profitability_analysis?.levers} accent="text-emerald-300" /></div>
        </Section>
        <Section id="pm_workflows" icon="🗂️" title="PM Workflows">
          <div className="space-y-2">{(pb.pm_workflows || []).map((p, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="flex items-center justify-between"><div className="font-semibold text-white text-sm">{p.initiative}</div><Chip>{p.cadence}</Chip></div><ol className="mt-2 flex flex-wrap gap-2 text-xs text-slate-300">{(p.milestones || []).map((m, j) => <li key={j} className="px-2 py-0.5 rounded bg-slate-700/40">{j + 1}. {m}</li>)}</ol></div>))}</div>
        </Section>
        <Section id="product_service_lifecycle" icon="🔄" title="Product / Service Lifecycle">
          <div className="grid md:grid-cols-2 gap-3">{(pb.product_service_lifecycle || []).map((p, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="font-semibold text-white text-sm">{i + 1}. {p.phase}</div><ul className="mt-1 text-xs text-slate-400 list-disc list-inside space-y-0.5">{(p.key_activities || []).map((a, j) => <li key={j}>{a}</li>)}</ul></div>))}</div>
        </Section>
        <Section id="growth_playbook" icon="🚀" title="Growth Playbook">
          <div className="grid md:grid-cols-3 gap-3">{(pb.growth_playbook?.stages || []).map((s, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50"><div className="font-semibold text-white text-sm">{s.stage}</div><div className="text-xs text-indigo-300 mb-1">{s.focus}</div><ul className="text-xs text-slate-400 list-disc list-inside space-y-0.5">{(s.plays || []).map((p, j) => <li key={j}>{p}</li>)}</ul></div>))}</div>
        </Section>
        <Section id="digital_maturity_model" icon="📶" title="Digital Maturity Model">
          <div className="space-y-2">{(pb.digital_maturity_model || []).map((m, i) => (
            <div key={i} className="rounded-xl bg-slate-800/50 p-3 border border-slate-700/50 flex gap-3"><div className="h-8 w-8 shrink-0 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 grid place-items-center text-sm font-bold text-white">{m.level}</div>
              <div className="min-w-0"><div className="font-semibold text-white text-sm">{m.name}</div><div className="flex flex-wrap gap-1 mt-1">{(m.signals || []).map((s, j) => <Chip key={j}>{s}</Chip>)}</div><div className="text-xs text-emerald-300 mt-1">→ Next: {m.next_step}</div></div></div>))}</div>
        </Section>
        <Section id="compliance" icon="🏛️" title="Compliance & Citations">
          <div className="mb-3"><div className="text-xs text-slate-500 mb-1">Binding compliance</div><div className="flex flex-wrap gap-1.5">{(pb.compliance_resolved || []).map((c, i) => <Chip key={i} cls={TIER_BADGE[c.tier] || ""}>{c.title}</Chip>)}</div></div>
          <div className="text-xs text-slate-500 mb-1">Sources</div>
          <div className="space-y-1">{(pb.citations_resolved || []).map((c, i) => (<div key={i} className="text-xs text-slate-400 flex items-start gap-2"><span className={`px-1.5 rounded ${TIER_BADGE[c.tier] || ""}`}>{c.tier}</span><span><b className="text-slate-300">{c.title}</b>{c.ref ? ` — ${c.ref}` : ""}{c.authority ? ` (${c.authority})` : ""}</span></div>))}</div>
        </Section>
      </div>
    </div>
  );
}
