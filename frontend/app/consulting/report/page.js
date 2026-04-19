"use client";
import { useState, useEffect, useRef } from "react";

export default function ConsultingReportPage() {
  const [meta, setMeta] = useState({});
  const [sections, setSections] = useState([]);
  const [pendingSections, setPendingSections] = useState([]);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [mode, setMode] = useState(""); // dd | demo | stream
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    const params = new URLSearchParams(window.location.search);
    const m = params.get("mode") || "stream";
    setMode(m);
    if (m === "demo") {
      loadDemo(params.get("id"));
    } else if (m === "dd") {
      loadFromDD();
    } else {
      const desc = params.get("description") || sessionStorage.getItem("consulting_description") || "";
      if (!desc) { setError("No description provided."); return; }
      setMeta({ description: desc });
      streamReport(desc);
    }
  }, []);

  async function loadDemo(demoId) {
    setStreaming(true); setDone(false);
    setPendingSections(["Loading preloaded report..."]);
    try {
      const r = await fetch("/api/pipeline", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: "consulting-demo", demo_id: demoId }),
      });
      const data = await r.json();
      if (data.error) { setError(data.error); setStreaming(false); return; }
      setMeta({ description: data.demo?.description, company: data.demo?.company, domains: data.domains, domain_names: data.domain_names, scenario_count: data.scenario_count, engagement_type: data.demo?.engagement_type, agents_involved: data.agents_involved });
      // Simulate streaming for visual effect
      for (let i = 0; i < data.sections.length; i++) {
        await new Promise(r => setTimeout(r, 300));
        setSections(prev => [...prev, data.sections[i]]);
      }
      setDone(true); setStreaming(false);
    } catch (e) { setError("Network error: " + e.message); setStreaming(false); }
  }

  async function loadFromDD() {
    setStreaming(true); setDone(false);
    setPendingSections(["Deploying AI agents..."]);
    try {
      const dd = JSON.parse(sessionStorage.getItem("consulting_dd") || "{}");
      const r = await fetch("/api/pipeline", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: "consulting-dd", company_profile: { company_name: dd.company_name, industry: dd.industry, revenue: dd.revenue, employees: dd.employees, erp_system: dd.erp_system, recent_changes: dd.recent_changes }, scope_selection: { primary_domains: dd.primary_domains, engagement_type: dd.engagement_type, pain_points: dd.pain_points }, current_state: { close_days: dd.close_days, automation_level: dd.automation_level, sox_applicable: dd.sox_applicable, recent_audit_findings: dd.recent_audit_findings, shared_services: dd.shared_services, additional_context: dd.additional_context } }),
      });
      const data = await r.json();
      if (data.error) { setError(data.error); setStreaming(false); return; }
      setMeta({ description: data.description, company: data.company_profile, domains: data.domains, domain_names: data.domain_names, scenario_count: data.scenario_count, engagement_type: data.engagement_type, agents_involved: data.agents_involved });
      for (let i = 0; i < data.sections.length; i++) {
        await new Promise(r => setTimeout(r, 400));
        setSections(prev => [...prev, data.sections[i]]);
      }
      setDone(true); setStreaming(false);
    } catch (e) { setError("Network error: " + e.message); setStreaming(false); }
  }

  async function streamReport(desc) {
    setStreaming(true); setSections([]); setDone(false);
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
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "start") { setMeta(prev => ({ ...prev, ...event })); setPendingSections(event.section_titles || []); }
            else if (event.type === "section") { setSections(s => [...s, event]); }
            else if (event.type === "done") { setDone(true); setStreaming(false); }
            else if (event.type === "error") { setError(event.error); setStreaming(false); }
          } catch {}
        }
      }
      setStreaming(false);
    } catch (e) { setError("Stream error: " + e.message); setStreaming(false); }
  }

  const description = meta.description || "";
  const company = meta.company || {};
  const domainNames = meta.domain_names || [];

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
          <div className="text-xs uppercase tracking-[3px] opacity-60 font-bold">PMGuru Consulting Pro — Research-Grade AI Advisory</div>
          <div className="text-xs uppercase tracking-wider opacity-50 mt-1">McKinsey · BCG · Bain · Deloitte · PwC · EY · KPMG — Blended Methodology</div>
          {company.name && <h1 className="text-3xl font-black mt-6">{company.name}</h1>}
          <p className="text-sm opacity-90 mt-2 leading-relaxed max-w-3xl">{description?.slice(0, 300) || "Loading..."}</p>
          {domainNames.length > 0 && (
            <div className="mt-6 flex gap-2 flex-wrap">
              {domainNames.map(d => <span key={d} className="px-3 py-1.5 rounded-full bg-white/10 text-xs font-bold">{d}</span>)}
              <span className="px-3 py-1.5 rounded-full bg-white/10 text-xs font-bold">{meta.scenario_count || "..."} scenarios evaluated</span>
              {meta.engagement_type && <span className="px-3 py-1.5 rounded-full bg-emerald-500/30 text-xs font-bold">{meta.engagement_type}</span>}
            </div>
          )}
          <div className="mt-8 text-xs opacity-70 grid grid-cols-3 gap-4 max-w-md">
            <div><div className="opacity-50 uppercase tracking-wider">Prepared by</div><div className="font-bold mt-1">PMGuru AI Advisory</div></div>
            <div><div className="opacity-50 uppercase tracking-wider">Date</div><div className="font-bold mt-1">{new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</div></div>
            <div><div className="opacity-50 uppercase tracking-wider">Classification</div><div className="font-bold mt-1">Confidential</div></div>
          </div>
        </div>

        {error && <div className="bg-rose-50 border-2 border-rose-300 rounded-xl p-4 mb-6"><pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre></div>}

        {streaming && (
          <div className="no-print bg-white rounded-xl border p-4 mb-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin" style={{ borderWidth: "3px" }}></div>
              <div className="flex-1">
                <div className="font-bold text-sm">AI consulting agents are analyzing {meta.scenario_count || "..."} scenarios...</div>
                <div className="text-xs text-slate-500">{sections.length} of {pendingSections.length || 9} sections complete</div>
              </div>
            </div>
            <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500" style={{ width: `${Math.max(5, (sections.length / Math.max(pendingSections.length || 9, 1)) * 100)}%` }} />
            </div>
          </div>
        )}

        <div className="space-y-6">
          {sections.map((s, i) => <ReportSection key={s.id || i} section={s} index={i} />)}
        </div>

        {done && (
          <div className="mt-10 pt-6 border-t border-slate-300 text-center text-xs text-slate-500">
            <div>Powered by PMGuru Consulting Intelligence · 20,060 scenario coverage · 12 domains · 8 AI agents</div>
            <div className="mt-1">McKinsey · BCG · Bain · Deloitte · PwC · EY · KPMG — Blended Methodology</div>
            <div className="mt-1">© {new Date().getFullYear()} PMGuru · Confidential — for authorized recipients only</div>
          </div>
        )}
      </div>
    </div>
  );
}

