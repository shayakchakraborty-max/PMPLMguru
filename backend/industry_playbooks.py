"""
industry_playbooks.py — INDUSTRY PLAYBOOK ENGINE for the AI-native MSME
Consulting & Advisory OS.

Philosophy (same as msme_agents.py): deterministic, self-contained, no runtime
deps, India-aware, always sub-second, never a 500. The 30 priority business-type
playbooks live as data in `industry_playbooks.json` (generated research-grade
content); this module loads, validates, matches and serves them.

Each playbook is a 13-part operating blueprint:
  operating_model, workflow_architecture, department_structure,
  operational_bottlenecks, ai_automation_opportunities, consulting_frameworks,
  risk_model, kpi_structure, profitability_analysis, pm_workflows,
  product_service_lifecycle, growth_playbook, digital_maturity_model
plus compliance_keys + citations that point at the REAL Indian-statute citation
library in msme_agents.CITATIONS — so every claim stays traceable.
"""

import json
import os

# Reuse the citation library + classifier from the agent layer. Optional so this
# module still loads standalone (citations just won't resolve to full refs).
try:
    import msme_agents as M
except Exception:  # pragma: no cover
    M = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_PATH = os.path.join(_HERE, "industry_playbooks.json")


# ============================================================
# 1. THE PLAYBOOK CONTRACT — the 13 parts every playbook holds
# ============================================================
PLAYBOOK_SECTIONS = [
    {"key": "operating_model",            "label": "Operating Model",            "icon": "🧩"},
    {"key": "workflow_architecture",      "label": "Workflow Architecture",      "icon": "🔗"},
    {"key": "department_structure",       "label": "Department Structure",       "icon": "🏛️"},
    {"key": "operational_bottlenecks",    "label": "Operational Bottlenecks",    "icon": "🚧"},
    {"key": "ai_automation_opportunities","label": "AI Automation Opportunities","icon": "🤖"},
    {"key": "consulting_frameworks",      "label": "Consulting Frameworks",      "icon": "📐"},
    {"key": "risk_model",                 "label": "Risk Model",                 "icon": "⚠️"},
    {"key": "kpi_structure",              "label": "KPI Structure",              "icon": "📊"},
    {"key": "profitability_analysis",     "label": "Profitability Analysis",     "icon": "💰"},
    {"key": "pm_workflows",               "label": "PM Workflows",               "icon": "🗂️"},
    {"key": "product_service_lifecycle",  "label": "Product / Service Lifecycle","icon": "🔄"},
    {"key": "growth_playbook",            "label": "Growth Playbook",            "icon": "🚀"},
    {"key": "digital_maturity_model",     "label": "Digital Maturity Model",     "icon": "📶"},
]
_SECTION_KEYS = [s["key"] for s in PLAYBOOK_SECTIONS]

TIERS = {
    1: "Tier 1 — Highest revenue / strategic priority",
    2: "Tier 2 — High priority",
    3: "Tier 3 — Broad coverage",
}


