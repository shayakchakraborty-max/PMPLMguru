"""
gov_schemes.py — Government Schemes module for the AI-Native MSME Consulting OS.

Deterministic, no external deps. A curated registry of real Indian government
schemes for MSMEs / startups / exporters, plus a matcher that returns
personalised recommendations from a business profile (sector, size, trade role,
stage, ownership, geography).

Figures (subsidy %, loan ceilings) are INDICATIVE — schemes change; every card
carries the official portal so the owner can verify current terms. We reuse
msme_agents.classify_business() when available to derive a profile from free text.

Endpoints (wired in main.py):
  GET  /schemes/meta            -> registry stats + filter vocab
  GET  /schemes/tests           -> self-test
  POST /schemes                 -> body {description | sector,size,trade_role,stage,state,...}
                                   -> personalised recommendations
"""

try:
    import msme_agents as _M
except Exception:
    _M = None

# Category buckets for the UI.
CATEGORIES = [
    ("credit", "Credit & Collateral"),
    ("subsidy", "Capital & Subsidy"),
    ("equity", "Equity & Startup"),
    ("tax", "Tax & Incentives"),
    ("export", "Export & Trade"),
    ("quality", "Quality & Tech Upgrade"),
    ("market", "Market & Procurement"),
    ("sector", "Sector-Specific"),
    ("state", "State & Registration"),
]

