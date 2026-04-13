"use client";
import {useState} from "react";

const C = ["from-indigo-500 to-purple-600","from-emerald-500 to-teal-600","from-amber-500 to-orange-600","from-rose-500 to-pink-600","from-sky-500 to-blue-600","from-violet-500 to-fuchsia-600","from-lime-500 to-green-600","from-cyan-500 to-blue-500"];

function PMReport({data}) {
  if (!data?.pm_agents) return null;
  const agents = data.pm_agents;
  return (<div id="pm-report" className="space-y-4">
    <div className="bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-white rounded-3xl p-10">
      <div className="text-xs uppercase tracking-[3px] opacity-60">PM STRATEGIC REPORT</div>
      <h1 className="text-4xl font-black mt-2">{data.idea}</h1>
      <div className="mt-4 text-sm opacity-70">PMGuru Advisory · {new Date().toLocaleDateString()}</div>
    </div>
    {agents["Methodology Expert"]?.data && (()=>{const m=agents["Methodology Expert"].data;return(
      <div className="bg-white rounded-2xl shadow-xl p-8 border-l-8 border-indigo-600 break">
        <div className="text-xs font-bold text-indigo-600 tracking-wider">🎯 METHODOLOGY RECOMMENDATION</div>
        <div className="mt-3 flex items-baseline gap-4 flex-wrap">
          <h2 className="text-5xl font-black text-slate-900">{m.recommended_method}</h2>
          <span className="text-xs bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full font-bold">{m.confidence} Confidence</span>
        </div>
        <p className="text-slate-700 mt-3 italic border-l-4 border-slate-300 pl-4">{m.reasoning}</p>
        {m.tool_recommendation && <div className="mt-5 p-5 bg-gradient-to-r from-slate-900 to-indigo-900 rounded-xl text-white">
          <div className="text-xs font-bold opacity-60">RECOMMENDED PM TOOL</div>
          <div className="text-2xl font-black mt-1">{m.tool_recommendation.primary}</div>
          <div className="text-xs mt-2 opacity-80">{m.tool_recommendation.reason}</div>
        </div>}
      </div>);})()}
    {agents["Project Planner"]?.data && (()=>{const p=agents["Project Planner"].data;return(
      <div className="bg-white rounded-2xl shadow-xl p-8 break">
        <div className="text-xs font-bold text-emerald-600 tracking-wider">📊 PROJECT PLAN</div>
        {p.executive_summary && <p className="mt-3 text-lg text-slate-700 italic">{p.executive_summary}</p>}
        {p.budget_estimate && <div className="mt-3 p-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl">
          <div className="text-xs opacity-80">BUDGET</div>
          <div className="text-3xl font-black">{p.budget_estimate.total}</div>
        </div>}
        {p.phases && <div className="mt-5 space-y-2">{p.phases.map((ph,i)=><div key={i} className={`p-4 rounded-xl bg-gradient-to-r ${C[i%8]} text-white`}>
          <div className="flex justify-between"><b>{ph.name}</b><span className="text-xs bg-white/20 px-2 py-1 rounded">{ph.duration}</span></div>
        </div>)}</div>}
      </div>);})()}
  </div>);
}

function PLMReport({data}) {
  if (!data?.phases) return null;
  return(<div id="plm-report" className="space-y-4">
    <div className="bg-gradient-to-br from-emerald-600 via-teal-700 to-cyan-700 text-white rounded-3xl p-10">
      <div className="text-xs uppercase tracking-[3px] opacity-60">PLM EXECUTION REPORT</div>
      <h1 className="text-4xl font-black mt-2">{data.idea}</h1>
    </div>
    {data.phases.map((ph,i)=>(<div key={ph.id} className={`p-6 rounded-2xl bg-gradient-to-br ${C[i%8]} text-white shadow-xl break`}>
      <div className="flex items-start gap-4">
        <div className="text-6xl font-black opacity-30">{ph.id}</div>
        <div className="flex-1">
          <h3 className="text-2xl font-black">{ph.agent_icon} {ph.name}</h3>
          <p className="text-xs opacity-90">{ph.agent_role} · {ph.duration}</p>
          {ph.data?.summary && <p className="mt-3 text-sm italic opacity-90 border-l-4 border-white/40 pl-3">{ph.data.summary}</p>}
        </div>
      </div>
    </div>))}
  </div>);
}

