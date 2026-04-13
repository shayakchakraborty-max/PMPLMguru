"use client";
import { useState, useEffect } from "react";

// ============================================================
// PMGuru Workspace v11 - The real PM tool
// ============================================================
// Single-file component that renders Linear/Jira/Asana/Notion-blended UI.
// All data lives in localStorage. Every field is editable inline.
// Views: Overview · Board · Sprints · Risks · Team · Stakeholders · Timeline · Dashboard
// ============================================================

const VIEWS = [
  { id: "overview",     icon: "📋", label: "Overview" },
  { id: "board",        icon: "🗂️",  label: "Board" },
  { id: "sprints",      icon: "🏃", label: "Sprints" },
  { id: "risks",        icon: "🛡️",  label: "Risks" },
  { id: "team",         icon: "👥", label: "Team" },
  { id: "stakeholders", icon: "🤝", label: "Stakeholders" },
  { id: "timeline",     icon: "📅", label: "Timeline" },
  { id: "dashboard",    icon: "📊", label: "Dashboard" },
];

const STATUS_COLUMNS = [
  { id: "todo",        label: "To Do",        color: "bg-slate-100 text-slate-700 border-slate-300" },
  { id: "in_progress", label: "In Progress",  color: "bg-blue-100 text-blue-700 border-blue-300" },
  { id: "in_review",   label: "In Review",    color: "bg-amber-100 text-amber-700 border-amber-300" },
  { id: "done",        label: "Done",         color: "bg-emerald-100 text-emerald-700 border-emerald-300" },
];

const PRIORITY_COLORS = {
  high: "bg-rose-100 text-rose-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-slate-100 text-slate-600",
};

