"use client";
import { useState, useEffect } from "react";

// ============================================================
// PMGuru /plm v1 — Product Lifecycle Management report
// Reads the PLM payload from localStorage (generated via /plm/execute)
// and renders all 8 phases as an editorial-style expandable report.
// ============================================================

const PHASE_COLORS = [
  "from-indigo-500 to-indigo-600",
  "from-purple-500 to-purple-600",
  "from-pink-500 to-pink-600",
  "from-rose-500 to-rose-600",
  "from-amber-500 to-amber-600",
  "from-emerald-500 to-emerald-600",
  "from-teal-500 to-teal-600",
  "from-sky-500 to-sky-600",
];

export default function PLMPage() {
  const [plm, setPlm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id") || localStorage.getItem("pmguru_current_plm");
    if (!id) { setLoading(false); return; }
    try {
      const raw = localStorage.getItem(`pmguru_plm_${id}`);
      if (raw) {
        const data = JSON.parse(raw);
        setPlm(data);
        // Expand first phase by default
        if (data.phases?.[0]) setExpanded({ [data.phases[0].id]: true });
      }
    } catch (e) {
      console.error("Failed to load PLM:", e);
    }
    setLoading(false);
  }, []);

  function toggle(id) {
    setExpanded(e => ({ ...e, [id]: !e[id] }));
  }
  function expandAll() {
    const all = {};
    plm.phases?.forEach(p => { all[p.id] = true; });
    setExpanded(all);
  }
  function collapseAll() {
    setExpanded({});
  }
  function exportJSON() {
    const blob = new Blob([JSON.stringify(plm, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `PLM_Report_${(plm._idea || "plan").replace(/\W+/g, "_").slice(0, 40)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  function print() {
    window.print();
  }

  if (loading) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600">Loading PLM report...</div>;
  }
  if (!plm) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">📘</div>
          <h1 className="text-2xl font-black text-slate-900">No PLM report found</h1>
          <p className="text-slate-600 mt-2">Generate one by entering an idea first.</p>
          <a href="/auto" className="inline-block mt-6 px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold">Start on /auto</a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-5xl mx-auto p-6">
        {/* Header */}
        <header className="mb-8 pt-6 print:pt-0">
          <div className="flex items-start justify-between gap-3 flex-wrap mb-4 print:hidden">
            <a href="/auto" className="text-xs text-slate-500 hover:text-indigo-600 underline">← Back to launcher</a>
            <div className="flex gap-2">
              <button onClick={expandAll} className="px-3 py-1.5 bg-white border rounded-lg text-xs font-bold hover:bg-slate-50">Expand all</button>
              <button onClick={collapseAll} className="px-3 py-1.5 bg-white border rounded-lg text-xs font-bold hover:bg-slate-50">Collapse all</button>
              <button onClick={print} className="px-3 py-1.5 bg-white border rounded-lg text-xs font-bold hover:bg-slate-50">🖨️ Print</button>
              <button onClick={exportJSON} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700">📥 Export JSON</button>
            </div>
          </div>

          <div className="inline-block px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-bold mb-3">
            Product Lifecycle Management · 8-Phase Report
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight">{plm._idea || plm.idea}</h1>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold">
              {plm.classification?.method_key || "scrum"}
            </span>
            <span className="px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-bold">
              {plm.classification?.industry}
            </span>
            <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-700 text-xs font-bold">
              {(plm.classification?.complexity || "medium").replace("_", " ")} complexity
            </span>
            <span className="px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-bold">
              {plm.summary?.ok || plm.phases?.length || 0} phases
            </span>
          </div>
        </header>

        {/* Phase navigation rail */}
        <div className="bg-white rounded-2xl border shadow-sm p-4 mb-6 print:hidden">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Phase overview</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {plm.phases?.map((phase, i) => (
              <a
                key={phase.id}
                href={`#phase-${phase.id}`}
                onClick={() => setExpanded(e => ({ ...e, [phase.id]: true }))}
                className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 transition text-sm"
              >
                <span className="text-lg">{phase.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-slate-900 truncate">{phase.name}</div>
                  <div className="text-[10px] text-slate-500">{phase.duration}</div>
                </div>
              </a>
            ))}
          </div>
        </div>

        {/* Phase cards */}
        <div className="space-y-4">
          {plm.phases?.map((phase, i) => {
            const isOpen = !!expanded[phase.id];
            const color = PHASE_COLORS[i % PHASE_COLORS.length];
            return (
              <div key={phase.id} id={`phase-${phase.id}`} className="bg-white rounded-2xl border shadow-sm overflow-hidden">
                <button
                  onClick={() => toggle(phase.id)}
                  className="w-full text-left p-6 hover:bg-slate-50 transition"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center text-2xl shadow-md flex-shrink-0`}>
                      {phase.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-bold text-slate-500">PHASE {phase.id}</span>
                        <span className="text-xs text-slate-400">·</span>
                        <span className="text-xs text-slate-500">{phase.agent}</span>
                        <span className="text-xs text-slate-400">·</span>
                        <span className="text-xs text-slate-500">{phase.duration}</span>
                      </div>
                      <h2 className="text-2xl font-black text-slate-900 mt-1">{phase.name}</h2>
                      {phase.data?.summary && (
                        <p className="text-sm text-slate-600 mt-2 line-clamp-2">{phase.data.summary}</p>
                      )}
                    </div>
                    <div className="flex-shrink-0 text-2xl text-slate-400">
                      {isOpen ? "−" : "+"}
                    </div>
                  </div>
                </button>

                {isOpen && (
                  <div className="px-6 pb-6 pt-2 border-t border-slate-100">
                    <PhaseDetails phase={phase} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="mt-12 mb-8 text-center text-xs text-slate-400 print:hidden">
          PMGuru · PLM Report · Generated {plm._created_at ? new Date(plm._created_at).toLocaleString() : "recently"}
        </div>
      </div>

      <style jsx global>{`
        @media print {
          button { display: none !important; }
          .print\\:hidden { display: none !important; }
          .print\\:pt-0 { padding-top: 0 !important; }
          body { background: white !important; }
        }
      `}</style>
    </div>
  );
}

// ============================================================
// Phase-specific detail renderers
// ============================================================
function PhaseDetails({ phase }) {
  const d = phase.data;
  if (!d) return <div className="text-sm text-slate-500 italic">No details available.</div>;
  if (phase.status === "error") {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-4">
        <div className="font-bold text-rose-900 text-sm">Phase error</div>
        <p className="text-xs text-rose-700 mt-1">{phase.error || d.summary}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 mt-3">
      {d.summary && (
        <p className="text-sm text-slate-700 italic border-l-2 border-indigo-300 pl-3">{d.summary}</p>
      )}

      {/* DISCOVERY */}
      {d.problem_statement && (
        <Section title="Problem Statement">
          <p className="text-sm text-slate-700">{d.problem_statement}</p>
        </Section>
      )}
      {d.user_personas && (
        <Section title="User Personas">
          <div className="grid md:grid-cols-2 gap-3">
            {d.user_personas.map((p, i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-4">
                <div className="font-bold text-slate-900">{p.name}</div>
                <div className="text-xs text-slate-600 mt-1">{p.description}</div>
                {p.goals && (
                  <div className="mt-3">
                    <div className="text-[10px] font-bold uppercase text-emerald-700 mb-1">Goals</div>
                    <ul className="text-xs text-slate-700 space-y-0.5">
                      {p.goals.map((g, j) => <li key={j}>✓ {g}</li>)}
                    </ul>
                  </div>
                )}
                {p.pain_points && (
                  <div className="mt-2">
                    <div className="text-[10px] font-bold uppercase text-rose-700 mb-1">Pain Points</div>
                    <ul className="text-xs text-slate-700 space-y-0.5">
                      {p.pain_points.map((pp, j) => <li key={j}>✗ {pp}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
      {d.market_sizing && (
        <Section title="Market Sizing">
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(d.market_sizing).map(([k, v]) => (
              <div key={k} className="bg-indigo-50 rounded-lg p-3 text-center">
                <div className="text-xs font-bold text-indigo-700 uppercase">{k}</div>
                <div className="text-xs text-slate-700 mt-1">{v}</div>
              </div>
            ))}
          </div>
        </Section>
      )}
      {d.key_insights && (
        <Section title="Key Insights">
          <ul className="space-y-1">
            {d.key_insights.map((k, i) => <li key={i} className="text-sm text-slate-700">💡 {k}</li>)}
          </ul>
        </Section>
      )}

      {/* IDEATION */}
      {d.solution_concepts && (
        <Section title="Solution Concepts — RICE Prioritized">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-600">
                  <th className="p-2 font-bold">Concept</th>
                  <th className="p-2 font-bold text-center">R</th>
                  <th className="p-2 font-bold text-center">I</th>
                  <th className="p-2 font-bold text-center">C</th>
                  <th className="p-2 font-bold text-center">E</th>
                  <th className="p-2 font-bold text-center">Score</th>
                </tr>
              </thead>
              <tbody>
                {d.solution_concepts.map((c, i) => (
                  <tr key={i} className="border-t">
                    <td className="p-2">
                      <div className="font-bold text-slate-900">{c.name}</div>
                      <div className="text-xs text-slate-500">{c.description}</div>
                    </td>
                    <td className="p-2 text-center text-xs">{c.rice?.reach}</td>
                    <td className="p-2 text-center text-xs">{c.rice?.impact}</td>
                    <td className="p-2 text-center text-xs">{c.rice?.confidence}</td>
                    <td className="p-2 text-center text-xs">{c.rice?.effort}</td>
                    <td className="p-2 text-center">
                      <span className="px-2 py-1 rounded bg-indigo-100 text-indigo-700 font-bold text-xs">{c.rice?.score}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}
      {d.mvp_scope && (
        <Section title="MVP Scope">
          <div className="flex flex-wrap gap-2">
            {d.mvp_scope.map((s, i) => (
              <span key={i} className="px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">✓ {s}</span>
            ))}
          </div>
          {d.deferred_to_v2 && (
            <div className="mt-3">
              <div className="text-xs font-bold text-slate-500 uppercase mb-2">Deferred to v2</div>
              <div className="flex flex-wrap gap-2">
                {d.deferred_to_v2.map((s, i) => (
                  <span key={i} className="px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-xs">{s}</span>
                ))}
              </div>
            </div>
          )}
        </Section>
      )}

      {/* DEFINITION */}
      {d.user_stories && (
        <Section title="User Stories">
          <div className="space-y-2">
            {d.user_stories.map((s, i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <span className="text-[10px] font-mono text-slate-400 flex-shrink-0 mt-1">{s.id}</span>
                  <div className="flex-1">
                    <div className="text-sm text-slate-900">{s.story}</div>
                    {s.acceptance_criteria && (
                      <ul className="mt-2 space-y-0.5">
                        {s.acceptance_criteria.map((a, j) => (
                          <li key={j} className="text-xs text-slate-600">✓ {a}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <span className="text-xs font-bold text-indigo-600 flex-shrink-0">{s.story_points}pt</span>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
      {d.prd_sections && (
        <Section title="PRD Sections">
          <div className="flex flex-wrap gap-2">
            {d.prd_sections.map((s, i) => (
              <span key={i} className="px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold">{s}</span>
            ))}
          </div>
        </Section>
      )}

      {/* DESIGN */}
      {d.user_flows && (
        <Section title="User Flows">
          <div className="space-y-2">
            {d.user_flows.map((f, i) => (
              <div key={i} className="bg-indigo-50 rounded-lg p-3 text-sm text-slate-700 font-mono text-xs">{f}</div>
            ))}
          </div>
        </Section>
      )}
      {d.wireframe_description && (
        <Section title="Wireframe Description">
          <p className="text-sm text-slate-700">{d.wireframe_description}</p>
        </Section>
      )}
      {d.design_principles && (
        <Section title="Design Principles">
          <ul className="space-y-1">
            {d.design_principles.map((p, i) => <li key={i} className="text-sm text-slate-700">◆ {p}</li>)}
          </ul>
        </Section>
      )}
      {d.design_system && (
        <Section title="Design System">
          <div className="grid md:grid-cols-2 gap-3">
            {Object.entries(d.design_system).map(([k, v]) => (
              <div key={k} className="bg-slate-50 rounded-lg p-3">
                <div className="text-[10px] font-bold uppercase text-slate-500">{k}</div>
                <div className="text-sm text-slate-700 mt-1">{Array.isArray(v) ? v.join(", ") : v}</div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* DEVELOPMENT */}
      {d.sprint_plan && (
        <Section title="Sprint Plan">
          <div className="space-y-2">
            {d.sprint_plan.map((s, i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-slate-900 text-sm">Sprint {s.sprint}: {s.goal}</div>
                  <span className="text-xs text-indigo-600 font-bold">{s.story_points}pt</span>
                </div>
                {s.tasks && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {s.tasks.map((t, j) => (
                      <span key={j} className="text-[10px] px-2 py-0.5 rounded bg-white border text-slate-600">{t}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
      {d.velocity_forecast && (
        <Section title="Velocity Forecast">
          <p className="text-sm text-slate-700">{d.velocity_forecast}</p>
        </Section>
      )}
      {d.tech_stack && (
        <Section title="Tech Stack">
          <div className="flex flex-wrap gap-2">
            {d.tech_stack.map((t, i) => (
              <span key={i} className="px-3 py-1 rounded-full bg-slate-800 text-white text-xs font-mono">{t}</span>
            ))}
          </div>
        </Section>
      )}

      {/* TESTING */}
      {d.test_strategy && (
        <Section title="Test Strategy">
          <p className="text-sm text-slate-700">{d.test_strategy}</p>
        </Section>
      )}
      {d.test_cases && (
        <Section title="Test Cases">
          <div className="space-y-2">
            {d.test_cases.map((t, i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <span className="text-[10px] font-mono text-slate-400 flex-shrink-0 mt-1">{t.id}</span>
                  <div className="flex-1">
                    <div className="text-sm text-slate-900 font-medium">{t.scenario}</div>
                    <div className="text-xs text-slate-600 mt-1">→ {t.expected}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
      {d.quality_gates && (
        <Section title="Quality Gates">
          <ul className="space-y-1">
            {d.quality_gates.map((q, i) => <li key={i} className="text-sm text-slate-700">✓ {q}</li>)}
          </ul>
        </Section>
      )}

      {/* LAUNCH */}
      {d.ci_cd_pipeline && (
        <Section title="CI/CD Pipeline">
          <div className="space-y-1">
            {d.ci_cd_pipeline.map((step, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold flex-shrink-0">{i + 1}</div>
                <div className="text-sm text-slate-700">{step}</div>
              </div>
            ))}
          </div>
        </Section>
      )}
      {d.infrastructure && (
        <Section title="Infrastructure">
          <p className="text-sm text-slate-700 font-mono bg-slate-50 rounded-lg p-3">{d.infrastructure}</p>
        </Section>
      )}
      {d.monitoring && (
        <Section title="Monitoring">
          <ul className="space-y-1">
            {d.monitoring.map((m, i) => <li key={i} className="text-sm text-slate-700">📊 {m}</li>)}
          </ul>
        </Section>
      )}
      {d.rollback_plan && (
        <Section title="Rollback Plan">
          <p className="text-sm text-slate-700">{d.rollback_plan}</p>
        </Section>
      )}

      {/* ITERATE */}
      {d.launch_announcement && (
        <Section title="Launch Announcement">
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-4 border border-indigo-200">
            <div className="text-lg font-black text-slate-900">{d.launch_announcement.headline}</div>
            <p className="text-sm text-slate-700 mt-2">{d.launch_announcement.body}</p>
            <button className="mt-3 px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold">{d.launch_announcement.cta}</button>
          </div>
        </Section>
      )}
      {d.success_metrics && (
        <Section title="Success Metrics">
          <div className="grid md:grid-cols-2 gap-2">
            {d.success_metrics.map((m, i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-3 flex items-center justify-between">
                <div className="text-sm font-bold text-slate-900">{m.kpi}</div>
                <div className="text-xs text-emerald-700 font-medium">{m.target}</div>
              </div>
            ))}
          </div>
        </Section>
      )}
      {d.feedback_loops && (
        <Section title="Feedback Loops">
          <ul className="space-y-1">
            {d.feedback_loops.map((f, i) => <li key={i} className="text-sm text-slate-700">🔄 {f}</li>)}
          </ul>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div>
      <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">{title}</h3>
      {children}
    </div>
  );
}
