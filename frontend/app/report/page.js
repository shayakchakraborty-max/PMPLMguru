"use client";
import { useState, useEffect, useRef } from "react";

// v12: /report — streaming Big 3 consulting report
// Connects to /api/report-stream which proxies SSE from backend
// Each section appears as it arrives, with a "thinking" animation between
// User can download the full report as PDF via window.print() with print-styled CSS

export default function ReportPage() {
  const [idea, setIdea] = useState("");
  const [classification, setClassification] = useState(null);
  const [sections, setSections] = useState([]);
  const [pendingSections, setPendingSections] = useState([]);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [streaming, setStreaming] = useState(false);
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    const params = new URLSearchParams(window.location.search);
    const ideaParam = params.get("idea") || sessionStorage.getItem("pmguru_pending_idea") || "";
    if (!ideaParam) {
      setError("No idea provided. Please go back and enter one.");
      return;
    }
    setIdea(ideaParam);
    streamReport(ideaParam);
  }, []);

  async function streamReport(ideaText) {
    setStreaming(true);
    setSections([]);
    setDone(false);
    setError("");
    try {
      const res = await fetch("/api/report-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea: ideaText }),
      });
      if (!res.ok || !res.body) {
        setError(`Stream failed: HTTP ${res.status}`);
        setStreaming(false);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done: readerDone } = await reader.read();
        if (readerDone) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6);
          try {
            const event = JSON.parse(payload);
            handleEvent(event);
          } catch (e) {
            console.warn("Bad SSE payload:", payload, e);
          }
        }
      }
      setStreaming(false);
    } catch (e) {
      setError("Stream error: " + e.message);
      setStreaming(false);
    }
  }

  function handleEvent(event) {
    if (event.type === "start") {
      setClassification(event.classification);
      setPendingSections(event.section_titles || []);
    } else if (event.type === "section") {
      setSections(s => [...s, event]);
    } else if (event.type === "done") {
      setDone(true);
      setStreaming(false);
    } else if (event.type === "error") {
      setError(event.error);
      setStreaming(false);
    }
  }

  function downloadPDF() {
    window.print();
  }

  async function buildWorkspace() {
    const r = await fetch("/api/pipeline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage: "workspace", idea }),
    });
    const data = await r.json();
    if (data.error) { setError(data.error); return; }
    const ws = data.workspace;
    ws._created_at = new Date().toISOString();
    ws._idea = idea;
    localStorage.setItem(`pmguru_project_${ws.project.id}`, JSON.stringify(ws));
    localStorage.setItem("pmguru_current_project", ws.project.id);
    window.location.href = `/workspace?id=${ws.project.id}`;
  }

  function runPlmCycle() {
    sessionStorage.setItem("pmguru_pending_idea", idea);
    window.location.href = `/plm-cycle?idea=${encodeURIComponent(idea)}`;
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      {/* Print-only styles */}
      <style jsx global>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white !important; }
          .report-section { page-break-inside: avoid; }
          .report-section + .report-section { page-break-before: auto; }
        }
        @page { size: A4; margin: 0.6in; }
      `}</style>

      {/* Sticky toolbar (no-print) */}
      <div className="no-print sticky top-0 bg-white border-b shadow-sm z-10">
        <div className="max-w-5xl mx-auto p-4 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <a href="/auto" className="text-xs text-slate-500 hover:text-indigo-600">← Back to launcher</a>
            <div className="font-black text-lg mt-0.5">Consulting Report</div>
          </div>
          <div className="flex gap-2 flex-wrap">
            {done && (
              <>
                <button onClick={downloadPDF} className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-bold">
                  📥 Download PDF
                </button>
                <button onClick={buildWorkspace} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold">
                  🛠️ Build PM Workspace
                </button>
                <button onClick={runPlmCycle} className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-bold">
                  🔄 Run PLM Cycle
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto p-6 print:p-0">
        {/* Cover */}
        <div className="bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-white rounded-3xl p-10 mb-6 shadow-xl print:shadow-none print:rounded-none">
          <div className="text-xs uppercase tracking-[3px] opacity-60 font-bold">PMGuru Consulting</div>
          <div className="text-xs uppercase tracking-wider opacity-50 mt-1">Strategic Due Diligence Report</div>
          <h1 className="text-4xl font-black mt-6 leading-tight">{idea || "Loading..."}</h1>
          {classification && (
            <div className="mt-6 flex gap-2 flex-wrap">
              <span className="px-3 py-1.5 rounded-full bg-white/10 text-xs font-bold">{classification.industry}</span>
              <span className="px-3 py-1.5 rounded-full bg-white/10 text-xs font-bold">{classification.complexity?.replace("_", " ")} complexity</span>
              <span className="px-3 py-1.5 rounded-full bg-white/10 text-xs font-bold">McKinsey · BCG · Bain blended methodology</span>
            </div>
          )}
          <div className="mt-8 text-xs opacity-70 grid grid-cols-2 gap-4 max-w-md">
            <div>
              <div className="opacity-50 uppercase tracking-wider">Prepared by</div>
              <div className="font-bold mt-1">PMGuru Strategy Practice</div>
            </div>
            <div>
              <div className="opacity-50 uppercase tracking-wider">Date</div>
              <div className="font-bold mt-1">{new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</div>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-rose-50 border-2 border-rose-300 rounded-xl p-4 mb-6">
            <div className="font-bold text-rose-900 mb-1">Error</div>
            <pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre>
          </div>
        )}

        {/* Streaming progress */}
        {streaming && (
          <div className="no-print bg-white rounded-xl border p-4 mb-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" style={{ borderWidth: "3px" }}></div>
              <div className="flex-1">
                <div className="font-bold text-sm">Generating consulting report...</div>
                <div className="text-xs text-slate-500">{sections.length} of {pendingSections.length || 11} sections complete</div>
              </div>
            </div>
            <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                style={{ width: `${pendingSections.length ? (sections.length / pendingSections.length) * 100 : 0}%` }}
              />
            </div>
            <div className="mt-3 grid grid-cols-2 md:grid-cols-3 gap-1 text-[10px]">
              {pendingSections.map((title, i) => {
                const isDone = i < sections.length;
                const isActive = i === sections.length;
                return (
                  <div key={i} className={`px-2 py-1 rounded ${isDone ? "bg-emerald-100 text-emerald-700" : isActive ? "bg-amber-100 text-amber-700 animate-pulse" : "bg-slate-100 text-slate-400"}`}>
                    {isDone ? "✓" : isActive ? "⏳" : "○"} {title}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Sections */}
        <div className="space-y-6">
          {sections.map((s, i) => <ReportSection key={s.id} section={s} index={i} />)}
        </div>

        {/* Footer */}
        {done && (
          <div className="mt-10 pt-6 border-t border-slate-300 text-center text-xs text-slate-500">
            <div>This report was generated by PMGuru's template-driven consulting engine.</div>
            <div className="mt-1">All recommendations are based on 500+ real project benchmarks. Adapt to your specific context.</div>
            <div className="mt-1">© {new Date().getFullYear()} PMGuru · Confidential</div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// Section renderer - dispatches to specialized components per section ID
// ============================================================
function ReportSection({ section, index }) {
  return (
    <div className="report-section bg-white rounded-2xl shadow-sm border p-8 print:rounded-none print:shadow-none print:border-0 animate-fadeIn" style={{ animationDelay: "0.1s" }}>
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn { animation: fadeIn 0.5s ease-out forwards; }
      `}</style>
      <div className="flex items-baseline gap-3 mb-1 pb-3 border-b border-slate-200">
        <span className="text-2xl">{section.icon}</span>
        <div className="flex-1">
          <div className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider">Section {index + 1} of 11 · {section.style}</div>
          <h2 className="text-2xl font-black text-slate-900 mt-0.5">{section.title}</h2>
        </div>
      </div>

      {section.status === "error" ? (
        <div className="text-rose-700 text-sm bg-rose-50 p-3 rounded-lg">{section.error}</div>
      ) : (
        <div className="mt-4">
          {section.id === "executive_summary"     && <ExecutiveSummary data={section.data} />}
          {section.id === "market_sizing"         && <MarketSizing data={section.data} />}
          {section.id === "competitive_landscape" && <CompetitiveLandscape data={section.data} />}
          {section.id === "tech_stack"            && <TechStack data={section.data} />}
          {section.id === "methodology"           && <MethodologySec data={section.data} />}
          {section.id === "financial_projections" && <FinancialProjections data={section.data} />}
          {section.id === "risk_assessment"       && <RiskAssessment data={section.data} />}
          {section.id === "gtm_strategy"          && <GtmStrategy data={section.data} />}
          {section.id === "team_resource_plan"    && <TeamResourcePlan data={section.data} />}
          {section.id === "regulatory_compliance" && <RegulatoryCompliance data={section.data} />}
          {section.id === "implementation_roadmap"&& <ImplementationRoadmap data={section.data} />}
        </div>
      )}
    </div>
  );
}