# ---- The registry. Each scheme: matching `tags` drive recommendations. ----
# tags:
#   sectors: list of msme_agents industry keys this is *especially* for, or "all"
#   sizes:   subset of {micro, small, medium} (omit/"all" = any)
#   trade:   "any" | "export" | "import"
#   stage:   "any" | "startup" | "existing"
#   needs_dpiit / women / sc_st: bool flags that *boost* fit when the profile matches
SCHEMES = [
    # ---------------- CREDIT & COLLATERAL ----------------
    {"key": "cgtmse", "name": "CGTMSE — Collateral-free Credit Guarantee", "category": "credit",
     "authority": "Ministry of MSME / CGTMSE Trust",
     "one_liner": "Collateral-free, third-party-guarantee-free working-capital & term loans.",
     "benefit": "Credit guarantee cover on loans up to ₹5 crore — no collateral, no third-party guarantee.",
     "eligibility": "New & existing micro and small enterprises (manufacturing or service) with Udyam registration, borrowing from a member lending institution.",
     "how_to_apply": "Apply for a business loan at any CGTMSE member bank/NBFC and request CGTMSE cover; the lender files the guarantee.",
     "portal": "https://www.cgtmse.in", "citation": "udyam",
     "tags": {"sectors": "all", "sizes": ["micro", "small"], "trade": "any", "stage": "any"}},

    {"key": "mudra", "name": "PM MUDRA Yojana (Shishu/Kishore/Tarun)", "category": "credit",
     "authority": "MUDRA / Dept. of Financial Services",
     "one_liner": "Micro loans up to ₹10 lakh for non-farm income-generating activities.",
     "benefit": "Loans: Shishu up to ₹50k, Kishore ₹50k–₹5L, Tarun ₹5L–₹10L. Collateral-free.",
     "eligibility": "Non-corporate, non-farm micro/small enterprises — manufacturing, trading, services, allied agri.",
     "how_to_apply": "Apply at any bank/NBFC/MFI or via the Jan Samarth / Udyamimitra portal.",
     "portal": "https://www.mudra.org.in", "citation": "udyam",
     "tags": {"sectors": "all", "sizes": ["micro"], "trade": "any", "stage": "any"}},

    {"key": "standup_india", "name": "Stand-Up India", "category": "credit",
     "authority": "Dept. of Financial Services",
     "one_liner": "Greenfield loans ₹10L–₹1cr for SC/ST and women entrepreneurs.",
     "benefit": "Bank loan ₹10 lakh–₹1 crore for a greenfield enterprise (manufacturing, services, trading, agri-allied).",
     "eligibility": "SC/ST and/or women entrepreneurs, ≥51% ownership, first-time greenfield venture.",
     "how_to_apply": "Apply on the Stand-Up India portal or at the bank branch.",
     "portal": "https://www.standupmitra.in", "citation": "udyam",
     "tags": {"sectors": "all", "sizes": "all", "trade": "any", "stage": "startup", "women": True, "sc_st": True}},

    # ---------------- CAPITAL & SUBSIDY ----------------
    {"key": "pmegp", "name": "PMEGP — Credit-Linked Subsidy", "category": "subsidy",
     "authority": "KVIC / Ministry of MSME",
     "one_liner": "Margin-money subsidy for new micro manufacturing/service units.",
     "benefit": "Subsidy 15–35% of project cost (higher for special categories/rural). Project up to ₹50L (mfg) / ₹20L (service).",
     "eligibility": "New micro enterprises (not existing units), individuals 18+, SHGs, societies; income ceiling does not apply but unit must be new.",
     "how_to_apply": "Apply on the PMEGP e-portal (KVIC).",
     "portal": "https://www.kviconline.gov.in/pmegpeportal", "citation": "udyam",
     "tags": {"sectors": ["manufacturing", "food_bev", "textile", "services"], "sizes": ["micro"], "trade": "any", "stage": "startup"}},

    {"key": "clcss", "name": "CLCSS — Credit Linked Capital Subsidy", "category": "subsidy",
     "authority": "Ministry of MSME",
     "one_liner": "15% capital subsidy for technology / plant & machinery upgradation.",
     "benefit": "15% capital subsidy (up to ₹15 lakh) on institutional finance for upgrading to approved technology.",
     "eligibility": "Existing micro & small manufacturing units upgrading plant & machinery to approved sub-sector technologies.",
     "how_to_apply": "Through the primary lending institution to the nodal agency.",
     "portal": "https://clcss.dcmsme.gov.in", "citation": "udyam",
     "tags": {"sectors": ["manufacturing", "textile", "food_bev", "pharma"], "sizes": ["micro", "small"], "trade": "any", "stage": "existing"}},

    # ---------------- EQUITY & STARTUP ----------------
    {"key": "sisfs", "name": "Startup India Seed Fund Scheme (SISFS)", "category": "equity",
     "authority": "DPIIT",
     "one_liner": "Seed capital up to ₹50 lakh for early-stage DPIIT startups.",
     "benefit": "Up to ₹20L grant (validation/PoC) + up to ₹50L (market entry/scale) via approved incubators.",
     "eligibility": "DPIIT-recognised startup, incorporated ≤2 years, not received >₹10L other govt funding.",
     "how_to_apply": "Apply via the Startup India Seed Fund portal to a participating incubator.",
     "portal": "https://seedfund.startupindia.gov.in", "citation": "sisfs" if False else "startup_india",
     "tags": {"sectors": ["tech_saas"], "sizes": "all", "trade": "any", "stage": "startup", "needs_dpiit": True}},

    {"key": "ffs", "name": "Fund of Funds for Startups (FFS)", "category": "equity",
     "authority": "SIDBI / DPIIT",
     "one_liner": "Indirect equity capital via SEBI-registered Alternative Investment Funds.",
     "benefit": "Capital infusion into SEBI-registered AIFs that invest in startups (no direct govt equity).",
     "eligibility": "DPIIT-recognised startups raising from FFS-backed AIFs.",
     "how_to_apply": "Raise from a SIDBI/FFS-backed VC fund; not a direct application.",
     "portal": "https://www.startupindia.gov.in", "citation": "startup_india",
     "tags": {"sectors": ["tech_saas"], "sizes": "all", "trade": "any", "stage": "startup", "needs_dpiit": True}},

    # ---------------- TAX & INCENTIVES ----------------
    {"key": "sec_80iac", "name": "80-IAC — 3-Year Income-Tax Holiday", "category": "tax",
     "authority": "CBDT / DPIIT",
     "one_liner": "100% tax deduction on profits for 3 of the first 10 years.",
     "benefit": "100% deduction of profits for any 3 consecutive years within the first 10 years of incorporation.",
     "eligibility": "DPIIT-recognised startup, incorporated within the eligible window, turnover ≤ ₹100 cr in the relevant FY, working on innovation/scalability.",
     "how_to_apply": "Apply for 80-IAC certification on the Startup India portal (Inter-Ministerial Board).",
     "portal": "https://www.startupindia.gov.in", "citation": "startup_india",
     "tags": {"sectors": ["tech_saas"], "sizes": "all", "trade": "any", "stage": "startup", "needs_dpiit": True}},

    {"key": "angel_tax", "name": "Angel Tax Exemption (Sec 56(2)(viib))", "category": "tax",
     "authority": "CBDT / DPIIT",
     "one_liner": "Exemption from tax on share premium above fair value for recognised startups.",
     "benefit": "Eligible DPIIT startups are exempt from angel tax on investments above fair market value.",
     "eligibility": "DPIIT-recognised, aggregate paid-up capital & share premium within prescribed limit, eligible investor.",
     "how_to_apply": "Self-declare via Form-2 on the Startup India portal after DPIIT recognition.",
     "portal": "https://www.startupindia.gov.in", "citation": "startup_india",
     "tags": {"sectors": ["tech_saas"], "sizes": "all", "trade": "any", "stage": "startup", "needs_dpiit": True}},

    # ---------------- EXPORT & TRADE ----------------
    {"key": "rodtep", "name": "RoDTEP — Remission of Duties & Taxes on Exports", "category": "export",
     "authority": "DGFT / Dept. of Commerce",
     "one_liner": "Refund of embedded central, state & local duties on exported products.",
     "benefit": "Transferable duty-credit scrips at notified % of FOB value, credited to the exporter's ledger.",
     "eligibility": "Exporters of notified products (including MSME); claimed at the shipping-bill stage.",
     "how_to_apply": "Claim in the shipping bill; scrips issued in the ICEGATE ledger.",
     "portal": "https://www.dgft.gov.in", "citation": "customs",
     "tags": {"sectors": "all", "sizes": "all", "trade": "export", "stage": "any"}},

    {"key": "ies", "name": "Interest Equalisation Scheme (Export Credit)", "category": "export",
     "authority": "RBI / DGFT",
     "one_liner": "Interest subvention on pre- & post-shipment rupee export credit.",
     "benefit": "Interest equalisation (notified %, higher for MSME manufacturer exporters) on export credit.",
     "eligibility": "MSME manufacturer exporters and exporters of notified tariff lines (subject to current notification).",
     "how_to_apply": "Availed automatically through your export-credit bank.",
     "portal": "https://www.dgft.gov.in", "citation": "customs",
     "tags": {"sectors": "all", "sizes": "all", "trade": "export", "stage": "any"}},

    {"key": "mai", "name": "Market Access Initiative (MAI)", "category": "export",
     "authority": "Dept. of Commerce",
     "one_liner": "Financial support for export promotion — trade fairs, buyer-seller meets, market studies.",
     "benefit": "Reimbursement support for participation in international fairs, market studies and export promotion.",
     "eligibility": "Exporters via EPCs / trade bodies; eligible export-promotion activities.",
     "how_to_apply": "Through your Export Promotion Council / APEDA / FIEO.",
     "portal": "https://www.commerce.gov.in", "citation": "fieo",
     "tags": {"sectors": "all", "sizes": "all", "trade": "export", "stage": "any"}},

    {"key": "epcg", "name": "EPCG — Export Promotion Capital Goods", "category": "export",
     "authority": "DGFT",
     "one_liner": "Import capital goods at zero customs duty against an export obligation.",
     "benefit": "Zero-duty import of capital goods; export obligation of 6× duty saved over 6 years.",
     "eligibility": "Manufacturer exporters & merchant exporters tied to a supporting manufacturer.",
     "how_to_apply": "Apply for an EPCG authorisation on the DGFT portal.",
     "portal": "https://www.dgft.gov.in", "citation": "customs",
     "tags": {"sectors": ["manufacturing", "textile", "pharma", "food_bev"], "sizes": "all", "trade": "export", "stage": "any"}},

    # ---------------- QUALITY & TECH UPGRADE ----------------
    {"key": "zed", "name": "MSME Sustainable (ZED) Certification", "category": "quality",
     "authority": "Ministry of MSME / QCI",
     "one_liner": "Zero Defect Zero Effect certification with subsidised cost & benefits.",
     "benefit": "Subsidy on certification cost (higher for micro/women/SC-ST/NER), plus handholding & incentives.",
     "eligibility": "Udyam-registered manufacturing MSMEs.",
     "how_to_apply": "Register on the ZED portal and pursue Bronze/Silver/Gold certification.",
     "portal": "https://zed.msme.gov.in", "citation": "udyam",
     "tags": {"sectors": ["manufacturing", "textile", "food_bev", "pharma"], "sizes": "all", "trade": "any", "stage": "existing"}},

    {"key": "lean", "name": "Lean Manufacturing Competitiveness Scheme", "category": "quality",
     "authority": "Ministry of MSME",
     "one_liner": "Subsidised lean consultants to cut waste and raise productivity.",
     "benefit": "Govt funds a large share of lean-consultant cost for implementing 5S, Kaizen, TPM, VSM etc.",
     "eligibility": "Udyam-registered manufacturing MSMEs (often in clusters).",
     "how_to_apply": "Via the MSME Champions / DC-MSME implementation framework.",
     "portal": "https://champions.gov.in", "citation": "udyam",
     "tags": {"sectors": ["manufacturing", "textile", "food_bev"], "sizes": ["micro", "small"], "trade": "any", "stage": "existing"}},

    # ---------------- MARKET & PROCUREMENT ----------------
    {"key": "gem", "name": "GeM — Government e-Marketplace Access", "category": "market",
     "authority": "GeM / Ministry of Commerce",
     "one_liner": "Sell directly to government buyers; MSEs get procurement preference.",
     "benefit": "Access to public procurement; 25% MSE procurement mandate, EMD/tender-fee relaxations for MSEs.",
     "eligibility": "Any registered business; MSE benefits need Udyam.",
     "how_to_apply": "Register as a seller on GeM with Udyam + GST.",
     "portal": "https://gem.gov.in", "citation": "udyam",
     "tags": {"sectors": "all", "sizes": "all", "trade": "any", "stage": "any"}},

    {"key": "treds", "name": "TReDS — Receivables Discounting", "category": "market",
     "authority": "RBI-licensed TReDS platforms",
     "one_liner": "Discount your verified receivables for fast, collateral-free working capital.",
     "benefit": "Auction-based early payment of invoices to corporates/PSUs at competitive rates.",
     "eligibility": "MSME suppliers with Udyam; buyer onboarded on a TReDS platform.",
     "how_to_apply": "Onboard on RXIL / M1xchange / Invoicemart.",
     "portal": "https://www.rxil.in", "citation": "msme_payment" if False else "udyam",
     "tags": {"sectors": "all", "sizes": "all", "trade": "any", "stage": "existing"}},

    {"key": "pms", "name": "Procurement & Marketing Support (PMS)", "category": "market",
     "authority": "Ministry of MSME",
     "one_liner": "Support for participating in exhibitions, GeM onboarding and marketing.",
     "benefit": "Reimbursement support for trade fairs, vendor development, GeM adoption, packaging & branding.",
     "eligibility": "Udyam-registered MSMEs.",
     "how_to_apply": "Through DC-MSME / MSME-DI offices.",
     "portal": "https://dcmsme.gov.in", "citation": "udyam",
     "tags": {"sectors": "all", "sizes": "all", "trade": "any", "stage": "any"}},

    # ---------------- SECTOR-SPECIFIC ----------------
    {"key": "pmfme", "name": "PMFME — Micro Food Processing Enterprises", "category": "sector",
     "authority": "Ministry of Food Processing Industries",
     "one_liner": "35% credit-linked subsidy for micro food-processing units.",
     "benefit": "35% subsidy (up to ₹10L) on eligible project cost + seed capital for SHGs + branding/marketing support.",
     "eligibility": "Individual/Group micro food-processing enterprises, FPOs, SHGs, cooperatives.",
     "how_to_apply": "Apply on the PMFME portal with a DPR.",
     "portal": "https://pmfme.mofpi.gov.in", "citation": "fssai",
     "tags": {"sectors": ["food_bev"], "sizes": ["micro", "small"], "trade": "any", "stage": "any"}},

    {"key": "atufs", "name": "ATUFS — Amended Technology Upgradation Fund (Textiles)", "category": "sector",
     "authority": "Ministry of Textiles",
     "one_liner": "Capital subsidy for technology upgradation in textiles & apparel.",
     "benefit": "Credit-linked capital investment subsidy on eligible textile machinery.",
     "eligibility": "Textile units (garmenting, technical textiles, processing, etc.) investing in benchmarked machinery.",
     "how_to_apply": "Through the iTUFS portal via the lending bank.",
     "portal": "https://ifms.texmin.nic.in", "citation": "udyam",
     "tags": {"sectors": ["textile"], "sizes": "all", "trade": "any", "stage": "existing"}},

    {"key": "rosctl", "name": "RoSCTL — Rebate of State & Central Taxes (Apparel)", "category": "sector",
     "authority": "Ministry of Textiles / DGFT",
     "one_liner": "Duty-credit scrips rebating embedded taxes on apparel & made-up exports.",
     "benefit": "Transferable scrips at notified rates on exports of garments and made-ups.",
     "eligibility": "Exporters of apparel/garments and made-up articles.",
     "how_to_apply": "Claimed via shipping bill on ICEGATE.",
     "portal": "https://www.dgft.gov.in", "citation": "customs",
     "tags": {"sectors": ["textile"], "sizes": "all", "trade": "export", "stage": "any"}},

    {"key": "aif", "name": "Agriculture Infrastructure Fund (AIF)", "category": "sector",
     "authority": "Ministry of Agriculture",
     "one_liner": "Interest subvention + guarantee for post-harvest & agri-infra projects.",
     "benefit": "3% interest subvention on loans up to ₹2 cr + CGTMSE-style guarantee for post-harvest infra.",
     "eligibility": "FPOs, agri-entrepreneurs, startups, traders building warehouses, cold-chain, grading/packing infra.",
     "how_to_apply": "Apply on the AIF portal via a lending bank.",
     "portal": "https://agriinfra.dac.gov.in", "citation": "apeda" if False else "udyam",
     "tags": {"sectors": ["agro_export"], "sizes": "all", "trade": "any", "stage": "any"}},

    {"key": "apeda_fa", "name": "APEDA Financial Assistance (Agri Exports)", "category": "sector",
     "authority": "APEDA / Ministry of Commerce",
     "one_liner": "Support for infrastructure, quality and market development for agri exports.",
     "benefit": "Assistance for packhouse/cold-chain, quality certification, and export market development.",
     "eligibility": "APEDA-registered exporters of scheduled agri & processed products.",
     "how_to_apply": "Register with APEDA and apply for the relevant component.",
     "portal": "https://apeda.gov.in", "citation": "apeda",
     "tags": {"sectors": ["agro_export", "food_bev"], "sizes": "all", "trade": "export", "stage": "any"}},

    # ---------------- STATE & REGISTRATION ----------------
    {"key": "udyam", "name": "Udyam Registration (Gateway)", "category": "state",
     "authority": "Ministry of MSME",
     "one_liner": "Free MSME registration — the key that unlocks almost every scheme above.",
     "benefit": "Priority-sector lending, CGTMSE/subsidy eligibility, 45-day delayed-payment protection (MSMED Act / Sec 43B(h)), tender benefits.",
     "eligibility": "Any enterprise within MSME investment & turnover limits.",
     "how_to_apply": "Register free on the Udyam portal with PAN + Aadhaar.",
     "portal": "https://udyamregistration.gov.in", "citation": "udyam",
     "tags": {"sectors": "all", "sizes": "all", "trade": "any", "stage": "any"}},

    {"key": "state_psi", "name": "State MSME / Industrial Promotion Subsidy", "category": "state",
     "authority": "Respective State Industries Dept.",
     "one_liner": "State-level capital, SGST, power, stamp-duty & interest subsidies.",
     "benefit": "Varies by state — capital subsidy, SGST reimbursement, electricity-duty & stamp-duty exemption, interest subsidy (e.g. Maharashtra PSI, Gujarat, TN, UP, Karnataka schemes).",
     "eligibility": "Units set up in the state per its current industrial policy & zone classification.",
     "how_to_apply": "Apply on your State Single-Window / Industries portal.",
     "portal": "https://www.indiainvestmentgrid.gov.in", "citation": "udyam",
     "tags": {"sectors": "all", "sizes": "all", "trade": "any", "stage": "any"}},

    {"key": "iec", "name": "IEC — Importer Exporter Code", "category": "state",
     "authority": "DGFT",
     "one_liner": "The mandatory code to legally import or export from India.",
     "benefit": "Enables imports/exports, customs clearance, forex receipts and access to all export schemes.",
     "eligibility": "Any person/entity intending to import or export.",
     "how_to_apply": "Apply free/low-cost on the DGFT portal with PAN.",
     "portal": "https://www.dgft.gov.in", "citation": "customs",
     "tags": {"sectors": "all", "sizes": "all", "trade": "export", "stage": "any"}},
]

