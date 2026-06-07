"""
monitor.py — Stage 7 "Monitor" / Business Command Center for the MSME Consulting OS.

Deterministic, no external deps. The continuous-consulting layer: feed the latest
period's KPIs (current vs previous) + a business profile, and it returns a live
command center —
  * KPI tiles with trend direction, momentum and status vs target,
  * a rolling India statutory compliance calendar with day-countdowns,
  * proactive, prioritised AI recommendations (threshold + trend rules),
  * an overall "watch level".

Compliance dates are computed relative to the server's current date (recurring
GST/TDS/PF/ESI/advance-tax/ROC/annual filings). Sector licences are surfaced via
msme_agents.compliance_for() when available.

Endpoint (wired in main.py): POST /monitor   (also GET /monitor/meta)
"""

import datetime

try:
    import msme_agents as _M
except Exception:
    _M = None


# ---- KPI definitions: target + which direction is "good" ----
METRICS = [
    {"key": "revenue", "label": "Monthly Revenue", "unit": "₹", "better": "up", "target": None},
    {"key": "gross_margin_pct", "label": "Gross Margin", "unit": "%", "better": "up", "target": 25},
    {"key": "net_margin_pct", "label": "Net Margin", "unit": "%", "better": "up", "target": 8},
    {"key": "dso_days", "label": "Receivable Days (DSO)", "unit": "days", "better": "down", "target": 50},
    {"key": "collection_rate_pct", "label": "Collection Rate", "unit": "%", "better": "up", "target": 90},
    {"key": "cash_runway_months", "label": "Cash Runway", "unit": "mo", "better": "up", "target": 6},
    {"key": "dead_stock_pct", "label": "Dead / Slow Stock", "unit": "%", "better": "down", "target": 8},
    {"key": "rev_per_employee_lakh", "label": "Revenue / Employee", "unit": "₹L/yr", "better": "up", "target": None},
]
_METRIC_BY_KEY = {m["key"]: m for m in METRICS}


def _num(v):
    try:
        if v is None or v == "":
            return None
        return float(str(v).replace(",", "").replace("₹", "").strip())
    except Exception:
        return None


def _today(body):
    # Allow an override for deterministic testing; else server's date.
    o = (body or {}).get("today")
    if o:
        try:
            return datetime.date.fromisoformat(o)
        except Exception:
            pass
    return datetime.date.today()


# ---------------- KPI TREND ANALYSIS ----------------
def analyze_kpis(body):
    metrics_in = (body or {}).get("metrics") or {}
    out = []
    for m in METRICS:
        raw = metrics_in.get(m["key"]) or {}
        cur = _num(raw.get("current"))
        prev = _num(raw.get("previous"))
        if cur is None:
            continue
        # direction of change
        direction, change_pct = "flat", None
        if prev not in (None, 0):
            change_pct = round((cur - prev) / abs(prev) * 100, 1)
            if change_pct > 1.5:
                direction = "up"
            elif change_pct < -1.5:
                direction = "down"
        # momentum: is the change moving toward "better"?
        momentum = "steady"
        if direction != "flat":
            improving = (direction == m["better"])
            momentum = "improving" if improving else "worsening"
        # status vs target
        status = "ok"
        tgt = m["target"]
        if tgt is not None:
            if m["better"] == "up":
                status = "good" if cur >= tgt else ("watch" if cur >= tgt * 0.8 else "critical")
            else:  # lower is better
                status = "good" if cur <= tgt else ("watch" if cur <= tgt * 1.25 else "critical")
        out.append({
            "key": m["key"], "label": m["label"], "unit": m["unit"], "better": m["better"],
            "current": cur, "previous": prev, "target": tgt,
            "direction": direction, "change_pct": change_pct,
            "momentum": momentum, "status": status,
        })
    return out


# ---------------- COMPLIANCE CALENDAR ----------------
def _next_monthly(today, day):
    """Next occurrence of `day`-of-month on/after today."""
    y, m = today.year, today.month
    try:
        cand = datetime.date(y, m, day)
    except ValueError:
        cand = today
    if cand < today:
        m += 1
        if m > 12:
            m, y = 1, y + 1
        cand = datetime.date(y, m, day)
    return cand


def _next_fixed(today, month, day):
    """Next occurrence of a fixed month/day (this year or next)."""
    y = today.year
    cand = datetime.date(y, month, day)
    if cand < today:
        cand = datetime.date(y + 1, month, day)
    return cand


