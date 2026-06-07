"""
industry_experts.py — Industry Expert Agents (the master prompt's "Industry Layer").

For each of India's top MSME business types, produce a focused EXPERT BRIEF:
  * Market Size       — indicative India market, CAGR, demand drivers, unit economics
  * Export Solutions  — potential, target markets, applicable export schemes, readiness
  * Regulatory Compliance — sector licences / registrations (resolved to statutes)
  * Financial Compliance  — GST/TDS/ROC/ITR cadence, e-invoicing, Sec 43B(h), sector items
  * Growth Opportunities, Common Risks, Benchmarks — pulled from the sector playbook

Deterministic + reuses: industry_playbooks (profitability/risks/growth/compliance keys),
msme_agents (classify_business, compliance_for, CITATIONS), gov_schemes (export schemes).
Market figures are INDICATIVE — verify with latest IBEF / ministry data.

Endpoints (wired in main.py): GET /experts/meta, GET /experts/tests, POST /experts
"""

try:
    import msme_agents as _M
except Exception:
    _M = None
try:
    import industry_playbooks as _P
except Exception:
    _P = None
try:
    import gov_schemes as _S
except Exception:
    _S = None


# Top India MSME business types. `playbook` maps to an industry_playbooks key.
TOP_TYPES = [
    {"key": "retail_kirana", "name": "Retail / Kirana", "icon": "🛒", "playbook": "retail_chains",
     "market": {"india_size": "Indian retail ≈ ₹75–85 lakh cr; ~13 mn kirana stores carry the bulk of traditional trade",
                "cagr": "~9–10%", "segments": "Grocery, FMCG, general store, modern + quick-commerce",
                "drivers": ["Rising Tier-2/3 consumption", "Quick-commerce & digitisation", "Branded-pack penetration", "UPI-led formalisation"]},
     "export": {"potential": "Low", "markets": [], "note": "Largely domestic; export only via private-label sourcing or e-commerce."}},

    {"key": "wholesale", "name": "Wholesale / B2B Trade", "icon": "📦", "playbook": "wholesale_distribution",
     "market": {"india_size": "B2B wholesale & cash-and-carry is a multi-lakh-crore backbone of Indian trade",
                "cagr": "~8%", "segments": "Staples, FMCG, building materials, apparel, hardware",
                "drivers": ["B2B e-commerce (Udaan/Jio)", "GST-led formalisation", "Credit-on-trade demand", "Tier-2/3 retail expansion"]},
     "export": {"potential": "Low–Medium", "markets": ["Bangladesh", "Nepal", "Sri Lanka", "Middle East"], "note": "Border/neighbour trade for select staples & commodities."}},

    {"key": "distribution", "name": "FMCG Distribution", "icon": "🚚", "playbook": "fmcg_distribution",
     "market": {"india_size": "Indian FMCG ≈ ₹15+ lakh cr; distribution reaches ~10 mn outlets",
                "cagr": "~7–9%", "segments": "Food & beverage, home & personal care, OTC",
                "drivers": ["Rural revival", "Premiumisation", "Direct-distribution & DMS tech", "Quick-commerce fulfilment"]},
     "export": {"potential": "Low", "markets": [], "note": "Domestic distribution; export handled by principals."}},

    {"key": "manufacturing", "name": "Manufacturing (MSME)", "icon": "🏭", "playbook": "manufacturing_msme",
     "market": {"india_size": "MSMEs contribute ~30% of GDP and a large share of manufacturing GVA & employment",
                "cagr": "~8%", "segments": "Engineering goods, components, consumer goods, capital goods",
                "drivers": ["Make-in-India & PLI", "Import substitution", "China+1 sourcing", "Cluster & ZED upgrades"]},
     "export": {"potential": "High", "markets": ["USA", "EU", "Middle East", "Africa", "SE Asia"],
                "note": "Strong via EPCG/Advance Authorisation; engineering goods are a top export basket."}},

    {"key": "food_processing", "name": "Food Processing", "icon": "🍲", "playbook": "agro_trading",
     "market": {"india_size": "Indian food processing is a ~$300+ bn industry — among the world's largest",
                "cagr": "~9–11%", "segments": "Grains/flour, snacks, dairy, spices, ready-to-eat, beverages",
                "drivers": ["PMFME & PLISFPI subsidies", "Packaged-food shift", "Cold-chain build-out", "Export demand for Indian foods"]},
     "export": {"potential": "High", "markets": ["USA", "UAE", "EU", "UK", "Canada", "Australia"],
                "note": "APEDA-backed; FSSAI + importing-country food-safety norms are decisive."}},

    {"key": "agro_business", "name": "Agro Business / Trade", "icon": "🌾", "playbook": "agro_trading",
     "market": {"india_size": "Agriculture & allied ≈ 18% of GDP; agri exports ≈ $50 bn",
                "cagr": "~7%", "segments": "Spices, rice, pulses, grains, fresh produce, commodities",
                "drivers": ["Agri Infrastructure Fund", "FPO formalisation", "Value-add (grading/packing)", "Global demand for Indian spices/rice"]},
     "export": {"potential": "High", "markets": ["Middle East", "EU", "USA", "SE Asia", "Africa"],
                "note": "APEDA/Spices Board registration + phytosanitary & residue compliance critical."}},

    {"key": "pharma", "name": "Pharma / Chemist", "icon": "💊", "playbook": "pharma_retail_distribution",
     "market": {"india_size": "Indian pharma ≈ $50 bn — 3rd largest by volume; world's generics supplier",
                "cagr": "~10–12%", "segments": "Generics, APIs, formulations, retail chemist & distribution",
                "drivers": ["Generics export leadership", "PLI for APIs/bulk drugs", "Health-insurance expansion", "e-pharmacy growth"]},
     "export": {"potential": "Very High", "markets": ["USA", "EU", "Africa", "Latin America", "CIS"],
                "note": "WHO-GMP/USFDA/EU-GMP + Drugs Act licensing are gatekeepers."}},

    {"key": "textile", "name": "Textile & Apparel", "icon": "🧵", "playbook": "textile_businesses",
     "market": {"india_size": "Indian textiles & apparel ≈ $165–175 bn; exports ≈ $35–40 bn",
                "cagr": "~10%", "segments": "Cotton/yarn, fabric, garments, made-ups, technical textiles",
                "drivers": ["PLI & PM MITRA parks", "RoSCTL/ATUFS support", "China+1 apparel shift", "Sustainable/technical textiles"]},
     "export": {"potential": "Very High", "markets": ["USA", "EU", "UK", "UAE", "Bangladesh"],
                "note": "RoSCTL + RoDTEP scrips; buyer compliance (social/eco audits) increasingly required."}},

    {"key": "services", "name": "Professional Services", "icon": "🛠️", "playbook": "professional_services",
     "market": {"india_size": "Services ≈ 53% of GDP; professional & business services growing fast",
                "cagr": "~8%", "segments": "Consulting, IT/ITeS, design, B2B services, agencies",
                "drivers": ["Digital adoption by SMEs", "Global capability/outsourcing", "Specialisation & productisation", "SaaS-enablement"]},
     "export": {"potential": "Medium–High", "markets": ["USA", "UK", "EU", "Middle East", "Australia"],
                "note": "Services exports via LUT (GST), SOFTEX/RBI; strong for IT & knowledge services."}},

    {"key": "logistics", "name": "Logistics & Warehousing", "icon": "📦", "playbook": "logistics_warehousing",
     "market": {"india_size": "Indian logistics ≈ $300+ bn; logistics cost ~13% of GDP, targeted lower",
                "cagr": "~10–12%", "segments": "Transport, warehousing, 3PL, cold-chain, last-mile",
                "drivers": ["PM Gati Shakti & NLP", "E-commerce & quick-commerce", "GST-led hub consolidation", "Cold-chain demand"]},
     "export": {"potential": "Enabler", "markets": [], "note": "Enables others' exports; freight-forwarding & EXIM logistics are key services."}},

    {"key": "export_business", "name": "Export / EXIM House", "icon": "🌏", "playbook": "export_import",
     "market": {"india_size": "India's exports (goods + services) are at record highs (~$770+ bn scale)",
                "cagr": "~varies by basket", "segments": "Merchant & manufacturer exporters across sectors",
                "drivers": ["FTAs (UAE, Australia, EFTA)", "RoDTEP/RoSCTL remissions", "China+1 sourcing", "E-commerce exports"]},
     "export": {"potential": "Core", "markets": ["USA", "UAE", "EU", "UK", "ASEAN", "Africa"],
                "note": "IEC + DGFT schemes (RoDTEP/EPCG/Advance Authorisation) + buyer/country compliance."}},

    {"key": "restaurants", "name": "Restaurants / Cloud Kitchens", "icon": "🍽️", "playbook": "restaurants_cloud_kitchens",
     "market": {"india_size": "Indian food-services ≈ ₹5+ lakh cr; organised + cloud kitchens growing fast",
                "cagr": "~10–15%", "segments": "Dine-in, QSR, cloud kitchens, catering",
                "drivers": ["Online food delivery", "Cloud-kitchen economics", "Premiumisation & cuisines", "Tier-2/3 eating-out growth"]},
     "export": {"potential": "Low", "markets": [], "note": "Domestic; brand franchising abroad is the main cross-border path."}},

    {"key": "d2c", "name": "D2C / E-commerce Brand", "icon": "🛍️", "playbook": "d2c_brands",
     "market": {"india_size": "Indian D2C is estimated to reach ~$60–100 bn within a few years",
                "cagr": "~25–40%", "segments": "Beauty, F&B, fashion, wellness, home",
                "drivers": ["Cheap digital reach", "UPI + logistics rails", "Marketplace + own-site mix", "Cross-border e-commerce"]},
     "export": {"potential": "Medium", "markets": ["USA", "UAE", "UK", "SE Asia"],
                "note": "E-commerce exports via courier/postal + RoDTEP; FSSAI/cosmetic norms per category."}},

    {"key": "electronics", "name": "Electronics / ESDM", "icon": "🔌", "playbook": "electronics_distribution",
     "market": {"india_size": "Indian electronics market ≈ $155 bn, targeted toward ~$300 bn with ESDM push",
                "cagr": "~15%", "segments": "Mobile, components, consumer electronics, distribution",
                "drivers": ["PLI for electronics & components", "Import substitution", "Make-in-India assembly", "Repair/after-sales demand"]},
     "export": {"potential": "Growing", "markets": ["USA", "EU", "Middle East", "Africa"],
                "note": "Mobiles now a top export; BIS + e-waste compliance apply domestically."}},

    {"key": "automotive", "name": "Auto Components / Workshops", "icon": "🔧", "playbook": "automotive_workshops",
     "market": {"india_size": "Auto-components industry ≈ $70+ bn; exports ≈ $20 bn",
                "cagr": "~10%", "segments": "Components, aftermarket, EV parts, service workshops",
                "drivers": ["EV transition & localisation", "China+1 component sourcing", "Aftermarket formalisation", "Export competitiveness"]},
     "export": {"potential": "High", "markets": ["USA", "EU", "ASEAN", "Latin America"],
                "note": "Strong aftermarket exports; IATF/quality certification expected by OEM buyers."}},

    {"key": "construction", "name": "Construction / Infra Supplier", "icon": "🏗️", "playbook": "construction_infra_suppliers",
     "market": {"india_size": "Indian construction ≈ $700+ bn, riding a large public-infra capex cycle",
                "cagr": "~10%", "segments": "Building materials, contractors, infra suppliers, fit-out",
                "drivers": ["Govt infra capex (roads/rail/housing)", "Real-estate revival", "Green building", "Formalisation via GST/RERA"]},
     "export": {"potential": "Low", "markets": [], "note": "Largely domestic; select building-material exports."}},
]