_CAT_LABEL = dict(CATEGORIES)
_VALID_CITATIONS = set()
if _M is not None:
    _VALID_CITATIONS = set(getattr(_M, "CITATIONS", {}).keys())


# Keyword overrides — the shared classifier is coarse (lumps food/textile/etc.
# into "manufacturing"); refine to the sector keys our schemes target.
_SECTOR_KW = [
    ("food_bev", ("food process", "pickle", "snack", "bakery", "dairy", "spice", "masala", "beverage", "ready to eat", "fmcg food", "namkeen", "sweets", "confection")),
    ("textile", ("textile", "garment", "apparel", "fabric", "yarn", "weaving", "knitwear", "readymade", "saree", "handloom", "powerloom")),
    ("pharma", ("pharma", "drug", "medicine", "formulation", "api ", "nutraceutical")),
    ("agro_export", ("agro", "agri", "grain", "pulses", "rice mill", "mandi", "fpo", "commodity trad", "horticulture", "cashew", "tea ", "coffee bean")),
    ("retail", ("kirana", "grocery", "retail store", "retail chain", "supermarket", "general store")),
    ("wholesale", ("wholesale", "distributor", "distribution", "c&f", "stockist")),
]


def _refine_sector(desc, base):
    d = (desc or "").lower()
    for sec, kws in _SECTOR_KW:
        if any(k in d for k in kws):
            return sec
    return base


