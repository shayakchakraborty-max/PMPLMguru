"use client";
import { useEffect, useMemo, useState } from "react";

/* ============================================================
   Consulting Command Center — light, report-grade.
   Tab 1  New Engagement : multi-step due-diligence wizard -> customised report
   Tab 2  Playbook Library: 30 research-grade sector encyclopedias
   ============================================================ */

const TIER = {
  1: { label: "Tier 1 · Highest priority", grad: "from-indigo-600 to-violet-600", soft: "bg-indigo-50 text-indigo-700 border-indigo-200", dot: "bg-indigo-600" },
  2: { label: "Tier 2 · High priority",    grad: "from-sky-600 to-cyan-600",     soft: "bg-sky-50 text-sky-700 border-sky-200",         dot: "bg-sky-600" },
  3: { label: "Tier 3 · Broad coverage",   grad: "from-emerald-600 to-teal-600", soft: "bg-emerald-50 text-emerald-700 border-emerald-200", dot: "bg-emerald-600" },
};
const SEV = {
  Critical: "bg-rose-100 text-rose-700 border-rose-200",
  High:     "bg-amber-100 text-amber-700 border-amber-200",
  Medium:   "bg-sky-100 text-sky-700 border-sky-200",
  Low:      "bg-slate-100 text-slate-600 border-slate-200",
};
const CITE = { A: "bg-emerald-100 text-emerald-700", B: "bg-amber-100 text-amber-700", C: "bg-slate-100 text-slate-600" };

const Chip = ({ children, cls = "" }) => (
  <span className={`inline-block text-[11px] px-2 py-0.5 rounded-full border ${cls || "bg-slate-100 text-slate-600 border-slate-200"}`}>{children}</span>
);
function Section({ id, icon, title, sub, children }) {
  return (
    <section id={id} className="scroll-mt-24">
      <div className="flex items-center gap-2.5 mb-3">
        <div className="h-8 w-1.5 rounded-full bg-gradient-to-b from-indigo-500 to-violet-500" />
        <span className="text-xl">{icon}</span>
        <div><h3 className="text-lg font-bold text-slate-900 leading-tight">{title}</h3>{sub && <p className="text-xs text-slate-500">{sub}</p>}</div>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-5 md:p-6">{children}</div>
    </section>
  );
}
const Card = ({ children, cls = "" }) => <div className={`rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 ${cls}`}>{children}</div>;