_BY_KEY = {t["key"]: t for t in TOP_TYPES}


def _match(body):
    """Resolve a TOP_TYPES entry from key / business_type / free-text description."""
    body = body or {}
    k = (body.get("key") or body.get("business_type") or "").strip().lower()
    if k in _BY_KEY:
        return _BY_KEY[k]
    desc = (body.get("description") or "").lower()
    # Strong sector keywords first (so a "spice export house" resolves to the
    # agro sector, not the generic EXIM type). export_business is matched last.
    SECTOR_KW = {
        "pharma": ("pharma", "chemist", "medicine", "drug", "formulation"),
        "textile": ("textile", "garment", "apparel", "fabric", "yarn", "knitwear", "saree"),
        "food_processing": ("food process", "snack", "pickle", "bakery", "dairy", "ready to eat", "namkeen", "spice process"),
        "agro_business": ("spice", "agro", "agri", "grain", "pulses", "rice", "commodity", "mandi", "fpo", "horticulture", "cashew"),
        "retail_kirana": ("kirana", "grocery", "retail store", "supermarket", "general store"),
        "wholesale": ("wholesale", "cash and carry", "b2b trade"),
        "distribution": ("fmcg distribution", "distributor", "distribution"),
        "manufacturing": ("manufactur", "factory", "fabrication", "machining", "components", "engineering goods"),
        "pharma_": (),
        "logistics": ("logistic", "warehous", "3pl", "freight", "transport", "courier"),
        "restaurants": ("restaurant", "cloud kitchen", "qsr", "cafe", "catering"),
        "d2c": ("d2c", "direct to consumer", "ecommerce brand", "online brand"),
        "electronics": ("electronic", "esdm", "mobile", "appliance"),
        "automotive": ("auto component", "automotive", "workshop", "garage", "ev part"),
        "construction": ("construction", "infra", "building material", "contractor", "cement", "steel supply"),
        "services": ("consult", "agency", "it service", "saas", "professional service", "design studio"),
    }
    for key, kws in SECTOR_KW.items():
        if key in _BY_KEY and any(k in desc for k in kws):
            return _BY_KEY[key]
    # classifier sector mapping
    if _M and desc:
        cls = _M.classify_business(desc)
        ind = cls.get("industry")
        mapping = {"pharma": "pharma", "textile": "textile", "agro_export": "agro_business",
                   "retail": "retail_kirana", "wholesale": "wholesale", "manufacturing": "manufacturing",
                   "food_bev": "food_processing", "logistics": "logistics", "services": "services",
                   "tech_saas": "services", "construction": "construction"}
        if ind in mapping:
            return _BY_KEY[mapping[ind]]
    # generic EXIM only if explicitly about trading/exim and no sector matched
    if any(k in desc for k in ("exim", "merchant export", "trading house", "export house", "import export")):
        return _BY_KEY["export_business"]
    return _BY_KEY["retail_kirana"]


