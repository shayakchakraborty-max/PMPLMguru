"""
MSME Situation Simulation Library
=================================
Research-grade, scale-wise situations for every in-scope Indian MSME business
type — 100+ per type — so the agent crew can match a real situation instantly
(swift, deterministic) and respond end-to-end, from bootstrap to international.

Each situation = stage × challenge, mapped to the MSME agents that resolve it.
match(text) classifies the business + scale stage and returns the most relevant
situations + the recommended agent crew.
"""
try:
    import msme_agents as M
except Exception:
    M = None

# Five scale stages every business moves through.
SCALE_STAGES = [
    "Bootstrap / Idea",
    "Early (0-1 yr)",
    "Growth (1-3 yr)",
    "Scale (3-5 yr)",
    "International / Export",
]

# Generic challenges that apply to (almost) every business, mapped to agents.
# (title, detail, [agent keys])
_GENERIC = [
    ("Capital & funding", "decide bootstrap vs raise; build an 18-month plan", ["cfo_finance", "investor_readiness"]),
    ("Working capital & cash flow", "13-week cash forecast; receivables and payables discipline", ["cfo_finance"]),
    ("GST setup & filing", "registration, e-invoicing thresholds, monthly returns, ITC", ["gst_compliance"]),
    ("Statutory compliance", "Udyam, DPIIT, ROC, EPF/ESI, sector licences calendar", ["gst_compliance", "legal_contracts"]),
    ("Sourcing & procurement", "vendor selection, 3-way match, rate contracts, MSME 45-day", ["procurement_agent"]),
    ("Inventory & quality", "ABC analysis, reorder points, ageing, dead stock, QC", ["inventory_agent"]),
    ("Distribution & channel", "DTC vs marketplace vs distributor; channel economics", ["sales_gtm"]),
    ("Pricing & margins", "price list governance, discounts, contribution margin", ["cfo_finance", "sales_gtm"]),
    ("Brand & customer acquisition", "positioning, CAC, content, performance marketing", ["market_research", "sales_gtm"]),
    ("Customer retention & support", "SLAs, NPS, returns handling, repeat-purchase", ["customer_support"]),
    ("Hiring & payroll", "first key hires, salary structure, PF/ESI/TDS", ["hr_payroll"]),
    ("Tech & ERP", "system of record, automation, build-vs-buy", ["erp_consultant", "product_manager"]),
    ("Operations & cycle time", "process map, bottlenecks, SOPs, throughput", ["coo_operations", "sop_agent"]),
    ("Risk, fraud & controls", "segregation of duties, maker-checker, audit trail", ["risk_audit"]),
    ("Competitive positioning", "competitor teardown, white space, moat", ["competitor_intel"]),
    ("Market sizing", "TAM/SAM/SOM, beachhead, demand signals", ["market_research"]),
    ("Investor / lender readiness", "data room, metrics, red-flag clean-up", ["investor_readiness", "msme_due_diligence"]),
    ("Legal & contracts", "founder/vendor/customer agreements, IP, stamping", ["legal_contracts"]),
    ("Unit economics", "LTV:CAC, payback, gross margin, break-even", ["cfo_finance"]),
    ("Strategy & priorities", "3 priorities, OKRs, weekly operating cadence", ["ceo_copilot"]),
    ("Working with marketplaces", "Amazon/Flipkart/ONDC listing, fees, margin leakage", ["sales_gtm"]),
    ("Vendor / buyer due diligence", "credit checks, KYC, payment terms (LC/advance)", ["msme_due_diligence"]),
]

