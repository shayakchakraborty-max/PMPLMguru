"use client";
import {useState, useEffect} from "react";

const C = ["from-indigo-500 to-purple-600","from-emerald-500 to-teal-600","from-amber-500 to-orange-600","from-rose-500 to-pink-600","from-sky-500 to-blue-600","from-violet-500 to-fuchsia-600"];

const STAGES = [
  {label: "🧠 PM Planning (detailed)", detail: "Methodology + project plan + 10 risks"},
  {label: "🛠️ PM Tool", detail: "Custom Kanban board"},
  {label: "⚡ 6-Phase PLM", detail: "Init→Req→Design+Dev→QA→Deploy→Monitor"},
  {label: "🎨 Prototype", detail: "SaaS landing page"},
];

function download(content, filename, type="text/html") {
  try {
    const blob = new Blob([content], {type});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(()=>URL.revokeObjectURL(url), 1000);
  } catch(e) { alert("Download failed: "+e.message); }
}

function downloadPDF(elementId, title) {
  const el = document.getElementById(elementId);
  if (!el) { alert("Report not found"); return; }
  const w = window.open("", "_blank");
  if (!w) { alert("Allow popups to download PDF"); return; }
  w.document.write(`<!DOCTYPE html><html><head><title>${title}</title><script src="https://cdn.tailwindcss.com"></script><style>@media print{.break{page-break-before:always}.no-print{display:none}}body{font-family:system-ui;padding:30px;background:#f8fafc}</style></head><body>${el.innerHTML}</body></html>`);
  w.document.close();
  setTimeout(()=>{try{w.print()}catch(e){}}, 1500);
}

// Renders any agent's JSON data recursively into beautiful cards
function RenderFields({data, exclude=[]}) {
  if (!data || typeof data !== "object") return null;
  const entries = Object.entries(data).filter(([k]) => !exclude.includes(k) && !["summary","layman_summary","error","raw"].includes(k));
  return (<div className="space-y-3">
    {entries.map(([key, val]) => {
      const label = key.replace(/_/g, " ").toUpperCase();
      if (typeof val === "string") return (<div key={key} className="bg-white/10 p-3 rounded-lg"><div className="text-[10px] font-bold opacity-70">{label}</div><div className="text-sm mt-1">{val}</div></div>);
      if (typeof val === "number") return (<div key={key} className="bg-white/10 p-3 rounded-lg flex justify-between"><span className="text-[10px] font-bold opacity-70">{label}</span><span className="text-sm font-bold">{val}</span></div>);
      if (Array.isArray(val)) {
        if (val.length === 0) return null;
        if (typeof val[0] === "string") return (<div key={key} className="bg-white/10 p-3 rounded-lg"><div className="text-[10px] font-bold opacity-70 mb-2">{label}</div><ul className="text-sm space-y-1">{val.map((v,i)=><li key={i}>• {v}</li>)}</ul></div>);
        if (typeof val[0] === "object") return (<div key={key} className="bg-white/10 p-3 rounded-lg"><div className="text-[10px] font-bold opacity-70 mb-2">{label}</div><div className="space-y-2">{val.map((v,i)=><div key={i} className="bg-white/10 p-2 rounded text-xs">{Object.entries(v).map(([k2,v2])=>(<div key={k2}><b>{k2.replace(/_/g," ")}:</b> {typeof v2==="object"?JSON.stringify(v2).slice(0,100):String(v2).slice(0,200)}</div>))}</div>)}</div></div>);
      }
      if (typeof val === "object" && val !== null) return (<div key={key} className="bg-white/10 p-3 rounded-lg"><div className="text-[10px] font-bold opacity-70 mb-2">{label}</div><div className="text-xs space-y-1">{Object.entries(val).map(([k2,v2])=>(<div key={k2}><b>{k2.replace(/_/g," ")}:</b> {typeof v2==="object"?JSON.stringify(v2).slice(0,150):String(v2).slice(0,200)}</div>))}</div></div>);
      return null;
    })}
  </div>);
}

