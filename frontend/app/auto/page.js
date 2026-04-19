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
            PMGuru v12 · 1,003 Consulting Scenarios · 500 PM Training Examples
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

        {/* Two paths */}
        <div className="grid md:grid-cols-2 gap-6 mb-16">
          {/* PM Tool */}
          <div className="group relative bg-white rounded-3xl border-2 border-slate-200 hover:border-indigo-500 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden">
            <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-violet-700 text-white p-8">
              <div className="text-5xl mb-4">🚀</div>
              <h2 className="text-3xl font-black">Product & PM Tool</h2>
              <p className="text-sm opacity-80 mt-2">For founders, PMs, and product teams</p>
            </div>
            <div className="p-8">
              <p className="text-slate-600 mb-6">
                Enter your idea and get a complete consulting-grade due diligence report,
                a working PM workspace, and a full product lifecycle plan.
              </p>
              <div className="space-y-3 mb-8">
                <Feature icon="📑" text="Big 3-style due diligence report (11 sections, streaming)" />
                <Feature icon="🛠️" text="PM workspace with kanban, sprints, risks, team & timeline" />
                <Feature icon="🔄" text="8-phase product lifecycle with infographics" />
                <Feature icon="📊" text="Market sizing, competitive landscape, financial projections" />
                <Feature icon="⚙️" text="Technology stack & methodology recommendations" />
                <Feature icon="📥" text="Download everything as PDF" />
              </div>
              <a
                href="/pm"
                className="block w-full text-center px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-black text-lg hover:opacity-90 transition"
              >
                Launch PM Tool →
              </a>
            </div>
          </div>

          {/* Consulting Pro */}
          <div className="group relative bg-white rounded-3xl border-2 border-slate-200 hover:border-emerald-500 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden">
            <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-700 text-white p-8">
              <div className="text-5xl mb-4">🏛️</div>
              <h2 className="text-3xl font-black">Consulting Pro</h2>
              <p className="text-sm opacity-80 mt-2">For consultants, auditors, and advisory teams</p>
            </div>
            <div className="p-8">
              <p className="text-slate-600 mb-6">
                Describe any business and get a Big 3 + Big 4 style assessment report
                powered by 1,003 real-world scenarios across 12 finance domains.
              </p>
              <div className="space-y-3 mb-8">
                <Feature icon="💰" text="O2C, P2P, R2R, General Accounting — deep coverage" />
                <Feature icon="📈" text="FP&A, Tax, Treasury, Internal Audit, Supply Chain" />
                <Feature icon="🛡️" text="Risk, Fraud, Cyber, HR, Digital Transformation" />
                <Feature icon="📊" text="CMMI maturity assessment with gap analysis" />
                <Feature icon="🎯" text="Prioritized recommendations with ROI analysis" />
                <Feature icon="📥" text="Consulting-grade PDF report, ready to deliver" />
              </div>
              <a
                href="/consulting"
                className="block w-full text-center px-6 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-black text-lg hover:opacity-90 transition"
              >
                Launch Consulting Pro →
              </a>
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
