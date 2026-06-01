"""
PMGuru — Research-Grade MSME AI Agent Layer
===========================================
A new operating layer on top of the v12 consulting engine. Where the
consulting module produces Big-3/4 *engagement reports*, this layer produces
*operating copilots* that behave like Indian MSME consultants embedded inside
an ERP + Notion workspace.

DESIGN PRINCIPLES (consistent with main.py's template-driven philosophy):
  * Deterministic structure, India-specific knowledge, never a 500.
  * Every agent output is an AUDIT-READY ENVELOPE (the 16-part contract below)
    — no vague chatbot answers.
  * Every recommendation is citation-backed against real Indian statutes/sources.
  * Each agent declares which ERP modules it touches and which Notion
    databases it updates, so the platform can wire actions, not just text.
  * Agents are testable: golden-answer scenario benchmarks score accuracy,
    citation quality, hallucination risk, compliance coverage, and ERP-workflow
    validity BEFORE deployment.

This file is self-contained (no third-party deps) and is imported by main.py.
The vertical slice ships 3 flagship agents end-to-end (GST & Compliance,
CFO Finance, MSME Due Diligence); the remaining 17 are registered with full
metadata cards and marked "planned" so the platform surface is complete.
"""

# ============================================================
# 1. THE AUDIT-READY OUTPUT ENVELOPE
# ============================================================
# Every agent MUST return these keys. This is the contract that makes the
# agents "research-grade" rather than chatbots. Tests assert presence + quality.
ENVELOPE_KEYS = [
    "business_context",      # what we understood about the business
    "assumptions",           # explicit assumptions made (so they can be challenged)
    "required_data",         # data the agent needs; flags what is missing
    "clarifying_questions",  # questions to ask before acting (HITL)
    "analysis",              # the reasoning / numbers
    "risks",                 # {risk, severity, likelihood, control, owner}
    "recommendations",       # prioritized, specific, non-vague
    "action_plan",           # {step, owner, timeline, system}
    "erp_impact",            # which ERP modules change and how
    "notion_update",         # which Notion DBs get which entries
    "compliance_impact",     # statutory implications
    "kpis_to_monitor",       # {kpi, current, target, source}
    "citations",             # source-verified references
    "human_approval_points", # where a human must sign off
]


# ============================================================
# 2. ERP DATA MODEL — what a real MSME ERP holds
# ============================================================
# Agents reference these module keys in erp_impact so actions are concrete.
ERP_MODULES = {
    "master_data":  {"name": "Master Data",      "entities": ["Company", "Branch", "GSTIN", "Cost centers", "Chart of accounts"]},
    "customers":    {"name": "Customers",        "entities": ["Customer", "Ship-to/Bill-to", "Credit limit", "GSTIN", "Price list"]},
    "vendors":      {"name": "Vendors",          "entities": ["Vendor", "MSME status", "Payment terms", "Bank/UPI", "GSTIN"]},
    "products":     {"name": "Products / SKUs",  "entities": ["SKU", "HSN/SAC", "Batch", "Expiry", "UoM", "Tax rate"]},
    "inventory":    {"name": "Inventory",        "entities": ["Stock by location", "Batch ledger", "Reorder level", "Ageing", "Valuation"]},
    "purchase":     {"name": "Purchase",         "entities": ["Indent", "PO", "GRN", "Purchase invoice", "Debit note"]},
    "sales":        {"name": "Sales",            "entities": ["Quotation", "Sales order", "Delivery/E-way", "Invoice", "Credit note"]},
    "billing":      {"name": "Billing / GST",    "entities": ["Tax invoice", "E-invoice IRN", "E-way bill", "HSN summary"]},
    "finance":      {"name": "Finance / GL",     "entities": ["Journal", "Ledger", "Trial balance", "P&L", "Balance sheet"]},
    "receivables":  {"name": "Receivables (AR)", "entities": ["Outstanding", "Ageing buckets", "Collection", "Dunning"]},
    "payables":     {"name": "Payables (AP)",    "entities": ["Vendor outstanding", "MSME 45-day clock", "Payment run"]},
    "payroll":      {"name": "Payroll",          "entities": ["Employee", "Salary", "PF/ESI", "TDS", "Payslip"]},
    "compliance":   {"name": "Compliance",       "entities": ["GST returns", "TDS returns", "ROC filings", "Licenses", "Due dates"]},
    "approvals":    {"name": "Approvals",        "entities": ["Approval matrix", "Workflow state", "Maker-checker"]},
    "audit_logs":   {"name": "Audit Logs",       "entities": ["Who/what/when", "Field-level change history", "Document trail"]},
}


# ============================================================
# 3. NOTION WORKSPACE MODEL — what the operating workspace holds
# ============================================================
NOTION_DATABASES = {
    "founder_dashboard":   {"name": "Founder Dashboard",     "fields": ["Metric", "Value", "Trend", "Status", "Owner"]},
    "strategy_room":       {"name": "Strategy Room",         "fields": ["Initiative", "Thesis", "Owner", "Stage", "Impact"]},
    "dd_room":             {"name": "Due Diligence Room",    "fields": ["Item", "Category", "Status", "Finding", "Risk", "Evidence"]},
    "sop_repo":            {"name": "SOP Repository",        "fields": ["SOP", "Process", "Owner", "Version", "Last reviewed"]},
    "research_db":         {"name": "Research Database",     "fields": ["Question", "Finding", "Source", "Confidence", "Date"]},
    "investor_workspace":  {"name": "Investor Workspace",    "fields": ["Doc", "Type", "Status", "Audience", "Owner"]},
    "meeting_notes":       {"name": "Meeting Notes",         "fields": ["Date", "Attendees", "Decisions", "Action items"]},
    "task_tracker":        {"name": "Task Tracker",          "fields": ["Task", "Owner", "Due", "Priority", "Status", "Source"]},
    "risk_register":       {"name": "Risk Register",         "fields": ["Risk", "Severity", "Likelihood", "Control", "Owner", "Status"]},
    "compliance_tracker":  {"name": "Compliance Tracker",    "fields": ["Obligation", "Authority", "Due date", "Status", "Owner", "Evidence"]},
    "ai_reco_log":         {"name": "AI Recommendations Log","fields": ["Agent", "Recommendation", "Rationale", "Accepted?", "Date"]},
    "decision_history":    {"name": "Decision History",      "fields": ["Decision", "Options considered", "Rationale", "Owner", "Date"]},
    "kpi_db":              {"name": "KPI Database",          "fields": ["KPI", "Current", "Target", "Owner", "Source"]},
}


# ============================================================
# 4. CITATION LIBRARY — real Indian statutory / authoritative sources
# ============================================================
# Citations are keyed; agents reference keys so every claim is traceable.
# `tier`: A = statute/government portal, B = regulator guidance, C = benchmark/industry.
CITATIONS = {
    "cgst_act":        {"title": "CGST Act, 2017", "ref": "Central Goods and Services Tax Act, 2017", "authority": "Govt. of India", "url": "https://cbic-gst.gov.in", "tier": "A"},
    "gst_portal":      {"title": "GST Portal", "ref": "Returns: GSTR-1, GSTR-3B, GSTR-2B reconciliation", "authority": "GSTN", "url": "https://www.gst.gov.in", "tier": "A"},
    "einvoice":        {"title": "E-Invoicing Mandate", "ref": "E-invoice (IRN) mandatory for AATO > Rs.5 cr (Notification 10/2023-CT)", "authority": "CBIC", "url": "https://einvoice.gst.gov.in", "tier": "A"},
    "eway":            {"title": "E-Way Bill Rules", "ref": "Rule 138 CGST Rules — consignment > Rs.50,000", "authority": "NIC/CBIC", "url": "https://ewaybillgst.gov.in", "tier": "A"},
    "itc_rules":       {"title": "ITC Eligibility", "ref": "Sec 16 CGST Act — ITC only on GSTR-2B reflected invoices; Sec 17(5) blocked credits", "authority": "CBIC", "url": "https://cbic-gst.gov.in", "tier": "A"},
    "income_tax":      {"title": "Income-tax Act, 1961", "ref": "TDS Chapter XVII-B; advance tax; Sec 44AB tax audit", "authority": "CBDT", "url": "https://incometax.gov.in", "tier": "A"},
    "sec_43b_h":       {"title": "Section 43B(h), Income-tax Act", "ref": "Disallowance of expense if MSME supplier not paid within 45 days (w.e.f. AY 2024-25)", "authority": "CBDT", "url": "https://incometax.gov.in", "tier": "A"},
    "companies_act":   {"title": "Companies Act, 2013", "ref": "ROC filings AOC-4 (financials), MGT-7 (annual return), DIR-3 KYC", "authority": "MCA", "url": "https://www.mca.gov.in", "tier": "A"},
    "msmed_act":       {"title": "MSMED Act, 2006", "ref": "Sec 15-16 — 45-day payment + compound interest; Udyam classification", "authority": "M/o MSME", "url": "https://udyamregistration.gov.in", "tier": "A"},
    "udyam":           {"title": "Udyam Registration", "ref": "MSME classification: Micro/Small/Medium by investment + turnover", "authority": "M/o MSME", "url": "https://udyamregistration.gov.in", "tier": "A"},
    "dgft_iec":        {"title": "IEC & Foreign Trade Policy 2023", "ref": "Importer-Exporter Code; FTP 2023; RoDTEP/Duty drawback", "authority": "DGFT", "url": "https://www.dgft.gov.in", "tier": "A"},
    "epfo":            {"title": "EPF & MP Act, 1952", "ref": "12% PF contribution; ECR filing by 15th; applicable >= 20 employees", "authority": "EPFO", "url": "https://www.epfindia.gov.in", "tier": "A"},
    "esic":            {"title": "ESI Act, 1948", "ref": "ESI for wages <= Rs.21,000; employer 3.25% + employee 0.75%", "authority": "ESIC", "url": "https://www.esic.gov.in", "tier": "A"},
    "fssai":           {"title": "FSS Act, 2006 (FSSAI)", "ref": "Food licence/registration by turnover slab; labelling & hygiene norms", "authority": "FSSAI", "url": "https://www.fssai.gov.in", "tier": "A"},
    "drugs_act":       {"title": "Drugs & Cosmetics Act, 1940", "ref": "Schedule H/H1 sale records; retail/wholesale drug licence (Form 20/21)", "authority": "CDSCO/State FDA", "url": "https://cdsco.gov.in", "tier": "A"},
    "startup_india":   {"title": "Startup India / DPIIT", "ref": "DPIIT recognition (entity < 10 yrs, turnover < Rs.100 cr, innovative/scalable)", "authority": "DPIIT", "url": "https://www.startupindia.gov.in", "tier": "A"},
    "sec_80iac":       {"title": "Section 80-IAC, Income-tax Act", "ref": "100% profit tax holiday for any 3 consecutive of first 10 yrs; needs DPIIT + IMB certificate", "authority": "CBDT", "url": "https://www.startupindia.gov.in", "tier": "A"},
    "angel_tax":       {"title": "Angel Tax Exemption — Sec 56(2)(viib)", "ref": "DPIIT-recognised startups exempt from angel tax on share premium (subject to conditions/declaration)", "authority": "CBDT/DPIIT", "url": "https://www.startupindia.gov.in", "tier": "A"},
    "sisfs":           {"title": "Startup India Seed Fund Scheme (SISFS)", "ref": "Up to Rs.20L grant (PoC) + up to Rs.50L (commercialization) via approved incubators", "authority": "DPIIT", "url": "https://seedfund.startupindia.gov.in", "tier": "A"},
    "state_startup":   {"title": "State Startup / IT Policy Incentives", "ref": "State subsidies: patent reimbursement, lease rental, SGST refund, electricity duty waiver (varies by state)", "authority": "State Govt", "url": "", "tier": "B"},
    "meity_ai":        {"title": "MeitY / IndiaAI & DPDP Act, 2023", "ref": "Digital Personal Data Protection Act 2023 obligations; IndiaAI Mission compute/grant support", "authority": "MeitY", "url": "https://www.meity.gov.in", "tier": "A"},
    "benchmark_saas":  {"title": "SaaS metrics benchmark", "ref": "Healthy: net revenue retention > 100%, gross margin > 70%, burn multiple < 1.5", "authority": "Industry", "url": "", "tier": "C"},
    "rbi_msme":        {"title": "RBI MSME Lending Norms", "ref": "Priority sector lending; TReDS for receivables discounting", "authority": "RBI", "url": "https://www.rbi.org.in", "tier": "B"},
    "shops_act":       {"title": "Shops & Establishments Act (State)", "ref": "State-specific registration, working hours, leave rules", "authority": "State Labour Dept", "url": "", "tier": "A"},
    "benchmark_ar":    {"title": "Working-capital benchmark", "ref": "Indian MSME DSO typically 45-90 days; healthy < 60", "authority": "Industry", "url": "", "tier": "C"},
    "benchmark_d2c":   {"title": "D2C unit-economics benchmark", "ref": "Sustainable LTV:CAC >= 3:1; CAC payback < 12 months", "authority": "Industry", "url": "", "tier": "C"},
    "customs":         {"title": "Customs Act, 1962 (Imports)", "ref": "Bill of Entry, BCD + IGST + cess; ICEGATE filing; IGST on imports creditable as ITC", "authority": "CBIC Customs", "url": "https://www.icegate.gov.in", "tier": "A"},
    "apeda":           {"title": "APEDA Registration", "ref": "RCMC for export of scheduled agro/processed-food products; quality & packaging norms", "authority": "APEDA", "url": "https://apeda.gov.in", "tier": "A"},
    "fieo":            {"title": "FIEO / RCMC", "ref": "Registration-cum-Membership Certificate from Export Promotion Council for FTP benefits", "authority": "FIEO/EPC", "url": "https://www.fieo.org", "tier": "B"},
    "factory_license": {"title": "Factories Act, 1948", "ref": "Factory licence + safety/working-hours norms; applies to manufacturing units above worker thresholds", "authority": "State Factories Dept", "url": "", "tier": "A"},
    "rera":            {"title": "RERA, 2016", "ref": "Project & agent registration for real estate; escrow of 70% of buyer funds", "authority": "State RERA", "url": "", "tier": "A"},
    "nabh":            {"title": "NABH Accreditation", "ref": "Hospital/clinic quality accreditation; often required for insurer empanelment", "authority": "NABH/QCI", "url": "https://nabh.co", "tier": "B"},
    "bis":             {"title": "BIS / ISI & Quality Control Orders", "ref": "Mandatory BIS certification for notified products (incl. many imports) under QCOs", "authority": "BIS", "url": "https://www.bis.gov.in", "tier": "A"},
    "prof_tax":        {"title": "Professional Tax (State)", "ref": "State-levied PT deducted from salaries; slabs and due dates vary by state", "authority": "State Govt", "url": "", "tier": "A"},
    "labour_codes":    {"title": "Labour Codes, 2019-20", "ref": "Code on Wages, Industrial Relations, Social Security, OSH — consolidating 29 labour laws", "authority": "M/o Labour", "url": "https://labour.gov.in", "tier": "A"},
    "gratuity":        {"title": "Payment of Gratuity Act, 1972", "ref": "Gratuity payable after 5 yrs service; 15 days' wages per completed year", "authority": "M/o Labour", "url": "", "tier": "A"},
    "tds_salary":      {"title": "TDS on Salary — Sec 192", "ref": "Employer deducts TDS on salary; deposit by 7th, file Form 24Q quarterly, issue Form 16", "authority": "CBDT", "url": "https://incometax.gov.in", "tier": "A"},
    "ibef":            {"title": "IBEF Sectoral Reports", "ref": "India Brand Equity Foundation — sector size, growth and structure data", "authority": "IBEF (Dept of Commerce)", "url": "https://www.ibef.org", "tier": "B"},
    "contract_act":    {"title": "Indian Contract Act, 1872", "ref": "Validity, consideration, breach, indemnity, termination of agreements", "authority": "Govt. of India", "url": "", "tier": "A"},
    "stamp_act":       {"title": "Indian Stamp Act, 1899 (State)", "ref": "Stamp duty on agreements; unstamped/under-stamped docs inadmissible as evidence", "authority": "State Govt", "url": "", "tier": "A"},
    "consumer_protection": {"title": "Consumer Protection Act, 2019", "ref": "Deficiency-in-service & product liability; warranty/repair obligations; e-commerce & unfair-trade rules; CCPA jurisdiction", "authority": "Dept of Consumer Affairs", "url": "https://consumeraffairs.nic.in", "tier": "A"},
    "ewaste":          {"title": "E-Waste (Management) Rules, 2022", "ref": "Extended Producer Responsibility (EPR) for electronics; authorised collection/recycling; CPCB EPR portal registration", "authority": "MoEFCC / CPCB", "url": "https://eprewastecpcb.in", "tier": "A"},
}


# ============================================================
# 5. FINANCIAL / INDUSTRY BENCHMARKS (deterministic reference)
# ============================================================
BENCHMARKS = {
    "dso_days":            {"healthy": "< 60 days", "watch": "60-90 days", "critical": "> 90 days", "cite": "benchmark_ar"},
    "inventory_turns":     {"healthy": "> 6x/yr",   "watch": "4-6x/yr",   "critical": "< 4x/yr",   "cite": "benchmark_ar"},
    "gross_margin_retail": {"healthy": "18-25%",    "watch": "12-18%",    "critical": "< 12%",     "cite": "benchmark_ar"},
    "gross_margin_pharma": {"healthy": "8-20%",     "watch": "5-8%",      "critical": "< 5%",      "cite": "benchmark_ar"},
    "ltv_cac":             {"healthy": ">= 3:1",    "watch": "2-3:1",     "critical": "< 2:1",     "cite": "benchmark_d2c"},
    "current_ratio":       {"healthy": "1.5-2.5",   "watch": "1.0-1.5",   "critical": "< 1.0",     "cite": "benchmark_ar"},
    "saas_gross_margin":   {"healthy": "> 70%",     "watch": "55-70%",    "critical": "< 55%",     "cite": "benchmark_saas"},
    "net_revenue_ret":     {"healthy": "> 100%",    "watch": "85-100%",   "critical": "< 85%",     "cite": "benchmark_saas"},
    "burn_multiple":       {"healthy": "< 1.5",     "watch": "1.5-2.5",   "critical": "> 2.5",     "cite": "benchmark_saas"},
}


# ============================================================
# 6. BUSINESS CLASSIFIER — India MSME aware
# ============================================================
_INDUSTRY_KEYWORDS = {
    "pharma":        ["pharma", "chemist", "medicine", "drug", "schedule h", "distributor pharma", "medical store", "api ", "surgical"],
    "retail":        ["kirana", "retail", "shop", "store", "pos", "fmcg", "grocery", "supermarket", "showroom"],
    "wholesale":     ["wholesale", "distribution", "distributor", "dealer", "beat", "secondary sales", "stockist", "c&f"],
    "manufacturing": ["manufactur", "factory", "production", "bom", "wip", "machining", "assembly", "fabrication", "molding", "processing unit"],
    "agro_export":   ["agro", "farm", "mandi", "commodity", "spices", "spice", "rice", "basmati", "makhana", "foxnut", "tea", "coffee", "marine", "apeda",
                       "turmeric", "garlic", "chilli", "chili", "ginger", "dried", "dehydrated", "dehydration", "beetroot", "onion", "pulses", "grain", "oilseed", "cumin", "coriander", "masala"],
    "import_export": ["import", "merchant export", "trading company", "sourcing", "global seller", "cross-border", "customs", "bill of entry", "icegate"],
    "logistics":     ["logistics", "transport", "trucking", "fleet", "freight", "warehouse", "cold chain", "courier", "last mile", "cargo", "cha"],
    "construction":  ["construction", "builder", "real estate developer", "civil contractor", "interior", "hvac", "rera"],
    "healthcare":    ["hospital", "clinic", "diagnostic", "lab", "telemedicine", "wellness", "nabh"],
    "food_bev":      ["restaurant", "cloud kitchen", "cafe", "bakery", "catering", "tiffin", "packaged food", "ice cream", "beverage", "dairy", "food company", "food processing", "fmcg food", "snack", "frozen food", "ready to eat"],
    "education":     ["coaching", "school", "edtech", "skill training", "test prep", "vocational"],
    "d2c":           ["d2c", "ecommerce", "e-commerce", "marketplace", "amazon", "flipkart", "shopify", "ad spend", "cac", "quick commerce"],
    "tech_saas":     ["saas", "ai startup", "ai/saas", "software", "platform", "app", "api", "ml ", "machine learning", "deeptech", "fintech", "healthtech", "edtech", "legaltech", "b2b software", "tech startup", "cybersecurity"],
    "services":      ["service", "agency", "consult", "it services", "law firm", "ca firm", "staffing", "bpo", "kpo", "marketing"],
}

# Words that mark an early-stage / DPIIT-eligible startup (drives govt-incentive logic).
_STARTUP_HINTS = ["startup", "founder", "seed", "pre-seed", "angel", "vc", "venture", "raise", "funding round", "dpiit", "incubator", "mvp", "arr", "burn"]

_SIZE_HINTS = {
    "micro":  ["kirana", "single shop", "proprietor", "small shop"],
    "small":  ["small business", "msme", "few crore"],
    "medium": ["multi-branch", "distributor", "factory", "exporter"],
}


def classify_business(description: str) -> dict:
    """Lightweight India-MSME classifier. Deterministic, no LLM."""
    d = (description or "").lower()
    industry = "services"
    best = 0
    for ind, kws in _INDUSTRY_KEYWORDS.items():
        hits = sum(1 for k in kws if k in d)
        if hits > best:
            best, industry = hits, ind
    size = "small"
    for sz, kws in _SIZE_HINTS.items():
        if any(k in d for k in kws):
            size = sz
            break
    is_tech = industry == "tech_saas" or any(k in d for k in ("ai", "saas", "software", "platform"))
    is_import = "import" in d or "bill of entry" in d or "customs" in d
    is_export = "export" in d or "iec" in d or industry == "agro_export"
    if is_import and is_export:
        trade_role = "import_export_hybrid"
    elif is_import:
        trade_role = "import"
    elif is_export:
        trade_role = "export"
    else:
        trade_role = "domestic"
    return {
        "industry": industry,
        "size": size,
        "trade_role": trade_role,
        "is_import": is_import,
        "is_export": is_export,
        "is_regulated": industry in ("pharma", "agro_export", "healthcare", "food_bev", "construction") or "fssai" in d or "food" in d,
        "is_tech": is_tech,
        "is_startup": is_tech or any(k in d for k in _STARTUP_HINTS),
        "is_ai": "ai" in d.split() or "artificial intelligence" in d or "machine learning" in d or "ai startup" in d or "ai/saas" in d,
    }