// ---------- Section sub-components ----------

function CalloutBox({ label, children, color = "indigo" }) {
  return (
    <div className={`bg-${color}-50 border-l-4 border-${color}-500 rounded p-3 my-3`}>
      <div className={`text-[10px] font-bold text-${color}-700 uppercase tracking-wider`}>{label}</div>
      <div className="text-sm text-slate-800 mt-1">{children}</div>
    </div>
  );
}

function StatCard({ label, value, subtitle, color = "indigo" }) {
  return (
    <div className={`bg-${color}-50 border border-${color}-200 rounded-xl p-4`}>
      <div className={`text-[10px] font-bold text-${color}-700 uppercase tracking-wider`}>{label}</div>
      <div className="text-2xl font-black text-slate-900 mt-1">{value}</div>
      {subtitle && <div className="text-xs text-slate-500 mt-1">{subtitle}</div>}
    </div>
  );
}

function ExecutiveSummary({ data }) {
  return (
    <div className="space-y-3">
      <CalloutBox label="Situation" color="slate">{data.situation}</CalloutBox>
      <CalloutBox label="Complication" color="amber">{data.complication}</CalloutBox>
      <CalloutBox label="Recommendation" color="emerald">{data.recommendation}</CalloutBox>
      <div className="grid md:grid-cols-2 gap-3 mt-4">
        <div className="p-4 bg-indigo-50 rounded-xl">
          <div className="text-xs font-bold text-indigo-700 uppercase mb-2">Key Findings</div>
          <ul className="space-y-1.5 text-sm text-slate-700">
            {data.key_findings?.map((f, i) => <li key={i}>• {f}</li>)}
          </ul>
        </div>
        <div className="p-4 bg-slate-900 text-white rounded-xl">
          <div className="text-xs font-bold opacity-60 uppercase mb-2">Recommendation</div>
          <div className="text-3xl font-black">{data.go_no_go}</div>
          <div className="text-xs opacity-70 mt-1">Confidence: {data.confidence_level}</div>
        </div>
      </div>
    </div>
  );
}

