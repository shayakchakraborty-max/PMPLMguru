"""
market_intel.py — the MSME Intelligence Database for the AI Consulting OS.

Sector- and business-type-level market intelligence for Indian MSMEs: market size
(TAM), MSME presence, average & top-quartile revenue, EBITDA, CAGR, working-capital
benchmarks, key risks/KPIs, ERP modules, compliance, export potential, AI opportunity
— plus the recommended AI advisor agents and a ready-to-run sample engagement per
business type, so the landing page can go from "filter business type" straight to a
stunning end-to-end demo report.

Figures are industry-level estimates / consulting benchmarks (India does not publish
MSME revenue by every business type), clearly labelled as such.

Deterministic, no deps. Endpoints (main.py): GET /market/sectors, GET /market/segments,
POST /market/lookup (+ /market/meta).
"""

try:
    import msme_agents as _M
except Exception:
    _M = None
try:
    import industry_playbooks as _PB
except Exception:
    _PB = None


# ---------------------------------------------------------------------------
# SECTOR-LEVEL LANDSCAPE (2026 estimates)
# ---------------------------------------------------------------------------
SECTORS = [
    {"key": "retail", "name": "Retail Trade", "icon": "🛒", "market_value": "₹90-100 Lakh Cr", "msme_presence": "Very High",
     "avg_revenue": "₹25 Lakh – ₹5 Cr", "top_revenue": "₹100 Cr+", "ebitda": "3-15%", "cagr": "9-11%",
     "export_potential": "Low", "ai_opportunity": "Very High", "gross_margin": "12-30%",
     "wc_days": 35, "inventory_days": 45, "receivable_days": 15, "payable_days": 30,
     "key_risks": ["Inventory & dead stock", "Thin margins", "Credit/working capital", "Quick-commerce disruption"],
     "key_kpis": ["Inventory turns", "Gross margin", "Sales/sq ft", "Repeat rate"],
     "erp_modules": ["inventory", "sales", "billing", "receivables"], "agents": ["inventory_agent", "cfo_finance", "o2c_expert", "marketing_agent"]},
    {"key": "wholesale", "name": "Wholesale & Distribution", "icon": "📦", "market_value": "₹60-80 Lakh Cr", "msme_presence": "Very High",
     "avg_revenue": "₹1-20 Cr", "top_revenue": "₹500 Cr+", "ebitda": "2-8%", "cagr": "8-10%",
     "export_potential": "Low-Med", "ai_opportunity": "Very High", "gross_margin": "5-12%",
     "wc_days": 55, "inventory_days": 40, "receivable_days": 55, "payable_days": 35,
     "key_risks": ["Stretched receivables", "Thin spreads", "Principal margin pressure", "Beat coverage"],
     "key_kpis": ["DSO", "Inventory turns", "Secondary sales", "Spread %"],
     "erp_modules": ["inventory", "sales", "receivables", "customers"], "agents": ["o2c_expert", "cfo_finance", "sales_gtm", "inventory_agent"]},
    {"key": "manufacturing", "name": "Manufacturing", "icon": "🏭", "market_value": "₹50-60 Lakh Cr", "msme_presence": "Very High",
     "avg_revenue": "₹50 Lakh – ₹50 Cr", "top_revenue": "₹500 Cr+", "ebitda": "8-20%", "cagr": "9-12%",
     "export_potential": "High", "ai_opportunity": "Very High", "gross_margin": "20-40%",
     "wc_days": 75, "inventory_days": 60, "receivable_days": 60, "payable_days": 45,
     "key_risks": ["RM price volatility", "Yield/rework", "Working capital", "OEM dependency"],
     "key_kpis": ["OEE", "First-pass yield", "Cycle time", "RM cost %"],
     "erp_modules": ["inventory", "purchase", "sales", "finance"], "agents": ["coo_operations", "procurement_agent", "sop_agent", "cfo_finance"]},
    {"key": "construction", "name": "Construction & Infrastructure", "icon": "🏗️", "market_value": "₹25-35 Lakh Cr", "msme_presence": "High",
     "avg_revenue": "₹1-50 Cr", "top_revenue": "₹1000 Cr+", "ebitda": "5-15%", "cagr": "7-9%",
     "export_potential": "Low", "ai_opportunity": "Medium", "gross_margin": "12-25%",
     "wc_days": 90, "inventory_days": 30, "receivable_days": 90, "payable_days": 45,
     "key_risks": ["Delayed payments", "Retention money / WIP", "Project delays", "RERA compliance"],
     "key_kpis": ["Project margin", "WIP days", "Retention recovery", "On-time completion"],
     "erp_modules": ["finance", "receivables", "purchase", "approvals"], "agents": ["cfo_finance", "risk_audit", "legal_contracts", "ceo_copilot"]},
    {"key": "logistics", "name": "Logistics", "icon": "🚚", "market_value": "₹20-25 Lakh Cr", "msme_presence": "High",
     "avg_revenue": "₹50 Lakh – ₹20 Cr", "top_revenue": "₹500 Cr+", "ebitda": "5-15%", "cagr": "10-13%",
     "export_potential": "Med", "ai_opportunity": "High", "gross_margin": "12-25%",
     "wc_days": 50, "inventory_days": 5, "receivable_days": 55, "payable_days": 30,
     "key_risks": ["Low utilisation", "Fuel cost", "Detention charges", "Thin margins"],
     "key_kpis": ["Fleet utilisation", "Cost/km", "On-time delivery", "Detention %"],
     "erp_modules": ["finance", "sales", "receivables"], "agents": ["coo_operations", "cfo_finance", "inventory_agent", "o2c_expert"]},
    {"key": "food_processing", "name": "Food Processing", "icon": "🍲", "market_value": "₹30-35 Lakh Cr", "msme_presence": "High",
     "avg_revenue": "₹50 Lakh – ₹25 Cr", "top_revenue": "₹500 Cr+", "ebitda": "8-20%", "cagr": "11-14%",
     "export_potential": "High", "ai_opportunity": "High", "gross_margin": "20-35%",
     "wc_days": 60, "inventory_days": 50, "receivable_days": 45, "payable_days": 35,
     "key_risks": ["FSSAI compliance", "Cold-chain loss", "RM/feed cost", "Shelf life"],
     "key_kpis": ["Yield", "Wastage %", "Gross margin", "Capacity utilisation"],
     "erp_modules": ["inventory", "purchase", "sales", "compliance"], "agents": ["coo_operations", "sop_agent", "procurement_agent", "sustainability_esg"]},
    {"key": "healthcare", "name": "Healthcare", "icon": "🏥", "market_value": "₹12-15 Lakh Cr", "msme_presence": "Medium",
     "avg_revenue": "₹25 Lakh – ₹20 Cr", "top_revenue": "₹200 Cr+", "ebitda": "10-25%", "cagr": "12-15%",
     "export_potential": "Low", "ai_opportunity": "High", "gross_margin": "35-55%",
     "wc_days": 45, "inventory_days": 30, "receivable_days": 60, "payable_days": 40,
     "key_risks": ["TPA/insurer receivables", "NABH gaps", "Equipment utilisation", "Staff cost"],
     "key_kpis": ["Bed/asset utilisation", "TAT", "AR days (TPA)", "Patient throughput"],
     "erp_modules": ["finance", "receivables", "compliance", "inventory"], "agents": ["coo_operations", "o2c_expert", "cfo_finance", "cyber_dpdp"]},
    {"key": "pharma", "name": "Pharma", "icon": "💊", "market_value": "₹5-6 Lakh Cr", "msme_presence": "Medium",
     "avg_revenue": "₹1-50 Cr", "top_revenue": "₹1000 Cr+", "ebitda": "10-30%", "cagr": "10-13%",
     "export_potential": "Very High", "ai_opportunity": "High", "gross_margin": "30-55%",
     "wc_days": 80, "inventory_days": 70, "receivable_days": 65, "payable_days": 50,
     "key_risks": ["Batch expiry / FEFO", "Schedule-H / GMP", "Price control (NPPA)", "Working capital"],
     "key_kpis": ["Expiry write-off %", "Inventory turns", "Batch yield", "Compliance score"],
     "erp_modules": ["inventory", "compliance", "purchase", "finance"], "agents": ["inventory_agent", "sop_agent", "gst_compliance", "export_compliance"]},
    {"key": "education", "name": "Education", "icon": "🎓", "market_value": "₹10-12 Lakh Cr", "msme_presence": "Medium",
     "avg_revenue": "₹10 Lakh – ₹10 Cr", "top_revenue": "₹100 Cr+", "ebitda": "15-40%", "cagr": "12-16%",
     "export_potential": "Low", "ai_opportunity": "High", "gross_margin": "40-65%",
     "wc_days": 20, "inventory_days": 0, "receivable_days": 25, "payable_days": 25,
     "key_risks": ["High CAC", "Low completion", "Fee-collection delays", "Regulatory"],
     "key_kpis": ["CAC", "Completion rate", "Fee realisation", "Segment P&L"],
     "erp_modules": ["customers", "billing", "receivables"], "agents": ["marketing_agent", "cfo_finance", "ceo_copilot", "o2c_expert"]},
    {"key": "it_services", "name": "IT Services", "icon": "💻", "market_value": "₹25-30 Lakh Cr", "msme_presence": "Medium",
     "avg_revenue": "₹25 Lakh – ₹20 Cr", "top_revenue": "₹1000 Cr+", "ebitda": "20-50%", "cagr": "12-18%",
     "export_potential": "Very High", "ai_opportunity": "Very High", "gross_margin": "40-70%",
     "wc_days": 60, "inventory_days": 0, "receivable_days": 65, "payable_days": 30,
     "key_risks": ["Client concentration", "Utilisation/bench", "Attrition", "Margin pressure"],
     "key_kpis": ["Utilisation", "Revenue/employee", "Client concentration", "Gross margin"],
     "erp_modules": ["finance", "receivables", "payroll"], "agents": ["ceo_copilot", "cfo_finance", "org_change", "investor_readiness"]},
    {"key": "hospitality", "name": "Hospitality", "icon": "🏨", "market_value": "₹8-10 Lakh Cr", "msme_presence": "High",
     "avg_revenue": "₹25 Lakh – ₹15 Cr", "top_revenue": "₹200 Cr+", "ebitda": "8-25%", "cagr": "10-13%",
     "export_potential": "Low", "ai_opportunity": "Medium", "gross_margin": "25-50%",
     "wc_days": 25, "inventory_days": 15, "receivable_days": 20, "payable_days": 35,
     "key_risks": ["Seasonality", "Staff cost", "OTA commissions", "Direct-booking conversion"],
     "key_kpis": ["Occupancy", "RevPAR", "Staff cost %", "Direct-booking %"],
     "erp_modules": ["sales", "billing", "inventory"], "agents": ["coo_operations", "marketing_agent", "cfo_finance", "customer_support"]},
    {"key": "agri_allied", "name": "Agriculture & Allied", "icon": "🌾", "market_value": "₹40-50 Lakh Cr", "msme_presence": "Very High",
     "avg_revenue": "₹5 Lakh – ₹5 Cr", "top_revenue": "₹100 Cr+", "ebitda": "5-20%", "cagr": "8-11%",
     "export_potential": "High", "ai_opportunity": "Medium", "gross_margin": "15-30%",
     "wc_days": 55, "inventory_days": 45, "receivable_days": 40, "payable_days": 25,
     "key_risks": ["Cold-chain loss", "FSSAI/APEDA", "Commodity price", "Procurement"],
     "key_kpis": ["Wastage %", "Realisation/kg", "Capacity utilisation", "Procurement cost"],
     "erp_modules": ["inventory", "purchase", "compliance"], "agents": ["coo_operations", "export_compliance", "sustainability_esg", "cfo_finance"]},
    {"key": "import_export", "name": "Import Export", "icon": "🌐", "market_value": "₹70-80 Lakh Cr", "msme_presence": "Medium",
     "avg_revenue": "₹2-100 Cr", "top_revenue": "₹1000 Cr+", "ebitda": "5-20%", "cagr": "9-12%",
     "export_potential": "Very High", "ai_opportunity": "High", "gross_margin": "10-25%",
     "wc_days": 70, "inventory_days": 50, "receivable_days": 60, "payable_days": 40,
     "key_risks": ["Customs/BIS", "FX exposure", "RoDTEP/incentives", "Working capital"],
     "key_kpis": ["Realisation", "FX cost", "Lead time", "Incentive capture"],
     "erp_modules": ["purchase", "sales", "compliance", "finance"], "agents": ["export_compliance", "cfo_finance", "o2c_expert", "gst_compliance"]},
]
_SECTOR_BY_KEY = {s["key"]: s for s in SECTORS}