def _cite(key):
    if _M and key in getattr(_M, "CITATIONS", {}):
        c = _M.CITATIONS[key]
        return {"key": key, "title": c.get("title") or c.get("ref") or key,
                "authority": c.get("authority", ""), "url": c.get("url", ""), "tier": c.get("tier", "")}
    return {"key": key, "title": key.replace("_", " ").title(), "authority": "", "url": "", "tier": ""}


def _export_schemes(t):
    if not _S:
        return []
    try:
        out = _S.recommend_schemes({"description": t["name"], "is_export": True, "sector": t["playbook"]})
        picks = [s for s in out.get("all", []) if s.get("category") == "export"][:5]
        return [{"name": s["name"], "benefit": s["benefit"], "portal": s["portal"]} for s in picks]
    except Exception:
        return []


def expert_brief(body):
    t = _match(body)
    pb = _P.get_playbook(t["playbook"]) if _P else {}

    # Regulatory: playbook compliance keys + classifier compliance, resolved to statutes
    reg_keys = list(pb.get("compliance_keys", []) or [])
    if _M and (body or {}).get("description"):
        try:
            reg_keys += [k for k in _M.compliance_for(_M.classify_business(body["description"])) if k not in reg_keys]
        except Exception:
            pass
    regulatory = [_cite(k) for k in reg_keys][:10]

    # Financial compliance (standard India cadence + sector hooks)
    is_export = (t["export"]["potential"] not in ("Low", "Core", "Enabler")) or bool((body or {}).get("is_export"))
    financial = {
        "gst": "GST registration mandatory above threshold; file GSTR-1 (11th) + GSTR-3B (20th) monthly; reconcile GSTR-2B for full ITC.",
        "e_invoicing": "e-Invoicing applies once turnover crosses the notified threshold (currently ₹5 cr).",
        "tds_tcs": "Deduct/deposit TDS by the 7th; file quarterly TDS returns (24Q/26Q).",
        "msme_payments": "Sec 43B(h): pay MSME suppliers within 45 days or lose the expense deduction that year.",
        "income_tax": "Advance tax in 4 instalments (15 Jun/Sep/Dec, 15 Mar); ITR by 31 Jul (non-audit) / 31 Oct (audit).",
        "roc": "If a Pvt Ltd/LLP: ROC AOC-4 + MGT-7 annual filings; maintain statutory registers.",
        "sector_note": pb.get("profitability_analysis", {}).get("typical_net_margin", "") and
                       f"Watch sector margins — {pb['profitability_analysis'].get('typical_net_margin')}" or
                       "Track sector-typical margins and working-capital cycle.",
    }
    if is_export:
        financial["export_finance"] = "Exports under LUT (zero-rated, no IGST) or with refund; realise proceeds & file as per FEMA/RBI; claim RoDTEP/RoSCTL scrips."

    prof = pb.get("profitability_analysis", {}) or {}
    benchmarks = {
        "gross_margin": prof.get("typical_gross_margin", "—"),
        "net_margin": prof.get("typical_net_margin", "—"),
        "unit_economics": (prof.get("unit_economics") or [])[:4],
    }

    # Growth opportunities + risks from the playbook
    growth = []
    gp = pb.get("growth_playbook", {})
    if isinstance(gp, dict):
        for st in (gp.get("stages") or [])[:4]:
            if isinstance(st, dict):
                growth.append(st.get("focus") or st.get("stage") or st.get("name") or str(st)[:120])
            else:
                growth.append(str(st)[:120])
    risks = []
    rm = pb.get("risk_model", {})
    if isinstance(rm, dict):
        for r in (rm.get("top_risks") or rm.get("risks") or [])[:5]:
            risks.append(r if isinstance(r, str) else (r.get("risk") or r.get("name") or str(r)[:140]))
    elif isinstance(rm, list):
        risks = [str(r)[:140] for r in rm[:5]]

    return {
        "business_type": t["key"],
        "name": t["name"],
        "icon": t["icon"],
        "playbook_key": t["playbook"],
        "one_liner": pb.get("one_liner", ""),
        "market_size": t["market"],
        "export_solutions": {
            "potential": t["export"]["potential"],
            "target_markets": t["export"]["markets"],
            "note": t["export"]["note"],
            "schemes": _export_schemes(t),
        },
        "regulatory_compliance": regulatory,
        "financial_compliance": financial,
        "growth_opportunities": growth,
        "common_risks": risks,
        "benchmarks": benchmarks,
        "playbook_link": f"/playbooks?key={t['playbook']}",
        "disclaimer": "Market figures are indicative (verify with latest IBEF / ministry data). Compliance thresholds change — confirm with a CA/CS.",
    }


