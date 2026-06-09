// Shared demo businesses — one realistic sample per top India MSME business type.
// Used by the CEO Office (consulting engine) and Monitor (PM/command-center engine)
// so the demo version can showcase EVERY sector with one click.
//
// Each entry carries:
//   description / turnover_cr / city_tier / top_challenges  -> for /consult (CEO Office)
//   metrics {current, previous}                             -> for /monitor
// A mix of stressed and healthy profiles for variety.

export const DEMO_BUSINESSES = [
  {
    key: "retail_kirana", icon: "🛒", label: "Kirana / Retail",
    description: "8-store grocery / kirana retail chain in Pune, GST registered, 22 staff",
    turnover_cr: "12", city_tier: "Tier-2", top_challenges: "stockouts\nthin margins\ndead stock",
    metrics: { revenue: { current: 95, previous: 100 }, gross_margin_pct: { current: 18, previous: 21 }, net_margin_pct: { current: 3, previous: 5 }, dso_days: { current: 40, previous: 38 }, cash_runway_months: { current: 3, previous: 4 }, dead_stock_pct: { current: 18, previous: 13 } },
  },
  {
    key: "wholesale", icon: "📦", label: "Wholesale / B2B",
    description: "FMCG wholesale & cash-and-carry in Nagpur supplying 600+ retailers",
    turnover_cr: "34", city_tier: "Tier-2", top_challenges: "credit on trade\nstretched receivables\nthin spreads",
    metrics: { revenue: { current: 280, previous: 270 }, gross_margin_pct: { current: 9, previous: 10 }, dso_days: { current: 62, previous: 55 }, collection_rate_pct: { current: 84, previous: 90 }, cash_runway_months: { current: 4, previous: 5 } },
  },
  {
    key: "distribution", icon: "🚚", label: "FMCG Distribution",
    description: "FMCG super-stockist & distribution house in Indore for 3 HPC brands",
    turnover_cr: "45", city_tier: "Tier-2", top_challenges: "principal margin pressure\nbeat coverage\nworking capital",
    metrics: { revenue: { current: 370, previous: 360 }, gross_margin_pct: { current: 7, previous: 7 }, dso_days: { current: 48, previous: 50 }, cash_runway_months: { current: 5, previous: 5 }, rev_per_employee_lakh: { current: 95, previous: 90 } },
  },
  {
    key: "manufacturing", icon: "🏭", label: "Manufacturing",
    description: "auto-component machining MSME in Pune supplying Tier-1 OEMs, 60 workers",
    turnover_cr: "26", city_tier: "Tier-1", top_challenges: "capacity utilisation\nrework / scrap\norder concentration",
    metrics: { revenue: { current: 210, previous: 205 }, gross_margin_pct: { current: 28, previous: 30 }, net_margin_pct: { current: 7, previous: 9 }, dso_days: { current: 68, previous: 60 }, cash_runway_months: { current: 5, previous: 6 } },
  },
  {
    key: "food_processing", icon: "🍲", label: "Food Processing",
    description: "spice & masala processing unit in Rajkot selling under own brand + private label",
    turnover_cr: "18", city_tier: "Tier-2", top_challenges: "raw-material price swings\nFSSAI compliance\nbranding spend",
    metrics: { revenue: { current: 150, previous: 140 }, gross_margin_pct: { current: 26, previous: 25 }, net_margin_pct: { current: 8, previous: 7 }, dead_stock_pct: { current: 9, previous: 11 }, cash_runway_months: { current: 6, previous: 5 } },
  },
  {
    key: "agro_business", icon: "🌾", label: "Agro Trade",
    description: "agro-commodity trading house in Kochi aggregating spices & pulses from FPOs",
    turnover_cr: "52", city_tier: "Tier-2", top_challenges: "price volatility\nbuyer concentration\nquality grading",
    metrics: { revenue: { current: 420, previous: 400 }, gross_margin_pct: { current: 11, previous: 12 }, dso_days: { current: 58, previous: 52 }, top_customer_dep_pct: { current: 38, previous: 35 }, cash_runway_months: { current: 4, previous: 5 } },
  },
  {
    key: "pharma", icon: "💊", label: "Pharma / Chemist",
    description: "pharma retail & distribution business in Mumbai running 14 chemist outlets",
    turnover_cr: "40", city_tier: "Tier-1", top_challenges: "expiry write-offs\nprice control (DPCO)\ncredit cycle",
    metrics: { revenue: { current: 330, previous: 325 }, gross_margin_pct: { current: 19, previous: 20 }, net_margin_pct: { current: 4, previous: 5 }, dead_stock_pct: { current: 12, previous: 9 }, cash_runway_months: { current: 5, previous: 6 } },
  },
  {
    key: "textile", icon: "🧵", label: "Textile & Apparel",
    description: "textile garment manufacturer-exporter in Surat shipping to the EU & UAE",
    turnover_cr: "30", city_tier: "Tier-2", top_challenges: "order seasonality\nbuyer compliance audits\nFX risk",
    metrics: { revenue: { current: 250, previous: 230 }, gross_margin_pct: { current: 24, previous: 23 }, dso_days: { current: 72, previous: 65 }, cash_runway_months: { current: 5, previous: 5 }, rev_per_employee_lakh: { current: 18, previous: 17 } },
  },
  {
    key: "services", icon: "🛠️", label: "Professional Services",
    description: "B2B digital-marketing & design agency in Bengaluru, 35-person team",
    turnover_cr: "9", city_tier: "Tier-1", top_challenges: "utilisation\nclient concentration\ncollections",
    metrics: { revenue: { current: 72, previous: 68 }, gross_margin_pct: { current: 48, previous: 50 }, net_margin_pct: { current: 14, previous: 16 }, dso_days: { current: 55, previous: 48 }, rev_per_employee_lakh: { current: 26, previous: 24 } },
  },
  {
    key: "logistics", icon: "🚛", label: "Logistics & Warehousing",
    description: "3PL & warehousing operator in Bhiwandi running 1.2 lakh sq ft + a fleet",
    turnover_cr: "38", city_tier: "Tier-2", top_challenges: "fleet utilisation\nfuel cost\nspace occupancy",
    metrics: { revenue: { current: 310, previous: 300 }, gross_margin_pct: { current: 22, previous: 23 }, dso_days: { current: 64, previous: 58 }, cash_runway_months: { current: 4, previous: 5 } },
  },
  {
    key: "export_business", icon: "🌏", label: "Export / EXIM House",
    description: "merchant export house in Tiruppur exporting home textiles to US retailers",
    turnover_cr: "60", city_tier: "Tier-2", top_challenges: "buyer concentration\nRoDTEP claims\nFX & freight",
    metrics: { revenue: { current: 500, previous: 470 }, gross_margin_pct: { current: 14, previous: 15 }, dso_days: { current: 75, previous: 70 }, top_customer_dep_pct: { current: 45, previous: 42 }, cash_runway_months: { current: 5, previous: 6 } },
  },
  {
    key: "restaurants", icon: "🍽️", label: "Restaurants / Cloud Kitchen",
    description: "4-outlet cloud-kitchen brand in Hyderabad on Swiggy/Zomato + own app",
    turnover_cr: "7", city_tier: "Tier-1", top_challenges: "aggregator commissions\nfood cost\nrider/SLA",
    metrics: { revenue: { current: 56, previous: 60 }, gross_margin_pct: { current: 60, previous: 62 }, net_margin_pct: { current: 6, previous: 9 }, cash_runway_months: { current: 3, previous: 4 } },
  },
  {
    key: "d2c", icon: "🛍️", label: "D2C / E-commerce Brand",
    description: "D2C wellness brand in Delhi selling on own site + marketplaces",
    turnover_cr: "11", city_tier: "Tier-1", top_challenges: "rising CAC\nblended margins\nreturns (RTO)",
    metrics: { revenue: { current: 88, previous: 80 }, gross_margin_pct: { current: 55, previous: 58 }, net_margin_pct: { current: -2, previous: 1 }, cash_runway_months: { current: 7, previous: 9 } },
  },
  {
    key: "electronics", icon: "🔌", label: "Electronics / ESDM",
    description: "consumer-electronics & mobile-accessories distributor in Delhi",
    turnover_cr: "33", city_tier: "Tier-1", top_challenges: "price erosion\ninventory obsolescence\ncredit risk",
    metrics: { revenue: { current: 270, previous: 275 }, gross_margin_pct: { current: 8, previous: 9 }, dead_stock_pct: { current: 16, previous: 12 }, dso_days: { current: 52, previous: 48 }, cash_runway_months: { current: 4, previous: 5 } },
  },
  {
    key: "automotive", icon: "🔧", label: "Auto Components / Workshop",
    description: "multi-brand auto service & spares workshop chain in Coimbatore (5 bays)",
    turnover_cr: "8", city_tier: "Tier-2", top_challenges: "technician productivity\nspares margin\nrepeat footfall",
    metrics: { revenue: { current: 64, previous: 62 }, gross_margin_pct: { current: 35, previous: 36 }, net_margin_pct: { current: 9, previous: 10 }, rev_per_employee_lakh: { current: 16, previous: 15 }, cash_runway_months: { current: 5, previous: 5 } },
  },
  {
    key: "construction", icon: "🏗️", label: "Construction / Infra Supplier",
    description: "building-materials supplier & sub-contractor in Jaipur serving infra projects",
    turnover_cr: "22", city_tier: "Tier-2", top_challenges: "delayed payments\nproject concentration\nworking capital",
    metrics: { revenue: { current: 180, previous: 185 }, gross_margin_pct: { current: 16, previous: 17 }, dso_days: { current: 88, previous: 80 }, collection_rate_pct: { current: 78, previous: 85 }, cash_runway_months: { current: 3, previous: 4 } },
  },
];