def _profile_from(body):
    """Build a normalised profile from explicit fields, falling back to
    classify_business() on the free-text description."""
    body = body or {}
    desc = (body.get("description") or body.get("idea") or "").strip()
    cls = _M.classify_business(desc) if (_M and desc) else {}
    sector = (body.get("sector") or body.get("business_type") or "").strip()
    if not sector:
        sector = _refine_sector(desc, cls.get("industry") or "services")
    size = (body.get("size") or cls.get("size") or "small").strip().lower()
    if size not in ("micro", "small", "medium"):
        size = "small"
    trade = (body.get("trade_role") or cls.get("trade_role") or "domestic").strip().lower()
    is_export = bool(body.get("is_export")) or cls.get("is_export") or "export" in trade
    is_import = bool(body.get("is_import")) or cls.get("is_import") or trade == "import"
    # The shared classifier over-tags traditional MSMEs as "startup"; only treat
    # as startup when explicitly stated, DPIIT-recognised, or genuinely tech.
    explicit_stage = (body.get("stage") or "").strip().lower()
    _tech_kw = ("saas", "software", "app ", "platform", "ai startup", "tech startup", "deep tech", "marketplace app")
    if explicit_stage in ("startup", "existing"):
        stage = explicit_stage
    elif body.get("is_dpiit") or sector == "tech_saas" or cls.get("is_ai") or any(k in desc.lower() for k in _tech_kw):
        stage = "startup"
    else:
        stage = "existing"
    return {
        "description": desc,
        "sector": sector,
        "size": size,
        "trade_role": "export" if is_export else ("import" if is_import else "domestic"),
        "is_export": bool(is_export),
        "is_import": bool(is_import),
        "stage": stage,
        "state": (body.get("state") or "").strip(),
        "is_dpiit": bool(body.get("is_dpiit")),
        "women_owned": bool(body.get("women_owned")),
        "sc_st_owned": bool(body.get("sc_st_owned")),
    }


