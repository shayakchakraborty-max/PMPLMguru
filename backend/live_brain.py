"""
live_brain.py — the AI-NATIVE CONSULTING BRAIN.

Turns a structured business intake (a FORM, not a one-liner) into a *customised*
consulting engagement. Unlike the static playbooks, every answer is shaped by the
specific inputs and is grounded on three retrieval sources, then synthesised:

  1. PLAYBOOK grounding   — the matched 13-part sector blueprint (industry_playbooks)
  2. OPEN-SOURCE search   — keyless DuckDuckGo + Wikipedia snippets (live web)
  3. MEMORY recall        — similar past engagements from a persistent learning log

  -> SYNTHESIS            — Groq LLM (llm_stack) when a key exists; ALWAYS with a
                            deterministic, input-personalised fallback so it never
                            fails and never returns the same thing for two different
                            businesses.

  -> LEARN                — every engagement is appended to the learning log, so the
                            brain evolves: future prompts recall what was seen before.

Design rule (same as the rest of the codebase): never raise, always return a
complete uniform envelope, sub-second when keyless.
"""

import os
import re
import json
import time
import hashlib
import urllib.parse

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None

try:
    import industry_playbooks as PB
except Exception:  # pragma: no cover
    PB = None

try:
    import msme_agents as M
except Exception:  # pragma: no cover
    M = None

try:
    import llm_stack as LLM
except Exception:  # pragma: no cover
    LLM = None

try:
    import doc_store as DOCS
except Exception:  # pragma: no cover
    DOCS = None


# ============================================================
# 1. INTAKE FORM — what we capture to personalise the engagement
# ============================================================
# Drives the multi-step frontend form. `group` = wizard step; `modes` = visibility.
# This is the end-to-end due-diligence intake — the inputs a real consultant would
# ask for before diagnosing, organised so the form feels like a guided DD interview.
INTAKE_GROUPS = [
    {"key": "profile",    "label": "Business Profile",   "icon": "🏢", "blurb": "Who you are and what you do."},
    {"key": "financial",  "label": "Financial DD",       "icon": "💰", "blurb": "Revenue, margins, cash and collections."},
    {"key": "operations", "label": "Operations DD",      "icon": "⚙️", "blurb": "Systems, SOPs, inventory and workflow maturity."},
    {"key": "chain",      "label": "Supply Chain & Sales","icon": "🔗", "blurb": "Vendors, procurement, customers and concentration."},
    {"key": "compliance", "label": "Compliance DD",      "icon": "🏛️", "blurb": "GST, returns and licences."},
    {"key": "focus",      "label": "Your Focus",         "icon": "🎯", "blurb": "The questions and goals that matter most to you."},
]

INTAKE_FIELDS = [
    # --- Profile ---
    {"key": "description",      "group": "profile", "label": "Describe your business",           "type": "textarea", "ph": "e.g. 8-store grocery retail chain in Pune buying from FMCG distributors", "modes": ["startup", "existing"], "required": True},
    {"key": "business_type",    "group": "profile", "label": "Sector (auto-detected, editable)", "type": "playbook", "ph": "", "modes": ["startup", "existing"]},
    {"key": "stage",            "group": "profile", "label": "Stage",                            "type": "select",   "options_startup": ["idea", "pre-seed", "seed", "series-a", "early-revenue"], "options_existing": ["just-started", "growing", "established", "scaling", "turnaround"], "modes": ["startup", "existing"]},
    {"key": "city_tier",        "group": "profile", "label": "Primary market",                   "type": "select",   "options": ["Metro", "Tier-1", "Tier-2", "Tier-3", "Pan-India", "Export"], "modes": ["startup", "existing"]},
    {"key": "employees",        "group": "profile", "label": "Team size",                        "type": "number",   "ph": "24", "modes": ["startup", "existing"]},
    {"key": "years_operating",  "group": "profile", "label": "Years operating",                  "type": "number",   "ph": "6", "modes": ["existing"]},
    # --- Financial DD ---
    {"key": "turnover_cr",      "group": "financial", "label": "Annual turnover (₹ cr)",         "type": "number", "ph": "8",  "modes": ["existing"]},
    {"key": "target_raise_cr",  "group": "financial", "label": "Target raise (₹ cr)",            "type": "number", "ph": "2",  "modes": ["startup"]},
    {"key": "gross_margin_pct", "group": "financial", "label": "Gross margin (%)",               "type": "number", "ph": "18", "modes": ["startup", "existing"]},
    {"key": "net_margin_pct",   "group": "financial", "label": "Net margin (%)",                 "type": "number", "ph": "6",  "modes": ["startup", "existing"]},
    {"key": "receivables_cr",   "group": "financial", "label": "Receivables outstanding (₹ cr)", "type": "number", "ph": "2",  "modes": ["existing"]},
    {"key": "dso_days",         "group": "financial", "label": "Collection period / DSO (days)", "type": "number", "ph": "75", "modes": ["existing"]},
    {"key": "cash_runway_months","group": "financial","label": "Cash runway (months)",           "type": "number", "ph": "9",  "modes": ["startup", "existing"]},
    # --- Operations DD ---
    {"key": "systems_used",     "group": "operations", "label": "Systems you run on",            "type": "select", "options": ["Pen & paper", "Excel/Sheets", "WhatsApp + Excel", "Tally", "Tally + Excel", "An ERP", "Mixed"], "modes": ["startup", "existing"]},
    {"key": "has_sops",         "group": "operations", "label": "Documented SOPs exist?",        "type": "select", "options": ["No", "A few", "Mostly", "Yes - followed"], "modes": ["startup", "existing"]},
    {"key": "owner_dependency", "group": "operations", "label": "How owner-dependent are ops?",  "type": "select", "options": ["Totally - I do everything", "High", "Medium", "Low - team runs it"], "modes": ["startup", "existing"]},
    {"key": "inventory_value_cr","group": "operations","label": "Inventory value (₹ cr)",        "type": "number", "ph": "3", "modes": ["existing"]},
    {"key": "dead_stock_pct",   "group": "operations", "label": "Dead / slow stock (%)",         "type": "number", "ph": "12", "modes": ["existing"]},
    # --- Supply Chain & Sales ---
    {"key": "procurement_method","group": "chain", "label": "How you procure",                   "type": "select", "options": ["Single supplier", "Few suppliers", "Open market", "Imports", "Mixed"], "modes": ["startup", "existing"]},
    {"key": "top_supplier_dep_pct","group": "chain","label": "Top supplier dependence (%)",      "type": "number", "ph": "40", "modes": ["existing"]},
    {"key": "top_customer_dep_pct","group": "chain","label": "Top customer dependence (%)",      "type": "number", "ph": "25", "modes": ["startup", "existing"]},
    {"key": "repeat_rate_pct",  "group": "chain", "label": "Repeat-customer rate (%)",           "type": "number", "ph": "45", "modes": ["startup", "existing"]},
    {"key": "has_crm",          "group": "chain", "label": "Use a CRM / customer database?",     "type": "select", "options": ["No", "Spreadsheet", "WhatsApp only", "Yes - a CRM"], "modes": ["startup", "existing"]},
    # --- Compliance DD ---
    {"key": "gst_registered",   "group": "compliance", "label": "GST registered?",               "type": "select", "options": ["Yes", "No", "Not sure"], "modes": ["startup", "existing"]},
    {"key": "returns_current",  "group": "compliance", "label": "GST/IT returns up to date?",    "type": "select", "options": ["Yes", "Mostly", "Behind", "Not sure"], "modes": ["existing"]},
    {"key": "licences_current", "group": "compliance", "label": "Sector licences current?",      "type": "select", "options": ["Yes", "Some pending", "No", "Not sure"], "modes": ["startup", "existing"]},
    # --- Focus ---
    {"key": "specific_question","group": "focus", "label": "Your #1 question right now",         "type": "textarea", "ph": "e.g. How do I cut working-capital lock without losing sales?", "modes": ["startup", "existing"]},
    {"key": "top_challenges",   "group": "focus", "label": "Top challenges (one per line)",      "type": "textarea", "ph": "thin margins\nstockouts\nstaff churn", "modes": ["startup", "existing"]},
    {"key": "goals",            "group": "focus", "label": "Goal for next 6-12 months",          "type": "text",     "ph": "e.g. double revenue, raise seed, open 3 stores", "modes": ["startup", "existing"]},
]

_FIELD_KEYS = [f["key"] for f in INTAKE_FIELDS]


def intake_meta():
    """Form schema (grouped, multi-step) + sector list for the frontend."""
    return {
        "fields": INTAKE_FIELDS,
        "groups": INTAKE_GROUPS,
        "playbooks": PB.list_playbooks() if PB else [],
        "demos": demo_samples(),
        "lenses": LENSES,
        "modes": [
            {"key": "startup", "label": "New / Startup", "icon": "🚀"},
            {"key": "existing", "label": "Existing Business", "icon": "🏢"},
        ],
    }


# Human-readable labels for the extended DD signals (used in prompts + diagnosis).
def _intake_summary_lines(intake):
    lines = []
    for f in INTAKE_FIELDS:
        v = intake.get(f["key"])
        if v not in (None, "", []):
            lines.append(f"- {f['label']}: {v}")
    # sector-specific KPI answers (kpi__*)
    for k, v in intake.items():
        if k.startswith("kpi__") and v not in (None, ""):
            lines.append(f"- {k.replace('kpi__','KPI ').replace('_',' ')}: {v}")
    return "\n".join(lines)


# ============================================================
# 1b. DEMO SCENARIOS — one live engagement per sector (for instant demos)
# ============================================================
# Each is a believable Indian-MSME situation with a real consulting trigger.
# The narrative + numbers are consistent so the brain's diagnosis lands hard.
_BIG = {"wholesale_distribution", "fmcg_distribution", "export_import", "electronics_distribution",
        "logistics_warehousing", "manufacturing_msme", "construction_infra_suppliers", "real_estate"}
_SMALL = {"local_service_msme", "repair_service", "beauty_wellness", "stationery_chains", "automotive_workshops",
          "ca_firms", "legal_firms", "travel_agencies", "event_businesses", "furniture_businesses",
          "hardware_stores", "restaurants_cloud_kitchens", "professional_services", "healthcare_clinics", "printing_packaging"}
_INVENTORY = {"retail_chains", "wholesale_distribution", "fmcg_distribution", "pharma_retail_distribution",
              "manufacturing_msme", "agro_trading", "electronics_distribution", "textile_businesses",
              "hardware_stores", "furniture_businesses", "stationery_chains", "d2c_brands", "printing_packaging"}
_CASH = {"retail_chains", "restaurants_cloud_kitchens", "beauty_wellness", "d2c_brands", "local_service_msme",
         "stationery_chains", "travel_agencies", "automotive_workshops"}

