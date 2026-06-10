"""
consulting_catalog.py — the AI Consulting OS service portfolio, encoded as a function.

Mirrors how a top-tier firm (McKinsey/BCG/Bain/Deloitte/PwC/EY/KPMG) organises
expertise, as a 3-level tree:

    Consulting Towers (L1)  ->  Service Lines (L2)  ->  Workflows (L3)

Each tower is mapped to the AI advisor persona that fronts it and to the live
msme_agents that actually deliver the work, so the OS can prove — for every
service a real consulting firm sells — which agent does the job (covered),
which does it partially (partial), or which is still a gap (planned).

Deterministic, no external deps. Reuses msme_agents.MSME_AGENTS for live status.

Endpoints (wired in main.py): GET /catalog, GET /catalog/coverage,
GET /catalog/meta, POST /catalog/resolve.
"""

try:
    import msme_agents as _M
except Exception:
    _M = None


def _sl(name, workflows, agent=None):
    return {"name": name, "workflows": workflows, "agent": agent}


# ---------------------------------------------------------------------------
# L1 TOWERS -> L2 SERVICE LINES -> L3 WORKFLOWS  (+ AI advisor + delivering agents)
# ---------------------------------------------------------------------------
TOWERS = [
    {
        "key": "strategy_corporate", "name": "Strategy & Corporate Advisory", "icon": "🎯",
        "ai_advisor": "AI Strategy Consultant",
        "agents": ["ceo_copilot", "market_research", "competitor_intel", "product_manager", "sales_gtm", "msme_due_diligence", "notion_workspace"],
        "service_lines": [
            _sl("Corporate Strategy", ["Vision & Mission", "Business Model Design", "Growth Strategy", "Market Entry Strategy", "Geographic Expansion", "Diversification Strategy", "Turnaround Strategy"], "ceo_copilot"),
            _sl("Commercial Excellence", ["Pricing Strategy", "Channel Strategy", "Sales Transformation", "Customer Segmentation", "Revenue Growth"], "sales_gtm"),
            _sl("M&A Advisory", ["Target Screening", "Due Diligence", "Valuation", "Synergy Analysis", "Post-Merger Integration"], "msme_due_diligence"),
            _sl("PMO & Transformation", ["Program Management", "Portfolio Management", "KPI Tracking", "Transformation Office"], "notion_workspace"),
        ],
    },
    {
        "key": "finance_transformation", "name": "Finance Transformation (CFO Advisory)", "icon": "💰",
        "ai_advisor": "AI CFO Advisor",
        "agents": ["cfo_finance", "r2r_expert"],
        "service_lines": [
            _sl("Financial Planning & Analysis (FP&A)", ["Budgeting", "Forecasting", "Scenario Planning", "Variance Analysis"], "cfo_finance"),
            _sl("Working Capital Management", ["Cash Flow Optimization", "Cash Conversion Cycle", "Liquidity Planning", "Treasury Advisory"], "cfo_finance"),
            _sl("Cost Optimization", ["Cost Reduction", "Zero-Based Budgeting", "Spend Analysis"], "cfo_finance"),
            _sl("Finance Operating Model", ["Shared Services", "GBS Setup", "Finance COE Design"], "r2r_expert"),
        ],
    },
    {
        "key": "o2c", "name": "Order-to-Cash (O2C)", "icon": "🧾",
        "ai_advisor": "AI O2C Expert",
        "agents": ["o2c_expert", "cfo_finance", "gst_compliance"],
        "service_lines": [
            _sl("Customer Master Data", ["Customer Onboarding", "Credit Setup", "Customer Maintenance"], "o2c_expert"),
            _sl("Credit Management", ["Credit Risk Assessment", "Credit Limits", "Credit Reviews", "Collection Strategy"], "o2c_expert"),
            _sl("Order Management", ["Order Entry", "Order Validation", "Order Release", "Customer Service"], "o2c_expert"),
            _sl("Billing", ["Invoice Generation", "E-Invoicing", "Tax Validation"], "o2c_expert"),
            _sl("Accounts Receivable", ["Collections", "Promise to Pay", "Aging Management"], "o2c_expert"),
            _sl("Cash Application", ["Lockbox", "EDI Remittance", "Auto Cash", "Unapplied Cash"], "o2c_expert"),
            _sl("Deductions & Disputes", ["Trade Promotions", "Pricing Claims", "Short Payments", "Returns"], "o2c_expert"),
            _sl("Revenue Assurance", ["Revenue Leakage", "Billing Accuracy"], "o2c_expert"),
        ],
    },
    {
        "key": "p2p", "name": "Procure-to-Pay (P2P)", "icon": "🛒",
        "ai_advisor": "AI P2P Expert",
        "agents": ["procurement_agent", "cfo_finance"],
        "service_lines": [
            _sl("Procurement", ["Vendor Sourcing", "RFQ/RFP", "Vendor Negotiation"], "procurement_agent"),
            _sl("Supplier Management", ["Vendor Onboarding", "Vendor Performance"], "procurement_agent"),
            _sl("Purchasing", ["Purchase Requisition", "Purchase Orders"], "procurement_agent"),
            _sl("Accounts Payable", ["Invoice Processing", "2-way Matching", "3-way Matching"], "procurement_agent"),
            _sl("Payment Processing", ["Vendor Payments", "Treasury Integration"], "cfo_finance"),
            _sl("Travel & Expense", ["Employee Reimbursements", "Expense Audits"], "procurement_agent"),
        ],
    },
    {
        "key": "r2r", "name": "Record-to-Report (R2R)", "icon": "📒",
        "ai_advisor": "AI R2R Expert",
        "agents": ["r2r_expert", "cfo_finance"],
        "service_lines": [
            _sl("General Accounting", ["Journal Entries", "Accruals", "Reconciliations"], "r2r_expert"),
            _sl("Fixed Assets", ["Asset Accounting", "Depreciation"], "r2r_expert"),
            _sl("Intercompany Accounting", ["Intercompany Billing", "Eliminations"], "r2r_expert"),
            _sl("Close Management", ["Month-End Close", "Year-End Close"], "r2r_expert"),
            _sl("Consolidation", ["Group Reporting", "Consolidated Financials"], "r2r_expert"),
            _sl("Financial Reporting", ["MIS Reporting", "Board Reporting"], "r2r_expert"),
        ],
    },
    {
        "key": "tax_compliance", "name": "Tax & Compliance Advisory", "icon": "🧮",
        "ai_advisor": "AI Tax Advisor",
        "agents": ["gst_compliance", "legal_contracts", "export_compliance"],
        "service_lines": [
            _sl("Direct Tax", ["Income Tax", "Corporate Tax"], "gst_compliance"),
            _sl("Indirect Tax", ["GST", "Customs Duty"], "gst_compliance"),
            _sl("International Tax", ["Transfer Pricing", "Global Tax Planning"], "export_compliance"),
            _sl("Regulatory Compliance", ["MCA Compliance", "Companies Act"], "legal_contracts"),
            _sl("Secretarial Compliance", ["Board Meetings", "ROC Filings"], "legal_contracts"),
        ],
    },
    {
        "key": "risk_advisory", "name": "Risk Advisory", "icon": "⚠️",
        "ai_advisor": "AI Risk Advisor",
        "agents": ["risk_audit", "cyber_dpdp"],
        "service_lines": [
            _sl("Enterprise Risk Management", ["Risk Registers", "Risk Assessment"], "risk_audit"),
            _sl("Internal Controls", ["SOX", "IFC"], "risk_audit"),
            _sl("Internal Audit", ["Process Audits", "Compliance Audits"], "risk_audit"),
            _sl("Fraud Risk", ["Fraud Detection", "Investigations"], "risk_audit"),
            _sl("Cyber Risk", ["Security Assessments"], "cyber_dpdp"),
        ],
    },
    {
        "key": "legal_advisory", "name": "Legal Advisory", "icon": "⚖️",
        "ai_advisor": "AI Legal Advisor",
        "agents": ["legal_contracts"],
        "service_lines": [
            _sl("Corporate Legal", ["Contracts", "Agreements"], "legal_contracts"),
            _sl("Litigation Support", ["Case Management"], "legal_contracts"),
            _sl("Compliance", ["Labor Laws", "Regulatory Matters"], "legal_contracts"),
            _sl("Contract Lifecycle Management", ["Drafting", "Review", "Renewal"], "legal_contracts"),
        ],
    },
    {
        "key": "human_capital", "name": "Human Capital Consulting", "icon": "👥",
        "ai_advisor": "AI CHRO Advisor",
        "agents": ["hr_payroll"],
        "service_lines": [
            _sl("HR Transformation", ["HR Operating Model"], "hr_payroll"),
            _sl("Talent Acquisition", ["Hiring", "Workforce Planning"], "hr_payroll"),
            _sl("Learning & Development", ["Training Programs"], "hr_payroll"),
            _sl("Performance Management", ["KPI Framework"], "hr_payroll"),
            _sl("Compensation & Benefits", ["Salary Benchmarking"], "hr_payroll"),
        ],
    },
    {
        "key": "supply_chain", "name": "Supply Chain Consulting", "icon": "🔗",
        "ai_advisor": "AI Supply Chain Advisor",
        "agents": ["inventory_agent", "procurement_agent", "coo_operations"],
        "service_lines": [
            _sl("Demand Planning", ["Forecasting"], "inventory_agent"),
            _sl("Procurement Strategy", ["Strategic Sourcing"], "procurement_agent"),
            _sl("Inventory Optimization", ["Safety Stock", "ABC Analysis"], "inventory_agent"),
            _sl("Warehouse Management", ["Inbound", "Outbound"], "coo_operations"),
            _sl("Logistics", ["Transportation", "Route Optimization"], "coo_operations"),
            _sl("S&OP", ["Sales & Operations Planning"], "coo_operations"),
        ],
    },
    {
        "key": "manufacturing_excellence", "name": "Manufacturing Excellence", "icon": "🏭",
        "ai_advisor": "AI COO Advisor",
        "agents": ["coo_operations", "sop_agent"],
        "service_lines": [
            _sl("Production Planning", ["Production Scheduling", "Capacity Planning"], "coo_operations"),
            _sl("Lean Manufacturing", ["Value-Stream Mapping", "Waste Elimination"], "coo_operations"),
            _sl("Six Sigma", ["DMAIC", "Process Capability"], "coo_operations"),
            _sl("Quality Management", ["QMS", "Defect Reduction"], "sop_agent"),
            _sl("Maintenance Excellence", ["Preventive Maintenance", "OEE"], "sop_agent"),
            _sl("Plant Performance", ["Throughput", "Bottleneck Analysis"], "coo_operations"),
            _sl("Industry 4.0", ["Smart Operations", "IoT/Sensors"], "coo_operations"),
        ],
    },
    {
        "key": "sales_crm", "name": "Sales & CRM Consulting", "icon": "📈",
        "ai_advisor": "AI CRO (Revenue) Advisor",
        "agents": ["sales_gtm", "customer_support"],
        "service_lines": [
            _sl("CRM Strategy", ["CRM Design", "Pipeline Hygiene"], "sales_gtm"),
            _sl("Lead Management", ["Lead Capture", "Qualification"], "sales_gtm"),
            _sl("Opportunity Management", ["Deal Stages", "Win/Loss"], "sales_gtm"),
            _sl("Territory Planning", ["Beat Plan", "Coverage"], "sales_gtm"),
            _sl("Sales Forecasting", ["Pipeline Forecast"], "sales_gtm"),
            _sl("Customer Success", ["Onboarding", "Retention"], "customer_support"),
        ],
    },
    {
        "key": "marketing", "name": "Marketing Consulting", "icon": "📣",
        "ai_advisor": "AI Marketing Advisor",
        "agents": ["sales_gtm"],
        "service_lines": [
            _sl("Brand Strategy", ["Positioning", "Brand Architecture"], "sales_gtm"),
            _sl("Digital Marketing", ["SEO", "Content"], "sales_gtm"),
            _sl("Performance Marketing", ["Paid Acquisition", "CAC/ROAS"], "sales_gtm"),
            _sl("Marketing Automation", ["Funnels", "CRM Journeys"], "sales_gtm"),
            _sl("Customer Experience", ["CX Journey", "NPS"], "customer_support"),
            _sl("Loyalty Programs", ["Rewards", "Repeat Rate"], "sales_gtm"),
        ],
    },
    {
        "key": "technology", "name": "Technology Consulting", "icon": "🖥️",
        "ai_advisor": "AI Technology Advisor",
        "agents": ["erp_consultant", "cyber_dpdp"],
        "service_lines": [
            _sl("Enterprise Architecture", ["Target Architecture", "Application Landscape"], "erp_consultant"),
            _sl("ERP Advisory", ["SAP S/4HANA", "Oracle Fusion Cloud ERP", "Microsoft Dynamics 365"], "erp_consultant"),
            _sl("Cloud Transformation", ["Cloud Migration", "Cost Optimization"], "erp_consultant"),
            _sl("Data & Analytics", ["Data Platform", "BI/Dashboards"], "erp_consultant"),
            _sl("AI Strategy", ["AI Roadmap", "Use-Case Prioritisation"], "erp_consultant"),
            _sl("Automation", ["Process Automation"], "erp_consultant"),
            _sl("RPA", ["Bot Identification", "Deployment"], "erp_consultant"),
            _sl("GenAI Implementation", ["Copilot/Assistant Build", "Guardrails"], "cyber_dpdp"),
        ],
    },
    {
        "key": "esg_sustainability", "name": "ESG & Sustainability", "icon": "🌱",
        "ai_advisor": "AI Sustainability Advisor",
        "agents": ["sustainability_esg"],
        "service_lines": [
            _sl("ESG Reporting", ["BRSR", "Disclosure"], "sustainability_esg"),
            _sl("Carbon Accounting", ["Scope 1/2/3", "CBAM"], "sustainability_esg"),
            _sl("Sustainability Strategy", ["Materiality", "Net-Zero Roadmap"], "sustainability_esg"),
            _sl("Energy Efficiency", ["Energy Audit", "BEE/PAT"], "sustainability_esg"),
            _sl("Green Supply Chain", ["Supplier ESG", "EPR"], "sustainability_esg"),
        ],
    },
    {
        "key": "industry_specific", "name": "Industry-Specific Advisory", "icon": "🏢",
        "ai_advisor": "AI Industry Expert",
        "agents": ["market_research", "competitor_intel", "sustainability_esg"],
        "service_lines": [
            _sl("Banking", ["Credit Risk", "Collections", "Treasury"], "cfo_finance"),
            _sl("Insurance", ["Claims", "Underwriting"], "risk_audit"),
            _sl("Retail", ["Merchandising", "Pricing"], "sales_gtm"),
            _sl("Manufacturing", ["Operations Excellence"], "coo_operations"),
            _sl("Pharma", ["GMP Compliance"], "sop_agent"),
            _sl("Healthcare", ["Hospital Operations"], "coo_operations"),
            _sl("Real Estate", ["Project Advisory"], "ceo_copilot"),
            _sl("Logistics", ["Network Design"], "coo_operations"),
            _sl("MSME Advisory", ["Business Setup", "Compliance", "Funding", "Growth Planning"], "ceo_copilot"),
        ],
        "note": "Backed by the 30 industry playbooks (industry_playbooks) + industry expert agents (industry_experts).",
    },
]

