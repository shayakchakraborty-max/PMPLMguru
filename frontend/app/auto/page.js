"use client";

/* Indian MSME Consulting · Powered by AI — the front door, framed as a
   Digital Consulting Firm (Executive Leadership + 8 Practice Areas +
   consulting deliverables + industry clouds). Consulting-first MVP:
   ERP / operational tooling is intentionally NOT surfaced here. */

const LEADERSHIP = [
  { icon: "🧭", title: "Managing Partner", role: "Runs your engagement end-to-end — scopes the work, assembles the right practices, and signs off the board pack." },
  { icon: "♟️", title: "Chief Strategy Officer", role: "Business model, market attractiveness, positioning and the growth thesis." },
  { icon: "🔄", title: "Chief Transformation Officer", role: "Turns findings into a 12-month roadmap and a 30/60/90-day execution plan." },
  { icon: "🛡️", title: "Chief Risk Officer", role: "Enterprise risk register, compliance exposure and resilience." },
  { icon: "📈", title: "Chief Growth Officer", role: "Sales, channels, customer acquisition and market expansion." },
  { icon: "💰", title: "Chief Financial Advisor", role: "Cash flow, working capital, profitability and funding readiness." },
];

const PRACTICES = [
  { icon: "♟️", name: "Strategy & Growth", grad: "from-indigo-500 to-violet-600", agent: "ceo_copilot",
    services: ["Business model review", "Growth & expansion strategy", "Pricing & portfolio", "Competitive positioning"],
    frameworks: ["SWOT", "PESTLE", "Porter's 5 Forces", "Business Model Canvas"] },
  { icon: "💰", name: "Finance & Working Capital", grad: "from-emerald-500 to-teal-600", agent: "cfo_finance",
    services: ["Cash flow & profitability", "Working capital optimization", "Cost reduction", "Loan / investor readiness"],
    frameworks: ["Financial health score", "Cash-flow roadmap", "Unit economics"] },
  { icon: "⚙️", name: "Operations Excellence", grad: "from-amber-500 to-orange-600", agent: "coo_operations",
    services: ["Process & bottleneck analysis", "Productivity improvement", "Supply chain & procurement", "Operational KPIs"],
    frameworks: ["Process maps", "Capacity planning", "OEE / cycle-time"] },
  { icon: "📣", name: "Sales & Marketing", grad: "from-pink-500 to-rose-600", agent: "sales_gtm",
    services: ["Lead gen & channel strategy", "Distributor strategy", "Retention & territory planning", "Digital marketing"],
    frameworks: ["Sales growth roadmap", "GTM plan", "Funnel design"] },
  { icon: "⚖️", name: "Compliance & Regulatory", grad: "from-sky-500 to-blue-600", agent: "gst_compliance",
    services: ["Udyam / GST / IEC / FSSAI", "Labour & factory compliance", "State registrations", "Gap analysis"],
    frameworks: ["Compliance health score", "Compliance calendar", "Gap roadmap"] },
  { icon: "🌏", name: "Export & International Trade", grad: "from-cyan-500 to-teal-600", agent: "export_compliance",
    services: ["Export readiness", "Country & buyer selection", "Trade documentation", "RoDTEP guidance"],
    frameworks: ["Export readiness score", "Export roadmap", "Target-country shortlist"] },
  { icon: "🛡️", name: "Risk & Resilience", grad: "from-red-500 to-rose-700", agent: "risk_audit",
    services: ["Business & financial risk", "Operational & compliance risk", "Concentration risk", "Mitigation planning"],
    frameworks: ["Enterprise risk register", "RAID log", "Mitigation roadmap"] },
  { icon: "🤖", name: "Digital Transformation", grad: "from-violet-500 to-fuchsia-600", agent: "erp_consultant",
    services: ["Technology maturity", "AI adoption assessment", "Automation opportunities", "Digital roadmap"],
    frameworks: ["Digital maturity score", "AI adoption roadmap", "Automation map"] },
];

const DELIVERABLES = [
  "Business Health Report", "Due Diligence Report", "Growth Strategy Report",
  "Cost Optimization Report", "Working Capital Report", "Compliance Report",
  "Risk Assessment Report", "Export Readiness Report", "Transformation Roadmap",
  "30 / 60 / 90-Day Plan", "KPI Dashboard", "Board Review Pack", "Investor Readiness Pack",
];