# Scenario lenses — each sector can be demoed through a different consulting situation.
LENSES = [
    {"key": "signature",  "label": "Signature situation", "icon": "📌"},
    {"key": "growth",     "label": "Growth & scale",      "icon": "📈"},
    {"key": "turnaround", "label": "Turnaround",          "icon": "🆘"},
    {"key": "fundraise",  "label": "Fundraise / capital", "icon": "💸"},
]

_SCEN = {
    "retail_chains": {"turnover_cr": 14, "gross_margin_pct": 14, "dead_stock_pct": 13, "dso_days": "",
        "description": "Sharma Mart runs 9 grocery stores across Pune & PCMC (~₹14 cr/yr). Footfall is steady but gross margin slipped to 14% after a quick-commerce player opened nearby, and 2 of the 9 stores are now loss-making.",
        "specific_question": "Should I shut the 2 weak stores or fix them, and how do I defend margins against quick-commerce?",
        "top_challenges": "2 of 9 stores loss-making\nmargin erosion from quick-commerce\nstockouts on fast-movers + dead stock on slow ones",
        "goals": "Open 3 more stores — but only after the core chain is healthy and margins recover."},
    "wholesale_distribution": {"turnover_cr": 32, "dso_days": 78, "receivables_cr": 4.5, "top_customer_dep_pct": 22,
        "description": "An FMCG sub-distributor in Nagpur (~₹32 cr/yr) servicing 1,800 outlets. Receivables have ballooned to ₹4.5 cr (DSO ~78 days) and the principal company keeps raising targets while margins stay thin.",
        "specific_question": "How do I bring DSO down and clear dead stock without losing retailer goodwill?",
        "top_challenges": "receivables stretched to ₹4.5 cr / 78-day DSO\nprincipal pushing targets on thin margins\nslow-moving SKUs blocking working capital",
        "goals": "Free up ₹1.5 cr of working capital and hit the principal's target profitably."},
    "pharma_retail_distribution": {"turnover_cr": 9, "dead_stock_pct": 9,
        "description": "A 6-store pharmacy chain with a small distribution arm in Jaipur (~₹9 cr). Expiry & breakage write-offs hit ₹35 lakh last year and Schedule-H register upkeep is messy ahead of an FDA visit.",
        "specific_question": "How do I stop expiry losses and get Schedule-H compliance audit-ready before the FDA inspection?",
        "top_challenges": "₹35 lakh expiry & breakage write-offs\nmessy Schedule-H record-keeping\nweak FEFO rotation across stores",
        "goals": "Halve expiry losses and pass the FDA inspection clean."},
    "manufacturing_msme": {"turnover_cr": 18, "top_customer_dep_pct": 55, "dso_days": 72,
        "description": "An auto-components machining unit in Pune (~₹18 cr) supplying 2 Tier-1 OEMs. On-time delivery is stuck at 82%, WIP is piling on the floor, and one OEM is 55% of sales.",
        "specific_question": "How do I lift OTIF above 95% and reduce my dangerous single-customer concentration?",
        "top_challenges": "OTIF only 82%\nWIP pile-up and long cycle time\none OEM = 55% of revenue",
        "goals": "Reach 95% OTIF and bring the top customer below 35% of sales within a year."},
    "fmcg_distribution": {"turnover_cr": 26, "dead_stock_pct": 18, "dso_days": 40,
        "description": "A snacks & beverages distributor in Indore (~₹26 cr) covering 1,200 outlets. Salesman beat productivity is low, ~18% of SKUs are near-dead, and secondary-sales visibility is poor.",
        "specific_question": "How do I raise beat productivity and clear slow stock while improving secondary-sales visibility?",
        "top_challenges": "low beat productivity / lines per call\n18% near-dead SKUs\nno secondary-sales visibility",
        "goals": "Lift productive calls 20% and cut dead stock to under 8%."},
    "agro_trading": {"turnover_cr": 22, "dso_days": 35, "city_tier": "Export",
        "description": "A turmeric & spice trader in Sangli (~₹22 cr) buying from mandis and selling domestic plus small exports. Commodity prices swing wildly and working capital is perpetually tight at harvest.",
        "specific_question": "How do I manage price-swing risk and free up working capital — and is scaling APEDA exports worth it?",
        "top_challenges": "volatile mandi prices squeeze margins\nworking capital locked at harvest\nquality/grading inconsistency for exports",
        "goals": "Stabilise margins and build a profitable APEDA-registered export line."},
    "export_import": {"turnover_cr": 15, "dso_days": 90, "city_tier": "Export", "procurement_method": "Few suppliers",
        "description": "A merchant exporter of handloom textiles in Karur (~₹15 cr) shipping to EU/US buyers. Container costs and a 90-day buyer-credit cycle are choking cash, and RoDTEP/drawback claims are pending.",
        "specific_question": "How do I fix the 90-day cash cycle and make sure I'm capturing every export incentive?",
        "top_challenges": "90-day buyer credit chokes cash\nhigh, volatile freight costs\npending RoDTEP/duty-drawback claims",
        "goals": "Cut the cash cycle by 30 days and recover all pending export incentives."},
    "logistics_warehousing": {"turnover_cr": 20, "dso_days": 65,
        "description": "A 40-truck fleet plus a 30,000 sq ft warehouse operator in Bhiwandi (~₹20 cr). Empty-return runs and detention charges are killing margins, and clients keep delaying payments.",
        "specific_question": "How do I cut empty miles, improve fleet utilisation, and speed up client collections?",
        "top_challenges": "high empty-return (deadhead) miles\ndetention & idle-truck costs\nclients delaying payment 60+ days",
        "goals": "Raise fleet utilisation to 80%+ and cut DSO below 45 days."},
    "d2c_brands": {"mode": "startup", "stage": "seed", "target_raise_cr": 5, "turnover_cr": 6, "gross_margin_pct": 55,
        "description": "A D2C skincare brand on Shopify + Amazon (~₹6 cr revenue run-rate, Mumbai). Blended CAC crept to ₹720 with payback over 7 months and returns running at 18%, just as they plan to raise.",
        "specific_question": "How do I get CAC payback under control and lift contribution margin before raising a round?",
        "top_challenges": "blended CAC ₹720 / payback >7 months\n18% return rate\nthin contribution margin after marketplace fees",
        "goals": "Raise ₹5 cr — with CAC payback under 4 months and clean unit economics."},
    "construction_infra_suppliers": {"turnover_cr": 30, "dso_days": 120, "receivables_cr": 9,
        "description": "A civil contractor and RMC supplier in Lucknow (~₹30 cr) on government and private projects. Cash is stuck in retention money and unbilled work, and two projects are running over budget.",
        "specific_question": "How do I unlock retention money and stop the cost overruns on running projects?",
        "top_challenges": "₹9 cr stuck in retention + unbilled work\ntwo projects over budget\nweak project cost tracking",
        "goals": "Release ₹3 cr of stuck cash and bring projects back to budgeted margin."},
    "restaurants_cloud_kitchens": {"mode": "existing", "turnover_cr": 4, "gross_margin_pct": 60,
        "description": "A 4-brand cloud kitchen in Bengaluru (~₹4 cr) running on Swiggy & Zomato. Aggregator commissions plus packaging eat ~35% of every order, and one of the four brands is bleeding money.",
        "specific_question": "Which brands should I kill or scale, and how do I reduce dependence on the aggregators?",
        "top_challenges": "35% lost to aggregator commission + packaging\none brand loss-making\nno direct-ordering channel",
        "goals": "Make every brand contribution-positive and build a 20% direct-order channel."},
    "healthcare_clinics": {"turnover_cr": 7, "dso_days": 55,
        "description": "A 2-branch diagnostic lab and polyclinic in Surat (~₹7 cr). Report turnaround complaints are rising, NABH accreditation is pending, and insurer/TPA payments are delayed.",
        "specific_question": "How do I get NABH-ready and speed up insurer/TPA collections without hurting patient experience?",
        "top_challenges": "rising report turnaround-time complaints\nNABH accreditation pending\ndelayed TPA/insurer payments",
        "goals": "Achieve NABH accreditation and cut TPA collection time in half."},
    "real_estate": {"turnover_cr": 35, "dso_days": 90,
        "description": "A residential developer and brokerage in Nagpur (~₹35 cr). One project's flats are slow to sell, RERA timelines are tight, and channel-partner payouts are opaque.",
        "specific_question": "How do I accelerate the slow-moving inventory and stay RERA-compliant on project cashflow?",
        "top_challenges": "slow-moving unsold inventory\ntight RERA timelines & escrow rules\nopaque channel-partner payouts",
        "goals": "Sell down the slow project and keep every project RERA-compliant."},
    "saas_startups": {"mode": "startup", "stage": "seed", "target_raise_cr": 12, "turnover_cr": "", "gross_margin_pct": 78, "cash_runway_months": 8,
        "description": "A seed-funded B2B SaaS for logistics in Bengaluru, ~₹2.4 cr ARR. Net revenue retention is ~92%, burn multiple ~2.3, and runway is down to 8 months as they prep a Series A.",
        "specific_question": "How do I push NRR above 110% and get the burn multiple under 1.5 to be Series-A ready?",
        "top_challenges": "NRR ~92% (net churn)\nburn multiple ~2.3\n8-month runway before Series A",
        "goals": "Hit Series-A metrics: NRR >110%, burn multiple <1.5, 18-month runway."},
    "professional_services": {"turnover_cr": 6, "top_customer_dep_pct": 50, "dso_days": 60,
        "description": "A 25-person digital marketing agency in Gurugram (~₹6 cr). Billable utilisation is ~60%, two clients are 50% of revenue, and scope-creep keeps eroding project margins.",
        "specific_question": "How do I raise utilisation and cut client concentration without a revenue dip?",
        "top_challenges": "billable utilisation only ~60%\ntwo clients = 50% of revenue\nscope-creep eroding margins",
        "goals": "Lift utilisation to 75% and get the top-2 clients under 35% of revenue."},
    "legal_firms": {"turnover_cr": 5, "dso_days": 95,
        "description": "A 12-lawyer commercial law firm in Delhi (~₹5 cr). Realisation on billed hours is low, receivables stretch past 90 days, and juniors are under-utilised.",
        "specific_question": "How do I improve realisation and collections without straining client relationships?",
        "top_challenges": "low realisation on billed hours\nreceivables 90+ days\nunder-utilised juniors",
        "goals": "Improve realisation 15% and bring collections under 60 days."},
    "ca_firms": {"turnover_cr": 4, "dso_days": 50,
        "description": "A CA firm in Ahmedabad (~₹4 cr, 30 staff) heavy on compliance work. There's a brutal seasonal crunch, a low advisory mix, and write-offs on fixed-fee jobs.",
        "specific_question": "How do I shift toward higher-margin advisory and smooth the seasonal workload?",
        "top_challenges": "seasonal compliance crunch\nlow advisory (high-margin) mix\nwrite-offs on fixed-fee work",
        "goals": "Grow advisory to 30% of revenue and reduce season overtime."},
    "education_institutes": {"turnover_cr": 8,
        "description": "A 3-centre test-prep coaching chain in Patna (~₹8 cr). Enrolment is dipping as edtech competes on price, and teacher attrition is high.",
        "specific_question": "How do I defend enrolment against edtech and retain my star faculty?",
        "top_challenges": "enrolment dipping vs edtech\nhigh teacher attrition\nweak digital/hybrid offering",
        "goals": "Stabilise enrolment and launch a hybrid model that lifts margins."},
    "textile_businesses": {"turnover_cr": 16, "gross_margin_pct": 12, "dso_days": 75,
        "description": "A power-loom and garment unit in Tiruppur (~₹16 cr) doing mostly job-work plus a small own-label line. Job-work margins are thin, receivables are stretched, and power costs are climbing.",
        "specific_question": "How do I shift toward own-label margins and manage the working-capital strain?",
        "top_challenges": "thin job-work margins\nstretched receivables\nrising power/input costs",
        "goals": "Grow own-label to 40% of output and stabilise working capital."},
    "electronics_distribution": {"turnover_cr": 28, "dead_stock_pct": 15, "dso_days": 45,
        "description": "A mobile & accessories distributor in Hyderabad (~₹28 cr). Price erosion is brutal, inventory obsolescence is high, and a few retailers have started defaulting.",
        "specific_question": "How do I protect margin against price erosion and control retailer credit risk?",
        "top_challenges": "rapid price erosion on handsets\nhigh inventory obsolescence\nretailer credit defaults",
        "goals": "Protect gross margin and cut bad-debt while holding market share."},
    "automotive_workshops": {"turnover_cr": 3.5, "repeat_rate_pct": 35,
        "description": "A multi-brand car-service garage in Coimbatore (~₹3.5 cr, 6 bays). Weekday bay utilisation is low, spare-parts pilferage is suspected, and the repeat-customer rate is weak.",
        "specific_question": "How do I raise bay utilisation and turn one-time jobs into repeat customers?",
        "top_challenges": "low weekday bay utilisation\nsuspected spare-parts pilferage\nweak repeat/AMC business",
        "goals": "Lift utilisation to 70% and double the repeat-customer rate."},
    "printing_packaging": {"turnover_cr": 9, "dso_days": 70,
        "description": "An offset and corrugated-box printer in Faridabad (~₹9 cr) serving FMCG clients. Make-ready waste is high, machines see unplanned downtime, and client payments lag.",
        "specific_question": "How do I cut make-ready waste and downtime while improving cash collection?",
        "top_challenges": "high make-ready waste\nunplanned machine downtime\nclient payments delayed 70 days",
        "goals": "Cut waste & downtime 25% and bring DSO under 45 days."},
    "beauty_wellness": {"turnover_cr": 3, "repeat_rate_pct": 40,
        "description": "A 3-salon and spa chain in Pune (~₹3 cr). Stylist churn is high (and they take clients with them), retail-product attach is low, and weekday footfall is thin.",
        "specific_question": "How do I retain stylists, lift revenue per chair, and grow product attach?",
        "top_challenges": "high stylist churn taking clients\nlow product-retail attach\nthin weekday footfall",
        "goals": "Cut stylist churn and lift revenue-per-chair 25%."},
    "furniture_businesses": {"turnover_cr": 7, "dso_days": 75,
        "description": "A modular-furniture maker with a showroom in Jodhpur (~₹7 cr) selling B2C plus project orders. Lead times are long, WIP is high, and project receivables are stuck.",
        "specific_question": "How do I shorten lead times and unlock the cash trapped in project receivables?",
        "top_challenges": "long make-to-order lead times\nhigh WIP on the floor\nstuck project receivables",
        "goals": "Halve lead time and release project cash faster."},
    "hardware_stores": {"turnover_cr": 6, "dead_stock_pct": 15, "dso_days": 50,
        "description": "A 2-branch hardware, paint & sanitaryware store in Bhopal (~₹6 cr) with 4,000+ SKUs. Dead stock is ~15% and credit extended to contractors keeps stretching.",
        "specific_question": "How do I clear dead stock across 4,000 SKUs and control contractor credit?",
        "top_challenges": "~15% dead stock across a huge SKU range\nstretched contractor credit\nno SKU-level velocity view",
        "goals": "Cut dead stock to 7% and tighten contractor credit terms."},
    "stationery_chains": {"turnover_cr": 4,
        "description": "A 4-store stationery & books chain in Kochi (~₹4 cr). Revenue spikes in school season then dips into an off-season cash crunch, and online players undercut on price.",
        "specific_question": "How do I smooth the seasonal cashflow and compete with online discounters?",
        "top_challenges": "sharp school-season seasonality\noff-season cash crunch\nonline price competition",
        "goals": "Smooth cashflow across the year and defend the core assortment."},
    "repair_service": {"turnover_cr": 2.5, "repeat_rate_pct": 40,
        "description": "An appliance repair and AMC service business in Chennai (~₹2.5 cr). Technician scheduling is chaotic, first-time-fix rate is low, and AMC renewals are leaking.",
        "specific_question": "How do I raise first-time-fix rate and stop AMC renewals from leaking?",
        "top_challenges": "chaotic technician scheduling\nlow first-time-fix rate\nleaking AMC renewals",
        "goals": "Lift first-time-fix to 85% and renew 80% of AMCs."},
    "event_businesses": {"turnover_cr": 5,
        "description": "A wedding and corporate-events company in Jaipur (~₹5 cr). Vendor advances tie up cash, demand is highly seasonal, and per-event margins are unpredictable.",
        "specific_question": "How do I stabilise cashflow and protect margin on each event?",
        "top_challenges": "vendor advances lock up cash\nhighly seasonal demand\nunpredictable per-event margins",
        "goals": "Stabilise cashflow and standardise event-level margin tracking."},
    "travel_agencies": {"turnover_cr": 6, "gross_margin_pct": 8,
        "description": "A travel agency and tour operator in Kochi (~₹6 cr) on domestic and outbound packages. Margins are thin, supplier advances are heavy, and post-season refund/credit-shells are a mess.",
        "specific_question": "How do I improve margins and recover the supplier refunds and credit-shells stuck post-season?",
        "top_challenges": "thin package margins\nheavy supplier advances\nstuck refunds/credit-shells",
        "goals": "Lift margin via corporate/MICE mix and recover stuck supplier credits."},
    "local_service_msme": {"turnover_cr": 1.2, "systems_used": "WhatsApp + Excel", "owner_dependency": "Totally - I do everything",
        "description": "A neighbourhood laundry and dry-clean with 2 outlets in Pune (~₹1.2 cr). Everything is cash/UPI with thin records, the owner does everything, and revenue leakage is suspected.",
        "specific_question": "How do I formalise the business, stop the revenue leakage, and free up my own time?",
        "top_challenges": "cash/UPI with no real records\nsuspected revenue leakage\ntotal owner dependency",
        "goals": "Formalise, plug leakage, and run with a trained No.2."},
}


