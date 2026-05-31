"use client";
import { useState, useEffect } from "react";

export default function PmLauncher() {
  const [idea, setIdea] = useState("");
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");
  const [recentProjects, setRecentProjects] = useState([]);

  useEffect(() => {
    try {
      const keys = Object.keys(localStorage).filter(k => k.startsWith("pmguru_project_"));
      const projects = keys.map(k => {
        try { const ws = JSON.parse(localStorage.getItem(k)); return { id: ws.project.id, name: ws.project.name, methodology: ws.project.methodology, industry: ws.project.industry, tasks: ws.tasks?.length || 0 }; } catch { return null; }
      }).filter(Boolean);
      setRecentProjects(projects.slice(0, 6));
    } catch {}
  }, []);

  function goToReport() {
    if (!idea.trim()) { setError("Please enter a project idea first."); return; }
    sessionStorage.setItem("pmguru_pending_idea", idea);
    window.location.href = `/report?idea=${encodeURIComponent(idea)}`;
  }

  function goToBlueprint() {
    if (!idea.trim()) { setError("Please enter a project idea first."); return; }
    sessionStorage.setItem("pmguru_pending_idea", idea);
    window.location.href = `/blueprint?idea=${encodeURIComponent(idea)}`;
  }

  function goToErp() {
    if (!idea.trim()) { setError("Please enter a project idea first."); return; }
    sessionStorage.setItem("pmguru_pending_idea", idea);
    window.location.href = `/erp?idea=${encodeURIComponent(idea)}`;
  }

  async function goToWorkspace() {
    if (!idea.trim()) { setError("Please enter a project idea first."); return; }
    setError(""); setLoading("workspace");
    try {
      const r = await fetch("/api/pipeline", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ stage: "workspace", idea }) });
      const data = await r.json();
      if (data.error) { setError(data.error); setLoading(null); return; }
      const ws = data.workspace; ws._created_at = new Date().toISOString(); ws._idea = idea;
      localStorage.setItem(`pmguru_project_${ws.project.id}`, JSON.stringify(ws));
      localStorage.setItem("pmguru_current_project", ws.project.id);
      window.location.href = `/workspace?id=${ws.project.id}`;
    } catch (e) { setError("Network error: " + e.message); setLoading(null); }
  }

  function goToPlmCycle() {
    if (!idea.trim()) { setError("Please enter a project idea first."); return; }
    sessionStorage.setItem("pmguru_pending_idea", idea);
    window.location.href = `/plm-cycle?idea=${encodeURIComponent(idea)}`;
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-5xl mx-auto p-6">
        <header className="mb-8 pt-4">
          <a href="/auto" className="text-xs text-slate-500 hover:text-indigo-600">← Back to home</a>
          <div className="inline-block px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold mt-3 mb-3">Product & PM Tool</div>
          <h1 className="text-4xl font-black tracking-tight">From idea to execution, in three stages</h1>
          <p className="text-slate-600 mt-2 max-w-2xl">Enter your idea once. Get a Big 3-style report, a working PM workspace, and a complete product lifecycle plan.</p>
        </header>

        <div className="bg-white rounded-2xl shadow-lg border p-8 mb-6">
          <label className="block text-sm font-bold text-slate-700 mb-3">What do you want to build?</label>
          <textarea value={idea} onChange={(e) => setIdea(e.target.value)} rows={4}
            placeholder="e.g. AI-powered grocery assistant for Indian kirana stores with voice ordering, inventory management, and GST filing..."
            className="w-full p-4 border-2 border-slate-200 rounded-xl text-base focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 outline-none transition"
            disabled={loading !== null} />
          {error && <div className="mt-3 bg-rose-50 border border-rose-300 rounded-lg p-3"><pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre></div>}
        </div>

        <button onClick={goToBlueprint} disabled={!idea.trim()}
          className="w-full mb-4 text-left rounded-2xl overflow-hidden bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 hover:shadow-xl transition disabled:opacity-50">
          <div className="flex items-center gap-4">
            <span className="text-4xl">🧭</span>
            <div className="flex-1">
              <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-300">One-click · India-aware</div>
              <div className="text-xl font-black">Startup Blueprint</div>
              <div className="text-sm text-white/70">Everything in one document — market, model, GTM, ₹ financials, compliance & registration, funding & govt incentives, 90-day plan, and how to scale.</div>
            </div>
            <span className="shrink-0 px-4 py-2.5 bg-white text-slate-900 rounded-lg font-black text-sm">Generate →</span>
          </div>
        </button>

        <button onClick={goToErp} disabled={!idea.trim()}
          className="w-full mb-6 text-left rounded-2xl overflow-hidden bg-white border-2 border-slate-200 hover:border-violet-400 p-5 transition disabled:opacity-50 flex items-center gap-4">
          <span className="text-3xl">🗂️</span>
          <div className="flex-1">
            <div className="text-[11px] font-bold uppercase tracking-wider text-violet-600">ERP-styled · self-explanatory · exports to Notion</div>
            <div className="text-lg font-black">ERP Workspace Copilot</div>
            <div className="text-sm text-slate-600">Master data, backlog, sprints, risk register, compliance calendar, KPIs & SOPs — auto-filled per project, editable, and one-click export to Notion.</div>
          </div>
          <span className="shrink-0 px-4 py-2.5 bg-slate-900 text-white rounded-lg font-black text-sm">Open →</span>
        </button>

        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <StageCard num="1" icon="📑" title="Due Diligence Report" desc="11-section Big 3 consulting report. Market sizing, competition, tech stack, financials, GTM. Download as PDF." cta="Generate Report" color="from-purple-600 to-indigo-700" onClick={goToReport} loading={loading === "report"} disabled={loading !== null || !idea.trim()} />
          <StageCard num="2" icon="🛠️" title="PM Workspace" desc="Linear/Jira-blended tool. Tasks, sprints, kanban, risks, team, stakeholders, timeline, dashboard." cta="Build Workspace" color="from-emerald-600 to-teal-700" onClick={goToWorkspace} loading={loading === "workspace"} disabled={loading !== null || !idea.trim()} />
          <StageCard num="3" icon="🔄" title="PLM Cycle" desc="8-phase product lifecycle with infographic reports. Discovery through Iterate." cta="Run PLM Cycle" color="from-rose-600 to-orange-600" onClick={goToPlmCycle} loading={loading === "plm"} disabled={loading !== null || !idea.trim()} />
        </div>

        {recentProjects.length > 0 && (
          <div>
            <h2 className="text-sm font-bold text-slate-600 uppercase tracking-wider mb-3">Recent projects</h2>
            <div className="grid md:grid-cols-2 gap-3">
              {recentProjects.map(p => (
                <div key={p.id} onClick={() => { localStorage.setItem("pmguru_current_project", p.id); window.location.href = `/workspace?id=${p.id}`; }}
                  className="bg-white rounded-xl border p-4 hover:shadow-md hover:border-indigo-300 cursor-pointer transition group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-slate-900 truncate">{p.name}</div>
                      <div className="text-xs text-slate-500 mt-1 flex gap-2 flex-wrap">
                        <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 font-bold">{p.methodology}</span>
                        <span>{p.industry} · {p.tasks} tasks</span>
                      </div>
                    </div>
                    <button onClick={(e) => { e.stopPropagation(); if(confirm("Delete?")) { localStorage.removeItem(`pmguru_project_${p.id}`); setRecentProjects(rp => rp.filter(x => x.id !== p.id)); } }}
                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-600 transition text-sm px-2">✕</button>
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

function StageCard({ num, icon, title, desc, cta, color, onClick, loading, disabled }) {
  return (
    <div className="bg-white rounded-2xl border shadow-sm overflow-hidden flex flex-col">
      <div className={`bg-gradient-to-br ${color} text-white p-5`}>
        <div className="flex items-center justify-between"><span className="text-3xl">{icon}</span><span className="text-xs font-bold opacity-60 uppercase">Stage {num}</span></div>
        <h3 className="text-xl font-black mt-3">{title}</h3>
      </div>
      <div className="p-5 flex-1 flex flex-col">
        <p className="text-sm text-slate-600 flex-1">{desc}</p>
        <button onClick={onClick} disabled={disabled} className="mt-4 w-full px-4 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-bold text-sm disabled:opacity-40 disabled:cursor-not-allowed transition">
          {loading ? "Loading..." : cta}
        </button>
      </div>
    </div>
  );
}