def _seg(key, label, market_value, avg_revenue, top_revenue, problems, ebitda=None, margin=None):
    return {"key": key, "label": label, "market_value": market_value, "avg_revenue": avg_revenue,
            "top_revenue": top_revenue, "problems": problems, "ebitda": ebitda, "margin": margin}


# ---------------------------------------------------------------------------
# BUSINESS-TYPE SEGMENTATION (per sector)
# ---------------------------------------------------------------------------
SEGMENTS = {
    "retail": [
        _seg("kirana", "Kirana Store", "₹20+ Lakh Cr", "₹15-50 Lakh", "₹10 Cr", ["Inventory", "Credit"]),
        _seg("pharmacy", "Pharmacy", "₹2-3 Lakh Cr", "₹50 Lakh-5 Cr", "₹100 Cr", ["Expiry", "Compliance"]),
        _seg("mobile_store", "Mobile Store", "₹1 Lakh Cr+", "₹50 Lakh-10 Cr", "₹100 Cr", ["Competition"]),
        _seg("electronics", "Electronics", "₹5 Lakh Cr+", "₹1-10 Cr", "₹200 Cr", ["Inventory"]),
        _seg("apparel", "Apparel Store", "₹8 Lakh Cr+", "₹25 Lakh-5 Cr", "₹100 Cr", ["Fashion Trends"]),
        _seg("hardware", "Hardware Store", "₹3 Lakh Cr+", "₹50 Lakh-10 Cr", "₹100 Cr", ["Working Capital"]),
        _seg("jewellery", "Jewellery", "₹7 Lakh Cr+", "₹2-25 Cr", "₹500 Cr", ["Gold Prices"]),
    ],
    "manufacturing": [
        _seg("rice_mill", "Rice Mill", "₹1.5 Lakh Cr", "₹2-20 Cr", "₹300 Cr", ["Commodity Pricing"]),
        _seg("flour_mill", "Flour Mill", "₹80,000 Cr", "₹1-10 Cr", "₹100 Cr", ["Raw Material Cost"]),
        _seg("dairy", "Dairy Processing", "₹15 Lakh Cr", "₹5-50 Cr", "₹1000 Cr", ["Procurement"]),
        _seg("spice", "Spice Processing", "₹90,000 Cr", "₹1-20 Cr", "₹300 Cr", ["Quality"]),
        _seg("garment", "Garment Factory", "₹8 Lakh Cr", "₹2-25 Cr", "₹500 Cr", ["Labor"]),
        _seg("packaging", "Packaging Unit", "₹1.5 Lakh Cr", "₹2-20 Cr", "₹300 Cr", ["Raw Material"]),
        _seg("plastic", "Plastic Products", "₹4 Lakh Cr", "₹2-50 Cr", "₹500 Cr", ["Compliance"]),
        _seg("auto_components", "Auto Components", "₹6 Lakh Cr", "₹5-100 Cr", "₹1000 Cr", ["OEM Dependency"]),
        _seg("cable", "Cable Manufacturing", "₹1 Lakh Cr", "₹5-50 Cr", "₹500 Cr", ["Copper Cost"]),
        _seg("pcb", "PCB Assembly", "₹80,000 Cr", "₹2-25 Cr", "₹300 Cr", ["Import Dependency"]),
    ],
    "construction": [
        _seg("civil", "Civil Contractor", "₹10 Lakh Cr+", "₹2-50 Cr", "₹500 Cr", ["Delayed Payments"]),
        _seg("interior", "Interior Contractor", "₹1 Lakh Cr+", "₹50 Lakh-10 Cr", "₹100 Cr", ["Vendor Control"]),
        _seg("hvac", "HVAC Contractor", "₹90,000 Cr", "₹2-25 Cr", "₹200 Cr", ["AMC Tracking"]),
        _seg("fire_safety", "Fire Safety Contractor", "₹35,000 Cr", "₹1-20 Cr", "₹100 Cr", ["Compliance"]),
        _seg("security_integrator", "Security Integrator", "₹50,000 Cr", "₹1-20 Cr", "₹100 Cr", ["Service Quality"]),
        _seg("epc", "EPC Contractor", "₹8 Lakh Cr+", "₹10-100 Cr", "₹1000 Cr", ["Project Delays"]),
    ],
    "logistics": [
        _seg("truck_fleet", "Truck Fleet Owner", "₹8 Lakh Cr", "₹50 Lakh-10 Cr", "₹200 Cr", ["Utilisation", "Fuel"]),
        _seg("warehouse", "Warehouse Operator", "₹2 Lakh Cr", "₹1-20 Cr", "₹300 Cr", ["Space utilisation"]),
        _seg("cold_storage", "Cold Storage", "₹1 Lakh Cr", "₹2-25 Cr", "₹200 Cr", ["Energy cost", "Spoilage"]),
        _seg("freight_forwarder", "Freight Forwarder", "₹3 Lakh Cr", "₹2-50 Cr", "₹500 Cr", ["FX", "Documentation"]),
        _seg("courier", "Courier Business", "₹1 Lakh Cr", "₹50 Lakh-20 Cr", "₹300 Cr", ["Last-mile cost"]),
    ],
    "professional_services": [
        _seg("ca_firm", "CA Firm", "₹60,000 Cr", "₹25 Lakh-5 Cr", "₹100 Cr", ["Capacity", "Compliance load"], margin="25-50%"),
        _seg("law_firm", "Law Firm", "₹40,000 Cr", "₹50 Lakh-10 Cr", "₹500 Cr", ["Utilisation"], margin="30-60%"),
        _seg("consulting_firm", "Consulting Firm", "₹1 Lakh Cr", "₹50 Lakh-20 Cr", "₹500 Cr", ["Client concentration"], margin="30-70%"),
        _seg("hr_agency", "HR Agency", "₹30,000 Cr", "₹25 Lakh-10 Cr", "₹200 Cr", ["Attrition", "Margins"], margin="20-50%"),
        _seg("marketing_agency", "Marketing Agency", "₹50,000 Cr", "₹25 Lakh-10 Cr", "₹300 Cr", ["Retainer churn"], margin="20-60%"),
    ],
    "it_services": [
        _seg("saas", "SaaS", "₹4-5 Lakh Cr", "₹50 Lakh-20 Cr", "₹1000 Cr+", ["CAC/LTV", "Churn"]),
        _seg("ai_startup", "AI Startup", "₹1 Lakh Cr+", "₹25 Lakh-10 Cr", "₹500 Cr", ["Funding", "Talent"]),
        _seg("edtech", "EdTech", "₹2 Lakh Cr", "₹25 Lakh-20 Cr", "₹500 Cr", ["CAC", "Completion"]),
        _seg("legaltech", "LegalTech", "₹15,000 Cr", "₹10 Lakh-5 Cr", "₹100 Cr", ["Adoption"]),
        _seg("agritech", "AgriTech", "₹50,000 Cr", "₹25 Lakh-10 Cr", "₹200 Cr", ["Unit economics"]),
        _seg("fintech", "FinTech", "₹5 Lakh Cr", "₹50 Lakh-50 Cr", "₹2000 Cr", ["Compliance", "Risk"]),
    ],
}
# attach sector to each segment
for _sk, _segs in SEGMENTS.items():
    for _s in _segs:
        _s["sector"] = _sk