def _low_pct(s):
    m = re.findall(r"\d+", s or "")
    return m[0] if m else ""


def _high_pct(s):
    m = re.findall(r"\d+", s or "")
    return m[-1] if m else ""


def _apply_lens(intake, key, pb, lens):
    """Re-frame a signature intake as a growth / turnaround / fundraise situation."""
    it = dict(intake)
    name = pb.get("name", "the business")
    prof = pb.get("profitability_analysis", {})
    _gnums = [int(x) for x in re.findall(r"\d+", prof.get("typical_gross_margin") or "")]
    gm_hi = str(max(_gnums)) if _gnums else ""              # healthy end (growth)
    gm_lo = str(max((min(_gnums) if _gnums else 6) - 4, 2))  # squeezed end (turnaround)
    size = f"~₹{it.get('turnover_cr')} cr" if it.get("turnover_cr") not in ("", None) else "early-stage"
    bns = [b.get("bottleneck", "") for b in pb.get("operational_bottlenecks", [])]
    top_bn = bns[0] if bns else ""
    startup = it.get("mode") == "startup"
    has_dso = it.get("dso_days") not in ("", None)
    has_dead = it.get("dead_stock_pct") not in ("", None)

    if lens == "growth":
        it.update({
            "stage": "seed" if startup else "scaling",
            "gross_margin_pct": gm_hi or it.get("gross_margin_pct"),
            "dso_days": (45 if has_dso else ""),
            "dead_stock_pct": ("6" if has_dead else ""),
            "has_sops": "Mostly", "owner_dependency": "Medium",
            "systems_used": "Mixed" if startup else "Tally",
            "description": f"{name} ({size}) is profitable and growing fast — the fundamentals work and the owner now wants to scale aggressively over the next 24 months without breaking operations or cash.",
            "specific_question": "What is the fastest, safest way to double the business without margins or cash breaking?",
            "goals": "Double revenue in 24 months — profitably, without an ops or cash blow-up.",
            "top_challenges": "scaling without losing margin\nbuilding SOPs + a team to delegate to\nworking capital to fund the growth",
        })
        if startup:
            it["target_raise_cr"] = it.get("target_raise_cr") or 8
    elif lens == "turnaround":
        it.update({
            "stage": "early-revenue" if startup else "turnaround",
            "gross_margin_pct": gm_lo,
            "net_margin_pct": "-3",
            "dso_days": (105 if has_dso else ""),
            "dead_stock_pct": ("22" if has_dead else ""),
            "cash_runway_months": 3, "has_sops": "No", "owner_dependency": "Totally - I do everything",
            "systems_used": "Excel/Sheets", "returns_current": "Behind", "licences_current": "Some pending",
            "description": f"{name} ({size}) is in distress — margins have collapsed, cash is tight, and {(top_bn[0].lower() + top_bn[1:]) if top_bn else 'operations are slipping'}. The owner needs a stabilisation plan, fast.",
            "specific_question": "How do I stop the bleeding and get back to positive cash and profit within 90 days?",
            "goals": "Return to positive cash and profit within two quarters.",
        })
    elif lens == "fundraise":
        if startup:
            it.update({
                "target_raise_cr": it.get("target_raise_cr") or 5,
                "description": f"{name} is preparing to raise its next round and needs to be diligence-ready — clean metrics, a tight story, and no red flags.",
                "specific_question": "Am I investment-ready, what will diligence flag, and which metrics must I hit before I raise?",
                "goals": "Close the round on good terms with a clean data room.",
                "top_challenges": "metrics not yet at benchmark\nno investor data room\npositioning/story not tight",
            })
        else:
            it.update({
                "has_sops": "Mostly", "systems_used": "Tally + Excel",
                "description": f"{name} ({size}) wants to raise growth capital / a working-capital line and needs to be credit- and investment-ready.",
                "specific_question": "How do I become investment/credit-ready, and what will a lender or investor flag in diligence?",
                "goals": "Raise growth capital / a working-capital line on good terms.",
                "top_challenges": "books not investor-ready\nworking-capital cycle too long\nno clean MIS / data room",
            })
    return it