def _score(scheme, p):
    """Relevance score + human reasons for why this scheme fits the profile."""
    t = scheme["tags"]
    score, reasons = 0, []

    # Sector
    secs = t.get("sectors", "all")
    if secs == "all":
        score += 1
    elif p["sector"] in secs:
        score += 5
        reasons.append(f"Built for {p['sector'].replace('_', ' ')} businesses")
    else:
        # sector-specific scheme but sector doesn't match -> heavy penalty
        if scheme["category"] in ("sector",):
            return (-1, [])
        score += 0

    # Size
    sizes = t.get("sizes", "all")
    if sizes != "all":
        if p["size"] in sizes:
            score += 3
            reasons.append(f"Targets {p['size']} enterprises")
        else:
            score -= 2

    # Trade
    trade = t.get("trade", "any")
    if trade == "export":
        if p["is_export"]:
            score += 5
            reasons.append("You export — this is an export scheme")
        else:
            return (-1, [])  # export scheme, non-exporter: drop
    elif trade == "import":
        if p["is_import"]:
            score += 4
            reasons.append("You import — relevant to trade")
        else:
            return (-1, [])

    # Stage
    stage = t.get("stage", "any")
    if stage != "any":
        if stage == p["stage"]:
            score += 3
            reasons.append("Startup-stage benefit" if stage == "startup" else "For established units")
        else:
            score -= 3

    # DPIIT requirement
    if t.get("needs_dpiit"):
        if p["is_dpiit"]:
            score += 4
            reasons.append("You're DPIIT-recognised — directly eligible")
        else:
            score += 1
            reasons.append("Requires DPIIT recognition (get it first — it's free)")

    # Ownership boosts
    if t.get("women") and p["women_owned"]:
        score += 4; reasons.append("Women-entrepreneur priority")
    if t.get("sc_st") and p["sc_st_owned"]:
        score += 4; reasons.append("SC/ST-entrepreneur priority")

    # Gateway schemes are universally useful
    if scheme["key"] in ("udyam", "cgtmse"):
        score += 2

    return (score, reasons)