def _next_quarterly_tds(today):
    # TDS returns: 31 Jul, 31 Oct, 31 Jan, 31 May
    opts = [(7, 31), (10, 31), (1, 31), (5, 31)]
    cands = sorted(_next_fixed(today, mo, d) for mo, d in opts)
    return cands[0]


def _next_advance_tax(today):
    opts = [(6, 15), (9, 15), (12, 15), (3, 15)]
    cands = sorted(_next_fixed(today, mo, d) for mo, d in opts)
    return cands[0]


def compliance_calendar(body):
    today = _today(body)
    items = [
        ("GSTR-1 (outward supplies)", "GST / CBIC", _next_monthly(today, 11), "Monthly"),
        ("GSTR-3B (summary + tax)", "GST / CBIC", _next_monthly(today, 20), "Monthly"),
        ("TDS payment", "Income Tax", _next_monthly(today, 7), "Monthly"),
        ("EPF (PF) contribution", "EPFO", _next_monthly(today, 15), "Monthly"),
        ("ESI contribution", "ESIC", _next_monthly(today, 15), "Monthly"),
        ("TDS return (24Q/26Q)", "Income Tax", _next_quarterly_tds(today), "Quarterly"),
        ("Advance tax instalment", "Income Tax", _next_advance_tax(today), "Quarterly"),
        ("GSTR-9 annual return", "GST / CBIC", _next_fixed(today, 12, 31), "Annual"),
        ("Income Tax Return (non-audit)", "Income Tax", _next_fixed(today, 7, 31), "Annual"),
        ("ROC AOC-4 (financials)", "MCA", _next_fixed(today, 10, 30), "Annual"),
        ("ROC MGT-7 (annual return)", "MCA", _next_fixed(today, 11, 29), "Annual"),
    ]
    cal = []
    for name, auth, due, cadence in items:
        days = (due - today).days
        urgency = "overdue" if days < 0 else ("due_soon" if days <= 7 else ("upcoming" if days <= 30 else "scheduled"))
        cal.append({
            "name": name, "authority": auth, "due_date": due.isoformat(),
            "days_left": days, "cadence": cadence, "urgency": urgency,
        })
    cal.sort(key=lambda x: x["days_left"])

    # Sector licences (informational) from the classifier + compliance map.
    sector_notes = []
    desc = (body or {}).get("description", "")
    if _M and desc:
        try:
            cls = _M.classify_business(desc)
            cmp = _M.compliance_for(cls) if hasattr(_M, "compliance_for") else None
            if isinstance(cmp, dict):
                for k in ("licences", "registrations", "sector_specific", "items"):
                    v = cmp.get(k)
                    if isinstance(v, list):
                        sector_notes.extend([str(x) for x in v][:6])
        except Exception:
            pass
    return {"today": today.isoformat(), "calendar": cal, "sector_licences": sector_notes[:6]}


# ---------------- PROACTIVE ALERTS ----------------
def _alerts(kpis, cal):
    alerts = []
    by = {k["key"]: k for k in kpis}

    def add(sev, title, detail, action):
        alerts.append({"severity": sev, "title": title, "detail": detail, "action": action})

    cr = by.get("cash_runway_months")
    if cr:
        if cr["current"] < 3:
            add("Critical", "Cash runway under 3 months", f"Runway is {cr['current']:.0f} months.",
                "Trigger the cash-release levers (collect receivables, liquidate dead stock) and line up a CGTMSE/working-capital facility now.")
        elif cr["current"] < 6:
            add("High", "Cash runway below comfort", f"Runway is {cr['current']:.0f} months (target ≥ 6).",
                "Build a 13-week cash-flow forecast and tighten collections before it bites.")

    dso = by.get("dso_days")
    if dso and dso["status"] in ("watch", "critical"):
        add("High" if dso["status"] == "critical" else "Medium", "Receivables stretching",
            f"DSO at {dso['current']:.0f} days (target {dso['target']}).",
            "Run an ageing review, enforce credit terms, and consider TReDS to discount invoices.")
    elif dso and dso.get("momentum") == "worsening":
        add("Medium", "Receivable days creeping up", f"DSO rose {abs(dso['change_pct']):.0f}% vs last period.",
            "Tighten follow-ups on the oldest 20% of invoices.")

    gm = by.get("gross_margin_pct")
    if gm and gm.get("momentum") == "worsening":
        add("Medium", "Gross margin erosion", f"Gross margin fell {abs(gm['change_pct']):.0f}% vs last period.",
            "Re-price slow movers, renegotiate top-3 input costs, and audit discount leakage.")

    ds = by.get("dead_stock_pct")
    if ds and ds["status"] in ("watch", "critical"):
        add("Medium", "Dead / slow stock building", f"Dead stock at {ds['current']:.0f}% (target ≤ {ds['target']}%).",
            "Run a clearance push on non-movers and tighten reorder points.")

    rev = by.get("revenue")
    if rev and rev.get("momentum") == "worsening":
        add("High", "Revenue declining", f"Revenue down {abs(rev['change_pct']):.0f}% vs last period.",
            "Review the sales funnel, reactivate dormant customers, and check competitive/seasonal causes.")

    # compliance
    for c in cal["calendar"]:
        if c["urgency"] == "overdue":
            add("Critical", f"OVERDUE: {c['name']}", f"Was due {c['due_date']} ({-c['days_left']} days ago).",
                f"File immediately with {c['authority']} to limit interest/late fees.")
        elif c["urgency"] == "due_soon":
            add("High", f"Due in {c['days_left']}d: {c['name']}", f"Due {c['due_date']} ({c['authority']}).",
                "Prepare and file before the deadline.")

    sev_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    alerts.sort(key=lambda a: sev_rank.get(a["severity"], 4))
    return alerts