const INDUSTRIES = [
  ["🛒", "Retail / Kirana"], ["📦", "Wholesale"], ["🚚", "Distribution"], ["🏭", "Manufacturing"],
  ["🍲", "Food Processing"], ["🌾", "Agro Business"], ["💊", "Pharma"], ["🧵", "Textile"],
  ["🛠️", "Services"], ["📦", "Logistics"], ["🌏", "Export Businesses"],
];

const FLOW = [
  ["🔍", "Diagnose", "9-dimension business health score"],
  ["📑", "Due Diligence", "Consulting-grade DD report"],
  ["🗺️", "Strategy & Roadmap", "SWOT + 12-month plan"],
  ["✅", "Execute", "AI PMO: OKRs, sprints, tasks"],
  ["📡", "Monitor", "Proactive ongoing recommendations"],
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-slate-900">
      {/* Nav */}
      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <span className="font-black tracking-tight text-sm sm:text-base">
            Indian MSME Consulting <span className="text-indigo-600">· Powered by AI</span>
          </span>
          <div className="hidden sm:flex items-center gap-1 text-sm">
            <a href="/ceo" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-semibold">CEO Office</a>
            <a href="#practices" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-semibold">Practices</a>
            <a href="/advisor" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-semibold">Advisors</a>
            <a href="#industries" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-semibold">Industries</a>
            <a href="/playbooks" className="px-3 py-1.5 rounded-lg bg-slate-900 text-white hover:bg-slate-800 font-semibold">Start engagement</a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <header className="relative overflow-hidden bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-24 text-center relative">
          <div className="inline-flex items-center gap-2 bg-white/10 px-4 py-1.5 rounded-full text-[11px] sm:text-xs font-bold mb-6">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            AI-Native Consulting OS for Indian MSMEs · 24×7 · ₹ & India-aware
          </div>
          <h1 className="text-4xl sm:text-6xl font-black tracking-tight leading-[1.05]">
            A full consulting firm<br className="hidden sm:block" /> for your business.{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-emerald-400 bg-clip-text text-transparent">In software.</span>
          </h1>
          <p className="text-base sm:text-xl text-slate-300 mt-6 max-w-3xl mx-auto">
            McKinsey · Deloitte · PwC · EY · KPMG-grade consulting, plus your CA, CS and industry
            experts — working together, 24×7, for every Indian MSME. Not an ERP. Not accounting.
            A consulting firm that lives in your pocket.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center mt-9">
            <a href="/ceo" className="px-7 py-4 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl font-black text-lg hover:opacity-90 transition shadow-lg shadow-indigo-900/40">
              Open my CEO Office →
            </a>
            <a href="/playbooks" className="px-7 py-4 bg-white/10 border border-white/20 rounded-xl font-bold text-lg hover:bg-white/20 transition">
              Start a full engagement
            </a>
          </div>
          <p className="text-xs text-slate-400 mt-6">
            Research-grade · citation-backed · India-aware (GST · Udyam · DPIIT · ₹) · sub-second
          </p>
        </div>
      </header>

      {/* Engagement flow */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 -mt-8 sm:-mt-10 relative z-10">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xl p-5 sm:p-7">
          <div className="text-center text-xs font-bold uppercase tracking-wide text-slate-400 mb-5">How an engagement works</div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {FLOW.map(([icon, title, sub], i) => (
              <div key={title} className="text-center relative">
                <div className="text-3xl mb-2">{icon}</div>
                <div className="font-black text-sm">{i + 1}. {title}</div>
                <div className="text-[11px] text-slate-500 mt-1 leading-snug">{sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Executive Leadership */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
        <SectionHead kicker="Your engagement team" title="Executive leadership layer"
          sub="Senior AI partners coordinate every engagement — exactly like a real consulting firm." />
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-9">
          {LEADERSHIP.map((l) => (
            <div key={l.title} className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg hover:border-indigo-300 transition">
              <div className="text-3xl mb-3">{l.icon}</div>
              <div className="font-black">{l.title}</div>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">{l.role}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Practice Areas */}
      <section id="practices" className="bg-slate-50 border-y border-slate-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
          <SectionHead kicker="8 consulting practices" title="Practice areas"
            sub="Every practice is a team of research-grade AI consultants. Tap one to start." />
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-9">
            {PRACTICES.map((p) => (
              <a key={p.name} href={`/advisor?agent=${p.agent}`}
                className="group bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-xl hover:-translate-y-0.5 transition flex flex-col">
                <div className={`h-1.5 bg-gradient-to-r ${p.grad}`} />
                <div className="p-5 flex-1 flex flex-col">
                  <div className="text-2xl mb-2">{p.icon}</div>
                  <div className="font-black text-[15px] leading-tight">{p.name}</div>
                  <ul className="mt-3 space-y-1.5 flex-1">
                    {p.services.map((s) => (
                      <li key={s} className="text-[12px] text-slate-600 flex gap-1.5">
                        <span className="text-emerald-500">✓</span><span>{s}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="flex flex-wrap gap-1 mt-3">
                    {p.frameworks.map((f) => (
                      <span key={f} className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-medium">{f}</span>
                    ))}
                  </div>
                  <span className="mt-4 text-[13px] font-bold text-indigo-600 group-hover:translate-x-0.5 transition">Open practice →</span>
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Deliverables */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
        <SectionHead kicker="What you get" title="Consulting deliverables, generated by AI"
          sub="Board-ready outputs — the same artefacts a top firm would hand you, in minutes not months." />
        <div className="flex flex-wrap gap-2.5 justify-center mt-9">
          {DELIVERABLES.map((d) => (
            <span key={d} className="bg-white border border-slate-200 rounded-full px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm">
              📄 {d}
            </span>
          ))}
        </div>
      </section>

      {/* Industry clouds */}
      <section id="industries" className="bg-slate-950 text-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
          <div className="text-center">
            <div className="text-xs font-bold uppercase tracking-wide text-indigo-300">Industry consulting clouds</div>
            <h2 className="text-2xl sm:text-4xl font-black mt-2">Sector intelligence built in</h2>
            <p className="text-slate-400 mt-3 max-w-2xl mx-auto">Each industry ships with its own KPIs, benchmarks, common risks, growth opportunities and consulting playbooks.</p>
          </div>
          <div className="flex flex-wrap gap-2.5 justify-center mt-9">
            {INDUSTRIES.map(([icon, name]) => (
              <a key={name} href="/playbooks" className="bg-white/10 hover:bg-white/20 border border-white/15 rounded-full px-4 py-2 text-sm font-semibold transition">
                {icon} {name}
              </a>
            ))}
          </div>
          <div className="text-center mt-10">
            <a href="/playbooks" className="inline-block px-7 py-4 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl font-black text-lg hover:opacity-90 transition">
              Explore the 30-sector playbook library →
            </a>
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-20 text-center">
        <h2 className="text-3xl sm:text-5xl font-black tracking-tight">World-class consulting,<br className="hidden sm:block" /> for every Indian MSME.</h2>
        <p className="text-slate-600 mt-5 max-w-2xl mx-auto text-lg">Start a free engagement now — get your business health score, due-diligence report and execution roadmap in minutes.</p>
        <a href="/playbooks" className="inline-block mt-8 px-8 py-4 bg-slate-900 text-white rounded-xl font-black text-lg hover:bg-slate-800 transition">
          Start a consulting engagement →
        </a>
      </section>

      <footer className="border-t border-slate-200 text-center text-xs text-slate-400 py-10 px-4">
        Indian MSME Consulting · Powered by AI · research-grade · citation-backed · India-aware ·
        figures are planning estimates — verify statutory & financial items with a CA / CS before acting.
      </footer>
    </div>
  );
}

function SectionHead({ kicker, title, sub }) {
  return (
    <div className="text-center">
      <div className="text-xs font-bold uppercase tracking-wide text-indigo-600">{kicker}</div>
      <h2 className="text-2xl sm:text-4xl font-black tracking-tight mt-2 text-slate-900">{title}</h2>
      {sub && <p className="text-slate-600 mt-3 max-w-2xl mx-auto">{sub}</p>}
    </div>
  );
}