export default function Auto() {
  const [step, setStep] = useState("input");
  const [idea, setIdea] = useState("");
  const [pmData, setPmData] = useState(null);
  const [pmTool, setPmTool] = useState(null);
  const [plmData, setPlmData] = useState(null);
  const [proto, setProto] = useState(null);
  const [cur, setCur] = useState(0);
  const [showTool, setShowTool] = useState(false);

  const runPM = async () => {
    if (!idea) return;
    setStep("pm_running");
    try {
      const r = await fetch("/api/pipeline", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({idea, action:"pm_plan"})});
      setPmData(await r.json());
      setStep("pm_done");
    } catch(e) { setStep("input"); alert(e.message); }
  };

  const buildPMTool = async () => {
    setStep("tool_running");
    try {
      const r = await fetch("/api/pmtool", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({idea, pm_plan: pmData})});
      const j = await r.json();
      setPmTool(j);
      setStep("tool_done");
    } catch(e) { alert(e.message); setStep("pm_done"); }
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

  const dlTool = () => {
    if (!pmTool?.html) return;
    const b = new Blob([pmTool.html], {type:"text/html"});
    const u = URL.createObjectURL(b);
    const a = document.createElement("a");
    a.href = u; a.download = "pm-tool.html"; a.click();
  };

  const dlProto = () => {
    const b = new Blob([proto], {type:"text/html"});
    const u = URL.createObjectURL(b);
    const a = document.createElement("a");
    a.href = u; a.download = "prototype.html"; a.click();
  };

  return(<div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50 p-6"><div className="max-w-6xl mx-auto">
    <header className="mb-6 bg-white rounded-2xl shadow-xl p-6 border-t-4 border-indigo-600">
      <h1 className="text-4xl font-black bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">🤖 PMGuru v10 · Autopilot</h1>
      <p className="text-slate-600 mt-1">PM Strategy → Custom PM Tool → PLM Execution → Prototype</p>
    </header>

    <div className="mb-6 bg-white rounded-2xl shadow p-4 flex items-center justify-between text-xs overflow-x-auto">
      {["💡 Idea","🧠 PM Plan","🛠️ PM Tool","⚡ PLM","🎨 Prototype"].map((s,i)=>{
        const steps = ["input","pm_running","pm_done","tool_running","tool_done","plm_running","plm_done"];
        const progress = steps.indexOf(step);
        const checkpoints = [0, 2, 4, 5, 6];
        const active = progress >= checkpoints[i];
        return(<div key={i} className={`flex-1 text-center px-2 ${active?"font-bold text-indigo-600":"text-slate-400"}`}>{s}</div>);
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
      <p className="text-slate-600 mt-2">Methodology · Planning · Risk · Stakeholders</p>
    </div>}

    {step==="pm_done" && pmData && <div className="space-y-6 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-xl p-4 flex gap-3 flex-wrap no-print">
        <button onClick={()=>dlPDF("pm-report","PM Report")} className="px-5 py-2 bg-indigo-600 text-white rounded-lg font-bold">📄 PM Report PDF</button>
        <button onClick={buildPMTool} className="px-5 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-bold shadow-lg">🛠️ Build Custom PM Tool</button>
        <button onClick={()=>{setStep("input");setPmData(null);}} className="px-5 py-2 bg-slate-200 rounded-lg font-bold">↩️ Edit</button>
      </div>
      <PMReport data={pmData}/>
    </div>}

    {step==="tool_running" && <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
      <div className="text-6xl mb-4 animate-pulse">🛠️</div>
      <h2 className="text-2xl font-black">PM Tool Architect Building...</h2>
      <p className="text-slate-600 mt-2">Designing columns, sprints, cards, and team for your project</p>
    </div>}

    {step==="tool_done" && pmTool && <div className="space-y-6 animate-fadeIn">
      <div className="bg-gradient-to-br from-purple-600 via-pink-600 to-rose-600 text-white rounded-3xl shadow-2xl p-10">
        <div className="text-xs uppercase tracking-widest opacity-80">🛠️ YOUR CUSTOM PM TOOL</div>
        <h1 className="text-3xl font-black mt-2">{pmTool.board_data?.board_title || "Custom PM Board"}</h1>
        <div className="text-sm mt-2 opacity-80">
          {pmTool.board_data?.methodology} · {pmTool.board_data?.cards?.length || 0} tasks · {pmTool.board_data?.team_members?.length || 0} team members
        </div>
        <div className="flex gap-3 mt-6 flex-wrap">
          <button onClick={dlTool} className="px-5 py-2 bg-white text-purple-600 rounded-lg font-bold shadow">💾 Download PM Tool (HTML)</button>
          <button onClick={()=>setShowTool(!showTool)} className="px-5 py-2 bg-white/20 text-white rounded-lg font-bold">{showTool?"Hide":"👁️ Preview"}</button>
          <button onClick={runPLM} className="px-5 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg font-bold">✅ Continue to PLM Execution</button>
        </div>
      </div>
      {showTool && <div className="bg-white rounded-2xl shadow-xl p-4">
        <iframe srcDoc={pmTool.html} className="w-full h-[750px] rounded-xl border-2 border-purple-200"/>
      </div>}
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
        <button onClick={()=>dlPDF("pm-report","PM Report")} className="px-5 py-2 bg-indigo-600 text-white rounded-lg font-bold">📄 PM Report PDF</button>
        <button onClick={()=>dlPDF("plm-report","PLM Report")} className="px-5 py-2 bg-emerald-600 text-white rounded-lg font-bold">📄 PLM Report PDF</button>
        {pmTool && <button onClick={dlTool} className="px-5 py-2 bg-purple-600 text-white rounded-lg font-bold">🛠️ PM Tool</button>}
        {proto && <button onClick={dlProto} className="px-5 py-2 bg-pink-600 text-white rounded-lg font-bold">🎨 Prototype</button>}
        <button onClick={()=>{setStep("input");setIdea("");setPmData(null);setPmTool(null);setPlmData(null);setProto(null);}} className="px-5 py-2 bg-slate-200 rounded-lg font-bold">🔄 New Project</button>
      </div>
      <PMReport data={pmData}/>
      <PLMReport data={plmData}/>
      {proto && <div className="bg-white rounded-2xl shadow-xl p-4 no-print"><h2 className="text-xl font-black mb-3">🎨 Live Prototype</h2><iframe srcDoc={proto} className="w-full h-[700px] rounded-xl border-2"/></div>}
    </div>}
  </div></div>);
}
