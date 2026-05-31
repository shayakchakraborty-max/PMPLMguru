"use client";

/* PMGuru landing — clear two-door entry: Startup vs Existing Business.
   One primary action per door; everything else discoverable via the tools row. */

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white text-slate-900">
      {/* Top nav */}
      <nav className="sticky top-0 z-30 bg-white/80 backdrop-blur border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <span className="font-black tracking-tight">PMGuru</span>
          <div className="flex items-center gap-1 text-sm">
            <NavLink href="/studio">Studio</NavLink>
            <NavLink href="/advisor">AI Agents</NavLink>
            <NavLink href="/erp">Workspace</NavLink>
            <NavLink href="/consulting">Consulting</NavLink>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        {/* Hero */}
        <header className="text-center mb-10 sm:mb-14">
          <div className="inline-flex items-center gap-2 bg-indigo-100 text-indigo-700 px-4 py-1.5 rounded-full text-xs font-bold mb-5">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            AI consulting & operating system for Indian MSMEs · 20 AI agents · ₹ India-aware
          </div>
          <h1 className="text-4xl sm:text-6xl font-black tracking-tight leading-tight">
            From idea to running business,<br className="hidden sm:block" />
            <span className="bg-gradient-to-r from-indigo-600 to-emerald-500 bg-clip-text text-transparent"> one AI platform</span>
          </h1>
          <p className="text-base sm:text-xl text-slate-600 mt-5 max-w-2xl mx-auto">
            Pick where you are. We'll generate India-specific plans, reports and an AI advisory team —
            with rupees, GST/Udyam/DPIIT compliance, funding incentives and how to scale.
          </p>
        </header>

        {/* Primary: Business Studio — one idea -> full plan */}
        <a href="/studio"
          className="group block rounded-3xl overflow-hidden mb-10 bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 text-white p-7 sm:p-9 hover:shadow-2xl transition">
          <div className="flex flex-col md:flex-row md:items-center gap-6">
            <div className="text-5xl">✨</div>
            <div className="flex-1">
              <div className="inline-flex items-center gap-2 bg-white/15 px-3 py-1 rounded-full text-[11px] font-bold mb-2">START HERE · one idea → a complete plan</div>
              <h2 className="text-2xl sm:text-3xl font-black">Business Studio</h2>
              <p className="text-sm sm:text-base text-white/85 mt-2 max-w-2xl">
                Type your idea once. Get a research-grade report — deep due diligence, market study (TAM/SAM/SOM),
                product lifecycle, the right PM method, tech stack, ₹ financials, GTM & roadmap — then open your
                preloaded PM workspace. Downloadable as PDF.
              </p>
            </div>
            <span className="shrink-0 px-6 py-4 bg-white text-slate-900 rounded-xl font-black group-hover:bg-emerald-300 transition">
              Open Studio →
            </span>
          </div>
        </a>

        {/* Or go straight to a specialised path */}
        <p className="text-center text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">…or jump to a focused path</p>

        {/* Two doors */}
        <div className="grid md:grid-cols-2 gap-5 mb-10">
          {/* Startup */}
          <div className="bg-white rounded-3xl border-2 border-slate-200 hover:border-indigo-400 shadow-sm hover:shadow-xl transition overflow-hidden flex flex-col">
            <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-violet-700 text-white p-7">
              <div className="text-4xl mb-3">🚀</div>
              <h2 className="text-2xl font-black">Starting a new business</h2>
              <p className="text-sm opacity-80 mt-1">Validate, plan and launch — then scale</p>
            </div>
            <div className="p-7 flex-1 flex flex-col">
              <ul className="space-y-2.5 mb-6">
                <Feature icon="🧭" text="One-click Startup Blueprint — market, model, ₹ financials, compliance, funding & 90-day plan" />
                <Feature icon="🤖" text="Startup AI agents: market sizing, competitor intel, due diligence, investor readiness" />
                <Feature icon="🗂️" text="ERP-style workspace + a Big-3-style due-diligence report" />
              </ul>
              <div className="mt-auto space-y-2">
                <a href="/blueprint" className="block text-center px-5 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-black text-lg hover:opacity-90 transition">
                  Generate my Startup Blueprint →
                </a>
                <div className="flex justify-center gap-4 text-sm text-slate-500">
                  <a href="/advisor" className="hover:text-indigo-600 font-semibold">AI agents</a>
                  <span className="text-slate-300">·</span>
                  <a href="/pm" className="hover:text-indigo-600 font-semibold">PM tools & report</a>
                  <span className="text-slate-300">·</span>
                  <a href="/erp" className="hover:text-indigo-600 font-semibold">Workspace</a>
                </div>
              </div>
            </div>
          </div>

          {/* Existing */}
          <div className="bg-white rounded-3xl border-2 border-slate-200 hover:border-emerald-400 shadow-sm hover:shadow-xl transition overflow-hidden flex flex-col">
            <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-700 text-white p-7">
              <div className="text-4xl mb-3">🏢</div>
              <h2 className="text-2xl font-black">Running an existing business</h2>
              <p className="text-sm opacity-80 mt-1">Diagnose, fix and scale operations</p>
            </div>
            <div className="p-7 flex-1 flex flex-col">
              <ul className="space-y-2.5 mb-6">
                <Feature icon="📋" text="Big 3 + Big 4 style assessment across 12 finance & ops domains" />
                <Feature icon="🤖" text="Operating AI agents: CFO, GST, operations, inventory, procurement, HR, risk & audit" />
                <Feature icon="🌐" text="All sectors incl. import/export — India compliance (GST/EPF/ESI/customs)" />
              </ul>
              <div className="mt-auto space-y-2">
                <a href="/advisor" className="block text-center px-5 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-black text-lg hover:opacity-90 transition">
                  Open my Business Advisor →
                </a>
                <div className="flex justify-center gap-4 text-sm text-slate-500">
                  <a href="/consulting" className="hover:text-emerald-600 font-semibold">Assessment report</a>
                  <span className="text-slate-300">·</span>
                  <a href="/erp" className="hover:text-emerald-600 font-semibold">ERP workspace</a>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* All tools — discoverable, no clutter */}
        <div className="mb-10">
          <p className="text-center text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">All tools</p>
          <div className="flex flex-wrap justify-center gap-2">
            <Tool href="/studio" icon="✨" label="Business Studio" />
            <Tool href="/blueprint" icon="🧭" label="Startup Blueprint" />
            <Tool href="/advisor" icon="🤖" label="AI Agents (20)" />
            <Tool href="/erp" icon="🗂️" label="ERP Workspace" />
            <Tool href="/pm" icon="🛠️" label="PM Tool" />
            <Tool href="/consulting" icon="📋" label="Consulting Pro" />
          </div>
        </div>

        {/* Stats (accurate) */}
        <div className="bg-slate-900 rounded-2xl p-6 sm:p-8 grid grid-cols-2 md:grid-cols-4 gap-6 text-center text-white">
          <Stat value="20" label="Research-grade AI agents" />
          <Stat value="17" label="MSME sectors incl. import/export" />
          <Stat value="₹" label="India-aware (GST · DPIIT · Udyam)" />
          <Stat value="1,000+" label="Consulting scenarios" />
        </div>

        <footer className="text-center text-xs text-slate-400 pt-10 pb-6">
          India-aware · citation-backed · template-driven (sub-second, no LLM dependency)
        </footer>
      </div>
    </div>
  );
}

function NavLink({ href, children }) {
  return <a href={href} className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-semibold">{children}</a>;
}

function Tool({ href, icon, label }) {
  return (
    <a href={href} className="inline-flex items-center gap-2 bg-white border border-slate-200 hover:border-indigo-300 hover:shadow-sm rounded-full px-4 py-2 text-sm font-bold text-slate-700 transition">
      <span>{icon}</span>{label}
    </a>
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
      <div className="text-3xl font-black">{value}</div>
      <div className="text-xs opacity-60 mt-1">{label}</div>
    </div>
  );
}