def meta():
    return {
        "total_types": len(TOP_TYPES),
        "types": [{"key": t["key"], "name": t["name"], "icon": t["icon"],
                   "export_potential": t["export"]["potential"]} for t in TOP_TYPES],
        "endpoints": ["GET /experts/meta", "GET /experts/tests", "POST /experts"],
    }


def run_experts_tests():
    cases = [
        ({"key": "pharma"}, "pharma"),
        ({"description": "textile garment exporter in Surat"}, "textile"),
        ({"description": "spice export house in Kochi"}, "agro_business"),
        ({"key": "manufacturing"}, "manufacturing"),
        ({"description": "kirana grocery store in Pune"}, "retail_kirana"),
    ]
    passed, results = 0, []
    for body, expect in cases:
        b = expert_brief(body)
        ok = (b["business_type"] == expect
              and bool(b["market_size"].get("india_size"))
              and "potential" in b["export_solutions"]
              and len(b["regulatory_compliance"]) > 0
              and bool(b["financial_compliance"].get("gst")))
        passed += 1 if ok else 0
        results.append({"input": body, "expected": expect, "got": b["business_type"], "ok": ok})
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)}, "results": results}


if __name__ == "__main__":
    import json
    print(json.dumps(run_experts_tests()["summary"], indent=2))
    b = expert_brief({"description": "pharma distribution in Mumbai"})
    print("sample:", b["name"], "| reg:", [r["key"] for r in b["regulatory_compliance"]], "| export schemes:", [s["name"] for s in b["export_solutions"]["schemes"]])
