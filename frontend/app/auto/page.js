"use client";
import { useState } from "react";

// v10: Renders PM plan and PLM execution as beautiful formatted cards,
// not raw JSON dumps. Backend is deterministic so output structure is guaranteed.

const PHASE_COLORS = [
  "from-indigo-500 to-purple-600",
  "from-emerald-500 to-teal-600",
  "from-amber-500 to-orange-600",
  "from-rose-500 to-pink-600",
  "from-sky-500 to-blue-600",
  "from-violet-500 to-fuchsia-600",
  "from-lime-500 to-green-600",
  "from-cyan-500 to-blue-500",
];

export default function AutoPage() {
  const [idea, setIdea] = useState("");
  const [step, setStep] = useState("idle");
  const [pmData, setPmData] = useState(null);
  const [plmData, setPlmData] = useState(null);
  const [prototype, setPrototype] = useState(null);
  const [error, setError] = useState("");

  async function runPMStage() {
    if (!idea.trim()) return setError("Please enter a project idea first.");
    setError(""); setPmData(null); setPlmData(null); setPrototype(null);
    setStep("pm_loading");
    try {
      const r = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: "pm", idea }),
      });
      const data = await r.json();
      if (data.error) { setError(data.error); setStep("idle"); return; }
      setPmData(data);
      setStep("pm_done");
    } catch (e) { setError("Network error: " + e.message); setStep("idle"); }
  }

  async function runPLMStage() {
    setError(""); setStep("plm_loading");
    try {
      const r = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: "plm", idea, pm_plan: pmData }),
      });
      const data = await r.json();
      if (data.error) { setError(data.error); setStep("pm_done"); return; }
      setPlmData(data);
      try {
        const pr = await fetch("/api/prototype", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idea }),
        });
        const pd = await pr.json();
        if (pd.html) setPrototype(pd.html);
      } catch (e) { console.warn(e); }
      setStep("plm_done");
    } catch (e) { setError("Network error: " + e.message); setStep("pm_done"); }
  }

  function download(content, filename, type = "text/html") {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  }

  function reset() {
    setIdea(""); setPmData(null); setPlmData(null); setPrototype(null); setError(""); setStep("idle");
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-6xl mx-auto p-6">
        <header className="mb-8">
          <h1 className="text-4xl font-black tracking-tight">📊 PMGuru Autopilot v10</h1>
          <p className="text-slate-600 mt-2">Template-driven PM + PLM. Enter idea → instant consulting-grade plan → approve → full lifecycle execution.</p>
        </header>

        <div className="flex items-center gap-2 mb-6 text-sm flex-wrap">
          <StepBadge done={!!pmData} label="1. Idea" />
          <Chevron />
          <StepBadge done={!!pmData} loading={step === "pm_loading"} label="2. PM Plan" />
          <Chevron />
          <StepBadge done={!!plmData} label="3. Approve" />
          <Chevron />
          <StepBadge done={!!plmData} loading={step === "plm_loading"} label="4. PLM Execute" />
          <Chevron />
          <StepBadge done={!!plmData && !!prototype} label="5. Prototype" />
        </div>

        {step === "idle" && !pmData && (
          <div className="bg-white rounded-2xl shadow-sm border p-6">
            <label className="block text-sm font-semibold text-slate-700 mb-2">Describe your project idea</label>
            <textarea
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              rows={5}
              placeholder="e.g. AI-powered grocery assistant for Indian kirana stores with voice ordering, inventory management, and GST filing..."
              className="w-full p-4 border border-slate-300 rounded-xl text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none"
            />
            <button
              onClick={runPMStage}
              className="mt-4 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg"
            >
              🧠 Generate PM Strategic Plan
            </button>
          </div>
        )}

        {(step === "pm_loading" || step === "plm_loading") && (
          <div className="bg-white rounded-2xl shadow-sm border p-10 text-center">
            <div className="inline-block w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-slate-700 font-semibold">
              {step === "pm_loading" ? "4 PM experts analyzing..." : "8 PLM agents executing..."}
            </p>
            <p className="mt-2 text-xs text-slate-500">Template-driven — this should complete in under 3 seconds.</p>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-rose-50 border border-rose-300 rounded-xl p-4">
            <div className="font-bold text-rose-900 mb-1">❌ Error</div>
            <pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre>
            <button onClick={() => { setError(""); setStep("idle"); }} className="mt-3 px-4 py-2 bg-rose-600 text-white rounded-lg text-sm font-bold">🔄 Try Again</button>
          </div>
        )}

        {pmData && step !== "plm_loading" && (
          <div className="mt-6">
            <PMReport data={pmData} />
            {step === "pm_done" && !plmData && (
              <div className="mt-6 flex gap-3 flex-wrap">
                <button onClick={runPLMStage} className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-lg">
                  ✅ Approve PM Plan & Run PLM Execution
                </button>
                <button onClick={() => download(JSON.stringify(pmData, null, 2), "pm-report.json", "application/json")} className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-bold">
                  📄 Download PM JSON
                </button>
                <button onClick={reset} className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-bold">← Start Over</button>
              </div>
            )}
          </div>
        )}

        {plmData && (
          <div className="mt-6">
            <PLMReport data={plmData} />
            <div className="mt-6 flex gap-3 flex-wrap">
              {prototype && (
                <button onClick={() => download(prototype, "prototype.html")} className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold">
                  🎨 Download Prototype HTML
                </button>
              )}
              <button onClick={() => download(JSON.stringify(plmData, null, 2), "plm-report.json", "application/json")} className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-bold">
                📄 Download PLM JSON
              </button>
              <button onClick={reset} className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-bold">← Start Over</button>
            </div>
            {prototype && (
              <div className="mt-6 bg-white rounded-2xl border shadow-sm overflow-hidden">
                <div className="bg-slate-100 px-4 py-2 text-xs font-bold text-slate-600">🎨 LIVE PROTOTYPE PREVIEW</div>
                <iframe srcDoc={prototype} className="w-full h-[600px] border-0" title="prototype" />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------- Small UI bits ----------
function StepBadge({ done, loading, label }) {
  const base = "px-3 py-1.5 rounded-full text-xs font-bold ";
  if (done) return <div className={base + "bg-emerald-100 text-emerald-700"}>✓ {label}</div>;
  if (loading) return <div className={base + "bg-amber-100 text-amber-800 animate-pulse"}>⏳ {label}</div>;
  return <div className={base + "bg-slate-100 text-slate-500"}>{label}</div>;
}
function Chevron() { return <span className="text-slate-300">→</span>; }

function Section({ title, children, className = "" }) {
  return (
    <div className={"bg-white rounded-2xl shadow-sm border p-6 " + className}>
      <h3 className="text-xs font-black tracking-wider text-indigo-600 uppercase mb-3">{title}</h3>
      {children}
    </div>
  );
}

function StatBox({ label, value, color = "indigo" }) {
  return (
    <div className={`bg-${color}-50 rounded-xl p-4`}>
      <div className={`text-xs font-bold text-${color}-700 uppercase tracking-wide`}>{label}</div>
      <div className="text-2xl font-black text-slate-900 mt-1">{value}</div>
    </div>
  );
}

// ---------- PM REPORT ----------
function PMReport({ data }) {
  const agents = data?.pm_agents || {};
  const cls = data?.classification || {};
  const summary = data?.summary || {};

  const methodAgent = agents["Methodology Expert"];
  const plannerAgent = agents["Project Planner"];
  const riskAgent = agents["Risk & Governance"];
  const stakeAgent = agents["Stakeholder Strategist"];

  return (
    <div className="space-y-5">
      {/* Hero */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-white rounded-3xl p-10 shadow-2xl">
        <div className="text-xs uppercase tracking-[3px] opacity-60">PM STRATEGIC REPORT</div>
        <h2 className="text-3xl md:text-4xl font-black mt-2 leading-tight">{data.idea}</h2>
        <div className="mt-4 flex gap-2 flex-wrap">
          <span className="px-3 py-1 rounded-full bg-white/10 text-xs font-bold">{cls.industry}</span>
          <span className="px-3 py-1 rounded-full bg-white/10 text-xs font-bold">{cls.complexity?.replace("_", " ")} complexity</span>
          <span className="px-3 py-1 rounded-full bg-emerald-500/30 text-xs font-bold">{summary.ok}/{summary.total} agents</span>
        </div>
      </div>

      {/* Methodology */}
      {methodAgent?.data && (
        <div className="bg-white rounded-2xl shadow-xl p-8 border-l-8 border-indigo-600">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-4xl">{methodAgent.icon}</span>
            <div>
              <div className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Methodology Recommendation</div>
              <div className="text-xs text-slate-500">{methodAgent.role}</div>
            </div>
          </div>
          <div className="flex items-baseline gap-4 flex-wrap">
            <h2 className="text-5xl font-black text-slate-900">{methodAgent.data.recommended_method}</h2>
            <span className="text-xs bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full font-bold">{methodAgent.data.confidence} Confidence</span>
          </div>
          <p className="text-slate-700 mt-4 text-sm border-l-4 border-slate-200 pl-4 italic">{methodAgent.data.reasoning}</p>

          {methodAgent.data.method_details && (
            <div className="grid md:grid-cols-2 gap-3 mt-6">
              <div className="p-4 bg-indigo-50 rounded-xl">
                <div className="text-xs font-bold text-indigo-700 uppercase mb-2">Roles</div>
                <ul className="text-sm text-slate-700 space-y-1">
                  {methodAgent.data.method_details.roles?.map((r, i) => <li key={i}>• {r}</li>)}
                </ul>
              </div>
              <div className="p-4 bg-purple-50 rounded-xl">
                <div className="text-xs font-bold text-purple-700 uppercase mb-2">Ceremonies</div>
                <ul className="text-sm text-slate-700 space-y-1">
                  {methodAgent.data.method_details.ceremonies?.map((c, i) => <li key={i}>• {c}</li>)}
                </ul>
              </div>
              <div className="p-4 bg-emerald-50 rounded-xl">
                <div className="text-xs font-bold text-emerald-700 uppercase mb-2">Artifacts</div>
                <ul className="text-sm text-slate-700 space-y-1">
                  {methodAgent.data.method_details.artifacts?.map((a, i) => <li key={i}>• {a}</li>)}
                </ul>
              </div>
              <div className="p-4 bg-amber-50 rounded-xl">
                <div className="text-xs font-bold text-amber-700 uppercase mb-2">Cadence</div>
                <p className="text-sm text-slate-700">{methodAgent.data.method_details.cadence}</p>
              </div>
            </div>
          )}

          {methodAgent.data.why_not_others && (
            <div className="mt-6">
              <div className="text-xs font-bold text-rose-700 uppercase mb-2">Why Not Other Methodologies</div>
              <div className="space-y-2">
                {methodAgent.data.why_not_others.map((w, i) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <span className="font-bold text-slate-900 whitespace-nowrap">✗ {w.method}:</span>
                    <span className="text-slate-600">{w.reason}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {methodAgent.data.tool_recommendation && (
            <div className="mt-6 bg-gradient-to-br from-slate-900 to-slate-700 text-white rounded-2xl p-6">
              <div className="text-xs font-bold uppercase tracking-wider opacity-60 mb-1">Recommended PM Tool</div>
              <div className="text-3xl font-black">{methodAgent.data.tool_recommendation.primary}</div>
              <p className="text-sm opacity-80 mt-2">{methodAgent.data.tool_recommendation.reason}</p>
              <div className="mt-3 text-xs opacity-60">Alternatives: {methodAgent.data.tool_recommendation.alternatives?.join(", ")}</div>
            </div>
          )}
        </div>
      )}

      {/* Project Plan */}
      {plannerAgent?.data && (
        <Section title={`${plannerAgent.icon} Project Plan — ${plannerAgent.role}`}>
          <p className="text-sm text-slate-700 mb-4">{plannerAgent.data.executive_summary}</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <StatBox label="Timeline" value={`${plannerAgent.data.timeline_weeks} weeks`} color="indigo" />
            <StatBox label="Team Size" value={plannerAgent.data.team_composition?.length || 0} color="purple" />
            <StatBox label="Phases" value={plannerAgent.data.phases?.length || 0} color="emerald" />
            <StatBox label="Total Budget" value={`$${(plannerAgent.data.budget_breakdown?.total || 0).toLocaleString()}`} color="amber" />
          </div>

          {plannerAgent.data.phases && (
            <div className="space-y-2 mb-6">
              <div className="text-xs font-bold text-slate-600 uppercase">Phases</div>
              {plannerAgent.data.phases.map((p, i) => (
                <div key={i} className={`rounded-xl p-4 text-white bg-gradient-to-br ${PHASE_COLORS[i % PHASE_COLORS.length]}`}>
                  <div className="flex justify-between items-start">
                    <div className="font-black">{p.name}</div>
                    <div className="text-xs bg-white/20 px-2 py-0.5 rounded">{p.duration_weeks || "Ongoing"} wk</div>
                  </div>
                  <div className="text-xs opacity-90 mt-2"><strong>Activities:</strong> {p.key_activities?.join(" · ")}</div>
                  <div className="text-xs opacity-90 mt-1"><strong>Deliverables:</strong> {p.deliverables?.join(" · ")}</div>
                </div>
              ))}
            </div>
          )}

          {plannerAgent.data.team_composition && (
            <div className="mb-6">
              <div className="text-xs font-bold text-slate-600 uppercase mb-2">Team Composition</div>
              <div className="grid md:grid-cols-2 gap-2">
                {plannerAgent.data.team_composition.map((t, i) => (
                  <div key={i} className="flex justify-between items-center bg-slate-50 rounded-lg p-3 text-sm">
                    <span className="font-bold">{t.role}</span>
                    <span className="text-xs text-slate-500">×{t.count} @ {t.allocation}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {plannerAgent.data.budget_breakdown && (
            <div className="mb-6">
              <div className="text-xs font-bold text-slate-600 uppercase mb-2">Budget Breakdown</div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {["people", "tools", "infrastructure", "contingency"].map(k => (
                  <div key={k} className="bg-slate-50 rounded-lg p-3">
                    <div className="text-xs text-slate-500 uppercase">{k}</div>
                    <div className="text-lg font-black">${plannerAgent.data.budget_breakdown[k]?.toLocaleString()}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {plannerAgent.data.kpis && (
            <div>
              <div className="text-xs font-bold text-slate-600 uppercase mb-2">Success KPIs</div>
              <div className="space-y-1">
                {plannerAgent.data.kpis.map((k, i) => (
                  <div key={i} className="flex justify-between text-sm bg-emerald-50 rounded-lg p-2">
                    <span className="font-bold text-emerald-900">{k.metric}</span>
                    <span className="text-emerald-700">{k.target}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Section>
      )}

      {/* Risk Register */}
      {riskAgent?.data && (
        <Section title={`${riskAgent.icon} Risk Register — ${riskAgent.role}`}>
          <p className="text-sm text-slate-700 mb-4">{riskAgent.data.summary}</p>
          {riskAgent.data.raid_log && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-slate-100 text-left">
                    <th className="p-2 font-bold">ID</th>
                    <th className="p-2 font-bold">Risk</th>
                    <th className="p-2 font-bold text-center">P</th>
                    <th className="p-2 font-bold text-center">I</th>
                    <th className="p-2 font-bold text-center">Score</th>
                    <th className="p-2 font-bold">Mitigation</th>
                    <th className="p-2 font-bold">Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {riskAgent.data.raid_log.map((r, i) => (
                    <tr key={i} className="border-b">
                      <td className="p-2 font-bold">{r.id}</td>
                      <td className="p-2">{r.description}</td>
                      <td className="p-2 text-center">{r.probability}</td>
                      <td className="p-2 text-center">{r.impact}</td>
                      <td className={`p-2 text-center font-bold ${r.score >= 15 ? "text-rose-600" : r.score >= 9 ? "text-amber-600" : "text-emerald-600"}`}>{r.score}</td>
                      <td className="p-2 text-slate-600">{r.mitigation}</td>
                      <td className="p-2 text-slate-500">{r.owner}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>
      )}

      {/* Stakeholders */}
      {stakeAgent?.data && (
        <Section title={`${stakeAgent.icon} Stakeholder Map — ${stakeAgent.role}`}>
          <p className="text-sm text-slate-700 mb-4">{stakeAgent.data.summary}</p>
          <div className="grid md:grid-cols-2 gap-2">
            {stakeAgent.data.stakeholders?.map((s, i) => (
              <div key={i} className="border rounded-lg p-3 text-sm">
                <div className="font-bold text-slate-900">{s.name}</div>
                <div className="text-xs text-slate-500 mt-1">Power: <strong>{s.power}</strong> · Interest: <strong>{s.interest}</strong></div>
                <div className="text-xs text-indigo-700 mt-1">→ {s.strategy}</div>
                <div className="text-xs text-slate-600 mt-1">📡 {s.channel}</div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// ---------- PLM REPORT ----------
function PLMReport({ data }) {
  return (
    <div className="space-y-5">
      <div className="bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-3xl p-8 shadow-2xl">
        <div className="text-xs uppercase tracking-[3px] opacity-70">PLM EXECUTION REPORT</div>
        <h2 className="text-3xl font-black mt-2">{data.idea}</h2>
        <div className="mt-2 text-xs opacity-80">{data.summary?.ok}/{data.summary?.total} phases completed successfully</div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {(data.phases || []).map((p, i) => (
          <div key={p.id} className={`rounded-2xl p-6 text-white shadow-lg bg-gradient-to-br ${PHASE_COLORS[i % PHASE_COLORS.length]}`}>
            <div className="text-xs opacity-80">PHASE {p.id} · {p.duration}</div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl">{p.icon}</span>
              <h3 className="text-xl font-black">{p.name}</h3>
            </div>
            <div className="text-xs opacity-80 mt-1 mb-3">by {p.agent}</div>

            {p.data?.summary && <p className="text-sm bg-black/20 rounded-lg p-3">{p.data.summary}</p>}

            <div className="mt-3 space-y-2 text-xs">
              {p.data?.user_personas && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">User Personas</div>
                  {p.data.user_personas.map((u, j) => <div key={j}>• <strong>{u.name}</strong>: {u.description}</div>)}
                </div>
              )}
              {p.data?.key_insights && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">Key Insights</div>
                  {p.data.key_insights.map((k, j) => <div key={j}>• {k}</div>)}
                </div>
              )}
              {p.data?.solution_concepts && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">Solutions (RICE-scored)</div>
                  {p.data.solution_concepts.map((s, j) => <div key={j}>• <strong>{s.name}</strong> (score: {s.rice?.score})</div>)}
                </div>
              )}
              {p.data?.user_stories && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">User Stories</div>
                  {p.data.user_stories.slice(0, 3).map((s, j) => <div key={j}>• {s.id}: {s.story?.slice(0, 80)}...</div>)}
                </div>
              )}
              {p.data?.user_flows && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">User Flows</div>
                  {p.data.user_flows.map((f, j) => <div key={j}>• {f}</div>)}
                </div>
              )}
              {p.data?.design_principles && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">Design Principles</div>
                  {p.data.design_principles.slice(0, 3).map((d, j) => <div key={j}>• {d}</div>)}
                </div>
              )}
              {p.data?.sprint_plan && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">Sprint Plan</div>
                  {p.data.sprint_plan.map((s, j) => <div key={j}>• Sprint {s.sprint}: {s.goal} ({s.story_points} pts)</div>)}
                </div>
              )}
              {p.data?.test_cases && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">Test Cases</div>
                  {p.data.test_cases.slice(0, 3).map((t, j) => <div key={j}>• {t.id}: {t.scenario}</div>)}
                </div>
              )}
              {p.data?.ci_cd_pipeline && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">CI/CD Pipeline</div>
                  {p.data.ci_cd_pipeline.slice(0, 4).map((c, j) => <div key={j}>• {c}</div>)}
                </div>
              )}
              {p.data?.success_metrics && (
                <div className="bg-black/20 rounded p-2">
                  <div className="font-bold opacity-80 mb-1">Success Metrics</div>
                  {p.data.success_metrics.map((m, j) => <div key={j}>• {m.kpi}: {m.target}</div>)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
