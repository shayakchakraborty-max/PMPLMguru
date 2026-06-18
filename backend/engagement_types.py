"""
engagement_types.py — the standardized engagement TYPES a Big-3/Big-4 firm actually
sells, mapped to the consulting taxonomy and staffed end-to-end with AI agents.

A firm doesn't start from "describe a problem" — it sells a *named engagement*:
Finance Transformation, Order-to-Cash, Working Capital, Supply Chain, etc. Each type
here defines its end-to-end scope: the AI agent team (so the right specialists are
always on the case), the standard deliverables, the KPIs / value levers, and a sample
scope. The orchestrator uses the type's team to guarantee end-to-end coverage, then
engagement_360 staffs the human hierarchy + workplan + billing on top.

Deterministic, no deps. Endpoints (main.py): GET /engagement-types, /engagement-types/meta,
/engagement-types/tests. Each `agents` list references live msme_agents keys.
"""

try:
    import msme_agents as _M
except Exception:
    _M = None


def _t(key, name, tower, icon, objective, weeks, agents, deliverables, kpis, value_levers, sample):
    return {"key": key, "name": name, "tower": tower, "icon": icon, "objective": objective,
            "duration_weeks": weeks, "agents": agents, "deliverables": deliverables,
            "kpis": kpis, "value_levers": value_levers, "sample": sample}