# Sector-specific challenges keyed to the classify_business industry buckets.
_SECTOR = {
    "food_bev": [
        ("FSSAI licensing", "registration/licence by turnover slab, labelling, hygiene", ["gst_compliance", "legal_contracts"]),
        ("Cold chain & shelf life", "temperature control, spoilage, batch & expiry (FEFO)", ["inventory_agent"]),
        ("Farm-gate / mandi sourcing", "procurement from farmers/mandis, grading, price volatility", ["procurement_agent"]),
        ("Processing & packaging", "drying/grinding/packing lines, BOM, costing", ["coo_operations", "erp_consultant"]),
        ("Export incentives (APEDA/RoDTEP)", "APEDA registration, RoDTEP/drawback, phytosanitary certs", ["export_compliance"]),
        ("International buyer development", "buyer DD, samples, FSSAI/importing-country norms", ["export_compliance", "sales_gtm"]),
    ],
    "agro_export": [
        ("APEDA & RCMC", "RCMC, scheduled-product norms, quality certificates", ["export_compliance"]),
        ("Farm-gate sourcing", "contract farming, grading, drying yield, price hedging", ["procurement_agent"]),
        ("Export documentation", "IEC, LUT, shipping bill, eBRC, RoDTEP/drawback", ["export_compliance"]),
        ("Phytosanitary & quality", "phytosanitary cert, residue/aflatoxin limits, lab tests", ["export_compliance", "inventory_agent"]),
        ("International logistics", "container/freight, Incoterms, demurrage control", ["procurement_agent"]),
        ("Global buyer due diligence", "verify buyer, LC/advance, ECGC cover", ["msme_due_diligence"]),
    ],
    "import_export": [
        ("Customs & Bill of Entry", "BCD+IGST+cess, ICEGATE, IGST credit", ["export_compliance"]),
        ("BIS/QCO on imports", "mandatory certification for notified goods", ["export_compliance"]),
        ("FX exposure", "hedging payables/receivables, FEMA timelines", ["cfo_finance"]),
        ("Merchant export model", "sourcing, RCMC, incentive capture", ["export_compliance", "procurement_agent"]),
    ],
    "pharma": [
        ("Drug licence & Schedule H", "Form 20/21, Schedule H/H1 records", ["legal_contracts", "gst_compliance"]),
        ("Batch & expiry (FEFO)", "near-expiry returns, recall readiness", ["inventory_agent"]),
        ("Cold-chain integrity", "temperature logging, wastage control", ["inventory_agent"]),
    ],
    "manufacturing": [
        ("Factory licence & safety", "Factories Act, layout, worker norms", ["legal_contracts"]),
        ("BOM & production planning", "WIP, capacity, costing, scrap", ["coo_operations", "erp_consultant"]),
        ("Vendor performance (OTIF)", "raw-material reliability, multi-sourcing", ["procurement_agent"]),
    ],
    "retail": [
        ("POS & GST billing", "fast billing, HSN, daily cash reconciliation", ["gst_compliance"]),
        ("Dead stock & assortment", "ageing, reorder, planogram", ["inventory_agent"]),
        ("Quick/Q-commerce", "marketplace + 10-min delivery economics", ["sales_gtm"]),
    ],
    "wholesale": [
        ("Beat planning & secondary sales", "route clusters, outlet coverage, range selling", ["sales_gtm"]),
        ("Dealer outstanding & credit", "credit limits, dunning, scheme control", ["cfo_finance"]),
        ("Distributor margin analysis", "margin leakage, claims, returns", ["cfo_finance", "sales_gtm"]),
    ],
    "tech_saas": [
        ("DPIIT & startup benefits", "80-IAC tax holiday, angel-tax, SISFS", ["investor_readiness", "gst_compliance"]),
        ("ARR & retention quality", "NRR, churn, cohort analysis", ["cfo_finance", "product_manager"]),
        ("IP & data (DPDP)", "IP assignment, DPDP Act readiness", ["legal_contracts"]),
        ("SaaS export (services)", "LUT, eBRC, FEMA for software exports", ["export_compliance"]),
    ],
    "d2c": [
        ("Marketplace margin leakage", "fees, returns, ad spend ROI", ["sales_gtm", "cfo_finance"]),
        ("Cohort & retention", "repeat rate, LTV, subscription", ["product_manager", "customer_support"]),
        ("Cross-border D2C", "international shipping, duties, marketplaces", ["export_compliance"]),
    ],
    "logistics": [
        ("Fleet & route optimization", "utilization, last-mile cost, cold chain", ["coo_operations"]),
        ("CHA & freight forwarding", "customs broking, documentation", ["export_compliance"]),
    ],
    "services": [
        ("Lead-to-cash & billing leakage", "utilization, SLA, billing accuracy", ["coo_operations", "cfo_finance"]),
        ("Client profitability", "project margins, scope creep", ["cfo_finance"]),
    ],
    "healthcare": [
        ("NABH & clinical compliance", "accreditation, records, insurer empanelment", ["legal_contracts", "risk_audit"]),
    ],
    "construction": [
        ("RERA & project finance", "registration, escrow, milestone billing", ["legal_contracts", "cfo_finance"]),
    ],
    "education": [
        ("Content, counselors & CAC", "performance marketing, counselor sales", ["sales_gtm"]),
    ],
}

