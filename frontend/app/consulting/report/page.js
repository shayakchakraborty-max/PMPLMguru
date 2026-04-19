"use client";
import { useState, useEffect, useRef } from "react";

export default function ConsultingReportPage() {
  const [description, setDescription] = useState("");
  const [domains, setDomains] = useState([]);
  const [domainNames, setDomainNames] = useState([]);
  const [scenarioCount, setScenarioCount] = useState(0);
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
    const desc = params.get("description") || sessionStorage.getItem("consulting_description") || "";
    if (!desc) { setError("No description provided."); return; }
    setDescription(desc);
    streamReport(desc);
  }, []);

  async function streamReport(desc) {
    setStreaming(true); setSections([]); setDone(false); setError("");
    try {
      const res = await fetch("/api/consulting-stream", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: desc }),
      });
      if (!res.ok || !res.body) { setError(`Stream failed: HTTP ${res.status}`); setStreaming(false); return; }
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
          try { handleEvent(JSON.parse(line.slice(6))); } catch {}
        }
      }
      setStreaming(false);
    } catch (e) { setError("Stream error: " + e.message); setStreaming(false); }
  }

  function handleEvent(event) {
    if (event.type === "start") {
      setDomains(event.domains || []);
      setDomainNames(event.domain_names || []);
      setScenarioCount(event.scenario_count || 0);
      setPendingSections(event.section_titles || []);
    } else if (event.type === "section") {
      setSections(s => [...s, event]);
    } else if (event.type === "done") {
      setDone(true); setStreaming(false);
    } else if (event.type === "error") {
      setError(event.error); setStreaming(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <style jsx global>{`@media print { .no-print { display: none !important; } body { background: white !important; } .report-section { page-break-inside: avoid; } } @page { size: A4; margin: 0.6in; }`}</style>

      <div className="no-print sticky top-0 bg-white border-b shadow-sm z-10">
        <div className="max-w-5xl mx-auto p-4 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <a href="/consulting" className="text-xs text-slate-500 hover:text-emerald-600">← Back to consulting</a>
            <div className="font-black text-lg mt-0.5">Consulting Assessment Report</div>
          </div>
          {done && <button onClick={() => window.print()} className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-bold">📥 Download PDF</button>}
        </div>
      </div>

      <div className="max-w-5xl mx-auto p-6 print:p-0">
        {/* Cover */}
        <div className="bg-gradient-to-br from-emerald-900 via-teal-900 to-cyan-900 text-white rounded-3xl p-10 mb-6 shadow-xl print:shadow-none print:rounded-none">
          <div className="text-xs uppercase tracking-[3px] opacity-60 font-bold">PMGuru Consulting Pro</div>
          <div className="text-xs uppercase tracking-wider opacity-50 mt-1">Big 3 + Big 4 Blended Assessment Report</div>
          <h1 className="text-3xl font-black mt-6 leading-tight">{description || "Loading..."}</h1>
          {domainNames.length > 0 && (
            <div className="mt-6 flex gap-2 flex-wrap">
              {domainNames.map(d => <span key={d} className="px-3 py-1.5 rounded-full bg-white/10 text-xs font-bold">{d}</span>)}
              <span className="px-3 py-1.5 rounded-full bg-white/10 text-xs font-bold">{scenarioCount} scenarios evaluated</span>
            </div>
          )}
          <div className="mt-8 text-xs opacity-70 grid grid-cols-3 gap-4 max-w-md">
            <div><div className="opacity-50 uppercase tracking-wider">Prepared by</div><div className="font-bold mt-1">PMGuru Advisory</div></div>
            <div><div className="opacity-50 uppercase tracking-wider">Date</div><div className="font-bold mt-1">{new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</div></div>
            <div><div className="opacity-50 uppercase tracking-wider">Methodology</div><div className="font-bold mt-1">Big 3 + Big 4</div></div>
          </div>
        </div>

        {error && <div className="bg-rose-50 border-2 border-rose-300 rounded-xl p-4 mb-6"><pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre></div>}

        {streaming && (
          <div className="no-print bg-white rounded-xl border p-4 mb-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin" style={{ borderWidth: "3px" }}></div>
              <div className="flex-1">
                <div className="font-bold text-sm">Analyzing {scenarioCount} scenarios across {domainNames.length} domains...</div>
                <div className="text-xs text-slate-500">{sections.length} of {pendingSections.length || 9} sections complete</div>
              </div>
            </div>
            <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500" style={{ width: `${pendingSections.length ? (sections.length / pendingSections.length) * 100 : 0}%` }} />
            </div>
            <div className="mt-3 grid grid-cols-3 gap-1 text-[10px]">
              {pendingSections.map((title, i) => {
                const isDone = i < sections.length;
                const isActive = i === sections.length;
                return <div key={i} className={`px-2 py-1 rounded ${isDone ? "bg-emerald-100 text-emerald-700" : isActive ? "bg-amber-100 text-amber-700 animate-pulse" : "bg-slate-100 text-slate-400"}`}>{isDone ? "✓" : isActive ? "⏳" : "○"} {title}</div>;
              })}
            </div>
          </div>
        )}

        <div className="space-y-6">
          {sections.map((s, i) => <ConsultingSection key={s.id} section={s} index={i} />)}
        </div>

        {done && (
          <div className="mt-10 pt-6 border-t border-slate-300 text-center text-xs text-slate-500">
            <div>Powered by PMGuru Consulting Intelligence · 1,003 scenarios · 12 domains</div>
            <div className="mt-1">© {new Date().getFullYear()} PMGuru · Confidential — for authorized recipients only</div>
          </div>
        )}
      </div>
    </div>
  );
}

function ConsultingSection({ section, index }) {
  return (
    <div className="report-section bg-white rounded-2xl shadow-sm border p-8 print:rounded-none print:shadow-none animate-fadeIn" style={{ animationDelay: "0.1s" }}>
      <style jsx>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } } .animate-fadeIn { animation: fadeIn 0.5s ease-out forwards; }`}</style>
      <div className="flex items-baseline gap-3 mb-1 pb-3 border-b border-slate-200">
        <span className="text-2xl">{section.icon}</span>
        <div className="flex-1">
          <div className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">Section {index + 1} of 9 · {section.style}</div>
          <h2 className="text-2xl font-black text-slate-900 mt-0.5">{section.title}</h2>
        </div>
      </div>
      {section.status === "error" ? <div className="text-rose-700 text-sm bg-rose-50 p-3 rounded-lg mt-4">{section.error}</div> : (
        <div className="mt-4">
          {section.id === "engagement_summary" && <EngagementSummary data={section.data} />}
          {section.id === "maturity_assessment" && <MaturityAssessment data={section.data} />}
          {section.id === "detailed_findings" && <DetailedFindings data={section.data} />}
          {section.id === "gap_analysis" && <GapAnalysis data={section.data} />}
          {section.id === "benchmarks" && <Benchmarks data={section.data} />}
          {section.id === "recommendations" && <Recommendations data={section.data} />}
          {section.id === "roadmap" && <Roadmap data={section.data} />}
          {section.id === "roi_analysis" && <RoiAnalysis data={section.data} />}
          {section.id === "governance" && <Governance data={section.data} />}
        </div>
      )}
    </div>
  );
}

function Callout({ label, children, color = "emerald" }) {
  return (
    <div className={`bg-${color}-50 border-l-4 border-${color}-500 rounded p-3 my-3`}>
      <div className={`text-[10px] font-bold text-${color}-700 uppercase tracking-wider`}>{label}</div>
      <div className="text-sm text-slate-800 mt-1">{children}</div>
    </div>
  );
}

function EngagementSummary({ data }) {
  return (
    <div className="space-y-3">
      <Callout label="Situation" color="slate">{data.situation}</Callout>
      <Callout label="Complication" color="amber">{data.complication}</Callout>
      <Callout label="Recommendation" color="emerald">{data.recommendation}</Callout>
      {data.key_metrics && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-4">
          {Object.entries(data.key_metrics).map(([k, v]) => (
            <div key={k} className="bg-slate-900 text-white rounded-xl p-3 text-center">
              <div className="text-xl font-black">{v}</div>
              <div className="text-[10px] opacity-60 mt-0.5 capitalize">{k.replace(/_/g, " ")}</div>
            </div>
          ))}
        </div>
      )}
      <p className="text-xs text-slate-500 italic mt-2">{data.methodology}</p>
    </div>
  );
}

function MaturityAssessment({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="space-y-3">
        {data.maturity_scores && Object.entries(data.maturity_scores).map(([key, m]) => (
          <div key={key} className="border rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-black">{m.domain}</span>
              <div className="flex gap-2 text-xs">
                <span className="px-2 py-0.5 rounded" style={{ backgroundColor: m.color + "20", color: m.color }}>Level {m.current_level}: {m.current_name}</span>
                <span className="text-slate-400">→</span>
                <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700">Target: Level {m.target_level}</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {[1,2,3,4,5].map(level => (
                <div key={level} className="flex-1 h-3 rounded-full" style={{
                  backgroundColor: level <= m.current_level ? m.color : level <= m.target_level ? m.color + "30" : "#e2e8f0"
                }} />
              ))}
            </div>
            <div className="text-xs text-slate-500 mt-1">{m.critical_count} critical · {m.high_count} high · {m.total_findings} total findings</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DetailedFindings({ data }) {
  const [expanded, setExpanded] = useState({});
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="grid grid-cols-4 gap-2 mb-4">
        {data.risk_distribution && Object.entries(data.risk_distribution).map(([level, count]) => (
          <div key={level} className={`text-center p-3 rounded-xl ${level === "Critical" ? "bg-rose-100 text-rose-700" : level === "High" ? "bg-orange-100 text-orange-700" : level === "Medium" ? "bg-amber-100 text-amber-700" : "bg-blue-100 text-blue-700"}`}>
            <div className="text-2xl font-black">{count}</div>
            <div className="text-[10px] font-bold uppercase">{level}</div>
          </div>
        ))}
      </div>
      {data.domains && Object.entries(data.domains).map(([domainKey, domainData]) => (
        <div key={domainKey} className="border rounded-xl overflow-hidden">
          <button onClick={() => setExpanded(e => ({...e, [domainKey]: !e[domainKey]}))}
            className="w-full text-left p-4 bg-slate-50 hover:bg-slate-100 transition flex items-center justify-between">
            <span className="font-black">{domainData.icon} {domainData.domain_name} ({domainData.findings.length} findings)</span>
            <span className="text-slate-400">{expanded[domainKey] ? "▲" : "▼"}</span>
          </button>
          {expanded[domainKey] && (
            <div className="p-3 space-y-2">
              {domainData.findings.slice(0, 15).map((f, i) => (
                <div key={i} className="flex items-start gap-3 p-2 bg-slate-50 rounded text-xs">
                  <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] shrink-0 ${f.risk_level === "Critical" ? "bg-rose-100 text-rose-700" : f.risk_level === "High" ? "bg-orange-100 text-orange-700" : "bg-amber-100 text-amber-700"}`}>{f.risk_level}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold">{f.title}</div>
                    <div className="text-slate-600 mt-0.5">{f.finding}</div>
                    <div className="text-emerald-700 mt-0.5">→ {f.recommendation}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function GapAnalysis({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead><tr className="bg-slate-100 text-left"><th className="p-2 font-bold">Domain</th><th className="p-2 font-bold">Process Area</th><th className="p-2 font-bold">Current</th><th className="p-2 font-bold">Target</th><th className="p-2 font-bold">Gap</th><th className="p-2 font-bold">Key Action</th></tr></thead>
          <tbody>
            {data.gaps?.slice(0, 20).map((g, i) => (
              <tr key={i} className="border-t">
                <td className="p-2 text-slate-600">{g.domain}</td>
                <td className="p-2 font-bold">{g.process_area}</td>
                <td className="p-2"><span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 text-[10px]">{g.current_state}</span></td>
                <td className="p-2"><span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 text-[10px]">{g.target_state}</span></td>
                <td className="p-2"><span className={`font-bold ${g.gap_severity === "High" ? "text-rose-700" : g.gap_severity === "Medium" ? "text-amber-700" : "text-blue-700"}`}>{g.gap_severity}</span></td>
                <td className="p-2 text-slate-600">{g.key_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Benchmarks({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="space-y-2">
        {data.benchmarks?.map((b, i) => (
          <div key={i} className="border rounded-xl p-4 flex items-center gap-4">
            <div className="flex-1">
              <div className="font-bold text-sm">{b.metric}</div>
              <div className="text-xs text-slate-500">{b.domain}</div>
            </div>
            <div className="text-center px-3">
              <div className="text-xs text-slate-400 uppercase">Current</div>
              <div className="font-black text-rose-700">{b.current}</div>
            </div>
            <div className="text-slate-300">→</div>
            <div className="text-center px-3">
              <div className="text-xs text-slate-400 uppercase">Target</div>
              <div className="font-black text-emerald-700">{b.benchmark}</div>
            </div>
            <div className="text-xs text-slate-500 max-w-[200px]">{b.best_in_class}</div>
          </div>
        ))}
      </div>
      <div className="text-xs text-slate-400 mt-2">Sources: {data.sources?.join(" · ")}</div>
    </div>
  );
}

function Recommendations({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <div className="text-xs font-bold text-emerald-700 uppercase mb-3">⚡ Quick Wins (0-90 days)</div>
          <div className="space-y-2">
            {data.quick_wins?.map((r, i) => (
              <div key={i} className="p-3 bg-emerald-50 rounded-lg text-xs">
                <div className="font-bold">{r.title}</div>
                <div className="text-slate-600 mt-0.5">{r.recommendation}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">{r.domain} · {r.category}</div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="text-xs font-bold text-indigo-700 uppercase mb-3">🎯 Strategic (90-365 days)</div>
          <div className="space-y-2">
            {data.strategic?.slice(0, 12).map((r, i) => (
              <div key={i} className="p-3 bg-indigo-50 rounded-lg text-xs">
                <div className="flex items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${r.risk === "Critical" ? "bg-rose-100 text-rose-700" : "bg-orange-100 text-orange-700"}`}>{r.risk}</span>
                  <span className="font-bold">{r.title}</span>
                </div>
                <div className="text-slate-600 mt-0.5">{r.recommendation}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      {data.investment_estimate && (
        <Callout label="Investment Estimate" color="amber">
          <div className="text-xs space-y-1">
            {Object.entries(data.investment_estimate).map(([k, v]) => (
              <div key={k}><strong className="capitalize">{k.replace(/_/g, " ")}:</strong> {v}</div>
            ))}
          </div>
        </Callout>
      )}
    </div>
  );
}

function Roadmap({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="space-y-3">
        {data.phases?.map((p, i) => (
          <div key={i} className={`border-l-4 ${i === 0 ? "border-rose-500" : i === 1 ? "border-amber-500" : "border-emerald-500"} rounded-r-xl p-4 bg-slate-50`}>
            <div className="font-black text-sm">{p.phase}</div>
            <div className="text-xs text-slate-600 mt-1"><strong>Focus:</strong> {p.focus}</div>
            <div className="text-xs text-slate-600 mt-1"><strong>Investment:</strong> {p.investment} · <strong>Team:</strong> {p.team}</div>
            <div className="mt-2 flex flex-wrap gap-1">
              {p.items?.map((item, j) => (
                <span key={j} className="text-[10px] px-2 py-0.5 rounded bg-white border">{item}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
      {data.governance && (
        <div className="bg-indigo-50 rounded-xl p-4 mt-3">
          <div className="text-xs font-bold text-indigo-700 uppercase mb-2">Program Governance</div>
          <div className="text-xs space-y-1">
            {Object.entries(data.governance).map(([k, v]) => (
              <div key={k}><strong className="capitalize">{k.replace(/_/g, " ")}:</strong> {v}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RoiAnalysis({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-rose-50 rounded-xl p-4">
          <div className="text-xs font-bold text-rose-700 uppercase mb-2">Investment Required</div>
          <div className="space-y-1 text-xs">
            {data.investment && Object.entries(data.investment).map(([k, v]) => (
              <div key={k}><strong className="capitalize">{k.replace(/_/g, " ")}:</strong> {v}</div>
            ))}
          </div>
        </div>
        <div className="bg-emerald-50 rounded-xl p-4">
          <div className="text-xs font-bold text-emerald-700 uppercase mb-2">Annual Benefits</div>
          <div className="space-y-1 text-xs">
            {data.benefits && Object.entries(data.benefits).filter(([k]) => k !== "total_annual").map(([k, v]) => (
              <div key={k}><strong className="capitalize">{k.replace(/_/g, " ")}:</strong> {typeof v === "object" ? `${v.annual_value} — ${v.source}` : v}</div>
            ))}
          </div>
        </div>
      </div>
      <div className="bg-slate-900 text-white rounded-xl p-6 grid grid-cols-3 gap-4 text-center">
        <div><div className="text-xs opacity-60">Payback</div><div className="text-xl font-black mt-1">{data.payback_period}</div></div>
        <div><div className="text-xs opacity-60">ROI Multiple</div><div className="text-xl font-black mt-1">{data.roi_multiple}</div></div>
        <div><div className="text-xs opacity-60">Annual Benefit</div><div className="text-xl font-black mt-1">{data.benefits?.total_annual || "TBD"}</div></div>
      </div>
      {data.intangible_benefits && (
        <div><div className="text-xs font-bold text-slate-600 uppercase mb-2">Intangible Benefits</div>
        <ul className="text-sm space-y-1">{data.intangible_benefits.map((b, i) => <li key={i}>✓ {b}</li>)}</ul></div>
      )}
    </div>
  );
}

function Governance({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">{data.summary}</p>
      {data.three_lines_model && (
        <div className="grid md:grid-cols-3 gap-3">
          {Object.entries(data.three_lines_model).map(([key, line]) => (
            <div key={key} className={`p-4 rounded-xl ${key === "first_line" ? "bg-blue-50" : key === "second_line" ? "bg-purple-50" : "bg-emerald-50"}`}>
              <div className="font-black text-sm">{line.name}</div>
              <div className="text-xs text-slate-600 mt-1">{line.responsibility}</div>
              <ul className="text-xs mt-2 space-y-0.5">{line.key_activities?.map((a, i) => <li key={i}>• {a}</li>)}</ul>
            </div>
          ))}
        </div>
      )}
      {data.meeting_cadence && (
        <div><div className="text-xs font-bold text-slate-600 uppercase mb-2">Meeting Cadence</div>
        <table className="w-full text-xs"><thead><tr className="bg-slate-100 text-left"><th className="p-2 font-bold">Meeting</th><th className="p-2 font-bold">Frequency</th><th className="p-2 font-bold">Attendees</th><th className="p-2 font-bold">Purpose</th></tr></thead>
        <tbody>{data.meeting_cadence.map((m, i) => (
          <tr key={i} className="border-t"><td className="p-2 font-bold">{m.meeting}</td><td className="p-2">{m.frequency}</td><td className="p-2">{m.attendees}</td><td className="p-2 text-slate-600">{m.purpose}</td></tr>
        ))}</tbody></table></div>
      )}
      {data.kpis && (
        <div><div className="text-xs font-bold text-slate-600 uppercase mb-2">Governance KPIs</div>
        <div className="grid md:grid-cols-2 gap-2">{data.kpis.map((k, i) => (
          <div key={i} className="p-3 bg-slate-50 rounded-lg"><div className="font-bold text-sm">{k.kpi}</div><div className="text-xs text-emerald-700 font-bold mt-0.5">Target: {k.target}</div><div className="text-xs text-slate-500">{k.measurement}</div></div>
        ))}</div></div>
      )}
    </div>
  );
}