# The high-demand engagement types (the way firms package & sell work).
TYPES = [
    _t("strategy_growth", "Strategy & Growth", "strategy_corporate", "🎯",
       "Set the growth thesis, where-to-play / how-to-win and the operating model to get there.", 8,
       ["ceo_copilot", "market_research", "competitor_intel", "sales_gtm", "product_manager"],
       ["Growth strategy & where-to-play", "Market sizing (TAM/SAM/SOM)", "Operating-model blueprint", "Value-creation plan", "Board deck"],
       ["Revenue growth %", "Market share", "EBITDA margin", "New-revenue mix"],
       ["New markets/segments", "Pricing & mix", "Channel expansion", "Portfolio focus"],
       "Set a 3-year growth strategy and market-entry plan with a quantified value-creation roadmap."),
    _t("finance_transformation", "Finance Transformation", "finance_transformation", "💰",
       "Modernise the finance function: FP&A, close, controls, cost and the operating model.", 12,
       ["cfo_finance", "fpa", "r2r_expert", "treasury", "o2c_expert"],
       ["Finance diagnostic & target operating model", "FP&A & MIS redesign", "Close & controls uplift", "Cost-out plan"],
       ["Days to close", "Forecast accuracy", "Cost-to-serve", "Finance FTE productivity"],
       ["Faster close", "Better forecasting", "Cost reduction", "Shared services / GBS"],
       "Stand up FP&A, a 5-day close and a finance operating model with a cost-out plan."),
    _t("working_capital", "Working Capital Optimization", "finance_transformation", "💧",
       "Release trapped cash end-to-end across the cash-conversion cycle (AR + AP + inventory).", 8,
       ["cfo_finance", "collections", "credit_management", "procurement_agent", "inventory_agent", "treasury"],
       ["Cash-conversion-cycle diagnostic", "Receivables & collections plan", "Payables & terms strategy", "Inventory optimisation", "Cash-release roadmap"],
       ["DSO", "DPO", "DIO", "Cash conversion cycle", "Cash released (₹)"],
       ["Collect faster (DSO)", "Pay smarter (DPO)", "Cut dead stock (DIO)", "Unlock blocked cash"],
       "Release cash end-to-end: cut DSO and dead stock, optimise payment terms, shorten the cash-conversion cycle."),
    _t("o2c_transformation", "Order-to-Cash (O2C) Transformation", "o2c", "🧾",
       "End-to-end O2C: credit, order, billing/e-invoicing, collections, cash application, deductions.", 10,
       ["o2c_expert", "credit_management", "collections", "cash_application", "deductions"],
       ["O2C value-stream diagnostic", "Credit & collections playbook", "Cash-application & deductions redesign", "DSO-improvement plan"],
       ["DSO", "Collection effectiveness", "Unapplied cash", "Revenue leakage %"],
       ["Collections cadence", "Auto cash application", "Deduction recovery", "Clean e-invoicing"],
       "Fix a stretched O2C: 68-day DSO, unapplied cash and deductions eroding realised revenue."),
    _t("p2p_transformation", "Procure-to-Pay (P2P) Transformation", "p2p", "🛒",
       "End-to-end P2P: sourcing, supplier management, purchasing, AP, 3-way match, payments.", 10,
       ["procurement_agent", "cfo_finance"],
       ["P2P value-stream diagnostic", "Sourcing & supplier strategy", "3-way-match & AP controls", "Spend-analytics & savings plan"],
       ["Spend under management", "Maverick spend %", "Invoice cycle time", "Savings realised"],
       ["Strategic sourcing", "3-way match", "Supplier consolidation", "Terms optimisation"],
       "Plug procurement leakage: no 3-way match, maverick spend and delayed supplier payments."),
    _t("r2r_transformation", "Record-to-Report (R2R) Transformation", "r2r", "📒",
       "End-to-end R2R: GL, reconciliations, fixed assets, close, consolidation, MIS reporting.", 10,
       ["r2r_expert", "cfo_finance"],
       ["R2R maturity diagnostic", "Close calendar & checklist", "Reconciliation framework", "MIS & board-reporting pack"],
       ["Days to close", "Reconciliations complete %", "Audit adjustments", "MIS turnaround"],
       ["Faster close", "Clean reconciliations", "Auto MIS", "Stronger controls"],
       "Cut an 18-day close with unreconciled ledgers and no monthly MIS to a reliable 5-day close."),
    _t("cost_optimization", "Cost Optimization", "finance_transformation", "✂️",
       "Structural cost-out across spend, operations and overheads, protecting growth.", 8,
       ["cfo_finance", "procurement_agent", "coo_operations"],
       ["Spend & cost baseline", "Cost-reduction initiatives (ZBB)", "Operations efficiency plan", "Savings tracker"],
       ["Cost-to-serve", "SG&A %", "Savings realised", "Gross margin"],
       ["Zero-based budgeting", "Procurement savings", "Process efficiency", "Footprint rationalisation"],
       "Deliver a structural cost-out programme with a zero-based budget and a savings tracker."),
    _t("supply_chain", "Supply Chain Transformation", "supply_chain", "🔗",
       "End-to-end supply chain: demand planning, inventory, warehousing, logistics, S&OP.", 10,
       ["inventory_agent", "procurement_agent", "coo_operations"],
       ["Supply-chain diagnostic", "Demand planning & S&OP", "Inventory optimisation", "Logistics & network plan"],
       ["Fill rate / OTIF", "Inventory turns", "Forecast accuracy", "Logistics cost %"],
       ["Demand planning", "Safety-stock optimisation", "Network design", "S&OP cadence"],
       "Lift OTIF and inventory turns end-to-end with demand planning, S&OP and network optimisation."),
    _t("tax_compliance", "Tax & Compliance", "tax_compliance", "🧮",
       "Direct & indirect tax, regulatory and secretarial compliance, end-to-end.", 6,
       ["gst_compliance", "legal_contracts", "export_compliance"],
       ["Compliance health-check", "GST/TDS/ROC calendar", "Tax-position review", "Remediation plan"],
       ["Compliance score", "Notices / penalties", "ITC leakage", "Filing timeliness"],
       ["Clean GST/ITC", "Statutory calendar", "Tax optimisation", "Secretarial hygiene"],
       "Close compliance gaps across GST, income tax, ROC and sector licences with a remediation plan."),
    _t("risk_internal_audit", "Risk & Internal Audit", "risk_advisory", "⚠️",
       "Enterprise risk, internal controls, internal audit, fraud and cyber risk.", 8,
       ["risk_audit", "cyber_dpdp"],
       ["Risk register (RAID)", "Controls & SoD assessment", "Internal-audit plan", "Cyber & DPDP posture"],
       ["Open high risks", "Control coverage %", "Audit findings closed", "DPDP readiness"],
       ["Segregation of duties", "3-way controls", "Fraud detection", "Cyber hardening"],
       "Stand up a risk register, fix segregation-of-duties gaps and a DPDP/cyber posture."),
    _t("technology_erp", "Technology & ERP Transformation", "technology", "🖥️",
       "ERP modernisation, cloud, data & analytics, AI strategy and automation.", 12,
       ["erp_consultant", "cyber_dpdp"],
       ["Tech & data diagnostic", "ERP selection & roadmap", "Data/BI plan", "AI & automation roadmap"],
       ["Process automation %", "Data quality", "System uptime", "IT cost %"],
       ["ERP modernisation", "Automation/RPA", "Data platform", "AI use-cases"],
       "Move off spreadsheets to an ERP with BOM/inventory/GST and management dashboards."),
    _t("human_capital", "Human Capital & Org", "human_capital", "👥",
       "Org design, target operating model, workforce, performance and change.", 8,
       ["org_change", "hr_payroll"],
       ["Operating-model & org design", "RACI & role charters", "OKR/performance framework", "Change plan"],
       ["Span of control", "Goal attainment", "Attrition", "Role clarity"],
       ["Operating model", "Accountability (RACI)", "OKRs", "Capability building"],
       "Scale past the founder: operating model, clear roles, OKR cadence and a change plan."),
    _t("mna_dd", "M&A and Due Diligence", "strategy_corporate", "🤝",
       "Commercial / financial / operational due diligence, valuation and 100-day plan.", 6,
       ["msme_due_diligence", "investor_readiness", "cfo_finance"],
       ["Due-diligence report (red flags)", "Valuation view", "Synergy/value-creation plan", "100-day integration plan"],
       ["Deal readiness score", "EBITDA quality", "Synergy value", "Integration milestones"],
       ["Risk discovery", "Value creation", "Synergy capture", "Integration"],
       "Run buy-side due diligence with red flags, valuation view and a 100-day integration plan."),
    _t("customer_experience", "Customer Experience & Growth", "marketing", "📣",
       "CX, marketing, demand generation and revenue growth, end-to-end.", 8,
       ["marketing_agent", "customer_support", "sales_gtm"],
       ["CX & funnel diagnostic", "Channel-mix & CAC/LTV plan", "Retention & loyalty plan", "GTM playbook"],
       ["CAC", "LTV:CAC", "Repeat rate", "Conversion %"],
       ["Profitable acquisition", "Retention/loyalty", "Channel mix", "Pricing"],
       "Fix CAC > LTV: profitable channel mix, retention and a GTM playbook."),
    _t("esg_sustainability", "ESG & Sustainability", "esg_sustainability", "🌱",
       "ESG diagnostic, decarbonisation, energy/EPR and export-carbon (CBAM/BRSR) readiness.", 8,
       ["sustainability_esg", "coo_operations"],
       ["ESG baseline & materiality", "Decarbonisation roadmap", "Energy/EPR plan", "CBAM/BRSR readiness"],
       ["Energy intensity", "Emissions intensity", "Waste recycled %", "ZED level"],
       ["Energy efficiency", "Decarbonisation", "EPR compliance", "Market access (CBAM)"],
       "Prepare for EU CBAM and buyer-ESG: baseline emissions, energy efficiency and a decarbonisation plan."),
]
_BY_KEY = {t["key"]: t for t in TYPES}