HIGHEST_OPPORTUNITY = [
    {"rank": 1, "segment": "Retail + Wholesale", "market_value": "₹160-180 Lakh Cr"},
    {"rank": 2, "segment": "Manufacturing", "market_value": "₹50-60 Lakh Cr"},
    {"rank": 3, "segment": "Agriculture & Allied", "market_value": "₹40-50 Lakh Cr"},
    {"rank": 4, "segment": "Import Export", "market_value": "₹70-80 Lakh Cr"},
    {"rank": 5, "segment": "Construction & Infrastructure", "market_value": "₹25-35 Lakh Cr"},
    {"rank": 6, "segment": "Logistics", "market_value": "₹20-25 Lakh Cr"},
    {"rank": 7, "segment": "IT & Digital", "market_value": "₹25-30 Lakh Cr"},
    {"rank": 8, "segment": "Food Processing", "market_value": "₹30-35 Lakh Cr"},
    {"rank": 9, "segment": "Healthcare & Pharma", "market_value": "₹17-20 Lakh Cr"},
    {"rank": 10, "segment": "Professional Services", "market_value": "₹2-3 Lakh Cr"},
]


# ---------------------------------------------------------------------------
# Sample engagement per business type (feeds the one-click demo -> report)
# ---------------------------------------------------------------------------
def _sample_for(seg, sector):
    label = seg["label"]
    probs = ", ".join(seg["problems"]).lower()
    desc = (f"{label} in India ({sector['name']}), typical MSME with {seg['avg_revenue']} revenue, "
            f"facing {probs}. Wants a diagnostic and a 90-day plan to improve margins, working capital and growth.")
    return {"description": desc, "intake": {"company": label, "sector": sector["name"], "top_challenges": ", ".join(seg["problems"])}}


