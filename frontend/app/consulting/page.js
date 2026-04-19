"use client";
import { useState, useEffect } from "react";

const BRAIN = "";  // API calls go through Next.js proxy

const AGENTS = [
  { key: "engagement_lead", name: "Priya Sharma", title: "Engagement Partner", firm: "McKinsey", icon: "👩‍💼", color: "indigo" },
  { key: "process_analyst", name: "Rajesh Mehta", title: "Sr. Manager — Process", firm: "Deloitte", icon: "🔬", color: "blue" },
  { key: "controls_specialist", name: "Sarah Chen", title: "Director — Controls", firm: "PwC", icon: "🛡️", color: "purple" },
  { key: "transformation_architect", name: "Amit Verma", title: "Partner — Digital", firm: "EY", icon: "🏗️", color: "emerald" },
  { key: "value_engineer", name: "Kavita Iyer", title: "Principal — Value", firm: "BCG", icon: "💎", color: "amber" },
  { key: "tax_advisory", name: "Vikram Nair", title: "Tax Partner", firm: "KPMG", icon: "⚖️", color: "rose" },
  { key: "treasury_specialist", name: "Ananya Desai", title: "Treasury Lead", firm: "Deloitte", icon: "🏦", color: "cyan" },
  { key: "audit_lead", name: "Karthik Rajan", title: "IA Director", firm: "Bain", icon: "🔍", color: "violet" },
];

const DOMAINS = [
  { key: "O2C", icon: "💰", name: "Order to Cash" }, { key: "P2P", icon: "🛒", name: "Procure to Pay" },
  { key: "R2R", icon: "📊", name: "Record to Report" }, { key: "GL", icon: "📒", name: "General Accounting" },
  { key: "FPA", icon: "📈", name: "FP&A" }, { key: "TAX", icon: "⚖️", name: "Tax & Compliance" },
  { key: "TREASURY", icon: "🏦", name: "Treasury" }, { key: "AUDIT", icon: "🔍", name: "Internal Audit" },
  { key: "SUPPLY", icon: "🚚", name: "Supply Chain" }, { key: "HR", icon: "👥", name: "HR & Payroll" },
  { key: "RISK", icon: "🛡️", name: "Risk & Cyber" }, { key: "DIGITAL", icon: "🖥️", name: "Digital & GRC" },
];

const INDUSTRIES = ["Manufacturing", "Retail", "BFSI", "Healthcare", "Technology", "Pharma", "FMCG", "Real Estate", "Energy", "Telecom", "Automotive", "Hospitality", "E-commerce", "Education", "Agriculture", "Mining", "Media", "Logistics", "Insurance", "Infrastructure"];
const REVENUES = ["<$10M", "$10M-$50M", "$50M-$200M", "$200M-$500M", "$500M-$1B", "$1B-$5B", ">$5B"];
const EMPLOYEES = ["<100", "100-500", "500-2000", "2000-10000", "10000-50000", ">50000"];
const ENG_TYPES = ["Full Finance Transformation", "Process-specific Assessment", "Controls & SOX Readiness", "Technology Modernization (ERP/RPA/AI)", "Post-M&A Integration", "IPO Readiness", "Cost Optimization", "Regulatory Compliance Review"];

const WORKFLOW_PHASES = [
  { id: 1, name: "Scoping", icon: "📝", dur: "1-2 wk", color: "from-slate-500 to-slate-700" },
  { id: 2, name: "Discovery", icon: "🔍", dur: "2-4 wk", color: "from-indigo-500 to-blue-600" },
  { id: 3, name: "Assessment", icon: "📊", dur: "2-3 wk", color: "from-purple-500 to-violet-600" },
  { id: 4, name: "Recommendations", icon: "🎯", dur: "2-3 wk", color: "from-emerald-500 to-teal-600" },
  { id: 5, name: "Reporting", icon: "📑", dur: "1-2 wk", color: "from-amber-500 to-orange-600" },
  { id: 6, name: "Implementation", icon: "🚀", dur: "3-12 mo", color: "from-rose-500 to-pink-600" },
];