def _watch_level(kpis, alerts):
    if any(a["severity"] == "Critical" for a in alerts):
        return {"level": "Critical", "color": "red"}
    if sum(1 for a in alerts if a["severity"] == "High") >= 2:
        return {"level": "Elevated", "color": "amber"}
    if alerts:
        return {"level": "Watch", "color": "amber"}
    return {"level": "Healthy", "color": "emerald"}


def command_center(body):
    body = body or {}
    kpis = analyze_kpis(body)
    cal = compliance_calendar(body)
    alerts = _alerts(kpis, cal)
    watch = _watch_level(kpis, alerts)
    return {
        "business": (body.get("description") or "Your business").strip()[:120],
        "today": cal["today"],
        "watch_level": watch,
        "kpis": kpis,
        "alerts": alerts,
        "alert_count": len(alerts),
        "compliance": cal["calendar"],
        "compliance_due_soon": [c for c in cal["calendar"] if c["urgency"] in ("overdue", "due_soon")],
        "sector_licences": cal["sector_licences"],
        "disclaimer": "Statutory due dates are the usual recurring deadlines and can shift with government notifications/extensions — confirm exact dates with your CA/CS. KPI thresholds are indicative.",
    }


def meta():
    return {
        "metrics": [{"key": m["key"], "label": m["label"], "unit": m["unit"], "better": m["better"], "target": m["target"]} for m in METRICS],
        "endpoints": ["POST /monitor", "GET /monitor/meta", "GET /monitor/tests"],
    }


def run_monitor_tests():
    cases = []
    # critical cash + overdue-aware
    out = command_center({
        "description": "kirana retail chain in Pune",
        "today": "2026-06-07",
        "metrics": {
            "revenue": {"current": 95, "previous": 100},
            "gross_margin_pct": {"current": 18, "previous": 21},
            "dso_days": {"current": 72, "previous": 60},
            "cash_runway_months": {"current": 2, "previous": 4},
            "dead_stock_pct": {"current": 19, "previous": 14},
        },
    })
    cases.append(("trends+alerts", out["alert_count"] > 0 and out["watch_level"]["level"] == "Critical"
                  and len(out["kpis"]) == 5 and len(out["compliance"]) >= 10))
    # healthy business -> fewer/no KPI alerts (compliance alerts may still appear)
    out2 = command_center({
        "description": "textile exporter", "today": "2026-06-07",
        "metrics": {"gross_margin_pct": {"current": 30, "previous": 29}, "cash_runway_months": {"current": 9, "previous": 8}},
    })
    cases.append(("healthy", out2["watch_level"]["level"] in ("Healthy", "Watch", "Elevated") and len(out2["kpis"]) == 2))
    # compliance countdown sane
    out3 = command_center({"today": "2026-06-07", "metrics": {}})
    cal_ok = all("days_left" in c and "due_date" in c for c in out3["compliance"]) and out3["compliance"][0]["days_left"] >= -400
    cases.append(("calendar", cal_ok and len(out3["compliance"]) >= 10))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    import json
    print(json.dumps(run_monitor_tests(), indent=2))
