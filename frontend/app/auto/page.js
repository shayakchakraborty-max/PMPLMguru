"use client";
import {useState} from "react";

const PHASES_PREVIEW = [
  {id:1,name:"Discovery",agent:"Strategist",duration:"1-2 weeks"},
  {id:2,name:"Ideation",agent:"Strategist",duration:"1 week"},
  {id:3,name:"Definition",agent:"Business Analyst",duration:"2 weeks"},
  {id:4,name:"Design",agent:"UX Designer",duration:"2-3 weeks"},
  {id:5,name:"Development",agent:"Scrum Master",duration:"6-12 weeks"},
  {id:6,name:"Testing",agent:"QA Lead",duration:"2 weeks"},
  {id:7,name:"Launch",agent:"DevOps Engineer",duration:"1 week"},
  {id:8,name:"Iterate",agent:"Stakeholder Comms",duration:"Ongoing"},
];

const C=["from-indigo-500 to-purple-600","from-emerald-500 to-teal-600","from-amber-500 to-orange-600","from-rose-500 to-pink-600","from-sky-500 to-blue-600","from-violet-500 to-fuchsia-600","from-lime-500 to-green-600","from-cyan-500 to-blue-500"];

export default function Auto(){
  const [step,setStep] = useState("input"); // input | planning | approval | executing | done
  const [idea,setIdea] = useState("");
  const [plan,setPlan] = useState(null);
  const [result,setResult] = useState(null);
  const [proto,setProto] = useState(null);
  const [cur,setCur] = useState(0);
  const [showProto,setShowProto] = useState(false);

  const generatePlan = async () => {
    if(!idea) return;
    setStep("planning");
    try {
      const r = await fetch("/api/pipeline",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({idea,action:"plan"})});
      const j = await r.json();
      setPlan(j);
      setStep("approval");
    } catch(e) { setStep("input"); alert("Error: "+e.message); }
  };

  const approveAndExecute = async () => {
    setStep("executing");
    setCur(0);
    const timer = setInterval(()=>setCur(c=>c<7?c+1:c),5000);
    try {
      const r = await fetch("/api/pipeline",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({idea,action:"execute"})});
      const j = await r.json();
      clearInterval(timer);
      setResult(j);
      setCur(8);
      // Auto-generate prototype
      const pr = await fetch("/api/prototype",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({idea,phases:j.phases})});
      const pj = await pr.json();
      setProto(pj.html);
      setStep("done");
    } catch(e) { clearInterval(timer); alert("Error: "+e.message); }
  };

  const dlProto = () => {
    const b = new Blob([proto],{type:"text/html"});
    const u = URL.createObjectURL(b);
    const a = document.createElement("a");
    a.href = u; a.download = "prototype.html"; a.click();
  };

  return(<div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50 p-6"><div className="max-w-6xl mx-auto">
    <header className="mb-6 bg-white rounded-2xl shadow-xl p-6 border-t-4 border-indigo-600">
      <h1 className="text-4xl font-black bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">🤖 PMGuru Autopilot v7</h1>
      <p className="text-slate-600 mt-1">Idea → Plan → Approve → 8 AI Agents Build Everything Autonomously</p>
    </header>

    {/* STEP 1: INPUT */}
    {step==="input" && <div className="bg-white rounded-2xl shadow-xl p-8">
      <h2 className="text-2xl font-black mb-4">💡 Step 1: Enter Your Idea</h2>
      <textarea value={idea} onChange={e=>setIdea(e.target.value)} rows={5} placeholder="e.g. 'AI-powered grocery assistant for Indian kirana stores with voice ordering, GST billing, and inventory management'" className="w-full p-4 border-2 border-indigo-200 rounded-xl focus:border-indigo-500 outline-none"/>
      <button onClick={generatePlan} className="mt-4 w-full px-8 py-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-xl font-black text-lg shadow-xl hover:scale-[1.02] transition-all">🧠 Generate Project Plan</button>
    </div>}

    {/* STEP 2: PLANNING */}
    {step==="planning" && <div className="bg-white rounded-2xl shadow-xl p-12 text-center glow">
      <div className="text-6xl mb-4">🧠</div>
      <h2 className="text-2xl font-black">Strategist Agent is Thinking...</h2>
      <p className="text-slate-600 mt-2">Analyzing market, defining scope, building roadmap</p>
    </div>}

    {/* STEP 3: APPROVAL */}
    {step==="approval" && plan && <div className="space-y-6 animate-fadeIn">
      <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 text-white rounded-3xl shadow-2xl p-8">
        <div className="text-xs uppercase tracking-widest opacity-80">📋 Initial Plan for Approval</div>
        <h2 className="text-3xl font-black mt-2">{idea.slice(0,80)}</h2>
      </div>
      <div className="bg-white rounded-2xl shadow-xl p-6">
        <h3 className="text-xl font-black mb-3">🎯 Strategist's Plan</h3>
        <pre className="whitespace-pre-wrap text-sm bg-slate-50 p-5 rounded-xl">{plan.plan}</pre>
      </div>
      <div className="bg-white rounded-2xl shadow-xl p-6">
        <h3 className="text-xl font-black mb-3">⚡ Pipeline (8 Phases / 8 Agents)</h3>
        <div className="grid md:grid-cols-4 gap-2">
          {PHASES_PREVIEW.map((p,i)=><div key={p.id} className={`p-3 rounded-xl bg-gradient-to-br ${C[i%8]} text-white`}>
            <div className="text-2xl font-black">{p.id}</div>
            <div className="font-bold text-sm">{p.name}</div>
            <div className="text-xs opacity-90">🤖 {p.agent}</div>
          </div>)}
        </div>
      </div>
      <div className="flex gap-3">
        <button onClick={approveAndExecute} className="flex-1 px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl font-black text-lg shadow-xl hover:scale-[1.02] transition-all">✅ Approve & Execute All 8 Agents</button>
        <button onClick={()=>setStep("input")} className="px-6 py-4 bg-slate-200 rounded-xl font-bold">↩️ Edit</button>
      </div>
    </div>}

    {/* STEP 4: EXECUTING */}
    {step==="executing" && <div className="bg-white rounded-2xl shadow-xl p-6">
      <h2 className="text-2xl font-black mb-4">⚡ Agents Working Sequentially...</h2>
      <div className="space-y-2">
        {PHASES_PREVIEW.map((p,i)=>{const done=i<cur,active=i===cur;
          return(<div key={p.id} className={`flex items-center gap-3 p-3 rounded-xl transition-all ${done?`bg-gradient-to-r ${C[i%8]} text-white shadow-md`:active?"bg-indigo-100 animate-pulse glow":"bg-slate-50"}`}>
            <div className="text-2xl font-black w-10">{done?"✅":active?"⚙️":p.id}</div>
            <div className="flex-1"><div className="font-bold">{p.name}</div><div className="text-xs opacity-80">🤖 {p.agent}</div></div>
            {active && <span className="text-xs bg-indigo-600 text-white px-3 py-1 rounded-full">RUNNING</span>}
            {done && <span className="text-xs bg-white/20 px-3 py-1 rounded-full">DONE</span>}
          </div>);})}
      </div>
    </div>}

    {/* STEP 5: DONE */}
    {step==="done" && result && <div className="space-y-6 animate-fadeIn">
      <div className="bg-gradient-to-br from-emerald-500 via-teal-600 to-cyan-600 text-white rounded-3xl shadow-2xl p-10">
        <div className="text-xs uppercase tracking-widest opacity-80">✅ Autopilot Complete</div>
        <h1 className="text-4xl font-black mt-2">{idea.slice(0,80)}</h1>
        <div className="flex gap-6 mt-6 text-sm flex-wrap">
          <div><div className="opacity-70">PHASES</div><div className="text-xl font-bold">8/8 ✅</div></div>
          <div><div className="opacity-70">AGENTS</div><div className="text-xl font-bold">{result.agents_used?.length||8}</div></div>
          <div><div className="opacity-70">PROTOTYPE</div><div className="text-xl font-bold">Ready 🎨</div></div>
        </div>
        <div className="flex gap-3 mt-6 flex-wrap">
          {proto && <button onClick={dlProto} className="px-5 py-2 bg-white text-emerald-600 rounded-lg font-bold">🎨 Download Prototype</button>}
          {proto && <button onClick={()=>setShowProto(!showProto)} className="px-5 py-2 bg-white/20 text-white rounded-lg font-bold">{showProto?"Hide":"👁️ Preview"}</button>}
          <button onClick={()=>{setStep("input");setIdea("");setPlan(null);setResult(null);setProto(null);}} className="px-5 py-2 bg-white/20 text-white rounded-lg font-bold">🔄 New Project</button>
        </div>
      </div>

      {showProto && proto && <div className="bg-white rounded-2xl shadow-xl p-4">
        <h2 className="text-xl font-black mb-3">🎨 Live Prototype</h2>
        <iframe srcDoc={proto} className="w-full h-[600px] rounded-xl border-2 border-indigo-200"/>
      </div>}

      <div className="bg-white rounded-2xl shadow-xl p-6">
        <h2 className="text-xl font-black mb-4">📋 Agent Outputs</h2>
        <div className="space-y-3">
          {result.phases.map((ph,i)=>(<div key={ph.id} className={`p-5 rounded-2xl bg-gradient-to-r ${C[i%8]} text-white shadow-lg animate-fadeIn`} style={{animationDelay:`${i*150}ms`}}>
            <div className="flex items-start gap-4">
              <div className="text-5xl font-black opacity-40">{ph.id}</div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div><h3 className="text-xl font-black">{ph.name}</h3><p className="text-xs opacity-90">🤖 {ph.agent} • {ph.duration} • via {ph.provider}</p></div>
                  <span className="text-xs bg-white/20 px-3 py-1 rounded-full">{ph.status}</span>
                </div>
                <div className="mt-3 bg-white/10 p-3 rounded-lg text-xs whitespace-pre-wrap max-h-64 overflow-y-auto">{ph.output}</div>
              </div>
            </div>
          </div>))}
        </div>
      </div>
    </div>}
  </div></div>);
}
