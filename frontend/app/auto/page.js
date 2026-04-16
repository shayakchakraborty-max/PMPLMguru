"use client";
import { useState, useEffect } from "react";

// v12: /auto is the launcher. User enters idea, picks one of three actions:
//   1. Generate Consulting Report (Big 3 style, streaming)
//   2. Build PM Workspace (Linear/Jira-style tool)
//   3. Run PLM Cycle (8-phase product lifecycle with infographics)

export default function AutoPage() {
  const [idea, setIdea] = useState("");
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");
  const [recentProjects, setRecentProjects] = useState([]);

  useEffect(() => {
    try {
      const keys = Object.keys(localStorage).filter(k => k.startsWith("pmguru_project_"));
      const projects = keys.map(k => {
        try {
          const ws = JSON.parse(localStorage.getItem(k));
          return {
            id: ws.project.id,
            name: ws.project.name,
            methodology: ws.project.methodology,
            industry: ws.project.industry,
            tasks: ws.tasks?.length || 0,
          };
        } catch { return null; }
      }).filter(Boolean);
      setRecentProjects(projects.slice(0, 6));
    } catch {}
  }, []);

  function goToReport() {
    if (!idea.trim()) { setError("Please enter a project idea first."); return; }
    setError("");
    sessionStorage.setItem("pmguru_pending_idea", idea);
    window.location.href = `/report?idea=${encodeURIComponent(idea)}`;
  }

  async function goToWorkspace() {
    if (!idea.trim()) { setError("Please enter a project idea first."); return; }
    setError("");
    setLoading("workspace");
    try {
      const r = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: "workspace", idea }),
      });
      const data = await r.json();
      if (data.error) { setError(data.error); setLoading(null); return; }
      const ws = data.workspace;
      ws._created_at = new Date().toISOString();
      ws._idea = idea;
      localStorage.setItem(`pmguru_project_${ws.project.id}`, JSON.stringify(ws));
      localStorage.setItem("pmguru_current_project", ws.project.id);
      window.location.href = `/workspace?id=${ws.project.id}`;
    } catch (e) {
      setError("Network error: " + e.message);
      setLoading(null);
    }
  }

  function goToPlmCycle() {
    if (!idea.trim()) { setError("Please enter a project idea first."); return; }
    setError("");
    sessionStorage.setItem("pmguru_pending_idea", idea);
    window.location.href = `/plm-cycle?idea=${encodeURIComponent(idea)}`;
  }

  function openProject(id) {
    localStorage.setItem("pmguru_current_project", id);
    window.location.href = `/workspace?id=${id}`;
  }

  function deleteProject(id, e) {
    e.stopPropagation();
    if (!confirm("Delete this project?")) return;
    localStorage.removeItem(`pmguru_project_${id}`);
    setRecentProjects(rp => rp.filter(p => p.id !== id));
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-5xl mx-auto p-6">
        <header className="mb-8 pt-8">
          <div className="inline-block px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold mb-3">
            PMGuru v12 · Consulting-Grade PM Platform
          </div>
          <h1 className="text-5xl font-black tracking-tight">From idea to execution, in three stages</h1>
          <p className="text-slate-600 mt-3 text-lg max-w-2xl">
            Enter your idea once. Get a Big 3-style due diligence report, a working PM workspace, and a complete product lifecycle plan — all from the same input.
          </p>
        </header>

        <div className="bg-white rounded-2xl shadow-lg border p-8 mb-6">
          <label className="block text-sm font-bold text-slate-700 mb-3">What do you want to build?</label>
          <textarea
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            rows={4}
            placeholder="e.g. AI-powered grocery assistant for Indian kirana stores with voice ordering, inventory management, and GST filing..."
            className="w-full p-4 border-2 border-slate-200 rounded-xl text-base focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 outline-none transition"
            disabled={loading !== null}
          />
          {error && (
            <div className="mt-3 bg-rose-50 border border-rose-300 rounded-lg p-3">
              <pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre>
            </div>
          )}
        </div>

        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <StageCard
            num="1"
            icon="📑"
            title="Due Diligence Report"
            desc="Big 3 consulting-style report with 11 sections. Market sizing, competitive landscape, tech stack, financials, GTM. Streaming delivery (~16 sec). Download as PDF."
            cta="Generate Report"
            color="from-purple-600 to-indigo-700"
            onClick={goToReport}
            loading={loading === "report"}
            disabled={loading !== null || !idea.trim()}
          />
          <StageCard
            num="2"
            icon="🛠️"
            title="PM Workspace"
            desc="Linear/Jira/Asana-blended tool. Pre-filled tasks, sprints, kanban board, risk register, team roster, stakeholder map, timeline, dashboard. Edit everything inline."
            cta="Build Workspace"
            color="from-emerald-600 to-teal-700"
            onClick={goToWorkspace}
            loading={loading === "workspace"}
            disabled={loading !== null || !idea.trim()}
          />
          <StageCard
            num="3"
            icon="🔄"
            title="PLM Cycle"
            desc="8-phase product lifecycle with infographic-rich reports. Discovery, ideation, definition, design, development, testing, launch, iterate. Niche consulting style."
            cta="Run PLM Cycle"
            color="from-rose-600 to-orange-600"
            onClick={goToPlmCycle}
            loading={loading === "plm"}
            disabled={loading !== null || !idea.trim()}
          />
        </div>

        {recentProjects.length > 0 && (
          <div>
            <h2 className="text-sm font-bold text-slate-600 uppercase tracking-wider mb-3">Recent projects</h2>
            <div className="grid md:grid-cols-2 gap-3">
              {recentProjects.map(p => (
                <div
                  key={p.id}
                  onClick={() => openProject(p.id)}
                  className="bg-white rounded-xl border p-4 hover:shadow-md hover:border-indigo-300 cursor-pointer transition group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-slate-900 truncate">{p.name}</div>
                      <div className="text-xs text-slate-500 mt-1 flex gap-2 flex-wrap">
                        <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 font-bold">{p.methodology}</span>
                        <span>{p.industry}</span>
                        <span>·</span>
                        <span>{p.tasks} tasks</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => deleteProject(p.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-600 transition text-sm px-2"
                      title="Delete"
                    >✕</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-12 text-center text-xs text-slate-400">
          Trained on 500+ real project examples · 97.8% methodology classification accuracy · Template-driven, zero LLM failures
        </div>
      </div>
    </div>
  );
}

function StageCard({ num, icon, title, desc, cta, color, onClick, loading, disabled }) {
  return (
    <div className="bg-white rounded-2xl border shadow-sm overflow-hidden flex flex-col">
      <div className={`bg-gradient-to-br ${color} text-white p-5`}>
        <div className="flex items-center justify-between">
          <span className="text-3xl">{icon}</span>
          <span className="text-xs font-bold opacity-60 uppercase">Stage {num}</span>
        </div>
        <h3 className="text-xl font-black mt-3">{title}</h3>
      </div>
      <div className="p-5 flex-1 flex flex-col">
        <p className="text-sm text-slate-600 flex-1">{desc}</p>
        <button
          onClick={onClick}
          disabled={disabled}
          className="mt-4 w-full px-4 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-bold text-sm disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          {loading ? "Loading..." : cta}
        </button>
      </div>
    </div>
  );
}