# ============================================================
# 6b. BUSINESS-TYPE TAXONOMY + COMPLIANCE MAP (India MSME)
# ============================================================
# Reference data surfaced via /agents/meta so the platform and agents share one
# vocabulary of business types, operating models, and the compliance each implies.
BUSINESS_TAXONOMY = {
    "manufacturing": ["Food Processing", "Textile/Garment", "Leather", "Plastic/Rubber", "Metal Fabrication",
                       "Furniture", "Packaging/Paper", "Printing", "Electrical/Electronics", "Auto Parts",
                       "Pharma/Ayurvedic/Cosmetic", "Chemical/Paint", "Machinery", "Solar/LED", "Medical Devices",
                       "Handicraft/Handloom", "Jewellery", "Sports Goods", "Toys"],
    "retail":        ["Kirana", "Supermarket/Hypermarket", "Pharmacy", "Apparel/Footwear", "Jewellery",
                       "Electronics/Mobile", "Furniture/Hardware/Paint", "Agro Retail", "Auto Showroom/Spares",
                       "Cosmetics", "Books/Stationery/Gifts", "Home Decor", "E-commerce/D2C", "Quick Commerce"],
    "wholesale":     ["FMCG", "Pharma", "Agro Commodity", "Electrical/Hardware", "Textile", "Building Material",
                       "Auto Parts", "Mobile/Electronics", "Chemical", "Medical Equipment", "Cosmetic",
                       "Beverage/Dairy/Frozen"],
    "distribution_models": ["Super Stockist", "Distributor", "Sub-Distributor", "Dealer", "Wholesaler",
                            "C&F", "Redistribution Stockist", "Franchise Distribution"],
    "import":        ["Machinery/Industrial Equipment", "CNC/Robotics", "Semiconductors", "Electronics/Mobile",
                       "Apparel/Cosmetics/Luxury/Toys", "Chemicals/Plastic Granules/Metals", "Fabric/Yarn/Timber/Pulp",
                       "Pulses/Dry Fruits/Edible Oil/Seafood", "APIs/Medical/Diagnostic", "Servers/IT/Networking"],
    "export":        ["Rice/Basmati/Millet/Makhana", "Spices/Tea/Coffee", "Marine/Meat/Poultry/Dairy",
                       "Fruits & Veg/Organic", "Garments/Cotton/Silk/Handloom/Carpets", "Engineering/Auto/Machinery",
                       "Chemicals/Plastics", "Generic Medicines/APIs/Ayurvedic", "IT/SaaS/BPO/KPO/AI Services",
                       "Handicrafts/Jewellery/Furniture/Home Decor"],
    "import_export_hybrid": ["Global Trading Co", "Merchant Exporter", "Import-Export House", "Commodity Trader",
                             "Cross-border E-commerce", "Amazon Global Seller", "Sourcing Company"],
    "agro_rural":    ["Organic/Contract Farming", "Hydroponics/Greenhouse", "Dairy/Poultry/Fisheries/Goat/Bee",
                       "Mushroom", "Millet/Foxnut Processing", "Cold Storage/Warehousing", "Seed/Fertilizer", "Agro Equipment Rental"],
    "food_bev":      ["Restaurants/Cloud Kitchens/Cafes", "Bakery/Sweets", "Catering/Tiffin", "Packaged/Frozen Foods",
                       "Snacks/Beverages", "Dairy/Ice Cream"],
    "logistics":     ["Transport/Trucking", "Cold Chain", "Warehousing", "Freight Forwarding", "CHA", "Shipping Agency",
                       "Cargo/Courier", "Last Mile", "E-commerce/Port/Air/Rail Logistics"],
    "construction":  ["Real Estate Developers", "Builders/Civil Contractors", "Interior Designers", "HVAC/Fire/Security",
                       "Plumbing/Electrical Contractors", "Smart Building Automation"],
    "technology":    ["SaaS", "AI Startups", "ERP/CRM", "FinTech/HealthTech/EdTech/LegalTech", "Supply Chain Tech",
                       "AI Agent Platforms", "Cybersecurity/Cloud", "App Dev", "Data Analytics"],
    "professional_services": ["CA/Audit/Tax", "Law Firms", "HR/Staffing", "Architecture", "Digital Marketing/Advertising",
                              "BPO/KPO", "Insurance Agencies"],
    "healthcare":    ["Clinics/Hospitals", "Diagnostic Labs", "Pharmacies", "Telemedicine", "Wellness", "Medical Equipment"],
    "education":     ["Coaching Centers", "Schools", "Skill/Vocational Training", "Online Learning", "Test Prep"],
    "media_creative":["Animation/VFX/Gaming", "Film/Music Production", "Publishing", "Graphic Design",
                       "Influencer Agencies", "YouTube/Media"],
    "tourism":       ["Hotels/Resorts/Homestays", "Travel Agencies/Tour Operators", "Event/Wedding Management"],
    "real_estate":   ["Property Management", "Brokerage", "Rental Management", "Co-working", "Facility Management"],
    "operating_models": ["B2B", "B2C", "D2C", "Marketplace", "Franchise", "Subscription", "Trading",
                          "Manufacturing", "Aggregator", "Export-Oriented Unit"],
}

# Industry/role -> the compliance regimes that typically bind it (citation keys).
COMPLIANCE_MAP = {
    "all":           ["udyam", "gst_portal", "income_tax", "shops_act"],
    "manufacturing": ["factory_license", "bis", "gst_portal"],
    "retail":        ["gst_portal", "shops_act"],
    "wholesale":     ["gst_portal", "eway"],
    "pharma":        ["drugs_act", "gst_portal"],
    "food_bev":      ["fssai", "gst_portal"],
    "agro_export":   ["apeda", "dgft_iec", "fieo"],
    "import":        ["customs", "dgft_iec", "bis"],
    "export":        ["dgft_iec", "fieo", "apeda"],
    "import_export_hybrid": ["customs", "dgft_iec", "fieo"],
    "logistics":     ["eway", "gst_portal"],
    "construction":  ["rera", "gst_portal"],
    "healthcare":    ["nabh", "drugs_act"],
    "technology":    ["meity_ai", "startup_india"],
    "education":     ["gst_portal", "shops_act"],
}

# Government & trade-ecosystem bodies + enterprise systems to benchmark against.
GOV_BODIES = ["M/o MSME", "DGFT", "FIEO", "APEDA", "GST Council", "CBIC", "CBDT", "MCA", "SEBI", "RBI", "DPIIT", "MeitY", "BIS", "FSSAI", "CDSCO", "EPFO", "ESIC"]
ENTERPRISE_BENCHMARKS = ["SAP", "Oracle", "Microsoft Dynamics", "NetSuite", "Zoho", "Odoo", "Tally", "Blue Yonder", "Kinaxis"]


def compliance_for(cls: dict) -> list:
    """Resolve the compliance citation keys that bind a classified business."""
    keys = list(COMPLIANCE_MAP["all"])
    keys += COMPLIANCE_MAP.get(cls.get("industry"), [])
    if cls.get("trade_role") in COMPLIANCE_MAP:
        keys += COMPLIANCE_MAP[cls["trade_role"]]
    # de-dupe, keep order
    seen, out = set(), []
    for k in keys:
        if k not in seen and k in CITATIONS:
            seen.add(k); out.append(k)
    return out


# ============================================================
# 7. ENVELOPE HELPERS
# ============================================================
def _cite(*keys):
    """Resolve citation keys to full reference dicts; de-dupe, skip unknown keys."""
    seen, out = set(), []
    for k in keys:
        if k in CITATIONS and k not in seen:
            seen.add(k)
            out.append({"key": k, **CITATIONS[k]})
    return out


# Keys that may legitimately be empty: pure research/strategy agents
# (market research, competitor intel, product PRD) touch no ERP module.
# The key must still be PRESENT (honest "no ERP impact"), just may be empty.
_OPTIONAL_EMPTY_KEYS = {"erp_impact"}


def _validate_envelope(env: dict) -> list:
    """Return list of missing required keys (used by tests).
    A key is 'missing' if absent entirely, or empty when it is not allowed to be."""
    missing = []
    for k in ENVELOPE_KEYS:
        if k not in env:
            missing.append(k)
            continue
        v = env.get(k)
        if v in (None, "", [], {}) and k not in _OPTIONAL_EMPTY_KEYS:
            missing.append(k)
    return missing


# ============================================================
# 8. AGENT REGISTRY — 20 research-grade MSME copilots
# ============================================================
# Each card declares the operating contract. `generator` (set later for live
# agents) produces the audit-ready envelope. `status`: "live" | "planned".
MSME_AGENTS = {
    "ceo_copilot": {
        "name": "CEO Copilot Agent", "icon": "🧭", "status": "planned",
        "purpose": "Translate founder intent into strategy, priorities, and a weekly operating cadence.",
        "business_types": ["all"],
        "inputs_required": ["Business goals", "P&L summary", "Top initiatives"],
        "tools_connected": ["KPI engine", "Strategy room", "OKR builder"],
        "erp_modules": ["finance", "audit_logs"],
        "notion_databases": ["founder_dashboard", "strategy_room", "decision_history"],
        "kpis_improved": ["Revenue growth", "Operating margin", "Initiative throughput"],
        "example_scenario": "Founder asks: 'What are my top 3 priorities this quarter given cash is tight?'",
    },
    "coo_operations": {
        "name": "COO Operations Agent", "icon": "⚙️", "status": "planned",
        "purpose": "Find operational bottlenecks and standardize workflows + SOPs.",
        "business_types": ["retail", "wholesale", "manufacturing", "services"],
        "inputs_required": ["Process map", "Throughput data", "Headcount"],
        "tools_connected": ["Process mining", "SOP generator"],
        "erp_modules": ["purchase", "sales", "inventory", "approvals"],
        "notion_databases": ["sop_repo", "task_tracker", "risk_register"],
        "kpis_improved": ["Cycle time", "On-time delivery", "Rework %"],
        "example_scenario": "Distributor order-to-delivery takes 6 days; target 2 days.",
    },
    "cfo_finance": {
        "name": "CFO Finance Agent", "icon": "💰", "status": "live",
        "purpose": "Cash flow, working capital, receivables, profitability and funding readiness for an MSME.",
        "business_types": ["all"],
        "inputs_required": ["P&L", "Balance sheet", "AR/AP ageing", "Bank balance"],
        "tools_connected": ["Ratio engine", "Working-capital model", "Benchmark library"],
        "erp_modules": ["finance", "receivables", "payables", "billing"],
        "notion_databases": ["founder_dashboard", "kpi_db", "ai_reco_log", "decision_history"],
        "kpis_improved": ["DSO", "Cash conversion cycle", "Gross margin", "Current ratio"],
        "example_scenario": "Wholesaler with Rs.2 cr stuck in receivables and a cash crunch before GST payment.",
    },
    "gst_compliance": {
        "name": "GST & Compliance Agent", "icon": "🧾", "status": "live",
        "purpose": "Keep the business GST-correct and statutorily compliant; catch ITC leakage and filing risk.",
        "business_types": ["all"],
        "inputs_required": ["GSTIN", "Turnover (AATO)", "Sales/purchase registers", "Filing status"],
        "tools_connected": ["GSTR-2B reconciler", "Due-date calendar", "HSN validator"],
        "erp_modules": ["billing", "compliance", "purchase", "sales"],
        "notion_databases": ["compliance_tracker", "risk_register", "ai_reco_log"],
        "kpis_improved": ["ITC claimed %", "Return filing on-time %", "Notice exposure"],
        "example_scenario": "Trader with Rs.8 cr turnover not on e-invoicing and ITC mismatches in GSTR-2B.",
    },
    "erp_consultant": {
        "name": "ERP Consultant Agent", "icon": "🗄️", "status": "planned",
        "purpose": "Recommend & configure the right ERP modules and master data for the business type.",
        "business_types": ["all"],
        "inputs_required": ["Current systems", "Pain points", "Transaction volume"],
        "tools_connected": ["ERP module map", "Data model designer"],
        "erp_modules": list(ERP_MODULES.keys()),
        "notion_databases": ["sop_repo", "decision_history"],
        "kpis_improved": ["Process automation %", "Data accuracy", "Manual effort hrs"],
        "example_scenario": "Manufacturer on spreadsheets wants ERP for BOM + production + GST.",
    },
    "msme_due_diligence": {
        "name": "MSME Due Diligence Agent", "icon": "🔍", "status": "live",
        "purpose": "Produce an investor/acquirer/lender-ready due-diligence pack across finance, legal, compliance, ops — and for AI/SaaS/tech startups, assess DPIIT/Startup-India incentive eligibility and tech-specific risks.",
        "business_types": ["all", "tech_saas", "d2c"],
        "inputs_required": ["Financials (3 yrs)", "Cap table", "Licenses", "Contracts", "GST/ITR filings", "DPIIT status (if startup)", "ARR/metrics (if SaaS)", "IP/ESOP details (if tech)"],
        "tools_connected": ["DD checklist engine", "Red-flag scanner", "Benchmark library", "Govt-incentive eligibility checker"],
        "erp_modules": ["finance", "compliance", "receivables", "payables", "audit_logs"],
        "notion_databases": ["dd_room", "risk_register", "investor_workspace", "decision_history"],
        "kpis_improved": ["DD readiness score", "Open red flags", "Data-room completeness", "Incentive capture"],
        "example_scenario": "Investor evaluating an AI/SaaS startup before a Rs.5 cr cheque; needs red flags + which govt benefits (80-IAC, angel-tax, SISFS) the company qualifies for.",
    },
    "market_research": {
        "name": "Market Research Agent", "icon": "📈", "status": "planned",
        "purpose": "TAM/SAM/SOM, demand signals, and India market structure with sources.",
        "business_types": ["all"],
        "inputs_required": ["Category", "Geography", "Target segment"],
        "tools_connected": ["Web research", "Citation engine"],
        "erp_modules": [],
        "notion_databases": ["research_db", "strategy_room"],
        "kpis_improved": ["Market sizing confidence", "Segment coverage"],
        "example_scenario": "Founder wants TAM for B2B logistics SaaS in Tier-2 India.",
    },
    "competitor_intel": {
        "name": "Competitor Intelligence Agent", "icon": "🎯", "status": "planned",
        "purpose": "Map competitors, pricing, positioning and find white space.",
        "business_types": ["all"],
        "inputs_required": ["Competitor names", "Category", "Pricing data"],
        "tools_connected": ["Web research", "Pricing scraper"],
        "erp_modules": [],
        "notion_databases": ["research_db", "strategy_room"],
        "kpis_improved": ["Win rate", "Price realization"],
        "example_scenario": "D2C brand losing share; needs competitor pricing teardown.",
    },
    "product_manager": {
        "name": "Product Manager Agent", "icon": "🧩", "status": "planned",
        "purpose": "Turn problems into PRDs, roadmaps and RICE-prioritized backlogs.",
        "business_types": ["d2c", "services"],
        "inputs_required": ["Problem", "Users", "Constraints"],
        "tools_connected": ["RICE scorer", "PRD generator"],
        "erp_modules": [],
        "notion_databases": ["task_tracker", "strategy_room"],
        "kpis_improved": ["Feature throughput", "Time-to-launch"],
        "example_scenario": "SaaS founder needs a prioritized 90-day roadmap.",
    },
    "notion_workspace": {
        "name": "Notion Workspace Agent", "icon": "🗂️", "status": "planned",
        "purpose": "Create and maintain the Notion operating workspace; sync AI outputs to the right DBs.",
        "business_types": ["all"],
        "inputs_required": ["Workspace goals", "Team roles"],
        "tools_connected": ["Notion API", "Template library"],
        "erp_modules": [],
        "notion_databases": list(NOTION_DATABASES.keys()),
        "kpis_improved": ["Workspace adoption", "Action-item closure"],
        "example_scenario": "Set up a founder + investor + DD workspace from scratch.",
    },
    "sop_agent": {
        "name": "SOP Agent", "icon": "📋", "status": "planned",
        "purpose": "Generate role-specific, audit-ready SOPs per process.",
        "business_types": ["all"],
        "inputs_required": ["Process name", "Roles", "Systems"],
        "tools_connected": ["SOP generator", "Process mining"],
        "erp_modules": ["approvals"],
        "notion_databases": ["sop_repo"],
        "kpis_improved": ["Process consistency", "Onboarding time"],
        "example_scenario": "Pharma wholesaler needs an SOP for batch-expiry handling.",
    },
    "risk_audit": {
        "name": "Risk & Audit Agent", "icon": "🛡️", "status": "planned",
        "purpose": "Maintain a live risk register and run control/audit checks.",
        "business_types": ["all"],
        "inputs_required": ["Process map", "Controls", "Incident history"],
        "tools_connected": ["RAID logger", "Control tester"],
        "erp_modules": ["audit_logs", "approvals", "finance"],
        "notion_databases": ["risk_register", "compliance_tracker"],
        "kpis_improved": ["Open high risks", "Control coverage"],
        "example_scenario": "Owner wants to know where cash/inventory fraud could happen.",
    },
    "inventory_agent": {
        "name": "Inventory Agent", "icon": "📦", "status": "planned",
        "purpose": "Optimize stock, reorder points, ageing and dead-stock.",
        "business_types": ["retail", "wholesale", "pharma", "manufacturing"],
        "inputs_required": ["SKU master", "Stock on hand", "Sales velocity"],
        "tools_connected": ["Reorder model", "Ageing analyzer"],
        "erp_modules": ["inventory", "purchase", "products"],
        "notion_databases": ["task_tracker", "kpi_db"],
        "kpis_improved": ["Inventory turns", "Dead stock %", "Stockout rate"],
        "example_scenario": "Kirana store has Rs.3 lakh dead stock and frequent stockouts.",
    },
    "sales_gtm": {
        "name": "Sales & GTM Agent", "icon": "🚀", "status": "planned",
        "purpose": "Design GTM motion, beat plans, pricing and channel strategy.",
        "business_types": ["wholesale", "d2c", "services"],
        "inputs_required": ["Sales data", "Channels", "Pricing"],
        "tools_connected": ["GTM planner", "Pricing model"],
        "erp_modules": ["sales", "customers"],
        "notion_databases": ["strategy_room", "kpi_db"],
        "kpis_improved": ["CAC", "Conversion", "Revenue/rep"],
        "example_scenario": "Distributor needs a salesman beat plan for 200 outlets.",
    },
    "procurement_agent": {
        "name": "Procurement Agent", "icon": "🛒", "status": "planned",
        "purpose": "Optimize purchasing, vendor performance and PO-to-GRN workflow.",
        "business_types": ["manufacturing", "wholesale", "retail"],
        "inputs_required": ["Vendor master", "PO history", "Quality data"],
        "tools_connected": ["Vendor scorecard", "PO workflow"],
        "erp_modules": ["purchase", "vendors", "inventory"],
        "notion_databases": ["task_tracker", "risk_register"],
        "kpis_improved": ["PO cycle time", "Vendor OTIF", "Cost savings"],
        "example_scenario": "Factory faces raw-material delays; needs vendor performance view.",
    },
    "customer_support": {
        "name": "Customer Support Agent", "icon": "💬", "status": "planned",
        "purpose": "Triage tickets, draft responses, track SLAs.",
        "business_types": ["d2c", "services"],
        "inputs_required": ["Ticket data", "SLA policy"],
        "tools_connected": ["Ticket triager", "Response drafter"],
        "erp_modules": ["customers", "sales"],
        "notion_databases": ["task_tracker"],
        "kpis_improved": ["First response time", "CSAT", "SLA breach %"],
        "example_scenario": "D2C brand drowning in WhatsApp return queries.",
    },
    "hr_payroll": {
        "name": "HR & Payroll Agent", "icon": "👥", "status": "planned",
        "purpose": "Payroll, PF/ESI, TDS and labour-law compliance.",
        "business_types": ["all"],
        "inputs_required": ["Employee master", "Salary structure", "Attendance"],
        "tools_connected": ["Payroll engine", "Statutory calculator"],
        "erp_modules": ["payroll", "compliance"],
        "notion_databases": ["compliance_tracker", "task_tracker"],
        "kpis_improved": ["Payroll accuracy", "Statutory on-time %"],
        "example_scenario": "Factory crossing 20 employees must start EPF compliance.",
    },
    "export_compliance": {
        "name": "Export Compliance Agent", "icon": "🌐", "status": "planned",
        "purpose": "IEC, export docs, incentives and buyer due diligence.",
        "business_types": ["agro_export", "manufacturing"],
        "inputs_required": ["IEC", "Product/HSN", "Destination", "Buyer"],
        "tools_connected": ["FTP rule engine", "Doc checklist"],
        "erp_modules": ["compliance", "sales", "billing"],
        "notion_databases": ["compliance_tracker", "dd_room"],
        "kpis_improved": ["Doc compliance %", "Incentive capture"],
        "example_scenario": "Spice exporter to UAE unsure about RoDTEP and docs.",
    },
    "legal_contracts": {
        "name": "Legal Contracts Agent", "icon": "📜", "status": "planned",
        "purpose": "Review/draft contracts, flag clauses and obligations.",
        "business_types": ["all"],
        "inputs_required": ["Contract text", "Party details"],
        "tools_connected": ["Clause library", "Obligation extractor"],
        "erp_modules": ["compliance", "vendors", "customers"],
        "notion_databases": ["risk_register", "compliance_tracker"],
        "kpis_improved": ["Contract turnaround", "Obligation tracking"],
        "example_scenario": "Founder reviewing a distributor agreement for risky clauses.",
    },
    "investor_readiness": {
        "name": "Investor Readiness Agent", "icon": "🏦", "status": "planned",
        "purpose": "Build the data room, metrics narrative and pitch readiness.",
        "business_types": ["d2c", "services", "manufacturing"],
        "inputs_required": ["Financials", "Metrics", "Cap table", "Pitch"],
        "tools_connected": ["Data-room builder", "Metrics validator"],
        "erp_modules": ["finance", "compliance"],
        "notion_databases": ["investor_workspace", "dd_room", "kpi_db"],
        "kpis_improved": ["Investor readiness score", "Data-room completeness"],
        "example_scenario": "Founder raising seed needs a clean data room in 2 weeks.",
    },
}


# ============================================================
# 9. SCENARIO HELPERS
# ============================================================
import re as _re

def _num(text, *patterns):
    """Best-effort numeric extraction from a scenario (e.g. 'Rs.2 cr')."""
    t = (text or "").lower()
    for p in patterns:
        m = _re.search(p, t)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                continue
    return None

def _bench(metric):
    b = BENCHMARKS[metric]
    return {"metric": metric, "healthy": b["healthy"], "watch": b["watch"], "critical": b["critical"]}