def demo_sample(key, lens="signature"):
    """Build a complete, scenario-driven demo intake for one sector + lens."""
    pb = PB.get_playbook(key) if PB else None
    if not pb:
        return None
    sc = _SCEN.get(key, {})
    mode = sc.get("mode", "existing")
    tier = pb.get("tier", 2)
    prof = pb.get("profitability_analysis", {})
    turnover = sc.get("turnover_cr", "" if mode == "startup" else (30 if key in _BIG else (3 if key in _SMALL else 12)))
    dso = sc.get("dso_days", "" if (key in _CASH or mode == "startup") else 80)
    rec = sc.get("receivables_cr", "")
    if rec == "" and str(turnover).replace(".", "").isdigit() and str(dso).isdigit() and int(dso) > 0:
        rec = round(float(turnover) * float(dso) / 365.0, 1)
    inv = sc.get("inventory_value_cr", "")
    if inv == "" and key in _INVENTORY and str(turnover).replace(".", "").isdigit():
        inv = round(float(turnover) * 0.18, 1)
    base = {
        "mode": mode,
        "business_type": key,
        "description": sc.get("description", pb.get("one_liner", "")[:240]),
        "stage": sc.get("stage", "seed" if mode == "startup" else "growing"),
        "city_tier": sc.get("city_tier", "Pan-India" if key in _BIG else f"Tier-{min(max(tier, 1), 3)}"),
        "employees": sc.get("employees", 12 if mode == "startup" else (80 if key in _BIG else (8 if key in _SMALL else 30))),
        "years_operating": "" if mode == "startup" else sc.get("years_operating", 7),
        "turnover_cr": turnover,
        "target_raise_cr": sc.get("target_raise_cr", 3) if mode == "startup" else "",
        "gross_margin_pct": sc.get("gross_margin_pct", _low_pct(prof.get("typical_gross_margin"))),
        "net_margin_pct": sc.get("net_margin_pct", _low_pct(prof.get("typical_net_margin"))),
        "receivables_cr": rec,
        "dso_days": dso,
        "cash_runway_months": sc.get("cash_runway_months", 7 if mode == "startup" else ""),
        "systems_used": sc.get("systems_used", "Mixed" if mode == "startup" else ("WhatsApp + Excel" if key in _SMALL else ("Tally + Excel" if key in _BIG else "Tally"))),
        "has_sops": sc.get("has_sops", "A few"),
        "owner_dependency": sc.get("owner_dependency", "High"),
        "inventory_value_cr": inv,
        "dead_stock_pct": sc.get("dead_stock_pct", "12" if key in _INVENTORY else ""),
        "procurement_method": sc.get("procurement_method", "Imports" if key == "export_import" else ("Open market" if key == "agro_trading" else "Few suppliers")),
        "top_supplier_dep_pct": sc.get("top_supplier_dep_pct", "45" if key in _INVENTORY else ""),
        "top_customer_dep_pct": sc.get("top_customer_dep_pct", "30"),
        "repeat_rate_pct": sc.get("repeat_rate_pct", "45" if (key in _CASH or key in _SMALL) else ""),
        "has_crm": sc.get("has_crm", "Spreadsheet"),
        "gst_registered": "Yes",
        "returns_current": sc.get("returns_current", "Mostly"),
        "licences_current": sc.get("licences_current", "Some pending"),
        "specific_question": sc.get("specific_question", "How do I improve profitability and cashflow while scaling?"),
        "top_challenges": sc.get("top_challenges", "\n".join([b.get("bottleneck", "") for b in pb.get("operational_bottlenecks", [])][:3])),
        "goals": sc.get("goals", "Improve profitability and cash, and scale sustainably over the next 12 months."),
    }
    return base if lens == "signature" else _apply_lens(base, key, pb, lens)


def demo_samples():
    """Every sector with its scenario lenses (signature / growth / turnaround / fundraise)."""
    if not PB:
        return []
    out = []
    for c in PB.list_playbooks():
        scenarios = []
        for L in LENSES:
            intake = demo_sample(c["key"], L["key"])
            if intake:
                scenarios.append({"lens": L["key"], "label": L["label"], "icon": L["icon"],
                                  "mode": intake["mode"], "scenario": intake["description"], "intake": intake})
        if scenarios:
            out.append({"key": c["key"], "name": c["name"], "icon": c["icon"], "tier": c["tier"], "scenarios": scenarios})
    return out


# ============================================================
# 2. OPEN-SOURCE WEB SEARCH (keyless: DuckDuckGo + Wikipedia)
# ============================================================
_UA = {"User-Agent": "Mozilla/5.0 (compatible; PMGuruBrain/1.0)"}


def _http_get(url, params=None, timeout=8.0):
    if not httpx:
        return None
    try:
        with httpx.Client(timeout=timeout, headers=_UA, follow_redirects=True) as c:
            r = c.get(url, params=params)
            if r.status_code == 200:
                return r
    except Exception as e:
        print(f"[live_brain] GET failed {url}: {str(e)[:100]}", flush=True)
    return None