# ============================================================
# 2. MATCH KEYWORDS — free-text business -> the right playbook
# ============================================================
# Mirrors the classify hints used to generate each playbook. Deterministic,
# scored against the business description so /playbook can take plain text.
_MATCH_KEYWORDS = {
    "retail_chains":               ["retail chain", "multi-branch", "supermarket", "hypermarket", "grocery", "kirana", "pos", "showroom", "store chain"],
    "wholesale_distribution":      ["wholesale", "distributor", "stockist", "c&f", "secondary sales", "redistribution", "super stockist"],
    "pharma_retail_distribution":  ["pharma", "chemist", "medical store", "medicine", "drug", "schedule h", "pharmacy", "surgical"],
    "manufacturing_msme":          ["manufactur", "factory", "production", "bom", "wip", "machining", "assembly", "fabrication", "molding", "processing unit"],
    "fmcg_distribution":           ["fmcg", "beat", "super stockist", "consumer goods distribution"],
    "agro_trading":                ["agro", "mandi", "commodity", "spices", "rice", "grain", "pulses", "turmeric", "garlic", "makhana", "apeda", "agri trading"],
    "export_import":               ["import", "export", "merchant export", "iec", "customs", "bill of entry", "icegate", "sourcing", "cross-border"],
    "logistics_warehousing":       ["logistics", "transport", "trucking", "fleet", "freight", "warehouse", "cold chain", "last mile", "courier", "cargo"],
    "d2c_brands":                  ["d2c", "ecommerce", "e-commerce", "shopify", "amazon", "flipkart", "ad spend", "cac", "quick commerce", "direct to consumer"],
    "construction_infra_suppliers":["construction", "builder", "civil contractor", "infrastructure", "building material", "contractor"],
    "restaurants_cloud_kitchens":  ["restaurant", "cloud kitchen", "cafe", "catering", "tiffin", "qsr", "food outlet", "dine"],
    "healthcare_clinics":          ["clinic", "hospital", "diagnostic", "lab", "telemedicine", "nabh", "healthcare", "doctor"],
    "real_estate":                 ["real estate", "property", "brokerage", "rental management", "rera", "co-working", "facility management"],
    "saas_startups":               ["saas", "software", "platform", "app", "api", "arr", "mvp", "ai startup", "tech startup", "subscription software"],
    "professional_services":       ["agency", "consult", "it services", "staffing", "marketing", "bpo", "kpo", "professional service"],
    "legal_firms":                 ["law firm", "legal", "advocate", "litigation", "attorney", "counsel"],
    "ca_firms":                    ["ca firm", "chartered accountant", "audit firm", "tax consultant", "accounting firm", "bookkeeping"],
    "education_institutes":        ["coaching", "school", "edtech", "skill training", "test prep", "vocational", "institute", "tuition"],
    "textile_businesses":          ["textile", "garment", "fabric", "yarn", "weaving", "handloom", "apparel manufactur", "spinning"],
    "electronics_distribution":    ["electronics distribution", "mobile distribution", "gadget", "consumer electronics", "electronics dealer"],
    "automotive_workshops":        ["automotive", "workshop", "garage", "vehicle repair", "auto spares", "car service", "two wheeler service"],
    "printing_packaging":          ["printing", "packaging", "press", "carton", "label", "corrugated", "flexo", "offset"],
    "beauty_wellness":             ["beauty", "salon", "spa", "wellness", "cosmetic service", "grooming"],
    "furniture_businesses":        ["furniture", "woodwork", "carpentry", "modular", "interior furnishing"],
    "hardware_stores":             ["hardware store", "paint shop", "electrical shop", "building material retail", "sanitary"],
    "stationery_chains":           ["stationery", "books retail", "gifts", "office supplies"],
    "repair_service":              ["repair", "appliance service", "maintenance", "after-sales", "service center"],
    "event_businesses":            ["event", "wedding", "decor", "event management", "exhibition", "mice"],
    "travel_agencies":             ["travel agency", "tour operator", "ticketing", "holiday package", "tourism"],
    "local_service_msme":          ["local service", "neighbourhood", "small shop", "proprietor", "local business"],
}

# Fallback: classify_business industry -> a representative playbook key.
_INDUSTRY_TO_PLAYBOOK = {
    "pharma": "pharma_retail_distribution",
    "retail": "retail_chains",
    "wholesale": "wholesale_distribution",
    "manufacturing": "manufacturing_msme",
    "agro_export": "agro_trading",
    "import_export": "export_import",
    "logistics": "logistics_warehousing",
    "construction": "construction_infra_suppliers",
    "healthcare": "healthcare_clinics",
    "food_bev": "restaurants_cloud_kitchens",
    "education": "education_institutes",
    "d2c": "d2c_brands",
    "tech_saas": "saas_startups",
    "services": "professional_services",
}


# ============================================================
# 3. LOAD
# ============================================================
def _load():
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("playbooks", data) if isinstance(data, dict) else data
        return {p["key"]: p for p in items if isinstance(p, dict) and p.get("key")}
    except Exception as e:  # pragma: no cover
        print(f"[industry_playbooks] could not load {_DATA_PATH}: {e}", flush=True)
        return {}


PLAYBOOKS = _load()


# ============================================================
# 4. CITATION RESOLUTION
# ============================================================
def _resolve_citations(keys):
    """Resolve citation keys -> full reference dicts via msme_agents.CITATIONS."""
    out, seen = [], set()
    cites = getattr(M, "CITATIONS", {}) if M else {}
    for k in (keys or []):
        if k in seen:
            continue
        seen.add(k)
        if k in cites:
            out.append({"key": k, **cites[k]})
        else:
            out.append({"key": k, "title": k, "tier": "C"})
    return out