# ============================================================
# 10. FLAGSHIP GENERATOR — GST & COMPLIANCE AGENT
# ============================================================
def gen_gst_compliance(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    aato = data.get("turnover_cr") or _num(desc, r"rs\.?\s*([0-9.]+)\s*cr", r"turnover[^0-9]*([0-9.]+)\s*cr")
    on_einvoice = data.get("on_einvoice")
    mismatch = data.get("itc_mismatch") or ("mismatch" in desc.lower() or "2b" in desc.lower())

    # e-invoice threshold logic (Rs.5 cr AATO)
    einvoice_needed = (aato is not None and aato >= 5)
    einvoice_gap = einvoice_needed and on_einvoice is not True

    risks = [
        {"risk": "Input Tax Credit (ITC) claimed on invoices not reflected in GSTR-2B",
         "severity": "High", "likelihood": "High" if mismatch else "Medium",
         "control": "Monthly GSTR-2B vs purchase-register reconciliation before filing GSTR-3B; hold ITC on unmatched invoices.",
         "owner": "Accounts/GST in-charge", "cite": "itc_rules"},
        {"risk": "Late / non-filing of GSTR-1 / GSTR-3B attracting interest (18% p.a.) and late fee",
         "severity": "High", "likelihood": "Medium",
         "control": "Automated due-date calendar with reminders; lock books by 10th/20th.",
         "owner": "GST in-charge", "cite": "gst_portal"},
        {"risk": "Wrong HSN/SAC or tax rate on invoices",
         "severity": "Medium", "likelihood": "Medium",
         "control": "HSN master validation at SKU level; rate audit quarterly.",
         "owner": "Billing", "cite": "cgst_act"},
    ]
    if einvoice_gap:
        risks.insert(0, {
            "risk": f"E-invoicing not implemented despite AATO ~Rs.{aato} cr (mandatory above Rs.5 cr) — invoices may be treated as invalid, buyer ITC blocked",
            "severity": "Critical", "likelihood": "High",
            "control": "Onboard to IRP, generate IRN+QR on every B2B invoice immediately.",
            "owner": "Finance Head", "cite": "einvoice"})

    recs = []
    if einvoice_gap:
        recs.append("Go live on e-invoicing (IRP/IRN) within 7 days — currently a critical statutory gap above the Rs.5 cr threshold.")
    recs += [
        "Run a 3-way reconciliation each month: purchase register ↔ GSTR-2B ↔ GSTR-3B; claim ITC only on 2B-matched invoices (Sec 16).",
        "Validate blocked credits under Sec 17(5) (motor vehicles, personal use, CSR) are not being claimed.",
        "Set up a statutory due-date calendar: GSTR-1 (11th), GSTR-3B (20th), and reconcile e-way bills to invoices.",
    ]
    if cls["is_export"]:
        recs.append("For exports, file under LUT (zero-rated) and track GST refund claims; reconcile with shipping bills on ICEGATE.")
    if cls["is_import"]:
        recs.append("For imports, claim IGST paid at customs (Bill of Entry) as ITC — reconcile BoE data in GSTR-2B with ICEGATE; ensure BCD/cess and HSN classification are correct.")

    return {
        "business_context": f"{cls['size'].title()} {cls['industry'].replace('_',' ')} business"
                            + (f" with annual turnover ~Rs.{aato} cr." if aato else " (turnover not stated).")
                            + " GST correctness and on-time filing are the immediate compliance surface.",
        "assumptions": [
            "Business is GST-registered (regular scheme, not composition) unless stated otherwise.",
            f"AATO assumed ~Rs.{aato} cr from input." if aato else "Turnover band unknown — flagged in required_data.",
            "Books are maintained in an accounting/ERP system that can export registers.",
        ],
        "required_data": [
            {"item": "GSTIN(s) and registration type", "have": bool(data.get("gstin")), "why": "Determines return set and place-of-supply rules."},
            {"item": "Annual Aggregate Turnover (AATO)", "have": aato is not None, "why": "Drives e-invoicing/QRMP thresholds."},
            {"item": "Last 3 months GSTR-1, GSTR-3B, GSTR-2B", "have": False, "why": "Reconciliation and filing-status check."},
            {"item": "Purchase & sales registers", "have": False, "why": "ITC matching and HSN validation."},
        ],
        "clarifying_questions": [
            "What was your AATO in the previous financial year (to confirm e-invoicing/QRMP applicability)?",
            "Are you on the regular or composition scheme, and do you have multiple GSTINs (states)?",
            "Do you currently reconcile GSTR-2B before claiming ITC, or claim on books?",
        ],
        "analysis": {
            "einvoice_status": "MANDATORY and missing" if einvoice_gap else ("Mandatory and assumed in place" if einvoice_needed else "Not yet mandatory (AATO below Rs.5 cr or unknown)"),
            "itc_risk": "High — mismatches indicated" if mismatch else "Standard — reconcile monthly",
            "filing_cadence": "Monthly GSTR-1 + GSTR-3B (or QRMP if AATO <= Rs.5 cr)",
            "interest_exposure": "Interest @18% p.a. on late tax + late fees apply on delayed returns.",
        },
        "risks": risks,
        "recommendations": recs,
        "action_plan": [
            {"step": "Pull GSTR-2B and purchase register; build reconciliation sheet", "owner": "Accountant", "timeline": "Day 1-2", "system": "ERP billing + GST portal"},
            {"step": "Onboard to e-invoicing (if AATO >= Rs.5 cr) and test IRN generation", "owner": "Finance Head", "timeline": "Day 1-7", "system": "IRP / ERP billing"},
            {"step": "Configure statutory due-date calendar with maker-checker", "owner": "GST in-charge", "timeline": "Week 1", "system": "Compliance module"},
            {"step": "Quarterly HSN/rate audit", "owner": "Billing", "timeline": "Quarterly", "system": "Products/SKU master"},
        ],
        "erp_impact": [
            {"module": "billing", "change": "Enable e-invoice IRN+QR generation; enforce HSN/SAC + tax rate at invoice creation."},
            {"module": "compliance", "change": "Add GST return calendar, store filed returns, track due dates and ARNs."},
            {"module": "purchase", "change": "Tag each purchase invoice with GSTR-2B match status; block ITC on unmatched."},
            {"module": "sales", "change": "Auto-generate e-way bills for consignments > Rs.50,000."},
        ],
        "notion_update": [
            {"database": "compliance_tracker", "entry": "GST obligations (GSTR-1/3B/2B) with authorities, due dates, owners, evidence links."},
            {"database": "risk_register", "entries": [r["risk"] for r in risks]},
            {"database": "ai_reco_log", "entry": "GST & Compliance Agent recommendations with statutory rationale."},
        ],
        "compliance_impact": "Directly affects GST liability, ITC eligibility (Sec 16/17(5)), and exposure to interest/penalty and departmental notices (ASMT-10, DRC). E-invoicing non-compliance can invalidate invoices and block customers' ITC.",
        "kpis_to_monitor": [
            {"kpi": "Return filing on-time %", "current": "TBD", "target": "100%", "source": "GST portal"},
            {"kpi": "ITC matched % (2B vs books)", "current": "TBD", "target": "> 98%", "source": "Reconciliation"},
            {"kpi": "Notices / mismatches open", "current": "TBD", "target": "0", "source": "GST portal"},
        ],
        "citations": _cite(*(["cgst_act", "gst_portal", "einvoice", "eway", "itc_rules"] + compliance_for(cls))),
        "human_approval_points": [
            "CA/Finance Head sign-off before filing GSTR-3B and before claiming any disputed ITC.",
            "Authorised signatory approval to onboard a new GSTIN to e-invoicing.",
        ],
    }


# ============================================================
# 11. FLAGSHIP GENERATOR — CFO FINANCE AGENT
# ============================================================
def gen_cfo_finance(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    ar_cr = data.get("receivables_cr") or _num(desc, r"rs\.?\s*([0-9.]+)\s*cr\b.*receivab", r"receivab[^0-9]*rs\.?\s*([0-9.]+)\s*cr")
    revenue_cr = data.get("revenue_cr") or _num(desc, r"revenue[^0-9]*rs\.?\s*([0-9.]+)\s*cr", r"turnover[^0-9]*([0-9.]+)\s*cr")
    dso = data.get("dso_days")
    if dso is None and ar_cr and revenue_cr and revenue_cr > 0:
        dso = round((ar_cr / revenue_cr) * 365, 0)
    cash_crunch = "cash crunch" in desc.lower() or "cash flow" in desc.lower() or "tight" in desc.lower() or bool(data.get("cash_crunch"))

    margin_metric = "saas_gross_margin" if cls["is_tech"] else ("gross_margin_pharma" if cls["industry"] == "pharma" else "gross_margin_retail")

    risks = [
        {"risk": f"High receivables tying up working capital (DSO ~{int(dso)} days)" if dso else "Receivables ageing not tracked",
         "severity": "High" if (dso and dso > 90) else "Medium", "likelihood": "High",
         "control": "Ageing buckets + dunning workflow; enforce credit limits; consider TReDS / bill discounting.",
         "owner": "CFO / Accounts", "cite": "benchmark_ar"},
        {"risk": "Cash runway not forecast — payment obligations (GST, payroll, vendors) may not be funded",
         "severity": "Critical" if cash_crunch else "Medium", "likelihood": "High" if cash_crunch else "Medium",
         "control": "13-week rolling cash-flow forecast; prioritise statutory dues (GST/TDS/PF).",
         "owner": "CFO", "cite": "benchmark_ar"},
        {"risk": "MSME vendor payments beyond 45 days → expense disallowance under Sec 43B(h)",
         "severity": "High", "likelihood": "Medium",
         "control": "Tag MSME (Udyam) vendors; enforce 45-day payment clock in AP.",
         "owner": "Accounts Payable", "cite": "sec_43b_h"},
    ]

    recs = []
    if cash_crunch:
        recs.append("Build a 13-week cash-flow forecast immediately and rank outflows: statutory dues (GST/TDS/PF) first, then critical vendors and payroll.")
    if ar_cr:
        recs.append(f"Attack the Rs.{ar_cr} cr receivables: segment by ageing, run a focused collection drive on >90-day buckets, and discount eligible invoices on TReDS to release cash within days.")
    recs += [
        "Set customer-level credit limits in the ERP and block dispatches that breach them (maker-checker override only).",
        f"Track gross margin against the {cls['industry'].replace('_',' ')} benchmark and protect it via price/discount governance.",
        "Tag all Udyam-registered MSME vendors and pay within 45 days to avoid Sec 43B(h) disallowance at year-end.",
    ]

    return {
        "business_context": f"{cls['size'].title()} {cls['industry'].replace('_',' ')} business"
                            + (f" with ~Rs.{revenue_cr} cr revenue" if revenue_cr else "")
                            + (f" and ~Rs.{ar_cr} cr in receivables" if ar_cr else "")
                            + (". Cash flow is the stated pain point." if cash_crunch else ". Focus is working-capital and profitability health."),
        "assumptions": [
            "Figures provided are current-year; prior-year comparatives not available.",
            f"DSO derived as AR/Revenue×365 ≈ {int(dso)} days." if dso else "DSO unknown — receivables and revenue both needed.",
            "Statutory dues (GST/TDS/PF) are non-negotiable and rank first in any cash prioritisation.",
        ],
        "required_data": [
            {"item": "P&L and Balance Sheet (current + prior year)", "have": bool(data.get("pnl")), "why": "Margin, ratio and trend analysis."},
            {"item": "AR & AP ageing reports", "have": ar_cr is not None, "why": "Working-capital and Sec 43B(h) exposure."},
            {"item": "Bank balance & sanctioned limits", "have": bool(data.get("bank_balance")), "why": "Runway and funding-gap calc."},
            {"item": "Revenue (for DSO)", "have": revenue_cr is not None, "why": "Receivable-days computation."},
        ],
        "clarifying_questions": [
            "What is your current bank balance and any sanctioned CC/OD limit?",
            "What are your monthly fixed outflows (payroll, rent, EMIs) and the next big statutory due date?",
            "What credit terms do you offer customers, and which customers are the largest overdue balances?",
        ],
        "analysis": {
            "dso_days": int(dso) if dso else "unknown (need AR + revenue)",
            "dso_benchmark": _bench("dso_days"),
            "gross_margin_benchmark": _bench(margin_metric),
            "working_capital_lever": f"Releasing Rs.{round(ar_cr*0.3,2)} cr (~30% of receivables) would materially ease the crunch." if ar_cr else "Quantify once receivables are segmented by ageing.",
            "priority": "Stabilise cash (forecast + collections) before any growth spend." if cash_crunch else "Optimise working-capital cycle and protect margin.",
        },
        "risks": risks,
        "recommendations": recs,
        "action_plan": [
            {"step": "Build 13-week rolling cash-flow forecast", "owner": "CFO/Accountant", "timeline": "Day 1-3", "system": "finance"},
            {"step": "Generate AR ageing; launch collection drive on >90-day buckets", "owner": "Accounts", "timeline": "Week 1", "system": "receivables"},
            {"step": "Tag MSME vendors (Udyam) and set 45-day payment alerts", "owner": "AP", "timeline": "Week 1", "system": "payables"},
            {"step": "Configure customer credit limits + dispatch block", "owner": "CFO", "timeline": "Week 2", "system": "customers/sales"},
            {"step": "Evaluate TReDS / invoice discounting for fast cash", "owner": "CFO", "timeline": "Week 2-3", "system": "receivables"},
        ],
        "erp_impact": [
            {"module": "receivables", "change": "Enable ageing buckets, dunning workflow, and collection tracking."},
            {"module": "payables", "change": "Flag Udyam MSME vendors; enforce 45-day payment clock with alerts."},
            {"module": "finance", "change": "Cash-flow forecast view; ratio dashboard (DSO, current ratio, gross margin)."},
            {"module": "customers", "change": "Credit limits with dispatch-block on breach."},
        ],
        "notion_update": [
            {"database": "founder_dashboard", "entry": "Cash position, DSO, gross margin, runway — refreshed weekly."},
            {"database": "kpi_db", "entries": ["DSO", "Cash conversion cycle", "Gross margin", "Current ratio"]},
            {"database": "risk_register", "entries": [r["risk"] for r in risks]},
            {"database": "ai_reco_log", "entry": "CFO Finance Agent recommendations + rationale."},
        ],
        "compliance_impact": "Sec 43B(h) disallows expenses to MSME vendors unpaid beyond 45 days, increasing taxable income — a direct tax cost. Delayed GST/TDS payment triggers interest and penalty. Cash prioritisation must never starve statutory dues.",
        "kpis_to_monitor": [
            {"kpi": "DSO (days)", "current": int(dso) if dso else "TBD", "target": "< 60", "source": "AR ledger"},
            {"kpi": "Gross margin %", "current": "TBD", "target": BENCHMARKS[margin_metric]["healthy"], "source": "P&L"},
            {"kpi": "Cash runway (weeks)", "current": "TBD", "target": "> 13", "source": "Cash forecast"},
            {"kpi": "MSME payments within 45 days %", "current": "TBD", "target": "100%", "source": "AP ledger"},
        ],
        "citations": _cite("sec_43b_h", "msmed_act", "rbi_msme", "benchmark_ar", *(["benchmark_saas"] if cls["is_tech"] else [])),
        "human_approval_points": [
            "Founder/CFO approval before drawing on credit lines or discounting receivables.",
            "Owner sign-off on any customer credit-limit override.",
        ],
    }


# ============================================================
# 12. GOVERNMENT INCENTIVE ELIGIBILITY (India startup/MSME benefits)
# ============================================================
def _govt_incentives(cls: dict, desc: str) -> list:
    """Map a business to Indian government subsidies/benefits it likely qualifies for.
    Critical for AI/SaaS/tech startup DD — these benefits materially change valuation,
    runway and tax. Each item is a CLAIM TO VERIFY, not a guarantee."""
    out = []
    if cls["is_startup"] or cls["is_tech"]:
        out += [
            {"benefit": "DPIIT Recognition (Startup India)", "value": "Gateway to all startup benefits below; self-certification on labour/environment laws",
             "eligibility": "Entity < 10 yrs old, turnover < Rs.100 cr, working on innovation/scalability", "cite": "startup_india"},
            {"benefit": "Sec 80-IAC — 3-year income-tax holiday", "value": "100% profit deduction for any 3 of first 10 years",
             "eligibility": "DPIIT-recognised + Inter-Ministerial Board (IMB) certificate; incorporated as Pvt Ltd/LLP after 01-Apr-2016", "cite": "sec_80iac"},
            {"benefit": "Angel Tax exemption — Sec 56(2)(viib)", "value": "Share-premium raises not taxed as income",
             "eligibility": "DPIIT-recognised + declaration in Form 2; aggregate paid-up capital + premium <= Rs.25 cr (with carve-outs)", "cite": "angel_tax"},
            {"benefit": "Startup India Seed Fund Scheme (SISFS)", "value": "Up to Rs.20L (PoC/prototype) + up to Rs.50L (commercialization via debt/convertible)",
             "eligibility": "DPIIT-recognised, < 2 yrs at application, via approved incubator", "cite": "sisfs"},
            {"benefit": "State Startup / IT Policy incentives", "value": "Patent-cost reimbursement, lease-rental subsidy, SGST refund, electricity-duty waiver (state-specific)",
             "eligibility": "Registration under the relevant state startup/IT policy", "cite": "state_startup"},
        ]
    if cls["is_ai"]:
        out.append({"benefit": "IndiaAI Mission support + DPDP Act readiness", "value": "Access to subsidised GPU/compute, datasets, and grants; data-protection compliance is now a DD checklist item",
                    "eligibility": "AI/ML product companies; DPDP Act 2023 applies to all processing personal data", "cite": "meity_ai"})
    # Every Indian MSME (incl. tech) should hold Udyam for MSME benefits
    out.append({"benefit": "Udyam (MSME) Registration", "value": "Priority-sector credit, collateral-free loans (CGTMSE), 45-day payment protection, govt-tender preference",
                "eligibility": "Investment + turnover within MSME limits", "cite": "udyam"})
    return out


# ============================================================
# 13. FLAGSHIP GENERATOR — MSME / STARTUP DUE DILIGENCE AGENT
# ============================================================
def gen_due_diligence(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    is_tech_dd = cls["is_tech"] or cls["is_startup"]
    incentives = _govt_incentives(cls, desc)

    # DD checklist categories
    categories = ["Financial", "Tax & GST", "Legal & Corporate", "Compliance & Licenses", "Operations", "Commercial"]
    if is_tech_dd:
        categories += ["Tech / IP / Data", "Cap Table & ESOP", "SaaS Metrics", "Govt Incentives"]

    # Red flags (the value of DD is finding these)
    red_flags = [
        {"flag": "GST/ITR filings not reconciled with audited financials (revenue mismatch)", "category": "Tax & GST", "severity": "High", "cite": "gst_portal"},
        {"flag": "Related-party transactions not disclosed / not at arm's length", "category": "Financial", "severity": "High", "cite": "companies_act"},
        {"flag": "ROC filings (AOC-4/MGT-7) overdue → penalties + 'active non-compliant' status", "category": "Legal & Corporate", "severity": "Medium", "cite": "companies_act"},
        {"flag": "Statutory dues (PF/ESI/TDS/GST) in arrears — hidden liability", "category": "Compliance & Licenses", "severity": "High", "cite": "epfo"},
        {"flag": "Receivables concentration / ageing — revenue quality risk", "category": "Commercial", "severity": "Medium", "cite": "benchmark_ar"},
    ]
    if is_tech_dd:
        red_flags += [
            {"flag": "IP not assigned to the company (founder/contractor holds code/model weights)", "category": "Tech / IP / Data", "severity": "Critical", "cite": "companies_act"},
            {"flag": "Cap table messy — verbal ESOP promises, no ESOP pool, SAFE/CCD terms unclear", "category": "Cap Table & ESOP", "severity": "High", "cite": "startup_india"},
            {"flag": "ARR quality: one-time/services revenue counted as recurring; high churn masked", "category": "SaaS Metrics", "severity": "High", "cite": "benchmark_saas"},
            {"flag": "DPDP Act 2023 non-compliance / no data-processing agreements / training data provenance unclear", "category": "Tech / IP / Data", "severity": "High", "cite": "meity_ai"},
            {"flag": "Claimed govt benefits (80-IAC/angel-tax) without valid DPIIT/IMB certificate — tax exposure if reversed", "category": "Govt Incentives", "severity": "High", "cite": "sec_80iac"},
        ]

    recs = ["Assemble a structured data room mirroring the DD categories; mark each item Received/Pending/N-A."]
    if is_tech_dd:
        recs += [
            "Verify IP assignment: confirm all code, models, and datasets are owned by the company via signed assignment/IP clauses in every founder & contractor agreement.",
            "Validate ARR/retention from raw invoices and contracts — separate recurring from one-time and services; compute net revenue retention and churn.",
            "Confirm DPIIT recognition and, for each claimed benefit (80-IAC, angel-tax, SISFS), check the supporting certificate — these materially change post-money economics and tax exposure.",
            "Assess DPDP Act 2023 readiness and training-data provenance (especially for AI models) as a standing diligence item.",
        ]
    recs += [
        "Reconcile 3 years of GST returns and ITRs to audited financials; investigate any revenue/turnover gaps.",
        "Confirm all statutory dues (GST/TDS/PF/ESI) are paid to date; quantify any arrears as a deal liability.",
        "Verify ROC filing status and 'active compliant' standing on MCA.",
    ]

    readiness = "Low — multiple categories unverified" if not data.get("data_room") else "Partial — data room exists, pending verification"

    return {
        "business_context": ("AI/SaaS/tech startup" if is_tech_dd else f"{cls['size']} {cls['industry'].replace('_',' ')} business")
                            + " under due diligence for "
                            + (data.get("purpose") or "investment / acquisition / lending")
                            + ". Objective: surface red flags, quantify hidden liabilities, and confirm what the business legitimately qualifies for.",
        "assumptions": [
            "Diligence is pre-transaction; access to a data room will be granted.",
            "Financials are (or will be) audited; unaudited numbers are treated as management-certified only.",
            "Government-incentive items are eligibility CLAIMS to verify against certificates, not confirmed entitlements.",
        ],
        "required_data": [
            {"item": "3 years audited financials + provisional current year", "have": bool(data.get("financials")), "why": "Revenue quality, margins, liabilities."},
            {"item": "GST returns + ITRs (3 yrs)", "have": False, "why": "Reconcile to financials; find revenue gaps."},
            {"item": "Cap table, shareholder agreements, ESOP pool", "have": bool(data.get("cap_table")), "why": "Ownership, dilution, option overhang."},
            {"item": "Licenses, ROC filings, statutory challans", "have": False, "why": "Compliance standing and arrears."},
            {"item": "Customer contracts + revenue cohorts" if is_tech_dd else "Top customer/vendor contracts", "have": False, "why": "Revenue durability and concentration."},
        ] + ([
            {"item": "IP assignment agreements (founders + contractors)", "have": False, "why": "Confirm company owns code/models — a deal-breaker if not."},
            {"item": "DPIIT recognition + IMB/80-IAC/angel-tax certificates", "have": bool(data.get("dpiit")), "why": "Validate claimed government benefits."},
            {"item": "Product/AI metrics: ARR, churn, NRR, gross margin", "have": False, "why": "SaaS revenue-quality and unit economics."},
        ] if is_tech_dd else []),
        "clarifying_questions": [
            "What is the transaction type and target valuation/ticket size?",
            "Are the last 3 years' financials audited, and by whom?",
        ] + ([
            "Is the company DPIIT-recognised, and which government benefits has it already claimed (80-IAC, angel-tax, SISFS)?",
            "Is all IP (code, model weights, datasets) formally assigned to the company?",
            "How is ARR defined internally, and what is monthly logo + revenue churn?",
        ] if is_tech_dd else [
            "Which licenses are core to operations, and are any due for renewal?",
        ]),
        "analysis": {
            "dd_categories": categories,
            "readiness_assessment": readiness,
            "red_flag_count": len(red_flags),
            "critical_flags": [r["flag"] for r in red_flags if r["severity"] == "Critical"],
            "incentive_upside": (f"{len(incentives)} government benefit(s) potentially available — verify certificates."
                                 if incentives else "No specific incentives mapped."),
            "valuation_note": ("For AI/SaaS: value rests on recurring-revenue quality, retention, IP ownership and the tax shield from 80-IAC — each must be verified, not assumed."
                               if is_tech_dd else "Value rests on normalized EBITDA, working-capital cycle and clean compliance."),
        },
        "risks": [
            {"risk": rf["flag"], "severity": rf["severity"],
             "likelihood": "Medium", "control": "Verify in data room; quantify as deal liability or condition precedent.",
             "owner": "DD Lead", "cite": rf["cite"]}
            for rf in red_flags
        ],
        "recommendations": recs,
        "action_plan": [
            {"step": "Issue DD checklist + data-room request list by category", "owner": "DD Lead", "timeline": "Day 1", "system": "dd_room"},
            {"step": "Reconcile GST/ITR to financials; flag gaps", "owner": "Finance DD", "timeline": "Week 1", "system": "finance/compliance"},
            {"step": "Verify statutory dues paid; quantify arrears", "owner": "Compliance DD", "timeline": "Week 1", "system": "compliance"},
        ] + ([
            {"step": "Verify IP assignment for all founders/contractors", "owner": "Legal DD", "timeline": "Week 1-2", "system": "legal_contracts"},
            {"step": "Validate ARR/churn/NRR from raw contracts & invoices", "owner": "Commercial DD", "timeline": "Week 1-2", "system": "sales/finance"},
            {"step": "Verify DPIIT + each claimed govt benefit certificate", "owner": "Tax DD", "timeline": "Week 2", "system": "compliance"},
        ] if is_tech_dd else [
            {"step": "Verify licenses and renewal status", "owner": "Compliance DD", "timeline": "Week 1-2", "system": "compliance"},
        ]) + [
            {"step": "Compile red-flag report + go/no-go memo", "owner": "DD Lead", "timeline": "Week 2-3", "system": "dd_room/investor_workspace"},
        ],
        "erp_impact": [
            {"module": "finance", "change": "Extract trial balance, P&L, ledgers for diligence; tag related-party accounts."},
            {"module": "compliance", "change": "Pull filing history (GST/TDS/ROC) and licenses with evidence."},
            {"module": "receivables", "change": "Generate ageing + customer concentration for revenue-quality review."},
            {"module": "audit_logs", "change": "Export change history to detect backdated/edited records."},
        ],
        "notion_update": [
            {"database": "dd_room", "entry": "One row per DD checklist item: category, status, finding, risk, evidence link."},
            {"database": "risk_register", "entries": [r["flag"] for r in red_flags]},
            {"database": "investor_workspace", "entry": "Red-flag report + go/no-go memo + incentive-eligibility summary."},
            {"database": "decision_history", "entry": "Investment decision with options considered and rationale."},
        ],
        "compliance_impact": ("Confirms statutory standing (GST/TDS/PF/ESI/ROC) and, for startups, the validity of claimed tax benefits. "
                              "Mis-claimed 80-IAC/angel-tax exemptions can be reversed with interest/penalty — a real post-deal liability. "
                              "DPDP Act 2023 non-compliance is now a standard diligence and indemnity item for tech/AI companies."),
        "kpis_to_monitor": [
            {"kpi": "DD readiness score", "current": "TBD", "target": "> 90%", "source": "DD checklist"},
            {"kpi": "Open red flags", "current": len(red_flags), "target": "0 critical", "source": "Risk register"},
            {"kpi": "Data-room completeness %", "current": "TBD", "target": "100%", "source": "Data room"},
        ] + ([
            {"kpi": "Net revenue retention", "current": "TBD", "target": "> 100%", "source": "Cohort analysis"},
            {"kpi": "Verified govt benefits captured", "current": "TBD", "target": "All eligible", "source": "Certificates"},
        ] if is_tech_dd else []),
        "citations": _cite(*(["companies_act", "gst_portal", "income_tax", "epfo", "esic", "msmed_act"]
                           + compliance_for(cls)
                           + (["startup_india", "sec_80iac", "angel_tax", "sisfs", "state_startup", "meity_ai", "benchmark_saas"] if is_tech_dd else []))),
        "human_approval_points": [
            "Investment Committee / acquirer sign-off on the go/no-go memo.",
            "Legal counsel confirmation of IP ownership and material-contract assignability before closing.",
            "Tax advisor confirmation of every claimed government incentive before relying on it in valuation.",
        ],
        "government_incentives": incentives,
    }


# ============================================================
# 13b. FLAGSHIP GENERATOR — ERP CONSULTANT AGENT
# ============================================================
# Recommended ERP modules + suggested platform by business size/type.
_ERP_PLATFORMS = {
    "micro":  {"primary": "Tally Prime / Vyapar", "alt": ["Zoho Books", "myBillBook"], "why": "Low cost, GST-ready, minimal training; covers billing + basic accounts."},
    "small":  {"primary": "Zoho One / Odoo Community", "alt": ["Tally Prime", "Busy"], "why": "Modular, affordable, covers inventory + sales + purchase + GST with room to grow."},
    "medium": {"primary": "Odoo Enterprise / SAP Business One", "alt": ["Microsoft Dynamics 365 BC", "NetSuite"], "why": "Multi-branch, manufacturing/BOM, approvals and audit trails at scale."},
}

def gen_erp_consultant(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    current = data.get("current_system") or ("spreadsheets/manual" if "spreadsheet" in desc.lower() or "manual" in desc.lower() else "unknown")
    plat = _ERP_PLATFORMS.get(cls["size"], _ERP_PLATFORMS["small"])

    # Core modules everyone needs, plus industry-specific.
    core = ["master_data", "customers", "vendors", "products", "sales", "purchase", "billing", "finance", "compliance"]
    extra = []
    if cls["industry"] in ("retail", "wholesale", "pharma", "manufacturing", "food_bev"):
        extra += ["inventory"]
    if cls["industry"] == "manufacturing":
        extra += ["approvals"]
    if cls["is_import"] or cls["is_export"]:
        extra += ["compliance"]
    extra += ["receivables", "payables", "audit_logs"]
    modules = [m for m in (core + extra) if m in ERP_MODULES]
    modules = list(dict.fromkeys(modules))  # de-dupe, keep order

    pharma_note = " Batch + expiry tracking is mandatory at the SKU level for pharma." if cls["industry"] == "pharma" else ""
    mfg_note = " BOM, work-orders and WIP costing are the manufacturing-specific must-haves." if cls["industry"] == "manufacturing" else ""

    return {
        "business_context": f"{cls['size'].title()} {cls['industry'].replace('_',' ')} business currently on {current}. "
                            f"Goal: move to a fit-for-purpose ERP without over-buying.{pharma_note}{mfg_note}",
        "assumptions": [
            f"Recommendation tuned to a {cls['size']} business; revisit if headcount/turnover changes band.",
            "Build-vs-buy favours buy: a configured off-the-shelf ERP beats custom for an MSME.",
            "GST compliance must be native, not bolted on.",
        ],
        "required_data": [
            {"item": "Current systems & pain points", "have": current != "unknown", "why": "Scope and migration plan."},
            {"item": "Monthly transaction volume (invoices, SKUs, users)", "have": bool(data.get("volume")), "why": "Sizing and licence tier."},
            {"item": "Branch/warehouse count and locations", "have": False, "why": "Multi-entity vs single-entity setup."},
            {"item": "Must-have integrations (bank, marketplace, Tally, WhatsApp)", "have": False, "why": "Integration scoping."},
        ],
        "clarifying_questions": [
            "How many users, branches and SKUs, and roughly how many invoices a month?",
            "What absolutely must integrate (bank, e-commerce marketplaces, existing Tally data)?",
            "What is your monthly software budget per user?",
        ],
        "analysis": {
            "recommended_platform": plat["primary"],
            "alternatives": plat["alt"],
            "platform_rationale": plat["why"],
            "recommended_modules": [{"key": m, "name": ERP_MODULES[m]["name"]} for m in modules],
            "phasing": "Phase 1: master data + sales + billing + GST. Phase 2: purchase + inventory. Phase 3: finance/AR/AP + approvals + analytics.",
            "build_vs_buy": "Buy & configure — custom build is not justified at MSME scale.",
        },
        "risks": [
            {"risk": "Dirty master data migrated as-is (duplicate customers, wrong HSN/GSTIN)", "severity": "High", "likelihood": "High",
             "control": "Cleanse + de-dupe master data before migration; validate GSTIN/HSN.", "owner": "Project lead", "cite": "gst_portal"},
            {"risk": "Big-bang go-live without parallel run", "severity": "High", "likelihood": "Medium",
             "control": "Run new ERP in parallel with old system for one cycle; reconcile before cutover.", "owner": "Implementation partner", "cite": "companies_act"},
            {"risk": "Low user adoption — staff revert to spreadsheets", "severity": "Medium", "likelihood": "High",
             "control": "Role-based training + SOPs; make ERP the only source of invoices.", "owner": "Ops head", "cite": "msmed_act"},
        ],
        "recommendations": [
            f"Adopt {plat['primary']} as the core ERP ({plat['why']}).",
            "Phase the rollout (master data → sales/billing → inventory/purchase → finance/analytics); don't go big-bang.",
            "Cleanse master data (customers, vendors, SKUs with HSN/GSTIN) before any migration.",
            "Make GST e-invoice/e-way bill native in the ERP so compliance is automatic, not manual.",
            "Run the new ERP in parallel for one full month and reconcile before retiring the old system.",
        ],
        "action_plan": [
            {"step": "Document as-is processes + pain points; finalise module scope", "owner": "Project lead", "timeline": "Week 1-2", "system": "master_data"},
            {"step": "Shortlist + demo 2-3 platforms; pick partner", "owner": "Founder", "timeline": "Week 2-3", "system": "—"},
            {"step": "Cleanse & migrate master data", "owner": "Accountant", "timeline": "Week 3-5", "system": "master_data/products"},
            {"step": "Configure Phase-1 modules + GST; parallel run", "owner": "Partner", "timeline": "Week 5-9", "system": "billing/sales"},
            {"step": "Cutover + train users + publish SOPs", "owner": "Ops head", "timeline": "Week 9-12", "system": "approvals"},
        ],
        "erp_impact": [{"module": m, "change": f"Stand up {ERP_MODULES[m]['name']} ({', '.join(ERP_MODULES[m]['entities'][:3])}…)."} for m in modules[:6]],
        "notion_update": [
            {"database": "sop_repo", "entry": "ERP process SOPs per module (order-to-cash, procure-to-pay, record-to-report)."},
            {"database": "decision_history", "entry": "ERP platform selection with options considered + rationale."},
            {"database": "task_tracker", "entry": "Implementation milestones by phase with owners and dates."},
        ],
        "compliance_impact": "A GST-native ERP makes e-invoicing, e-way bills and return data automatic and auditable, reducing filing errors and ITC leakage. Audit logs support statutory and investor due diligence.",
        "kpis_to_monitor": [
            {"kpi": "Process automation %", "current": "TBD", "target": "> 70%", "source": "ERP usage"},
            {"kpi": "Manual data-entry hours/week", "current": "TBD", "target": "-60%", "source": "Time study"},
            {"kpi": "Invoice/GST error rate", "current": "TBD", "target": "< 1%", "source": "Compliance"},
        ],
        "citations": _cite(*(["gst_portal", "einvoice", "companies_act"] + compliance_for(cls))),
        "human_approval_points": [
            "Founder/owner sign-off on platform + budget before partner engagement.",
            "Finance head approval of migrated opening balances before go-live.",
        ],
    }


# ============================================================
# 13c. FLAGSHIP GENERATOR — INVESTOR READINESS AGENT
# ============================================================
def gen_investor_readiness(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    stage = data.get("stage") or ("seed" if "seed" in desc.lower() else ("series a" if "series a" in desc.lower() else "early"))
    incentives = _govt_incentives(cls, desc) if (cls["is_startup"] or cls["is_tech"]) else []

    data_room = ["Incorporation docs + cap table + ESOP", "3-yr financials + current MIS", "GST/ITR/ROC filings",
                 "Bank statements", "Key contracts (customers, vendors, leases)", "Statutory compliance proofs (PF/ESI/TDS)"]
    if cls["is_tech"]:
        data_room += ["ARR/MRR + cohort retention", "Product metrics + roadmap", "IP assignment agreements", "DPIIT + 80-IAC/angel-tax certificates"]

    return {
        "business_context": f"{'AI/SaaS/tech startup' if cls['is_tech'] else cls['industry'].replace('_',' ')} preparing for a {stage} raise. "
                            "Objective: a clean data room, a defensible metrics narrative, and verified eligibility for India startup benefits.",
        "assumptions": [
            "A priced equity round (not just grants/debt) is the target.",
            "Financials will be made audit-ready before sharing externally.",
            "Government-benefit eligibility is a claim to be evidenced with certificates.",
        ],
        "required_data": [
            {"item": "Cap table + ESOP pool + prior SAFEs/CCDs", "have": bool(data.get("cap_table")), "why": "Ownership/dilution clarity for investors."},
            {"item": "3-yr financials + 18-month projections", "have": bool(data.get("financials")), "why": "Historicals + the growth ask."},
            {"item": "Key metrics (revenue, growth, retention, burn, runway)", "have": bool(data.get("metrics")), "why": "The core diligence narrative."},
            {"item": "DPIIT recognition + benefit certificates", "have": bool(data.get("dpiit")), "why": "Tax shield + angel-tax safety materially affect economics."},
        ],
        "clarifying_questions": [
            f"What amount are you raising at {stage}, and against what 18-month milestones?",
            "What is current revenue/ARR, month-on-month growth, burn and runway?",
            "Is the cap table clean (all SAFEs/ESOPs documented), and is all IP assigned to the company?",
        ],
        "analysis": {
            "stage": stage,
            "data_room_checklist": data_room,
            "metrics_that_matter": (["ARR growth", "Net revenue retention", "Gross margin", "Burn multiple", "CAC payback"]
                                    if cls["is_tech"] else ["Revenue growth", "Gross/EBITDA margin", "Working-capital cycle", "Unit economics"]),
            "saas_benchmarks": {k: _bench(k) for k in ("saas_gross_margin", "net_revenue_ret", "burn_multiple")} if cls["is_tech"] else {},
            "incentive_upside": f"{len(incentives)} govt benefit(s) to evidence — these lift effective post-money economics." if incentives else "Limited startup-scheme eligibility.",
        },
        "risks": [
            {"risk": "Messy cap table / undocumented ESOP promises surface in diligence", "severity": "High", "likelihood": "Medium",
             "control": "Reconcile cap table, formalise ESOP pool, paper all SAFEs/CCDs before outreach.", "owner": "Founder/CS", "cite": "startup_india"},
            {"risk": "Revenue quality questioned (one-time vs recurring, churn hidden)", "severity": "High", "likelihood": "Medium",
             "control": "Build cohort retention from raw invoices; define ARR consistently.", "owner": "Finance", "cite": "benchmark_saas"},
            {"risk": "Angel-tax / 80-IAC claimed without valid certificates → post-raise tax exposure", "severity": "High", "likelihood": "Medium",
             "control": "Secure DPIIT + IMB certificates before relying on benefits in the deck.", "owner": "CA", "cite": "sec_80iac"},
            {"risk": "Statutory arrears (GST/TDS/PF/ESI) discovered in diligence", "severity": "High", "likelihood": "Medium",
             "control": "Clear all statutory dues and keep filing proofs in the data room.", "owner": "Finance", "cite": "epfo"},
        ],
        "recommendations": [
            "Build a structured data room mirroring the diligence checklist; mark each item Ready/Pending.",
            "Clean the cap table and formalise the ESOP pool before any investor conversation.",
            ("Define ARR consistently and prove retention with cohort analysis from raw invoices." if cls["is_tech"]
             else "Normalise EBITDA and show a clean working-capital story."),
            "Secure DPIIT recognition and the 80-IAC / angel-tax certificates so benefits are defensible, not assumed.",
            "Clear all statutory dues and keep filing evidence ready — arrears are a classic deal-killer.",
        ],
        "action_plan": [
            {"step": "Assemble data room (structured, access-controlled)", "owner": "Founder", "timeline": "Week 1-2", "system": "compliance/finance"},
            {"step": "Reconcile cap table + ESOP; paper instruments", "owner": "Company Secretary", "timeline": "Week 1-2", "system": "—"},
            {"step": "Build metrics pack + 18-month model", "owner": "Finance", "timeline": "Week 2-3", "system": "finance"},
            {"step": "Secure DPIIT + benefit certificates", "owner": "CA", "timeline": "Week 2-4", "system": "compliance"},
            {"step": "Polish narrative + investor pitch", "owner": "Founder", "timeline": "Week 3-4", "system": "—"},
        ],
        "erp_impact": [
            {"module": "finance", "change": "Lock MIS, generate clean P&L/BS and ratio pack for the data room."},
            {"module": "compliance", "change": "Export GST/TDS/PF/ESI/ROC filing proofs; flag any arrears."},
            {"module": "receivables", "change": "Provide ageing + concentration to evidence revenue quality."},
        ],
        "notion_update": [
            {"database": "investor_workspace", "entry": "Data-room index, metrics pack, pitch, and Q&A log by audience."},
            {"database": "kpi_db", "entries": ["ARR/Revenue growth", "Retention", "Burn multiple", "Runway"]},
            {"database": "dd_room", "entry": "Pre-empted diligence checklist with evidence links."},
            {"database": "decision_history", "entry": "Fundraise strategy: amount, stage, target investors, rationale."},
        ],
        "compliance_impact": "Verified DPIIT/80-IAC/angel-tax status protects valuation and avoids post-raise tax surprises. Clean statutory standing (GST/TDS/PF/ESI/ROC) removes the most common diligence red flags. For tech, DPDP Act readiness is increasingly a term-sheet condition.",
        "kpis_to_monitor": [
            {"kpi": "Investor readiness score", "current": "TBD", "target": "> 90%", "source": "Data-room checklist"},
            {"kpi": "Data-room completeness %", "current": "TBD", "target": "100%", "source": "Investor workspace"},
            {"kpi": "Runway (months)", "current": "TBD", "target": "> 12 post-raise", "source": "Cash model"},
        ],
        "citations": _cite(*(["startup_india", "sec_80iac", "angel_tax", "sisfs", "companies_act", "epfo", "income_tax"]
                           + (["benchmark_saas", "meity_ai"] if cls["is_tech"] else []) + compliance_for(cls))),
        "human_approval_points": [
            "Founder + board approval of the fundraise terms and dilution.",
            "CA/CS sign-off on cap table and all claimed government benefits before sharing externally.",
        ],
        "government_incentives": incentives,
    }


# ============================================================
# 13d. FLAGSHIP GENERATOR — INVENTORY AGENT
# ============================================================
def gen_inventory(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    dead_stock = data.get("dead_stock_value") or _num(desc, r"rs\.?\s*([0-9.]+)\s*lakh.*dead", r"dead stock[^0-9]*rs\.?\s*([0-9.]+)\s*lakh")
    stockouts = "stockout" in desc.lower() or "out of stock" in desc.lower() or bool(data.get("stockouts"))
    is_pharma = cls["industry"] == "pharma"

    risks = [
        {"risk": "Capital locked in dead/slow-moving stock", "severity": "High" if dead_stock else "Medium", "likelihood": "High",
         "control": "Monthly ageing + ABC analysis; liquidate/return slow movers; stop reordering D-class.", "owner": "Inventory in-charge", "cite": "benchmark_ar"},
        {"risk": "Stockouts on fast movers → lost sales", "severity": "High" if stockouts else "Medium", "likelihood": "High" if stockouts else "Medium",
         "control": "Set reorder point = (avg daily sales × lead time) + safety stock for A-class SKUs.", "owner": "Purchase", "cite": "benchmark_ar"},
        {"risk": "Inventory valuation drift vs physical (shrinkage/theft)", "severity": "Medium", "likelihood": "Medium",
         "control": "Cycle counting (A-class weekly); reconcile book vs physical; investigate variance.", "owner": "Store", "cite": "companies_act"},
    ]
    if is_pharma:
        risks.insert(0, {"risk": "Expired/near-expiry stock sold or written off — patient-safety + Schedule H records",
                         "severity": "Critical", "likelihood": "High",
                         "control": "FEFO (first-expiry-first-out) picking; near-expiry alerts; supplier return before expiry.",
                         "owner": "Pharmacist", "cite": "drugs_act"})

    return {
        "business_context": f"{cls['size'].title()} {cls['industry'].replace('_',' ')} business"
                            + (f" with ~Rs.{dead_stock} lakh dead stock" if dead_stock else "")
                            + (" and recurring stockouts" if stockouts else "")
                            + (". Expiry control is safety-critical for pharma." if is_pharma else ". Goal: free locked cash and stop lost sales."),
        "assumptions": [
            "SKU-level sales velocity and stock-on-hand are available or can be exported from billing.",
            f"Dead-stock figure ~Rs.{dead_stock} lakh from input." if dead_stock else "Dead-stock value unknown — flagged in required_data.",
            "Lead times per supplier are roughly known for reorder-point math.",
        ],
        "required_data": [
            {"item": "SKU master with cost + selling price", "have": False, "why": "ABC analysis and margin-weighted decisions."},
            {"item": "Stock-on-hand by SKU + location", "have": bool(data.get("stock")), "why": "Ageing and reorder calc."},
            {"item": "Sales velocity (units/day per SKU, 90 days)", "have": False, "why": "Reorder points and dead-stock flagging."},
            {"item": "Supplier lead times + MOQ", "have": False, "why": "Safety stock and order sizing."},
        ] + ([{"item": "Batch + expiry by SKU", "have": False, "why": "FEFO and near-expiry returns (mandatory for pharma)."}] if is_pharma else []),
        "clarifying_questions": [
            "Can you export 90 days of SKU-level sales and current stock-on-hand?",
            "What are typical supplier lead times and minimum order quantities?",
            ("What is your supplier return/expiry policy and window?" if is_pharma else "Which SKUs do you consider your top sellers today?"),
        ],
        "analysis": {
            "method": "ABC analysis (A=top 80% value, B=next 15%, C=last 5%) + ageing buckets (0-30/31-60/61-90/90+ days).",
            "reorder_formula": "Reorder point = (avg daily sales × lead-time days) + safety stock; safety stock ≈ Z × σ(demand) × √lead-time.",
            "dead_stock_lever": (f"Liquidating ~Rs.{round(dead_stock*0.6,2)} lakh of the dead stock (≈60%) releases immediate cash." if dead_stock else "Quantify after ageing report."),
            "turns_benchmark": _bench("inventory_turns"),
            "picking_policy": "FEFO" if is_pharma else "FIFO",
        },
        "risks": risks,
        "recommendations": [
            "Run ABC analysis and set differentiated policies: tight reorder control on A-class, minimal stock on C-class.",
            "Compute reorder points + safety stock per A/B SKU and automate purchase indents in the ERP.",
            ("Enforce FEFO picking and near-expiry alerts; return near-expiry pharma stock to suppliers within policy window." if is_pharma
             else "Liquidate dead/slow stock via discounts or supplier returns; stop reordering non-movers."),
            "Introduce cycle counting (A-class weekly) to keep book vs physical accurate.",
        ],
        "action_plan": [
            {"step": "Export SKU sales + stock; build ABC + ageing report", "owner": "Inventory in-charge", "timeline": "Week 1", "system": "inventory"},
            {"step": "Set reorder points + safety stock for A/B SKUs", "owner": "Purchase", "timeline": "Week 1-2", "system": "purchase/products"},
            {"step": ("Configure FEFO + near-expiry alerts" if is_pharma else "Launch dead-stock liquidation/return drive"), "owner": "Store/Pharmacist" if is_pharma else "Sales", "timeline": "Week 2-3", "system": "inventory"},
            {"step": "Start cycle counting + variance review", "owner": "Store", "timeline": "Ongoing", "system": "audit_logs"},
        ],
        "erp_impact": [
            {"module": "inventory", "change": "Enable ABC classification, ageing buckets, reorder points, batch/expiry + cycle counting."},
            {"module": "products", "change": "Maintain cost/price, HSN, lead time, MOQ per SKU."},
            {"module": "purchase", "change": "Auto-generate indents when stock hits reorder point."},
        ] + ([{"module": "audit_logs", "change": "Log expiry write-offs and stock adjustments."}] if is_pharma else []),
        "notion_update": [
            {"database": "task_tracker", "entries": ["Dead-stock liquidation drive", "Reorder-point setup", "Cycle-count schedule"]},
            {"database": "kpi_db", "entries": ["Inventory turns", "Dead stock %", "Stockout rate"]},
            {"database": "risk_register", "entries": [r["risk"] for r in risks]},
        ],
        "compliance_impact": ("For pharma, expiry handling and Schedule H/H1 batch records are statutory (Drugs & Cosmetics Act) — selling expired stock is an offence. "
                              if is_pharma else "Accurate inventory valuation affects GST stock records and the balance sheet; large unexplained write-offs draw audit scrutiny."),
        "kpis_to_monitor": [
            {"kpi": "Inventory turns", "current": "TBD", "target": BENCHMARKS["inventory_turns"]["healthy"], "source": "ERP inventory"},
            {"kpi": "Dead stock % of value", "current": "TBD", "target": "< 5%", "source": "Ageing report"},
            {"kpi": "Stockout rate (A-class)", "current": "TBD", "target": "< 2%", "source": "Sales/stock"},
        ] + ([{"kpi": "Near-expiry value", "current": "TBD", "target": "Returned before expiry", "source": "Batch ledger"}] if is_pharma else []),
        "citations": _cite(*(["benchmark_ar"] + (["drugs_act"] if is_pharma else []) + compliance_for(cls))),
        "human_approval_points": [
            "Owner approval before liquidating dead stock below cost.",
            ("Pharmacist sign-off on expiry write-offs and supplier returns." if is_pharma else "Purchase head approval of new reorder points."),
        ],
    }


# ============================================================
# 13e. FLAGSHIP GENERATOR — EXPORT COMPLIANCE AGENT
# ============================================================
def gen_export_compliance(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    dest = data.get("destination") or next((c for c in ("uae", "usa", "eu", "uk", "africa", "singapore") if c in desc.lower()), "the destination market")
    is_agro_food = cls["industry"] in ("agro_export", "food_bev") or any(k in desc.lower() for k in ("spice", "rice", "tea", "food", "makhana", "marine"))
    is_import = cls["is_import"]

    docs = ["IEC (Importer-Exporter Code)", "GST registration + LUT (for zero-rated export without IGST)",
            "Commercial invoice + packing list", "Shipping bill (ICEGATE)", "Bill of Lading / Airway bill",
            "Certificate of Origin", "RCMC from the relevant Export Promotion Council"]
    if is_agro_food:
        docs += ["APEDA registration (scheduled products)", "Phytosanitary / health certificate", "FSSAI compliance for food"]
    if is_import:
        docs = ["IEC", "Bill of Entry (ICEGATE)", "Customs duty payment (BCD + IGST + cess)", "BIS certification (notified goods)", "Commercial invoice + packing list"]

    return {
        "business_context": (f"{cls['industry'].replace('_',' ')} business importing into India" if is_import
                             else f"{cls['industry'].replace('_',' ')} exporter shipping to {dest}")
                            + ". Objective: complete, correct cross-border documentation, claim all eligible incentives, and de-risk the counterparty.",
        "assumptions": [
            "The business holds (or will obtain) a valid IEC from DGFT.",
            f"Trade role assessed as: {cls['trade_role']}.",
            "HSN classification drives duty/incentive rates and must be verified.",
        ],
        "required_data": [
            {"item": "IEC + GSTIN", "have": bool(data.get("iec")), "why": "Mandatory for any cross-border trade."},
            {"item": "Product HSN code(s)", "have": bool(data.get("hsn")), "why": "Determines duty, RoDTEP/drawback, and BIS/QCO applicability."},
            {"item": ("Supplier + country of origin" if is_import else "Buyer details + destination country"), "have": False, "why": "Counterparty due diligence + origin rules."},
            {"item": ("Customs duty structure (BCD/IGST/cess)" if is_import else "Incentive eligibility (RoDTEP/drawback/EPC)"), "have": False, "why": "Landed cost / incentive capture."},
        ],
        "clarifying_questions": [
            "What is the product and its HSN code, and what is the order value?",
            ("Which country are you importing from, and is the product under any BIS/QCO?" if is_import
             else f"Who is the buyer in {dest}, and what are the payment terms (advance/LC/open account)?"),
            "Do you hold a valid IEC and (for exports) an RCMC from the relevant council?",
        ],
        "analysis": {
            "trade_role": cls["trade_role"],
            "document_checklist": docs,
            "gst_treatment": ("IGST paid at customs on Bill of Entry is creditable as ITC; verify BoE reflects in GSTR-2B." if is_import
                              else "Export is zero-rated — ship under LUT (no IGST) or pay IGST and claim refund; reconcile with shipping bills."),
            "incentives": ([] if is_import else ["RoDTEP (Remission of Duties and Taxes on Exported Products)", "Duty Drawback", "Interest Equalisation / EPC benefits via RCMC"]),
            "buyer_due_diligence": ("N/A (import)" if is_import else f"Verify the {dest} buyer: credit check, prior trade history, and secure payment terms (LC/advance) for first orders."),
        },
        "risks": [
            {"risk": "Wrong HSN classification → duty/incentive errors + customs penalty", "severity": "High", "likelihood": "Medium",
             "control": "Confirm HSN with a customs broker; document the basis.", "owner": "Export/Import desk", "cite": "customs" if is_import else "dgft_iec"},
            {"risk": ("Missing BIS/QCO certification on notified imported goods → seizure" if is_import
                      else "Incomplete export docs → shipment held / payment delayed"), "severity": "High", "likelihood": "Medium",
             "control": ("Check BIS/QCO list before ordering; obtain certification." if is_import else "Use a document checklist gate before dispatch."),
             "owner": "Compliance", "cite": "bis" if is_import else "fieo"},
            {"risk": ("FX exposure on import payables" if is_import else "Buyer default / non-payment on open-account terms"),
             "severity": "Medium", "likelihood": "Medium",
             "control": ("Hedge large FX payables." if is_import else "Use LC or advance for new buyers; consider ECGC cover."), "owner": "Finance", "cite": "rbi_msme"},
        ] + ([] if is_import else [
            {"risk": "Export proceeds not realised within FEMA timeline (eBRC not closed)", "severity": "High", "likelihood": "Medium",
             "control": "Track eBRC realisation; follow up before the RBI-prescribed window.", "owner": "Finance", "cite": "rbi_msme"},
        ]),
        "recommendations": ([
            "Verify HSN and check the BIS/QCO list before placing the import order.",
            "File Bill of Entry on ICEGATE; pay BCD+IGST+cess; claim the IGST as ITC and reconcile with GSTR-2B.",
            "Hedge material FX payables to protect landed cost.",
        ] if is_import else [
            "Obtain/confirm IEC + RCMC from the relevant Export Promotion Council to unlock FTP benefits.",
            "Export under LUT to avoid blocking working capital in IGST; reconcile shipping bills for any refund.",
            "Verify HSN to claim the correct RoDTEP/Duty-Drawback rate — leaving incentives unclaimed is lost cash.",
            f"Run buyer due diligence on the {dest} counterparty and secure first orders with LC or advance payment.",
            "Track eBRC realisation to stay FEMA-compliant on export proceeds.",
        ]) + (["Ensure APEDA registration + phytosanitary/health certificates for agro/food consignments."] if is_agro_food and not is_import else []),
        "action_plan": [
            {"step": "Confirm IEC + verify HSN with customs broker", "owner": "Trade desk", "timeline": "Day 1-3", "system": "compliance"},
            {"step": ("File Bill of Entry + pay customs duty" if is_import else "Obtain RCMC + file LUT"), "owner": "Compliance", "timeline": "Week 1", "system": "compliance/billing"},
            {"step": ("Reconcile BoE IGST in GSTR-2B" if is_import else "Run buyer due diligence + set payment terms"), "owner": "Finance", "timeline": "Week 1-2", "system": "billing/customers"},
            {"step": ("Set up FX hedging" if is_import else "Claim RoDTEP/drawback + track eBRC"), "owner": "Finance", "timeline": "Per shipment", "system": "finance"},
        ],
        "erp_impact": [
            {"module": "compliance", "change": ("Store Bill of Entry, customs challans, BIS certs with due dates." if is_import
                                                else "Store IEC, RCMC, LUT, shipping bills, eBRC, and incentive claims.")},
            {"module": "billing", "change": ("Capture customs IGST for ITC." if is_import else "Generate export invoices under LUT (zero-rated) with currency + buyer details.")},
            {"module": "sales" if not is_import else "purchase", "change": ("Link import POs to Bill of Entry and landed cost." if is_import else "Link export orders to shipping bills and incentive claims.")},
        ],
        "notion_update": [
            {"database": "compliance_tracker", "entry": ("Import obligations: BoE, duty, BIS, with due dates." if is_import else "Export obligations: RCMC, LUT, eBRC realisation, incentive claims.")},
            {"database": "dd_room", "entry": ("Supplier verification record." if is_import else "Buyer due-diligence record + payment-term decision.")},
            {"database": "risk_register", "entries": ["HSN classification", "Certification/docs gap", ("FX exposure" if is_import else "Buyer default / eBRC realisation")]},
        ],
        "compliance_impact": ("Imports require correct Customs Act filings (Bill of Entry), duty payment, and BIS/QCO certification for notified goods — non-compliance risks seizure and penalty; IGST paid is recoverable as ITC. "
                              if is_import else
                              "Exports are zero-rated under GST (LUT/refund route); FTP benefits (RoDTEP/drawback) require correct HSN and RCMC; export proceeds must be realised within FEMA timelines (eBRC)."),
        "kpis_to_monitor": ([
            {"kpi": "Customs clearance time", "current": "TBD", "target": "Minimise demurrage", "source": "ICEGATE"},
            {"kpi": "Import IGST claimed as ITC %", "current": "TBD", "target": "100%", "source": "GSTR-2B"},
        ] if is_import else [
            {"kpi": "Document compliance %", "current": "TBD", "target": "100%", "source": "Doc checklist"},
            {"kpi": "Incentive captured (RoDTEP/drawback)", "current": "TBD", "target": "All eligible", "source": "DGFT/ICEGATE"},
            {"kpi": "eBRC realisation on time %", "current": "TBD", "target": "100%", "source": "Bank/DGFT"},
        ]),
        "citations": _cite(*(["dgft_iec", "customs", "gst_portal"] + (["bis"] if is_import else ["fieo", "rbi_msme"]) + (["apeda", "fssai"] if is_agro_food else []) + compliance_for(cls))),
        "human_approval_points": [
            "Finance head approval of payment terms / LC for a new counterparty.",
            ("Compliance sign-off that BIS/QCO + customs docs are complete before clearance." if is_import
             else "Compliance sign-off that the export document set is complete before dispatch."),
        ],
    }


# ============================================================
# 13f. FLAGSHIP GENERATOR — CEO COPILOT AGENT
# ============================================================
def gen_ceo_copilot(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    cash_tight = "cash" in desc.lower() or "tight" in desc.lower() or "runway" in desc.lower()
    horizon = data.get("horizon") or "this quarter"

    priorities = (
        ["Stabilise cash: 13-week forecast + collections drive (delegate to CFO Finance Agent).",
         "Protect the top revenue line: defend the largest accounts and the highest-margin SKUs.",
         "Cut or defer non-essential spend; tie every rupee to a near-term outcome."]
        if cash_tight else
        ["Pick one growth bet and resource it properly; say no to the rest this quarter.",
         "Fix the biggest operational bottleneck (delegate to COO Operations Agent).",
         "Put a weekly metric review cadence in place so decisions are data-led."]
    )

    return {
        "business_context": f"{cls['size'].title()} {cls['industry'].replace('_',' ')} business. Founder needs clear top priorities for {horizon}"
                            + (" under a cash constraint." if cash_tight else " to drive focused growth."),
        "assumptions": [
            "Founder wants 3 priorities, not 15 — focus beats coverage.",
            "Other agents (CFO, COO, Sales) execute the detail; this agent sets direction + cadence.",
            f"Planning horizon: {horizon}.",
        ],
        "required_data": [
            {"item": "Current P&L + cash position", "have": bool(data.get("pnl")), "why": "Anchors priorities in reality."},
            {"item": "Top 3 goals / constraints", "have": bool(data.get("goals")), "why": "Aligns priorities to intent."},
            {"item": "Current initiatives in flight", "have": False, "why": "Decide what to stop, not just start."},
        ],
        "clarifying_questions": [
            "What is the single most important outcome you want by end of " + horizon + "?",
            "What is your current monthly burn and cash runway?",
            "What are you currently spending time on that you suspect doesn't matter?",
        ],
        "analysis": {
            "operating_mode": "Defend / conserve" if cash_tight else "Focused growth",
            "top_priorities": priorities,
            "okrs": [
                {"objective": priorities[0].split(":")[0], "key_results": ["Measurable KR 1", "Measurable KR 2"]},
            ],
            "operating_cadence": "Weekly: 30-min metric review. Monthly: priorities + cash review. Quarterly: strategy reset.",
            "delegation": {"cash/finance": "cfo_finance", "operations/SOPs": "coo_operations", "compliance": "gst_compliance", "fundraise": "investor_readiness"},
        },
        "risks": [
            {"risk": "Founder spread across too many initiatives → none move", "severity": "High", "likelihood": "High",
             "control": "Hard-cap to 3 priorities; park the rest in a 'not now' list.", "owner": "Founder", "cite": "benchmark_ar"},
            {"risk": "Decisions made on gut, not numbers", "severity": "Medium", "likelihood": "Medium",
             "control": "Weekly metric review on a single founder dashboard.", "owner": "Founder", "cite": "benchmark_ar"},
        ],
        "recommendations": priorities + ["Stand up a one-page founder dashboard and run a 30-minute weekly review against it."],
        "action_plan": [
            {"step": "Confirm the 3 priorities + the 'not now' list", "owner": "Founder", "timeline": "Day 1", "system": "strategy_room"},
            {"step": "Set OKRs + owners for each priority", "owner": "Founder", "timeline": "Week 1", "system": "strategy_room"},
            {"step": "Stand up founder dashboard + weekly review", "owner": "Founder", "timeline": "Week 1", "system": "finance"},
        ],
        "erp_impact": [
            {"module": "finance", "change": "Surface revenue, margin, cash and runway to the founder dashboard."},
            {"module": "audit_logs", "change": "Track decisions and their owners for accountability."},
        ],
        "notion_update": [
            {"database": "founder_dashboard", "entry": "Top 3 priorities, owners, status, and the headline metrics."},
            {"database": "strategy_room", "entries": [p.split(":")[0] for p in priorities]},
            {"database": "decision_history", "entry": "Quarterly priorities with rationale + the explicit 'not now' list."},
        ],
        "compliance_impact": "Indirect — ensures compliance (GST/payroll/statutory) stays a standing priority and is delegated to the right agent rather than dropped under growth pressure.",
        "kpis_to_monitor": [
            {"kpi": "Revenue growth", "current": "TBD", "target": "Per plan", "source": "P&L"},
            {"kpi": "Operating margin", "current": "TBD", "target": "Improving", "source": "P&L"},
            {"kpi": "Priority completion", "current": "TBD", "target": "3/3", "source": "Strategy room"},
        ],
        "citations": _cite(*(["benchmark_ar"] + compliance_for(cls))),
        "human_approval_points": ["Founder owns and signs off the priority list and the OKRs."],
    }


# ============================================================
# 13g. FLAGSHIP GENERATOR — COO OPERATIONS AGENT
# ============================================================
def gen_coo_operations(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    cycle_now = data.get("cycle_days") or _num(desc, r"([0-9.]+)\s*days?")
    target = data.get("target_days")
    if target is None and cycle_now:
        target = max(1, round(cycle_now / 2))

    core_process = ("order-to-delivery" if cls["industry"] in ("wholesale", "retail", "d2c") else
                    "procure-to-produce-to-dispatch" if cls["industry"] == "manufacturing" else
                    "lead-to-cash")

    return {
        "business_context": f"{cls['size'].title()} {cls['industry'].replace('_',' ')} business. Focus: the {core_process} process"
                            + (f", currently ~{int(cycle_now)} days, target ~{int(target)} days." if cycle_now else ", reducing cycle time and standardising it."),
        "assumptions": [
            f"The bottleneck sits inside the {core_process} flow.",
            "Cycle time can be roughly halved by removing handoffs + manual steps." if cycle_now else "Process timings will be measured before optimising.",
            "SOPs + ERP workflow states will make the gains stick.",
        ],
        "required_data": [
            {"item": "Process map with step-level timings", "have": bool(data.get("process_map")), "why": "Locate the actual bottleneck."},
            {"item": "Volume + handoff points", "have": cycle_now is not None, "why": "Quantify queue/wait time."},
            {"item": "Headcount per step", "have": False, "why": "Capacity vs demand balance."},
        ],
        "clarifying_questions": [
            f"Walk me through the {core_process} steps — where do orders sit waiting the longest?",
            "Which steps are manual or need a person to chase someone else?",
            "What is your current vs desired cycle time, and what breaks at higher volume?",
        ],
        "analysis": {
            "target_process": core_process,
            "current_cycle_days": int(cycle_now) if cycle_now else "to be measured",
            "target_cycle_days": int(target) if target else "halve current",
            "method": "Map value stream → find the bottleneck (longest wait) → remove handoffs, parallelise, and automate the manual step → lock in with an SOP + ERP workflow state.",
            "quick_wins": ["Eliminate re-keying between systems", "Approve-by-exception instead of every order", "Standard pick/pack/dispatch checklist"],
        },
        "risks": [
            {"risk": "Bottleneck masked by firefighting — optimising the wrong step", "severity": "High", "likelihood": "Medium",
             "control": "Measure step-level timings before changing anything.", "owner": "COO/Ops lead", "cite": "benchmark_ar"},
            {"risk": "Improvement not sustained — team reverts to old habits", "severity": "Medium", "likelihood": "High",
             "control": "SOP + ERP workflow gates + a weekly cycle-time KPI.", "owner": "Ops lead", "cite": "msmed_act"},
        ],
        "recommendations": [
            f"Map the {core_process} value stream and measure wait time at each step before changing anything.",
            "Attack the single biggest bottleneck first; remove handoffs and parallelise where possible.",
            "Automate the most manual step (re-keying, chasing approvals) via ERP workflow + approve-by-exception.",
            "Lock the new flow with an SOP (delegate to SOP Agent) and a weekly cycle-time KPI.",
        ],
        "action_plan": [
            {"step": "Value-stream map with step timings", "owner": "Ops lead", "timeline": "Week 1", "system": "approvals"},
            {"step": "Redesign flow: remove handoffs, set approval matrix", "owner": "COO", "timeline": "Week 2", "system": "approvals"},
            {"step": "Configure ERP workflow states + automate manual step", "owner": "ERP admin", "timeline": "Week 2-4", "system": "sales/purchase"},
            {"step": "Publish SOP + start weekly cycle-time review", "owner": "Ops lead", "timeline": "Week 4", "system": "—"},
        ],
        "erp_impact": [
            {"module": "approvals", "change": "Define workflow states + approval matrix (maker-checker, approve-by-exception)."},
            {"module": "sales", "change": "Track order status transitions with timestamps for cycle-time measurement."},
            {"module": "purchase", "change": "Streamline indent→PO→GRN with auto-routing."},
        ],
        "notion_update": [
            {"database": "sop_repo", "entry": f"{core_process} SOP with roles, steps and SLAs."},
            {"database": "task_tracker", "entries": ["Value-stream map", "Bottleneck fix", "ERP workflow config"]},
            {"database": "kpi_db", "entries": ["Cycle time", "On-time delivery %", "Rework %"]},
        ],
        "compliance_impact": "Standardised workflows with maker-checker approvals and timestamps create the audit trail needed for statutory and due-diligence scrutiny.",
        "kpis_to_monitor": [
            {"kpi": "Cycle time (days)", "current": int(cycle_now) if cycle_now else "TBD", "target": int(target) if target else "halve", "source": "ERP timestamps"},
            {"kpi": "On-time delivery %", "current": "TBD", "target": "> 95%", "source": "Sales"},
            {"kpi": "Rework %", "current": "TBD", "target": "< 3%", "source": "QC"},
        ],
        "citations": _cite(*(["benchmark_ar", "msmed_act"] + compliance_for(cls))),
        "human_approval_points": ["COO/owner sign-off on the redesigned approval matrix before go-live."],
    }


# ============================================================
# 13h. FLAGSHIP GENERATOR — RISK & AUDIT AGENT
# ============================================================
def gen_risk_audit(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    fraud_focus = "fraud" in desc.lower() or "theft" in desc.lower() or "leakage" in desc.lower()

    risks = [
        {"risk": "Cash handling without segregation of duties (same person bills + collects + reconciles)", "severity": "High", "likelihood": "High",
         "control": "Segregate duties; daily cash reconciliation; maker-checker on receipts.", "owner": "Finance", "cite": "companies_act"},
        {"risk": "Inventory shrinkage / pilferage not detected", "severity": "High", "likelihood": "Medium",
         "control": "Cycle counts + CCTV on stores + variance investigation.", "owner": "Store", "cite": "benchmark_ar"},
        {"risk": "Vendor/purchase fraud (inflated rates, ghost vendors, kickbacks)", "severity": "High", "likelihood": "Medium",
         "control": "Vendor master controls, 3-way match (PO-GRN-invoice), periodic rate benchmarking.", "owner": "Procurement", "cite": "companies_act"},
        {"risk": "Statutory dues missed (GST/TDS/PF/ESI) → interest, penalty, notices", "severity": "High", "likelihood": "Medium",
         "control": "Compliance calendar with maker-checker + evidence archive.", "owner": "Compliance", "cite": "gst_portal"},
        {"risk": "No audit trail — changes to invoices/master data untracked", "severity": "Medium", "likelihood": "High",
         "control": "Enable field-level audit logs; restrict edit rights; periodic log review.", "owner": "ERP admin", "cite": "companies_act"},
    ]

    return {
        "business_context": f"{cls['size'].title()} {cls['industry'].replace('_',' ')} business"
                            + (" — owner concerned about where cash/inventory fraud could happen." if fraud_focus else " — establishing a live risk register and control framework."),
        "assumptions": [
            "Controls are assessed by process area (cash, inventory, purchase, payroll, compliance).",
            "RAID approach: Risks, Assumptions, Issues, Dependencies, scored Probability × Impact.",
            "Maker-checker and segregation of duties are the cheapest high-leverage controls.",
        ],
        "required_data": [
            {"item": "Process map + who-does-what (roles)", "have": False, "why": "Spot segregation-of-duties gaps."},
            {"item": "Current controls + approval matrix", "have": False, "why": "Control coverage assessment."},
            {"item": "Incident/loss history", "have": False, "why": "Prioritise by realised risk."},
        ],
        "clarifying_questions": [
            "Who bills, who collects cash, and who reconciles the bank — same person or different?",
            "Have you had any losses (cash, stock, vendor) in the last year?",
            "Who can edit invoices and master data in your system, and is it logged?",
        ],
        "analysis": {
            "framework": "RAID register + Probability×Impact (1-5 each) scoring; control mapping per process.",
            "highest_exposure": [r["risk"] for r in risks if r["severity"] == "High"][:3],
            "key_controls": ["Segregation of duties", "Maker-checker approvals", "3-way match", "Cycle counts", "Audit logs", "Compliance calendar"],
            "fraud_hotspots": ["Cash receipts", "Inventory stores", "Vendor onboarding + purchase rates", "Payroll (ghost employees)"],
        },
        "risks": risks,
        "recommendations": [
            "Stand up a live risk register (RAID) scored Probability×Impact; review monthly.",
            "Enforce segregation of duties on cash: different people bill, collect and reconcile.",
            "Implement 3-way match (PO-GRN-invoice) and vendor-master controls to block purchase fraud.",
            "Turn on field-level audit logs and restrict edit rights on invoices + master data.",
            "Run a compliance calendar with maker-checker so no statutory due date is missed.",
        ],
        "action_plan": [
            {"step": "Build RAID register; score top 10 risks", "owner": "Risk owner", "timeline": "Week 1", "system": "audit_logs"},
            {"step": "Map controls per process; fix segregation-of-duties gaps", "owner": "Finance/Ops", "timeline": "Week 1-2", "system": "approvals"},
            {"step": "Enable audit logs + restrict edit rights", "owner": "ERP admin", "timeline": "Week 2", "system": "audit_logs"},
            {"step": "Quarterly internal control review", "owner": "Risk owner", "timeline": "Quarterly", "system": "—"},
        ],
        "erp_impact": [
            {"module": "approvals", "change": "Define approval matrix + maker-checker on cash, purchase, master-data changes."},
            {"module": "audit_logs", "change": "Enable field-level change history; restrict and review edit rights."},
            {"module": "finance", "change": "Daily cash reconciliation + variance flags."},
        ],
        "notion_update": [
            {"database": "risk_register", "entries": [r["risk"] for r in risks]},
            {"database": "compliance_tracker", "entry": "Statutory obligations with owners + evidence."},
            {"database": "sop_repo", "entry": "Control SOPs: cash handling, 3-way match, cycle counting."},
        ],
        "compliance_impact": "Strong internal controls + audit logs are prerequisites for clean statutory audits, lender/investor due diligence, and reduce promoter exposure under the Companies Act.",
        "kpis_to_monitor": [
            {"kpi": "Open high risks", "current": len([r for r in risks if r["severity"] == "High"]), "target": "0", "source": "Risk register"},
            {"kpi": "Control coverage %", "current": "TBD", "target": "> 90%", "source": "Control map"},
            {"kpi": "Cash/stock variance", "current": "TBD", "target": "~0", "source": "Reconciliation"},
        ],
        "citations": _cite(*(["companies_act", "gst_portal", "benchmark_ar"] + compliance_for(cls))),
        "human_approval_points": ["Owner/board approval of the approval matrix and edit-rights restrictions."],
    }


# ============================================================
# 13i. FLAGSHIP GENERATOR — SOP AGENT
# ============================================================
def gen_sop(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    process = data.get("process") or (desc.strip() or "core operating process")
    is_pharma = cls["industry"] == "pharma"

    return {
        "business_context": f"{cls['size'].title()} {cls['industry'].replace('_',' ')} business needs a clear, audit-ready SOP for: {process}.",
        "assumptions": [
            "The SOP must be role-specific and usable by frontline staff, not a policy essay.",
            "It will live in the SOP repository, be versioned, and be reviewed periodically.",
            "Steps map to ERP actions where the process touches the system.",
        ],
        "required_data": [
            {"item": "Process name + trigger + desired outcome", "have": process != "core operating process", "why": "Defines SOP scope."},
            {"item": "Roles involved + who approves", "have": False, "why": "Assign each step an owner."},
            {"item": "Systems/forms touched", "have": False, "why": "Link steps to ERP/records."},
        ],
        "clarifying_questions": [
            f"What triggers the '{process}' process and what is the successful end state?",
            "Which roles are involved and where is an approval needed?",
            "What records or ERP entries must exist at each step?",
        ],
        "analysis": {
            "sop_structure": ["Purpose & scope", "Roles & responsibilities", "Trigger", "Step-by-step procedure (with owner + system per step)",
                              "Approvals / maker-checker", "Records to maintain", "Exceptions & escalation", "KPIs", "Version & review date"],
            "example_steps": [
                {"step": "Receive trigger + validate inputs", "owner": "Frontline", "system": "ERP"},
                {"step": "Process + record entry", "owner": "Frontline", "system": "ERP"},
                {"step": "Review/approve (maker-checker)", "owner": "Supervisor", "system": "approvals"},
                {"step": "Complete + archive evidence", "owner": "Frontline", "system": "audit_logs"},
            ],
            "review_cadence": "Quarterly, or whenever the process or a regulation changes.",
        },
        "risks": [
            {"risk": "SOP written but not followed", "severity": "Medium", "likelihood": "High",
             "control": "Embed steps as ERP workflow gates; spot-audit adherence.", "owner": "Process owner", "cite": "msmed_act"},
            {"risk": "SOP goes stale after a process/regulation change", "severity": "Medium", "likelihood": "Medium",
             "control": "Version control + quarterly review date + owner.", "owner": "Process owner", "cite": "companies_act"},
        ] + ([{"risk": "SOP omits Schedule H/expiry handling (pharma statutory)", "severity": "High", "likelihood": "Medium",
              "control": "Include FEFO + Schedule H record-keeping steps explicitly.", "owner": "Pharmacist", "cite": "drugs_act"}] if is_pharma else []),
        "recommendations": [
            f"Document '{process}' in the standard 9-part SOP structure with an owner + system noted on every step.",
            "Embed the critical steps as ERP workflow gates so the SOP is enforced, not just filed.",
            "Version the SOP, set a review date, and store it in the SOP repository.",
            "Spot-audit adherence monthly for the first quarter.",
        ],
        "action_plan": [
            {"step": "Draft SOP in the 9-part structure", "owner": "Process owner", "timeline": "Week 1", "system": "sop_repo"},
            {"step": "Review with frontline + supervisor; refine", "owner": "Ops lead", "timeline": "Week 1-2", "system": "—"},
            {"step": "Embed steps as ERP workflow gates", "owner": "ERP admin", "timeline": "Week 2", "system": "approvals"},
            {"step": "Publish + train + set review date", "owner": "Process owner", "timeline": "Week 2-3", "system": "sop_repo"},
        ],
        "erp_impact": [
            {"module": "approvals", "change": "Encode SOP approval steps as workflow gates."},
            {"module": "audit_logs", "change": "Capture evidence + completion for each SOP run."},
        ],
        "notion_update": [
            {"database": "sop_repo", "entry": f"'{process}' SOP — versioned, with owner and review date."},
            {"database": "task_tracker", "entry": "SOP rollout + training tasks."},
        ],
        "compliance_impact": ("For pharma, SOPs covering FEFO and Schedule H/H1 records are part of statutory good practice under the Drugs & Cosmetics Act. "
                              if is_pharma else "Documented, followed SOPs are evidence of process control for statutory audits and due diligence."),
        "kpis_to_monitor": [
            {"kpi": "SOP adherence %", "current": "TBD", "target": "> 95%", "source": "Spot audit"},
            {"kpi": "Process consistency / error rate", "current": "TBD", "target": "Falling", "source": "QC"},
            {"kpi": "New-hire onboarding time", "current": "TBD", "target": "-30%", "source": "HR"},
        ],
        "citations": _cite(*(["msmed_act", "companies_act"] + (["drugs_act"] if is_pharma else []) + compliance_for(cls))),
        "human_approval_points": ["Process owner + supervisor sign-off before the SOP is published as the standard."],
    }


# ============================================================
# 13j. FLAGSHIP GENERATOR — HR & PAYROLL AGENT
# ============================================================
def gen_hr_payroll(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    headcount = data.get("headcount") or _num(desc, r"([0-9]+)\s*employee", r"([0-9]+)\s*staff", r"crossing\s*([0-9]+)")
    epf_applies = (headcount is not None and headcount >= 20) or "epf" in desc.lower() or "pf" in desc.lower()

    risks = [
        {"risk": "EPF not registered/contributed despite crossing 20 employees", "severity": "Critical" if epf_applies else "Medium", "likelihood": "High" if epf_applies else "Low",
         "control": "Register with EPFO; deduct 12% + employer match; file ECR by 15th.", "owner": "HR/Payroll", "cite": "epfo"},
        {"risk": "ESI not deducted for wages <= Rs.21,000", "severity": "High", "likelihood": "Medium",
         "control": "Register with ESIC; employer 3.25% + employee 0.75%; monthly contribution.", "owner": "HR/Payroll", "cite": "esic"},
        {"risk": "TDS on salary not deducted/deposited (Sec 192)", "severity": "High", "likelihood": "Medium",
         "control": "Compute TDS on projected annual salary; deposit by 7th; file 24Q; issue Form 16.", "owner": "Payroll", "cite": "tds_salary"},
        {"risk": "Professional Tax / state labour registrations missed", "severity": "Medium", "likelihood": "Medium",
         "control": "Register for PT; deduct per state slab; track Shops & Establishment registration.", "owner": "HR", "cite": "prof_tax"},
        {"risk": "Gratuity liability not provided for (5+ yr employees)", "severity": "Medium", "likelihood": "Medium",
         "control": "Provision gratuity (15 days' wages/year) in the books.", "owner": "Finance", "cite": "gratuity"},
    ]

    return {
        "business_context": f"{cls['size'].title()} {cls['industry'].replace('_',' ')} business"
                            + (f" with ~{int(headcount)} employees" if headcount else "")
                            + (". Crossing the 20-employee EPF threshold makes PF registration mandatory." if epf_applies else ". Setting up compliant payroll + HR."),
        "assumptions": [
            f"Headcount ~{int(headcount)} from input." if headcount else "Headcount unknown — flagged in required_data.",
            "Salaries are structured (Basic + HRA + allowances) for statutory computation.",
            "State-specific PT and Shops & Establishment rules apply by location.",
        ],
        "required_data": [
            {"item": "Headcount + salary structure", "have": headcount is not None, "why": "Statutory applicability + computation."},
            {"item": "State(s) of operation", "have": False, "why": "PT slabs + Shops & Establishment + labour rules."},
            {"item": "Existing EPF/ESI/PT registrations", "have": bool(data.get("registrations")), "why": "Gap assessment."},
            {"item": "Attendance / leave data", "have": False, "why": "Payroll accuracy."},
        ],
        "clarifying_questions": [
            "How many employees, and what is the typical monthly gross + salary structure?",
            "Which states do you operate in (drives PT and labour registrations)?",
            "Are you already registered for EPF, ESI and Professional Tax?",
        ],
        "analysis": {
            "headcount": int(headcount) if headcount else "unknown",
            "epf_applicable": epf_applies,
            "statutory_stack": [
                {"item": "EPF", "rate": "12% employee + 12% employer", "trigger": ">= 20 employees", "filing": "ECR by 15th", "cite": "epfo"},
                {"item": "ESI", "rate": "0.75% employee + 3.25% employer", "trigger": "wages <= Rs.21,000", "filing": "Monthly", "cite": "esic"},
                {"item": "TDS (Sec 192)", "rate": "Per slab on salary", "trigger": "Above exemption", "filing": "Deposit 7th, 24Q quarterly, Form 16", "cite": "tds_salary"},
                {"item": "Professional Tax", "rate": "State slab", "trigger": "State-specific", "filing": "Monthly/annual per state", "cite": "prof_tax"},
                {"item": "Gratuity", "rate": "15 days' wages/yr", "trigger": "5+ yrs service", "filing": "Provision in books", "cite": "gratuity"},
            ],
            "labour_codes_note": "The four Labour Codes (Wages, IR, Social Security, OSH) consolidate 29 laws — track state notification of rules.",
        },
        "risks": risks,
        "recommendations": [
            ("Register with EPFO immediately — you've crossed the 20-employee threshold; backdated non-compliance attracts damages + interest." if epf_applies
             else "Monitor headcount; register for EPF the month you reach 20 employees."),
            "Register for ESI and deduct for all employees earning <= Rs.21,000; remit monthly.",
            "Run TDS on salary correctly (Sec 192): deposit by the 7th, file Form 24Q quarterly, issue Form 16.",
            "Register for Professional Tax + Shops & Establishment in each state of operation.",
            "Provision for gratuity for employees crossing 5 years; reflect the liability in the books.",
        ],
        "action_plan": [
            {"step": "Assess statutory applicability vs current registrations", "owner": "HR", "timeline": "Week 1", "system": "payroll"},
            {"step": "Register for any missing EPF/ESI/PT", "owner": "HR/CA", "timeline": "Week 1-2", "system": "compliance"},
            {"step": "Configure payroll: salary structure + statutory deductions", "owner": "Payroll", "timeline": "Week 2-3", "system": "payroll"},
            {"step": "Set filing calendar (ECR 15th, TDS 7th, ESI monthly)", "owner": "Payroll", "timeline": "Ongoing", "system": "compliance"},
        ],
        "erp_impact": [
            {"module": "payroll", "change": "Configure salary structure, EPF/ESI/PT/TDS deductions, payslips."},
            {"module": "compliance", "change": "Statutory filing calendar (ECR, 24Q, ESI, PT) with evidence."},
            {"module": "finance", "change": "Book employer contributions + gratuity provision."},
        ],
        "notion_update": [
            {"database": "compliance_tracker", "entries": ["EPF ECR", "ESI", "TDS 24Q", "Professional Tax"]},
            {"database": "task_tracker", "entry": "Payroll setup + statutory registration tasks."},
            {"database": "risk_register", "entries": [r["risk"] for r in risks]},
        ],
        "compliance_impact": "Payroll statutory non-compliance (EPF/ESI/TDS/PT) attracts interest, damages and prosecution, and is a standard red flag in due diligence. Correct setup protects employees and the promoters.",
        "kpis_to_monitor": [
            {"kpi": "Statutory filing on-time %", "current": "TBD", "target": "100%", "source": "Compliance"},
            {"kpi": "Payroll accuracy %", "current": "TBD", "target": "> 99%", "source": "Payroll"},
            {"kpi": "EPF/ESI coverage gap", "current": "TBD", "target": "0", "source": "EPFO/ESIC"},
        ],
        "citations": _cite(*(["epfo", "esic", "tds_salary", "prof_tax", "gratuity", "labour_codes"] + compliance_for(cls))),
        "human_approval_points": [
            "Finance head approval of salary-structure changes and statutory rates.",
            "CA sign-off on registrations and the first compliant payroll run.",
        ],
    }


# ============================================================
# 13k. FLAGSHIP GENERATOR — MARKET RESEARCH AGENT
# ============================================================
def gen_market_research(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    category = data.get("category") or desc.strip() or "the target category"
    geo = data.get("geography") or ("Tier-2/3 India" if "tier" in desc.lower() else "India")

    return {
        "business_context": f"Sizing and structuring the market for: {category} in {geo}. "
                            "Objective: a defensible TAM/SAM/SOM with sources, plus demand signals and segment structure.",
        "assumptions": [
            "Top-down (published sector size) cross-checked with bottom-up (units × price × adoption).",
            "Figures are estimates with stated sources, not precise forecasts.",
            f"Geography scoped to {geo}.",
        ],
        "required_data": [
            {"item": "Target customer definition + price point", "have": bool(data.get("price")), "why": "Bottom-up SAM/SOM math."},
            {"item": "Geography + segment focus", "have": True, "why": "Scope the addressable market."},
            {"item": "Adoption / penetration assumptions", "have": False, "why": "SOM realism."},
        ],
        "clarifying_questions": [
            f"Who exactly is the buyer for {category}, and what will they pay per year?",
            f"Which geography/segment do you serve first — all of {geo} or a beachhead?",
            "What share of the serviceable market do you realistically expect in 3 years?",
        ],
        "analysis": {
            "framework": "TAM (whole category) → SAM (serviceable: your geo + segment) → SOM (obtainable: realistic 3-yr share).",
            "tam": "Top-down from IBEF/industry sector size; state the figure + source.",
            "sam": "TAM filtered to your geography and target segment.",
            "som": "SAM × realistic reachable share (bottom-up: target customers × price × win-rate).",
            "demand_signals": ["Search/keyword trends", "Competitor funding + expansion", "Distributor/retailer pull", "Government scheme tailwinds"],
            "method_note": "Always reconcile top-down vs bottom-up; if they diverge >2x, re-examine assumptions.",
        },
        "risks": [
            {"risk": "TAM inflated by counting non-buyers (vanity sizing)", "severity": "High", "likelihood": "High",
             "control": "Bottom-up cross-check; define buyer + willingness-to-pay precisely.", "owner": "Strategy", "cite": "ibef"},
            {"risk": "Stale or single-source data", "severity": "Medium", "likelihood": "Medium",
             "control": "Triangulate ≥2 sources; date every figure.", "owner": "Research", "cite": "ibef"},
        ],
        "recommendations": [
            f"Build TAM/SAM/SOM for {category} with top-down (IBEF/sector reports) and bottom-up reconciled.",
            "Define the buyer and annual price point precisely — that drives a credible SAM/SOM.",
            "Pick a beachhead segment for SOM rather than claiming all of " + geo + ".",
            "Date and source every market figure; triangulate at least two sources.",
        ],
        "action_plan": [
            {"step": "Pull sector size (IBEF/industry) for TAM", "owner": "Research", "timeline": "Week 1", "system": "research_db"},
            {"step": "Bottom-up SAM/SOM from buyer × price × reach", "owner": "Strategy", "timeline": "Week 1", "system": "research_db"},
            {"step": "Document demand signals + sources", "owner": "Research", "timeline": "Week 1-2", "system": "research_db"},
        ],
        "erp_impact": [],
        "notion_update": [
            {"database": "research_db", "entry": f"TAM/SAM/SOM for {category} with sources, confidence and date."},
            {"database": "strategy_room", "entry": "Market-sizing summary + beachhead segment recommendation."},
        ],
        "compliance_impact": "Low direct compliance impact — but accurate, sourced market sizing is required for investor decks and grant/scheme applications (Startup India, state subsidies), where overstated claims are a diligence red flag.",
        "kpis_to_monitor": [
            {"kpi": "Market-sizing confidence", "current": "TBD", "target": "Triangulated ≥2 sources", "source": "research_db"},
            {"kpi": "SOM vs actual capture", "current": "TBD", "target": "On track", "source": "Sales"},
        ],
        "citations": _cite(*(["ibef", "startup_india"] + compliance_for(cls))),
        "human_approval_points": ["Founder sign-off on the SAM/SOM assumptions before they go into any investor or grant document."],
    }


# ============================================================
# 13l. FLAGSHIP GENERATOR — COMPETITOR INTELLIGENCE AGENT
# ============================================================
def gen_competitor_intel(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    competitors = data.get("competitors") or []

    return {
        "business_context": f"Mapping the competitive landscape for a {cls['industry'].replace('_',' ')} business"
                            + (f" vs {', '.join(competitors[:4])}" if competitors else "")
                            + ". Objective: positioning, pricing teardown, and white-space identification.",
        "assumptions": [
            "Competitor financials (for registered cos) can be pulled from MCA filings.",
            "Pricing/positioning gathered from public sources (sites, listings, GST/registered data).",
            "White space = unmet segment or price tier no competitor serves well.",
        ],
        "required_data": [
            {"item": "Named competitors (3-6)", "have": bool(competitors), "why": "Scope the teardown."},
            {"item": "Their pricing + positioning", "have": False, "why": "Pricing/positioning map."},
            {"item": "Your win/loss reasons", "have": False, "why": "Where you actually beat/lose them."},
        ],
        "clarifying_questions": [
            "Who are your top 3-5 competitors, and which one do you lose to most?",
            "What do customers say when they pick a competitor over you?",
            "Which segment or price tier do you think is underserved today?",
        ],
        "analysis": {
            "framework": "Competitor matrix (price × positioning × segment) → strengths/weaknesses → white-space.",
            "data_sources": ["MCA filings (financials for registered cos)", "Public pricing/listings", "Customer win/loss interviews", "IBEF sector structure"],
            "positioning_axes": ["Price (low↔premium)", "Breadth (niche↔full-range)", "Service (self-serve↔high-touch)"],
            "white_space_hypotheses": ["Underserved segment", "Unaddressed price tier", "Service/SLA gap", "Geography no one covers"],
        },
        "risks": [
            {"risk": "Competing on price into a margin war", "severity": "High", "likelihood": "Medium",
             "control": "Differentiate on service/segment, not just price; defend margin.", "owner": "Strategy", "cite": "benchmark_ar"},
            {"risk": "Intel based on assumptions, not evidence", "severity": "Medium", "likelihood": "High",
             "control": "Use MCA financials + real customer win/loss, not hearsay.", "owner": "Research", "cite": "companies_act"},
        ],
        "recommendations": [
            "Build a competitor matrix on price × positioning × segment; mark where you genuinely win.",
            "Pull MCA financials for registered competitors to gauge their scale and health.",
            "Run 5-10 win/loss interviews — the cheapest, highest-signal competitive intel.",
            "Target a white-space (underserved segment / price tier / service gap) rather than a head-on price fight.",
        ],
        "action_plan": [
            {"step": "Build competitor matrix + pull MCA financials", "owner": "Research", "timeline": "Week 1", "system": "research_db"},
            {"step": "Run win/loss interviews", "owner": "Sales", "timeline": "Week 1-2", "system": "—"},
            {"step": "Define positioning + white-space play", "owner": "Strategy", "timeline": "Week 2", "system": "strategy_room"},
        ],
        "erp_impact": [],
        "notion_update": [
            {"database": "research_db", "entry": "Competitor matrix + financials + win/loss findings with sources."},
            {"database": "strategy_room", "entry": "Positioning statement + white-space play."},
        ],
        "compliance_impact": "Low direct impact. Ensure competitive intel uses lawful public sources (MCA, listings) — avoid misappropriating confidential data.",
        "kpis_to_monitor": [
            {"kpi": "Win rate vs key competitor", "current": "TBD", "target": "Rising", "source": "CRM"},
            {"kpi": "Price realization", "current": "TBD", "target": "Hold/improve", "source": "Sales"},
        ],
        "citations": _cite(*(["companies_act", "ibef", "benchmark_ar"] + compliance_for(cls))),
        "human_approval_points": ["Founder sign-off on the positioning + white-space play before go-to-market."],
    }


# ============================================================
# 13m. FLAGSHIP GENERATOR — PRODUCT MANAGER AGENT
# ============================================================
def gen_product_manager(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    problem = data.get("problem") or desc.strip() or "the product problem"

    return {
        "business_context": f"Turning a problem into a shippable plan: {problem}. "
                            "Objective: a crisp PRD, a RICE-prioritized backlog, and a 90-day roadmap.",
        "assumptions": [
            "Build the smallest thing that validates the riskiest assumption first (MVP).",
            "Prioritise by RICE (Reach × Impact × Confidence ÷ Effort), not loudest stakeholder.",
            "Each item ties to a measurable outcome.",
        ],
        "required_data": [
            {"item": "Problem + target user", "have": problem != "the product problem", "why": "Scope the PRD."},
            {"item": "Current solution / workaround", "have": False, "why": "Baseline + switching cost."},
            {"item": "Success metric", "have": bool(data.get("metric")), "why": "Define done."},
        ],
        "clarifying_questions": [
            f"Who has the '{problem}' problem most acutely, and how do they solve it today?",
            "What single metric tells you this is working?",
            "What is the hard deadline or constraint (budget, team size)?",
        ],
        "analysis": {
            "prd_outline": ["Problem + user", "Goals + non-goals", "User stories", "Success metrics", "Scope (MVP vs later)", "Risks/dependencies"],
            "prioritization": "RICE — score each feature Reach × Impact × Confidence ÷ Effort; build top quartile first.",
            "mvp_principle": "Ship the smallest slice that validates the riskiest assumption; instrument it.",
            "roadmap_90d": ["Days 0-30: MVP of top RICE item", "Days 31-60: iterate on usage data", "Days 61-90: expand to next segment/feature"],
        },
        "risks": [
            {"risk": "Building features nobody asked for (no validation)", "severity": "High", "likelihood": "High",
             "control": "Validate the riskiest assumption with an MVP before scaling.", "owner": "PM", "cite": "benchmark_d2c"},
            {"risk": "Scope creep blows the timeline", "severity": "Medium", "likelihood": "High",
             "control": "Lock MVP scope; everything else to the backlog.", "owner": "PM", "cite": "benchmark_d2c"},
        ],
        "recommendations": [
            f"Write a one-page PRD for '{problem}' with explicit goals, non-goals and a success metric.",
            "Score the backlog with RICE and build only the top quartile for the MVP.",
            "Ship the MVP in 30 days, instrument usage, and let data drive the next 60.",
            "Guard scope ruthlessly — defer everything non-essential to the backlog.",
        ],
        "action_plan": [
            {"step": "Draft PRD + define success metric", "owner": "PM", "timeline": "Week 1", "system": "strategy_room"},
            {"step": "RICE-score backlog; lock MVP scope", "owner": "PM", "timeline": "Week 1", "system": "task_tracker"},
            {"step": "Build + instrument MVP", "owner": "Eng", "timeline": "Days 0-30", "system": "task_tracker"},
            {"step": "Review usage; plan next 60 days", "owner": "PM", "timeline": "Day 30", "system": "task_tracker"},
        ],
        "erp_impact": [],
        "notion_update": [
            {"database": "strategy_room", "entry": "PRD: problem, goals, success metric, MVP scope."},
            {"database": "task_tracker", "entry": "RICE-scored backlog + 90-day roadmap."},
        ],
        "compliance_impact": "If the product handles personal data, the PRD must include DPDP Act 2023 requirements (consent, data minimisation) as non-functional requirements from day one.",
        "kpis_to_monitor": [
            {"kpi": "Time-to-MVP", "current": "TBD", "target": "<= 30 days", "source": "task_tracker"},
            {"kpi": "MVP success metric", "current": "TBD", "target": "Defined + hit", "source": "Product analytics"},
            {"kpi": "Feature throughput", "current": "TBD", "target": "Rising", "source": "task_tracker"},
        ],
        "citations": _cite(*(["benchmark_d2c"] + (["meity_ai"] if cls["is_tech"] else []) + compliance_for(cls))),
        "human_approval_points": ["Founder/PM sign-off on MVP scope and the success metric before build starts."],
    }


# ============================================================
# 13n. FLAGSHIP GENERATOR — NOTION WORKSPACE AGENT
# ============================================================
def gen_notion_workspace(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    return {
        "business_context": f"Standing up the Notion operating workspace for a {cls['size']} {cls['industry'].replace('_',' ')} business "
                            "so every AI-agent output lands in the right database and becomes a tracked action.",
        "assumptions": [
            "Notion is the operating/PM layer; the ERP is the system of record for transactions.",
            "Agents write recommendations, risks, tasks and compliance items to specific databases (no free-floating notes).",
            "Access is role-based (founder/investor/ops views).",
        ],
        "required_data": [
            {"item": "Team roles + who needs which view", "have": False, "why": "Access control + dashboards."},
            {"item": "Workspace goals (founder/investor/DD/ops)", "have": False, "why": "Which rooms to build first."},
            {"item": "Notion API token (for live sync)", "have": False, "why": "Automated agent → DB writes."},
        ],
        "clarifying_questions": [
            "Who are the users and what does each role need to see (founder, ops, investor)?",
            "Which rooms do you need first — founder dashboard, DD room, or SOP repo?",
            "Do you want agents to write to Notion automatically, or propose-then-approve?",
        ],
        "analysis": {
            "databases_to_create": [{"key": k, "name": v["name"], "fields": v["fields"]} for k, v in NOTION_DATABASES.items()],
            "agent_sync_map": {
                "cfo_finance → founder_dashboard, kpi_db": "cash/DSO/margin",
                "gst_compliance → compliance_tracker": "filing obligations",
                "risk_audit → risk_register": "scored risks",
                "msme_due_diligence → dd_room, investor_workspace": "DD checklist + red flags",
                "sop_agent → sop_repo": "versioned SOPs",
            },
            "views": ["Founder dashboard (KPIs + priorities)", "Investor view (read-only data room)", "Ops board (tasks + SOPs)", "Compliance calendar"],
            "sync_modes": "Propose-then-approve by default; auto-write for low-risk items (KPIs, tasks).",
        },
        "risks": [
            {"risk": "Workspace becomes a dumping ground nobody uses", "severity": "Medium", "likelihood": "High",
             "control": "Structured databases (not free pages) + a single founder dashboard as the entry point.", "owner": "Ops", "cite": "msmed_act"},
            {"risk": "Sensitive data over-shared via wrong access", "severity": "High", "likelihood": "Medium",
             "control": "Role-based access; investor view is read-only and scoped.", "owner": "Founder", "cite": "meity_ai"},
        ],
        "recommendations": [
            "Create the 13 core databases as structured tables (not free-form pages) so agents can write to defined fields.",
            "Make the Founder Dashboard the single entry point; everything rolls up to it.",
            "Wire each agent's output to its database via the sync map; default to propose-then-approve.",
            "Set role-based access: founder full, ops board, investor read-only scoped to the data room.",
        ],
        "action_plan": [
            {"step": "Create core databases + fields", "owner": "Ops", "timeline": "Week 1", "system": "—"},
            {"step": "Build role-based views + founder dashboard", "owner": "Ops", "timeline": "Week 1-2", "system": "—"},
            {"step": "Connect Notion API; wire agent sync map", "owner": "Tech", "timeline": "Week 2-3", "system": "—"},
            {"step": "Set access controls + train team", "owner": "Founder", "timeline": "Week 3", "system": "—"},
        ],
        "erp_impact": [
            {"module": "finance", "change": "Feed KPIs (cash, DSO, margin) to the Notion founder dashboard."},
            {"module": "compliance", "change": "Sync obligations + due dates to the compliance tracker."},
        ],
        "notion_update": [{"database": k, "entry": f"Initialise '{v['name']}' with fields: {', '.join(v['fields'])}."} for k, v in list(NOTION_DATABASES.items())[:6]],
        "compliance_impact": "Role-based access + a scoped investor view support DPDP Act data-minimisation. A structured compliance tracker ensures statutory obligations are visible and owned, not lost in chat.",
        "kpis_to_monitor": [
            {"kpi": "Workspace adoption (active users)", "current": "TBD", "target": "All roles weekly", "source": "Notion"},
            {"kpi": "Action-item closure rate", "current": "TBD", "target": "> 80%", "source": "task_tracker"},
        ],
        "citations": _cite(*(["meity_ai", "msmed_act"] + compliance_for(cls))),
        "human_approval_points": ["Founder approval of access roles before sharing any investor/DD view externally."],
    }


# ============================================================
# 13o. FLAGSHIP GENERATOR — SALES & GTM AGENT
# ============================================================
def gen_sales_gtm(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    outlets = data.get("outlets") or _num(desc, r"([0-9]+)\s*outlet", r"([0-9]+)\s*store", r"([0-9]+)\s*dealer")
    is_distribution = cls["industry"] in ("wholesale", "retail") or "beat" in desc.lower() or outlets

    if is_distribution:
        motion = "Distribution: salesman beat plan + outlet coverage + secondary-sales visibility"
    elif cls["is_tech"] or cls["industry"] == "d2c":
        motion = "Digital: funnel (acquire → activate → retain) + CAC/LTV-led spend"
    else:
        motion = "B2B: lead → qualify → proposal → close with a defined pipeline"

    return {
        "business_context": f"Designing the GTM motion for a {cls['industry'].replace('_',' ')} business"
                            + (f" covering ~{int(outlets)} outlets" if outlets else "")
                            + f". Recommended motion — {motion.split(':')[0]}.",
        "assumptions": [
            "Channel + pricing strategy follow the chosen motion.",
            f"Motion selected: {motion}.",
            "CRM/ERP captures the pipeline or beat so it's measurable.",
        ],
        "required_data": [
            {"item": "Current sales data + channels", "have": bool(data.get("sales")), "why": "Baseline conversion + channel mix."},
            {"item": ("Outlet list + geography" if is_distribution else "Funnel/pipeline data"), "have": outlets is not None, "why": "Beat design / funnel math."},
            {"item": "Pricing + margin by SKU/plan", "have": False, "why": "Channel + discount strategy."},
        ],
        "clarifying_questions": [
            ("How many outlets, how many salesmen, and what's the current coverage frequency?" if is_distribution
             else "What's your current CAC, conversion rate and sales-cycle length?"),
            "What are your highest-margin products/plans to push?",
            "Which channel converts best today, and which is most under-used?",
        ],
        "analysis": {
            "recommended_motion": motion,
            "beat_plan": ((f"~{int(outlets)} outlets" if outlets else "Your outlet universe") + " ÷ coverage frequency ÷ ~30-40 calls/salesman/day → required salesmen + route clusters." if is_distribution else "N/A"),
            "funnel": ("Acquire → Activate → Retain; track CAC, conversion, LTV per channel." if not is_distribution else "Primary → secondary sales; track outlet productivity + range-selling."),
            "pricing_levers": ["Differentiated price list by channel", "Scheme/discount governance", "Push high-margin range"],
            "unit_economics": _bench("ltv_cac") if (cls["is_tech"] or cls["industry"] == "d2c") else _bench("dso_days"),
        },
        "risks": [
            {"risk": ("Uneven outlet coverage / unproductive beats" if is_distribution else "CAC exceeds LTV — unprofitable growth"),
             "severity": "High", "likelihood": "Medium",
             "control": ("Cluster routes; set calls/day + range-selling targets; track via CRM." if is_distribution else "Cap CAC at LTV/3; kill channels below threshold."),
             "owner": "Sales head", "cite": "benchmark_d2c"},
            {"risk": "Uncontrolled discounts erode margin", "severity": "High", "likelihood": "High",
             "control": "Discount approval matrix; track net realization per order.", "owner": "Sales head", "cite": "benchmark_ar"},
        ],
        "recommendations": ([
            f"Design a beat plan for ~{int(outlets) if outlets else 'all'} outlets: cluster routes, set calls/day and range-selling targets per salesman.",
            "Track secondary sales + outlet productivity in CRM/ERP, not just primary dispatch.",
            "Run differentiated price lists by channel and govern schemes with an approval matrix.",
        ] if is_distribution else [
            "Map the funnel and measure CAC, conversion and LTV per channel; double down on the best.",
            "Hold LTV:CAC ≥ 3:1 and CAC payback < 12 months; cut channels that miss it.",
            "Push high-margin plans/SKUs and govern discounts with an approval matrix.",
        ]) + ["Tie every salesperson/channel to a measurable target in the CRM/ERP."],
        "action_plan": [
            {"step": ("Build beat plan + route clusters" if is_distribution else "Map funnel + channel CAC/LTV"), "owner": "Sales head", "timeline": "Week 1-2", "system": "sales/customers"},
            {"step": "Set channel price lists + discount approval matrix", "owner": "Sales head", "timeline": "Week 2", "system": "customers"},
            {"step": "Configure CRM targets + tracking", "owner": "Sales ops", "timeline": "Week 2-3", "system": "sales"},
        ],
        "erp_impact": [
            {"module": "sales", "change": ("Capture beat/route, outlet visits, secondary sales." if is_distribution else "Track pipeline stages + channel attribution.")},
            {"module": "customers", "change": "Channel-specific price lists + credit terms + discount approval."},
        ],
        "notion_update": [
            {"database": "strategy_room", "entry": f"GTM motion + {'beat plan' if is_distribution else 'funnel strategy'} + pricing."},
            {"database": "kpi_db", "entries": (["Outlet coverage %", "Secondary sales", "Lines/bill"] if is_distribution else ["CAC", "Conversion %", "LTV:CAC"])},
        ],
        "compliance_impact": "Channel pricing and schemes must keep GST treatment correct (discounts via credit notes, not off-invoice without documentation) to avoid ITC/valuation issues.",
        "kpis_to_monitor": ([
            {"kpi": "Outlet coverage %", "current": "TBD", "target": "> 90%", "source": "CRM"},
            {"kpi": "Lines per bill (range selling)", "current": "TBD", "target": "Rising", "source": "Sales"},
        ] if is_distribution else [
            {"kpi": "LTV:CAC", "current": "TBD", "target": ">= 3:1", "source": "Finance/CRM"},
            {"kpi": "CAC payback (months)", "current": "TBD", "target": "< 12", "source": "Finance"},
        ]),
        "citations": _cite(*(["benchmark_d2c", "benchmark_ar", "gst_portal"] + compliance_for(cls))),
        "human_approval_points": ["Sales head/owner approval of pricing, discount matrix and beat/channel plan."],
    }


# ============================================================
# 13p. FLAGSHIP GENERATOR — PROCUREMENT AGENT
# ============================================================
def gen_procurement(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    return {
        "business_context": f"Optimising procurement for a {cls['size']} {cls['industry'].replace('_',' ')} business: "
                            "vendor performance, PO-to-GRN discipline, and cost control.",
        "assumptions": [
            "Vendor master, PO history and quality data are (or can be) captured in the ERP.",
            "3-way match (PO ↔ GRN ↔ invoice) is the core control.",
            "MSME (Udyam) vendors carry the 45-day payment obligation.",
        ],
        "required_data": [
            {"item": "Vendor master + MSME (Udyam) status", "have": bool(scenario.get("data", {}).get("vendors")), "why": "Scorecard + 45-day clock."},
            {"item": "PO + GRN + invoice history", "have": False, "why": "3-way match + cycle time."},
            {"item": "Quality/rejection data", "have": False, "why": "Vendor performance (OTIF, quality)."},
        ],
        "clarifying_questions": [
            "Where do delays happen — indent, PO, supplier dispatch, or GRN?",
            "Do you 3-way match (PO-GRN-invoice) before paying, or pay on invoice?",
            "How many vendors per key item — single-source or multi-source?",
        ],
        "analysis": {
            "vendor_scorecard": ["On-time-in-full (OTIF) %", "Quality/rejection rate", "Price competitiveness", "Responsiveness"],
            "controls": ["3-way match before payment", "Approval matrix by PO value", "Vendor master maker-checker", "Periodic rate benchmarking"],
            "cost_levers": ["Consolidate volume to fewer, better vendors", "Negotiate annual rate contracts", "Multi-source critical items to de-risk"],
            "cycle": "Indent → PO → GRN → invoice → payment; measure each step's time.",
        },
        "risks": [
            {"risk": "Vendor fraud (ghost vendors, inflated rates, kickbacks)", "severity": "High", "likelihood": "Medium",
             "control": "Vendor-master maker-checker, 3-way match, periodic rate benchmarking.", "owner": "Procurement head", "cite": "companies_act"},
            {"risk": "Raw-material delays stall production/sales", "severity": "High", "likelihood": "Medium",
             "control": "Track OTIF; multi-source critical items; safety stock on long-lead items.", "owner": "Procurement", "cite": "benchmark_ar"},
            {"risk": "MSME vendors unpaid beyond 45 days → Sec 43B(h) disallowance", "severity": "High", "likelihood": "Medium",
             "control": "Tag Udyam vendors; enforce 45-day payment.", "owner": "AP", "cite": "sec_43b_h"},
        ],
        "recommendations": [
            "Build a vendor scorecard (OTIF, quality, price, responsiveness) and review quarterly.",
            "Enforce 3-way match (PO-GRN-invoice) before any payment to block purchase fraud.",
            "Consolidate volume to high-performing vendors; multi-source critical items to de-risk supply.",
            "Tag Udyam (MSME) vendors and pay within 45 days to avoid Sec 43B(h) disallowance.",
        ],
        "action_plan": [
            {"step": "Clean vendor master + tag MSME status", "owner": "Procurement", "timeline": "Week 1", "system": "vendors"},
            {"step": "Enable 3-way match + PO approval matrix", "owner": "ERP admin", "timeline": "Week 1-2", "system": "purchase"},
            {"step": "Build vendor scorecard from history", "owner": "Procurement", "timeline": "Week 2-3", "system": "purchase"},
            {"step": "Negotiate rate contracts with top vendors", "owner": "Procurement head", "timeline": "Week 3-4", "system": "vendors"},
        ],
        "erp_impact": [
            {"module": "vendors", "change": "Vendor master with MSME status, terms, scorecard fields."},
            {"module": "purchase", "change": "Indent→PO→GRN flow with 3-way match + value-based approval matrix."},
            {"module": "inventory", "change": "Link GRN to stock + reorder for supply continuity."},
            {"module": "payables", "change": "45-day clock on Udyam vendors."},
        ],
        "notion_update": [
            {"database": "task_tracker", "entries": ["Vendor master cleanup", "3-way match setup", "Rate-contract negotiation"]},
            {"database": "risk_register", "entry": "Vendor fraud + supply-continuity risks with controls."},
            {"database": "kpi_db", "entries": ["Vendor OTIF %", "PO cycle time", "Cost savings"]},
        ],
        "compliance_impact": "3-way match and vendor-master controls are core internal controls for statutory audit. Sec 43B(h) makes paying MSME vendors within 45 days a direct tax matter.",
        "kpis_to_monitor": [
            {"kpi": "Vendor OTIF %", "current": "TBD", "target": "> 95%", "source": "Purchase"},
            {"kpi": "PO cycle time", "current": "TBD", "target": "Falling", "source": "Purchase"},
            {"kpi": "MSME payments within 45 days %", "current": "TBD", "target": "100%", "source": "AP"},
        ],
        "citations": _cite(*(["companies_act", "sec_43b_h", "benchmark_ar"] + compliance_for(cls))),
        "human_approval_points": [
            "Procurement head approval of new vendors (after maker-checker) and rate contracts.",
            "Finance approval of the PO approval matrix thresholds.",
        ],
    }


# ============================================================
# 13q. FLAGSHIP GENERATOR — CUSTOMER SUPPORT AGENT
# ============================================================
def gen_customer_support(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    is_whatsapp = "whatsapp" in desc.lower()
    is_returns = "return" in desc.lower()

    return {
        "business_context": f"Setting up support for a {cls['industry'].replace('_',' ')} business"
                            + (" handling high WhatsApp query volume" if is_whatsapp else "")
                            + (" with heavy returns" if is_returns else "")
                            + ". Objective: triage, SLA control, and consistent responses.",
        "assumptions": [
            "Tickets flow from one or more channels (WhatsApp, email, calls) into one queue.",
            "SLAs are defined by priority; breaches are tracked.",
            "Repetitive queries can be templated/automated; edge cases go to humans.",
        ],
        "required_data": [
            {"item": "Ticket volume + channels", "have": False, "why": "Staffing + automation scope."},
            {"item": "Top query types", "have": False, "why": "Template/automate the repetitive 80%."},
            {"item": "SLA policy", "have": False, "why": "Prioritisation + breach tracking."},
        ],
        "clarifying_questions": [
            "What are your top 5 query types, and which are pure repetition?",
            "What response-time do customers expect, and what's your current SLA?",
            "Which channel carries the most volume (WhatsApp, calls, email)?",
        ],
        "analysis": {
            "triage": "Classify by type + priority (P1 urgent → P3 routine); route P1 to humans, template P3.",
            "sla_targets": {"P1 first response": "< 1 hr", "P2": "< 4 hrs", "P3": "< 24 hrs"},
            "automation": "Draft templated replies for the repetitive 80%; AI suggests, human approves for sensitive cases.",
            "returns_flow": ("Returns: validate → approve → credit note + restock; track reason codes to fix root cause." if is_returns else "N/A"),
            "channels": (["WhatsApp Business API", "Email", "Calls"] if is_whatsapp else ["Email", "Calls"]),
        },
        "risks": [
            {"risk": "SLA breaches → churn + bad reviews", "severity": "High", "likelihood": "Medium",
             "control": "Priority-based SLAs + breach alerts + daily queue review.", "owner": "Support lead", "cite": "benchmark_d2c"},
            {"risk": "Inconsistent answers across agents", "severity": "Medium", "likelihood": "High",
             "control": "Approved response templates + a knowledge base.", "owner": "Support lead", "cite": "benchmark_d2c"},
            {"risk": "Returns abuse / unrecorded credit notes", "severity": "Medium", "likelihood": "Medium",
             "control": "Returns approval workflow + credit note in ERP + reason codes.", "owner": "Ops", "cite": "gst_portal"},
        ],
        "recommendations": [
            "Funnel all channels into one queue; classify every ticket by type + priority.",
            "Template the repetitive 80% (AI-drafted, human-approved for sensitive cases).",
            "Set priority-based SLAs with breach alerts and a daily queue review.",
            ("Formalise the returns flow: validate → approve → ERP credit note + restock, with reason codes to fix root causes." if is_returns
             else "Build a knowledge base so answers are consistent across the team."),
        ],
        "action_plan": [
            {"step": "Define query taxonomy + SLA policy", "owner": "Support lead", "timeline": "Week 1", "system": "customers"},
            {"step": "Build response templates + knowledge base", "owner": "Support", "timeline": "Week 1-2", "system": "—"},
            {"step": ("Wire WhatsApp/email into one queue" if is_whatsapp else "Set up shared ticket queue"), "owner": "Tech", "timeline": "Week 2", "system": "customers"},
            {"step": "Track SLA + CSAT; weekly review", "owner": "Support lead", "timeline": "Ongoing", "system": "—"},
        ],
        "erp_impact": [
            {"module": "customers", "change": "Link tickets to customer; capture interaction history."},
            {"module": "sales", "change": ("Returns → credit note + restock with reason codes." if is_returns else "Surface order status for support context.")},
        ],
        "notion_update": [
            {"database": "task_tracker", "entry": "Support setup: taxonomy, templates, SLA, knowledge base."},
            {"database": "kpi_db", "entries": ["First response time", "CSAT", "SLA breach %"]},
        ],
        "compliance_impact": ("Returns must generate proper GST credit notes (not informal refunds) to keep tax records correct. " if is_returns else "")
                              + "If support handles personal data, follow DPDP Act 2023 (consent, retention limits).",
        "kpis_to_monitor": [
            {"kpi": "First response time", "current": "TBD", "target": "< 1 hr (P1)", "source": "Helpdesk"},
            {"kpi": "CSAT", "current": "TBD", "target": "> 90%", "source": "Survey"},
            {"kpi": "SLA breach %", "current": "TBD", "target": "< 5%", "source": "Helpdesk"},
        ],
        "citations": _cite(*(["benchmark_d2c", "gst_portal", "meity_ai"] + compliance_for(cls))),
        "human_approval_points": ["Support lead approval of templates and the SLA policy; humans handle all sensitive/escalated tickets."],
    }


# ============================================================
# 13r. FLAGSHIP GENERATOR — LEGAL CONTRACTS AGENT
# ============================================================
def gen_legal_contracts(scenario: dict, cls: dict) -> dict:
    desc = scenario.get("description", "")
    data = scenario.get("data", {})
    ctype = data.get("contract_type") or next((t for t in ("distributor", "vendor", "employment", "nda", "lease", "saas", "service") if t in desc.lower()), "the agreement")

    flagged = [
        {"clause": "Payment terms + interest on delay", "why": "MSME 45-day + interest under MSMED Act; align with cash flow.", "cite": "msmed_act"},
        {"clause": "Termination + notice period", "why": "Avoid lock-in; ensure a clean exit and survival clauses.", "cite": "contract_act"},
        {"clause": "Indemnity + limitation of liability", "why": "Cap exposure; mutual indemnity, not one-sided.", "cite": "contract_act"},
        {"clause": "Dispute resolution + jurisdiction", "why": "Prefer arbitration seat in India; define governing law.", "cite": "contract_act"},
        {"clause": "Confidentiality + IP ownership", "why": "Ensure IP/work product vests in the company.", "cite": "contract_act"},
    ]
    if ctype in ("distributor", "vendor"):
        flagged.append({"clause": "Exclusivity + territory + minimum commitments", "why": "Don't over-commit volumes/exclusivity without protection.", "cite": "contract_act"})
    if ctype == "saas":
        flagged.append({"clause": "Data processing + DPDP compliance", "why": "Define controller/processor roles + data-protection obligations.", "cite": "meity_ai"})

    return {
        "business_context": f"Reviewing {ctype} contract(s) for a {cls['industry'].replace('_',' ')} business. "
                            "Objective: flag risky clauses, extract obligations, and ensure enforceability.",
        "assumptions": [
            "This is a first-pass risk review, not a substitute for a lawyer on high-value contracts.",
            "Indian Contract Act governs validity; stamp duty affects admissibility.",
            "Obligations and dates must be tracked, not just signed and filed.",
        ],
        "required_data": [
            {"item": "The contract text + parties", "have": bool(data.get("text")), "why": "Clause-level review."},
            {"item": "Contract value + duration", "have": False, "why": "Risk weighting + stamp duty."},
            {"item": "Commercial intent (what you actually agreed)", "have": False, "why": "Check text matches intent."},
        ],
        "clarifying_questions": [
            f"What is the value and duration of this {ctype} contract?",
            "What's the worst-case scenario you want protection against?",
            "Is this on your paper or the counterparty's (drives negotiating leverage)?",
        ],
        "analysis": {
            "contract_type": ctype,
            "clauses_to_review": flagged,
            "enforceability_checks": ["Properly stamped (Stamp Act)", "Authorised signatories", "Clear consideration", "Defined term + termination"],
            "obligation_extraction": "List every obligation with owner + due date; load into the compliance/task tracker.",
        },
        "risks": [
            {"risk": "One-sided indemnity / unlimited liability", "severity": "High", "likelihood": "Medium",
             "control": "Cap liability; make indemnity mutual.", "owner": "Legal/Founder", "cite": "contract_act"},
            {"risk": "Unstamped / under-stamped agreement inadmissible in court", "severity": "High", "likelihood": "Medium",
             "control": "Pay correct stamp duty for the state before signing.", "owner": "Legal", "cite": "stamp_act"},
            {"risk": "Auto-renewal / lock-in with no clean exit", "severity": "Medium", "likelihood": "Medium",
             "control": "Negotiate notice-based termination + survival clauses.", "owner": "Legal", "cite": "contract_act"},
            {"risk": "IP / work product not vesting in the company", "severity": "High", "likelihood": "Medium",
             "control": "Explicit IP-assignment clause.", "owner": "Legal", "cite": "contract_act"},
        ],
        "recommendations": [
            f"Review the {ctype} contract against the flagged clauses (payment, termination, indemnity, dispute, IP).",
            "Cap liability and make indemnity mutual; reject one-sided exposure.",
            "Ensure the agreement is correctly stamped for the state — unstamped docs aren't admissible.",
            "Extract every obligation with an owner + due date and load it into the compliance tracker.",
        ],
        "action_plan": [
            {"step": "Clause-by-clause review against the checklist", "owner": "Legal/Founder", "timeline": "Day 1-3", "system": "—"},
            {"step": "Negotiate flagged clauses with counterparty", "owner": "Founder", "timeline": "Week 1", "system": "—"},
            {"step": "Confirm stamping + authorised signatories", "owner": "Legal", "timeline": "Before signing", "system": "compliance"},
            {"step": "Extract obligations into tracker", "owner": "Ops", "timeline": "On signing", "system": "compliance"},
        ],
        "erp_impact": [
            {"module": "compliance", "change": "Store contract + extracted obligations with due dates + renewal alerts."},
            {"module": "vendors", "change": "Link vendor/distributor contracts to the vendor master + payment terms."},
            {"module": "customers", "change": "Link customer contracts to terms + credit limits."},
        ],
        "notion_update": [
            {"database": "risk_register", "entries": [r["risk"] for r in [
                {"risk": "One-sided indemnity"}, {"risk": "Unstamped agreement"}, {"risk": "IP not vesting"}]]},
            {"database": "compliance_tracker", "entry": "Contract obligations + renewal/termination dates with owners."},
        ],
        "compliance_impact": "Enforceability hinges on the Indian Contract Act (valid consideration, free consent) and the Stamp Act (correct stamp duty — unstamped agreements are inadmissible). For SaaS/data contracts, DPDP Act roles must be defined.",
        "kpis_to_monitor": [
            {"kpi": "Contract turnaround time", "current": "TBD", "target": "Falling", "source": "Legal"},
            {"kpi": "Obligations tracked %", "current": "TBD", "target": "100%", "source": "Compliance tracker"},
            {"kpi": "Renewals missed", "current": "TBD", "target": "0", "source": "Compliance tracker"},
        ],
        "citations": _cite(*(["contract_act", "stamp_act", "msmed_act"] + (["meity_ai"] if ctype == "saas" else []) + compliance_for(cls))),
        "human_approval_points": [
            "Qualified lawyer review for high-value or non-standard contracts.",
            "Founder/authorised signatory sign-off before execution.",
        ],
    }


# ============================================================
# 14. WIRE GENERATORS → REGISTRY + DISPATCHER
# ============================================================
_GENERATORS = {
    "gst_compliance": gen_gst_compliance,
    "cfo_finance": gen_cfo_finance,
    "msme_due_diligence": gen_due_diligence,
    "erp_consultant": gen_erp_consultant,
    "investor_readiness": gen_investor_readiness,
    "inventory_agent": gen_inventory,
    "export_compliance": gen_export_compliance,
    "ceo_copilot": gen_ceo_copilot,
    "coo_operations": gen_coo_operations,
    "risk_audit": gen_risk_audit,
    "sop_agent": gen_sop,
    "hr_payroll": gen_hr_payroll,
    "market_research": gen_market_research,
    "competitor_intel": gen_competitor_intel,
    "product_manager": gen_product_manager,
    "notion_workspace": gen_notion_workspace,
    "sales_gtm": gen_sales_gtm,
    "procurement_agent": gen_procurement,
    "customer_support": gen_customer_support,
    "legal_contracts": gen_legal_contracts,
}
for _k, _fn in _GENERATORS.items():
    MSME_AGENTS[_k]["generator"] = _fn
    MSME_AGENTS[_k]["status"] = "live"  # any agent with a generator is live

# UX metadata: which workspace mode (startup / existing business) an agent suits,
# and its grouping category. Drives the two-section, filterable frontend.
AGENT_UX = {
    "ceo_copilot":        {"category": "Strategy & Growth",     "modes": ["startup", "existing"]},
    "coo_operations":     {"category": "Operations",            "modes": ["existing"]},
    "cfo_finance":        {"category": "Finance & Compliance",  "modes": ["startup", "existing"]},
    "gst_compliance":     {"category": "Finance & Compliance",  "modes": ["startup", "existing"]},
    "erp_consultant":     {"category": "Operations",            "modes": ["existing"]},
    "msme_due_diligence": {"category": "Risk & Diligence",      "modes": ["startup", "existing"]},
    "market_research":    {"category": "Strategy & Growth",     "modes": ["startup"]},
    "competitor_intel":   {"category": "Strategy & Growth",     "modes": ["startup", "existing"]},
    "product_manager":    {"category": "Strategy & Growth",     "modes": ["startup"]},
    "notion_workspace":   {"category": "Workspace",             "modes": ["startup", "existing"]},
    "sop_agent":          {"category": "Operations",            "modes": ["existing"]},
    "risk_audit":         {"category": "Risk & Diligence",      "modes": ["existing"]},
    "inventory_agent":    {"category": "Operations",            "modes": ["existing"]},
    "sales_gtm":          {"category": "Strategy & Growth",     "modes": ["startup", "existing"]},
    "procurement_agent":  {"category": "Operations",            "modes": ["existing"]},
    "customer_support":   {"category": "Operations",            "modes": ["existing"]},
    "hr_payroll":         {"category": "Finance & Compliance",  "modes": ["existing"]},
    "export_compliance":  {"category": "Risk & Diligence",      "modes": ["startup", "existing"]},
    "legal_contracts":    {"category": "Finance & Compliance",  "modes": ["startup", "existing"]},
    "investor_readiness": {"category": "Risk & Diligence",      "modes": ["startup"]},
}
for _k, _ux in AGENT_UX.items():
    if _k in MSME_AGENTS:
        MSME_AGENTS[_k].update(_ux)


def list_agents():
    """Public registry (no function objects) for /agents/meta."""
    out = {}
    for k, a in MSME_AGENTS.items():
        out[k] = {x: v for x, v in a.items() if x != "generator"}
    return out


def run_agent(agent_key: str, scenario: dict) -> dict:
    """Run one agent against a scenario; always returns the audit-ready envelope."""
    agent = MSME_AGENTS.get(agent_key)
    if not agent:
        return {"error": f"unknown agent '{agent_key}'", "available": list(MSME_AGENTS.keys())}
    if agent.get("status") != "live" or "generator" not in agent:
        return {
            "agent": agent_key, "name": agent["name"], "status": "planned",
            "message": f"{agent['name']} is registered but not yet live in this build. Live agents: "
                       + ", ".join(k for k, a in MSME_AGENTS.items() if a.get('status') == 'live') + ".",
            "card": {x: v for x, v in agent.items() if x != "generator"},
        }
    desc = (scenario or {}).get("description", "")
    cls = classify_business(desc)
    try:
        env = agent["generator"](scenario or {}, cls)
    except Exception as e:
        import traceback as _tb
        return {"agent": agent_key, "name": agent["name"], "status": "error",
                "error": str(e), "trace": _tb.format_exc()[-800:]}
    missing = _validate_envelope(env)
    return {
        "agent": agent_key,
        "name": agent["name"],
        "icon": agent["icon"],
        "status": "ok",
        "classification": cls,
        "envelope_complete": len(missing) == 0,
        "missing_keys": missing,
        "output": env,
    }


# ============================================================
# 14b. END-TO-END ENGAGEMENT (JOURNEY) ORCHESTRATOR
# ============================================================
# Runs every agent relevant to the chosen mode (startup / existing) against ONE
# business scenario and assembles a consolidated engagement pack — the platform's
# "full advisory team", end-to-end. Works for all 17 sectors incl. import/export
# (the classifier + compliance_for cover trade roles automatically).
_CATEGORY_RANK = {c: i for i, c in enumerate(
    ["Strategy & Growth", "Finance & Compliance", "Operations", "Risk & Diligence", "Workspace"])}


def agents_for_mode(mode: str, cls: dict = None) -> list:
    """Ordered list of live agent keys relevant to a mode (and business, if given)."""
    keys = [k for k, a in MSME_AGENTS.items()
            if a.get("status") == "live" and mode in a.get("modes", [])]
    # If the business does no cross-border trade, drop the export/customs agent
    # from the auto-journey (still available to run individually).
    if cls and cls.get("trade_role") == "domestic":
        keys = [k for k in keys if k != "export_compliance"]
    keys.sort(key=lambda k: (_CATEGORY_RANK.get(MSME_AGENTS[k].get("category"), 9), MSME_AGENTS[k]["name"]))
    return keys


def run_journey(mode: str, scenario: dict) -> dict:
    """End-to-end: run all relevant agents + aggregate an executive summary."""
    mode = mode if mode in ("startup", "existing") else "existing"
    desc = (scenario or {}).get("description", "")
    cls = classify_business(desc)
    keys = agents_for_mode(mode, cls)

    agents_out = []
    sev = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    recs = actions = kpis = 0
    incentives, sources = {}, {}
    for k in keys:
        r = run_agent(k, scenario)
        if r.get("status") != "ok":
            continue
        o = r["output"]
        agents_out.append({
            "agent": k, "name": r["name"], "icon": r["icon"],
            "category": MSME_AGENTS[k].get("category"), "output": o,
        })
        for risk in o.get("risks", []):
            s = risk.get("severity", "Medium")
            sev[s] = sev.get(s, 0) + 1
        recs += len(o.get("recommendations", []))
        actions += len(o.get("action_plan", []))
        kpis += len(o.get("kpis_to_monitor", []))
        for g in o.get("government_incentives", []):
            incentives[g.get("benefit")] = g
        for c in o.get("citations", []):
            sources[c.get("key")] = c

    return {
        "mode": mode,
        "classification": cls,
        "summary": {
            "agents_run": len(agents_out),
            "risks": sev,
            "total_risks": sum(sev.values()),
            "recommendations": recs,
            "action_items": actions,
            "kpis": kpis,
            "government_incentives": list(incentives.values()),
            "compliance_sources": sorted(sources.values(), key=lambda c: (c.get("tier", "Z"), c.get("title", ""))),
        },
        "agents": agents_out,
    }


# ============================================================
# 15. SCENARIO TEST SUITE — golden-answer benchmarks + scoring
# ============================================================
# Each test: a real Indian MSME scenario + golden expectations. Scoring covers:
#   accuracy (expected keywords present), citation quality (>=1 tier-A source),
#   hallucination guard (citations exist for claims), compliance coverage
#   (compliance_impact non-trivial), envelope completeness, ERP-workflow validity
#   (erp_impact references real module keys).
SCENARIO_TESTS = [
    {
        "agent": "gst_compliance",
        "scenario": {"description": "Trader with Rs.8 cr turnover, not on e-invoicing, with ITC mismatches in GSTR-2B"},
        "expect_keywords": ["e-invoic", "itc", "gstr-2b", "reconcil"],
        "expect_citations": ["einvoice", "itc_rules"],
        "expect_severity": "Critical",
    },
    {
        "agent": "gst_compliance",
        "scenario": {"description": "Spice exporter to UAE, Rs.3 cr turnover, unsure about GST on exports"},
        "expect_keywords": ["lut", "zero-rated", "refund"],
        "expect_citations": ["dgft_iec"],
        "expect_severity": None,
    },
    {
        "agent": "cfo_finance",
        "scenario": {"description": "Wholesaler with Rs.10 cr revenue and Rs.2 cr stuck in receivables, facing a cash crunch before GST payment"},
        "expect_keywords": ["dso", "13-week", "receivab", "43b"],
        "expect_citations": ["sec_43b_h", "msmed_act"],
        "expect_severity": "Critical",
    },
    {
        "agent": "msme_due_diligence",
        "scenario": {"description": "Investor evaluating an AI/SaaS startup before a Rs.5 cr cheque; needs red flags and which govt benefits it qualifies for"},
        "expect_keywords": ["ip", "arr", "dpiit", "80-iac", "angel"],
        "expect_citations": ["sec_80iac", "angel_tax", "startup_india"],
        "expect_severity": "Critical",
    },
    {
        "agent": "msme_due_diligence",
        "scenario": {"description": "Lender doing diligence on a manufacturing MSME before a working-capital loan"},
        "expect_keywords": ["roc", "statutory", "gst", "data room"],
        "expect_citations": ["companies_act", "epfo"],
        "expect_severity": None,
    },
    {
        "agent": "erp_consultant",
        "scenario": {"description": "Manufacturer on spreadsheets wants an ERP for BOM, production and GST"},
        "expect_keywords": ["phase", "master data", "parallel", "migrat"],
        "expect_citations": ["gst_portal", "einvoice"],
        "expect_severity": "High",
    },
    {
        "agent": "investor_readiness",
        "scenario": {"description": "AI/SaaS startup founder preparing for a seed raise; needs a clean data room"},
        "expect_keywords": ["data room", "cap table", "dpiit", "arr", "runway"],
        "expect_citations": ["sec_80iac", "angel_tax", "startup_india"],
        "expect_severity": "High",
    },
    {
        "agent": "inventory_agent",
        "scenario": {"description": "Pharma distributor with batch expiry risk and Rs.3 lakh dead stock and stockouts"},
        "expect_keywords": ["fefo", "abc", "reorder", "expiry", "dead"],
        "expect_citations": ["drugs_act", "benchmark_ar"],
        "expect_severity": "Critical",
    },
    {
        "agent": "export_compliance",
        "scenario": {"description": "Spice exporter to UAE unsure about RoDTEP, IEC and export documentation"},
        "expect_keywords": ["iec", "rodtep", "lut", "rcmc", "ebrc"],
        "expect_citations": ["dgft_iec", "apeda"],
        "expect_severity": "High",
    },
    {
        "agent": "export_compliance",
        "scenario": {"description": "Electronics importer filing Bill of Entry at customs, unsure about BIS"},
        "expect_keywords": ["bill of entry", "bis", "igst", "itc"],
        "expect_citations": ["customs", "bis"],
        "expect_severity": "High",
    },
    {
        "agent": "ceo_copilot",
        "scenario": {"description": "Founder of a small D2C brand asks for top 3 priorities this quarter given cash is tight"},
        "expect_keywords": ["priorit", "cadence", "cash", "dashboard"],
        "expect_citations": ["benchmark_ar"],
        "expect_severity": "High",
    },
    {
        "agent": "coo_operations",
        "scenario": {"description": "Distributor order-to-delivery takes 6 days, target 2 days"},
        "expect_keywords": ["bottleneck", "cycle", "handoff", "sop"],
        "expect_citations": ["benchmark_ar"],
        "expect_severity": "High",
    },
    {
        "agent": "risk_audit",
        "scenario": {"description": "Owner wants to know where cash and inventory fraud could happen"},
        "expect_keywords": ["segregation", "maker-checker", "3-way match", "audit log"],
        "expect_citations": ["companies_act"],
        "expect_severity": "High",
    },
    {
        "agent": "sop_agent",
        "scenario": {"description": "Pharma wholesaler needs an SOP for batch-expiry handling"},
        "expect_keywords": ["sop", "version", "fefo", "schedule h"],
        "expect_citations": ["drugs_act"],
        "expect_severity": "High",
    },
    {
        "agent": "hr_payroll",
        "scenario": {"description": "Factory crossing 20 employees must start EPF compliance"},
        "expect_keywords": ["epf", "esi", "tds", "professional tax", "ecr"],
        "expect_citations": ["epfo", "esic", "tds_salary"],
        "expect_severity": "Critical",
    },
    {
        "agent": "market_research",
        "scenario": {"description": "Founder wants TAM for a B2B logistics SaaS in Tier-2 India"},
        "expect_keywords": ["tam", "sam", "som", "bottom-up"],
        "expect_citations": ["ibef", "startup_india"],
        "expect_severity": "High",
    },
    {
        "agent": "competitor_intel",
        "scenario": {"description": "D2C brand losing share wants a competitor pricing teardown"},
        "expect_keywords": ["matrix", "white-space", "win/loss", "positioning"],
        "expect_citations": ["companies_act", "ibef"],
        "expect_severity": "High",
    },
    {
        "agent": "product_manager",
        "scenario": {"description": "SaaS founder needs a prioritized 90-day roadmap and PRD"},
        "expect_keywords": ["prd", "rice", "mvp", "roadmap"],
        "expect_citations": ["benchmark_d2c"],
        "expect_severity": "High",
    },
    {
        "agent": "notion_workspace",
        "scenario": {"description": "Set up a founder, investor and DD workspace from scratch"},
        "expect_keywords": ["database", "dashboard", "access", "sync"],
        "expect_citations": ["meity_ai"],
        "expect_severity": "High",
    },
    {
        "agent": "sales_gtm",
        "scenario": {"description": "Distributor needs a salesman beat plan for 200 outlets"},
        "expect_keywords": ["beat", "outlet", "secondary sales", "coverage"],
        "expect_citations": ["benchmark_ar", "gst_portal"],
        "expect_severity": "High",
    },
    {
        "agent": "procurement_agent",
        "scenario": {"description": "Factory faces raw-material delays and needs a vendor performance view"},
        "expect_keywords": ["otif", "3-way match", "scorecard", "43b"],
        "expect_citations": ["companies_act", "sec_43b_h"],
        "expect_severity": "High",
    },
    {
        "agent": "customer_support",
        "scenario": {"description": "D2C brand drowning in WhatsApp return queries"},
        "expect_keywords": ["sla", "triage", "template", "return"],
        "expect_citations": ["benchmark_d2c", "gst_portal"],
        "expect_severity": "High",
    },
    {
        "agent": "legal_contracts",
        "scenario": {"description": "Founder reviewing a distributor agreement for risky clauses"},
        "expect_keywords": ["indemnity", "termination", "stamp", "ip"],
        "expect_citations": ["contract_act", "stamp_act"],
        "expect_severity": "High",
    },
]


def _gather_text(env: dict) -> str:
    """Flatten an envelope to lowercase text for keyword scoring."""
    import json as _json
    return _json.dumps(env, default=str).lower()


def run_agent_tests() -> dict:
    """Run all scenario tests and produce a deployment-readiness scorecard."""
    results = []
    for i, t in enumerate(SCENARIO_TESTS):
        res = run_agent(t["agent"], t["scenario"])
        env = res.get("output", {})
        text = _gather_text(env)
        cite_keys = [c.get("key") for c in env.get("citations", [])]

        # --- scoring dimensions ---
        kw_hits = [kw for kw in t["expect_keywords"] if kw in text]
        accuracy = round(len(kw_hits) / max(1, len(t["expect_keywords"])), 2)

        cite_hits = [c for c in t["expect_citations"] if c in cite_keys]
        citation_quality = round(len(cite_hits) / max(1, len(t["expect_citations"])), 2)
        has_tier_a = any(c.get("tier") == "A" for c in env.get("citations", []))

        # hallucination guard: any recommendations/risks but zero citations = red flag
        has_claims = bool(env.get("recommendations")) or bool(env.get("risks"))
        hallucination_ok = (not has_claims) or bool(env.get("citations"))

        compliance_ok = len(str(env.get("compliance_impact", ""))) > 40

        # erp_impact must be PRESENT, and every entry must reference a real ERP
        # module. An empty list is valid only for pure research/strategy agents.
        erp_items = env.get("erp_impact", [])
        erp_keys_valid = ("erp_impact" in env) and all(item.get("module") in ERP_MODULES for item in erp_items)

        severity_ok = True
        if t.get("expect_severity"):
            severities = [r.get("severity") for r in env.get("risks", [])]
            severity_ok = t["expect_severity"] in severities

        envelope_ok = res.get("envelope_complete", False)

        checks = {
            "accuracy": accuracy,
            "accuracy_pass": accuracy >= 0.75,
            "citation_quality": citation_quality,
            "citation_pass": citation_quality >= 0.5 and has_tier_a,
            "hallucination_guard_pass": hallucination_ok,
            "compliance_coverage_pass": compliance_ok,
            "erp_workflow_valid": erp_keys_valid,
            "severity_pass": severity_ok,
            "envelope_complete": envelope_ok,
        }
        passed = all([
            checks["accuracy_pass"], checks["citation_pass"], checks["hallucination_guard_pass"],
            checks["compliance_coverage_pass"], checks["erp_workflow_valid"],
            checks["severity_pass"], checks["envelope_complete"],
        ])
        results.append({
            "test": i + 1,
            "agent": t["agent"],
            "scenario": t["scenario"]["description"][:90],
            "passed": passed,
            "missing_keywords": [kw for kw in t["expect_keywords"] if kw not in text],
            "missing_citations": [c for c in t["expect_citations"] if c not in cite_keys],
            "checks": checks,
        })

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    live = [k for k, a in MSME_AGENTS.items() if a.get("status") == "live"]
    return {
        "summary": {
            "total_tests": total,
            "passed": passed,
            "pass_rate": round(passed / max(1, total), 2),
            "deployment_ready": passed == total,
            "live_agents": live,
            "planned_agents": [k for k, a in MSME_AGENTS.items() if a.get("status") != "live"],
        },
        "results": results,
    }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(run_agent_tests()["summary"], indent=2))