function ReportSection({ section, index }) {
  const agent = section.agent;
  return (
    <div className="report-section bg-white rounded-2xl shadow-sm border p-8 print:rounded-none print:shadow-none animate-fadeIn" style={{ animationDelay: "0.1s" }}>
      <style jsx>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } } .animate-fadeIn { animation: fadeIn 0.5s ease-out forwards; }`}</style>
      <div className="flex items-start justify-between gap-3 mb-1 pb-3 border-b border-slate-200">
        <div className="flex items-baseline gap-3">
          <span className="text-2xl">{section.icon}</span>
          <div>
            <div className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">Section {index + 1} · {section.style}</div>
            <h2 className="text-2xl font-black text-slate-900 mt-0.5">{section.title}</h2>
          </div>
        </div>
        {agent && (
          <div className="bg-slate-50 rounded-lg p-2 text-right shrink-0">
            <div className="text-sm">{agent.icon} <span className="font-bold text-xs">{agent.name}</span></div>
            <div className="text-[10px] text-slate-500">{agent.title} · {agent.firm_style}</div>
          </div>
        )}
      </div>
      {section.status === "error" ? <div className="text-rose-700 text-sm bg-rose-50 p-3 rounded-lg mt-4">{section.error}</div> : (
        <div className="mt-4">
          {section.id === "engagement_summary" && <EngagementSummary d={section.data} />}
          {section.id === "maturity_assessment" && <Maturity d={section.data} />}
          {section.id === "detailed_findings" && <Findings d={section.data} />}
          {section.id === "gap_analysis" && <GapAnalysis d={section.data} />}
          {section.id === "benchmarks" && <Benchmarks d={section.data} />}
          {section.id === "recommendations" && <Recs d={section.data} />}
          {section.id === "roadmap" && <Roadmap d={section.data} />}
          {section.id === "roi_analysis" && <ROI d={section.data} />}
          {section.id === "governance" && <Gov d={section.data} />}
        </div>
      )}
    </div>
  );
}

function CB({ label, children, color = "emerald" }) {
  return <div className={`bg-${color}-50 border-l-4 border-${color}-500 rounded p-3 my-3`}><div className={`text-[10px] font-bold text-${color}-700 uppercase tracking-wider`}>{label}</div><div className="text-sm text-slate-800 mt-1">{children}</div></div>;
}

function EngagementSummary({ d }) {
  return <div className="space-y-3"><CB label="Situation" color="slate">{d.situation}</CB><CB label="Complication" color="amber">{d.complication}</CB><CB label="Recommendation" color="emerald">{d.recommendation}</CB>{d.key_metrics && <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-4">{Object.entries(d.key_metrics).map(([k,v]) => <div key={k} className="bg-slate-900 text-white rounded-xl p-3 text-center"><div className="text-xl font-black">{v}</div><div className="text-[10px] opacity-60 mt-0.5 capitalize">{k.replace(/_/g," ")}</div></div>)}</div>}<p className="text-xs text-slate-500 italic mt-2">{d.methodology}</p></div>;
}

function Maturity({ d }) {
  return <div className="space-y-4"><p className="text-sm text-slate-700">{d.summary}</p>{d.maturity_scores && Object.entries(d.maturity_scores).map(([k,m]) => <div key={k} className="border rounded-xl p-4"><div className="flex items-center justify-between mb-2"><span className="font-black">{m.domain}</span><div className="flex gap-2 text-xs"><span className="px-2 py-0.5 rounded" style={{backgroundColor:m.color+"20",color:m.color}}>Level {m.current_level}: {m.current_name}</span><span className="text-slate-400">→</span><span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700">Target: Level {m.target_level}</span></div></div><div className="flex gap-1">{[1,2,3,4,5].map(l => <div key={l} className="flex-1 h-3 rounded-full" style={{backgroundColor:l<=m.current_level?m.color:l<=m.target_level?m.color+"30":"#e2e8f0"}} />)}</div><div className="text-xs text-slate-500 mt-1">{m.critical_count} critical · {m.high_count} high · {m.total_findings} total</div></div>)}</div>;
}

function Findings({ d }) {
  const [exp, setExp] = useState({});
  return <div className="space-y-4"><p className="text-sm text-slate-700">{d.summary}</p><div className="grid grid-cols-4 gap-2 mb-4">{d.risk_distribution && Object.entries(d.risk_distribution).map(([l,c]) => <div key={l} className={`text-center p-3 rounded-xl ${l==="Critical"?"bg-rose-100 text-rose-700":l==="High"?"bg-orange-100 text-orange-700":l==="Medium"?"bg-amber-100 text-amber-700":"bg-blue-100 text-blue-700"}`}><div className="text-2xl font-black">{c}</div><div className="text-[10px] font-bold uppercase">{l}</div></div>)}</div>{d.domains && Object.entries(d.domains).map(([dk,dd2]) => <div key={dk} className="border rounded-xl overflow-hidden"><button onClick={() => setExp(e => ({...e,[dk]:!e[dk]}))} className="w-full text-left p-4 bg-slate-50 hover:bg-slate-100 transition flex items-center justify-between"><span className="font-black">{dd2.icon} {dd2.domain_name} ({dd2.findings.length})</span><span className="text-slate-400">{exp[dk]?"▲":"▼"}</span></button>{exp[dk] && <div className="p-3 space-y-2">{dd2.findings.slice(0,15).map((f,i) => <div key={i} className="flex items-start gap-3 p-2 bg-slate-50 rounded text-xs"><span className={`px-1.5 py-0.5 rounded font-bold text-[10px] shrink-0 ${f.risk_level==="Critical"?"bg-rose-100 text-rose-700":f.risk_level==="High"?"bg-orange-100 text-orange-700":"bg-amber-100 text-amber-700"}`}>{f.risk_level}</span><div className="flex-1"><div className="font-bold">{f.title}</div><div className="text-slate-600 mt-0.5">{f.finding}</div><div className="text-emerald-700 mt-0.5">→ {f.recommendation}</div></div></div>)}</div>}</div>)}</div>;
}

function GapAnalysis({ d }) {
  return <div className="space-y-4"><p className="text-sm text-slate-700">{d.summary}</p><div className="overflow-x-auto"><table className="w-full text-xs"><thead><tr className="bg-slate-100 text-left"><th className="p-2 font-bold">Domain</th><th className="p-2 font-bold">Process</th><th className="p-2 font-bold">Current</th><th className="p-2 font-bold">Target</th><th className="p-2 font-bold">Gap</th></tr></thead><tbody>{d.gaps?.slice(0,20).map((g,i) => <tr key={i} className="border-t"><td className="p-2 text-slate-600">{g.domain}</td><td className="p-2 font-bold">{g.process_area}</td><td className="p-2"><span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 text-[10px]">{g.current_state}</span></td><td className="p-2"><span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 text-[10px]">{g.target_state}</span></td><td className="p-2"><span className={`font-bold ${g.gap_severity==="High"?"text-rose-700":"text-amber-700"}`}>{g.gap_severity}</span></td></tr>)}</tbody></table></div></div>;
}

function Benchmarks({ d }) {
  return <div className="space-y-4"><p className="text-sm text-slate-700">{d.summary}</p>{d.benchmarks?.map((b,i) => <div key={i} className="border rounded-xl p-4 flex items-center gap-4"><div className="flex-1"><div className="font-bold text-sm">{b.metric}</div><div className="text-xs text-slate-500">{b.domain}</div></div><div className="text-center px-3"><div className="text-[10px] text-slate-400 uppercase">Current</div><div className="font-black text-rose-700">{b.current}</div></div><div className="text-slate-300">→</div><div className="text-center px-3"><div className="text-[10px] text-slate-400 uppercase">Target</div><div className="font-black text-emerald-700">{b.benchmark}</div></div><div className="text-xs text-slate-500 max-w-[180px]">{b.best_in_class}</div></div>)}<div className="text-xs text-slate-400">Sources: {d.sources?.join(" · ")}</div></div>;
}

function Recs({ d }) {
  return <div className="space-y-4"><p className="text-sm text-slate-700">{d.summary}</p><div className="grid md:grid-cols-2 gap-4"><div><div className="text-xs font-bold text-emerald-700 uppercase mb-3">⚡ Quick Wins (0-90 days)</div>{d.quick_wins?.map((r,i) => <div key={i} className="p-3 bg-emerald-50 rounded-lg text-xs mb-2"><div className="font-bold">{r.title}</div><div className="text-slate-600 mt-0.5">{r.recommendation}</div></div>)}</div><div><div className="text-xs font-bold text-indigo-700 uppercase mb-3">🎯 Strategic (90-365 days)</div>{d.strategic?.slice(0,10).map((r,i) => <div key={i} className="p-3 bg-indigo-50 rounded-lg text-xs mb-2"><div className="flex items-center gap-2"><span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${r.risk==="Critical"?"bg-rose-100 text-rose-700":"bg-orange-100 text-orange-700"}`}>{r.risk}</span><span className="font-bold">{r.title}</span></div><div className="text-slate-600 mt-0.5">{r.recommendation}</div></div>)}</div></div>{d.investment_estimate && <CB label="Investment Estimate" color="amber"><div className="text-xs space-y-1">{Object.entries(d.investment_estimate).map(([k,v]) => <div key={k}><strong className="capitalize">{k.replace(/_/g," ")}:</strong> {v}</div>)}</div></CB>}</div>;
}

