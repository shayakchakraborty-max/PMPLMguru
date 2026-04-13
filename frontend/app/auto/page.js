"use client";
import { useState } from "react";

// Two-stage autopilot UI: Idea -> PM Plan -> Approve -> PLM Execute -> Prototype
// All errors surface as friendly messages instead of "Server returned 500".

const PHASE_COLORS = [
  "from-indigo-500 to-purple-600",
  "from-emerald-500 to-teal-600",
  "from-amber-500 to-orange-600",
  "from-rose-500 to-pink-600",
  "from-sky-500 to-blue-600",
  "from-violet-500 to-fuchsia-600",
  "from-lime-500 to-green-600",
  "from-cyan-500 to-blue-500",
];

export default function AutoPage() {
  const [idea, setIdea] = useState("");
  const [step, setStep] = useState("idle"); // idle | pm_loading | pm_done | plm_loading | plm_done
  const [pmData, setPmData] = useState(null);
  const [plmData, setPlmData] = useState(null);
  const [prototype, setPrototype] = useState(null);
  const [error, setError] = useState("");

  async function runPMStage() {
    if (!idea.trim()) {
      setError("Please enter a project idea first.");
      return;
    }
    setError("");
    setPmData(null);
    setPlmData(null);
    setPrototype(null);
    setStep("pm_loading");
    try {
      const r = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: "pm", idea }),
      });
      const data = await r.json();
      if (data.error) {
        setError(data.error + (data.detail ? "\n\nDetails: " + JSON.stringify(data.detail).slice(0, 500) : ""));
        setStep("idle");
        return;
      }
      setPmData(data);
      setStep("pm_done");
    } catch (e) {
      setError("Network error: " + e.message);
      setStep("idle");
    }
  }

  async function runPLMStage() {
    setError("");
    setStep("plm_loading");
    try {
      const r = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: "plm", idea, pm_plan: pmData }),
      });
      const data = await r.json();
      if (data.error) {
        setError(data.error);
        setStep("pm_done");
        return;
      }
      setPlmData(data);

      // Also fetch prototype
      try {
        const pr = await fetch("/api/prototype", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idea }),
        });
        const pd = await pr.json();
        if (pd.html) setPrototype(pd.html);
      } catch (e) {
        console.warn("Prototype fetch failed:", e);
      }

      setStep("plm_done");
    } catch (e) {
      setError("Network error: " + e.message);
      setStep("pm_done");
    }
  }

  function downloadHTML(html, filename) {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function reset() {
    setIdea("");
    setPmData(null);
    setPlmData(null);
    setPrototype(null);
    setError("");
    setStep("idle");
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-6xl mx-auto p-6">
        <header className="mb-8">
          <h1 className="text-4xl font-black tracking-tight">📊 PMGuru Autopilot v9.1</h1>
          <p className="text-slate-600 mt-2">Enter idea → Get PM strategy → Approve → Run PLM execution → Ship prototype</p>
        </header>

        {/* Progress tracker */}
        <div className="flex items-center gap-2 mb-6 text-sm">
          <StepBadge active={step === "idle" || step === "pm_loading"} done={!!pmData} label="1. Idea" />
          <Chevron />
          <StepBadge active={step === "pm_loading"} done={!!pmData} label="2. PM Plan" loading={step === "pm_loading"} />
          <Chevron />
          <StepBadge active={step === "pm_done"} done={!!plmData} label="3. Approve" />
          <Chevron />
          <StepBadge active={step === "plm_loading"} done={!!plmData} label="4. PLM Execute" loading={step === "plm_loading"} />
          <Chevron />
          <StepBadge active={step === "plm_done"} done={!!plmData} label="5. Download" />
        </div>

        {/* Idea input */}
        {step === "idle" && (
          <div className="bg-white rounded-2xl shadow-sm border p-6">
            <label className="block text-sm font-semibold text-slate-700 mb-2">Describe your project idea</label>
            <textarea
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              rows={5}
              placeholder="e.g. AI-powered grocery assistant for Indian kirana stores with voice ordering, inventory management, and GST filing..."
              className="w-full p-4 border border-slate-300 rounded-xl text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none"
            />
            <button
              onClick={runPMStage}
              className="mt-4 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg"
            >
              🧠 Generate PM Strategic Plan
            </button>
          </div>
        )}

        {/* Loading state */}
        {(step === "pm_loading" || step === "plm_loading") && (
          <div className="bg-white rounded-2xl shadow-sm border p-10 text-center">
            <div className="inline-block w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-slate-700 font-semibold">
              {step === "pm_loading" ? "4 PM experts analyzing your idea..." : "8 PLM agents executing with PM context..."}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Render free tier may take 30-60s on first request (cold start). Please wait.
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 bg-rose-50 border border-rose-300 rounded-xl p-4">
            <div className="font-bold text-rose-900 mb-1">❌ Error</div>
            <pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre>
            <button onClick={() => { setError(""); setStep("idle"); }} className="mt-3 px-4 py-2 bg-rose-600 text-white rounded-lg text-sm font-bold">
              🔄 Try Again
            </button>
          </div>
        )}

        {/* PM Report */}
        {pmData && step !== "plm_loading" && (
          <div className="mt-6">
            <PMReport data={pmData} />
            {step === "pm_done" && !plmData && (
              <div className="mt-6 flex gap-3">
                <button
                  onClick={runPLMStage}
                  className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-lg"
                >
                  ✅ Approve PM Plan & Run PLM Execution
                </button>
                <button onClick={reset} className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-bold">
                  ← Start Over
                </button>
              </div>
            )}
          </div>
        )}

        {/* PLM Report */}
        {plmData && (
          <div className="mt-6">
            <PLMReport data={plmData} />
            <div className="mt-6 flex gap-3 flex-wrap">
              {prototype && (
                <button
                  onClick={() => downloadHTML(prototype, "prototype.html")}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold"
                >
                  🎨 Download Prototype HTML
                </button>
              )}
              <button onClick={reset} className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-bold">
                ← Start Over
              </button>
            </div>
            {prototype && (
              <div className="mt-6 bg-white rounded-2xl border shadow-sm overflow-hidden">
                <div className="bg-slate-100 px-4 py-2 text-xs font-bold text-slate-600">🎨 LIVE PROTOTYPE PREVIEW</div>
                <iframe srcDoc={prototype} className="w-full h-[600px] border-0" title="prototype" />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StepBadge({ active, done, loading, label }) {
  const base = "px-3 py-1.5 rounded-full text-xs font-bold ";
  if (done) return <div className={base + "bg-emerald-100 text-emerald-700"}>✓ {label}</div>;
  if (loading) return <div className={base + "bg-amber-100 text-amber-800 animate-pulse"}>⏳ {label}</div>;
  if (active) return <div className={base + "bg-indigo-100 text-indigo-700"}>{label}</div>;
  return <div className={base + "bg-slate-100 text-slate-400"}>{label}</div>;
}

function Chevron() {
  return <span className="text-slate-300">→</span>;
}

function PMReport({ data }) {
  const agents = data?.pm_agents || {};
  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-white rounded-3xl p-8 shadow-2xl">
        <div className="text-xs uppercase tracking-[3px] opacity-60">PM STRATEGIC REPORT</div>
        <h2 className="text-3xl font-black mt-2">{data.idea}</h2>
        <div className="mt-2 text-xs opacity-70">
          PMGuru Advisory · {new Date().toLocaleDateString()} · {data.summary?.ok || 0}/{data.summary?.total || 0} agents succeeded
        </div>
      </div>
      {Object.entries(agents).map(([name, agent]) => (
        <AgentCard key={name} name={name} agent={agent} />
      ))}
    </div>
  );
}

function AgentCard({ name, agent }) {
  const statusColor =
    agent.status === "ok" ? "bg-emerald-100 text-emerald-700" :
    agent.status === "partial" ? "bg-amber-100 text-amber-700" :
    "bg-rose-100 text-rose-700";
  return (
    <div className="bg-white rounded-2xl shadow-sm border p-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{agent.icon}</span>
          <div>
            <h3 className="font-black text-slate-900">{name}</h3>
            <p className="text-xs text-slate-500">{agent.role}</p>
          </div>
        </div>
        <span className={`text-xs font-bold px-2 py-1 rounded ${statusColor}`}>{agent.status}</span>
      </div>
      {agent.error && <div className="text-xs text-rose-700 bg-rose-50 p-2 rounded mb-2">{agent.error}</div>}
      <pre className="text-xs text-slate-700 bg-slate-50 p-3 rounded-lg overflow-auto max-h-80 whitespace-pre-wrap">
        {JSON.stringify(agent.data, null, 2)}
      </pre>
    </div>
  );
}

function PLMReport({ data }) {
  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-3xl p-8 shadow-2xl">
        <div className="text-xs uppercase tracking-[3px] opacity-70">PLM EXECUTION REPORT</div>
        <h2 className="text-3xl font-black mt-2">{data.idea}</h2>
        <div className="mt-2 text-xs opacity-80">
          {data.summary?.ok || 0}/{data.summary?.total || 0} phases completed
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        {(data.phases || []).map((p, i) => (
          <div key={p.id} className={`rounded-2xl p-5 text-white shadow-lg bg-gradient-to-br ${PHASE_COLORS[i % PHASE_COLORS.length]}`}>
            <div className="text-xs opacity-80">PHASE {p.id} · {p.duration}</div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl">{p.icon}</span>
              <h3 className="text-xl font-black">{p.name}</h3>
            </div>
            <div className="text-xs opacity-80 mt-1">by {p.agent} · {p.status}</div>
            <pre className="text-xs mt-3 bg-black/20 p-2 rounded overflow-auto max-h-48 whitespace-pre-wrap">
              {JSON.stringify(p.data, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