def _agents(sector):
    return [{"key": a, "name": (_M.MSME_AGENTS.get(a, {}).get("name", a) if _M else a)} for a in sector.get("agents", [])]


def _benchmarks(sector):
    return {"working_capital_days": sector.get("wc_days"), "inventory_days": sector.get("inventory_days"),
            "receivable_days": sector.get("receivable_days"), "payable_days": sector.get("payable_days"),
            "gross_margin": sector.get("gross_margin"), "ebitda": sector.get("ebitda")}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def sectors():
    return {"sectors": SECTORS, "count": len(SECTORS), "highest_opportunity": HIGHEST_OPPORTUNITY}


def segments(sector_key=None):
    if sector_key and sector_key in SEGMENTS:
        return {"sector": sector_key, "segments": SEGMENTS[sector_key]}
    flat = [s for segs in SEGMENTS.values() for s in segs]
    return {"segments": flat, "count": len(flat), "by_sector": {k: len(v) for k, v in SEGMENTS.items()}}


def _find_segment(q):
    ql = (q or "").lower().strip()
    if not ql:
        return None
    for segs in SEGMENTS.values():
        for s in segs:
            if s["key"] == ql or s["label"].lower() == ql:
                return s
    # loose contains
    for segs in SEGMENTS.values():
        for s in segs:
            if s["label"].lower() in ql or ql in s["label"].lower():
                return s
    return None


