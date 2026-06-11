"""
situations.py — a library of realistic Indian-MSME engagement situations.

Each situation is a one-click demo for the orchestrator: a real-sounding problem
across a sector x service-line, with an ERP-style intake pre-filled. Used to power
the landing-page demo gallery so visitors can run stunning sample engagements.

Deterministic, no deps. Endpoint (main.py): GET /situations (+ /situations/meta).
"""


def _s(id, title, icon, sector, lens, description, intake):
    return {"id": id, "title": title, "icon": icon, "sector": sector, "lens": lens,
            "description": description, "intake": intake}


SITUATIONS = [
    _s("kirana_cash", "Kirana chain: stockouts + cash crunch", "🛒", "Retail", "Working Capital",
       "8-store kirana grocery retail chain in Pune, GST registered, 22 staff, with frequent stockouts on fast-movers, thin margins and a cash crunch before the GST payment.",
       {"company": "Pune Kirana Chain", "turnover_cr": 12, "headcount": 22, "city_tier": "Tier-2", "top_challenges": "stockouts, thin margins, dead stock, cash crunch"}),
    _s("wholesale_receivables", "FMCG wholesaler: receivables choking cash", "📦", "Wholesale", "O2C",
       "FMCG wholesale distributor in Nagpur supplying 600+ retailers, Rs.34 cr turnover, with a 68-day DSO, stretched receivables, trade-promotion deductions and unapplied cash.",
       {"company": "Nagpur FMCG Distribution", "turnover_cr": 34, "headcount": 40, "city_tier": "Tier-2", "dso_days": 68, "top_challenges": "stretched receivables, deductions, thin spreads"}),
    _s("auto_parts_margin", "Auto-parts factory: margin & delivery", "🏭", "Manufacturing", "Operations",
       "Auto-parts manufacturing factory near Pune, Rs.45 cr turnover, 120 staff, with order-to-delivery taking 9 days, rework on the line, raw-material price volatility and squeezed margins.",
       {"company": "Pune Auto Components", "turnover_cr": 45, "headcount": 120, "city_tier": "Tier-2", "top_challenges": "long lead time, rework, RM price volatility, margin squeeze"}),
    _s("textile_export_cbam", "Textile exporter: EU buyers + ESG", "🧵", "Textile / Export", "ESG",
       "Cotton garment manufacturer-exporter in Surat shipping to the EU, Rs.60 cr turnover, where buyers now demand embedded-carbon (CBAM) data and a decarbonisation plan, amid yarn price volatility.",
       {"company": "Surat Garments Exports", "turnover_cr": 60, "headcount": 300, "city_tier": "Tier-2", "is_export": True, "top_challenges": "CBAM/ESG buyer demands, yarn price volatility, EU compliance"}),
    _s("pharma_distrib_compliance", "Pharma distributor: expiry + compliance", "💊", "Pharma", "Risk & Compliance",
       "Pharma distributor with batch-expiry risk, Schedule-H controls, Rs.3 lakh dead stock, frequent stockouts and worry about drug-licence and GST compliance.",
       {"company": "MediDistribuCo", "turnover_cr": 28, "headcount": 35, "city_tier": "Tier-2", "dead_stock_value": 3, "top_challenges": "batch expiry, schedule-H compliance, stockouts"}),
    _s("d2c_cac", "D2C brand: CAC above LTV", "🛍️", "Retail / D2C", "Marketing",
       "D2C skincare brand selling on its own site + marketplaces, Rs.8 cr GMV, burning on ads with CAC above LTV, weak repeat purchase and shrinking contribution margin.",
       {"company": "GlowD2C", "turnover_cr": 8, "headcount": 18, "city_tier": "Tier-1", "is_tech": True, "top_challenges": "CAC above LTV, low repeat rate, ad burn"}),
    _s("saas_seed", "AI SaaS: seed raise readiness", "🤖", "Technology", "Deals & DD",
       "AI/SaaS startup, Rs.4 cr ARR, preparing for a seed raise, needs a clean data room, defensible metrics, DPDP/data-protection posture and to verify 80-IAC/angel-tax benefits.",
       {"company": "AIStack", "turnover_cr": 4, "headcount": 25, "city_tier": "Tier-1", "is_tech": True, "is_startup": True, "top_challenges": "fundraise readiness, data room, DPDP, metrics quality"}),
    _s("logistics_ops", "Logistics: utilisation & cost", "🚚", "Logistics", "Supply Chain",
       "Regional transport & freight-forwarding firm, Rs.30 cr turnover, 80 vehicles, with low fleet utilisation, rising fuel cost, detention charges and thin operating margins.",
       {"company": "FastFreight Logistics", "turnover_cr": 30, "headcount": 150, "city_tier": "Tier-2", "top_challenges": "low utilisation, fuel cost, detention, thin margins"}),
    _s("restaurant_chain", "Cloud-kitchen chain: unit economics", "🍔", "Food & Beverage", "Strategy",
       "Cloud-kitchen + bakery chain across 6 outlets in Bengaluru, Rs.14 cr turnover, with aggregator commissions eating margin, food cost creep and inconsistent SOPs across kitchens.",
       {"company": "CloudBite Kitchens", "turnover_cr": 14, "headcount": 70, "city_tier": "Tier-1", "top_challenges": "aggregator commissions, food cost, SOP consistency"}),
    _s("construction_wc", "Civil contractor: working capital", "🏗️", "Construction", "Finance",
       "Civil contractor under RERA executing 4 projects, Rs.50 cr turnover, with cash locked in retention money + WIP, delayed client payments and bonus/penalty exposure on timelines.",
       {"company": "BuildRight Infra", "turnover_cr": 50, "headcount": 90, "city_tier": "Tier-2", "top_challenges": "retention money, WIP, delayed payments, project delays"}),
    _s("clinic_ops", "Diagnostic lab + clinic: throughput", "🏥", "Healthcare", "Operations",
       "Diagnostic lab + multi-speciality clinic, Rs.18 cr turnover, with patient wait times, low equipment utilisation, NABH gaps and receivables stuck with TPAs/insurers.",
       {"company": "CarePlus Diagnostics", "turnover_cr": 18, "headcount": 60, "city_tier": "Tier-2", "top_challenges": "patient wait time, utilisation, NABH, TPA receivables"}),
    _s("founder_scaling", "Founder-led firm: scale past the owner", "🧩", "Manufacturing", "People & Org",
       "Founder-led engineering firm at 60 staff where every decision routes through the owner; needs a target operating model, clear roles (RACI), an OKR cadence and to reduce key-person risk.",
       {"company": "FounderEng", "turnover_cr": 22, "headcount": 60, "city_tier": "Tier-2", "top_challenges": "founder bottleneck, role clarity, no OKRs, key-person risk"}),
    _s("electronics_import", "Electronics importer: customs + BIS", "📱", "Import / Trade", "Tax & Compliance",
       "Electronics & mobile-accessories importer filing Bills of Entry, Rs.40 cr turnover, unsure on BIS certification, customs valuation, IGST credit and FX exposure.",
       {"company": "GadgetImport Co", "turnover_cr": 40, "headcount": 30, "city_tier": "Tier-1", "is_import": True, "top_challenges": "BIS, customs valuation, IGST credit, FX risk"}),
    _s("agro_export", "Spice exporter: market access", "🌶️", "Agro / Export", "Growth",
       "Spice & makhana exporter, Rs.20 cr turnover, APEDA & IEC registered, wanting to grow EU/US market access, improve realisation and de-risk RoDTEP/forex.",
       {"company": "SpiceRoots Exports", "turnover_cr": 20, "headcount": 45, "city_tier": "Tier-3", "is_export": True, "top_challenges": "market access, realisation, RoDTEP, forex"}),
    _s("hotel_resort", "Resort: occupancy & cost", "🏨", "Tourism", "Operations",
       "Boutique resort + travel desk in Goa, Rs.16 cr turnover, with seasonal occupancy swings, high staff cost, OTA commissions and weak direct-booking conversion.",
       {"company": "CoastLine Resorts", "turnover_cr": 16, "headcount": 80, "city_tier": "Tier-2", "top_challenges": "seasonality, staff cost, OTA commissions, direct bookings"}),
    _s("ecom_close", "E-commerce seller: messy books", "📒", "Retail / D2C", "R2R",
       "Multi-marketplace seller, Rs.25 cr turnover, where month-end close takes 18 days, marketplace settlements + GST are unreconciled and there is no monthly MIS for the owner.",
       {"company": "OmniSeller", "turnover_cr": 25, "headcount": 22, "city_tier": "Tier-1", "close_days": 18, "top_challenges": "slow close, unreconciled settlements, no MIS"}),
    _s("manufacturer_erp", "Manufacturer: ERP & data", "🖥️", "Manufacturing", "Technology",
       "Sheet-metal manufacturer on spreadsheets + Tally, Rs.35 cr turnover, wanting an ERP for BOM, production, inventory and GST, with reliable dashboards for the management.",
       {"company": "MetalWorks", "turnover_cr": 35, "headcount": 110, "city_tier": "Tier-2", "current_system": "spreadsheets + Tally", "top_challenges": "no ERP, BOM/WIP visibility, dashboards"}),
    _s("retailer_cyber", "Retail chain: data & cyber risk", "🔐", "Retail", "Cyber & Data",
       "Retail chain with a loyalty programme holding lakhs of customer records, no consent notice, shared logins, no MFA and no breach plan — worried about DPDP and a possible leak.",
       {"company": "ShopSmart Retail", "turnover_cr": 30, "headcount": 140, "city_tier": "Tier-2", "top_challenges": "DPDP, no MFA, no breach plan, data leak risk"}),
    _s("services_growth", "IT services firm: growth strategy", "💼", "Professional Services", "Strategy",
       "IT services & staffing firm, Rs.26 cr turnover, over-reliant on 2 clients, wanting a growth + diversification strategy, better margins and a path to mid-market enterprise deals.",
       {"company": "TechServe", "turnover_cr": 26, "headcount": 180, "city_tier": "Tier-1", "top_challenges": "client concentration, margins, growth strategy"}),
    _s("furniture_p2p", "Furniture maker: procurement leakage", "🪑", "Manufacturing", "P2P",
       "Furniture manufacturer, Rs.19 cr turnover, with vendor rate leakage, no 3-way match, delayed supplier payments (Sec 43B(h) exposure) and inconsistent quality from suppliers.",
       {"company": "WoodCraft Furniture", "turnover_cr": 19, "headcount": 75, "city_tier": "Tier-3", "top_challenges": "procurement leakage, no 3-way match, supplier quality, delayed payments"}),
    _s("edtech_unit", "Coaching + edtech: profitability", "🎓", "Education", "Finance",
       "Coaching centre with an online test-prep arm, Rs.11 cr turnover, with high CAC, low course completion, fee-collection delays and unclear segment profitability.",
       {"company": "LearnWell", "turnover_cr": 11, "headcount": 50, "city_tier": "Tier-2", "top_challenges": "high CAC, completion rate, fee collection, segment P&L"}),
    _s("jewellery_compliance", "Jewellery retailer: compliance + cash", "💍", "Retail", "Tax & Compliance",
       "Family jewellery retailer, Rs.55 cr turnover, with hallmarking (BIS) obligations, high-value cash controls, GST on making charges and weak inventory/loss controls.",
       {"company": "Sona Jewellers", "turnover_cr": 55, "headcount": 40, "city_tier": "Tier-2", "top_challenges": "hallmarking, cash controls, GST, inventory shrinkage"}),
    _s("solar_mfg_growth", "Solar/LED maker: scale & funding", "🔆", "Manufacturing", "Strategy",
       "Solar & LED products manufacturer, Rs.32 cr turnover, wanting to scale capacity, access government incentives, raise growth capital and tighten unit economics.",
       {"company": "SunBright Energy", "turnover_cr": 32, "headcount": 95, "city_tier": "Tier-2", "top_challenges": "capacity scale, incentives, growth capital, unit economics"}),
    _s("distributor_gtm", "Distributor: route-to-market", "🚛", "Distribution", "Sales & CRM",
       "FMCG super-stockist & distribution house, Rs.45 cr turnover, with weak beat coverage, low secondary-sales visibility, principal margin pressure and salesman productivity issues.",
       {"company": "Indore Distribution House", "turnover_cr": 45, "headcount": 60, "city_tier": "Tier-2", "outlets": 800, "top_challenges": "beat coverage, secondary sales, margin pressure, productivity"}),
    _s("chemicals_safety", "Chemicals unit: risk & audit", "⚗️", "Manufacturing", "Risk & Audit",
       "Specialty chemicals manufacturer, Rs.38 cr turnover, with factory-safety/EHS exposure, weak internal controls, statutory-dues arrears and fraud risk at stores and procurement.",
       {"company": "ChemPro Industries", "turnover_cr": 38, "headcount": 130, "city_tier": "Tier-3", "top_challenges": "EHS, internal controls, statutory arrears, fraud risk"}),
    _s("apparel_retail_turnaround", "Apparel retailer: turnaround", "👗", "Retail", "Turnaround",
       "Apparel & footwear retail chain, Rs.42 cr turnover, loss-making for 2 years, with dead stock, high rentals, falling footfall and a stretched overdraft — needs a turnaround plan.",
       {"company": "TrendKart Retail", "turnover_cr": 42, "headcount": 160, "city_tier": "Tier-2", "top_challenges": "losses, dead stock, rentals, footfall, OD stretched"}),
    _s("printing_packaging", "Printing & packaging: efficiency", "🖨️", "Manufacturing", "Lean",
       "Printing & packaging unit, Rs.21 cr turnover, with high make-ready waste, machine downtime, missed delivery dates and quality rejections from FMCG clients.",
       {"company": "PrintPack Co", "turnover_cr": 21, "headcount": 85, "city_tier": "Tier-2", "top_challenges": "make-ready waste, downtime, delivery, rejections"}),
    _s("real_estate_advisory", "Real-estate firm: project advisory", "🏢", "Real Estate", "Industry-Specific",
       "Property development + brokerage firm, Rs.70 cr turnover, with project cash-flow mismatches, RERA compliance load, slow sales velocity and channel-partner payouts.",
       {"company": "Skyline Realty", "turnover_cr": 70, "headcount": 55, "city_tier": "Tier-1", "top_challenges": "project cash flow, RERA, sales velocity, channel payouts"}),
    _s("dairy_domestic", "Dairy/poultry farm: ops + compliance", "🐄", "Agro / Rural", "Operations",
       "Dairy & poultry farm with cold storage supplying the domestic market, Rs.15 cr turnover, with cold-chain losses, FSSAI compliance, feed-cost volatility and thin margins.",
       {"company": "GreenField Dairy", "turnover_cr": 15, "headcount": 45, "city_tier": "Tier-3", "top_challenges": "cold-chain losses, FSSAI, feed cost, margins"}),
    _s("ma_acquire", "Mid-size firm: bolt-on acquisition", "🤝", "Manufacturing", "M&A / DD",
       "Profitable packaging manufacturer, Rs.80 cr turnover, evaluating a bolt-on acquisition of a smaller competitor — needs target screening, due diligence, valuation and an integration plan.",
       {"company": "PackLeader", "turnover_cr": 80, "headcount": 220, "city_tier": "Tier-1", "top_challenges": "target screening, due diligence, valuation, integration"}),
]


def situations():
    return {"situations": SITUATIONS, "count": len(SITUATIONS),
            "sectors": sorted({s["sector"] for s in SITUATIONS}),
            "lenses": sorted({s["lens"] for s in SITUATIONS})}


def meta():
    return {"count": len(SITUATIONS),
            "sectors": sorted({s["sector"] for s in SITUATIONS}),
            "lenses": sorted({s["lens"] for s in SITUATIONS}),
            "endpoints": ["GET /situations", "GET /situations/meta"]}


def run_situations_tests():
    ok = (len(SITUATIONS) >= 25
          and all(s.get("id") and s.get("description") and isinstance(s.get("intake"), dict) for s in SITUATIONS)
          and len({s["id"] for s in SITUATIONS}) == len(SITUATIONS))
    return {"summary": {"total": 1, "passed": 1 if ok else 0, "deployment_ready": ok, "count": len(SITUATIONS)}}


if __name__ == "__main__":
    import json
    print(json.dumps(run_situations_tests(), indent=2))
