"use client";
import { useState, useEffect, useRef } from "react";

// v12: /plm-cycle - 8-phase product lifecycle with infographic rendering
// Calls /api/pipeline with stage="plm" to get the 8 phases in one shot
// Renders each phase as a rich card with all its sub-data (personas, stories, sprints, etc.)

const PHASE_GRADIENTS = [
  { from: "from-indigo-500", to: "to-purple-600", text: "text-indigo-700", bg: "bg-indigo-50", border: "border-indigo-200" },
  { from: "from-emerald-500", to: "to-teal-600", text: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200" },
  { from: "from-amber-500", to: "to-orange-600", text: "text-amber-700", bg: "bg-amber-50", border: "border-amber-200" },
  { from: "from-rose-500", to: "to-pink-600", text: "text-rose-700", bg: "bg-rose-50", border: "border-rose-200" },
  { from: "from-sky-500", to: "to-blue-600", text: "text-sky-700", bg: "bg-sky-50", border: "border-sky-200" },
  { from: "from-violet-500", to: "to-fuchsia-600", text: "text-violet-700", bg: "bg-violet-50", border: "border-violet-200" },
  { from: "from-lime-500", to: "to-green-600", text: "text-lime-700", bg: "bg-lime-50", border: "border-lime-200" },
  { from: "from-cyan-500", to: "to-blue-500", text: "text-cyan-700", bg: "bg-cyan-50", border: "border-cyan-200" },
];

export default function PlmCyclePage() {
  const [idea, setIdea] = useState("");
  const [phases, setPhases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    const params = new URLSearchParams(window.location.search);
    const ideaParam = params.get("idea") || sessionStorage.getItem("pmguru_pending_idea") || "";
    if (!ideaParam) { setError("No idea provided."); setLoading(false); return; }
    setIdea(ideaParam);
    runPlm(ideaParam);
  }, []);

  async function runPlm(ideaText) {
    try {
      const r = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: "plm", idea: ideaText }),
      });
      const data = await r.json();
      if (data.error) { setError(data.error); setLoading(false); return; }
      setPhases(data.phases || []);
      setLoading(false);
    } catch (e) {
      setError("Network error: " + e.message);
      setLoading(false);
    }
  }

  function downloadPDF() { window.print(); }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <style jsx global>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white !important; }
          .phase-card { page-break-inside: avoid; }
        }
        @page { size: A4; margin: 0.5in; }
      `}</style>

      <div className="no-print sticky top-0 bg-white border-b shadow-sm z-10">
        <div className="max-w-6xl mx-auto p-4 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <a href="/auto" className="text-xs text-slate-500 hover:text-indigo-600">← Back to launcher</a>
            <div className="font-black text-lg mt-0.5">Product Lifecycle Report</div>
          </div>
          {!loading && phases.length > 0 && (
            <button onClick={downloadPDF} className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-bold">
              📥 Download PDF
            </button>
          )}
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-gradient-to-br from-emerald-700 via-teal-700 to-cyan-800 text-white rounded-3xl p-10 mb-6 shadow-xl print:shadow-none">
          <div className="text-xs uppercase tracking-[3px] opacity-60 font-bold">PMGuru Product Lifecycle</div>
          <h1 className="text-4xl font-black mt-4 leading-tight">{idea || "Loading..."}</h1>
          <div className="mt-4 text-sm opacity-90">8-phase product lifecycle plan, generated from idea analysis. Each phase carries deliverables, success criteria, and tactical guidance.</div>
        </div>

        {error && (
          <div className="bg-rose-50 border-2 border-rose-300 rounded-xl p-4 mb-6">
            <pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre>
          </div>
        )}

        {loading && (
          <div className="bg-white rounded-xl p-10 text-center">
            <div className="inline-block w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
            <div className="mt-4 font-bold text-slate-700">Generating product lifecycle plan...</div>
          </div>
        )}

        {/* Journey infographic - phase pills connected */}
        {!loading && phases.length > 0 && (
          <div className="bg-white rounded-2xl border p-6 mb-6 overflow-x-auto print:rounded-none">
            <div className="text-xs font-bold text-slate-600 uppercase mb-4 tracking-wider">The 8-Phase Journey</div>
            <div className="flex items-center gap-2 min-w-[700px]">
              {phases.map((p, i) => (
                <div key={p.id} className="flex items-center flex-1">
                  <div className={`flex-1 rounded-xl p-3 text-white text-center bg-gradient-to-br ${PHASE_GRADIENTS[i].from} ${PHASE_GRADIENTS[i].to}`}>
                    <div className="text-2xl">{p.icon}</div>
                    <div className="text-[10px] opacity-80 mt-1">PHASE {p.id}</div>
                    <div className="text-xs font-black mt-0.5">{p.name}</div>
                  </div>
                  {i < phases.length - 1 && <div className="text-slate-300 text-xl px-1">→</div>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Phase detail cards */}
        <div className="space-y-5">
          {phases.map((p, i) => <PhaseCard key={p.id} phase={p} colors={PHASE_GRADIENTS[i]} />)}
        </div>

        {!loading && phases.length > 0 && (
          <div className="mt-10 pt-6 border-t border-slate-300 text-center text-xs text-slate-500">
            <div>Generated by PMGuru's deterministic PLM engine.</div>
            <div className="mt-1">© {new Date().getFullYear()} PMGuru · Confidential</div>
          </div>
        )}
      </div>
    </div>
  );
}

function PhaseCard({ phase, colors }) {
  const d = phase.data || {};
  return (
    <div className="phase-card bg-white rounded-2xl shadow-sm border overflow-hidden print:rounded-none print:shadow-none print:border">
      <div className={`bg-gradient-to-br ${colors.from} ${colors.to} text-white p-5`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs opacity-70 uppercase tracking-wider">PHASE {phase.id} · {phase.duration}</div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-3xl">{phase.icon}</span>
              <h3 className="text-2xl font-black">{phase.name}</h3>
            </div>
            <div className="text-xs opacity-80 mt-1">Owner: {phase.agent}</div>
          </div>
          <span className="text-xs px-3 py-1 rounded-full bg-white/20 font-bold">{phase.status}</span>
        </div>
      </div>
      <div className="p-6 space-y-4">
        {d.summary && <p className="text-sm text-slate-700 italic border-l-4 border-slate-300 pl-3">{d.summary}</p>}

        {d.problem_statement && (
          <PhaseSection title="Problem Statement" colors={colors}>
            <p className="text-sm">{d.problem_statement}</p>
          </PhaseSection>
        )}

        {d.user_personas && (
          <PhaseSection title="User Personas" colors={colors}>
            <div className="grid md:grid-cols-2 gap-2">
              {d.user_personas.map((u, i) => (
                <div key={i} className={`p-3 rounded-lg border ${colors.bg} ${colors.border}`}>
                  <div className="font-bold text-sm">{u.name}</div>
                  <div className="text-xs text-slate-600 mt-1">{u.description}</div>
                  <div className="text-xs mt-2"><strong className="text-emerald-700">Goals:</strong> {u.goals?.join(", ")}</div>
                  <div className="text-xs"><strong className="text-rose-700">Pain points:</strong> {u.pain_points?.join(", ")}</div>
                </div>
              ))}
            </div>
          </PhaseSection>
        )}

        {d.market_sizing && (
          <PhaseSection title="Market Sizing" colors={colors}>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(d.market_sizing).map(([k, v]) => (
                <div key={k} className={`p-3 ${colors.bg} rounded-lg text-center`}>
                  <div className={`text-[10px] font-bold ${colors.text} uppercase`}>{k}</div>
                  <div className="text-sm mt-1">{v}</div>
                </div>
              ))}
            </div>
          </PhaseSection>
        )}

        {d.key_insights && (
          <PhaseSection title="Key Insights" colors={colors}>
            <ul className="text-sm space-y-1">
              {d.key_insights.map((k, i) => <li key={i}>💡 {k}</li>)}
            </ul>
          </PhaseSection>
        )}

        {d.solution_concepts && (
          <PhaseSection title="Solution Concepts (RICE-prioritized)" colors={colors}>
            <table className="w-full text-xs">
              <thead><tr className="bg-slate-100 text-left"><th className="p-2 font-bold">Concept</th><th className="p-2 font-bold">R</th><th className="p-2 font-bold">I</th><th className="p-2 font-bold">C</th><th className="p-2 font-bold">E</th><th className="p-2 font-bold">Score</th></tr></thead>
              <tbody>
                {d.solution_concepts.map((s, i) => (
                  <tr key={i} className="border-t">
                    <td className="p-2 font-bold">{s.name}</td>
                    <td className="p-2 text-center">{s.rice?.reach}</td>
                    <td className="p-2 text-center">{s.rice?.impact}</td>
                    <td className="p-2 text-center">{s.rice?.confidence}</td>
                    <td className="p-2 text-center">{s.rice?.effort}</td>
                    <td className={`p-2 text-center font-black ${s.rice?.score > 30 ? "text-emerald-700" : "text-amber-700"}`}>{s.rice?.score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {d.mvp_scope && (
              <div className="mt-2 text-xs">
                <strong className="text-emerald-700">MVP scope:</strong> {d.mvp_scope.join(" · ")}
              </div>
            )}
            {d.deferred_to_v2 && (
              <div className="text-xs">
                <strong className="text-amber-700">Deferred to v2:</strong> {d.deferred_to_v2.join(" · ")}
              </div>
            )}
          </PhaseSection>
        )}

        {d.user_stories && (
          <PhaseSection title="User Stories" colors={colors}>
            <div className="space-y-2">
              {d.user_stories.map((s, i) => (
                <div key={i} className={`p-3 ${colors.bg} rounded-lg`}>
                  <div className="text-xs font-bold font-mono text-slate-500">{s.id} · {s.story_points} pts</div>
                  <div className="text-sm font-bold mt-1">{s.story}</div>
                  <div className="text-xs text-slate-600 mt-1">
                    <strong>AC:</strong> {s.acceptance_criteria?.join(" · ")}
                  </div>
                </div>
              ))}
            </div>
          </PhaseSection>
        )}

        {d.user_flows && (
          <PhaseSection title="User Flows" colors={colors}>
            <ul className="text-sm space-y-1">
              {d.user_flows.map((f, i) => <li key={i}>→ {f}</li>)}
            </ul>
          </PhaseSection>
        )}

        {d.wireframe_description && (
          <PhaseSection title="Wireframe Description" colors={colors}>
            <p className="text-sm">{d.wireframe_description}</p>
          </PhaseSection>
        )}

        {d.design_principles && (
          <PhaseSection title="Design Principles" colors={colors}>
            <ul className="text-sm space-y-1">
              {d.design_principles.map((p, i) => <li key={i}>✓ {p}</li>)}
            </ul>
          </PhaseSection>
        )}

        {d.design_system && (
          <PhaseSection title="Design System Tokens" colors={colors}>
            <div className="grid md:grid-cols-2 gap-2 text-xs">
              {Object.entries(d.design_system).map(([k, v]) => (
                <div key={k}><strong className="capitalize">{k}:</strong> {Array.isArray(v) ? v.join(", ") : v}</div>
              ))}
            </div>
          </PhaseSection>
        )}

        {d.sprint_plan && (
          <PhaseSection title="Sprint Plan" colors={colors}>
            <div className="space-y-2">
              {d.sprint_plan.map((s, i) => (
                <div key={i} className="border-l-4 border-indigo-500 pl-3 py-1">
                  <div className="font-bold text-sm">Sprint {s.sprint}: {s.goal}</div>
                  <div className="text-xs text-slate-600">Tasks: {s.tasks?.join(" · ")}</div>
                  <div className="text-xs text-indigo-600 font-bold">{s.story_points} story points</div>
                </div>
              ))}
            </div>
            {d.velocity_forecast && <p className="text-xs italic text-slate-600 mt-2">{d.velocity_forecast}</p>}
          </PhaseSection>
        )}

        {d.tech_stack && (
          <PhaseSection title="Tech Stack" colors={colors}>
            <div className="flex flex-wrap gap-1">
              {d.tech_stack.map((t, i) => (
                <span key={i} className={`text-xs px-2 py-1 rounded ${colors.bg} ${colors.text} font-bold`}>{t}</span>
              ))}
            </div>
          </PhaseSection>
        )}

        {d.test_strategy && (
          <PhaseSection title="Test Strategy" colors={colors}>
            <p className="text-sm">{d.test_strategy}</p>
          </PhaseSection>
        )}

        {d.test_cases && (
          <PhaseSection title="Test Cases" colors={colors}>
            <table className="w-full text-xs">
              <thead><tr className="bg-slate-100 text-left"><th className="p-2 font-bold">ID</th><th className="p-2 font-bold">Scenario</th><th className="p-2 font-bold">Expected</th></tr></thead>
              <tbody>
                {d.test_cases.map((t, i) => (
                  <tr key={i} className="border-t"><td className="p-2 font-mono">{t.id}</td><td className="p-2">{t.scenario}</td><td className="p-2 text-emerald-700">{t.expected}</td></tr>
                ))}
              </tbody>
            </table>
          </PhaseSection>
        )}

        {d.quality_gates && (
          <PhaseSection title="Quality Gates" colors={colors}>
            <ul className="text-sm space-y-1">
              {d.quality_gates.map((q, i) => <li key={i}>🚦 {q}</li>)}
            </ul>
          </PhaseSection>
        )}

        {d.ci_cd_pipeline && (
          <PhaseSection title="CI/CD Pipeline" colors={colors}>
            <div className="space-y-1">
              {d.ci_cd_pipeline.map((step, i) => (
                <div key={i} className={`flex items-center gap-2 p-2 ${colors.bg} rounded text-xs`}>
                  <span className="font-bold w-5 text-center">{i + 1}</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </PhaseSection>
        )}

        {d.infrastructure && (
          <PhaseSection title="Infrastructure" colors={colors}>
            <p className="text-sm">{d.infrastructure}</p>
          </PhaseSection>
        )}

        {d.monitoring && (
          <PhaseSection title="Monitoring & Alerts" colors={colors}>
            <ul className="text-sm space-y-1">
              {d.monitoring.map((m, i) => <li key={i}>📡 {m}</li>)}
            </ul>
          </PhaseSection>
        )}

        {d.rollback_plan && (
          <PhaseSection title="Rollback Plan" colors={colors}>
            <p className="text-sm">{d.rollback_plan}</p>
          </PhaseSection>
        )}

        {d.launch_announcement && (
          <PhaseSection title="Launch Announcement" colors={colors}>
            <div className={`p-4 rounded-lg ${colors.bg}`}>
              <div className="font-black text-lg">{d.launch_announcement.headline}</div>
              <p className="text-sm mt-2">{d.launch_announcement.body}</p>
              <button className={`mt-3 px-4 py-2 bg-gradient-to-r ${colors.from} ${colors.to} text-white rounded-lg text-sm font-bold`}>
                {d.launch_announcement.cta}
              </button>
            </div>
          </PhaseSection>
        )}

        {d.success_metrics && (
          <PhaseSection title="Success Metrics" colors={colors}>
            <div className="grid md:grid-cols-2 gap-2">
              {d.success_metrics.map((m, i) => (
                <div key={i} className={`p-3 ${colors.bg} rounded-lg`}>
                  <div className="font-bold text-sm">{m.kpi}</div>
                  <div className={`text-xs ${colors.text} mt-1`}>Target: {m.target}</div>
                </div>
              ))}
            </div>
          </PhaseSection>
        )}

        {d.feedback_loops && (
          <PhaseSection title="Feedback Loops" colors={colors}>
            <ul className="text-sm space-y-1">
              {d.feedback_loops.map((f, i) => <li key={i}>🔄 {f}</li>)}
            </ul>
          </PhaseSection>
        )}

        {d.recommendations && (
          <PhaseSection title="Recommendations" colors={colors}>
            <ul className="text-sm space-y-1">
              {d.recommendations.map((r, i) => <li key={i}>→ {r}</li>)}
            </ul>
          </PhaseSection>
        )}

        {d.prd_sections && (
          <PhaseSection title="PRD Sections" colors={colors}>
            <div className="flex flex-wrap gap-1">
              {d.prd_sections.map((s, i) => (
                <span key={i} className={`text-xs px-2 py-1 rounded ${colors.bg} ${colors.text} font-bold`}>{s}</span>
              ))}
            </div>
          </PhaseSection>
        )}
      </div>
    </div>
  );
}

function PhaseSection({ title, children, colors }) {
  return (
    <div>
      <div className={`text-[10px] font-bold ${colors.text} uppercase tracking-wider mb-2`}>{title}</div>
      {children}
    </div>
  );
}
