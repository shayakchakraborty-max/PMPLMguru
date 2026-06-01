"use client";

/* PMGuru landing — exactly two platforms:
   1. New Business / Startup  -> Business Studio (/studio): detailed Big-3 DD report
   2. Existing Business        -> Advisor (/advisor): consultant agents across all domains */

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white text-slate-900">
      <nav className="sticky top-0 z-30 bg-white/80 backdrop-blur border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <span className="font-black tracking-tight">PMGuru</span>
          <div className="flex items-center gap-1 text-sm">
            <a href="/studio" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-semibold">New</a>
            <a href="/advisor" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-semibold">Existing</a>
            <a href="/playbooks" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-semibold">Playbooks</a>
            <a href="/simulate" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-semibold">Simulate</a>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <header className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-indigo-100 text-indigo-700 px-4 py-1.5 rounded-full text-xs font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            AI consulting & operating system for Indian MSMEs · 20 research-grade agents · ₹ & $
          </div>
          <h1 className="text-4xl sm:text-6xl font-black tracking-tight leading-tight">
            Two platforms.<br className="hidden sm:block" />
            <span className="bg-gradient-to-r from-indigo-600 to-emerald-500 bg-clip-text text-transparent"> One AI consultant for your business.</span>
          </h1>
          <p className="text-base sm:text-xl text-slate-600 mt-5 max-w-2xl mx-auto">
            Starting something new, or running an existing business — pick your platform and get
            India-aware, research-grade help across every domain.
          </p>
        </header>

        <div className="grid md:grid-cols-2 gap-6">
          {/* NEW */}
          <a href="/studio" className="group bg-white rounded-3xl border-2 border-slate-200 hover:border-indigo-500 shadow-sm hover:shadow-2xl transition overflow-hidden flex flex-col">
            <div className="bg-gradient-to-br from-indigo-600 via-violet-600 to-indigo-800 text-white p-8">
              <div className="text-5xl mb-4">🚀</div>
              <h2 className="text-3xl font-black">New Business / Startup</h2>
              <p className="text-sm opacity-85 mt-2">Idea → fundable plan (bootstrap or raise)</p>
            </div>
            <div className="p-8 flex-1 flex flex-col">
              <ul className="space-y-3 mb-7">
                <Feature icon="📑" text="Detailed Big-3-style due-diligence report with infographics" />
                <Feature icon="📈" text="Market study — TAM / SAM / SOM, competition, GTM" />
                <Feature icon="💰" text="Financials in ₹ & $, funding & government incentives" />
                <Feature icon="🔄" text="Product lifecycle + recommended PM method + tech stack" />
                <Feature icon="🗂️" text="Preloaded PM workspace + 20 AI startup consultants · PDF" />
              </ul>
              <span className="mt-auto block text-center px-6 py-4 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl font-black text-lg group-hover:opacity-90 transition">
                Start a new business →
              </span>
            </div>
          </a>

          {/* EXISTING */}
          <a href="/advisor" className="group bg-white rounded-3xl border-2 border-slate-200 hover:border-emerald-500 shadow-sm hover:shadow-2xl transition overflow-hidden flex flex-col">
            <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-700 text-white p-8">
              <div className="text-5xl mb-4">🏢</div>
              <h2 className="text-3xl font-black">Existing Business</h2>
              <p className="text-sm opacity-85 mt-2">Diagnose, fix & scale — all sectors & domains</p>
            </div>
            <div className="p-8 flex-1 flex flex-col">
              <ul className="space-y-3 mb-7">
                <Feature icon="🤖" text="20 AI consultants: CFO, GST, ops, inventory, procurement, HR, risk" />
                <Feature icon="🌐" text="Every sector incl. import/export — pick your business type" />
                <Feature icon="🔍" text="Due diligence, audit-ready reports with citations & KPIs" />
                <Feature icon="⚖️" text="India compliance — GST, EPF/ESI, customs, ROC" />
                <Feature icon="🗂️" text="ERP-style workspace + Big 3/4 consulting assessment" />
              </ul>
              <span className="mt-auto block text-center px-6 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-black text-lg group-hover:opacity-90 transition">
                Open my business advisor →
              </span>
            </div>
          </a>
        </div>

        {/* Industry Playbooks banner */}
        <a href="/playbooks" className="group block mt-6 rounded-3xl border-2 border-slate-200 hover:border-indigo-500 bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-6 sm:p-8 shadow-sm hover:shadow-2xl transition">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wide">Consulting Command Center</div>
              <div className="text-xl sm:text-2xl font-black mt-1">30 Industry Playbooks</div>
              <p className="text-slate-300 text-sm mt-1 max-w-2xl">
                Research-grade 13-part operating blueprints for every priority Indian-MSME sector — operating model,
                value chain, bottlenecks, AI-automation map, KPI tree, ₹ profitability, growth & digital-maturity ladder.
              </p>
            </div>
            <span className="shrink-0 px-6 py-3 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl font-black group-hover:opacity-90 transition">
              Browse playbooks →
            </span>
          </div>
        </a>

        {/* accurate stats */}
        <div className="bg-slate-900 rounded-2xl p-6 sm:p-8 grid grid-cols-2 md:grid-cols-4 gap-6 text-center text-white mt-10">
          <Stat value="20" label="Research-grade AI agents" />
          <Stat value="17" label="Sectors incl. import/export" />
          <Stat value="₹ & $" label="India-aware (GST · DPIIT · Udyam)" />
          <Stat value="1,000+" label="Consulting scenarios" />
        </div>

        <footer className="text-center text-xs text-slate-400 pt-10">
          India-aware · citation-backed · sub-second · no LLM dependency
        </footer>
      </div>
    </div>
  );
}

function Feature({ icon, text }) {
  return (
    <li className="flex items-start gap-3">
      <span className="text-lg">{icon}</span>
      <span className="text-sm text-slate-700">{text}</span>
    </li>
  );
}

function Stat({ value, label }) {
  return (
    <div>
      <div className="text-2xl sm:text-3xl font-black">{value}</div>
      <div className="text-xs opacity-60 mt-1">{label}</div>
    </div>
  );
}