export default function CommandCenter() {
  const [tab, setTab] = useState("engagement");
  const [meta, setMeta] = useState(null);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [pb, setPb] = useState(null);
  const [pbLoading, setPbLoading] = useState(false);
  const [pendingDemo, setPendingDemo] = useState(null);

  useEffect(() => {
    fetch("/api/consult").then((r) => r.json()).then((d) => { if (d.error) setErr(d.error); else setMeta(d); }).catch((e) => setErr(String(e)));
  }, []);

  function runAsEngagement(key) { setPb(null); setTab("engagement"); setPendingDemo(key); window.scrollTo({ top: 0, behavior: "smooth" }); }

  async function openPlaybook(key) {
    setPbLoading(true); setPb(null);
    try {
      const r = await fetch("/api/playbooks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key }) });
      const d = await r.json(); if (d.error) setErr(d.error); else { setPb(d.playbook); window.scrollTo({ top: 0, behavior: "smooth" }); }
    } catch (e) { setErr(String(e)); }
    setPbLoading(false);
  }

  const sectors = meta?.playbooks || [];
  const grouped = useMemo(() => {
    const list = sectors.filter((c) => !q.trim() || (c.name + " " + (c.one_liner || "")).toLowerCase().includes(q.toLowerCase()));
    return { 1: list.filter((c) => c.tier === 1), 2: list.filter((c) => c.tier === 2), 3: list.filter((c) => c.tier === 3) };
  }, [sectors, q]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-6">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2"><a href="/auto" className="hover:text-slate-700">← Home</a><span>/</span><span className="text-slate-600">Consulting Command Center</span></div>
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">Consulting Command Center</h1>
              <p className="text-slate-500 mt-1 max-w-3xl text-sm md:text-base">A research-grade engagement for <b className="text-slate-700">your</b> business — grounded on its sector playbook, live open-source research and what the brain has learned, plus an encyclopedia for all 30 MSME sectors.</p>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={() => { setTab("engagement"); setPb(null); }} className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${tab === "engagement" ? "bg-indigo-600 text-white shadow" : "bg-white border border-slate-200 text-slate-600 hover:border-indigo-300"}`}>🧠 New Engagement</button>
            <button onClick={() => setTab("library")} className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${tab === "library" ? "bg-indigo-600 text-white shadow" : "bg-white border border-slate-200 text-slate-600 hover:border-indigo-300"}`}>📚 Playbook Library</button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 md:px-6 py-6">
        {err && <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 px-4 py-3 text-sm">{err}</div>}

        {tab === "engagement" && <Wizard meta={meta} sectors={sectors} setErr={setErr} pendingDemo={pendingDemo} onConsumedDemo={() => setPendingDemo(null)} />}

        {tab === "library" && (
          <>
            {pbLoading && <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-400 animate-pulse mb-6">Loading playbook…</div>}
            {pb && <div className="mb-8"><Encyclopedia pb={pb} onClose={() => setPb(null)} onRun={() => runAsEngagement(pb.key)} /></div>}
            {!pb && (
              <>
                <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter sectors…" className="mb-5 w-full sm:w-72 rounded-xl bg-white border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" />
                {[1, 2, 3].map((t) => grouped[t]?.length > 0 && (
                  <div key={t} className="mb-8">
                    <div className="flex items-center gap-2 mb-3"><span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${TIER[t].soft}`}>{TIER[t].label}</span><span className="text-xs text-slate-400">{grouped[t].length} sectors</span></div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {grouped[t].map((c) => (
                        <button key={c.key} onClick={() => openPlaybook(c.key)} className="text-left rounded-2xl border border-slate-200 bg-white p-4 hover:shadow-md hover:border-indigo-300 transition group">
                          <div className="flex items-start gap-3">
                            <div className={`h-11 w-11 shrink-0 rounded-xl bg-gradient-to-br ${TIER[t].grad} grid place-items-center text-xl text-white shadow-sm`}>{c.icon}</div>
                            <div className="min-w-0"><div className="font-semibold text-slate-900 group-hover:text-indigo-600 truncate">{c.name}</div><div className="text-xs text-slate-500 line-clamp-2 mt-0.5">{c.one_liner}</div></div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
                {!meta && !err && <div className="text-slate-400 text-sm">Loading…</div>}
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}

/* ================= Multi-step DD wizard ================= */
function Wizard({ meta, sectors, setErr, pendingDemo, onConsumedDemo }) {
  const [mode, setMode] = useState("existing");
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({});
  const [ddFields, setDdFields] = useState([]);
  const [running, setRunning] = useState(false);
  const [engagement, setEngagement] = useState(null);
  const [selSector, setSelSector] = useState("");

  const groups = meta?.groups || [];
  const allFields = meta?.fields || [];
  const demos = meta?.demos || [];
  const setF = (k, v) => setForm((p) => ({ ...p, [k]: v }));

  // sector KPI fields when a sector is explicitly chosen
  useEffect(() => {
    const key = form.business_type;
    if (!key) { setDdFields([]); return; }
    fetch("/api/playbooks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key }) })
      .then((r) => r.json()).then((d) => setDdFields(d.playbook?.dd_fields || [])).catch(() => setDdFields([]));
  }, [form.business_type]);

  const stepFields = useMemo(() => allFields.filter((f) => f.group === groups[step]?.key && (f.modes || []).includes(mode)), [allFields, groups, step, mode]);
  const onFinancial = groups[step]?.key === "operations"; // attach sector KPIs to operations step

  async function run(overrideForm, overrideMode) {
    const useForm = overrideForm || form;
    const useMode = overrideMode || mode;
    if (!useForm.description?.trim()) { setErr("Please describe your business in step 1."); setStep(0); return; }
    setErr(""); setRunning(true); setEngagement(null);
    try {
      const r = await fetch("/api/consult", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: useMode, ...useForm }) });
      const d = await r.json();
      if (d.error) setErr(d.error); else { setEngagement(d); window.scrollTo({ top: 0, behavior: "smooth" }); }
    } catch (e) { setErr(String(e)); }
    setRunning(false);
  }

  function loadIntake(intake, andRun) {
    setMode(intake.mode); setForm({ ...intake }); setStep(0); setEngagement(null);
    if (andRun) run({ ...intake }, intake.mode);
  }
  const sectorScenarios = (key) => (demos.find((x) => x.key === key)?.scenarios) || [];

  // "Run as engagement" from the Playbook Library lands here (uses the signature scenario).
  useEffect(() => {
    if (pendingDemo && demos.length) {
      const sc = sectorScenarios(pendingDemo);
      const sig = sc.find((s) => s.lens === "signature") || sc[0];
      if (sig) { setSelSector(pendingDemo); loadIntake(sig.intake, true); }
      onConsumedDemo && onConsumedDemo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingDemo, demos.length]);

  if (engagement) return <div><button onClick={() => setEngagement(null)} className="mb-4 text-sm text-indigo-600 hover:underline">← New engagement</button><EngagementReport e={engagement} /></div>;

  const last = step === groups.length - 1;
  return (
    <>
    {/* Demo scenario bar */}
    {demos.length > 0 && (
      <div className="mb-5 rounded-2xl border border-indigo-200 bg-gradient-to-r from-indigo-50 to-violet-50 p-4">
        <div className="flex flex-col lg:flex-row lg:items-center gap-3">
          <div className="shrink-0">
            <div className="text-xs font-bold text-indigo-700 uppercase tracking-wide">✨ Try a live demo scenario</div>
            <div className="text-xs text-slate-500">Pick a sector, then a situation — the brain fills the form and runs a full engagement.</div>
          </div>
          <select value={selSector} onChange={(e) => setSelSector(e.target.value)}
            className="lg:flex-1 rounded-xl bg-white border border-indigo-200 px-3 py-2 text-sm focus:outline-none focus:border-indigo-400">
            <option value="">Choose a sector…</option>
            {[1, 2, 3].map((t) => (
              <optgroup key={t} label={`Tier ${t}`}>
                {demos.filter((d) => d.tier === t).map((d) => <option key={d.key} value={d.key}>{d.icon} {d.name}</option>)}
              </optgroup>
            ))}
          </select>
        </div>
        {selSector && (
          <div className="mt-3 grid sm:grid-cols-2 lg:grid-cols-4 gap-2">
            {sectorScenarios(selSector).map((s) => (
              <button key={s.lens} onClick={() => loadIntake(s.intake, true)}
                className="rounded-xl border border-indigo-200 bg-white px-3 py-2 text-left hover:border-indigo-500 hover:shadow-sm transition">
                <div className="text-xs font-bold text-indigo-700">{s.icon} {s.label}</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wide">{s.mode === "startup" ? "Startup" : "Existing"}</div>
                <div className="text-[11px] text-slate-500 line-clamp-3 mt-1">{s.scenario}</div>
              </button>
            ))}
          </div>
        )}
        {form.description && (
          <div className="mt-3 text-xs text-slate-600 bg-white/70 rounded-xl border border-indigo-100 px-3 py-2"><b className="text-indigo-700">Scenario loaded:</b> {form.description}</div>
        )}
      </div>
    )}
    <div className="grid lg:grid-cols-12 gap-6">
      {/* stepper */}
      <aside className="lg:col-span-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 sticky top-4">
          <div className="flex gap-2 mb-4">
            {(meta?.modes || []).map((m) => (
              <button key={m.key} onClick={() => { setMode(m.key); setStep(0); }} className={`flex-1 px-2 py-2 rounded-lg text-xs font-semibold border ${mode === m.key ? "bg-indigo-600 text-white border-indigo-600" : "bg-white border-slate-200 text-slate-600 hover:border-indigo-300"}`}>{m.icon} {m.label}</button>
            ))}
          </div>
          <ol className="space-y-1">
            {groups.map((g, i) => (
              <li key={g.key}>
                <button onClick={() => setStep(i)} className={`w-full text-left flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition ${i === step ? "bg-indigo-50 text-indigo-700 font-semibold" : "text-slate-500 hover:bg-slate-50"}`}>
                  <span className={`h-6 w-6 shrink-0 grid place-items-center rounded-full text-xs font-bold ${i < step ? "bg-emerald-500 text-white" : i === step ? "bg-indigo-600 text-white" : "bg-slate-200 text-slate-500"}`}>{i < step ? "✓" : i + 1}</span>
                  <span>{g.icon} {g.label}</span>
                </button>
              </li>
            ))}
          </ol>
        </div>
      </aside>

      {/* step panel */}
      <div className="lg:col-span-9">
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-5 md:p-6">
          <div className="mb-4">
            <div className="text-xs font-semibold text-indigo-600 uppercase tracking-wide">Step {step + 1} of {groups.length}</div>
            <h2 className="text-xl font-bold text-slate-900">{groups[step]?.icon} {groups[step]?.label}</h2>
            <p className="text-sm text-slate-500">{groups[step]?.blurb}</p>
            <div className="mt-3 h-1.5 rounded-full bg-slate-100 overflow-hidden"><div className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all" style={{ width: `${((step + 1) / groups.length) * 100}%` }} /></div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            {stepFields.map((f) => <Field key={f.key} f={f} mode={mode} value={form[f.key] || ""} sectors={sectors} onChange={(v) => setF(f.key, v)} full={f.type === "textarea"} />)}
          </div>

          {onFinancial && ddFields.length > 0 && (
            <div className="mt-5">
              <div className="text-xs font-semibold text-slate-500 mb-2">📊 Sector KPIs for {sectors.find((s) => s.key === form.business_type)?.name} <span className="font-normal text-slate-400">(optional — sharpens the diagnosis)</span></div>
              <div className="grid sm:grid-cols-2 gap-4">
                {ddFields.map((f) => (
                  <div key={f.key}>
                    <label className="text-xs font-semibold text-slate-600">{f.label}</label>
                    <input value={form[f.key] || ""} onChange={(e) => setF(f.key, e.target.value)} placeholder={f.hint} className="mt-1 w-full rounded-xl bg-white border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
            <button disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))} className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 disabled:opacity-40 hover:border-slate-300">← Back</button>
            {!last ? (
              <button onClick={() => setStep((s) => Math.min(groups.length - 1, s + 1))} className="px-5 py-2 rounded-xl text-sm font-semibold bg-slate-900 text-white hover:bg-slate-800">Next →</button>
            ) : (
              <button onClick={run} disabled={running} className="px-6 py-2.5 rounded-xl text-sm font-bold bg-gradient-to-r from-indigo-600 to-violet-600 text-white hover:opacity-90 disabled:opacity-50">{running ? "Researching & synthesising…" : "Generate consulting report →"}</button>
            )}
          </div>
          {!last && <p className="text-[11px] text-slate-400 mt-2 text-right">You can generate anytime — only the business description is required.</p>}
        </div>
        {running && <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-400 animate-pulse">Searching open sources, recalling past engagements, synthesising your report…</div>}
      </div>
    </div>
    </>
  );
}

function Field({ f, mode, value, onChange, sectors, full }) {
  const base = "mt-1 w-full rounded-xl bg-white border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-indigo-400";
  let input;
  if (f.type === "textarea") input = <textarea rows={f.key === "description" ? 3 : 2} value={value} onChange={(e) => onChange(e.target.value)} placeholder={f.ph} className={base} />;
  else if (f.type === "number") input = <input type="number" value={value} onChange={(e) => onChange(e.target.value)} placeholder={f.ph} className={base} />;
  else if (f.type === "playbook") input = <select value={value} onChange={(e) => onChange(e.target.value)} className={base}><option value="">Auto-detect from description</option>{(sectors || []).map((s) => <option key={s.key} value={s.key}>{s.icon} {s.name}</option>)}</select>;
  else if (f.type === "select") { const opts = f.options || (mode === "startup" ? f.options_startup : f.options_existing) || []; input = <select value={value} onChange={(e) => onChange(e.target.value)} className={base}><option value="">Select…</option>{opts.map((o) => <option key={o} value={o}>{o}</option>)}</select>; }
  else input = <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={f.ph} className={base} />;
  return <div className={full ? "sm:col-span-2" : ""}><label className="text-xs font-semibold text-slate-600">{f.label}{f.required && <span className="text-rose-500"> *</span>}</label>{input}</div>;
}

/* ================= DD Scorecard cockpit ================= */
const BAND = {
  strong:   { bar: "bg-emerald-500", chip: "bg-emerald-100 text-emerald-700" },
  moderate: { bar: "bg-amber-500",   chip: "bg-amber-100 text-amber-700" },
  weak:     { bar: "bg-rose-500",    chip: "bg-rose-100 text-rose-700" },
};
const GRADE_GRAD = { A: "from-emerald-500 to-teal-600", B: "from-sky-500 to-indigo-600", C: "from-amber-500 to-orange-600", D: "from-rose-500 to-pink-600" };
function Scorecard({ sc }) {
  return (
    <Section id="scorecard" icon="📈" title="Due-Diligence Scorecard" sub="Institutional health scores from your inputs — higher is healthier">
      <div className="flex flex-col lg:flex-row gap-5">
        <div className="shrink-0 flex lg:flex-col items-center gap-3 lg:w-28">
          <div className={`h-24 w-24 rounded-2xl bg-gradient-to-br ${GRADE_GRAD[sc.grade] || GRADE_GRAD.C} text-white grid place-items-center shadow-md`}>
            <div className="text-center"><div className="text-4xl font-black leading-none">{sc.grade}</div><div className="text-xs mt-0.5">{sc.overall}/100</div></div>
          </div>
          <div className="text-[11px] text-slate-500 lg:text-center font-semibold uppercase tracking-wide">Overall DD grade</div>
        </div>
        <div className="flex-1 grid sm:grid-cols-2 gap-3">
          {(sc.scores || []).map((s) => {
            const b = BAND[s.band] || BAND.moderate;
            return (
              <div key={s.key} className="rounded-xl border border-slate-200 bg-white p-3.5">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold text-slate-800">{s.icon} {s.label}</div>
                  <div className="text-sm font-bold text-slate-900">{s.score}<span className="text-slate-400 text-xs">/100</span></div>
                </div>
                <div className="mt-1.5 h-2 rounded-full bg-slate-100 overflow-hidden"><div className={`h-full ${b.bar} transition-all`} style={{ width: `${s.score}%` }} /></div>
                <div className="mt-2 space-y-0.5">
                  {(s.drivers || []).slice(0, 2).map((d, i) => (
                    <div key={i} className={`text-[11px] ${d.effect === "+" ? "text-emerald-700" : "text-rose-600"}`}>{d.effect === "+" ? "▲" : "▼"} {d.note}</div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Section>
  );
}

/* ================= Board Pack (CXO / print-to-PDF) ================= */
function engagementMarkdown(e) {
  const sc = e.scorecard || {};
  const L = [];
  L.push(`# Strategic Consulting Engagement — ${e.sector_name}`);
  L.push(`_${e.mode === "startup" ? "Startup" : "Existing business"} · Overall DD grade **${sc.grade}** (${sc.overall}/100) · Private & confidential_\n`);
  L.push(`## Executive Scorecard`);
  (sc.scores || []).forEach((s) => L.push(`- **${s.label}**: ${s.score}/100 (${s.band})${(s.drivers || []).slice(0, 2).map((d) => ` — ${d.effect === "+" ? "▲" : "▼"} ${d.note}`).join("")}`));
  L.push(`\n## Diagnosis\n${e.diagnosis || ""}`);
  if (e.swot) { L.push(`\n## SWOT`); ["strengths", "weaknesses", "opportunities", "threats"].forEach((k) => { L.push(`**${k[0].toUpperCase() + k.slice(1)}**`); (e.swot[k] || []).forEach((x) => L.push(`- ${x}`)); }); }
  L.push(`\n## Recommendations`);
  (e.tailored_recommendations || []).forEach((r) => L.push(`- **${r.title}**${r.priority ? ` [${r.priority}]` : ""}${r.why ? ` — ${r.why}` : ""}${r.how ? ` _How:_ ${r.how}` : ""}`));
  if ((e.quick_wins || []).length) { L.push(`\n## Quick Wins`); e.quick_wins.forEach((w) => L.push(`- ${w}`)); }
  L.push(`\n## Risks`);
  (e.risks || []).forEach((r) => L.push(`- **${r.risk}** [${r.severity}]${r.control ? ` — ${r.control}` : ""}`));
  L.push(`\n## KPIs to hit`);
  (e.kpis || []).forEach((k) => L.push(`- **${k.kpi}** → ${k.target}${k.why ? ` (${k.why})` : ""}`));
  L.push(`\n## 90-Day Action Plan`);
  (e.action_plan_90day || []).forEach((p) => { L.push(`### ${p.phase}`); (p.steps || []).forEach((s) => L.push(`- ${s}`)); });
  if ((e.opportunities || []).length) { L.push(`\n## Growth Opportunities`); e.opportunities.forEach((o) => L.push(`- ${o}`)); }
  if ((e.sources || []).length) { L.push(`\n## Sources`); e.sources.forEach((s) => L.push(`- [${s.source}] ${s.title}${s.url ? ` — ${s.url}` : ""}`)); }
  if ((e.citations || []).length) { L.push(`\n## Statutory Citations`); e.citations.forEach((c) => L.push(`- (${c.tier}) ${c.title}${c.ref ? ` — ${c.ref}` : ""}`)); }
  return L.join("\n");
}
function downloadText(name, text) {
  const blob = new Blob([text], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = url; a.download = name; a.click();
  URL.revokeObjectURL(url);
}
const BH = ({ children }) => <h2 className="text-lg font-black text-slate-900 border-b-2 border-indigo-500 pb-1 mb-3">{children}</h2>;
function BoardPack({ e, onClose }) {
  const sc = e.scorecard || {};
  return (
    <div id="boardpack" className="fixed inset-0 z-50 bg-white overflow-auto text-slate-800">
      <style>{`@media print{ body *{visibility:hidden!important} #boardpack,#boardpack *{visibility:visible!important} #boardpack{position:absolute!important;inset:0!important;overflow:visible!important} .no-print{display:none!important} .bpage{break-after:page} @page{margin:14mm;size:A4} }`}</style>
      <div className="no-print sticky top-0 z-10 flex items-center justify-between bg-slate-900 text-white px-4 py-2">
        <div className="text-sm font-semibold">📑 Board Pack</div>
        <div className="flex gap-2">
          <button onClick={() => window.print()} className="rounded-lg bg-indigo-500 hover:bg-indigo-400 px-3 py-1.5 text-xs font-semibold">🖨 Print / Save PDF</button>
          <button onClick={() => downloadText(`engagement-${e.business_type || "msme"}.md`, engagementMarkdown(e))} className="rounded-lg bg-white/15 hover:bg-white/25 px-3 py-1.5 text-xs">⬇ Download .md</button>
          <button onClick={onClose} className="rounded-lg bg-white/15 hover:bg-white/25 px-3 py-1.5 text-xs">✕ Close</button>
        </div>
      </div>
      <div className="max-w-3xl mx-auto px-8 py-10">
        {/* Cover */}
        <div className="bpage min-h-[58vh] flex flex-col justify-center">
          <div className="text-xs uppercase tracking-[0.25em] text-indigo-600 font-bold">Strategic Consulting Engagement</div>
          <h1 className="text-4xl font-black text-slate-900 mt-2">{e.sector_name}</h1>
          <p className="text-slate-500 mt-1">{e.mode === "startup" ? "Startup" : "Existing business"} · AI-native advisory engagement</p>
          <div className="mt-8 flex items-center gap-4">
            <div className={`h-20 w-20 rounded-2xl bg-gradient-to-br ${GRADE_GRAD[sc.grade] || GRADE_GRAD.C} text-white grid place-items-center`}>
              <div className="text-center"><div className="text-3xl font-black leading-none">{sc.grade}</div><div className="text-[10px] mt-0.5">{sc.overall}/100</div></div>
            </div>
            <div className="text-sm text-slate-600">Overall due-diligence grade</div>
          </div>
          <div className="mt-10 text-[11px] text-slate-400 border-t border-slate-200 pt-3">Private &amp; confidential · Prepared by the AI Consulting Engine · For management use only</div>
        </div>
        {/* Executive summary */}
        <div className="bpage">
          <BH>Executive Summary</BH>
          <div className="grid grid-cols-2 gap-2 mb-4">
            {(sc.scores || []).map((s) => { const b = BAND[s.band] || BAND.moderate; return (
              <div key={s.key} className="border border-slate-200 rounded-lg p-2">
                <div className="flex justify-between text-xs font-semibold text-slate-700"><span>{s.label}</span><span>{s.score}</span></div>
                <div className="h-1.5 bg-slate-100 rounded mt-1"><div className={`${b.bar} h-full rounded`} style={{ width: `${s.score}%` }} /></div>
              </div>); })}
          </div>
          <p className="text-sm text-slate-700 leading-relaxed">{e.diagnosis}</p>
        </div>
        {/* SWOT */}
        {e.swot && <div className="bpage"><BH>SWOT Analysis</BH><Swot s={e.swot} /></div>}
        {/* Recommendations */}
        <div className="bpage">
          <BH>Recommendations</BH>
          <div className="space-y-2">
            {(e.tailored_recommendations || []).map((r, i) => (
              <div key={i} className="border-l-2 border-indigo-400 pl-3">
                <div className="text-sm font-bold text-slate-900">{r.title}{r.priority ? ` · ${r.priority}` : ""}</div>
                {r.why && <div className="text-xs text-slate-500">Why: {r.why}</div>}
                {r.how && <div className="text-xs text-slate-600">How: {r.how}</div>}
              </div>
            ))}
          </div>
        </div>
        {/* Risks + KPIs */}
        <div className="bpage">
          <BH>Risks &amp; KPIs</BH>
          <div className="grid md:grid-cols-2 gap-4">
            <div><div className="text-xs font-bold text-slate-500 uppercase mb-1">Risks</div>{(e.risks || []).map((r, i) => <div key={i} className="text-sm text-slate-700 mb-1">• <b>{r.risk}</b> <span className="text-rose-600">[{r.severity}]</span></div>)}</div>
            <div><div className="text-xs font-bold text-slate-500 uppercase mb-1">KPIs</div>{(e.kpis || []).map((k, i) => <div key={i} className="text-sm text-slate-700 mb-1">• {k.kpi} → <b className="text-emerald-700">{k.target}</b></div>)}</div>
          </div>
        </div>
        {/* 90-day plan */}
        <div className="bpage">
          <BH>90-Day Action Plan</BH>
          {(e.action_plan_90day || []).map((p, i) => (
            <div key={i} className="mb-3"><div className="text-sm font-bold text-indigo-700">{p.phase}</div><ul className="text-sm text-slate-700 list-disc list-inside">{(p.steps || []).map((s, j) => <li key={j}>{s}</li>)}</ul></div>
          ))}
          {(e.opportunities || []).length > 0 && <div className="mt-3"><div className="text-xs font-bold text-slate-500 uppercase mb-1">Growth opportunities</div><div className="text-sm text-slate-700">{e.opportunities.join(" · ")}</div></div>}
        </div>
        {/* Appendix */}
        <div>
          <BH>Appendix — Sources &amp; Citations</BH>
          {(e.sources || []).map((s, i) => <div key={i} className="text-xs text-slate-500 mb-0.5">[{s.source}] {s.title}</div>)}
          <div className="mt-2">{(e.citations || []).map((c, i) => <div key={i} className="text-xs text-slate-500 mb-0.5">({c.tier}) <b className="text-slate-700">{c.title}</b>{c.ref ? ` — ${c.ref}` : ""}</div>)}</div>
        </div>
      </div>
    </div>
  );
}

/* ================= Industry benchmark gauge ================= */
function BenchGauge({ g }) {
  const lower = g.direction === "lower_better";
  const colors = lower ? ["bg-emerald-400", "bg-amber-400", "bg-rose-400"] : ["bg-rose-400", "bg-amber-400", "bg-emerald-400"];
  const zc = { healthy: "bg-emerald-100 text-emerald-700", watch: "bg-amber-100 text-amber-700", critical: "bg-rose-100 text-rose-700" }[g.zone] || "";
  return (
    <div>
      <div className="flex justify-between items-center text-xs"><span className="font-semibold text-slate-700">{g.label}</span><span className={`px-1.5 py-0.5 rounded-full ${zc}`}>{g.value}{g.unit} · {g.zone}</span></div>
      <div className="relative h-2.5 rounded-full overflow-hidden mt-1 flex">
        <div className={colors[0]} style={{ width: `${g.segments[0]}%` }} />
        <div className={colors[1]} style={{ width: `${g.segments[1]}%` }} />
        <div className={colors[2]} style={{ width: `${g.segments[2]}%` }} />
        <div className="absolute -top-0.5 h-3.5 w-[3px] bg-slate-900 rounded" style={{ left: `calc(${g.position_pct}% - 1.5px)` }} />
      </div>
      <div className="text-[10px] text-slate-400 mt-0.5">{g.note}</div>
    </div>
  );
}

/* ================= SWOT ================= */
const SWOT_STYLE = {
  strengths: { t: "Strengths", icon: "💪", box: "border-emerald-200 bg-emerald-50", dot: "text-emerald-600" },
  weaknesses: { t: "Weaknesses", icon: "⚠️", box: "border-rose-200 bg-rose-50", dot: "text-rose-600" },
  opportunities: { t: "Opportunities", icon: "🚀", box: "border-sky-200 bg-sky-50", dot: "text-sky-600" },
  threats: { t: "Threats", icon: "🛡️", box: "border-amber-200 bg-amber-50", dot: "text-amber-600" },
};
function Swot({ s }) {
  return (
    <div className="grid sm:grid-cols-2 gap-3">
      {["strengths", "weaknesses", "opportunities", "threats"].map((k) => { const st = SWOT_STYLE[k]; return (
        <div key={k} className={`rounded-xl border p-3.5 ${st.box}`}>
          <div className="font-bold text-slate-800 text-sm mb-1.5">{st.icon} {st.t}</div>
          <ul className="space-y-1">
            {(s[k] || []).map((x, i) => <li key={i} className="text-xs text-slate-700 flex gap-1.5"><span className={st.dot}>•</span>{x}</li>)}
            {(s[k] || []).length === 0 && <li className="text-xs text-slate-400">—</li>}
          </ul>
        </div>
      ); })}
    </div>
  );
}

/* ================= AI PMO workspace ================= */
const OWNER_COLOR = {
  "CFO / Finance": "bg-emerald-100 text-emerald-700", "COO / Operations": "bg-blue-100 text-blue-700",
  "Sales / Growth": "bg-violet-100 text-violet-700", "Compliance": "bg-amber-100 text-amber-700",
  "Product": "bg-sky-100 text-sky-700", "HR / People": "bg-pink-100 text-pink-700", "Founder / PMO": "bg-slate-200 text-slate-700",
};
const PRIO_DOT = { High: "bg-rose-500", Medium: "bg-amber-500", Normal: "bg-slate-400" };
const STATUS = { todo: { label: "To do", cls: "bg-slate-100 text-slate-500" }, doing: { label: "In progress", cls: "bg-sky-100 text-sky-700" }, done: { label: "Done", cls: "bg-emerald-100 text-emerald-700" } };
function pmoMarkdown(pmo) {
  const L = [`# PM Workspace — ${pmo.summary?.sector || ""}`, `_${pmo.summary?.tasks} tasks · ${pmo.summary?.sprints} sprints · ${pmo.summary?.weeks} weeks_\n`, `## OKRs`];
  (pmo.objectives || []).forEach((o) => { L.push(`### ${o.objective}`); (o.key_results || []).forEach((k) => L.push(`- ${k.kr} _(${k.owner})_`)); });
  (pmo.sprints || []).forEach((s) => { L.push(`\n## ${s.name} (${s.window}) — ${s.goal}`); (pmo.tasks || []).filter((t) => t.sprint === s.id).forEach((t) => L.push(`- [${t.priority}] ${t.title} — ${t.owner}${t.depends_on?.length ? ` (after ${t.depends_on.join(",")})` : ""}`)); });
  return L.join("\n");
}
function PmoBoard({ pmo, sector, onClose }) {
  const [status, setStatus] = useState({});
  const st = (t) => status[t.id] || t.status || "todo";
  const cycle = (t) => { const o = ["todo", "doing", "done"]; setStatus((s) => ({ ...s, [t.id]: o[(o.indexOf(st(t)) + 1) % 3] })); };
  const done = (pmo.tasks || []).filter((t) => st(t) === "done").length;
  const pct = pmo.tasks?.length ? Math.round((done / pmo.tasks.length) * 100) : 0;
  const bySprint = (sid) => (pmo.tasks || []).filter((t) => t.sprint === sid);
  return (
    <div className="fixed inset-0 z-50 bg-slate-50 overflow-auto text-slate-800">
      <div className="sticky top-0 z-10 flex items-center justify-between bg-slate-900 text-white px-4 py-2">
        <div className="text-sm font-semibold">🗂 PM Workspace — {sector}</div>
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-xs"><div className="w-28 h-1.5 bg-white/20 rounded"><div className="h-full bg-emerald-400 rounded" style={{ width: `${pct}%` }} /></div>{pct}% done</div>
          <button onClick={() => downloadText(`pm-workspace-${(sector || "msme").toLowerCase().replace(/\s+/g, "-")}.md`, pmoMarkdown(pmo))} className="rounded-lg bg-white/15 hover:bg-white/25 px-3 py-1.5 text-xs">⬇ Export .md</button>
          <button onClick={onClose} className="rounded-lg bg-white/15 hover:bg-white/25 px-3 py-1.5 text-xs">✕ Close</button>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 md:px-6 py-6 space-y-6">
        {/* OKRs */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 mb-2">🎯 OKRs</h3>
          <div className="grid md:grid-cols-2 gap-3">
            {(pmo.objectives || []).map((o, i) => (
              <div key={i} className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="font-semibold text-slate-900 text-sm">{o.objective}</div>
                <div className="mt-2 space-y-1">{(o.key_results || []).map((k, j) => (
                  <div key={j} className="flex items-center justify-between text-xs"><span className="text-slate-600">◦ {k.kr}</span><span className={`px-1.5 py-0.5 rounded-full text-[10px] ${OWNER_COLOR[k.owner] || OWNER_COLOR["Founder / PMO"]}`}>{k.owner}</span></div>
                ))}</div>
              </div>
            ))}
          </div>
        </div>
        {/* Milestones */}
        <div className="flex flex-wrap gap-2">
          {(pmo.milestones || []).map((m, i) => <div key={i} className="rounded-full border border-indigo-200 bg-indigo-50 text-indigo-700 text-xs px-3 py-1">🚩 {m.name} <span className="text-indigo-400">({m.sprint})</span></div>)}
        </div>
        {/* Sprint board */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 mb-2">🏃 Sprint Board <span className="font-normal text-slate-400">· click a task to advance its status</span></h3>
          <div className="flex gap-3 overflow-x-auto pb-3">
            {(pmo.sprints || []).map((s) => (
              <div key={s.id} className="shrink-0 w-72 rounded-2xl border border-slate-200 bg-white">
                <div className="px-3 py-2 border-b border-slate-100 bg-slate-50 rounded-t-2xl">
                  <div className="text-sm font-bold text-slate-900">{s.name} <span className="text-xs font-normal text-slate-400">· {s.window}</span></div>
                  <div className="text-[11px] text-indigo-600 truncate">{s.goal}</div>
                </div>
                <div className="p-2 space-y-2 min-h-[60px]">
                  {bySprint(s.id).map((t) => { const stt = STATUS[st(t)]; return (
                    <button key={t.id} onClick={() => cycle(t)} className="w-full text-left rounded-xl border border-slate-200 bg-white p-2.5 hover:border-indigo-300 transition">
                      <div className="flex items-start gap-1.5"><span className={`mt-1 h-2 w-2 rounded-full shrink-0 ${PRIO_DOT[t.priority] || PRIO_DOT.Normal}`} /><span className={`text-xs ${st(t) === "done" ? "line-through text-slate-400" : "text-slate-800"}`}>{t.title}</span></div>
                      <div className="flex items-center justify-between mt-1.5">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${OWNER_COLOR[t.owner] || OWNER_COLOR["Founder / PMO"]}`}>{t.owner}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${stt.cls}`}>{stt.label}</span>
                      </div>
                      {t.depends_on?.length > 0 && <div className="text-[10px] text-slate-400 mt-1">↳ after {t.depends_on.join(", ")}</div>}
                    </button>
                  ); })}
                  {bySprint(s.id).length === 0 && <div className="text-[11px] text-slate-300 text-center py-2">—</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ================= Engagement report ================= */
function EngagementReport({ e }) {
  const live = (e.engine || "").startsWith("groq");
  const [board, setBoard] = useState(false);
  const [pmo, setPmo] = useState(null);
  const [loadingPmo, setLoadingPmo] = useState(false);
  async function genPmo() {
    setLoadingPmo(true);
    try { const r = await fetch("/api/pmo", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(e) }); const d = await r.json(); if (!d.error) setPmo(d); } catch { /* noop */ }
    setLoadingPmo(false);
  }
  return (
    <>
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="bg-gradient-to-r from-indigo-600 to-violet-600 text-white px-6 md:px-8 py-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs text-white/80 uppercase tracking-wide">{e.mode === "startup" ? "Startup engagement" : "Existing-business engagement"} · {e.sector_name}</div>
            <h2 className="text-2xl md:text-3xl font-extrabold mt-0.5">Consulting Report</h2>
          </div>
          <div className="flex gap-2 shrink-0">
            <button onClick={genPmo} className="rounded-lg bg-white text-violet-700 font-semibold text-xs px-3 py-1.5 hover:bg-violet-50 disabled:opacity-60" disabled={loadingPmo}>{loadingPmo ? "Building…" : "🗂 PM workspace"}</button>
            <button onClick={() => setBoard(true)} className="rounded-lg bg-white text-indigo-700 font-semibold text-xs px-3 py-1.5 hover:bg-indigo-50">📑 Board pack</button>
            <button onClick={() => window.print()} className="rounded-lg bg-white/15 hover:bg-white/25 text-xs px-3 py-1.5">Print / PDF</button>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5 mt-3">
          <Chip cls={live ? "bg-emerald-400/25 text-white border-emerald-200/40" : "bg-white/15 text-white border-white/25"}>{live ? "🟢 Live LLM synthesis" : "⚙️ Deterministic engine"}</Chip>
          <Chip cls="bg-white/15 text-white border-white/25">🔎 {(e.sources || []).length} open sources</Chip>
          <Chip cls="bg-white/15 text-white border-white/25">🧠 recalled {e.recall?.used || 0}/{e.recall?.total_memory || 0}</Chip>
          {e.learned && <Chip cls="bg-white/15 text-white border-white/25">💾 learned</Chip>}
          {e.playbook_link && <a href={e.playbook_link} className="text-[11px] px-2 py-0.5 rounded-full bg-white/15 border border-white/25 hover:bg-white/25">📚 full playbook →</a>}
        </div>
      </div>
      <div className="p-6 md:p-8 space-y-7">
        {e.scorecard && <Scorecard sc={e.scorecard} />}
        {(e.benchmark || []).length > 0 && (
          <Section id="bench" icon="📐" title="Benchmark vs Industry" sub="Your numbers against sector / India-MSME bands — green healthy, amber watch, red critical">
            <div className="grid sm:grid-cols-2 gap-x-6 gap-y-4">{e.benchmark.map((g, i) => <BenchGauge key={i} g={g} />)}</div>
          </Section>
        )}
        <Section id="diag" icon="🩺" title="Diagnosis"><p className="text-sm text-slate-700 leading-relaxed">{e.diagnosis}</p></Section>
        {e.swot && <Section id="swot" icon="🧭" title="SWOT Analysis" sub="Auto-synthesised from your scorecard, benchmarks, risks and sector playbook"><Swot s={e.swot} /></Section>}
        <Section id="recs" icon="🎯" title="Tailored Recommendations">
          <div className="space-y-2.5">{(e.tailored_recommendations || []).map((r, i) => (
            <Card key={i}><div className="flex items-center justify-between gap-2"><div className="font-semibold text-slate-900 text-sm">{r.title}</div>{r.priority && <Chip cls={SEV[r.priority]}>{r.priority}</Chip>}</div>
              {r.why && <div className="text-xs text-slate-500 mt-1"><b>Why:</b> {r.why}</div>}{r.how && <div className="text-xs text-slate-600 mt-0.5"><b>How:</b> {r.how}</div>}</Card>))}</div>
        </Section>
        {(e.quick_wins || []).length > 0 && <Section id="qw" icon="⚡" title="Quick Wins (this month)"><ul className="space-y-1.5">{e.quick_wins.map((w, i) => <li key={i} className="text-sm text-slate-700 flex gap-2"><span className="text-emerald-600">✓</span>{w}</li>)}</ul></Section>}
        <div className="grid md:grid-cols-2 gap-6">
          <Section id="risks" icon="⚠️" title="Risks"><div className="space-y-2">{(e.risks || []).map((r, i) => (<Card key={i}><div className="flex items-center justify-between gap-2"><div className="text-sm text-slate-800">{r.risk}</div><Chip cls={SEV[r.severity]}>{r.severity}</Chip></div>{r.control && <div className="text-xs text-slate-500 mt-1">{r.control}</div>}</Card>))}</div></Section>
          <Section id="kpis" icon="📊" title="KPIs to hit"><div className="space-y-2">{(e.kpis || []).map((k, i) => (<Card key={i}><div className="flex items-center justify-between gap-2"><div className="text-sm font-medium text-slate-800">{k.kpi}</div><span className="text-xs font-semibold text-emerald-700">{k.target}</span></div>{k.why && <div className="text-xs text-slate-500 mt-0.5">{k.why}</div>}</Card>))}</div></Section>
        </div>
        <Section id="plan" icon="🗓️" title="90-Day Action Plan"><div className="grid md:grid-cols-3 gap-3">{(e.action_plan_90day || []).map((p, i) => (<div key={i} className="rounded-xl border border-slate-200 bg-white p-4"><div className="font-semibold text-indigo-700 text-sm mb-1.5">{p.phase}</div><ul className="text-xs text-slate-600 space-y-1">{(p.steps || []).map((s, j) => <li key={j} className="flex gap-1.5"><span className="text-slate-300">•</span>{s}</li>)}</ul></div>))}</div></Section>
        {(e.opportunities || []).length > 0 && <Section id="opps" icon="🚀" title="Growth Opportunities"><div className="flex flex-wrap gap-2">{e.opportunities.map((o, i) => <Chip key={i} cls="bg-indigo-50 text-indigo-700 border-indigo-200">{o}</Chip>)}</div></Section>}
        {(e.sources || []).length > 0 && <Section id="src" icon="🔎" title="Open-Source Research Used"><div className="space-y-1.5">{e.sources.map((s, i) => (<div key={i} className="text-xs text-slate-500"><span className="px-1.5 rounded bg-slate-100 text-slate-600 mr-1">{s.source}</span>{s.url ? <a href={s.url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">{s.title}</a> : <b className="text-slate-700">{s.title}</b>}{s.snippet && <span> — {s.snippet}</span>}</div>))}</div></Section>}
        {(e.citations || []).length > 0 && <Section id="cite" icon="🏛️" title="Statutory Citations"><div className="space-y-1">{e.citations.map((c, i) => (<div key={i} className="text-xs text-slate-500 flex items-start gap-2"><span className={`px-1.5 rounded ${CITE[c.tier] || ""}`}>{c.tier}</span><span><b className="text-slate-700">{c.title}</b>{c.ref ? ` — ${c.ref}` : ""}</span></div>))}</div></Section>}
        {(e.recall?.notes || []).length > 0 && <Section id="mem" icon="🧠" title="What the brain remembered"><ul className="space-y-1">{e.recall.notes.map((n, i) => <li key={i} className="text-xs text-violet-700">• {n}</li>)}</ul></Section>}
      </div>
    </div>
    {board && <BoardPack e={e} onClose={() => setBoard(false)} />}
    {pmo && <PmoBoard pmo={pmo} sector={e.sector_name} onClose={() => setPmo(null)} />}
    </>
  );
}

/* ================= Workflow infographic ================= */
const FLOW_PALETTE = [
  { ring: "from-indigo-500 to-violet-500",  card: "bg-indigo-50 border-indigo-200 text-indigo-900",   arrow: "text-indigo-400" },
  { ring: "from-sky-500 to-cyan-500",       card: "bg-sky-50 border-sky-200 text-sky-900",            arrow: "text-sky-400" },
  { ring: "from-emerald-500 to-teal-500",   card: "bg-emerald-50 border-emerald-200 text-emerald-900", arrow: "text-emerald-400" },
  { ring: "from-amber-500 to-orange-500",   card: "bg-amber-50 border-amber-200 text-amber-900",      arrow: "text-amber-400" },
  { ring: "from-rose-500 to-pink-500",      card: "bg-rose-50 border-rose-200 text-rose-900",         arrow: "text-rose-400" },
  { ring: "from-fuchsia-500 to-purple-500", card: "bg-fuchsia-50 border-fuchsia-200 text-fuchsia-900", arrow: "text-fuchsia-400" },
  { ring: "from-teal-500 to-green-500",     card: "bg-teal-50 border-teal-200 text-teal-900",         arrow: "text-teal-400" },
  { ring: "from-blue-500 to-indigo-500",    card: "bg-blue-50 border-blue-200 text-blue-900",         arrow: "text-blue-400" },
];
function stageIcon(label) {
  const t = (label || "").toLowerCase();
  const map = [
    [["plan", "assort", "categor", "design", "develop", "r&d", "menu", "strateg", "forecast"], "🧭"],
    [["procure", "purchas", "sourc", "vendor", "supplier", "inbound", "import", "raw", "indent"], "📥"],
    [["manufactur", "produc", "make", "assembl", "process", "fabricat", "cook", "prep", "build"], "🏭"],
    [["quality", "qc", "inspect", "compliance", "test", "grading", "audit"], "✅"],
    [["store", "warehous", "stock", "invent", "putaway", "cold"], "🏬"],
    [["replenish", "distribut", "dispatch", "deliver", "logist", "transport", "ship", "route", "last mile", "fulfil"], "🚚"],
    [["sell", "sale", "pos", "checkout", "billing", "order", "retail", "counter", "booking"], "🛒"],
    [["market", "demand", "lead", "acqui", "promot", "brand", "gtm", "outreach", "campaign"], "📣"],
    [["customer", "crm", "loyal", "retention", "support", "service", "feedback", "onboard", "handover"], "🤝"],
    [["collect", "payment", "receivable", "cash", "invoice", "reconcil", "settle"], "💰"],
    [["return", "reverse", "expiry", "claim", "refund", "after"], "↩️"],
  ];
  for (const [kws, icon] of map) if (kws.some((k) => t.includes(k))) return icon;
  return "🔹";
}
function WorkflowInfographic({ stages }) {
  const s = stages || [];
  return (
    <div>
      <div className="flex flex-wrap items-start gap-y-5">
        {s.map((stage, i) => {
          const c = FLOW_PALETTE[i % FLOW_PALETTE.length];
          return (
            <div key={i} className="flex items-start">
              <div className="flex flex-col items-center w-[124px] sm:w-[140px]">
                <div className={`h-16 w-16 rounded-2xl bg-gradient-to-br ${c.ring} text-white grid place-items-center shadow-md relative`}>
                  <span className="text-2xl">{stageIcon(stage)}</span>
                  <span className="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-white text-slate-700 text-[11px] font-extrabold grid place-items-center shadow border border-slate-200">{i + 1}</span>
                </div>
                <div className={`mt-2.5 rounded-xl border px-2.5 py-2 text-center text-[11px] font-semibold leading-snug ${c.card} w-full min-h-[52px] flex items-center justify-center`}>{stage}</div>
              </div>
              {i < s.length - 1 && (
                <div className={`grid place-items-center h-16 px-0.5 sm:px-1 ${c.arrow}`} aria-hidden>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div className="flex items-center gap-2 mt-4 text-[11px] text-slate-400">
        <span className="h-2 w-6 rounded-full bg-gradient-to-r from-indigo-400 via-emerald-400 to-rose-400" />
        Value flows start → finish. Each stage is a control point where margin, time and quality are won or lost.
      </div>
    </div>
  );
}

/* ================= Playbook encyclopedia ================= */
function Encyclopedia({ pb, onClose, onRun }) {
  const t = pb.tier || 3; const st = TIER[t] || TIER[3];
  const Col = ({ title, items, dot }) => (
    <div><div className="text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">{title}</div><ul className="space-y-1.5">{(items || []).map((it, i) => <li key={i} className="text-xs text-slate-700 flex gap-1.5"><span className={`mt-1.5 h-1.5 w-1.5 rounded-full shrink-0 ${dot}`} />{it}</li>)}</ul></div>
  );
  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className={`bg-gradient-to-r ${st.grad} text-white px-6 md:px-8 py-7`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-2xl bg-white/15 grid place-items-center text-3xl">{pb.icon}</div>
            <div><div className="text-xs text-white/80">{pb.tier_label}</div><h2 className="text-2xl md:text-3xl font-extrabold">{pb.name}</h2><p className="text-white/90 text-sm mt-1 max-w-3xl">{pb.one_liner}</p></div>
          </div>
          <div className="flex gap-2 shrink-0">
            {onRun && <button onClick={onRun} className="rounded-lg bg-white text-indigo-700 font-semibold text-xs px-3 py-1.5 hover:bg-indigo-50">▶ Run as engagement</button>}
            <button onClick={() => window.print()} className="rounded-lg bg-white/15 hover:bg-white/25 text-xs px-3 py-1.5">Print / PDF</button>
            <button onClick={onClose} className="rounded-lg bg-white/15 hover:bg-white/25 text-xs px-3 py-1.5">← All sectors</button>
          </div>
        </div>
      </div>

      {/* section nav */}
      <nav className="flex flex-wrap gap-1.5 px-6 md:px-8 py-3 border-b border-slate-200 bg-white/95 backdrop-blur sticky top-0 z-10">
        {[["flow","🔗 Workflow"],["fix","🛠️ Bottlenecks→Solutions"],["method","📐 Methodologies"],["model","🧩 Model"],["dept","🏛️ Org"],["kpi","📊 KPIs"],["profit","💰 Economics"],["growth","🚀 Growth"],["maturity","📶 Maturity"],["cite","🏛️ Compliance"]].map(([id, label]) => (
          <a key={id} href={`#${id}`} className="text-[11px] px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 hover:bg-indigo-600 hover:text-white transition">{label}</a>
        ))}
      </nav>

      <div className="p-6 md:p-8 space-y-8">
        {/* End-to-end workflow */}
        <Section id="flow" icon="🔗" title="End-to-End Workflow" sub="How value flows through the business, stage by stage">
          <WorkflowInfographic stages={pb.workflow_architecture?.value_chain} />
          <div className="grid md:grid-cols-2 gap-3 mt-6">
            {(pb.workflow_architecture?.core_processes || []).map((p, i) => (<Card key={i}><div className="font-semibold text-slate-900 text-sm">{p.process}</div><div className="text-xs text-slate-500 mt-1">{p.description}</div></Card>))}
          </div>
        </Section>

        {/* Bottleneck -> Solution (centerpiece) */}
        <Section id="fix" icon="🛠️" title="Bottlenecks → Solutions" sub="Every operational chokepoint, its root cause, and the consulting fix">
          <div className="space-y-3">
            {(pb.bottleneck_solutions || []).map((b, i) => (
              <div key={i} className="grid md:grid-cols-[1fr_auto_1fr] gap-3 items-stretch">
                <div className="rounded-xl border border-rose-200 bg-rose-50 p-3.5">
                  <div className="text-[10px] font-bold text-rose-500 uppercase">Bottleneck</div>
                  <div className="font-semibold text-rose-900 text-sm">{b.bottleneck}</div>
                  <div className="text-xs text-rose-700/80 mt-1"><b>Symptom:</b> {b.symptom}</div>
                  <div className="text-xs text-rose-700/80"><b>Impact:</b> {b.impact}</div>
                  <div className="text-xs text-rose-700/80"><b>Root cause:</b> {b.root_cause}</div>
                </div>
                <div className="hidden md:grid place-items-center text-2xl text-emerald-400">→</div>
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3.5">
                  <div className="text-[10px] font-bold text-emerald-600 uppercase">Solution</div>
                  <ul className="text-xs text-emerald-900 space-y-1 mt-0.5">{(b.solution_steps || []).map((s, j) => <li key={j} className="flex gap-1.5"><span className="text-emerald-500">✓</span>{s}</li>)}</ul>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {(b.methodologies || []).map((m) => <Chip key={m.key} cls="bg-white text-emerald-700 border-emerald-200">{m.icon} {m.name}</Chip>)}
                    {b.agent && <a href={`/advisor?agent=${b.agent}`} className="text-[11px] px-2 py-0.5 rounded-full bg-violet-100 text-violet-700 border border-violet-200 hover:bg-violet-200">🤖 {b.agent}</a>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Methodologies */}
        <Section id="method" icon="📐" title="Methodologies Applied" sub="The operational-excellence toolkit this sector demands">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {(pb.methodologies || []).map((m) => (<Card key={m.key}><div className="text-sm font-semibold text-slate-900">{m.icon} {m.name}</div><div className="text-xs text-slate-500 mt-1">{m.principle}</div></Card>))}
          </div>
          <div className="mt-4"><div className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">Sector consulting frameworks</div>
            <div className="grid md:grid-cols-2 gap-3">{(pb.consulting_frameworks || []).map((f, i) => (<Card key={i}><div className="font-semibold text-indigo-700 text-sm">{f.framework}</div><div className="text-xs text-slate-500 mt-1">{f.use}</div></Card>))}</div></div>
        </Section>

        {/* Operating model */}
        <Section id="model" icon="🧩" title="Operating Model">
          <p className="text-sm text-slate-700 mb-4">{pb.operating_model?.summary}</p>
          <div className="grid md:grid-cols-3 gap-5">
            <Col title="Revenue streams" items={pb.operating_model?.revenue_streams} dot="bg-emerald-500" />
            <Col title="Cost structure" items={pb.operating_model?.cost_structure} dot="bg-rose-500" />
            <Col title="Value drivers" items={pb.operating_model?.value_drivers} dot="bg-indigo-500" />
          </div>
        </Section>

        {/* Org */}
        <Section id="dept" icon="🏛️" title="Department Structure">
          <div className="grid md:grid-cols-2 gap-3">{(pb.department_structure || []).map((d, i) => (<Card key={i}><div className="font-semibold text-slate-900 text-sm">{d.dept}</div><div className="text-xs text-slate-500 mt-1">{d.mandate}</div><div className="flex flex-wrap gap-1 mt-2">{(d.key_roles || []).map((r, j) => <Chip key={j}>{r}</Chip>)}</div></Card>))}</div>
        </Section>

        {/* KPIs */}
        <Section id="kpi" icon="📊" title="KPI Dashboard">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {(pb.kpi_structure || []).map((k, i) => (
              <div key={i} className="rounded-xl border border-slate-200 bg-white p-3.5">
                <div className="text-sm font-semibold text-slate-900">{k.kpi}</div>
                <div className="text-[11px] text-slate-400 mb-2">{k.definition}</div>
                <div className="flex gap-1 text-[10px]"><span className="flex-1 text-center py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">{k.healthy}</span><span className="flex-1 text-center py-1 rounded bg-amber-50 text-amber-700 border border-amber-200">{k.watch}</span><span className="flex-1 text-center py-1 rounded bg-rose-50 text-rose-700 border border-rose-200">{k.critical}</span></div>
              </div>
            ))}
          </div>
        </Section>

        {/* Economics */}
        <Section id="profit" icon="💰" title="Profitability & Unit Economics (₹)">
          <div className="grid sm:grid-cols-2 gap-3 mb-4">
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4"><div className="text-xs text-emerald-600">Typical gross margin</div><div className="text-2xl font-extrabold text-emerald-700">{pb.profitability_analysis?.typical_gross_margin}</div></div>
            <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-4"><div className="text-xs text-indigo-600">Typical net margin</div><div className="text-2xl font-extrabold text-indigo-700">{pb.profitability_analysis?.typical_net_margin}</div></div>
          </div>
          <Col title="Unit economics" items={pb.profitability_analysis?.unit_economics} dot="bg-slate-400" />
          <p className="text-xs text-slate-500 mt-3"><b>Working capital:</b> {pb.profitability_analysis?.working_capital_notes}</p>
          <div className="mt-3"><Col title="Profit levers" items={pb.profitability_analysis?.levers} dot="bg-emerald-500" /></div>
        </Section>

        {/* PM + lifecycle */}
        <Section id="pm" icon="🗂️" title="PM Workflows & Lifecycle">
          <div className="space-y-2 mb-5">{(pb.pm_workflows || []).map((p, i) => (<Card key={i}><div className="flex items-center justify-between"><div className="font-semibold text-slate-900 text-sm">{p.initiative}</div><Chip>{p.cadence}</Chip></div><ol className="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">{(p.milestones || []).map((m, j) => <li key={j} className="px-2 py-0.5 rounded bg-white border border-slate-200">{j + 1}. {m}</li>)}</ol></Card>))}</div>
          <div className="grid md:grid-cols-2 gap-3">{(pb.product_service_lifecycle || []).map((p, i) => (<Card key={i}><div className="font-semibold text-slate-900 text-sm">{i + 1}. {p.phase}</div><ul className="mt-1 text-xs text-slate-500 list-disc list-inside space-y-0.5">{(p.key_activities || []).map((a, j) => <li key={j}>{a}</li>)}</ul></Card>))}</div>
        </Section>

        {/* Growth */}
        <Section id="growth" icon="🚀" title="Growth Playbook">
          <div className="grid md:grid-cols-3 gap-3">{(pb.growth_playbook?.stages || []).map((s, i) => (<div key={i} className="rounded-xl border border-slate-200 bg-white p-4"><div className="font-semibold text-slate-900 text-sm">{s.stage}</div><div className="text-xs text-indigo-600 mb-1.5">{s.focus}</div><ul className="text-xs text-slate-500 list-disc list-inside space-y-0.5">{(s.plays || []).map((p, j) => <li key={j}>{p}</li>)}</ul></div>))}</div>
        </Section>

        {/* Maturity ladder */}
        <Section id="maturity" icon="📶" title="Digital Maturity Ladder">
          <div className="relative pl-6">
            <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-gradient-to-b from-slate-200 via-indigo-300 to-emerald-400" />
            <div className="space-y-3">{(pb.digital_maturity_model || []).map((m, i) => (
              <div key={i} className="relative">
                <div className="absolute -left-6 top-1 h-6 w-6 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-white grid place-items-center text-xs font-bold shadow">{m.level}</div>
                <Card><div className="font-semibold text-slate-900 text-sm">{m.name}</div><div className="flex flex-wrap gap-1 mt-1">{(m.signals || []).map((s, j) => <Chip key={j}>{s}</Chip>)}</div><div className="text-xs text-emerald-700 mt-1.5">→ Next: {m.next_step}</div></Card>
              </div>))}</div>
          </div>
        </Section>

        {/* Compliance */}
        <Section id="cite" icon="🏛️" title="Compliance & Citations">
          <div className="mb-3"><div className="text-xs text-slate-500 mb-1.5 uppercase tracking-wide font-semibold">Binding compliance</div><div className="flex flex-wrap gap-1.5">{(pb.compliance_resolved || []).map((c, i) => <Chip key={i} cls={CITE[c.tier] || ""}>{c.title}</Chip>)}</div></div>
          <div className="text-xs text-slate-500 mb-1.5 uppercase tracking-wide font-semibold">Sources</div>
          <div className="space-y-1">{(pb.citations_resolved || []).map((c, i) => (<div key={i} className="text-xs text-slate-500 flex items-start gap-2"><span className={`px-1.5 rounded ${CITE[c.tier] || ""}`}>{c.tier}</span><span><b className="text-slate-700">{c.title}</b>{c.ref ? ` — ${c.ref}` : ""}{c.authority ? ` (${c.authority})` : ""}</span></div>))}</div>
        </Section>
      </div>
    </div>
  );
}