const DEMOS = [
  { id: "demo-manufacturing-fintransform", icon: "🏭", title: "Manufacturing Finance Transformation", sub: "$800M · SAP ECC · IPO in 18 months", domains: ["O2C","P2P","R2R","GL","TAX","FPA"] },
  { id: "demo-bank-controls", icon: "🏦", title: "Bank SOX & Controls Remediation", sub: "$2B AUM · 150 branches · RBI observations", domains: ["GL","AUDIT","RISK","TREASURY"] },
  { id: "demo-fmcg-p2p", icon: "📦", title: "FMCG P2P Optimization", sub: "$300M · Oracle EBS · 40% maverick spend", domains: ["P2P","SUPPLY","FPA"] },
  { id: "demo-tech-digital", icon: "💻", title: "Tech Digital Finance & AI Governance", sub: "$150M · NetSuite · SOC 2 needed", domains: ["DIGITAL","RISK","AUDIT","R2R"] },
];

export default function ConsultingPage() {
  const [tab, setTab] = useState("workflow"); // workflow | dd | demos
  const [dd, setDd] = useState({ company_name: "", industry: "", revenue: "", employees: "", erp_system: "", recent_changes: "", primary_domains: [], engagement_type: "", pain_points: "", close_days: "", automation_level: "", sox_applicable: "", recent_audit_findings: "", shared_services: "", additional_context: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function updateDd(key, val) { setDd(prev => ({ ...prev, [key]: val })); }
  function toggleDomain(key) { setDd(prev => ({ ...prev, primary_domains: prev.primary_domains.includes(key) ? prev.primary_domains.filter(d => d !== key) : [...prev.primary_domains, key] })); }

  async function submitDD() {
    if (!dd.company_name || !dd.industry || !dd.pain_points || dd.primary_domains.length === 0) {
      setError("Please fill in company name, industry, focus domains, and pain points."); return;
    }
    setError(""); setLoading(true);
    sessionStorage.setItem("consulting_dd", JSON.stringify(dd));
    window.location.href = `/consulting/report?mode=dd`;
  }

  function openDemo(demoId) {
    window.location.href = `/consulting/report?mode=demo&id=${demoId}`;
  }

  function quickStart(description) {
    sessionStorage.setItem("consulting_description", description);
    window.location.href = `/consulting/report?description=${encodeURIComponent(description)}`;
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-6xl mx-auto p-6">
        <header className="mb-6 pt-4">
          <a href="/auto" className="text-xs text-slate-500 hover:text-emerald-600">← Back to home</a>
          <div className="flex items-center gap-3 mt-3">
            <div className="inline-block px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold">Consulting Pro</div>
            <div className="inline-block px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-bold">20,060 scenarios · 12 domains · 8 AI agents</div>
          </div>
          <h1 className="text-4xl font-black tracking-tight mt-3">Finance Transformation Intelligence</h1>
          <p className="text-slate-600 mt-2 max-w-3xl">Research-grade AI consulting agents trained on Big 3 + Big 4 methodologies. Fill in the due diligence questionnaire and the agents generate a consulting-grade assessment report — the same work a team of 6 consultants does in 4 weeks.</p>
        </header>

        {/* AI Agents bar */}
        <div className="bg-slate-900 rounded-2xl p-5 mb-6 overflow-x-auto">
          <div className="text-[10px] text-slate-400 uppercase tracking-wider font-bold mb-3">Your AI Consulting Team</div>
          <div className="flex gap-3 min-w-[700px]">
            {AGENTS.map(a => (
              <div key={a.key} className="bg-slate-800 rounded-xl p-3 flex-1 min-w-0">
                <div className="text-xl">{a.icon}</div>
                <div className="text-xs font-bold text-white mt-1 truncate">{a.name}</div>
                <div className="text-[10px] text-slate-400 truncate">{a.title}</div>
                <div className="text-[10px] text-emerald-400 font-bold mt-0.5">{a.firm}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white rounded-xl border p-1 mb-6">
          {[
            { key: "workflow", label: "📋 Engagement Workflow", sub: "How Big 4 runs a project" },
            { key: "dd", label: "📝 Due Diligence Form", sub: "Fill details → AI generates report" },
            { key: "demos", label: "📑 Demo Reports", sub: "Preloaded consulting reports" },
          ].map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`flex-1 p-3 rounded-lg text-left transition ${tab === t.key ? "bg-emerald-600 text-white shadow" : "hover:bg-slate-50"}`}>
              <div className="text-sm font-bold">{t.label}</div>
              <div className={`text-[10px] mt-0.5 ${tab === t.key ? "opacity-80" : "text-slate-500"}`}>{t.sub}</div>
            </button>
          ))}
        </div>

        {/* Workflow tab */}
        {tab === "workflow" && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl border p-6 overflow-x-auto">
              <div className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-4">The 6-Phase Consulting Engagement</div>
              <div className="flex items-center gap-2 min-w-[700px]">
                {WORKFLOW_PHASES.map((p, i) => (
                  <div key={p.id} className="flex items-center flex-1">
                    <div className={`flex-1 rounded-xl p-3 text-white text-center bg-gradient-to-br ${p.color}`}>
                      <div className="text-2xl">{p.icon}</div>
                      <div className="text-xs font-black mt-1">{p.name}</div>
                      <div className="text-[10px] opacity-70">{p.dur}</div>
                    </div>
                    {i < 5 && <div className="text-slate-300 text-xl px-1">→</div>}
                  </div>
                ))}
              </div>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              {WORKFLOW_PHASES.map(p => (
                <div key={p.id} className="bg-white rounded-xl border p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{p.icon}</span>
                    <div>
                      <div className="text-xs text-emerald-600 font-bold uppercase">Phase {p.id} · {p.dur}</div>
                      <div className="font-black text-lg">{p.name}</div>
                    </div>
                  </div>
                  <p className="text-xs text-slate-600">{p.id === 1 ? "Define engagement scope, objectives, deliverables, team composition, and timeline." : p.id === 2 ? "Conduct stakeholder interviews, process walkthroughs, document reviews, data collection." : p.id === 3 ? "Analyze findings against best practices, benchmark against peers, assess maturity levels." : p.id === 4 ? "Develop prioritized recommendations, design target operating model, build business cases." : p.id === 5 ? "Compile findings into consulting-grade deliverables. Present to C-suite." : "Support execution, program governance, change management, progress reviews."}</p>
                </div>
              ))}
            </div>
            <div className="text-center mt-4">
              <button onClick={() => setTab("dd")} className="px-8 py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 transition">
                Start Due Diligence →
              </button>
            </div>
          </div>
        )}

        {/* Due Diligence Form */}
        {tab === "dd" && (
          <div className="space-y-6">
            {/* Section 1: Company Profile */}
            <div className="bg-white rounded-2xl border p-6">
              <div className="flex items-center gap-2 mb-4"><span className="text-xl">🏢</span><h2 className="font-black text-lg">Company Profile</h2></div>
              <div className="grid md:grid-cols-2 gap-4">
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">Company / Client name *</label><input value={dd.company_name} onChange={e => updateDd("company_name", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none" placeholder="e.g. Bharat Industries Ltd." /></div>
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">Industry *</label><select value={dd.industry} onChange={e => updateDd("industry", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none"><option value="">Select...</option>{INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}</select></div>
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">Annual revenue</label><select value={dd.revenue} onChange={e => updateDd("revenue", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none"><option value="">Select...</option>{REVENUES.map(r => <option key={r} value={r}>{r}</option>)}</select></div>
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">Employees</label><select value={dd.employees} onChange={e => updateDd("employees", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none"><option value="">Select...</option>{EMPLOYEES.map(e2 => <option key={e2} value={e2}>{e2}</option>)}</select></div>
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">ERP / Accounting system</label><input value={dd.erp_system} onChange={e => updateDd("erp_system", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none" placeholder="e.g. SAP ECC 6.0, Tally, Oracle" /></div>
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">Recent events</label><input value={dd.recent_changes} onChange={e => updateDd("recent_changes", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none" placeholder="M&A, restructuring, IPO prep..." /></div>
              </div>
            </div>

            {/* Section 2: Scope */}
            <div className="bg-white rounded-2xl border p-6">
              <div className="flex items-center gap-2 mb-4"><span className="text-xl">🎯</span><h2 className="font-black text-lg">Engagement Scope</h2></div>
              <div className="mb-4">
                <label className="text-xs font-bold text-slate-700 mb-2 block">Focus domains * (select all that apply)</label>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {DOMAINS.map(d => (
                    <button key={d.key} onClick={() => toggleDomain(d.key)}
                      className={`text-left p-3 rounded-lg border-2 text-sm transition ${dd.primary_domains.includes(d.key) ? "border-emerald-500 bg-emerald-50" : "border-slate-200 hover:border-emerald-300"}`}>
                      {d.icon} {d.name} {dd.primary_domains.includes(d.key) && <span className="text-emerald-600 float-right">✓</span>}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">Engagement type</label><select value={dd.engagement_type} onChange={e => updateDd("engagement_type", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none"><option value="">Select...</option>{ENG_TYPES.map(t => <option key={t} value={t}>{t}</option>)}</select></div>
              </div>
              <div><label className="text-xs font-bold text-slate-700 mb-1 block">Top pain points / concerns *</label><textarea value={dd.pain_points} onChange={e => updateDd("pain_points", e.target.value)} rows={4} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none" placeholder="e.g. Close takes 15 days, no cash forecast, high invoice errors, SOX findings increasing..." /></div>
            </div>

            {/* Section 3: Current State */}
            <div className="bg-white rounded-2xl border p-6">
              <div className="flex items-center gap-2 mb-4"><span className="text-xl">📋</span><h2 className="font-black text-lg">Current State (optional — enriches the report)</h2></div>
              <div className="grid md:grid-cols-2 gap-4">
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">Month-end close cycle</label><select value={dd.close_days} onChange={e => updateDd("close_days", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none"><option value="">Select...</option>{["<5 days", "5-7 days", "8-10 days", "11-15 days", ">15 days"].map(o => <option key={o} value={o}>{o}</option>)}</select></div>
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">Automation level</label><select value={dd.automation_level} onChange={e => updateDd("automation_level", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none"><option value="">Select...</option>{["<20% (mostly manual)", "20-40%", "40-60%", "60-80%", ">80% (highly automated)"].map(o => <option key={o} value={o}>{o}</option>)}</select></div>
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">SOX / ICFR applicable?</label><select value={dd.sox_applicable} onChange={e => updateDd("sox_applicable", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none"><option value="">Select...</option>{["Yes - publicly listed", "Yes - IPO planned", "No - private company", "Partial - subsidiary of listed entity"].map(o => <option key={o} value={o}>{o}</option>)}</select></div>
                <div><label className="text-xs font-bold text-slate-700 mb-1 block">Open audit findings</label><select value={dd.recent_audit_findings} onChange={e => updateDd("recent_audit_findings", e.target.value)} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none"><option value="">Select...</option>{["0", "1-5", "6-15", "16-30", ">30"].map(o => <option key={o} value={o}>{o}</option>)}</select></div>
              </div>
              <div className="mt-4"><label className="text-xs font-bold text-slate-700 mb-1 block">Additional context</label><textarea value={dd.additional_context} onChange={e => updateDd("additional_context", e.target.value)} rows={3} className="w-full p-3 border-2 border-slate-200 rounded-lg text-sm focus:border-emerald-500 outline-none" placeholder="Anything else the consulting team should know..." /></div>
            </div>

            {error && <div className="bg-rose-50 border border-rose-300 rounded-lg p-3"><pre className="text-xs text-rose-800">{error}</pre></div>}
            <button onClick={submitDD} disabled={loading} className="w-full px-6 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-black text-lg hover:opacity-90 disabled:opacity-40 transition shadow-lg">
              {loading ? "Deploying AI agents..." : "Generate Consulting Report →"}
            </button>
          </div>
        )}

        {/* Demo Reports tab */}
        {tab === "demos" && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600 mb-4">Preloaded consulting reports — click any to see the full Big 3 + Big 4 style assessment instantly.</p>
            <div className="grid md:grid-cols-2 gap-4">
              {DEMOS.map(d => (
                <button key={d.id} onClick={() => openDemo(d.id)}
                  className="bg-white rounded-2xl border-2 border-slate-200 hover:border-emerald-500 p-6 text-left hover:shadow-lg transition group">
                  <div className="text-4xl mb-3">{d.icon}</div>
                  <h3 className="font-black text-lg group-hover:text-emerald-700 transition">{d.title}</h3>
                  <p className="text-xs text-slate-500 mt-1">{d.sub}</p>
                  <div className="flex flex-wrap gap-1 mt-3">
                    {d.domains.map(dk => {
                      const dm = DOMAINS.find(x => x.key === dk);
                      return dm ? <span key={dk} className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 font-bold">{dm.icon} {dm.name}</span> : null;
                    })}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
