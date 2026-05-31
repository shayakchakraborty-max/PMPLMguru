"use client";
import { useEffect, useMemo, useState } from "react";

/* ============================================================
   ERP-styled PLM / PM Workspace Copilot
   - Project -> auto-filled ERP modules (master data, backlog,
     sprints, risks, compliance calendar, KPIs, SOPs, team).
   - Self-explanatory: each module has a copilot "what & why".
   - Editable cells, add rows, persists to localStorage.
   - One-click Export to Notion (markdown: copy or download).
   - Mobile + desktop.
   ============================================================ */

const LS_KEY = "pmguru_erp_workspace";

export default function ErpWorkspace() {
  const [idea, setIdea] = useState("");
  const [ws, setWs] = useState(null);     // { project, modules }
  const [activeId, setActiveId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [copied, setCopied] = useState(false);

  // Load from query/sessionStorage or restore last workspace
  useEffect(() => {
    let seed = "";
    try {
      const u = new URL(window.location.href);
      seed = u.searchParams.get("idea") || sessionStorage.getItem("pmguru_pending_idea") || "";
    } catch {}
    if (seed) { setIdea(seed); build(seed); return; }
    try {
      const saved = JSON.parse(localStorage.getItem(LS_KEY) || "null");
      if (saved?.modules) { setWs(saved); setActiveId(saved.modules[0]?.id); setIdea(saved.project?.name || ""); }
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function persist(next) {
    setWs(next);
    try { localStorage.setItem(LS_KEY, JSON.stringify(next)); } catch {}
  }

  async function build(seedIdea) {
    const text = (seedIdea ?? idea).trim();
    if (!text) { setErr("Please enter your project / business idea."); return; }
    setLoading(true); setErr("");
    try {
      const r = await fetch("/api/workspace-erp", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea: text }),
      });
      const d = await r.json();
      if (d.error) { setErr(d.error); }
      else { persist(d); setActiveId(d.modules[0]?.id); }
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }

  const active = useMemo(() => ws?.modules?.find((m) => m.id === activeId) || ws?.modules?.[0], [ws, activeId]);

  function editCell(moduleId, rowIdx, key, value) {
    if (!ws) return;
    const modules = ws.modules.map((m) => {
      if (m.id !== moduleId) return m;
      const rows = m.rows.map((r, i) => (i === rowIdx ? { ...r, [key]: value } : r));
      return { ...m, rows };
    });
    persist({ ...ws, modules });
  }

  function addRow(moduleId) {
    const modules = ws.modules.map((m) => {
      if (m.id !== moduleId) return m;
      const blank = {}; m.columns.forEach((c) => (blank[c.key] = ""));
      return { ...m, rows: [...m.rows, blank], count: (m.count || m.rows.length) + 1 };
    });
    persist({ ...ws, modules });
  }

  function deleteRow(moduleId, rowIdx) {
    const modules = ws.modules.map((m) => {
      if (m.id !== moduleId) return m;
      const rows = m.rows.filter((_, i) => i !== rowIdx);
      return { ...m, rows, count: rows.length };
    });
    persist({ ...ws, modules });
  }

  function toMarkdown() {
    if (!ws) return "";
    let md = `# ${ws.project?.name || "Workspace"}\n\n`;
    md += `> ${ws.project?.geo === "India" ? "🇮🇳 India" : ws.project?.geo} · ${ws.project?.industry} · ${ws.project?.methodology} · ${ws.project?.total_weeks} weeks · currency ${ws.project?.currency}\n\n`;
    for (const m of ws.modules) {
      md += `## ${m.icon} ${m.name}\n\n_${m.help}_\n\n`;
      md += `| ${m.columns.map((c) => c.label).join(" | ")} |\n`;
      md += `| ${m.columns.map(() => "---").join(" | ")} |\n`;
      for (const row of m.rows) {
        md += `| ${m.columns.map((c) => String(row[c.key] ?? "").replace(/\|/g, "\\|").replace(/\n/g, " ")).join(" | ")} |\n`;
      }
      md += `\n`;
    }
    return md;
  }

  async function copyMarkdown() {
    const md = toMarkdown();
    try { await navigator.clipboard.writeText(md); setCopied(true); setTimeout(() => setCopied(false), 2000); }
    catch { downloadMarkdown(); }
  }

  function downloadMarkdown() {
    const blob = new Blob([toMarkdown()], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${(ws?.project?.name || "workspace").slice(0, 40).replace(/[^a-z0-9]+/gi, "-")}.md`;
    a.click(); URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Top bar */}
      <header className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-5">
          <a href="/auto" className="text-xs text-white/60 hover:text-white">← Home</a>
          <div className="flex items-center gap-2 mt-2 mb-1">
            <span className="text-2xl">🗂️</span>
            <h1 className="text-xl sm:text-2xl font-black">ERP Workspace Copilot</h1>
            <span className="text-[11px] bg-white/10 px-2 py-0.5 rounded-full font-bold">PLM + PM</span>
          </div>
          <p className="text-xs sm:text-sm text-white/70">Turn any project into a self-explanatory, ERP-styled operating workspace — then export it to Notion.</p>
          <div className="mt-4 flex flex-col sm:flex-row gap-2">
            <input value={idea} onChange={(e) => setIdea(e.target.value)} onKeyDown={(e) => e.key === "Enter" && build()}
              placeholder="e.g. AI logistics SaaS for Indian kirana distribution with GST + UPI"
              className="flex-1 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none" />
            <button onClick={() => build()} disabled={loading}
              className="px-5 py-2.5 rounded-xl font-black bg-white text-slate-900 hover:bg-emerald-300 transition disabled:opacity-50">
              {loading ? "Building…" : ws ? "Rebuild" : "Build Workspace →"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {err && <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 text-sm mb-4">{err}</div>}
        {!ws && !loading && !err && (
          <div className="text-center text-slate-400 py-20 text-sm">Enter an idea above to generate your ERP workspace.</div>
        )}
        {loading && <div className="text-center text-slate-400 py-20 text-sm animate-pulse">Building modules…</div>}

        {ws && (
          <>
            {/* Project bar + export */}
            <div className="bg-white border border-slate-200 rounded-2xl p-4 mb-4 flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-black text-slate-900">{ws.project?.name}</span>
                <Tag>{ws.project?.geo === "India" ? "🇮🇳 India" : "🌐 " + ws.project?.geo}</Tag>
                <Tag>{ws.project?.industry}</Tag>
                <Tag>{ws.project?.methodology}</Tag>
                <Tag>{ws.project?.total_weeks} wks</Tag>
              </div>
              <div className="flex gap-2">
                <button onClick={copyMarkdown} className="px-4 py-2 rounded-lg bg-violet-600 text-white text-sm font-bold hover:bg-violet-700">
                  {copied ? "✓ Copied!" : "⧉ Export to Notion"}
                </button>
                <button onClick={downloadMarkdown} className="px-4 py-2 rounded-lg bg-slate-100 text-slate-700 text-sm font-bold hover:bg-slate-200">
                  ⬇ .md
                </button>
              </div>
            </div>

            <div className="grid lg:grid-cols-[230px_1fr] gap-4">
              {/* Module nav */}
              <nav className="flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
                {ws.modules.map((m) => (
                  <button key={m.id} onClick={() => setActiveId(m.id)}
                    className={`shrink-0 text-left px-3 py-2.5 rounded-xl border text-sm font-bold transition flex items-center gap-2 ${active?.id === m.id ? "bg-indigo-600 text-white border-indigo-600" : "bg-white text-slate-700 border-slate-200 hover:border-indigo-300"}`}>
                    <span>{m.icon}</span>
                    <span className="flex-1">{m.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${active?.id === m.id ? "bg-white/20" : "bg-slate-100 text-slate-500"}`}>{m.count ?? m.rows.length}</span>
                  </button>
                ))}
              </nav>

              {/* Active module */}
              {active && (
                <section className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
                  <div className="p-4 border-b bg-slate-50">
                    <h2 className="font-black text-slate-900 flex items-center gap-2">{active.icon} {active.name}</h2>
                    <p className="text-xs text-slate-500 mt-1">💡 {active.help}</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-slate-100 text-left">
                          {active.columns.map((c) => <th key={c.key} className="p-2.5 font-bold text-slate-600 whitespace-nowrap">{c.label}</th>)}
                          <th className="p-2.5 w-8" />
                        </tr>
                      </thead>
                      <tbody>
                        {active.rows.map((row, ri) => (
                          <tr key={ri} className="border-t hover:bg-slate-50 group">
                            {active.columns.map((c) => (
                              <td key={c.key} className="p-1 align-top">
                                <input value={row[c.key] ?? ""} onChange={(e) => editCell(active.id, ri, c.key, e.target.value)}
                                  className="w-full bg-transparent px-1.5 py-1.5 rounded focus:bg-indigo-50 focus:outline-none text-slate-800" />
                              </td>
                            ))}
                            <td className="p-1 text-center">
                              <button onClick={() => deleteRow(active.id, ri)} title="Delete row"
                                className="opacity-0 group-hover:opacity-100 text-slate-300 hover:text-rose-600 text-xs px-1">✕</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="p-3 border-t">
                    <button onClick={() => addRow(active.id)} className="text-sm font-bold text-indigo-600 hover:text-indigo-800">+ Add row</button>
                    <span className="text-xs text-slate-400 ml-3">Edits auto-save in your browser.</span>
                  </div>
                </section>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function Tag({ children }) {
  return <span className="text-[11px] font-bold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full">{children}</span>;
}