# The 12 highest-revenue areas real firms actually sell, in priority order.
CORE_12 = [
    {"area": "Strategy & Growth", "tower": "strategy_corporate"},
    {"area": "Finance Transformation", "tower": "finance_transformation"},
    {"area": "O2C Transformation", "tower": "o2c"},
    {"area": "P2P Transformation", "tower": "p2p"},
    {"area": "R2R Transformation", "tower": "r2r"},
    {"area": "Working Capital Optimization", "tower": "finance_transformation"},
    {"area": "Tax & Compliance", "tower": "tax_compliance"},
    {"area": "Risk & Internal Audit", "tower": "risk_advisory"},
    {"area": "Technology & ERP Transformation", "tower": "technology"},
    {"area": "Supply Chain Transformation", "tower": "supply_chain"},
    {"area": "Human Capital Transformation", "tower": "human_capital"},
    {"area": "M&A and Due Diligence", "tower": "strategy_corporate"},
]

# The AI advisor roster the OS exposes (the "C-suite as agents"), each fronting a tower.
AI_ADVISORS = [
    {"advisor": "AI CEO Advisor", "agent": "ceo_copilot", "tower": "strategy_corporate"},
    {"advisor": "AI CFO Advisor", "agent": "cfo_finance", "tower": "finance_transformation"},
    {"advisor": "AI COO Advisor", "agent": "coo_operations", "tower": "manufacturing_excellence"},
    {"advisor": "AI CRO (Revenue) Advisor", "agent": "sales_gtm", "tower": "sales_crm"},
    {"advisor": "AI CHRO Advisor", "agent": "hr_payroll", "tower": "human_capital"},
    {"advisor": "AI Tax Advisor", "agent": "gst_compliance", "tower": "tax_compliance"},
    {"advisor": "AI Compliance Advisor", "agent": "gst_compliance", "tower": "tax_compliance"},
    {"advisor": "AI Legal Advisor", "agent": "legal_contracts", "tower": "legal_advisory"},
    {"advisor": "AI O2C Expert", "agent": "o2c_expert", "tower": "o2c"},
    {"advisor": "AI P2P Expert", "agent": "procurement_agent", "tower": "p2p"},
    {"advisor": "AI R2R Expert", "agent": "r2r_expert", "tower": "r2r"},
    {"advisor": "AI Working Capital Advisor", "agent": "cfo_finance", "tower": "finance_transformation"},
    {"advisor": "AI Supply Chain Advisor", "agent": "inventory_agent", "tower": "supply_chain"},
    {"advisor": "AI Strategy Consultant", "agent": "ceo_copilot", "tower": "strategy_corporate"},
    {"advisor": "AI Due Diligence Consultant", "agent": "msme_due_diligence", "tower": "strategy_corporate"},
    {"advisor": "AI Technology Advisor", "agent": "erp_consultant", "tower": "technology"},
    {"advisor": "AI Risk Advisor", "agent": "risk_audit", "tower": "risk_advisory"},
    {"advisor": "AI Sustainability Advisor", "agent": "sustainability_esg", "tower": "esg_sustainability"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _live(agent_key):
    if not _M:
        return False
    return _M.MSME_AGENTS.get(agent_key, {}).get("status") == "live"


def _agent_name(agent_key):
    if not _M:
        return agent_key
    return _M.MSME_AGENTS.get(agent_key, {}).get("name", agent_key)


def _tower_coverage(tower):
    """A tower is covered if any mapped agent is live; partial if some service lines
    have no live agent; planned if no live agent at all."""
    sls = tower["service_lines"]
    sl_live = [bool(s.get("agent") and _live(s["agent"])) for s in sls]
    any_live = any(_live(a) for a in tower.get("agents", []))
    if all(sl_live) and any_live:
        return "covered"
    if any(sl_live) or any_live:
        return "partial"
    return "planned"


def catalog():
    """The full L1->L2->L3 tree, annotated with live-agent coverage."""
    towers = []
    for t in TOWERS:
        sls = []
        for s in t["service_lines"]:
            sls.append({
                "name": s["name"], "workflows": s["workflows"],
                "agent": s.get("agent"),
                "agent_name": _agent_name(s["agent"]) if s.get("agent") else None,
                "live": bool(s.get("agent") and _live(s["agent"])),
            })
        towers.append({
            "key": t["key"], "name": t["name"], "icon": t["icon"],
            "ai_advisor": t["ai_advisor"],
            "agents": [{"key": a, "name": _agent_name(a), "live": _live(a)} for a in t.get("agents", [])],
            "coverage": _tower_coverage(t),
            "service_lines": sls,
            "service_line_count": len(sls),
            "workflow_count": sum(len(s["workflows"]) for s in t["service_lines"]),
            "note": t.get("note"),
        })
    return {
        "towers": towers,
        "tower_count": len(towers),
        "service_line_count": sum(len(t["service_lines"]) for t in TOWERS),
        "workflow_count": sum(len(s["workflows"]) for t in TOWERS for s in t["service_lines"]),
        "core_12": CORE_12,
        "ai_advisors": [{**a, "agent_name": _agent_name(a["agent"]), "live": _live(a["agent"])} for a in AI_ADVISORS],
    }


def coverage():
    """Coverage scorecard across all 16 towers + the 12 core areas + advisor roster."""
    rows = []
    for t in TOWERS:
        cov = _tower_coverage(t)
        live_sls = sum(1 for s in t["service_lines"] if s.get("agent") and _live(s["agent"]))
        rows.append({
            "tower": t["name"], "key": t["key"], "ai_advisor": t["ai_advisor"],
            "coverage": cov,
            "service_lines": len(t["service_lines"]),
            "service_lines_live": live_sls,
            "agents": [a for a in t.get("agents", []) if _live(a)],
        })
    covered = sum(1 for r in rows if r["coverage"] == "covered")
    partial = sum(1 for r in rows if r["coverage"] == "partial")
    planned = sum(1 for r in rows if r["coverage"] == "planned")
    advisors_live = sum(1 for a in AI_ADVISORS if _live(a["agent"]))
    return {
        "summary": {
            "towers": len(rows), "covered": covered, "partial": partial, "planned": planned,
            "advisors_total": len(AI_ADVISORS), "advisors_live": advisors_live,
            "deployment_ready": planned == 0,
        },
        "towers": rows,
        "advisors": [{**a, "agent_name": _agent_name(a["agent"]), "live": _live(a["agent"])} for a in AI_ADVISORS],
    }


_STOP = set("the a an and or of to for with in on at by from is are as per its their your our".split())


def _kw(s):
    return {w for w in (s or "").lower().replace("/", " ").replace("&", " ").split() if w not in _STOP and len(w) > 2}


def resolve(query):
    """Map a free-text consulting need to the best tower / service line / workflow + the
    delivering agent, so a request can be routed straight to the right AI advisor."""
    q = _kw(query)
    if not q:
        return {"matched": False}
    best = None
    for t in TOWERS:
        tower_kw = _kw(t["name"]) | _kw(t.get("ai_advisor", ""))
        for s in t["service_lines"]:
            # Weight name matches over generic workflow words (e.g. "reporting" shouldn't
            # pull an ESG query into R2R just because both have a "Reporting" workflow).
            name_score = len(q & _kw(s["name"])) * 3
            tower_score = len(q & tower_kw) * 2
            wf_words = set().union(*[_kw(w) for w in s["workflows"]] or [set()])
            wf_score = len(q & wf_words)
            wf_hit = next((w for w in s["workflows"] if q & _kw(w)), None)
            score = name_score + tower_score + wf_score + (2 if wf_hit else 0)
            if best is None or score > best["score"]:
                best = {"score": score, "tower": t, "sl": s, "workflow": wf_hit}
    if not best or best["score"] <= 0:
        return {"matched": False, "query": query}
    t, s = best["tower"], best["sl"]
    return {
        "matched": True, "query": query,
        "tower": {"key": t["key"], "name": t["name"], "icon": t["icon"], "ai_advisor": t["ai_advisor"]},
        "service_line": s["name"],
        "workflow": best["workflow"],
        "agent": s.get("agent"),
        "agent_name": _agent_name(s["agent"]) if s.get("agent") else None,
        "agent_live": bool(s.get("agent") and _live(s["agent"])),
        "run_hint": {"endpoint": "POST /agents/run", "body": {"agent": s.get("agent"), "description": query}},
    }


def meta():
    return {
        "towers": [{"key": t["key"], "name": t["name"], "icon": t["icon"], "ai_advisor": t["ai_advisor"],
                    "service_lines": len(t["service_lines"]),
                    "workflows": sum(len(s["workflows"]) for s in t["service_lines"])} for t in TOWERS],
        "tower_count": len(TOWERS),
        "core_12": [c["area"] for c in CORE_12],
        "ai_advisors": [a["advisor"] for a in AI_ADVISORS],
        "levels": {"L1": "Consulting Towers", "L2": "Service Lines", "L3": "Workflows"},
        "endpoints": ["GET /catalog", "GET /catalog/coverage", "GET /catalog/meta", "POST /catalog/resolve"],
    }


def run_catalog_tests():
    cases = []
    cat = catalog()
    cases.append(("structure", cat["tower_count"] == 16 and cat["workflow_count"] >= 100 and len(cat["ai_advisors"]) >= 15))
    cov = coverage()["summary"]
    cases.append(("coverage_no_planned", cov["planned"] == 0 and cov["covered"] >= 12))
    # every mapped agent key must exist in the live registry
    bad = []
    if _M:
        keys = set(_M.MSME_AGENTS.keys())
        for t in TOWERS:
            for s in t["service_lines"]:
                if s.get("agent") and s["agent"] not in keys:
                    bad.append(s["agent"])
            for a in t["agents"]:
                if a not in keys:
                    bad.append(a)
    cases.append(("agents_exist", not bad))
    # resolve routes a known need
    r = resolve("we have too many overdue invoices and high DSO, fix our collections")
    cases.append(("resolve_o2c", r.get("matched") and r.get("tower", {}).get("key") == "o2c"))
    r2 = resolve("month-end close takes too long and books are not reconciled")
    cases.append(("resolve_r2r", r2.get("matched") and r2.get("tower", {}).get("key") == "r2r"))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases),
                        "bad_agents": bad},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    import json
    print(json.dumps(run_catalog_tests(), indent=2))
    print(json.dumps(coverage()["summary"], indent=2))