export default function Auto() {
  const [idea, setIdea] = useState("");
  const [status, setStatus] = useState("idle");
  const [data, setData] = useState(null);
  const [activeStage, setActiveStage] = useState(0);
  const [showTool, setShowTool] = useState(false);
  const [showProto, setShowProto] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (status !== "running") return;
    const t = setInterval(() => setActiveStage(s => s < 3 ? s + 1 : s), 20000);
    return () => clearInterval(t);
  }, [status]);

  const runAutopilot = async () => {
    if (!idea.trim()) { alert("Please enter an idea"); return; }
    setStatus("running"); setActiveStage(0); setData(null); setErrorMsg("");
    try {
      const r = await fetch("/api/autopilot", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({idea})});
      if (!r.ok) throw new Error(`Server returned ${r.status}`);
      const j = await r.json();
      if (j.error) throw new Error(j.error);
      setData(j); setActiveStage(4); setStatus("done");
    } catch(e) { setErrorMsg(e.message); setStatus("error"); }
  };

  const reset = () => { setStatus("idle"); setIdea(""); setData(null); setActiveStage(0); setShowTool(false); setShowProto(false); setErrorMsg(""); };

  const pmAgents = data?.stages?.pm_planning?.pm_agents || {};
  const methodology = pmAgents["Methodology Expert"]?.data || {};
  const plannerData = pmAgents["Project Planner"]?.data || {};
  const riskData = pmAgents["Risk Manager"]?.data || {};
  const pmToolHTML = data?.stages?.pm_tool?.html || "";
  const boardData = data?.stages?.pm_tool?.board_data || {};
  const plmPhases = data?.stages?.plm_execution?.phases || [];
  const prototypeHTML = data?.stages?.prototype?.html || "";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6 bg-white rounded-2xl shadow-xl p-6 border-t-4 border-indigo-600">
          <h1 className="text-4xl font-black bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">🤖 PMGuru v12 · Detailed Autopilot</h1>
          <p className="text-slate-600 mt-1">Detailed PM Plan + 6-Phase PLM (Init → Requirements → Design+Dev → QA → Deploy → Monitor)</p>
        </header>

        {status === "idle" && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-black mb-2">💡 Enter Your Project Idea</h2>
            <p className="text-sm text-slate-500 mb-4">PMGuru will generate a detailed PM plan, custom PM tool, 6-phase PLM report, and working prototype. Each section is specific to your idea (not generic). Takes 3-5 minutes.</p>
            <textarea value={idea} onChange={e=>setIdea(e.target.value)} rows={5}
              placeholder="e.g. AI-powered grocery assistant for Indian kirana stores with voice ordering, GST billing, and inventory management..."
              className="w-full p-4 border-2 border-indigo-200 rounded-xl focus:border-indigo-500 outline-none"/>
            <button onClick={runAutopilot} className="mt-4 w-full px-8 py-5 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-xl font-black text-xl shadow-xl hover:scale-[1.02] transition-all">
              🚀 RUN FULL AUTOPILOT
            </button>
          </div>
        )}

        {status === "running" && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-black mb-6 text-center">🤖 Autopilot Running — Detailed Mode</h2>
            <div className="space-y-3">
              {STAGES.map((s, i) => {
                const done = i < activeStage, active = i === activeStage;
                return (
                  <div key={i} className={`p-4 rounded-xl transition-all ${done ? `bg-gradient-to-r ${C[i%6]} text-white` : active ? "bg-indigo-100 animate-pulse" : "bg-slate-50"}`}>
                    <div className="flex items-center gap-3">
                      <div className="text-3xl">{done ? "✅" : active ? "⚙️" : "⏳"}</div>
                      <div className="flex-1"><div className="font-bold">{s.label}</div><div className="text-xs opacity-80">{s.detail}</div></div>
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="text-xs text-slate-400 text-center mt-4">Detailed mode takes 3-5 minutes. Do not close this tab.</p>
          </div>
        )}

        {status === "error" && (
          <div className="bg-white rounded-2xl shadow-xl p-8 border-l-4 border-rose-500">
            <h2 className="text-2xl font-black text-rose-600">❌ Error</h2>
            <p className="text-sm text-slate-600 mt-2">{errorMsg}</p>
            <button onClick={reset} className="mt-4 px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold">🔄 Try Again</button>
          </div>
        )}

        {status === "done" && data && (
          <div className="space-y-6 animate-fadeIn">
            <div className="bg-white rounded-2xl shadow-xl p-5 no-print sticky top-4 z-20 border-2 border-indigo-200">
              <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                <div><h2 className="text-lg font-black text-emerald-600">✅ Autopilot Complete</h2><p className="text-xs text-slate-500">All deliverables ready</p></div>
                <button onClick={reset} className="px-4 py-2 bg-slate-200 rounded-lg font-bold text-sm">🔄 New Project</button>
              </div>
              <div className="flex gap-2 flex-wrap">
                <button onClick={()=>downloadPDF("full-report", "PMGuru Report")} className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-bold text-sm">📄 Download Full PDF</button>
                <button onClick={()=>download(pmToolHTML, "pm-tool.html")} className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-bold text-sm">🛠️ Download PM Tool</button>
                <button onClick={()=>download(prototypeHTML, "prototype.html")} className="px-4 py-2 bg-gradient-to-r from-rose-600 to-pink-600 text-white rounded-lg font-bold text-sm">🎨 Download Prototype</button>
                <button onClick={()=>setShowTool(!showTool)} className="px-4 py-2 bg-slate-100 rounded-lg font-bold text-sm">{showTool?"Hide":"👁️"} PM Tool</button>
                <button onClick={()=>setShowProto(!showProto)} className="px-4 py-2 bg-slate-100 rounded-lg font-bold text-sm">{showProto?"Hide":"👁️"} Prototype</button>
              </div>
            </div>

            {showTool && pmToolHTML && (<div className="bg-white rounded-2xl shadow-xl p-4 no-print"><h3 className="text-xl font-black mb-3">🛠️ PM Tool Preview</h3><iframe srcDoc={pmToolHTML} className="w-full h-[700px] rounded-xl border-2 border-purple-200"/></div>)}
            {showProto && prototypeHTML && (<div className="bg-white rounded-2xl shadow-xl p-4 no-print"><h3 className="text-xl font-black mb-3">🎨 Prototype Preview</h3><iframe srcDoc={prototypeHTML} className="w-full h-[700px] rounded-xl border-2 border-pink-200"/></div>)}

            <div id="full-report" className="space-y-6">
              <div className="bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-white rounded-3xl p-10">
                <div className="text-xs uppercase tracking-[3px] opacity-60">PMGuru Detailed Report</div>
                <h1 className="text-4xl font-black mt-2">{idea}</h1>
                <div className="mt-4 text-sm opacity-70">PMGuru v12 · {new Date().toLocaleDateString()}</div>
              </div>

              {/* METHODOLOGY - DETAILED */}
              {methodology.recommended_method && (
                <div className="bg-white rounded-2xl shadow-xl p-8 border-l-8 border-indigo-600 break">
                  <div className="text-xs font-bold text-indigo-600 tracking-wider">🎯 PART 1: METHODOLOGY RECOMMENDATION</div>
                  <div className="mt-3 flex items-baseline gap-4 flex-wrap">
                    <h2 className="text-5xl font-black text-slate-900">{methodology.recommended_method}</h2>
                    {methodology.confidence && <span className="text-xs bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full font-bold">{methodology.confidence} Confidence</span>}
                  </div>
                  {methodology.layman_explanation && (<div className="mt-4 p-5 bg-amber-50 border-l-4 border-amber-400 rounded-r-xl"><div className="text-xs font-bold text-amber-700 mb-2">💡 IN PLAIN ENGLISH</div><p className="text-slate-700">{methodology.layman_explanation}</p></div>)}
                  {methodology.reasoning && (<div className="mt-4"><div className="text-xs font-bold text-slate-500 mb-1">DETAILED REASONING</div><p className="text-slate-700 italic border-l-4 border-slate-300 pl-4 whitespace-pre-wrap">{methodology.reasoning}</p></div>)}
                  {methodology.fit_analysis && (<div className="mt-5 grid md:grid-cols-2 gap-3">{Object.entries(methodology.fit_analysis).map(([k,v])=>(<div key={k} className="p-4 bg-indigo-50 rounded-xl"><div className="text-xs font-bold text-indigo-600">{k.replace(/_/g," ").toUpperCase()}</div><div className="text-sm mt-1 text-slate-700">{v}</div></div>))}</div>)}
                  {methodology.method_details && (<div className="grid md:grid-cols-2 gap-3 mt-5">{Object.entries(methodology.method_details).map(([k,v])=>(<div key={k} className="p-4 bg-purple-50 rounded-xl"><div className="text-xs font-bold text-purple-600">{k.toUpperCase()}</div><div className="text-sm mt-2 text-slate-700">{Array.isArray(v)?v.join(", "):v}</div></div>))}</div>)}
                  {methodology.tool_recommendation && (<div className="mt-5 p-5 bg-gradient-to-r from-slate-900 to-indigo-900 rounded-xl text-white"><div className="text-xs font-bold opacity-60">RECOMMENDED PM TOOL</div><div className="text-2xl font-black mt-1">{methodology.tool_recommendation.primary}</div>{methodology.tool_recommendation.alternatives && <div className="text-xs mt-2 opacity-80">Alternatives: {methodology.tool_recommendation.alternatives.join(", ")}</div>}{methodology.tool_recommendation.reason && <div className="text-xs mt-1 opacity-70 italic">{methodology.tool_recommendation.reason}</div>}</div>)}
                  {methodology.why_not_others && (<div className="mt-5"><div className="text-xs font-bold text-slate-500 mb-2">WHY NOT OTHER METHODS</div><div className="space-y-2">{methodology.why_not_others.map((w,i)=>(<div key={i} className="p-3 bg-slate-50 rounded border-l-2 border-slate-300"><div className="font-bold text-sm">{w.method}</div><div className="text-xs text-slate-600 mt-1">{w.simple_reason || w.reason}</div></div>))}</div></div>)}
                  {methodology.success_factors && (<div className="mt-5 p-4 bg-emerald-50 rounded-xl"><div className="text-xs font-bold text-emerald-700 mb-2">✅ CRITICAL SUCCESS FACTORS</div><ul className="text-sm space-y-1">{methodology.success_factors.map((s,i)=><li key={i}>• {s}</li>)}</ul></div>)}
                </div>
              )}

              {/* PROJECT PLAN - DETAILED */}
              {plannerData.executive_summary && (
                <div className="bg-white rounded-2xl shadow-xl p-8 break">
                  <div className="text-xs font-bold text-emerald-600 tracking-wider">📊 PART 2: DETAILED PROJECT PLAN</div>
                  {plannerData.layman_summary && (<div className="mt-3 p-5 bg-amber-50 border-l-4 border-amber-400 rounded-r-xl"><div className="text-xs font-bold text-amber-700 mb-2">💡 IN PLAIN ENGLISH</div><p className="text-slate-700">{plannerData.layman_summary}</p></div>)}
                  <div className="mt-4"><div className="text-xs font-bold text-slate-500 mb-1">EXECUTIVE SUMMARY</div><p className="text-slate-700 whitespace-pre-wrap">{plannerData.executive_summary}</p></div>
                  {plannerData.business_context && (<div className="mt-4"><div className="text-xs font-bold text-slate-500 mb-1">BUSINESS CONTEXT</div><p className="text-slate-700 whitespace-pre-wrap">{plannerData.business_context}</p></div>)}
                  {plannerData.objectives && (<div className="mt-4 p-4 bg-indigo-50 rounded-xl"><div className="text-xs font-bold text-indigo-600 mb-2">OBJECTIVES</div><div className="text-sm mb-2"><b>Primary:</b> {plannerData.objectives.primary}</div>{plannerData.objectives.secondary && <ul className="text-sm space-y-1">{plannerData.objectives.secondary.map((o,i)=><li key={i}>• {o}</li>)}</ul>}</div>)}
                  {plannerData.scope && (<div className="mt-4 grid md:grid-cols-2 gap-3">{Object.entries(plannerData.scope).map(([k,v])=>(<div key={k} className="p-4 bg-slate-50 rounded-xl"><div className="text-xs font-bold text-slate-600 mb-2">{k.toUpperCase().replace(/_/g," ")}</div><ul className="text-sm space-y-1">{(Array.isArray(v)?v:[v]).map((item,i)=><li key={i}>• {item}</li>)}</ul></div>))}</div>)}
                  {plannerData.budget_estimate && (<div className="mt-4 p-5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl"><div className="text-xs opacity-80">BUDGET ESTIMATE</div><div className="text-3xl font-black">{plannerData.budget_estimate.total}</div>{plannerData.budget_estimate.breakdown && (<div className="flex gap-3 mt-2 text-xs flex-wrap">{Object.entries(plannerData.budget_estimate.breakdown).map(([k,v])=>(<div key={k}><b>{k.replace(/_/g," ")}:</b> {v}</div>))}</div>)}{plannerData.budget_estimate.rationale && <div className="text-xs mt-2 opacity-80">{plannerData.budget_estimate.rationale}</div>}</div>)}
                  {plannerData.timeline && (<div className="mt-3 p-4 bg-slate-50 rounded-xl"><div className="text-xs font-bold text-slate-500">TIMELINE</div><div className="text-xl font-black">{plannerData.timeline.total_duration}</div><div className="text-xs mt-1">{plannerData.timeline.start} → {plannerData.timeline.end}</div>{plannerData.timeline.critical_path && <div className="text-xs mt-2 italic">Critical path: {plannerData.timeline.critical_path}</div>}</div>)}
                  {plannerData.phases && Array.isArray(plannerData.phases) && (<div className="mt-5"><div className="text-xs font-bold text-slate-500 mb-2">PROJECT PHASES</div><div className="space-y-2">{plannerData.phases.map((ph,i)=>(<div key={i} className={`p-4 rounded-xl bg-gradient-to-r ${C[i%6]} text-white`}><div className="flex justify-between items-start flex-wrap gap-2"><b className="text-lg">{ph.name}</b><span className="text-xs bg-white/20 px-2 py-1 rounded">{ph.duration}</span></div>{ph.what_happens && <div className="text-xs mt-2 opacity-90">{ph.what_happens}</div>}{ph.key_deliverables && <div className="text-xs mt-2"><b>Deliverables:</b> {ph.key_deliverables.join(", ")}</div>}{ph.exit_criteria && <div className="text-xs mt-1 opacity-80"><b>Exit:</b> {ph.exit_criteria}</div>}</div>))}</div></div>)}
                  {plannerData.team_composition && (<div className="mt-5"><div className="text-xs font-bold text-slate-500 mb-2">TEAM COMPOSITION</div><div className="space-y-2">{plannerData.team_composition.map((t,i)=>(<div key={i} className="p-3 bg-slate-50 rounded-xl"><div className="flex justify-between"><b>{t.count}× {t.seniority} {t.role}</b>{t.when_needed && <span className="text-xs text-slate-500">{t.when_needed}</span>}</div>{t.responsibilities && <div className="text-xs text-slate-600 mt-1">{t.responsibilities}</div>}</div>))}</div></div>)}
                  {plannerData.kpis && (<div className="mt-5"><div className="text-xs font-bold text-slate-500 mb-2">KPIs</div><div className="space-y-2">{plannerData.kpis.map((k,i)=>(<div key={i} className="p-3 bg-purple-50 rounded-xl"><div className="flex justify-between"><b>{k.metric}</b><span className="text-purple-700 font-bold">{k.target}</span></div>{k.why_it_matters && <div className="text-xs mt-1 text-slate-600">{k.why_it_matters}</div>}</div>))}</div></div>)}
                  {plannerData.dependencies && (<div className="mt-4 p-3 bg-amber-50 rounded-xl"><div className="text-xs font-bold text-amber-700 mb-1">DEPENDENCIES</div><ul className="text-sm space-y-1">{plannerData.dependencies.map((d,i)=><li key={i}>• {d}</li>)}</ul></div>)}
                </div>
              )}

              {/* RISKS */}
              {riskData.risk_register && (
                <div className="bg-white rounded-2xl shadow-xl p-8 break">
                  <div className="text-xs font-bold text-rose-600 tracking-wider">🛡️ PART 3: RISK REGISTER (10 RISKS)</div>
                  {riskData.layman_summary && (<div className="mt-3 p-5 bg-amber-50 border-l-4 border-amber-400 rounded-r-xl"><div className="text-xs font-bold text-amber-700 mb-2">💡 IN PLAIN ENGLISH</div><p className="text-slate-700">{riskData.layman_summary}</p></div>)}
                  {riskData.executive_summary && <p className="mt-3 text-slate-700 whitespace-pre-wrap">{riskData.executive_summary}</p>}
                  <div className="mt-4 space-y-3">
                    {riskData.risk_register.map((r,i)=>(
                      <div key={i} className="p-4 bg-rose-50 rounded-xl border-l-4 border-rose-500">
                        <div className="flex justify-between items-start flex-wrap gap-2">
                          <div><b className="text-sm">{r.id}: {r.simple_description || r.description}</b>{r.category && <span className="ml-2 text-[10px] bg-slate-200 px-2 py-1 rounded">{r.category}</span>}</div>
                          <span className="text-xs bg-rose-600 text-white px-2 py-1 rounded">P×I: {r.score}</span>
                        </div>
                        <div className="text-xs mt-2 text-slate-600"><b>Mitigation:</b> {r.simple_mitigation || r.mitigation}</div>
                        {r.contingency && <div className="text-xs mt-1 text-slate-600"><b>Contingency:</b> {r.contingency}</div>}
                        {r.owner && <div className="text-xs mt-1 text-slate-500"><b>Owner:</b> {r.owner}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* PM TOOL SUMMARY */}
              {boardData.board_title && (
                <div className="bg-gradient-to-br from-purple-600 via-pink-600 to-rose-600 text-white rounded-3xl p-8 break">
                  <div className="text-xs uppercase tracking-widest opacity-80">🛠️ PART 4: CUSTOM PM TOOL</div>
                  <h2 className="text-2xl font-black mt-2">{boardData.board_title}</h2>
                  <div className="flex gap-6 mt-4 text-sm flex-wrap">
                    <div><div className="opacity-70 text-xs">METHOD</div><div className="font-bold">{boardData.methodology}</div></div>
                    <div><div className="opacity-70 text-xs">TASKS</div><div className="font-bold">{(boardData.cards||[]).length}</div></div>
                    <div><div className="opacity-70 text-xs">TEAM</div><div className="font-bold">{(boardData.team_members||[]).length}</div></div>
                    <div><div className="opacity-70 text-xs">VELOCITY</div><div className="font-bold">{boardData.velocity_target||0} pts</div></div>
                  </div>
                </div>
              )}

              {/* 6-PHASE PLM REPORT */}
              <div className="bg-gradient-to-br from-emerald-600 via-teal-700 to-cyan-700 text-white rounded-3xl p-10 break">
                <div className="text-xs uppercase tracking-[3px] opacity-60">PART 5: PRODUCT LIFECYCLE EXECUTION</div>
                <h2 className="text-3xl font-black mt-2">6-Phase PLM Pipeline</h2>
                <p className="text-sm opacity-80 mt-2">Initiation → Requirements → Design+Dev → Testing → Deployment → Monitoring</p>
              </div>

              {plmPhases.map((ph, i) => (
                <div key={ph.id} className={`p-6 rounded-2xl bg-gradient-to-br ${C[i%6]} text-white shadow-xl break`}>
                  <div className="flex items-start gap-4">
                    <div className="text-6xl font-black opacity-30">{ph.id}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between flex-wrap gap-2">
                        <div><h3 className="text-2xl font-black">{ph.agent_icon} Phase {ph.id}: {ph.name}</h3><p className="text-xs opacity-90">{ph.agent_role} · {ph.duration}</p></div>
                        <span className="text-xs bg-white/20 px-3 py-1 rounded-full">{ph.status === "error" ? "⚠️" : "✅"}</span>
                      </div>
                      {ph.data?.layman_summary && (<div className="mt-3 p-3 bg-white/10 rounded-lg"><div className="text-xs font-bold opacity-70 mb-1">💡 IN PLAIN ENGLISH</div><p className="text-sm">{ph.data.layman_summary}</p></div>)}
                      {ph.data?.summary && (<p className="mt-3 text-sm italic opacity-90 border-l-4 border-white/40 pl-3 whitespace-pre-wrap">{ph.data.summary}</p>)}
                      <div className="mt-4"><RenderFields data={ph.data}/></div>
                      {ph.status === "error" && (<div className="mt-3 p-3 bg-rose-900/30 rounded-lg text-xs">⚠️ Error: {ph.error || "unknown"}</div>)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