def lookup(body):
    """business_type / sector / free-text -> a full intelligence card + next steps."""
    body = body or {}
    bt = (body.get("business_type") or body.get("segment") or "").strip()
    sector_key = (body.get("sector") or "").strip()
    desc = (body.get("description") or "").strip()

    seg = _find_segment(bt) or _find_segment(desc)
    sector = None
    if seg:
        sector = _SECTOR_BY_KEY.get(seg["sector"])
    if not sector and sector_key in _SECTOR_BY_KEY:
        sector = _SECTOR_BY_KEY[sector_key]
    if not sector and (desc or bt) and _M:
        try:
            ind = _M.classify_business(desc or bt).get("industry", "")
            alias = {"d2c": "retail", "tech_saas": "it_services", "services": "professional_services",
                     "agro_export": "agri_allied", "food_bev": "food_processing"}
            sector = _SECTOR_BY_KEY.get(alias.get(ind, ind))
        except Exception:
            pass
    if not sector:
        sector = _SECTOR_BY_KEY["retail"]

    playbook = None
    if _PB:
        try:
            playbook = _PB.match_playbook(seg["label"] if seg else (desc or sector["name"]))
        except Exception:
            playbook = None

    sample = _sample_for(seg, sector) if seg else {
        "description": f"{sector['name']} MSME in India facing {', '.join(sector['key_risks'][:2]).lower()}; wants a diagnostic and 90-day plan.",
        "intake": {"sector": sector["name"], "top_challenges": ", ".join(sector["key_risks"][:3])}}

    return {
        "business_type": seg["label"] if seg else sector["name"],
        "segment": seg,
        "sector": {k: sector[k] for k in ("key", "name", "icon", "market_value", "msme_presence", "avg_revenue",
                                          "top_revenue", "ebitda", "cagr", "export_potential", "ai_opportunity",
                                          "gross_margin", "key_risks", "key_kpis", "erp_modules")},
        "benchmarks": _benchmarks(sector),
        "recommended_agents": _agents(sector),
        "playbook_key": playbook,
        "next_steps": [
            {"label": "Run a full engagement", "action": "engage", "sample": sample},
            {"label": "See the industry playbook", "action": "playbook", "key": playbook},
            {"label": "Find government schemes", "action": "schemes"},
            {"label": "Talk to a specialist advisor", "action": "advisor", "agent": (sector["agents"][0] if sector.get("agents") else None)},
        ],
        "sample_engagement": sample,
        "disclaimer": "Industry-level estimates / consulting benchmarks (India does not publish MSME revenue by every "
                      "business type). Use as directional context, not audited figures.",
    }


