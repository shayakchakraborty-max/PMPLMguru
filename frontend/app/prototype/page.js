"use client";
import { useState, useEffect } from "react";

// ============================================================
// PMGuru /prototype v1 — interactive HTML prototype viewer
// Reads the prototype payload from localStorage and displays it
// in a sandboxed iframe with download + regenerate controls.
// ============================================================

export default function PrototypePage() {
  const [proto, setProto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState("");
  const [viewMode, setViewMode] = useState("desktop"); // "desktop" | "tablet" | "mobile"

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id") || localStorage.getItem("pmguru_current_proto");
    if (!id) { setLoading(false); return; }
    try {
      const raw = localStorage.getItem(`pmguru_proto_${id}`);
      if (raw) setProto(JSON.parse(raw));
    } catch (e) {
      console.error("Failed to load prototype:", e);
    }
    setLoading(false);
  }, []);

  async function regenerate() {
    if (!proto?.idea) return;
    setRegenerating(true);
    setError("");
    try {
      const r = await fetch("/api/prototype", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea: proto.idea }),
      });
      const data = await r.json();
      if (data.error) {
        setError(data.error);
      } else {
        const updated = { ...proto, html: data.html, _created_at: new Date().toISOString() };
        setProto(updated);
        const id = localStorage.getItem("pmguru_current_proto");
        if (id) localStorage.setItem(`pmguru_proto_${id}`, JSON.stringify(updated));
      }
    } catch (e) {
      setError("Network error: " + e.message);
    }
    setRegenerating(false);
  }

  function downloadHTML() {
    const blob = new Blob([proto.html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Prototype_${(proto.idea || "build").replace(/\W+/g, "_").slice(0, 40)}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function openInNewTab() {
    const blob = new Blob([proto.html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  }

  if (loading) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600">Loading prototype...</div>;
  }
  if (!proto) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">🎨</div>
          <h1 className="text-2xl font-black text-slate-900">No prototype found</h1>
          <p className="text-slate-600 mt-2">Generate one by entering an idea first.</p>
          <a href="/auto" className="inline-block mt-6 px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold">Start on /auto</a>
        </div>
      </div>
    );
  }

  const frameWidth = viewMode === "mobile" ? 390 : viewMode === "tablet" ? 768 : "100%";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <header className="mb-4 pt-4">
          <div className="flex items-start justify-between gap-3 flex-wrap mb-4">
            <a href="/auto" className="text-xs text-slate-500 hover:text-indigo-600 underline">← Back to launcher</a>
            <div className="flex gap-2 flex-wrap">
              <div className="flex bg-white border rounded-lg overflow-hidden">
                <button
                  onClick={() => setViewMode("desktop")}
                  className={`px-3 py-1.5 text-xs font-bold ${viewMode === "desktop" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}
                >
                  🖥️ Desktop
                </button>
                <button
                  onClick={() => setViewMode("tablet")}
                  className={`px-3 py-1.5 text-xs font-bold ${viewMode === "tablet" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}
                >
                  📱 Tablet
                </button>
                <button
                  onClick={() => setViewMode("mobile")}
                  className={`px-3 py-1.5 text-xs font-bold ${viewMode === "mobile" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}
                >
                  📱 Mobile
                </button>
              </div>
              <button onClick={regenerate} disabled={regenerating} className="px-3 py-1.5 bg-white border rounded-lg text-xs font-bold hover:bg-slate-50 disabled:opacity-50">
                {regenerating ? "Regenerating..." : "🔄 Regenerate"}
              </button>
              <button onClick={openInNewTab} className="px-3 py-1.5 bg-white border rounded-lg text-xs font-bold hover:bg-slate-50">
                ↗ Open in new tab
              </button>
              <button onClick={downloadHTML} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700">
                📥 Download HTML
              </button>
            </div>
          </div>

          <div className="inline-block px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold mb-3">
            Interactive Prototype · Working HTML
          </div>
          <h1 className="text-3xl md:text-4xl font-black tracking-tight">{proto.idea}</h1>
          <p className="text-sm text-slate-500 mt-2">
            Clickable, shareable HTML prototype. Download the file to deploy or edit freely.
          </p>
        </header>

        {error && (
          <div className="bg-rose-50 border border-rose-300 rounded-xl p-4 mb-4">
            <div className="font-bold text-rose-900 text-sm mb-1">Error</div>
            <pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre>
          </div>
        )}

        {/* Iframe viewport */}
        <div className="bg-slate-200 rounded-2xl p-4 shadow-inner">
          <div className="bg-white rounded-xl overflow-hidden shadow-lg mx-auto border border-slate-300" style={{ width: frameWidth, maxWidth: "100%", transition: "width 0.3s ease" }}>
            {/* Fake browser chrome */}
            <div className="bg-slate-100 border-b border-slate-200 px-3 py-2 flex items-center gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-rose-400"></div>
                <div className="w-3 h-3 rounded-full bg-amber-400"></div>
                <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
              </div>
              <div className="flex-1 text-center">
                <div className="inline-block px-3 py-0.5 rounded-md bg-white text-xs text-slate-500 font-mono max-w-full truncate">
                  prototype://{(proto.idea || "").toLowerCase().replace(/\W+/g, "-").slice(0, 30)}
                </div>
              </div>
            </div>
            <iframe
              srcDoc={proto.html}
              sandbox="allow-scripts allow-same-origin allow-forms"
              className="w-full border-0"
              style={{ height: viewMode === "mobile" ? 700 : 800 }}
              title="prototype"
            />
          </div>
        </div>

        <div className="mt-6 text-center text-xs text-slate-400">
          PMGuru · Prototype · Generated {proto._created_at ? new Date(proto._created_at).toLocaleString() : "recently"}
        </div>
      </div>
    </div>
  );
}