function Roadmap({ d }) {
  return <div className="space-y-4"><p className="text-sm text-slate-700">{d.summary}</p>{d.phases?.map((p,i) => <div key={i} className={`border-l-4 ${i===0?"border-rose-500":i===1?"border-amber-500":"border-emerald-500"} rounded-r-xl p-4 bg-slate-50`}><div className="font-black text-sm">{p.phase}</div><div className="text-xs text-slate-600 mt-1"><strong>Focus:</strong> {p.focus} · <strong>Investment:</strong> {p.investment}</div><div className="mt-2 flex flex-wrap gap-1">{p.items?.map((item,j) => <span key={j} className="text-[10px] px-2 py-0.5 rounded bg-white border">{item}</span>)}</div></div>)}{d.governance && <div className="bg-indigo-50 rounded-xl p-4"><div className="text-xs font-bold text-indigo-700 uppercase mb-2">Program Governance</div><div className="text-xs space-y-1">{Object.entries(d.governance).map(([k,v]) => <div key={k}><strong className="capitalize">{k.replace(/_/g," ")}:</strong> {v}</div>)}</div></div>}</div>;
}

function ROI({ d }) {
  return <div className="space-y-4"><p className="text-sm text-slate-700">{d.summary}</p><div className="grid md:grid-cols-2 gap-4"><div className="bg-rose-50 rounded-xl p-4"><div className="text-xs font-bold text-rose-700 uppercase mb-2">Investment</div><div className="space-y-1 text-xs">{d.investment && Object.entries(d.investment).map(([k,v]) => <div key={k}><strong className="capitalize">{k.replace(/_/g," ")}:</strong> {v}</div>)}</div></div><div className="bg-emerald-50 rounded-xl p-4"><div className="text-xs font-bold text-emerald-700 uppercase mb-2">Benefits</div><div className="space-y-1 text-xs">{d.benefits && Object.entries(d.benefits).filter(([k]) => k!=="total_annual").map(([k,v]) => <div key={k}><strong className="capitalize">{k.replace(/_/g," ")}:</strong> {typeof v==="object"?`${v.annual_value} — ${v.source}`:v}</div>)}</div></div></div><div className="bg-slate-900 text-white rounded-xl p-6 grid grid-cols-3 gap-4 text-center"><div><div className="text-xs opacity-60">Payback</div><div className="text-xl font-black mt-1">{d.payback_period}</div></div><div><div className="text-xs opacity-60">ROI</div><div className="text-xl font-black mt-1">{d.roi_multiple}</div></div><div><div className="text-xs opacity-60">Annual Benefit</div><div className="text-xl font-black mt-1">{d.benefits?.total_annual||"TBD"}</div></div></div>{d.intangible_benefits && <div><div className="text-xs font-bold text-slate-600 uppercase mb-2">Intangible Benefits</div><ul className="text-sm space-y-1">{d.intangible_benefits.map((b,i) => <li key={i}>✓ {b}</li>)}</ul></div>}</div>;
}

function Gov({ d }) {
  return <div className="space-y-4"><p className="text-sm text-slate-700">{d.summary}</p>{d.three_lines_model && <div className="grid md:grid-cols-3 gap-3">{Object.entries(d.three_lines_model).map(([k,l]) => <div key={k} className={`p-4 rounded-xl ${k==="first_line"?"bg-blue-50":k==="second_line"?"bg-purple-50":"bg-emerald-50"}`}><div className="font-black text-sm">{l.name}</div><div className="text-xs text-slate-600 mt-1">{l.responsibility}</div><ul className="text-xs mt-2 space-y-0.5">{l.key_activities?.map((a,i) => <li key={i}>• {a}</li>)}</ul></div>)}</div>}{d.kpis && <div><div className="text-xs font-bold text-slate-600 uppercase mb-2">KPIs</div><div className="grid md:grid-cols-2 gap-2">{d.kpis.map((k,i) => <div key={i} className="p-3 bg-slate-50 rounded-lg"><div className="font-bold text-sm">{k.kpi}</div><div className="text-xs text-emerald-700 font-bold">Target: {k.target}</div></div>)}</div></div>}</div>;
}
