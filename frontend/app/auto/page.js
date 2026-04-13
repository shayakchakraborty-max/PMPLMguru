"use client";
import {useState} from "react";

const C = ["from-indigo-500 to-purple-600","from-emerald-500 to-teal-600","from-amber-500 to-orange-600","from-rose-500 to-pink-600","from-sky-500 to-blue-600","from-violet-500 to-fuchsia-600","from-lime-500 to-green-600","from-cyan-500 to-blue-500"];

function PMReport({data}) {
  if (!data?.pm_agents) return null;
  const agents = data.pm_agents;
  return (<div id="pm-report" className="space-y-4">
    <div className="bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-white rounded-3xl p-10">
      <div className="text-xs uppercase tracking-[3px] opacity-60">PROJECT MANAGEMENT STRATEGIC REPORT</div>
      <h1 className="text-4xl font-black mt-2">{data.idea}</h1>
      <div className="mt-4 text-sm opacity-70">PMGuru Advisory · {new Date().toLocaleDateString()} · Prepared by 4 PM Experts</div>
    </div>
    
    {/* Methodology Recommendation */}
    {agents["Methodology Expert"]?.data && (()=>{const m=agents["Methodology Expert"].data;return(
      <div className="bg-white rounded-2xl shadow-xl p-8 border-l-8 border-indigo-600 break">
        <div className="text-xs font-bold text-indigo-600 tracking-wider">🎯 METHODOLOGY RECOMMENDATION</div>
        <div className="mt-3 flex items-baseline gap-4">
          <h2 className="text-5xl font-black text-slate-900">{m.recommended_method}</h2>
          <span className="text-xs bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full font-bold">{m.confidence} Confidence</span>
        </div>
        <p className="text-slate-700 mt-3 italic border-l-4 border-slate-300 pl-4">{m.reasoning}</p>
        
        {m.method_details && <div className="grid md:grid-cols-2 gap-3 mt-5">
          {m.method_details.roles && <div className="p-4 bg-indigo-50 rounded-xl"><div className="text-xs font-bold text-indigo-600">ROLES</div><div className="text-sm mt-2">{m.method_details.roles.join(", ")}</div></div>}
          {m.method_details.ceremonies && <div className="p-4 bg-purple-50 rounded-xl"><div className="text-xs font-bold text-purple-600">CEREMONIES</div><div className="text-sm mt-2">{m.method_details.ceremonies.join(", ")}</div></div>}
          {m.method_details.artifacts && <div className="p-4 bg-pink-50 rounded-xl"><div className="text-xs font-bold text-pink-600">ARTIFACTS</div><div className="text-sm mt-2">{m.method_details.artifacts.join(", ")}</div></div>}
          {m.method_details.cadence && <div className="p-4 bg-emerald-50 rounded-xl"><div className="text-xs font-bold text-emerald-600">CADENCE</div><div className="text-sm mt-2">{m.method_details.cadence}</div></div>}
        </div>}
        
        {m.tool_recommendation && <div className="mt-5 p-5 bg-gradient-to-r from-slate-900 to-indigo-900 rounded-xl text-white">
          <div className="text-xs font-bold opacity-60">RECOMMENDED TOOL</div>
          <div className="text-2xl font-black mt-1">{m.tool_recommendation.primary}</div>
          <div className="text-xs mt-2 opacity-80">Alternatives: {(m.tool_recommendation.alternatives||[]).join(", ")}</div>
          <div className="text-xs mt-1 opacity-70 italic">{m.tool_recommendation.reason}</div>
        </div>}
        
        {m.why_not_others && <div className="mt-5"><div className="text-xs font-bold text-slate-500 mb-2">WHY NOT OTHER METHODS</div>
          <div className="space-y-2">{m.why_not_others.map((w,i)=><div key={i} className="text-xs p-2 bg-slate-50 rounded border-l-2 border-slate-300"><b>{w.method}:</b> {w.reason}</div>)}</div>
        </div>}
        
        {m.success_factors && <div className="mt-5 p-4 bg-amber-50 rounded-xl border border-amber-200">
          <div className="text-xs font-bold text-amber-700">🌟 CRITICAL SUCCESS FACTORS</div>
          <ul className="text-sm mt-2 space-y-1">{m.success_factors.map((s,i)=><li key={i}>✓ {s}</li>)}</ul>
        </div>}
      </div>);})()}
    
    {/* Project Plan */}
    {agents["Project Planner"]?.data && (()=>{const p=agents["Project Planner"].data;return(
      <div className="bg-white rounded-2xl shadow-xl p-8 break">
        <div className="text-xs font-bold text-emerald-600 tracking-wider">📊 PROJECT PLAN</div>
        {p.executive_summary && <p className="mt-3 text-lg text-slate-700 italic">{p.executive_summary}</p>}
        
        {p.timeline && <div className="mt-4 p-4 bg-emerald-50 rounded-xl flex justify-between items-center">
          <div><div className="text-xs text-slate-500">TIMELINE</div><div className="text-xl font-black">{p.timeline.total_duration}</div></div>
          <div className="text-sm text-slate-600">{p.timeline.start} → {p.timeline.end}</div>
        </div>}
        
        {p.budget_estimate && <div className="mt-3 p-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl">
          <div className="text-xs opacity-80">BUDGET ESTIMATE</div>
          <div className="text-3xl font-black">{p.budget_estimate.total}</div>
          {p.budget_estimate.breakdown && <div className="flex gap-3 mt-2 text-xs">{Object.entries(p.budget_estimate.breakdown).map(([k,v])=><div key={k}><b>{k}:</b> {v}</div>)}</div>}
        </div>}
        
        {p.phases && <div className="mt-5"><div className="text-xs font-bold text-slate-500 mb-2">PROJECT PHASES</div>
          <div className="space-y-2">{p.phases.map((ph,i)=><div key={i} className={`p-4 rounded-xl bg-gradient-to-r ${C[i%8]} text-white`}>
            <div className="flex justify-between"><b>{ph.name}</b><span className="text-xs bg-white/20 px-2 py-1 rounded">{ph.duration}</span></div>
            {ph.milestones && <div className="text-xs mt-1 opacity-90">Milestones: {ph.milestones.join(" · ")}</div>}
          </div>)}</div>
        </div>}
        
        {p.team_composition && <div className="mt-5"><div className="text-xs font-bold text-slate-500 mb-2">TEAM</div>
          <div className="flex gap-2 flex-wrap">{p.team_composition.map((t,i)=><div key={i} className="px-3 py-2 bg-slate-100 rounded-lg text-xs"><b>{t.count}×</b> {t.seniority} {t.role}</div>)}</div>
        </div>}
        
        {p.kpis && <div className="mt-5"><div className="text-xs font-bold text-slate-500 mb-2">KPIs</div>
          <div className="grid md:grid-cols-3 gap-2">{p.kpis.map((k,i)=><div key={i} className="p-3 bg-indigo-50 rounded-xl"><div className="text-xs text-slate-500">{k.metric}</div><div className="font-black text-indigo-700">{k.target}</div></div>)}</div>
        </div>}
      </div>);})()}
    
    {/* Risk & Governance */}
    {agents["Risk & Governance"]?.data && (()=>{const r=agents["Risk & Governance"].data;return(
      <div className="bg-white rounded-2xl shadow-xl p-8 break">
        <div className="text-xs font-bold text-rose-600 tracking-wider">🛡️ RISK & GOVERNANCE</div>
        {r.executive_summary && <p className="mt-3 text-slate-700 italic">{r.executive_summary}</p>}
        {r.risk_register && <div className="mt-4 space-y-2">{r.risk_register.slice(0,6).map((risk,i)=><div key={i} className="p-3 bg-rose-50 rounded-xl border-l-4 border-rose-500">
          <div className="flex justify-between"><b className="text-sm">{risk.id}: {risk.description}</b><span className="text-xs bg-rose-600 text-white px-2 py-1 rounded">P×I: {risk.score}</span></div>
          <div className="text-xs mt-1 text-slate-600">→ {risk.mitigation} <b>({risk.owner})</b></div>
        </div>)}</div>}
        {r.governance && <div className="mt-4 p-4 bg-slate-50 rounded-xl text-sm">
          <b>Governance:</b> {r.governance.steering_committee?.join(", ")} · {r.governance.meeting_cadence}
        </div>}
      </div>);})()}
    
    {/* Stakeholders */}
    {agents["Stakeholder Strategist"]?.data && (()=>{const s=agents["Stakeholder Strategist"].data;return(
      <div className="bg-white rounded-2xl shadow-xl p-8 break">
        <div className="text-xs font-bold text-purple-600 tracking-wider">🤝 STAKEHOLDER STRATEGY</div>
        {s.executive_summary && <p className="mt-3 text-slate-700 italic">{s.executive_summary}</p>}
        {s.stakeholder_map && <div className="mt-4 grid md:grid-cols-2 gap-2">{s.stakeholder_map.map((st,i)=><div key={i} className="p-3 bg-purple-50 rounded-xl">
          <div className="flex justify-between"><b className="text-sm">{st.name}</b><span className="text-xs bg-purple-600 text-white px-2 rounded">{st.strategy}</span></div>
          <div className="text-xs mt-1">Power: {st.power} · Interest: {st.interest} · {st.frequency}</div>
        </div>)}</div>}
      </div>);})()}
  </div>);
}

