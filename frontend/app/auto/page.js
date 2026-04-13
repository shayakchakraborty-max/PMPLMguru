"use client";
import { useState, useEffect } from "react";

// v11: The /auto page is now a compact launcher.
// User enters idea → backend generates full workspace → store in localStorage → open workspace.
// The old "view report" flow is still available as a fallback.

export default function AutoPage() {
  const [idea, setIdea] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [recentProjects, setRecentProjects] = useState([]);

  useEffect(() => {
    // Load recent projects from localStorage
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
            created: ws._created_at || "recently",
          };
        } catch { return null; }
      }).filter(Boolean);
      setRecentProjects(projects.slice(0, 6));
    } catch {}
  }, []);

  async function launchWorkspace() {
    if (!idea.trim()) return setError("Please enter a project idea first.");
    setError("");
    setLoading(true);
    try {
      const r = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: "workspace", idea }),
      });
      const data = await r.json();
      if (data.error) {
        setError(data.error);
        setLoading(false);
        return;
      }
      // Store workspace in localStorage
      const ws = data.workspace;
      ws._created_at = new Date().toISOString();
      ws._idea = idea;
      const key = `pmguru_project_${ws.project.id}`;
      localStorage.setItem(key, JSON.stringify(ws));
      // Also store a "current" pointer
      localStorage.setItem("pmguru_current_project", ws.project.id);
      // Redirect to workspace
      window.location.href = `/workspace?id=${ws.project.id}`;
    } catch (e) {
      setError("Network error: " + e.message);
      setLoading(false);
    }
  }

  function openProject(id) {
    localStorage.setItem("pmguru_current_project", id);
    window.location.href = `/workspace?id=${id}`;
  }

  function deleteProject(id, e) {
    e.stopPropagation();
    if (!confirm("Delete this project? This cannot be undone.")) return;
    localStorage.removeItem(`pmguru_project_${id}`);
    setRecentProjects(rp => rp.filter(p => p.id !== id));
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-5xl mx-auto p-6">
        <header className="mb-10 pt-8">
          <div className="inline-block px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold mb-3">
            PMGuru v11 · Autonomous PM Platform
          </div>
          <h1 className="text-5xl font-black tracking-tight">Turn any idea into a fully-planned project</h1>
          <p className="text-slate-600 mt-3 text-lg max-w-2xl">
            Enter your idea. Our AI trained on 500+ real-world projects will classify, plan, and generate a complete PM workspace — ready to manage like Linear or Jira.
          </p>
        </header>

        {/* Main input card */}
        <div className="bg-white rounded-2xl shadow-lg border p-8 mb-8">
          <label className="block text-sm font-bold text-slate-700 mb-3">What do you want to build?</label>
          <textarea
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            rows={4}
            placeholder="e.g. AI-powered grocery assistant for Indian kirana stores with voice ordering, inventory management, and GST filing..."
            className="w-full p-4 border-2 border-slate-200 rounded-xl text-base focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 outline-none transition"
            disabled={loading}
          />
          <div className="mt-4 flex gap-3 flex-wrap items-center">
            <button
              onClick={launchWorkspace}
              disabled={loading || !idea.trim()}
              className="px-8 py-4 bg-gradient-to-br from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl font-bold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading ? "Generating workspace..." : "🚀 Generate PM Workspace"}
            </button>
            <span className="text-xs text-slate-500">Pre-fills tasks, sprints, risks, team, stakeholders, KPIs</span>
          </div>
          {error && (
            <div className="mt-4 bg-rose-50 border border-rose-300 rounded-xl p-4">
              <div className="font-bold text-rose-900 text-sm mb-1">Error</div>
              <pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre>
            </div>
          )}
        </div>

        {/* Recent projects */}
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
                      <div className="text-xs text-slate-500 mt-1 flex gap-2">
                        <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 font-bold">{p.methodology}</span>
                        <span>{p.industry}</span>
                        <span>·</span>
                        <span>{p.tasks} tasks</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => deleteProject(p.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-600 transition text-sm px-2"
                      title="Delete project"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer info */}
        <div className="mt-12 text-center text-xs text-slate-400">
          Trained on 500+ real project examples · 97.8% methodology classification accuracy · Template-driven, zero LLM failures
        </div>
      </div>
    </div>
  );
}
