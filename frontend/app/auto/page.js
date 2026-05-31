"use client";
import { useState } from "react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white text-slate-900">
      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Header */}
        <header className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-indigo-100 text-indigo-700 px-4 py-1.5 rounded-full text-xs font-bold mb-6">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
            PMGuru v12 · 20,060 Scenario Coverage · 8 AI Consulting Agents
          </div>
          <h1 className="text-6xl font-black tracking-tight leading-tight">
            The AI brain behind<br />
            <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              great products & great audits
            </span>
          </h1>
          <p className="text-xl text-slate-600 mt-6 max-w-2xl mx-auto">
            Two platforms, one intelligence engine. Whether you're building a product or auditing a business,
            PMGuru delivers consulting-grade insights in seconds.
          </p>
        </header>

        {/* Featured: MSME Advisor */}
        <a href="/advisor"
          className="group block relative overflow-hidden rounded-3xl mb-8 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-8 hover:shadow-2xl transition">
          <div className="flex flex-col md:flex-row md:items-center gap-6">
            <div className="text-5xl">🧭</div>
            <div className="flex-1">
              <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1 rounded-full text-[11px] font-bold mb-2">
                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> NEW · 20 research-grade AI agents
              </div>
              <h2 className="text-3xl font-black">MSME Advisor</h2>
              <p className="text-sm text-slate-300 mt-2 max-w-2xl">
                An AI consulting team for every Indian business. Two modes — <b>New Startup</b> and <b>Existing Business</b> —
                with detailed forms, a full business-type filter, and audit-ready reports (citations, ERP & Notion actions, risks, KPIs).
              </p>
            </div>
            <span className="shrink-0 px-6 py-3.5 bg-white text-slate-900 rounded-xl font-black group-hover:bg-emerald-300 transition">
              Open Advisor →
            </span>
          </div>
        </a>

        {/* Two paths */}
        <div className="grid md:grid-cols-2 gap-6 mb-16">
          {/* Startup */}
          <div className="group relative bg-white rounded-3xl border-2 border-slate-200 hover:border-indigo-500 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden">
            <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-violet-700 text-white p-8">
              <div className="text-5xl mb-4">🚀</div>
              <h2 className="text-3xl font-black">Startup</h2>
              <p className="text-sm opacity-80 mt-2">Build & scale a new India business — idea to execution</p>
            </div>
            <div className="p-8">
              <p className="text-slate-600 mb-6">
                Enter your idea (mention India for ₹ + Indian market, compliance & funding) and get a
                consulting-grade blueprint, a working PM workspace, and a full lifecycle plan — plus the
                startup AI agents (market research, DD, investor readiness, GST).
              </p>
              <div className="space-y-3 mb-8">
                <Feature icon="📑" text="India-aware due-diligence report (₹, GST/Udyam/DPIIT, funding incentives)" />
                <Feature icon="🛠️" text="PM workspace with kanban, sprints, risks, team & timeline" />
                <Feature icon="🔄" text="8-phase product lifecycle + how to scale (Tier-1→2/3→pan-India)" />
                <Feature icon="🧭" text="Startup AI agents: market sizing, competitor intel, investor readiness" />
                <Feature icon="📥" text="Download everything as PDF" />
              </div>
              <a href="/blueprint" className="block text-center px-4 py-3.5 mb-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-black hover:opacity-90 transition">
                🧭 Generate Startup Blueprint →
              </a>
              <div className="grid grid-cols-2 gap-3">
                <a href="/pm" className="block text-center px-4 py-3.5 bg-slate-100 text-slate-800 rounded-xl font-bold hover:bg-slate-200 transition">
                  PM Tool
                </a>
                <a href="/advisor" className="block text-center px-4 py-3.5 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 transition">
                  Startup Agents
                </a>
              </div>
            </div>
          </div>

          {/* Consulting Pro */}
          <div className="group relative bg-white rounded-3xl border-2 border-slate-200 hover:border-emerald-500 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden">
            <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-700 text-white p-8">
              <div className="text-5xl mb-4">🏛️</div>
              <h2 className="text-3xl font-black">Existing Business</h2>
              <p className="text-sm opacity-80 mt-2">Run, fix & scale an operating India MSME</p>
            </div>
            <div className="p-8">
              <p className="text-slate-600 mb-6">
                Describe your running business and get a Big 3 + Big 4 style assessment (1,003 scenarios,
                12 finance domains) — plus the operating AI agents (CFO, GST, operations, inventory,
                procurement, HR/payroll, risk & audit) for your sector, including import/export.
              </p>
              <div className="space-y-3 mb-8">
                <Feature icon="💰" text="O2C, P2P, R2R, FP&A, Tax, Treasury, Audit, Supply Chain" />
                <Feature icon="🧭" text="Operating AI agents: CFO, GST, COO, inventory, procurement, HR" />
                <Feature icon="🛡️" text="Risk, fraud & audit + India compliance (GST/EPF/ESI/customs)" />
                <Feature icon="📊" text="CMMI maturity assessment with gap analysis + ROI" />
                <Feature icon="📥" text="Consulting-grade PDF report, ready to deliver" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <a href="/consulting" className="block text-center px-4 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-black hover:opacity-90 transition">
                  Consulting Pro →
                </a>
                <a href="/advisor" className="block text-center px-4 py-4 bg-slate-900 text-white rounded-xl font-black hover:bg-slate-800 transition">
                  Business Agents →
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Stats bar */}
        <div className="bg-slate-900 rounded-2xl p-8 grid grid-cols-2 md:grid-cols-5 gap-6 text-center text-white mb-12">
          <Stat value="1,003" label="Live scenarios" />
          <Stat value="12" label="Finance domains" />
          <Stat value="500+" label="PM training examples" />
          <Stat value="97.8%" label="Classification accuracy" />
          <Stat value="0" label="LLM failures" />
        </div>

        {/* Domain grid */}
        <div className="mb-12">
          <h3 className="text-center text-sm font-bold text-slate-600 uppercase tracking-wider mb-6">
            Consulting Pro covers 12 finance & operations domains
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {[
              { icon: "💰", name: "O2C", full: "Order to Cash" },
              { icon: "🛒", name: "P2P", full: "Procure to Pay" },
              { icon: "📊", name: "R2R", full: "Record to Report" },
              { icon: "📒", name: "GL", full: "General Accounting" },
              { icon: "📈", name: "FP&A", full: "Planning & Analysis" },
              { icon: "⚖️", name: "Tax", full: "Tax & Compliance" },
              { icon: "🏦", name: "Treasury", full: "Cash & FX" },
              { icon: "🔍", name: "Audit", full: "Internal Audit & SOX" },
              { icon: "🚚", name: "Supply", full: "Supply Chain" },
              { icon: "👥", name: "HR", full: "HR & Payroll" },
              { icon: "🛡️", name: "Risk", full: "Risk, Fraud & Cyber" },
              { icon: "🖥️", name: "Digital", full: "Digital & GRC" },
            ].map(d => (
              <div key={d.name} className="bg-white rounded-xl border p-4 text-center hover:shadow-md transition">
                <div className="text-2xl">{d.icon}</div>
                <div className="font-black text-sm mt-1">{d.name}</div>
                <div className="text-[10px] text-slate-500">{d.full}</div>
              </div>
            ))}
          </div>
        </div>

        <footer className="text-center text-xs text-slate-400 pb-8">
          Template-driven intelligence · Zero LLM dependency · Sub-second response · Big 3 + Big 4 blended methodology
        </footer>
      </div>
    </div>
  );
}

function Feature({ icon, text }) {
  return (
    <div className="flex items-start gap-3">
      <span className="text-lg">{icon}</span>
      <span className="text-sm text-slate-700">{text}</span>
    </div>
  );
}

function Stat({ value, label }) {
  return (
    <div>
      <div className="text-3xl font-black">{value}</div>
      <div className="text-xs opacity-60 mt-1">{label}</div>
    </div>
  );
}