def recommend_schemes(body):
    """Main entry: profile/free-text -> ranked, personalised scheme recommendations."""
    p = _profile_from(body)
    scored = []
    for s in SCHEMES:
        sc, reasons = _score(s, p)
        if sc < 0:
            continue
        fit = "High" if sc >= 7 else ("Medium" if sc >= 3 else "Explore")
        if not reasons:
            reasons = ["Generally available to MSMEs like yours"]
        item = {k: s[k] for k in ("key", "name", "category", "authority", "one_liner",
                                  "benefit", "eligibility", "how_to_apply", "portal", "citation")}
        item["category_label"] = _CAT_LABEL.get(s["category"], s["category"])
        item["fit"] = fit
        item["_score"] = sc
        item["fit_reasons"] = reasons[:3]
        scored.append(item)

    scored.sort(key=lambda x: (-x["_score"], x["name"]))

    # group by category preserving the CATEGORIES order
    by_cat = []
    for ckey, clabel in CATEGORIES:
        items = [s for s in scored if s["category"] == ckey]
        if items:
            by_cat.append({"key": ckey, "label": clabel, "schemes": items})

    high = [s for s in scored if s["fit"] == "High"]
    return {
        "profile": p,
        "total": len(scored),
        "high_fit_count": len(high),
        "top_picks": scored[:6],
        "by_category": by_cat,
        "all": scored,
        "disclaimer": "Scheme terms, ceilings and percentages are indicative and change — verify current eligibility and benefits on the official portal before applying.",
    }