# ============================================================
# 5. PUBLIC API
# ============================================================
def list_playbooks():
    """Lightweight cards for /playbooks/meta, sorted by tier then name."""
    cards = []
    for k, p in PLAYBOOKS.items():
        cards.append({
            "key": k,
            "name": p.get("name", k),
            "tier": p.get("tier", 3),
            "icon": p.get("icon", "📁"),
            "one_liner": p.get("one_liner", ""),
        })
    cards.sort(key=lambda c: (c.get("tier", 9), c.get("name", "")))
    return cards


def get_playbook(key):
    """Full playbook with citations + compliance resolved to traceable refs."""
    p = PLAYBOOKS.get(key)
    if not p:
        return None
    out = dict(p)
    out["tier_label"] = TIERS.get(p.get("tier"), "")
    out["citations_resolved"] = _resolve_citations(p.get("citations"))
    out["compliance_resolved"] = _resolve_citations(p.get("compliance_keys"))
    out["sections"] = PLAYBOOK_SECTIONS
    return out


def match_playbook(description):
    """Map a free-text business description to the best-fit playbook key.
    Scores keyword hits; falls back to the classifier's industry."""
    d = (description or "").lower().strip()
    if not d:
        return None
    best_key, best_score = None, 0
    for key, kws in _MATCH_KEYWORDS.items():
        if key not in PLAYBOOKS:
            continue
        score = sum(len(kw) for kw in kws if kw in d)  # weight longer phrases
        if score > best_score:
            best_score, best_key = score, key
    if best_key:
        return best_key
    # Fallback via the MSME classifier.
    if M and hasattr(M, "classify_business"):
        ind = M.classify_business(d).get("industry")
        cand = _INDUSTRY_TO_PLAYBOOK.get(ind)
        if cand in PLAYBOOKS:
            return cand
    return None


def resolve(business_type=None, key=None, description=None):
    """One-call resolver used by the HTTP handler. Returns (playbook, matched_key, how)."""
    if key and key in PLAYBOOKS:
        return get_playbook(key), key, "key"
    if business_type and business_type in PLAYBOOKS:
        return get_playbook(business_type), business_type, "key"
    if description:
        mk = match_playbook(description)
        if mk:
            return get_playbook(mk), mk, "matched"
    return None, None, "none"


# ============================================================
# 6. VALIDATION + SELF-TEST
# ============================================================
def _validate(p):
    """Return list of problems with a single playbook (used by tests)."""
    problems = []
    for sk in _SECTION_KEYS:
        v = p.get(sk)
        if v in (None, "", [], {}):
            problems.append(f"missing/empty section: {sk}")
    # citation keys must resolve to the real library
    cites = getattr(M, "CITATIONS", {}) if M else {}
    if cites:
        for ck in (p.get("citations") or []):
            if ck not in cites:
                problems.append(f"unknown citation key: {ck}")
        for ck in (p.get("compliance_keys") or []):
            if ck not in cites:
                problems.append(f"unknown compliance key: {ck}")
    # automation agent references should point at real agents
    agents = set(getattr(M, "MSME_AGENTS", {}).keys()) if M else set()
    if agents:
        for opp in (p.get("ai_automation_opportunities") or []):
            a = (opp or {}).get("agent")
            if a and a not in agents:
                problems.append(f"unknown automation agent ref: {a}")
    # digital maturity must be 5 ascending levels
    dm = p.get("digital_maturity_model") or []
    if len(dm) != 5:
        problems.append(f"digital_maturity_model has {len(dm)} levels (want 5)")
    return problems


def run_playbook_tests():
    """Validate every playbook; mirrors msme_agents.run_agent_tests() shape."""
    results, passed = [], 0
    for key, p in PLAYBOOKS.items():
        problems = _validate(p)
        ok = not problems
        passed += 1 if ok else 0
        results.append({"key": key, "name": p.get("name", key), "tier": p.get("tier"),
                        "pass": ok, "problems": problems})
    total = len(PLAYBOOKS)
    by_tier = {}
    for p in PLAYBOOKS.values():
        by_tier[p.get("tier", 0)] = by_tier.get(p.get("tier", 0), 0) + 1
    return {
        "total_playbooks": total,
        "passed": passed,
        "failed": total - passed,
        "by_tier": by_tier,
        "deployment_ready": total > 0 and passed == total,
        "results": results,
    }


def meta():
    """Everything the frontend needs to render the command center."""
    return {
        "playbooks": list_playbooks(),
        "sections": PLAYBOOK_SECTIONS,
        "tiers": TIERS,
        "total": len(PLAYBOOKS),
    }


if __name__ == "__main__":  # quick local check
    print(json.dumps(run_playbook_tests(), indent=2)[:2000])