def types():
    return {"types": TYPES, "count": len(TYPES)}


def get(key):
    return _BY_KEY.get((key or "").strip())


def live_agents(t):
    if not _M:
        return t.get("agents", [])
    return [a for a in t.get("agents", []) if _M.MSME_AGENTS.get(a, {}).get("status") == "live"]


def meta():
    return {"count": len(TYPES),
            "types": [{"key": t["key"], "name": t["name"], "tower": t["tower"], "icon": t["icon"],
                       "objective": t["objective"], "weeks": t["duration_weeks"], "agents": t["agents"]} for t in TYPES],
            "endpoints": ["GET /engagement-types", "GET /engagement-types/meta", "GET /engagement-types/tests"]}


def run_type_tests():
    cases = []
    cases.append(("count", len(TYPES) >= 12))
    # every type maps to live agents end-to-end
    bad = []
    if _M:
        keys = set(k for k, a in _M.MSME_AGENTS.items() if a.get("status") == "live")
        for t in TYPES:
            for a in t["agents"]:
                if a not in keys:
                    bad.append((t["key"], a))
    cases.append(("agents_live", not bad))
    # each type has deliverables + kpis + value levers + a sample
    cases.append(("complete", all(t["deliverables"] and t["kpis"] and t["value_levers"] and t["sample"] for t in TYPES)))
    # working_capital is the end-to-end cross-cut (AR via collections/credit + AP + inventory + cfo)
    wc = get("working_capital")
    cases.append(("working_capital_e2e", {"cfo_finance", "procurement_agent", "inventory_agent"}.issubset(set(wc["agents"]))
                  and any(a in wc["agents"] for a in ("collections", "credit_management", "o2c_expert"))))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases), "bad_agents": bad},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    import json
    print(json.dumps(run_type_tests(), indent=2))
