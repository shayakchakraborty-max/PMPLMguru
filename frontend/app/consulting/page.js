"use client";
import { useState } from "react";

const DOMAINS = [
  { key: "O2C", icon: "💰", name: "Order to Cash", desc: "Credit, billing, collections, revenue, cash application" },
  { key: "P2P", icon: "🛒", name: "Procure to Pay", desc: "Requisition, PO, vendor, invoice, payment" },
  { key: "R2R", icon: "📊", name: "Record to Report", desc: "GL, close, reconciliation, reporting, consolidation" },
  { key: "GL", icon: "📒", name: "General Accounting", desc: "Fixed assets, bank recon, expenses, controls, audit" },
  { key: "FPA", icon: "📈", name: "FP&A", desc: "Budgeting, forecasting, variance, modeling, reporting" },
  { key: "TAX", icon: "⚖️", name: "Tax & Compliance", desc: "GST, direct tax, transfer pricing, compliance" },
  { key: "TREASURY", icon: "🏦", name: "Treasury", desc: "Cash management, FX, debt, bank relations" },
  { key: "AUDIT", icon: "🔍", name: "Internal Audit", desc: "Risk assessment, SOX, IT audit, compliance" },
  { key: "SUPPLY", icon: "🚚", name: "Supply Chain", desc: "Inventory, demand, logistics, procurement, quality" },
  { key: "HR", icon: "👥", name: "HR & Payroll", desc: "Payroll, benefits, compensation, compliance, analytics" },
  { key: "RISK", icon: "🛡️", name: "Risk & Cyber", desc: "ERM, fraud, BCP, cybersecurity, incident response" },
  { key: "DIGITAL", icon: "🖥️", name: "Digital & GRC", desc: "ERP, RPA, cloud, AI governance, ESG, process" },
];

export default function ConsultingLauncher() {
  const [description, setDescription] = useState("");
  const [selectedDomains, setSelectedDomains] = useState([]);
  const [error, setError] = useState("");

  function toggleDomain(key) {
    setSelectedDomains(prev => prev.includes(key) ? prev.filter(d => d !== key) : prev.length < 6 ? [...prev, key] : prev);
  }

  function generateReport() {
    if (!description.trim()) { setError("Please describe the business or engagement context."); return; }
    setError("");
    const params = new URLSearchParams({ description });
    if (selectedDomains.length > 0) params.set("domains", selectedDomains.join(","));
    sessionStorage.setItem("consulting_description", description);
    if (selectedDomains.length > 0) sessionStorage.setItem("consulting_domains", selectedDomains.join(","));
    window.location.href = `/consulting/report?${params.toString()}`;
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-5xl mx-auto p-6">
        <header className="mb-8 pt-4">
          <a href="/auto" className="text-xs text-slate-500 hover:text-indigo-600">← Back to home</a>
          <div className="inline-block px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold mt-3 mb-3">
            Consulting Pro · 1,003 Scenarios · 12 Domains
          </div>
          <h1 className="text-4xl font-black tracking-tight">Big 3 + Big 4 consulting intelligence</h1>
          <p className="text-slate-600 mt-2 max-w-2xl">
            Describe any business scenario. Our engine matches it against 1,003 real-world consulting scenarios
            across O2C, P2P, R2R, GL, and 8 more finance domains to generate a consulting-grade assessment report.
          </p>
        </header>

        <div className="bg-white rounded-2xl shadow-lg border p-8 mb-6">
          <label className="block text-sm font-bold text-slate-700 mb-3">
            Describe the business, engagement, or area to assess
          </label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={5}
            placeholder="e.g. Mid-size manufacturing company with 3 plants and $200M revenue. Concerned about AP invoice processing efficiency, weak internal controls over financial reporting, GST compliance gaps, and no formal enterprise risk management. Recently acquired a smaller company and struggling with consolidation."
            className="w-full p-4 border-2 border-slate-200 rounded-xl text-base focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100 outline-none transition" />
          {error && <div className="mt-3 bg-rose-50 border border-rose-300 rounded-lg p-3"><pre className="text-xs text-rose-800 whitespace-pre-wrap">{error}</pre></div>}
        </div>

        <div className="bg-white rounded-2xl shadow-sm border p-8 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm font-bold text-slate-700">Focus domains (optional)</div>
              <div className="text-xs text-slate-500 mt-0.5">Select up to 6, or leave empty to auto-detect from your description</div>
            </div>
            {selectedDomains.length > 0 && (
              <button onClick={() => setSelectedDomains([])} className="text-xs text-slate-400 hover:text-rose-600">Clear all</button>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {DOMAINS.map(d => {
              const selected = selectedDomains.includes(d.key);
              return (
                <button key={d.key} onClick={() => toggleDomain(d.key)}
                  className={`text-left p-4 rounded-xl border-2 transition ${selected ? "border-emerald-500 bg-emerald-50 shadow-sm" : "border-slate-200 hover:border-emerald-300 bg-white"}`}>
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{d.icon}</span>
                    <span className="font-black text-sm">{d.name}</span>
                    {selected && <span className="ml-auto text-emerald-600 text-sm">✓</span>}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1 leading-tight">{d.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        <button onClick={generateReport} disabled={!description.trim()}
          className="w-full px-6 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-black text-lg hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-lg">
          Generate Consulting Report →
        </button>

        <div className="mt-8 bg-slate-900 rounded-2xl p-6 text-white">
          <div className="text-xs uppercase tracking-wider opacity-50 font-bold mb-3">What the report includes</div>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div><span className="font-black">📋 Engagement Summary</span><br /><span className="opacity-70">McKinsey pyramid principle</span></div>
            <div><span className="font-black">📊 Maturity Assessment</span><br /><span className="opacity-70">CMMI levels per domain</span></div>
            <div><span className="font-black">🔍 Key Findings</span><br /><span className="opacity-70">Big 4 audit-style findings</span></div>
            <div><span className="font-black">📐 Gap Analysis</span><br /><span className="opacity-70">Current vs target state</span></div>
            <div><span className="font-black">📈 Benchmarks</span><br /><span className="opacity-70">APQC & Hackett Group data</span></div>
            <div><span className="font-black">🎯 Recommendations</span><br /><span className="opacity-70">Quick wins + strategic</span></div>
            <div><span className="font-black">🗺️ Roadmap</span><br /><span className="opacity-70">3-phase implementation</span></div>
            <div><span className="font-black">💰 ROI Analysis</span><br /><span className="opacity-70">3-year value creation</span></div>
            <div><span className="font-black">🏛️ Governance</span><br /><span className="opacity-70">Three lines model</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