function PLMReport({data}) {
  if (!data?.phases) return null;
  return(<div id="plm-report" className="space-y-4">
    <div className="bg-gradient-to-br from-emerald-600 via-teal-700 to-cyan-700 text-white rounded-3xl p-10">
      <div className="text-xs uppercase tracking-[3px] opacity-60">PRODUCT LIFECYCLE EXECUTION REPORT</div>
      <h1 className="text-4xl font-black mt-2">{data.idea}</h1>
      <div className="mt-4 text-sm opacity-70">PMGuru PLM · {new Date().toLocaleDateString()} · 8 Specialist Agents</div>
    </div>
    {data.phases.map((ph,i)=>(<div key={ph.id} className={`p-6 rounded-2xl bg-gradient-to-br ${C[i%8]} text-white shadow-xl break`}>
      <div className="flex items-start gap-4">
        <div className="text-6xl font-black opacity-30">{ph.id}</div>
        <div className="flex-1">
          <h3 className="text-2xl font-black">{ph.agent_icon} {ph.name}</h3>
          <p className="text-xs opacity-90">{ph.agent_role} · {ph.duration}</p>
          {ph.data?.summary && <p className="mt-3 text-sm italic opacity-90 border-l-4 border-white/40 pl-3">{ph.data.summary}</p>}
          <div className="mt-3 text-xs bg-white/10 p-3 rounded-lg whitespace-pre-wrap max-h-80 overflow-y-auto">{JSON.stringify(ph.data, null, 2).slice(0,800)}</div>
        </div>
      </div>
    </div>))}
  </div>);
}