function MarketSizing({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="grid md:grid-cols-3 gap-3">
        <StatCard label="TAM" value={data.tam?.value} subtitle={data.tam?.definition} color="purple" />
        <StatCard label="SAM" value={data.sam?.value} subtitle={data.sam?.definition} color="indigo" />
        <StatCard label="SOM" value={data.som?.value} subtitle={data.som?.definition} color="emerald" />
      </div>
      <CalloutBox label={`Growth Rate · ${data.growth_rate}`} color="emerald">{data.growth_drivers}</CalloutBox>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Market Share Targets</div>
        <div className="space-y-2">
          {data.market_share_targets?.map((t, i) => (
            <div key={i} className="flex items-center gap-3 p-2 bg-slate-50 rounded">
              <span className="font-bold text-sm w-16">{t.year}</span>
              <span className="text-sm font-bold text-indigo-700 w-20">{t.target}</span>
              <span className="text-xs text-slate-600">{t.rationale}</span>
            </div>
          ))}
        </div>
      </div>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Geographic Priorities</div>
        <ul className="text-sm text-slate-700 space-y-1">
          {data.geographic_priorities?.map((g, i) => <li key={i}>• {g}</li>)}
        </ul>
      </div>
    </div>
  );
}

function CompetitiveLandscape({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="space-y-2">
        {data.competitors?.map((c, i) => (
          <div key={i} className="border rounded-xl p-4">
            <div className="font-black text-slate-900">{c.name}</div>
            <div className="grid md:grid-cols-3 gap-3 mt-2 text-xs">
              <div className="p-2 bg-emerald-50 rounded"><strong className="text-emerald-700">Strength:</strong> {c.strength}</div>
              <div className="p-2 bg-rose-50 rounded"><strong className="text-rose-700">Weakness:</strong> {c.weakness}</div>
              <div className="p-2 bg-amber-50 rounded"><strong className="text-amber-700">Moat:</strong> {c.moat}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="p-4 bg-indigo-50 rounded-xl">
        <div className="text-xs font-bold text-indigo-700 uppercase mb-2">2x2 Positioning Matrix</div>
        <div className="text-sm space-y-1">
          <div><strong>X-axis:</strong> {data.competitive_positioning?.axis_x}</div>
          <div><strong>Y-axis:</strong> {data.competitive_positioning?.axis_y}</div>
          <div className="mt-2"><strong>White space:</strong> {data.competitive_positioning?.white_space}</div>
          <div className="text-emerald-700"><strong>Our position:</strong> {data.competitive_positioning?.our_position}</div>
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <div>
          <div className="text-xs font-bold text-slate-600 uppercase mb-2">Differentiation Strategy</div>
          <ul className="text-sm space-y-1">
            {data.differentiation_strategy?.map((d, i) => <li key={i}>✓ {d}</li>)}
          </ul>
        </div>
        <div>
          <div className="text-xs font-bold text-slate-600 uppercase mb-2">Moat Assessment</div>
          <div className="space-y-1 text-xs">
            {data.moat_assessment && Object.entries(data.moat_assessment).map(([k, v]) => (
              <div key={k}><strong className="capitalize">{k.replace(/_/g, " ")}:</strong> {v}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function TechStack({ data }) {
  const groups = [
    { key: "frontend", label: "Frontend", color: "blue" },
    { key: "backend", label: "Backend", color: "purple" },
    { key: "infrastructure", label: "Infrastructure", color: "emerald" },
    { key: "ai_ml", label: "AI / ML", color: "indigo" },
    { key: "integrations", label: "Integrations", color: "amber" },
  ];
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="grid md:grid-cols-2 gap-3">
        {groups.map(g => (
          <div key={g.key} className={`p-4 bg-${g.color}-50 rounded-xl border border-${g.color}-100`}>
            <div className={`text-xs font-bold text-${g.color}-700 uppercase mb-2`}>{g.label}</div>
            <ul className="text-sm space-y-1">
              {data[g.key]?.map((item, i) => <li key={i}>• {item}</li>)}
            </ul>
          </div>
        ))}
      </div>
      <CalloutBox label="Stack Rationale" color="slate">{data.rationale}</CalloutBox>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Build vs Buy Matrix</div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-100 text-left">
                <th className="p-2 font-bold">Capability</th>
                <th className="p-2 font-bold">Decision</th>
                <th className="p-2 font-bold">Reason</th>
              </tr>
            </thead>
            <tbody>
              {data.build_vs_buy?.map((b, i) => (
                <tr key={i} className="border-t">
                  <td className="p-2 font-bold">{b.capability}</td>
                  <td className="p-2"><span className={`px-2 py-0.5 rounded text-[10px] font-bold ${b.decision.startsWith("Build") ? "bg-emerald-100 text-emerald-700" : "bg-blue-100 text-blue-700"}`}>{b.decision}</span></td>
                  <td className="p-2 text-slate-600">{b.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Scalability Path</div>
        <ul className="text-sm space-y-1">
          {data.scalability_path?.map((s, i) => <li key={i}>→ {s}</li>)}
        </ul>
      </div>
    </div>
  );
}

function MethodologySec({ data }) {
  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-br from-slate-900 to-indigo-900 text-white rounded-2xl p-6">
        <div className="text-xs opacity-60 uppercase tracking-wider">Recommended Methodology</div>
        <div className="text-4xl font-black mt-2">{data.recommended}</div>
        <div className="text-xs opacity-70 mt-1">{data.confidence} confidence</div>
        <p className="text-sm opacity-90 mt-3 italic">{data.primary_rationale}</p>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <div className="p-4 bg-indigo-50 rounded-xl">
          <div className="text-xs font-bold text-indigo-700 uppercase mb-2">Roles</div>
          <ul className="text-sm space-y-1">{data.method_details?.roles?.map((r, i) => <li key={i}>• {r}</li>)}</ul>
        </div>
        <div className="p-4 bg-purple-50 rounded-xl">
          <div className="text-xs font-bold text-purple-700 uppercase mb-2">Ceremonies</div>
          <ul className="text-sm space-y-1">{data.method_details?.ceremonies?.map((c, i) => <li key={i}>• {c}</li>)}</ul>
        </div>
        <div className="p-4 bg-emerald-50 rounded-xl">
          <div className="text-xs font-bold text-emerald-700 uppercase mb-2">Artifacts</div>
          <ul className="text-sm space-y-1">{data.method_details?.artifacts?.map((a, i) => <li key={i}>• {a}</li>)}</ul>
        </div>
        <div className="p-4 bg-amber-50 rounded-xl">
          <div className="text-xs font-bold text-amber-700 uppercase mb-2">Cadence</div>
          <div className="text-sm">{data.method_details?.cadence}</div>
        </div>
      </div>
      {data.tooling && (
        <CalloutBox label={`Recommended Tool: ${data.tooling.primary}`} color="indigo">
          {data.tooling.reason}
          <div className="text-xs text-slate-500 mt-1">Alternatives: {data.tooling.alternatives?.join(", ")}</div>
        </CalloutBox>
      )}
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Why Not Other Methodologies</div>
        <div className="space-y-1">
          {data.alternatives_considered?.map((a, i) => (
            <div key={i} className="text-xs"><strong className="text-slate-900">✗ {a.method}:</strong> <span className="text-slate-600">{a.reason}</span></div>
          ))}
        </div>
      </div>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Ceremony Calendar</div>
        <table className="w-full text-xs">
          <thead><tr className="bg-slate-100 text-left"><th className="p-2 font-bold">Event</th><th className="p-2 font-bold">Frequency</th><th className="p-2 font-bold">Duration</th><th className="p-2 font-bold">Attendees</th></tr></thead>
          <tbody>
            {data.ceremony_calendar?.map((c, i) => (
              <tr key={i} className="border-t"><td className="p-2 font-bold">{c.event}</td><td className="p-2">{c.frequency}</td><td className="p-2">{c.duration}</td><td className="p-2 text-slate-600">{c.attendees}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FinancialProjections({ data }) {
  const cur = data.currency || "$";
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Revenue Projection</div>
        <table className="w-full text-sm">
          <thead><tr className="bg-slate-100 text-left"><th className="p-2 font-bold">Year</th><th className="p-2 font-bold">Users</th><th className="p-2 font-bold">Revenue</th><th className="p-2 font-bold">Growth</th></tr></thead>
          <tbody>
            {data.revenue_projection?.map((r, i) => (
              <tr key={i} className="border-t">
                <td className="p-2 font-bold">{r.year}</td>
                <td className="p-2">{r.users}</td>
                <td className="p-2 font-bold text-emerald-700">{r.revenue}</td>
                <td className="p-2 text-slate-600">{r.growth}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">P&L Trajectory</div>
        <div className="space-y-2">
          {data.profit_loss?.map((p, i) => (
            <div key={i} className={`p-3 rounded-lg flex items-center gap-4 ${p.net > 0 ? "bg-emerald-50" : "bg-rose-50"}`}>
              <span className="font-black w-20">{p.year}</span>
              <span className="text-xs flex-1">Rev: {cur}{p.revenue?.toLocaleString()} · Costs: {cur}{p.costs?.toLocaleString()}</span>
              <span className={`font-black ${p.net > 0 ? "text-emerald-700" : "text-rose-700"}`}>{cur}{(p.net || 0).toLocaleString()}</span>
              <span className="text-xs text-slate-500">{p.status}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <div className="p-4 bg-indigo-50 rounded-xl">
          <div className="text-xs font-bold text-indigo-700 uppercase mb-2">Unit Economics</div>
          <div className="text-xs space-y-1">
            {data.unit_economics && Object.entries(data.unit_economics).map(([k, v]) => (
              <div key={k}><strong className="capitalize">{k.replace(/_/g, " ")}:</strong> {v}</div>
            ))}
          </div>
        </div>
        <div className="p-4 bg-purple-50 rounded-xl">
          <div className="text-xs font-bold text-purple-700 uppercase mb-2">Cost Structure (Y1)</div>
          <div className="text-xs space-y-1">
            {data.cost_structure && Object.entries(data.cost_structure).map(([k, v]) => (
              <div key={k}><strong className="capitalize">{k}:</strong> {typeof v === "number" ? `${cur}${v.toLocaleString()}` : v}</div>
            ))}
          </div>
        </div>
      </div>
      <CalloutBox label="Funding Requirement" color="amber">
        <div><strong>Seed:</strong> {data.funding_requirement?.seed}</div>
        <div><strong>Series A:</strong> {data.funding_requirement?.series_a}</div>
        <div className="mt-1 text-xs">Use of funds: {data.funding_requirement?.use_of_funds?.join(" · ")}</div>
      </CalloutBox>
    </div>
  );
}

function RiskAssessment({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="space-y-3">
        {data.risk_categories?.map((cat, i) => (
          <div key={i} className="border rounded-xl p-4">
            <div className="font-black text-slate-900 mb-2">{cat.category}</div>
            <div className="space-y-2">
              {cat.risks?.map((r, j) => (
                <div key={j} className="flex items-start gap-3 text-xs p-2 bg-slate-50 rounded">
                  <div className="flex-1">
                    <div className="font-bold">{r.description}</div>
                    <div className="text-slate-600 mt-0.5">→ {r.mitigation}</div>
                  </div>
                  <div className="flex flex-col gap-1 items-end">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-100 text-amber-700 font-bold">{r.likelihood}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${r.impact === "Critical" ? "bg-rose-100 text-rose-700" : r.impact === "High" ? "bg-orange-100 text-orange-700" : "bg-blue-100 text-blue-700"}`}>{r.impact}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <CalloutBox label="Risk Governance" color="indigo">
        <div className="text-xs space-y-1">
          {data.risk_governance && Object.entries(data.risk_governance).map(([k, v]) => (
            <div key={k}><strong className="capitalize">{k.replace(/_/g, " ")}:</strong> {v}</div>
          ))}
        </div>
      </CalloutBox>
    </div>
  );
}

function GtmStrategy({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <CalloutBox label="Primary GTM Motion" color="emerald">{data.primary_motion}</CalloutBox>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Channels</div>
        <ul className="text-sm space-y-1">
          {data.channels?.map((c, i) => <li key={i}>• {c}</li>)}
        </ul>
      </div>
      <div className="grid md:grid-cols-4 gap-2">
        {data.unit_economics && Object.entries(data.unit_economics).map(([k, v]) => (
          <StatCard key={k} label={k.replace(/_/g, " ")} value={v} color="indigo" />
        ))}
      </div>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Phased Rollout</div>
        <div className="space-y-2">
          {data.phased_rollout?.map((p, i) => (
            <div key={i} className="border-l-4 border-indigo-500 pl-3 py-1">
              <div className="font-bold text-sm">{p.phase}</div>
              <div className="text-xs text-slate-600">{p.target}</div>
              <div className="text-xs text-slate-500 mt-0.5">Tactics: {p.tactics?.join(" · ")}</div>
            </div>
          ))}
        </div>
      </div>
      {data.messaging_framework && (
        <CalloutBox label="Positioning Statement (Geoffrey Moore framework)" color="purple">
          <div className="text-sm leading-relaxed">
            <strong>For</strong> {data.messaging_framework.for} <strong>who</strong> {data.messaging_framework.who}, <strong>{data.messaging_framework.the_product}</strong> <strong>that provides</strong> {data.messaging_framework.that_provides}. <strong>Unlike</strong> {data.messaging_framework.unlike}, <strong>we deliver</strong> {data.messaging_framework.we_deliver}.
          </div>
        </CalloutBox>
      )}
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Success Metrics</div>
        <table className="w-full text-xs">
          <tbody>
            {data.success_metrics?.map((m, i) => (
              <tr key={i} className="border-t"><td className="p-2 font-bold">{m.metric}</td><td className="p-2 text-emerald-700">{m.target}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TeamResourcePlan({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Founding Team Composition</div>
        <div className="grid md:grid-cols-2 gap-2">
          {data.founding_team?.map((t, i) => (
            <div key={i} className="p-3 bg-slate-50 rounded text-sm">
              <span className="font-bold">{t.role}</span>
              <span className="text-xs text-slate-500 ml-2">×{t.count} @ {t.allocation}</span>
            </div>
          ))}
        </div>
      </div>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Hiring Plan</div>
        <div className="space-y-2">
          {data.hiring_plan?.map((h, i) => (
            <div key={i} className="border-l-4 border-purple-500 pl-3 py-1">
              <div className="font-bold text-sm">{h.phase}</div>
              <div className="text-xs">Hires: {h.hires?.join(", ")}</div>
              <div className="text-xs text-slate-500">{h.rationale}</div>
            </div>
          ))}
        </div>
      </div>
      {data.compensation_philosophy && (
        <CalloutBox label="Compensation Philosophy" color="indigo">
          <div className="text-xs space-y-1">
            {Object.entries(data.compensation_philosophy).map(([k, v]) => (
              <div key={k}><strong className="capitalize">{k}:</strong> {v}</div>
            ))}
          </div>
        </CalloutBox>
      )}
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Org Design Principles</div>
        <ul className="text-sm space-y-1">
          {data.org_design_principles?.map((p, i) => <li key={i}>✓ {p}</li>)}
        </ul>
      </div>
    </div>
  );
}

function RegulatoryCompliance({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="grid md:grid-cols-2 gap-3">
        <div className="p-4 bg-blue-50 rounded-xl">
          <div className="text-xs font-bold text-blue-700 uppercase mb-2">Key Regulations</div>
          <ul className="text-sm space-y-1">{data.key_regulations?.map((r, i) => <li key={i}>• {r}</li>)}</ul>
        </div>
        <div className="p-4 bg-purple-50 rounded-xl">
          <div className="text-xs font-bold text-purple-700 uppercase mb-2">Required Certifications</div>
          <ul className="text-sm space-y-1">{data.required_certifications?.map((c, i) => <li key={i}>• {c}</li>)}</ul>
        </div>
      </div>
      <CalloutBox label={`Data Residency: ${data.data_residency}`} color="amber" />
      <div>
        <div className="text-xs font-bold text-rose-600 uppercase mb-2">High-Risk Areas</div>
        <ul className="text-sm space-y-1">{data.high_risk_areas?.map((a, i) => <li key={i} className="text-rose-700">⚠ {a}</li>)}</ul>
      </div>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Compliance Roadmap</div>
        <div className="space-y-2">
          {data.compliance_roadmap?.map((r, i) => (
            <div key={i} className="border-l-4 border-emerald-500 pl-3 py-1">
              <div className="font-bold text-sm">{r.timeline}</div>
              <ul className="text-xs space-y-0.5 text-slate-600">{r.items?.map((it, j) => <li key={j}>→ {it}</li>)}</ul>
            </div>
          ))}
        </div>
      </div>
      {data.compliance_budget && (
        <div className="grid md:grid-cols-3 gap-2">
          {Object.entries(data.compliance_budget).map(([k, v]) => (
            <StatCard key={k} label={k.replace(/_/g, " ")} value={v} color="amber" />
          ))}
        </div>
      )}
    </div>
  );
}

function ImplementationRoadmap({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="space-y-2">
        {data.quarters?.map((q, i) => (
          <div key={i} className="border rounded-xl p-3">
            <div className="flex items-baseline gap-3">
              <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">{q.quarter}</span>
              <span className="font-black text-sm">{q.theme}</span>
            </div>
            <div className="mt-2 grid md:grid-cols-2 gap-2 text-xs">
              <div>
                <div className="font-bold text-slate-700 mb-1">Milestones</div>
                <ul className="space-y-0.5 text-slate-600">{q.milestones?.map((m, j) => <li key={j}>• {m}</li>)}</ul>
              </div>
              <div className="bg-emerald-50 rounded p-2">
                <div className="font-bold text-emerald-700 mb-1">Success Criteria</div>
                <div className="text-emerald-900">{q.success_criteria}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Decision Gates</div>
        <table className="w-full text-xs">
          <thead><tr className="bg-slate-100 text-left"><th className="p-2 font-bold">Gate</th><th className="p-2 font-bold">Decision</th><th className="p-2 font-bold">Criteria</th></tr></thead>
          <tbody>
            {data.decision_gates?.map((g, i) => (
              <tr key={i} className="border-t"><td className="p-2 font-bold">{g.gate}</td><td className="p-2">{g.decision}</td><td className="p-2 text-slate-600">{g.criteria}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <div>
        <div className="text-xs font-bold text-slate-600 uppercase mb-2">Dependency Map</div>
        <ul className="text-sm space-y-1">{data.dependency_map?.map((d, i) => <li key={i}>→ {d}</li>)}</ul>
      </div>
    </div>
  );
}