def meta():
    return {
        "total_schemes": len(SCHEMES),
        "categories": [{"key": k, "label": v, "count": sum(1 for s in SCHEMES if s["category"] == k)} for k, v in CATEGORIES],
        "sizes": ["micro", "small", "medium"],
        "stages": ["startup", "existing"],
        "trade_roles": ["domestic", "export", "import"],
        "endpoints": ["GET /schemes/meta", "GET /schemes/tests", "POST /schemes"],
    }


def run_schemes_tests():
    """Self-test: a few profiles should surface the right anchor schemes."""
    cases = [
        ({"description": "kirana retail store in Pune", "size": "micro"}, "cgtmse"),
        ({"description": "DPIIT AI SaaS startup in Bengaluru", "is_dpiit": True}, "sec_80iac"),
        ({"description": "spice export house shipping to UAE", "is_export": True}, "rodtep"),
        ({"description": "micro food processing unit making pickles", "size": "micro"}, "pmfme"),
        ({"description": "textile garment manufacturer in Surat", "is_export": True}, "rosctl"),
    ]
    results = []
    passed = 0
    for body, expect in cases:
        out = recommend_schemes(body)
        keys = [s["key"] for s in out["all"]]
        ok = expect in keys
        # also: registration gateway should always appear
        gate_ok = "udyam" in keys
        ok = ok and gate_ok and out["total"] > 0
        passed += 1 if ok else 0
        results.append({"profile": body.get("description"), "expected": expect, "found": ok, "total": out["total"]})
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)}, "results": results}


if __name__ == "__main__":
    import json
    print(json.dumps(run_schemes_tests()["summary"], indent=2))
    demo = recommend_schemes({"description": "DPIIT AI SaaS startup in Bengaluru that also exports services", "is_dpiit": True})
    print("top picks:", [s["key"] for s in demo["top_picks"]])