def _ddg_instant(query):
    """DuckDuckGo Instant Answer API — keyless, returns abstract + related topics."""
    out = []
    r = _http_get("https://api.duckduckgo.com/", {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"})
    if not r:
        return out
    try:
        d = r.json()
    except Exception:
        return out
    if d.get("AbstractText"):
        out.append({"title": d.get("Heading") or query, "snippet": d["AbstractText"],
                    "url": d.get("AbstractURL", ""), "source": d.get("AbstractSource") or "DuckDuckGo"})
    for t in (d.get("RelatedTopics") or [])[:6]:
        if isinstance(t, dict) and t.get("Text"):
            out.append({"title": t["Text"][:80], "snippet": t["Text"],
                        "url": (t.get("FirstURL") or ""), "source": "DuckDuckGo"})
    return out


def _ddg_html(query):
    """DuckDuckGo HTML results — best-effort scrape of titles + snippets."""
    out = []
    r = _http_get("https://html.duckduckgo.com/html/", {"q": query})
    if not r:
        return out
    html = r.text
    # result snippets live in <a class="result__snippet">...</a> and titles in result__a
    titles = re.findall(r'result__a[^>]*>(.*?)</a>', html, re.S)
    snips = re.findall(r'result__snippet[^>]*>(.*?)</a>', html, re.S)
    urls = re.findall(r'result__a"\s+href="(.*?)"', html, re.S)

    def _clean(s):
        return re.sub(r"<.*?>", "", s or "").replace("&amp;", "&").replace("&#x27;", "'").strip()
    for i in range(min(5, len(snips))):
        t = _clean(titles[i]) if i < len(titles) else query
        out.append({"title": t[:90], "snippet": _clean(snips[i])[:320],
                    "url": _clean(urls[i]) if i < len(urls) else "", "source": "Web"})
    return out


def _wikipedia(query):
    """Wikipedia search + summary — keyless, reliable grounding."""
    out = []
    r = _http_get("https://en.wikipedia.org/w/api.php",
                  {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": "2"})
    if not r:
        return out
    try:
        hits = r.json().get("query", {}).get("search", [])
    except Exception:
        return out
    for h in hits[:2]:
        title = h.get("title", "")
        s = _http_get("https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title))
        if s:
            try:
                js = s.json()
                if js.get("extract"):
                    out.append({"title": title, "snippet": js["extract"][:320],
                                "url": (js.get("content_urls", {}).get("desktop", {}) or {}).get("page", ""),
                                "source": "Wikipedia"})
            except Exception:
                pass
    return out


def web_search(query, max_results=6):
    """Aggregate keyless open-source results. Never raises; returns [] on full failure."""
    results, seen = [], set()
    for fn in (_ddg_instant, _wikipedia, _ddg_html):
        try:
            for item in fn(query):
                k = (item.get("snippet") or "")[:60]
                if k and k not in seen:
                    seen.add(k)
                    results.append(item)
        except Exception as e:
            print(f"[live_brain] search source failed: {str(e)[:80]}", flush=True)
        if len(results) >= max_results:
            break
    return results[:max_results]


# ============================================================
# 3. PERSISTENT LEARNING LOG  (the brain evolves with each prompt)
# ============================================================
# Stored as JSONL under BRAIN_DATA_DIR (mount a Railway volume there to persist
# across redeploys; falls back to a local dir otherwise).
_DATA_DIR = os.getenv("BRAIN_DATA_DIR", "").strip() or os.path.join(os.path.dirname(os.path.abspath(__file__)), "brain_data")
_LOG_PATH = os.path.join(_DATA_DIR, "engagements.jsonl")


def _ensure_dir():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        return True
    except Exception as e:  # pragma: no cover
        print(f"[live_brain] cannot create {_DATA_DIR}: {e}", flush=True)
        return False


def _read_log():
    out = []
    try:
        if os.path.exists(_LOG_PATH):
            with open(_LOG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            out.append(json.loads(line))
                        except Exception:
                            continue
    except Exception as e:  # pragma: no cover
        print(f"[live_brain] read log failed: {e}", flush=True)
    return out


def _tokens(text):
    return set(re.findall(r"[a-z]{4,}", (text or "").lower()))


def recall_similar(business_type, description, k=3):
    """Find past engagements most similar to this one (sector + keyword overlap)."""
    log = _read_log()
    if not log:
        return {"used": 0, "total_memory": 0, "notes": [], "matches": []}
    q_tokens = _tokens(description) | _tokens(business_type)
    scored = []
    for e in log:
        score = 0
        if e.get("business_type") and e.get("business_type") == business_type:
            score += 5
        overlap = len(q_tokens & set(e.get("tokens", [])))
        score += overlap
        if score > 0:
            scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [e for _, e in scored[:k]]
    notes = []
    for e in top:
        kf = e.get("key_findings") or []
        if kf:
            notes.append(f"Past {e.get('business_type','?')} engagement learned: {kf[0]}")
    return {"used": len(top), "total_memory": len(log), "notes": notes,
            "matches": [{"business_type": e.get("business_type"), "summary": e.get("summary", "")} for e in top]}


def save_engagement(intake, envelope):
    """Append this engagement so the brain learns. Best-effort; never raises."""
    if not _ensure_dir():
        return False
    desc = intake.get("description", "")
    recs = envelope.get("tailored_recommendations") or []
    key_findings = [r.get("title") for r in recs[:3] if r.get("title")]
    rid = envelope.get("engagement_id") or hashlib.sha1((desc + str(time.time())).encode()).hexdigest()[:12]
    sc = envelope.get("scorecard") or {}
    record = {
        "id": rid,
        "ts": int(time.time()),
        "business_type": envelope.get("business_type"),
        "sector_name": envelope.get("sector_name"),
        "mode": intake.get("mode"),
        "summary": (envelope.get("diagnosis") or "")[:240],
        "key_findings": key_findings,
        "tokens": sorted(list(_tokens(desc) | _tokens(intake.get("top_challenges", "")) | _tokens(intake.get("goals", ""))))[:40],
        "engine": envelope.get("engine"),
        "grade": sc.get("grade"),
        "overall": sc.get("overall"),
        "scores": {s["key"]: s["score"] for s in (sc.get("scores") or [])},
        "weaknesses": [w for w in (envelope.get("swot", {}) or {}).get("weaknesses", [])][:3],
    }
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception as e:  # pragma: no cover
        print(f"[live_brain] save failed: {e}", flush=True)
        return False


def brain_stats():
    log = _read_log()
    by_sector = {}
    for e in log:
        bt = e.get("business_type") or "unknown"
        by_sector[bt] = by_sector.get(bt, 0) + 1
    recent = sorted(log, key=lambda e: e.get("ts", 0), reverse=True)[:8]
    return {
        "total_engagements": len(log),
        "by_sector": by_sector,
        "recent": [{"business_type": e.get("business_type"), "mode": e.get("mode"),
                    "summary": e.get("summary", "")[:140], "engine": e.get("engine")} for e in recent],
        "data_dir": _DATA_DIR,
        "persisted": os.path.exists(_LOG_PATH),
    }


_DASH_DIMS = [
    ("investment_readiness", "Investment Readiness", "💸"),
    ("risk_resilience", "Risk & Resilience", "🛡️"),
    ("transformation", "Transformation", "🔄"),
    ("digital_maturity", "Digital Maturity", "📶"),
    ("growth", "Growth Potential", "🚀"),
]


def dashboard():
    """Founder portfolio analytics across all saved engagements."""
    log = _read_log()
    n = len(log)
    graded = [e for e in log if e.get("grade")]
    grade_dist = {g: 0 for g in ("A", "B", "C", "D")}
    for e in graded:
        grade_dist[e["grade"]] = grade_dist.get(e["grade"], 0) + 1
    by_sector = {}
    for e in log:
        key = e.get("sector_name") or e.get("business_type") or "Unknown"
        by_sector[key] = by_sector.get(key, 0) + 1
    by_mode = {}
    for e in log:
        by_mode[e.get("mode") or "existing"] = by_mode.get(e.get("mode") or "existing", 0) + 1
    dims = []
    for k, label, icon in _DASH_DIMS:
        vals = [e["scores"].get(k) for e in log if isinstance(e.get("scores"), dict) and e["scores"].get(k) is not None]
        dims.append({"key": k, "label": label, "icon": icon,
                     "avg": round(sum(vals) / len(vals)) if vals else None,
                     "min": min(vals) if vals else None, "max": max(vals) if vals else None})
    overalls = [e["overall"] for e in graded if e.get("overall") is not None]
    weak_counts = {}
    for e in log:
        for w in (e.get("weaknesses") or []):
            weak_counts[w] = weak_counts.get(w, 0) + 1
    top_weaknesses = sorted(weak_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    recent = sorted(log, key=lambda e: e.get("ts", 0), reverse=True)[:12]
    return {
        "total": n,
        "graded": len(graded),
        "avg_overall": round(sum(overalls) / len(overalls)) if overalls else None,
        "grade_distribution": grade_dist,
        "by_sector": dict(sorted(by_sector.items(), key=lambda x: x[1], reverse=True)),
        "by_mode": by_mode,
        "dimensions": dims,
        "top_weaknesses": [{"weakness": w, "count": c} for w, c in top_weaknesses],
        "recent": [{"sector": e.get("sector_name") or e.get("business_type"), "mode": e.get("mode"),
                    "grade": e.get("grade"), "overall": e.get("overall"),
                    "summary": (e.get("summary") or "")[:120], "engine": e.get("engine")} for e in recent],
        "persisted": os.path.exists(_LOG_PATH),
    }


# ============================================================
# 4. DETERMINISTIC PERSONALISER  (always-on base, input-shaped)
# ============================================================
def _f(intake, key, default=""):
    v = intake.get(key)
    return v if v not in (None, "") else default


def _challenge_list(intake):
    raw = _f(intake, "top_challenges")
    items = [x.strip() for x in re.split(r"[\n;,]", raw) if x.strip()]
    return items


def _deterministic_engagement(intake, pb, recall):
    """Build a complete, input-personalised engagement from the playbook + form.
    This is what guarantees different businesses (and different inputs) get
    different answers even with no LLM key."""
    mode = _f(intake, "mode", "existing")
    sector = pb.get("name", "your business") if pb else "your business"
    stage = _f(intake, "stage", "growing")
    tier = _f(intake, "city_tier", "Tier-2")
    challenges = _challenge_list(intake)
    goal = _f(intake, "goals")
    size_bits = []
    if _f(intake, "turnover_cr"):
        size_bits.append(f"₹{_f(intake,'turnover_cr')} cr turnover")
    if _f(intake, "target_raise_cr"):
        size_bits.append(f"raising ₹{_f(intake,'target_raise_cr')} cr")
    if _f(intake, "employees"):
        size_bits.append(f"{_f(intake,'employees')} people")
    size_str = ", ".join(size_bits) or "early scale"

    om = (pb.get("operating_model") or {}).get("summary", "") if pb else ""
    bottlenecks = pb.get("operational_bottlenecks", []) if pb else []
    autos = pb.get("ai_automation_opportunities", []) if pb else []
    pb_risks = pb.get("risk_model", []) if pb else []
    kpis = pb.get("kpi_structure", []) if pb else []
    growth_stages = (pb.get("growth_playbook") or {}).get("stages", []) if pb else []
    pm = pb.get("pm_workflows", []) if pb else []

    # Diagnosis — explicitly references THIS business's inputs.
    diag = (
        f"You are running {'a ' + mode + '-stage' if mode=='startup' else 'an existing'} "
        f"{sector} ({size_str}; primary market {tier}; stage: {stage}). "
        + (f"The operating reality of this sector: {om} " if om else "")
        + (f"Your stated priority — \"{_f(intake,'specific_question')}\" — " if _f(intake, 'specific_question') else "")
        + ("maps directly to the structural levers below. " if _f(intake, 'specific_question') else "")
    )
    if challenges:
        diag += f"You flagged {len(challenges)} pain point(s): {', '.join(challenges[:4])}. "
        bn0 = bottlenecks[0]["bottleneck"] if bottlenecks else None
        if bn0:
            diag += f"In {sector}, these typically trace back to the sector's #1 bottleneck — {bn0}. "
    # DD signals — make the diagnosis reference the actual numbers given.
    flags = []
    if _f(intake, "systems_used") in ("Pen & paper", "Excel/Sheets", "WhatsApp + Excel"):
        flags.append(f"you run on {_f(intake,'systems_used')} (low data visibility — a maturity gap)")
    if _f(intake, "dso_days") and str(_f(intake, "dso_days")).replace(".", "").isdigit() and float(_f(intake, "dso_days")) > 60:
        flags.append(f"DSO is {_f(intake,'dso_days')} days (working-capital leak vs <60 healthy)")
    if _f(intake, "dead_stock_pct") and str(_f(intake, "dead_stock_pct")).replace(".", "").isdigit() and float(_f(intake, "dead_stock_pct")) > 8:
        flags.append(f"{_f(intake,'dead_stock_pct')}% dead/slow stock (cash trapped on the shelf)")
    if _f(intake, "has_sops") in ("No", "A few"):
        flags.append("thin SOPs (owner-dependency + inconsistent execution risk)")
    if _f(intake, "top_customer_dep_pct") and str(_f(intake, "top_customer_dep_pct")).replace(".", "").isdigit() and float(_f(intake, "top_customer_dep_pct")) > 30:
        flags.append(f"top customer is {_f(intake,'top_customer_dep_pct')}% of revenue (concentration risk)")
    if _f(intake, "gst_registered") in ("No", "Not sure") or _f(intake, "returns_current") in ("Behind", "Not sure"):
        flags.append("compliance hygiene needs attention")
    if flags:
        diag += "Due-diligence read: " + "; ".join(flags) + ". "
    if goal:
        diag += f"Goal in scope: {goal}."

    # Recommendations — tailored: challenge-driven first, then sector bottlenecks, then mode plays.
    recs = []
    for ch in challenges[:3]:
        recs.append({"title": f"Resolve: {ch}", "priority": "High",
                     "why": f"You flagged this as a live pain point in your {sector} operation.",
                     "how": "Instrument it, set a target, assign an owner, review weekly. " +
                            ("Use the relevant AI agent below to automate the fix." if autos else "")})
    for b in bottlenecks[:3]:
        recs.append({"title": f"Pre-empt sector bottleneck: {b.get('bottleneck')}", "priority": "Medium",
                     "why": b.get("impact", ""), "how": f"Root cause is usually: {b.get('root_cause','')}. Put a control in before it bites."})
    if mode == "startup":
        recs.append({"title": "Tighten unit economics before scaling spend", "priority": "High",
                     "why": "Pre-PMF burn on unproven economics is the #1 startup killer.",
                     "how": "Prove contribution margin and CAC payback on a small cohort first; then pour fuel."})
        if _f(intake, "target_raise_cr"):
            recs.append({"title": "Build an investor-ready data room", "priority": "Medium",
                         "why": f"You're targeting ₹{_f(intake,'target_raise_cr')} cr — diligence readiness shortens the raise.",
                         "how": "Cap table, 3-statement model, metrics pack, DPIIT 80-IAC/angel-tax exemption filings."})
    else:
        recs.append({"title": "Stand up a weekly numbers cadence", "priority": "High",
                     "why": "Most MSME leakage is invisible without a weekly metric review.",
                     "how": "One dashboard: revenue, margin, cash, DSO, and your top-2 sector KPIs below."})

    quick_wins = [f"{a.get('opportunity')} (via {a.get('agent') or 'ops'})"
                  for a in autos if a.get("effort") == "Low"][:3]
    if not quick_wins:
        quick_wins = [a.get("opportunity") for a in autos[:3] if a.get("opportunity")]

    # Risk — bump severity if challenges mention cash/compliance.
    risk_text = " ".join(challenges).lower()
    risks = []
    for r in pb_risks[:4]:
        sev = r.get("severity", "Medium")
        if any(w in risk_text for w in ("cash", "gst", "compliance", "payment", "credit")) and r.get("severity") in ("Medium", "High"):
            sev = "High"
        risks.append({"risk": r.get("risk"), "severity": sev, "control": r.get("control")})

    kpi_out = [{"kpi": k.get("kpi"), "target": k.get("healthy"), "why": k.get("definition")} for k in kpis[:5]]

    # 90-day plan from PM workflows + growth stage plays.
    plays = []
    if growth_stages:
        idx = 0 if mode == "startup" or stage in ("idea", "pre-seed", "seed", "just-started") else min(1, len(growth_stages) - 1)
        plays = (growth_stages[idx] or {}).get("plays", [])
    plan = [
        {"phase": "Days 0-30 — Stabilise & measure",
         "steps": ([f"Instrument: {challenges[0]}"] if challenges else []) +
                  [(pm[0]["milestones"][0] if pm and pm[0].get("milestones") else "Stand up the core dashboard")] +
                  ["Confirm compliance calendar is current"]},
        {"phase": "Days 30-60 — Fix the binding constraint",
         "steps": [recs[0]["title"] if recs else "Address top recommendation",
                   (quick_wins[0] if quick_wins else "Automate one repetitive workflow")]},
        {"phase": "Days 60-90 — Compound",
         "steps": (plays[:2] if plays else ["Double down on what moved the needle", "Plan the next growth bet"])},
    ]

    opportunities = plays[:4] if plays else [a.get("opportunity") for a in autos[:4] if a.get("opportunity")]

    return {
        "diagnosis": diag,
        "tailored_recommendations": recs[:6],
        "quick_wins": quick_wins,
        "risks": risks,
        "kpis": kpi_out,
        "action_plan_90day": plan,
        "opportunities": opportunities,
    }


# ============================================================
# 5. LLM SYNTHESIS  (Groq via llm_stack; merges over the base)
# ============================================================
def _extract_json(text):
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(json)?", "", t).strip()
    t = re.sub(r"```$", "", t).strip()
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(t[start:end + 1])
    except Exception:
        return None


def _llm_enhance(intake, pb, web, recall, base, docs=None):
    """Ask Groq to produce a richer, business-specific engagement. Returns dict or None."""
    if not LLM or not LLM.available():
        return None
    sector = pb.get("name") if pb else "the business"
    grounding = {
        "operating_model": (pb.get("operating_model") or {}).get("summary") if pb else "",
        "bottlenecks": [b.get("bottleneck") for b in (pb.get("operational_bottlenecks") or [])][:6] if pb else [],
        "kpis": [k.get("kpi") for k in (pb.get("kpi_structure") or [])][:6] if pb else [],
        "risks": [r.get("risk") for r in (pb.get("risk_model") or [])][:5] if pb else [],
        "compliance": [c.get("title") for c in (pb.get("compliance_resolved") or [])] if pb else [],
    }
    web_block = "\n".join(f"- [{w.get('source')}] {w.get('title')}: {w.get('snippet')}" for w in web[:6]) or "(no live results)"
    recall_block = "\n".join(f"- {n}" for n in recall.get("notes", [])) or "(no prior memory)"
    doc_block = "\n".join(f"- [{d.get('source')}] {d.get('snippet')}" for d in (docs or [])[:4]) or "(no documents provided)"
    system = (
        "You are a blended top-tier strategy + operations consultant and a veteran Indian MSME operator. "
        "Produce a SPECIFIC, customised consulting engagement for THIS business using its exact inputs. "
        "Be concrete, India-aware, ₹-denominated. Never generic. Cite the live web sources when you use them. "
        "Return ONLY valid JSON with keys: diagnosis (string), tailored_recommendations (array of {title, priority, why, how}), "
        "quick_wins (array of strings), risks (array of {risk, severity, control}), kpis (array of {kpi, target, why}), "
        "action_plan_90day (array of {phase, steps[]}), opportunities (array of strings)."
    )
    user = (
        f"SECTOR: {sector}\nMODE: {intake.get('mode')}\n\n"
        f"FULL DUE-DILIGENCE INTAKE (use every signal that is filled in; call out anything missing that you'd need):\n"
        f"{_intake_summary_lines(intake)}\n\n"
        f"SECTOR GROUNDING (use, don't just repeat):\n{json.dumps(grounding, ensure_ascii=False)}\n\n"
        f"LIVE OPEN-SOURCE SEARCH RESULTS:\n{web_block}\n\n"
        f"EXCERPTS FROM THE OWNER'S OWN DOCUMENTS (treat as ground truth; cite the source name when you use them):\n{doc_block}\n\n"
        f"WHAT THE BRAIN REMEMBERS FROM SIMILAR PAST ENGAGEMENTS:\n{recall_block}\n\n"
        "Now produce the customised JSON engagement. Tie recommendations to the specific numbers the owner gave "
        "(margins, DSO, dead stock, dependence %, systems, SOPs, compliance). Quantify the ₹ upside where you can."
    )
    try:
        res = LLM.augment(system, user, max_tokens=1600)
    except Exception as e:
        print(f"[live_brain] llm augment failed: {str(e)[:120]}", flush=True)
        return None
    if not res or not res.get("text"):
        return None
    parsed = _extract_json(res["text"])
    if not isinstance(parsed, dict):
        return None
    parsed["_provider"] = res.get("provider")
    return parsed


# ============================================================
# 5b. AI DUE-DILIGENCE SCORECARD (institutional, explainable)
# ============================================================
# Five 0-100 scores (higher = healthier) computed deterministically from the DD
# intake + sector benchmarks, each with the drivers that moved it. This is the
# "business-health cockpit / risk heatmap" — trustworthy because it's explainable,
# and it works with zero LLM keys.
_SYS_SCORE = {"Pen & paper": 8, "Excel/Sheets": 28, "WhatsApp + Excel": 32, "Tally": 55,
              "Tally + Excel": 62, "An ERP": 88, "Mixed": 45}
_SOP_SCORE = {"No": 0, "A few": 6, "Mostly": 14, "Yes - followed": 20}
_CRM_SCORE = {"No": 0, "WhatsApp only": 4, "Spreadsheet": 7, "Yes - a CRM": 16}
_OWNER_SCORE = {"Totally - I do everything": 0, "High": 6, "Medium": 14, "Low - team runs it": 20}


def _numf(v):
    try:
        return float(str(v).replace("%", "").replace(",", "").strip())
    except Exception:
        return None


def _clamp(x):
    return int(max(0, min(100, round(x))))


def _band(s):
    return "strong" if s >= 70 else ("moderate" if s >= 45 else "weak")


def dd_scores(intake, pb):
    """Return the 5-score DD scorecard + weighted overall grade, with drivers."""
    g = _numf(intake.get("gross_margin_pct"))
    n = _numf(intake.get("net_margin_pct"))
    dso = _numf(intake.get("dso_days"))
    dead = _numf(intake.get("dead_stock_pct"))
    runway = _numf(intake.get("cash_runway_months"))
    custdep = _numf(intake.get("top_customer_dep_pct"))
    suppdep = _numf(intake.get("top_supplier_dep_pct"))
    repeat = _numf(intake.get("repeat_rate_pct"))
    sysn = _SYS_SCORE.get(intake.get("systems_used"), 35)
    sop = _SOP_SCORE.get(intake.get("has_sops"), 6)
    crm = _CRM_SCORE.get(intake.get("has_crm"), 5)
    owner = _OWNER_SCORE.get(intake.get("owner_dependency"), 6)
    gst_ok = intake.get("gst_registered") == "Yes"
    returns_ok = intake.get("returns_current") in ("Yes", "Mostly")
    lic_ok = intake.get("licences_current") == "Yes"
    stage = (intake.get("stage") or "").lower()
    city = (intake.get("city_tier") or "")
    tier = pb.get("tier", 2) if pb else 2
    prof = pb.get("profitability_analysis", {}) if pb else {}
    gm_lo = _numf(_low_pct(prof.get("typical_gross_margin")))
    gm_hi = _numf(_high_pct(prof.get("typical_gross_margin")))
    gm_mid = ((gm_lo or 0) + (gm_hi or (gm_lo or 0) + 10)) / 2 if gm_lo is not None else None
    growthy = stage in ("growth", "growing", "scaling", "seed", "series-a", "early-revenue")

    def mk(base, factors):
        """factors: list of (delta, '+'/'-', note). Returns (score, drivers sorted by impact)."""
        s = base + sum(d for d, _, _ in factors)
        drivers = [{"effect": e, "delta": int(d), "note": note} for d, e, note in factors if abs(d) >= 1]
        drivers.sort(key=lambda x: abs(x["delta"]), reverse=True)
        return _clamp(s), drivers[:4]

    # --- Digital Maturity ---
    dm, dm_dr = mk(0, [
        (sysn, "+" if sysn >= 45 else "-", f"Runs on {intake.get('systems_used') or 'mixed tools'}"),
        (sop, "+" if sop >= 10 else "-", f"SOPs: {intake.get('has_sops') or 'unclear'}"),
        (crm, "+" if crm >= 7 else "-", f"Customer system: {intake.get('has_crm') or 'none'}"),
        (5 if returns_ok else -4, "+" if returns_ok else "-", "Returns up to date" if returns_ok else "Returns behind/unsure"),
    ])

    # --- Risk & Resilience (higher = more resilient) ---
    risk_f = []
    if custdep is not None:
        risk_f.append((-26 if custdep >= 50 else (-15 if custdep > 30 else (6 if custdep <= 20 else -4)),
                       "-" if custdep > 30 else "+", f"Top customer = {custdep:.0f}% of revenue"))
    if suppdep is not None:
        risk_f.append((-12 if suppdep >= 50 else (-6 if suppdep > 35 else 4),
                       "-" if suppdep > 35 else "+", f"Top supplier = {suppdep:.0f}% of purchases"))
    risk_f.append((8 if gst_ok else -15, "+" if gst_ok else "-", "GST registered" if gst_ok else "GST not registered/unsure"))
    risk_f.append((4 if returns_ok else -10, "+" if returns_ok else "-", "Filings current" if returns_ok else "Filings behind"))
    risk_f.append((3 if lic_ok else -5, "+" if lic_ok else "-", "Licences current" if lic_ok else "Some licences pending"))
    if runway is not None:
        risk_f.append((6 if runway >= 12 else (-16 if runway < 3 else (-7 if runway < 6 else 0)),
                       "+" if runway >= 12 else "-", f"Cash runway {runway:.0f} months"))
    risk_f.append((owner - 10, "+" if owner >= 12 else "-", f"Owner-dependency: {intake.get('owner_dependency') or 'high'}"))
    if dead is not None and dead > 10:
        risk_f.append((-8, "-", f"{dead:.0f}% dead/slow stock"))
    risk, risk_dr = mk(72, risk_f)

    # --- Investment / Credit Readiness ---
    inv_f = []
    if g is not None and gm_mid is not None:
        inv_f.append((14 if g >= gm_mid else (5 if (gm_lo is not None and g >= gm_lo) else -10),
                      "+" if (gm_mid and g >= gm_lo) else "-", f"Gross margin {g:.0f}% vs sector ~{gm_lo:.0f}-{gm_hi:.0f}%" if gm_lo is not None else f"Gross margin {g:.0f}%"))
    if n is not None:
        inv_f.append((10 if n >= 8 else (-16 if n < 0 else 2), "+" if n >= 5 else "-", f"Net margin {n:.0f}%"))
    if dso is not None:
        inv_f.append((8 if dso <= 45 else (-12 if dso > 75 else 0), "+" if dso <= 45 else "-", f"DSO {dso:.0f} days"))
    inv_f.append((10 if sysn >= 55 else -8, "+" if sysn >= 55 else "-", "Books on Tally/ERP" if sysn >= 55 else "Books not system-grade"))
    inv_f.append((6 if returns_ok else -8, "+" if returns_ok else "-", "Compliance current" if returns_ok else "Compliance gaps"))
    if custdep is not None and custdep > 40:
        inv_f.append((-8, "-", f"Customer concentration {custdep:.0f}%"))
    if runway is not None:
        inv_f.append((6 if runway >= 12 else (-10 if runway < 3 else 0), "+" if runway >= 12 else "-", f"Runway {runway:.0f} mo"))
    inv, inv_dr = mk(50, inv_f)

    # --- Transformation Readiness (ability + appetite to change) ---
    tr, tr_dr = mk(40, [
        ((dm - 50) / 4.0, "+" if dm >= 50 else "-", f"Digital maturity {dm}/100"),
        (sop, "+" if sop >= 10 else "-", "Process discipline" if sop >= 10 else "Few SOPs to build on"),
        (owner, "+" if owner >= 12 else "-", "Team can execute change" if owner >= 12 else "Owner-bottlenecked"),
        (10 if growthy else -2, "+" if growthy else "-", f"Stage: {stage or 'steady'}"),
    ])

    # --- Growth Potential ---
    gr_f = [
        (8 if growthy else 0, "+" if growthy else " ", f"Stage: {stage or 'steady'}"),
        (8 if city in ("Pan-India", "Export") else (4 if city == "Metro" else 0), "+", f"Market: {city or 'local'}"),
        (6 if tier == 1 else (3 if tier == 2 else 0), "+", "High-opportunity sector" if tier == 1 else "Solid sector"),
    ]
    if repeat is not None:
        gr_f.append((8 if repeat >= 45 else (-4 if repeat < 25 else 0), "+" if repeat >= 45 else "-", f"Repeat rate {repeat:.0f}%"))
    if n is not None:
        gr_f.append((6 if n >= 6 else (-4 if n < 0 else 0), "+" if n >= 6 else "-", f"Profit to reinvest (net {n:.0f}%)"))
    if custdep is not None and custdep > 40:
        gr_f.append((-6, "-", "Concentration caps scalable growth"))
    gr, gr_dr = mk(50, gr_f)

    scores = [
        {"key": "investment_readiness", "label": "Investment Readiness", "icon": "💸", "score": inv, "band": _band(inv), "drivers": inv_dr},
        {"key": "risk_resilience", "label": "Risk & Resilience", "icon": "🛡️", "score": risk, "band": _band(risk), "drivers": risk_dr},
        {"key": "transformation", "label": "Transformation Readiness", "icon": "🔄", "score": tr, "band": _band(tr), "drivers": tr_dr},
        {"key": "digital_maturity", "label": "Digital Maturity", "icon": "📶", "score": dm, "band": _band(dm), "drivers": dm_dr},
        {"key": "growth", "label": "Growth Potential", "icon": "🚀", "score": gr, "band": _band(gr), "drivers": gr_dr},
    ]
    weights = {"investment_readiness": 0.25, "risk_resilience": 0.22, "transformation": 0.15, "digital_maturity": 0.18, "growth": 0.20}
    overall = _clamp(sum(s["score"] * weights[s["key"]] for s in scores))
    grade = "A" if overall >= 75 else ("B" if overall >= 60 else ("C" if overall >= 45 else "D"))
    return {"overall": overall, "grade": grade, "scores": scores}


# ============================================================
# 5b2. INDUSTRY BENCHMARKING — where each metric sits vs sector
# ============================================================
def _zone(value, t1, t2, direction):
    if direction == "higher_better":
        return "healthy" if value >= t2 else ("watch" if value >= t1 else "critical")
    return "healthy" if value <= t1 else ("watch" if value <= t2 else "critical")


def _gauge(label, value, unit, t1, t2, amin, amax, direction, note=""):
    span = (amax - amin) or 1
    v = max(amin, min(amax, value))
    seg = [round((t1 - amin) / span * 100, 1), round((t2 - t1) / span * 100, 1), round((amax - t2) / span * 100, 1)]
    return {"label": label, "value": value, "unit": unit, "direction": direction,
            "position_pct": round((v - amin) / span * 100, 1), "segments": seg,
            "zone": _zone(value, t1, t2, direction), "note": note}


def benchmark(intake, pb):
    """Plot the owner's actual numbers against sector / India-MSME benchmark bands."""
    out = []
    prof = pb.get("profitability_analysis", {}) if pb else {}
    glo, ghi = _numf(_low_pct(prof.get("typical_gross_margin"))), _numf(_high_pct(prof.get("typical_gross_margin")))
    nlo, nhi = _numf(_low_pct(prof.get("typical_net_margin"))), _numf(_high_pct(prof.get("typical_net_margin")))
    g = _numf(intake.get("gross_margin_pct"))
    if g is not None and glo is not None:
        hi = ghi or glo + 10
        out.append(_gauge("Gross margin", g, "%", glo, (glo + hi) / 2, 0, hi * 1.3, "higher_better", f"Sector ~{glo:.0f}-{hi:.0f}%"))
    n = _numf(intake.get("net_margin_pct"))
    if n is not None and nlo is not None:
        hi = nhi or nlo + 5
        out.append(_gauge("Net margin", n, "%", nlo, hi, -5, hi * 1.5, "higher_better", f"Sector ~{nlo:.0f}-{hi:.0f}%"))
    dso = _numf(intake.get("dso_days"))
    if dso is not None:
        out.append(_gauge("Collection period (DSO)", dso, " days", 45, 75, 0, 120, "lower_better", "Healthy < 45-60 days"))
    dead = _numf(intake.get("dead_stock_pct"))
    if dead is not None:
        out.append(_gauge("Dead / slow stock", dead, "%", 8, 15, 0, 30, "lower_better", "Healthy < 8%"))
    runway = _numf(intake.get("cash_runway_months"))
    if runway is not None:
        out.append(_gauge("Cash runway", runway, " mo", 6, 12, 0, 24, "higher_better", "Comfortable > 12 months"))
    cust = _numf(intake.get("top_customer_dep_pct"))
    if cust is not None:
        out.append(_gauge("Top-customer concentration", cust, "%", 20, 40, 0, 70, "lower_better", "Risk > 30-40%"))
    supp = _numf(intake.get("top_supplier_dep_pct"))
    if supp is not None:
        out.append(_gauge("Top-supplier concentration", supp, "%", 25, 45, 0, 80, "lower_better", "Risk > 35-45%"))
    rep = _numf(intake.get("repeat_rate_pct"))
    if rep is not None:
        out.append(_gauge("Repeat-customer rate", rep, "%", 30, 45, 0, 80, "higher_better", "Strong > 45%"))
    return out


# ============================================================
# 5b3. SWOT — synthesised from the whole engagement
# ============================================================
def swot(intake, pb, sc, bm, base):
    S, W, O, T = [], [], [], []
    for s in (sc.get("scores") or []):
        if s["band"] == "strong":
            S.append(f"Strong {s['label'].lower()} ({s['score']}/100)")
        elif s["band"] == "weak":
            W.append(f"Weak {s['label'].lower()} ({s['score']}/100)")
    for g in (bm or []):
        if g["zone"] == "healthy":
            S.append(f"{g['label']} {g['value']}{g['unit']} — ahead of sector")
        elif g["zone"] == "critical":
            W.append(f"{g['label']} {g['value']}{g['unit']} — below sector")
    if intake.get("systems_used") in ("Tally", "Tally + Excel", "An ERP"):
        S.append("System-based operations with data visibility")
    if intake.get("has_sops") in ("Mostly", "Yes - followed"):
        S.append("Documented SOPs / process discipline")
    if intake.get("systems_used") in ("Pen & paper", "Excel/Sheets", "WhatsApp + Excel"):
        W.append(f"Low system maturity ({intake.get('systems_used')})")
    if intake.get("owner_dependency") in ("Totally - I do everything", "High"):
        W.append("High owner-dependency / weak delegation")
    if intake.get("has_sops") in ("No", "A few"):
        W.append("Thin SOPs — inconsistent-execution risk")

    O.extend((base.get("opportunities") or [])[:4])
    if pb:
        for a in (pb.get("ai_automation_opportunities") or []):
            if a.get("impact") == "High" and a.get("opportunity"):
                O.append(f"Automate: {a['opportunity']}")
    if intake.get("city_tier") in ("Tier-2", "Tier-3", "Metro"):
        O.append("Geographic / channel expansion headroom")

    for r in (base.get("risks") or [])[:3]:
        if r.get("risk"):
            T.append(r["risk"])
    cust = _numf(intake.get("top_customer_dep_pct"))
    if cust and cust > 40:
        T.append(f"Customer concentration ({cust:.0f}% from one buyer)")
    supp = _numf(intake.get("top_supplier_dep_pct"))
    if supp and supp > 45:
        T.append(f"Supplier concentration ({supp:.0f}%)")
    if intake.get("gst_registered") in ("No", "Not sure") or intake.get("returns_current") in ("Behind", "Not sure"):
        T.append("Compliance exposure (GST / returns)")

    def cap(lst, n=5):
        seen, out = set(), []
        for x in lst:
            if x and x not in seen:
                seen.add(x); out.append(x)
            if len(out) >= n:
                break
        return out
    return {"strengths": cap(S), "weaknesses": cap(W), "opportunities": cap(O), "threats": cap(T)}


# ============================================================
# 5b4. 12-MONTH TRANSFORMATION ROADMAP
# ============================================================
def transformation_roadmap(intake, pb, base, sc):
    goal = intake.get("goals") or ""
    recs = base.get("tailored_recommendations") or []
    plan = base.get("action_plan_90day") or []
    autos = (pb.get("ai_automation_opportunities") if pb else []) or []
    growth = ((pb.get("growth_playbook") or {}).get("stages") if pb else []) or []
    bsol = (pb.get("bottleneck_solutions") if pb else []) or []
    dm = next((s["score"] for s in sc.get("scores", []) if s["key"] == "digital_maturity"), 50)
    grade = sc.get("grade", "C")

    q1 = [s for p in plan[:1] for s in (p.get("steps") or [])][:3] + [r["title"] for r in recs if r.get("priority") == "High"][:2]
    q2 = [f"Fix: {b.get('bottleneck')}" for b in bsol[:2]] + [r["title"] for r in recs if r.get("priority") == "Medium"][:2]
    q3 = [f"Automate: {a['opportunity']}" for a in autos if a.get("impact") in ("High", "Medium") and a.get("opportunity")][:3] + ((growth[0].get("plays") if growth else []) or [])[:1]
    q4 = ((growth[1].get("plays") if len(growth) > 1 else []) or [])[:2]
    if pb and pb.get("digital_maturity_model"):
        lvl = min(5, max(1, dm // 20 + 1))
        nm = next((m for m in pb["digital_maturity_model"] if m.get("level") == lvl), None)
        if nm and nm.get("next_step"):
            q4.append(nm["next_step"])

    def fill(lst, fallback):
        out, seen = [], set()
        for x in lst:
            if x and x not in seen:
                seen.add(x); out.append(x)
        return out[:4] or [fallback]

    to_grade = "A" if grade in ("A", "B") else "B"
    quarters = [
        {"quarter": "Q1", "window": "Months 0-3", "theme": "Stabilise & measure",
         "focus": "Stop the bleeding, get visibility, fix compliance",
         "initiatives": fill(q1, "Stand up the founder dashboard + weekly review"),
         "target": [f"Baseline the 5 DD scores (grade {grade}) and run a weekly cadence"]},
        {"quarter": "Q2", "window": "Months 3-6", "theme": "Fix the binding constraints",
         "focus": "Attack the top bottlenecks and the margin/cash leaks",
         "initiatives": fill(q2, "Resolve the #1 operational bottleneck"),
         "target": ["Move 2 weak scores up a band; recover working capital"]},
        {"quarter": "Q3", "window": "Months 6-9", "theme": "Optimise & automate",
         "focus": "Systematise and deploy AI agents on repetitive work",
         "initiatives": fill(q3, "Automate one repetitive workflow end-to-end"),
         "target": [f"Digital maturity {dm} → {min(100, dm + 15)}"]},
        {"quarter": "Q4", "window": "Months 9-12", "theme": "Scale & transform",
         "focus": "Pour fuel on what works; build for the next stage",
         "initiatives": fill(q4, "Resource the proven growth bet"),
         "target": [f"Lift overall DD grade toward {to_grade}"]},
    ]
    return {"north_star": goal or f"Transform into a more resilient, scalable {pb.get('name') if pb else 'business'}",
            "from_grade": grade, "to_grade": to_grade, "maturity_from": dm, "maturity_to": min(100, dm + 25),
            "quarters": quarters}


# ============================================================
# 5c. AI PMO — turn an engagement into a PM workspace
# ============================================================
# Converts the 90-day plan + recommendations + KPIs into an execution workspace:
# OKRs, six fortnightly sprints, tasks (owner / priority / dependencies), and
# milestones. Deterministic; the "workflow second" layer of the OS.
def _owner_for(text):
    t = (text or "").lower()
    if any(k in t for k in ("cash", "collection", "receivable", "dso", "margin", "gst", "tax", "finance", "working capital", "payment", "credit", "p&l", "pricing")):
        return "CFO / Finance"
    if any(k in t for k in ("sop", "process", "inventory", "stock", "supply", "procure", "ops", "operation", "quality", "cycle", "otif", "capacity", "warehouse", "fefo", "lead time", "downtime", "utilis")):
        return "COO / Operations"
    if any(k in t for k in ("sales", "customer", "crm", "growth", "market", "beat", "gtm", "retention", "lead", "brand", "channel", "footfall", "repeat")):
        return "Sales / Growth"
    if any(k in t for k in ("compliance", "licence", "license", "return", "filing", "schedule h", "rera", "fssai", "nabh", "audit")):
        return "Compliance"
    if any(k in t for k in ("product", "feature", "mvp", "roadmap", "release", "sprint", "nrr")):
        return "Product"
    if any(k in t for k in ("hire", "team", "payroll", "staff", "training", "attrition", "people")):
        return "HR / People"
    return "Founder / PMO"


def build_pmo(eng):
    """Engagement envelope -> PM workspace (OKRs, sprints, tasks, milestones)."""
    eng = eng or {}
    plan = eng.get("action_plan_90day") or []
    recs = eng.get("tailored_recommendations") or []
    kpis = eng.get("kpis") or []
    sector = eng.get("sector_name") or "the business"
    goal = eng.get("goals") or eng.get("goal") or ""

    phases = (plan or [])[:3]
    while len(phases) < 3:
        phases.append({"phase": f"Phase {len(phases) + 1}", "steps": []})
    windows = ["Weeks 1-2", "Weeks 3-4", "Weeks 5-6", "Weeks 7-8", "Weeks 9-10", "Weeks 11-12"]
    sprints = [{"id": f"S{i+1}", "name": f"Sprint {i+1}", "window": w, "goal": phases[i // 2].get("phase", "")}
               for i, w in enumerate(windows)]

    tasks = []

    def add_task(title, sprint_idx, priority, source, dep=None):
        if not title:
            return None
        tid = f"T{len(tasks)+1}"
        tasks.append({"id": tid, "title": title, "owner": _owner_for(title), "sprint": f"S{min(sprint_idx,5)+1}",
                      "priority": priority, "effort": "M", "status": "todo", "source": source,
                      "depends_on": [dep] if dep else []})
        return tid

    for p_i, p in enumerate(phases):
        prev = None
        for j, step in enumerate(p.get("steps") or []):
            sidx = p_i * 2 + (j % 2)
            prio = "High" if p_i == 0 else ("Medium" if p_i == 1 else "Normal")
            prev = add_task(step, sidx, prio, "90-day plan", dep=prev)
    for r in recs:
        prio = r.get("priority", "Medium")
        sidx = 0 if prio == "High" else (2 if prio == "Medium" else 4)
        add_task(r.get("title", ""), sidx, prio, "recommendation")

    krs = [{"kr": f"{k.get('kpi')} → {k.get('target')}", "owner": _owner_for(k.get("kpi", ""))} for k in kpis[:4]]
    objectives = [
        {"objective": goal or f"Execute the 90-day plan for {sector}",
         "key_results": krs or [{"kr": "Complete all 90-day plan tasks", "owner": "Founder / PMO"}]},
        {"objective": "Land the priority recommendations & retire top risks",
         "key_results": [{"kr": f"Ship {min(len(recs), 5) or 3} priority recommendations", "owner": "Founder / PMO"},
                         {"kr": "No High-severity risk left unmitigated", "owner": _owner_for("risk audit")}]},
    ]
    milestones = [
        {"name": f"{phases[0].get('phase', 'Day 30')} — complete", "sprint": "S2"},
        {"name": f"{phases[1].get('phase', 'Day 60')} — complete", "sprint": "S4"},
        {"name": f"{phases[2].get('phase', 'Day 90')} — complete", "sprint": "S6"},
    ]
    owners = sorted(set(t["owner"] for t in tasks))
    return {"objectives": objectives, "sprints": sprints, "tasks": tasks, "milestones": milestones,
            "owners": owners, "summary": {"tasks": len(tasks), "sprints": len(sprints), "weeks": 13, "sector": sector}}


# ============================================================
# 6. ORCHESTRATOR
# ============================================================
def consult(intake):
    """Main entry: intake (dict) -> customised engagement envelope. Never raises."""
    intake = intake or {}
    mode = intake.get("mode") or "existing"
    description = intake.get("description") or ""
    # Resolve the sector/playbook.
    key = (intake.get("business_type") or "").strip()
    pb, matched_key, how = (None, None, "none")
    if PB:
        pb, matched_key, how = PB.resolve(business_type=key or None, key=key or None, description=description or None)
    sector_name = pb.get("name") if pb else "General MSME"

    # Retrieval — playbook + live web + memory + the owner's own documents (RAG).
    search_q = f"{sector_name} India MSME {intake.get('specific_question') or intake.get('goals') or ''}".strip()
    web = web_search(search_q, max_results=6)
    recall = recall_similar(matched_key or key, description + " " + intake.get("top_challenges", ""))
    doc_query = " ".join([intake.get("specific_question", ""), intake.get("top_challenges", ""), description]).strip()
    doc_evidence = DOCS.search(doc_query, k=4, workspace=intake.get("workspace")) if DOCS else []

    # Base (deterministic, always personalised) then LLM enhancement merged on top.
    base = _deterministic_engagement(intake, pb, recall)
    engine = "deterministic"
    enhanced = _llm_enhance(intake, pb, web, recall, base, doc_evidence)
    if enhanced:
        for k in ("diagnosis", "tailored_recommendations", "quick_wins", "risks", "kpis", "action_plan_90day", "opportunities"):
            v = enhanced.get(k)
            if v:  # LLM value wins where present + non-empty
                base[k] = v
        engine = f"groq:{enhanced.get('_provider','llm')}"

    sc_data = dd_scores(intake, pb)
    bm_data = benchmark(intake, pb)
    swot_data = swot(intake, pb, sc_data, bm_data, base)
    roadmap_data = transformation_roadmap(intake, pb, base, sc_data)
    envelope = {
        "engagement_id": hashlib.sha1((description + str(time.time())).encode()).hexdigest()[:12],
        "mode": mode,
        "business_type": matched_key or key or None,
        "sector_name": sector_name,
        "matched_by": how,
        "engine": engine,
        "playbook_key": matched_key,
        "scorecard": sc_data,
        "benchmark": bm_data,
        "swot": swot_data,
        "roadmap": roadmap_data,
        **base,
        "sources": web,
        "doc_evidence": doc_evidence,
        "citations": (pb.get("citations_resolved") if pb else []) or [],
        "compliance": (pb.get("compliance_resolved") if pb else []) or [],
        "recall": recall,
        "playbook_link": f"/playbooks?key={matched_key}" if matched_key else None,
    }
    # Learn.
    saved = save_engagement(intake, envelope)
    envelope["learned"] = saved
    return envelope


if __name__ == "__main__":  # quick local smoke
    out = consult({"mode": "existing", "description": "8-store grocery retail chain in Pune",
                   "top_challenges": "stockouts\nthin margins", "turnover_cr": "12", "city_tier": "Tier-2",
                   "specific_question": "how do I improve margins?"})
    print("engine:", out["engine"], "| sector:", out["sector_name"], "| recs:", len(out["tailored_recommendations"]),
          "| sources:", len(out["sources"]), "| learned:", out["learned"])