# Stage-specific lens that sharpens every situation.
_STAGE_LENS = {
    "Bootstrap / Idea": "validate cheaply, conserve cash, do it founder-led",
    "Early (0-1 yr)": "get the first repeatable customers and clean books",
    "Growth (1-3 yr)": "make the motion repeatable and hire to it",
    "Scale (3-5 yr)": "multi-state ops, functional leadership, raise if needed",
    "International / Export": "IEC + export docs, incentives, buyer due diligence, FX",
}


def _situations_for(industry: str) -> list:
    challenges = _GENERIC + _SECTOR.get(industry, [])
    out = []
    n = 1
    for stage in SCALE_STAGES:
        lens = _STAGE_LENS[stage]
        for title, detail, agents in challenges:
            out.append({
                "id": f"{industry}-{n}",
                "business_type": industry,
                "stage": stage,
                "challenge": title,
                "situation": f"[{stage}] {title}: {detail} — {lens}.",
                "agents": agents,
            })
            n += 1
    return out


# Build the whole library at import (pure dict-building — fast).
_INDUSTRIES = ["food_bev", "agro_export", "import_export", "pharma", "manufacturing",
               "retail", "wholesale", "tech_saas", "d2c", "logistics", "services",
               "healthcare", "construction", "education"]
LIBRARY = {ind: _situations_for(ind) for ind in _INDUSTRIES}
TOTAL = sum(len(v) for v in LIBRARY.values())
PER_TYPE = {ind: len(v) for ind, v in LIBRARY.items()}


def _detect_stage(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ("export", "international", "abroad", "overseas", "global", "import")):
        return "International / Export"
    if any(k in t for k in ("scale", "multi-state", "pan-india", "series a", "series b")):
        return "Scale (3-5 yr)"
    if any(k in t for k in ("grow", "expand", "growing", "scaling up")):
        return "Growth (1-3 yr)"
    if any(k in t for k in ("new ", "start", "starting", "bootstrap", "idea", "launch", "pre-revenue", "mvp")):
        return "Bootstrap / Idea"
    return "Early (0-1 yr)"


def match(text: str, top: int = 12) -> dict:
    """Classify the business + scale stage, return the most relevant situations
    and the recommended agent crew."""
    industry = "services"
    if M:
        try:
            industry = M.classify_business(text).get("industry", "services")
        except Exception:
            pass
    tl = (text or "").lower()
    _agro = any(w in tl for w in ("garlic", "turmeric", "chilli", "chili", "spice", "dried", "dehydrat", "agro", "mandi", "grain", "pulses", "makhana", "beetroot", "onion"))
    _food = any(w in tl for w in ("food", "snack", "bakery", "dairy", "beverage", "frozen", "ready to eat"))
    _intl = any(w in tl for w in ("export", "international", "abroad", "overseas", "global"))
    # Route clearly agro/food businesses correctly even if the base classifier guessed generically.
    if industry in ("services", "retail", "wholesale", "manufacturing") and (_agro or _food):
        industry = "agro_export" if (_agro and _intl) else ("food_bev" if _food else "agro_export")
    if industry not in LIBRARY:
        industry = "food_bev" if _food or _agro else "services"
    stage = _detect_stage(text)
    pool = LIBRARY.get(industry, [])

    t = (text or "").lower()
    words = set(w for w in t.replace("/", " ").replace(",", " ").split() if len(w) > 3)

    def score(s):
        sc = 0
        if s["stage"] == stage:
            sc += 5
        # international plan should also surface the export situations
        if stage == "International / Export" and s["stage"] in ("Scale (3-5 yr)", "Growth (1-3 yr)"):
            sc += 1
        # when going international, prioritise export/customs situations
        if _intl and "export_compliance" in s["agents"]:
            sc += 4
        blob = (s["challenge"] + " " + s["situation"]).lower()
        sc += sum(1 for w in words if w in blob)
        return sc

    ranked = sorted(pool, key=score, reverse=True)[:top]
    crew, seen = [], set()
    for s in ranked:
        for a in s["agents"]:
            if a not in seen:
                seen.add(a); crew.append(a)
    return {
        "business_type": industry,
        "stage": stage,
        "matched": ranked,
        "crew": crew,
        "library_size_for_type": len(pool),
        "total_situations": TOTAL,
    }


if __name__ == "__main__":
    print("Total situations:", TOTAL)
    print("Per type:", PER_TYPE)
    r = match("New food company dealing with dried garlic, turmeric, chilli, tomato, beetroot — grow in India then export internationally")
    print("\nExample match:", r["business_type"], "|", r["stage"], "| crew:", r["crew"][:8])
    for s in r["matched"][:5]:
        print("  -", s["situation"])