export default function Auto() {
  const [step, setStep] = useState("input"); // input | pm_running | pm_done | plm_running | plm_done
  const [idea, setIdea] = useState("");
  const [pmData, setPmData] = useState(null);
  const [plmData, setPlmData] = useState(null);
  const [proto, setProto] = useState(null);
  const [cur, setCur] = useState(0);

  const runPM = async () => {
    if (!idea) return;
    setStep("pm_running");
    try {
      const r = await fetch("/api/pipeline", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({idea, action:"pm_plan"})});
      setPmData(await r.json());
      setStep("pm_done");
    } catch(e) { setStep("input"); alert(e.message); }
  };

  const runPLM = async () => {
    setStep("plm_running"); setCur(0);
    const timer = setInterval(()=>setCur(c=>c<7?c+1:c), 6000);
    try {
      const r = await fetch("/api/pipeline", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({idea, action:"plm_execute", pm_plan: pmData})});
      const j = await r.json();
      clearInterval(timer); setPlmData(j); setCur(8);
      const pr = await fetch("/api/prototype", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({idea, phases: j.phases})});
      setProto((await pr.json()).html);
      setStep("plm_done");
    } catch(e) { clearInterval(timer); alert(e.message); }
  };

  const dlPDF = (reportId, title) => {
    const el = document.getElementById(reportId);
    if (!el) return;
    const w = window.open("","_blank");
    w.document.write(`<html><head><title>${title}</title><script src="https://cdn.tailwindcss.com"></script><style>@media print{.break{page-break-before:always}}body{font-family:system-ui}</style></head><body class="p-8">${el.innerHTML}</body></html>`);
    setTimeout(()=>w.print(), 1500);
  };

  const dlProto = () => {
    const b = new Blob([proto], {type:"text/html"});
    const u = URL.createObjectURL(b);
    const a = document.createElement("a");
    a.href = u; a.download = "prototype.html"; a.click();
  };

  return(<div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50 p-6"><div className="max-w-6xl mx-auto">
    <header className="mb-6 bg-white rounded-2xl shadow-xl p-6 border-t-4 border-indigo-600">
      <h1 className="text-4xl font-black bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">🤖 PMGuru Autopilot v9</h1>
      <p className="text-slate-600 mt-1">PM Strategy (BCG-grade) → Approve → PLM Execution → Production Prototype</p>
    </header>

    {/* Progress steps */}
    <div className="mb-6 bg-white rounded-2xl shadow p-4 flex items-center justify-between text-xs">
      {["💡 Idea","🧠 PM Plan","✅ Approve","⚡ PLM Execute","🎨 Prototype"].map((s,i)=>{const active = ["input","pm_running","pm_done","plm_running","plm_done"].indexOf(step) >= i;
        return(<div key={i} className={`flex-1 text-center ${active?"font-bold text-indigo-600":"text-slate-400"}`}>{s}</div>);
      })}
    </div>

    {step==="input" && <div className="bg-white rounded-2xl shadow-xl p-8">
      <h2 className="text-2xl font-black mb-4">💡 Enter Your Project Idea</h2>
      <textarea value={idea} onChange={e=>setIdea(e.target.value)} rows={5} placeholder="e.g. AI-powered grocery assistant for Indian kirana stores..." className="w-full p-4 border-2 border-indigo-200 rounded-xl"/>
      <button onClick={runPM} className="mt-4 w-full px-8 py-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-xl font-black text-lg shadow-xl hover:scale-[1.02] transition-all">🧠 Generate PM Strategic Plan</button>
    </div>}

    {step==="pm_running" && <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
      <div className="text-6xl mb-4 animate-pulse">🧠</div>
      <h2 className="text-2xl font-black">4 PM Experts Analyzing...</h2>
      <p className="text-slate-600 mt-2">Methodology Expert · Project Planner · Risk & Governance · Stakeholder Strategist</p>
    </div>}

    {step==="pm_done" && pmData && <div className="space-y-6 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-xl p-4 flex gap-3 flex-wrap no-print">
        <button onClick={()=>dlPDF("pm-report","PM Strategic Report")} className="px-5 py-2 bg-indigo-600 text-white rounded-lg font-bold">📄 Download PM Report (PDF)</button>
        <button onClick={runPLM} className="px-5 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg font-bold">✅ Approve PM Plan & Run PLM</button>
        <button onClick={()=>{setStep("input");setPmData(null);}} className="px-5 py-2 bg-slate-200 rounded-lg font-bold">↩️ Edit Idea</button>
      </div>
      <PMReport data={pmData}/>
    </div>}

    {step==="plm_running" && <div className="bg-white rounded-2xl shadow-xl p-6">
      <h2 className="text-2xl font-black mb-4">⚡ PLM Agents Executing...</h2>
      <div className="space-y-2">{["Discovery","Ideation","Definition","Design","Development","Testing","Launch","Iterate"].map((n,i)=>{const done=i<cur,active=i===cur;
        return(<div key={i} className={`p-3 rounded-xl ${done?`bg-gradient-to-r ${C[i%8]} text-white`:active?"bg-indigo-100 animate-pulse":"bg-slate-50"}`}>
          <div className="flex items-center gap-3"><div className="text-2xl">{done?"✅":active?"⚙️":i+1}</div><div className="font-bold">{n}</div></div>
        </div>);})}</div>
    </div>}

    {step==="plm_done" && plmData && <div className="space-y-6 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-xl p-4 flex gap-3 flex-wrap no-print">
        <button onClick={()=>dlPDF("pm-report","PM Strategic Report")} className="px-5 py-2 bg-indigo-600 text-white rounded-lg font-bold">📄 PM Report PDF</button>
        <button onClick={()=>dlPDF("plm-report","PLM Execution Report")} className="px-5 py-2 bg-emerald-600 text-white rounded-lg font-bold">📄 PLM Report PDF</button>
        {proto && <button onClick={dlProto} className="px-5 py-2 bg-pink-600 text-white rounded-lg font-bold">🎨 Download Prototype</button>}
        <button onClick={()=>{setStep("input");setIdea("");setPmData(null);setPlmData(null);setProto(null);}} className="px-5 py-2 bg-slate-200 rounded-lg font-bold">🔄 New Project</button>
      </div>
      <PMReport data={pmData}/>
      <PLMReport data={plmData}/>
      {proto && <div className="bg-white rounded-2xl shadow-xl p-4 no-print"><h2 className="text-xl font-black mb-3">🎨 Live Prototype</h2><iframe srcDoc={proto} className="w-full h-[700px] rounded-xl border-2"/></div>}
    </div>}
  </div></div>);
}