def meta():
    return {"sectors": len(SECTORS), "segments": sum(len(v) for v in SEGMENTS.values()),
            "fields": ["market_value", "msme_presence", "avg_revenue", "top_revenue", "ebitda", "cagr",
                       "export_potential", "ai_opportunity", "gross_margin", "wc/inv/ar/ap days",
                       "key_risks", "key_kpis", "erp_modules", "recommended_agents", "playbook", "sample_engagement"],
            "endpoints": ["GET /market/sectors", "GET /market/segments", "POST /market/lookup", "GET /market/meta"]}


def run_market_tests():
    cases = []
    cases.append(("sectors", len(SECTORS) >= 12 and all(s.get("market_value") and s.get("ebitda") for s in SECTORS)))
    cases.append(("segments", sum(len(v) for v in SEGMENTS.values()) >= 35 and all("sector" in s for v in SEGMENTS.values() for s in v)))
    lk = lookup({"business_type": "Kirana Store"})
    cases.append(("lookup_segment", lk["sector"]["key"] == "retail" and bool(lk["recommended_agents"]) and bool(lk["sample_engagement"]["description"])))
    lk2 = lookup({"description": "we run an auto components manufacturing unit"})
    cases.append(("lookup_freetext", lk2["sector"]["key"] in ("manufacturing",) and len(lk2["next_steps"]) >= 3))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    import json
    print(json.dumps(run_market_tests(), indent=2))