export default function WorkspacePage() {
  const [workspace, setWorkspace] = useState(null);
  const [view, setView] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [projectId, setProjectId] = useState(null);

  useEffect(() => {
    // Read project ID from URL ?id=xxx or localStorage
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id") || localStorage.getItem("pmguru_current_project");
    if (!id) {
      setLoading(false);
      return;
    }
    setProjectId(id);
    try {
      const raw = localStorage.getItem(`pmguru_project_${id}`);
      if (raw) {
        setWorkspace(JSON.parse(raw));
      }
    } catch (e) {
      console.error("Failed to load workspace:", e);
    }
    setLoading(false);
  }, []);

  // Auto-save to localStorage whenever workspace changes
  useEffect(() => {
    if (workspace && projectId) {
      try {
        localStorage.setItem(`pmguru_project_${projectId}`, JSON.stringify(workspace));
      } catch (e) {
        console.error("Auto-save failed:", e);
      }
    }
  }, [workspace, projectId]);

  // Generic update helpers
  function updateWorkspace(updater) {
    setWorkspace(ws => ({ ...updater(ws) }));
  }
  function updateProject(changes) {
    updateWorkspace(ws => ({ ...ws, project: { ...ws.project, ...changes } }));
  }
  function updateTask(taskId, changes) {
    updateWorkspace(ws => ({
      ...ws,
      tasks: ws.tasks.map(t => t.id === taskId ? { ...t, ...changes } : t),
    }));
  }
  function deleteTask(taskId) {
    if (!confirm("Delete this task?")) return;
    updateWorkspace(ws => ({ ...ws, tasks: ws.tasks.filter(t => t.id !== taskId) }));
  }
  function addTask(sprintId) {
    const newTask = {
      id: `task_${Date.now()}`,
      ref: `PMG-${(workspace.tasks.length || 0) + 1}`,
      title: "New task",
      description: "",
      status: "todo",
      priority: "medium",
      sprint_id: sprintId,
      sprint_name: workspace.sprints.find(s => s.id === sprintId)?.name || "",
      assignee: null,
      story_points: 3,
      labels: [],
    };
    updateWorkspace(ws => ({ ...ws, tasks: [...ws.tasks, newTask] }));
  }
  function updateRisk(riskId, changes) {
    updateWorkspace(ws => ({
      ...ws,
      risks: ws.risks.map(r => {
        if (r.id !== riskId) return r;
        const updated = { ...r, ...changes };
        if ("probability" in changes || "impact" in changes) {
          updated.score = (updated.probability || 0) * (updated.impact || 0);
        }
        return updated;
      }),
    }));
  }
  function addRisk() {
    const newRisk = {
      id: `R-${Date.now()}`,
      type: "Risk",
      description: "New risk",
      probability: 3,
      impact: 3,
      score: 9,
      mitigation: "",
      owner: "TBD",
      status: "open",
    };
    updateWorkspace(ws => ({ ...ws, risks: [...ws.risks, newRisk] }));
  }
  function updateTeamMember(memberId, changes) {
    updateWorkspace(ws => ({
      ...ws,
      team: ws.team.map(m => m.id === memberId ? { ...m, ...changes } : m),
    }));
  }
  function updateStakeholder(stakeId, changes) {
    updateWorkspace(ws => ({
      ...ws,
      stakeholders: ws.stakeholders.map(s => s.id === stakeId ? { ...s, ...changes } : s),
    }));
  }
  function updateKpi(kpiId, changes) {
    updateWorkspace(ws => ({
      ...ws,
      kpis: ws.kpis.map(k => k.id === kpiId ? { ...k, ...changes } : k),
    }));
  }
  function updateSprint(sprintId, changes) {
    updateWorkspace(ws => ({
      ...ws,
      sprints: ws.sprints.map(s => s.id === sprintId ? { ...s, ...changes } : s),
    }));
  }

  function exportJSON() {
    const blob = new Blob([JSON.stringify(workspace, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${workspace.project.name.replace(/\W+/g, "_")}_workspace.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600">Loading workspace...</div>;
  }
  if (!workspace) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">🤷</div>
          <h1 className="text-2xl font-black text-slate-900">No workspace found</h1>
          <p className="text-slate-600 mt-2">Start by generating a new project.</p>
          <a href="/auto" className="inline-block mt-6 px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold">Create new project</a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex">
      {/* Sidebar */}
      <aside className="w-60 bg-slate-900 text-white min-h-screen p-4 flex flex-col">
        <div className="mb-6">
          <div className="text-xs opacity-60 uppercase tracking-wider">PMGuru Workspace</div>
          <div className="font-black text-lg mt-1 truncate" title={workspace.project.name}>{workspace.project.name}</div>
          <div className="mt-2 flex gap-1 flex-wrap">
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/30 text-indigo-200 font-bold">{workspace.project.methodology}</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-slate-300">{workspace.project.industry}</span>
          </div>
        </div>
        <nav className="space-y-1 flex-1">
          {VIEWS.map(v => (
            <button
              key={v.id}
              onClick={() => setView(v.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition ${
                view === v.id ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-white/10"
              }`}
            >
              <span>{v.icon}</span>
              <span>{v.label}</span>
            </button>
          ))}
        </nav>
        <div className="pt-4 border-t border-white/10 space-y-1">
          <button onClick={exportJSON} className="w-full text-left px-3 py-2 rounded-lg text-xs text-slate-400 hover:bg-white/10">📥 Export JSON</button>
          <a href="/auto" className="block px-3 py-2 rounded-lg text-xs text-slate-400 hover:bg-white/10">← New project</a>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto p-6">
          {view === "overview"     && <OverviewView ws={workspace} updateProject={updateProject} updateKpi={updateKpi} />}
          {view === "board"        && <BoardView ws={workspace} updateTask={updateTask} deleteTask={deleteTask} addTask={addTask} />}
          {view === "sprints"      && <SprintsView ws={workspace} updateSprint={updateSprint} />}
          {view === "risks"        && <RisksView ws={workspace} updateRisk={updateRisk} addRisk={addRisk} />}
          {view === "team"         && <TeamView ws={workspace} updateTeamMember={updateTeamMember} />}
          {view === "stakeholders" && <StakeholdersView ws={workspace} updateStakeholder={updateStakeholder} />}
          {view === "timeline"     && <TimelineView ws={workspace} />}
          {view === "dashboard"    && <DashboardView ws={workspace} />}
        </div>
      </main>
    </div>
  );
}

// ============================================================
// OVERVIEW VIEW - editable project details
// ============================================================
function OverviewView({ ws, updateProject, updateKpi }) {
  const p = ws.project;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black">Overview</h1>
        <p className="text-slate-600 mt-1 text-sm">Editable project details. Everything here was pre-filled from the AI analysis.</p>
      </div>

      {/* Editable project card */}
      <div className="bg-white rounded-2xl border shadow-sm p-6">
        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Project Name</label>
        <input
          type="text"
          value={p.name}
          onChange={e => updateProject({ name: e.target.value })}
          className="w-full text-2xl font-black mt-1 outline-none focus:bg-slate-50 rounded p-1"
        />

        <div className="mt-4">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Description</label>
          <textarea
            value={p.description}
            onChange={e => updateProject({ description: e.target.value })}
            rows={3}
            className="w-full text-sm mt-1 p-2 border border-slate-200 rounded-lg outline-none focus:border-indigo-500"
          />
        </div>

        <div className="grid md:grid-cols-4 gap-3 mt-4">
          <StatCard label="Methodology" value={p.methodology} color="indigo" />
          <StatCard label="Industry" value={p.industry} color="purple" />
          <StatCard label="Timeline" value={`${p.total_weeks} weeks`} color="emerald" />
          <StatCard label="Budget" value={`$${(p.budget || 0).toLocaleString()}`} color="amber" />
        </div>

        <div className="grid md:grid-cols-3 gap-3 mt-4">
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase">Status</label>
            <select value={p.status} onChange={e => updateProject({ status: e.target.value })} className="w-full mt-1 p-2 border rounded-lg text-sm">
              <option value="planning">Planning</option>
              <option value="active">Active</option>
              <option value="on_hold">On Hold</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase">Complexity</label>
            <select value={p.complexity} onChange={e => updateProject({ complexity: e.target.value })} className="w-full mt-1 p-2 border rounded-lg text-sm">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="very_high">Very High</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase">Recommended Tool</label>
            <input
              type="text"
              value={p.tool_recommendation || ""}
              onChange={e => updateProject({ tool_recommendation: e.target.value })}
              className="w-full mt-1 p-2 border rounded-lg text-sm"
            />
          </div>
        </div>
      </div>

      {/* Methodology details */}
      {ws.methodology_details && (
        <div className="bg-white rounded-2xl border shadow-sm p-6">
          <h2 className="text-lg font-black mb-4">Methodology: {p.methodology}</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <DetailBox title="Roles" items={ws.methodology_details.roles} color="indigo" />
            <DetailBox title="Ceremonies" items={ws.methodology_details.ceremonies} color="purple" />
            <DetailBox title="Artifacts" items={ws.methodology_details.artifacts} color="emerald" />
            <DetailBox title="Cadence" items={[ws.methodology_details.cadence]} color="amber" />
          </div>
          {ws.success_factors && (
            <div className="mt-4">
              <div className="text-xs font-bold text-slate-500 uppercase mb-2">Success Factors</div>
              <ul className="space-y-1">
                {ws.success_factors.map((f, i) => (
                  <li key={i} className="text-sm text-slate-700">✓ {f}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* KPIs */}
      <div className="bg-white rounded-2xl border shadow-sm p-6">
        <h2 className="text-lg font-black mb-4">Success KPIs</h2>
        <div className="space-y-2">
          {ws.kpis?.map(k => (
            <div key={k.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
              <input
                type="text"
                value={k.metric}
                onChange={e => updateKpi(k.id, { metric: e.target.value })}
                className="flex-1 bg-transparent font-bold text-slate-900 outline-none focus:bg-white px-2 py-1 rounded"
              />
              <span className="text-xs text-slate-400">Target:</span>
              <input
                type="text"
                value={k.target}
                onChange={e => updateKpi(k.id, { target: e.target.value })}
                className="w-40 bg-transparent text-emerald-700 font-medium outline-none focus:bg-white px-2 py-1 rounded"
              />
              <span className="text-xs text-slate-400">Current:</span>
              <input
                type="text"
                value={k.current}
                onChange={e => updateKpi(k.id, { current: e.target.value })}
                className="w-24 bg-transparent text-slate-700 outline-none focus:bg-white px-2 py-1 rounded"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className={`bg-${color}-50 rounded-xl p-3 border border-${color}-100`}>
      <div className={`text-[10px] font-bold text-${color}-700 uppercase tracking-wider`}>{label}</div>
      <div className="text-lg font-black text-slate-900 mt-1">{value}</div>
    </div>
  );
}

function DetailBox({ title, items, color }) {
  return (
    <div className={`p-4 bg-${color}-50 rounded-xl border border-${color}-100`}>
      <div className={`text-xs font-bold text-${color}-700 uppercase mb-2`}>{title}</div>
      <ul className="text-sm text-slate-700 space-y-1">
        {items?.filter(Boolean).map((item, i) => <li key={i}>• {item}</li>)}
      </ul>
    </div>
  );
}

// ============================================================
// BOARD VIEW - Kanban with drag-free click-to-move
// ============================================================
function BoardView({ ws, updateTask, deleteTask, addTask }) {
  const [filterSprint, setFilterSprint] = useState("all");
  const filteredTasks = filterSprint === "all"
    ? ws.tasks
    : ws.tasks.filter(t => t.sprint_id === filterSprint);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black">Board</h1>
          <p className="text-slate-600 mt-1 text-sm">Click a task's status pill to move it across columns. {filteredTasks.length} of {ws.tasks.length} tasks shown.</p>
        </div>
        <div className="flex gap-2 items-center">
          <select value={filterSprint} onChange={e => setFilterSprint(e.target.value)} className="px-3 py-2 border rounded-lg text-sm">
            <option value="all">All sprints</option>
            {ws.sprints?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          {filterSprint !== "all" && (
            <button onClick={() => addTask(filterSprint)} className="px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold">+ Task</button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {STATUS_COLUMNS.map(col => {
          const colTasks = filteredTasks.filter(t => t.status === col.id);
          return (
            <div key={col.id} className="bg-white rounded-xl border shadow-sm min-h-[300px]">
              <div className={`px-3 py-2 rounded-t-xl border-b font-bold text-xs uppercase tracking-wider ${col.color}`}>
                {col.label} · {colTasks.length}
              </div>
              <div className="p-2 space-y-2">
                {colTasks.map(task => <TaskCard key={task.id} task={task} columns={STATUS_COLUMNS} updateTask={updateTask} deleteTask={deleteTask} />)}
                {colTasks.length === 0 && (
                  <div className="text-xs text-slate-400 text-center py-8">Drop tasks here</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TaskCard({ task, columns, updateTask, deleteTask }) {
  const [editing, setEditing] = useState(false);
  const nextStatus = () => {
    const idx = columns.findIndex(c => c.id === task.status);
    const next = columns[(idx + 1) % columns.length];
    updateTask(task.id, { status: next.id });
  };
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-3 hover:shadow-md hover:border-indigo-300 transition">
      <div className="flex items-start justify-between mb-2">
        <span className="text-[10px] text-slate-400 font-mono">{task.ref}</span>
        <button onClick={() => deleteTask(task.id)} className="text-xs text-slate-300 hover:text-rose-600">✕</button>
      </div>
      {editing ? (
        <input
          type="text"
          value={task.title}
          onChange={e => updateTask(task.id, { title: e.target.value })}
          onBlur={() => setEditing(false)}
          autoFocus
          className="w-full text-sm font-bold outline-none border-b border-indigo-500"
        />
      ) : (
        <div onClick={() => setEditing(true)} className="text-sm font-bold text-slate-900 cursor-text hover:bg-slate-50 rounded px-1 -mx-1">
          {task.title}
        </div>
      )}
      <div className="mt-2 flex items-center gap-1 flex-wrap text-[10px]">
        <button onClick={nextStatus} className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 font-bold hover:bg-indigo-200">
          → Next status
        </button>
        <select value={task.priority} onChange={e => updateTask(task.id, { priority: e.target.value })} className={`px-2 py-0.5 rounded font-bold ${PRIORITY_COLORS[task.priority]}`}>
          <option value="high">High</option>
          <option value="medium">Med</option>
          <option value="low">Low</option>
        </select>
        <span className="text-slate-400">{task.story_points}pt</span>
      </div>
      <div className="mt-1 text-[10px] text-slate-400">{task.sprint_name}</div>
    </div>
  );
}

// ============================================================
// SPRINTS VIEW
// ============================================================
function SprintsView({ ws, updateSprint }) {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-black">Sprints</h1>
      <p className="text-slate-600 text-sm">Manage your delivery cadence. Each sprint was pre-populated from the AI methodology plan.</p>
      <div className="space-y-3">
        {ws.sprints?.map(sprint => {
          const sprintTasks = ws.tasks.filter(t => t.sprint_id === sprint.id);
          const doneTasks = sprintTasks.filter(t => t.status === "done").length;
          const totalPoints = sprintTasks.reduce((s, t) => s + (t.story_points || 0), 0);
          const donePoints = sprintTasks.filter(t => t.status === "done").reduce((s, t) => s + (t.story_points || 0), 0);
          const pct = sprintTasks.length ? Math.round(100 * doneTasks / sprintTasks.length) : 0;
          return (
            <div key={sprint.id} className="bg-white rounded-2xl border shadow-sm p-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-500">SPRINT {sprint.number}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">Weeks {sprint.start_week}–{sprint.end_week}</span>
                  </div>
                  <input
                    type="text"
                    value={sprint.name}
                    onChange={e => updateSprint(sprint.id, { name: e.target.value })}
                    className="text-xl font-black text-slate-900 outline-none focus:bg-slate-50 rounded px-1 -mx-1 mt-1 w-full"
                  />
                  <input
                    type="text"
                    value={sprint.goal}
                    onChange={e => updateSprint(sprint.id, { goal: e.target.value })}
                    placeholder="Sprint goal"
                    className="text-sm text-slate-600 outline-none focus:bg-slate-50 rounded px-1 -mx-1 mt-1 w-full italic"
                  />
                </div>
                <select
                  value={sprint.status}
                  onChange={e => updateSprint(sprint.id, { status: e.target.value })}
                  className="px-3 py-1 border rounded-lg text-xs font-bold"
                >
                  <option value="planned">Planned</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
              <div className="grid grid-cols-4 gap-3 mt-4 text-center">
                <div className="p-2 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500">Tasks</div>
                  <div className="text-lg font-black">{sprintTasks.length}</div>
                </div>
                <div className="p-2 bg-emerald-50 rounded-lg">
                  <div className="text-xs text-emerald-700">Done</div>
                  <div className="text-lg font-black text-emerald-900">{doneTasks}</div>
                </div>
                <div className="p-2 bg-indigo-50 rounded-lg">
                  <div className="text-xs text-indigo-700">Points</div>
                  <div className="text-lg font-black text-indigo-900">{donePoints}/{totalPoints}</div>
                </div>
                <div className="p-2 bg-purple-50 rounded-lg">
                  <div className="text-xs text-purple-700">Progress</div>
                  <div className="text-lg font-black text-purple-900">{pct}%</div>
                </div>
              </div>
              <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// RISKS VIEW - editable table with P x I heatmap
// ============================================================
function RisksView({ ws, updateRisk, addRisk }) {
  const sorted = [...(ws.risks || [])].sort((a, b) => (b.score || 0) - (a.score || 0));
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black">Risks</h1>
          <p className="text-slate-600 text-sm mt-1">RAID log sorted by probability × impact score.</p>
        </div>
        <button onClick={addRisk} className="px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold">+ Risk</button>
      </div>
      <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-600">
              <th className="p-3 font-bold">ID</th>
              <th className="p-3 font-bold">Description</th>
              <th className="p-3 font-bold text-center">P</th>
              <th className="p-3 font-bold text-center">I</th>
              <th className="p-3 font-bold text-center">Score</th>
              <th className="p-3 font-bold">Mitigation</th>
              <th className="p-3 font-bold">Owner</th>
              <th className="p-3 font-bold">Status</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(r => {
              const scoreColor = r.score >= 15 ? "bg-rose-100 text-rose-800" : r.score >= 9 ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800";
              return (
                <tr key={r.id} className="border-t hover:bg-slate-50">
                  <td className="p-3 font-mono text-xs text-slate-500">{r.id}</td>
                  <td className="p-3">
                    <input type="text" value={r.description} onChange={e => updateRisk(r.id, { description: e.target.value })} className="w-full bg-transparent outline-none focus:bg-white px-1 rounded" />
                  </td>
                  <td className="p-3 text-center">
                    <input type="number" min="1" max="5" value={r.probability} onChange={e => updateRisk(r.id, { probability: Number(e.target.value) })} className="w-12 bg-transparent text-center outline-none focus:bg-white rounded" />
                  </td>
                  <td className="p-3 text-center">
                    <input type="number" min="1" max="5" value={r.impact} onChange={e => updateRisk(r.id, { impact: Number(e.target.value) })} className="w-12 bg-transparent text-center outline-none focus:bg-white rounded" />
                  </td>
                  <td className="p-3 text-center">
                    <span className={`px-2 py-1 rounded font-bold ${scoreColor}`}>{r.score}</span>
                  </td>
                  <td className="p-3 text-xs text-slate-600">
                    <input type="text" value={r.mitigation} onChange={e => updateRisk(r.id, { mitigation: e.target.value })} className="w-full bg-transparent outline-none focus:bg-white px-1 rounded" />
                  </td>
                  <td className="p-3 text-xs">
                    <input type="text" value={r.owner} onChange={e => updateRisk(r.id, { owner: e.target.value })} className="w-full bg-transparent outline-none focus:bg-white px-1 rounded" />
                  </td>
                  <td className="p-3">
                    <select value={r.status} onChange={e => updateRisk(r.id, { status: e.target.value })} className="text-xs bg-transparent outline-none">
                      <option value="open">Open</option>
                      <option value="mitigating">Mitigating</option>
                      <option value="closed">Closed</option>
                    </select>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================
// TEAM VIEW - roster with editable contact
// ============================================================
function TeamView({ ws, updateTeamMember }) {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-black">Team</h1>
      <p className="text-slate-600 text-sm">Pre-filled roles from the methodology plan. Add real names and emails to activate.</p>
      <div className="grid md:grid-cols-2 gap-3">
        {ws.team?.map(m => (
          <div key={m.id} className="bg-white rounded-xl border shadow-sm p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="text-xs font-bold text-slate-500 uppercase">{m.role}</div>
                <input
                  type="text"
                  value={m.name || ""}
                  onChange={e => updateTeamMember(m.id, { name: e.target.value, status: e.target.value ? "active" : "to_be_hired" })}
                  placeholder="Assign a person..."
                  className="w-full text-lg font-black mt-1 outline-none focus:bg-slate-50 rounded px-1 -mx-1"
                />
                <input
                  type="email"
                  value={m.email || ""}
                  onChange={e => updateTeamMember(m.id, { email: e.target.value })}
                  placeholder="email@company.com"
                  className="w-full text-xs text-slate-500 mt-1 outline-none focus:bg-slate-50 rounded px-1 -mx-1"
                />
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-400">×{m.count}</div>
                <div className="text-xs text-slate-400">{m.allocation}</div>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${m.status === "active" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                {m.status === "active" ? "● Active" : "○ To be hired"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// STAKEHOLDERS VIEW - power/interest matrix
// ============================================================
function StakeholdersView({ ws, updateStakeholder }) {
  const quadrants = {
    "High-High": { title: "Manage Closely", color: "bg-rose-50 border-rose-300", strategy: "High power, high interest" },
    "High-Low":  { title: "Keep Satisfied", color: "bg-amber-50 border-amber-300", strategy: "High power, low interest" },
    "Low-High":  { title: "Keep Informed", color: "bg-blue-50 border-blue-300", strategy: "Low power, high interest" },
    "Low-Low":   { title: "Monitor", color: "bg-slate-50 border-slate-300", strategy: "Low power, low interest" },
  };
  function bucket(s) {
    const p = (s.power || "").toLowerCase().startsWith("h") ? "High" : "Low";
    const i = (s.interest || "").toLowerCase().startsWith("h") ? "High" : "Low";
    return `${p}-${i}`;
  }
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-black">Stakeholders</h1>
      <p className="text-slate-600 text-sm">Power/interest matrix. Click a stakeholder to edit their details.</p>

      <div className="grid grid-cols-2 gap-4">
        {Object.entries(quadrants).map(([key, q]) => {
          const members = (ws.stakeholders || []).filter(s => bucket(s) === key);
          return (
            <div key={key} className={`rounded-2xl border-2 p-4 ${q.color}`}>
              <div className="text-xs font-bold uppercase text-slate-600">{q.strategy}</div>
              <div className="text-lg font-black mt-1">{q.title}</div>
              <div className="mt-3 space-y-2">
                {members.map(s => (
                  <div key={s.id} className="bg-white rounded-lg p-3 border">
                    <input
                      type="text"
                      value={s.name}
                      onChange={e => updateStakeholder(s.id, { name: e.target.value })}
                      className="font-bold text-sm w-full outline-none focus:bg-slate-50 rounded px-1 -mx-1"
                    />
                    <input
                      type="text"
                      value={s.channel}
                      onChange={e => updateStakeholder(s.id, { channel: e.target.value })}
                      className="text-xs text-slate-600 w-full outline-none focus:bg-slate-50 rounded px-1 -mx-1 mt-1"
                    />
                    <div className="mt-2 flex gap-2 text-[10px]">
                      <select value={s.power} onChange={e => updateStakeholder(s.id, { power: e.target.value })} className="bg-transparent outline-none">
                        <option>High</option><option>Medium</option><option>Low</option>
                      </select>
                      <select value={s.interest} onChange={e => updateStakeholder(s.id, { interest: e.target.value })} className="bg-transparent outline-none">
                        <option>High</option><option>Medium</option><option>Low</option>
                      </select>
                    </div>
                  </div>
                ))}
                {members.length === 0 && <div className="text-xs text-slate-400 italic">No stakeholders in this quadrant</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// TIMELINE VIEW - horizontal sprint bars
// ============================================================
function TimelineView({ ws }) {
  const maxWeek = Math.max(...(ws.sprints || []).map(s => s.end_week || 0), 1);
  const colors = ["bg-indigo-500", "bg-purple-500", "bg-emerald-500", "bg-amber-500", "bg-rose-500", "bg-sky-500", "bg-violet-500"];
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-black">Timeline</h1>
      <p className="text-slate-600 text-sm">Sprint schedule across {maxWeek} weeks. Each bar represents a phase of the methodology plan.</p>

      <div className="bg-white rounded-2xl border shadow-sm p-6 overflow-x-auto">
        <div className="min-w-[800px]">
          {/* Week headers */}
          <div className="flex border-b pb-2 mb-3">
            <div className="w-48 flex-shrink-0 text-xs font-bold text-slate-500 uppercase">Sprint</div>
            <div className="flex-1 flex">
              {Array.from({ length: maxWeek }, (_, i) => (
                <div key={i} className="flex-1 text-[10px] text-center text-slate-400 font-mono">W{i + 1}</div>
              ))}
            </div>
          </div>
          {ws.sprints?.map((sprint, i) => {
            const startPct = ((sprint.start_week - 1) / maxWeek) * 100;
            const widthPct = ((sprint.end_week - sprint.start_week + 1) / maxWeek) * 100;
            return (
              <div key={sprint.id} className="flex items-center mb-3">
                <div className="w-48 flex-shrink-0 pr-3">
                  <div className="text-sm font-bold truncate" title={sprint.name}>{sprint.name}</div>
                  <div className="text-[10px] text-slate-500">Weeks {sprint.start_week}–{sprint.end_week}</div>
                </div>
                <div className="flex-1 relative h-8 bg-slate-50 rounded">
                  <div
                    className={`absolute top-0 h-8 rounded ${colors[i % colors.length]} flex items-center px-2 text-[10px] text-white font-bold`}
                    style={{ left: `${startPct}%`, width: `${widthPct}%` }}
                  >
                    Sprint {sprint.number}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// DASHBOARD VIEW - summary metrics
// ============================================================
function DashboardView({ ws }) {
  const totalTasks = ws.tasks?.length || 0;
  const doneTasks = ws.tasks?.filter(t => t.status === "done").length || 0;
  const inProgressTasks = ws.tasks?.filter(t => t.status === "in_progress").length || 0;
  const totalPoints = ws.tasks?.reduce((s, t) => s + (t.story_points || 0), 0) || 0;
  const donePoints = ws.tasks?.filter(t => t.status === "done").reduce((s, t) => s + (t.story_points || 0), 0) || 0;
  const highRisks = ws.risks?.filter(r => r.score >= 15).length || 0;
  const openRisks = ws.risks?.filter(r => r.status === "open").length || 0;
  const activeTeam = ws.team?.filter(m => m.status === "active").length || 0;
  const completionPct = totalTasks ? Math.round(100 * doneTasks / totalTasks) : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-black">Dashboard</h1>

      {/* Hero metric */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 text-white rounded-3xl p-8 shadow-xl">
        <div className="text-xs uppercase tracking-wider opacity-70">Project Progress</div>
        <div className="text-6xl font-black mt-2">{completionPct}%</div>
        <div className="text-sm opacity-80 mt-1">{doneTasks} of {totalTasks} tasks completed · {donePoints} of {totalPoints} story points shipped</div>
        <div className="mt-4 h-3 bg-white/20 rounded-full overflow-hidden">
          <div className="h-full bg-white" style={{ width: `${completionPct}%` }} />
        </div>
      </div>

      {/* Metric grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricTile label="In Progress" value={inProgressTasks} icon="🔄" color="blue" />
        <MetricTile label="High-Risk Items" value={highRisks} icon="⚠️" color="rose" />
        <MetricTile label="Open Risks" value={openRisks} icon="🛡️" color="amber" />
        <MetricTile label="Active Team" value={`${activeTeam}/${ws.team?.length || 0}`} icon="👥" color="emerald" />
      </div>

      {/* Sprint breakdown */}
      <div className="bg-white rounded-2xl border shadow-sm p-6">
        <h2 className="text-lg font-black mb-4">Sprint Health</h2>
        <div className="space-y-3">
          {ws.sprints?.map(sprint => {
            const sprintTasks = ws.tasks?.filter(t => t.sprint_id === sprint.id) || [];
            const sDone = sprintTasks.filter(t => t.status === "done").length;
            const pct = sprintTasks.length ? Math.round(100 * sDone / sprintTasks.length) : 0;
            return (
              <div key={sprint.id}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-bold">{sprint.name}</span>
                  <span className="text-slate-500">{sDone}/{sprintTasks.length} · {pct}%</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500" style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Budget */}
      <div className="bg-white rounded-2xl border shadow-sm p-6">
        <h2 className="text-lg font-black mb-4">Budget Allocation</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {["people", "tools", "infrastructure", "contingency", "total"].map(k => (
            <div key={k} className={`p-3 rounded-lg ${k === "total" ? "bg-indigo-50 border-2 border-indigo-300" : "bg-slate-50"}`}>
              <div className="text-[10px] font-bold uppercase text-slate-600">{k}</div>
              <div className="text-lg font-black mt-1">${(ws.budget?.[k] || 0).toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function MetricTile({ label, value, icon, color }) {
  return (
    <div className={`bg-${color}-50 rounded-xl p-4 border border-${color}-100`}>
      <div className="flex items-center justify-between">
        <div className={`text-[10px] font-bold text-${color}-700 uppercase tracking-wider`}>{label}</div>
        <span>{icon}</span>
      </div>
      <div className="text-2xl font-black text-slate-900 mt-2">{value}</div>
    </div>
  );
}
