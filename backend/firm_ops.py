"""
firm_ops.py — the consulting-firm ERP layer: RBAC, timesheets, expenses and the
firm-wide Finance / Partner Cockpit.

This turns the platform from "run one engagement" into "run the firm":
  * RBAC — modules x roles access matrix (who sees Engagements, Timesheets, Billing,
    Finance, Firm Cockpit, Admin…). Drives the UI per role; the seam for Cognito later.
  * Timesheets — billable / non-billable hours per engagement + consultant, with
    utilization. (Replaces manual timesheets; AI can pre-fill from activity later.)
  * Expenses — submission + approval, billable / non-billable, reimbursable.
  * Firm Cockpit — the Senior-Partner view: contracted value, recognised revenue by
    period, CAGR, utilization, realisation, billable mix, by-sector / by-type, top
    engagements, margin — rolled up across every saved engagement (the twin store).

Deterministic. JSONL persistence under BRAIN_DATA_DIR (owner-scoped; swappable for
Postgres like engagement_store). Endpoints (main.py): GET /firm/cockpit, /firm/rbac,
GET/POST /firm/timesheets, GET/POST /firm/expenses (+ /firm/meta, /firm/tests).
"""

import os
import json
import time
import hashlib

try:
    import engagement_store as _ES
except Exception:
    _ES = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.getenv("BRAIN_DATA_DIR", "").strip() or os.path.join(_HERE, "brain_data")
_TS_PATH = os.path.join(_DATA_DIR, "timesheets.jsonl")
_EX_PATH = os.path.join(_DATA_DIR, "expenses.jsonl")


# ---------------------------------------------------------------------------
# RBAC — modules x roles
# ---------------------------------------------------------------------------
MODULES = [
    {"key": "firm_cockpit",  "name": "Firm Cockpit",      "icon": "📊", "desc": "Firm-wide P&L, CAGR, utilization, pipeline"},
    {"key": "engagements",   "name": "Engagements",       "icon": "🛰️", "desc": "Run & view engagements (Engagement 360)"},
    {"key": "workplan",      "name": "Workplan & Tasks",  "icon": "🗂️", "desc": "Per-engagement AI-supported task lists"},
    {"key": "timesheets",    "name": "Timesheets",        "icon": "⏱️", "desc": "Billable / non-billable hours"},
    {"key": "billing",       "name": "Billing",           "icon": "💳", "desc": "Engagement fees, invoices, realisation"},
    {"key": "finance",       "name": "Finance",           "icon": "💰", "desc": "Firm finance, margin, revenue recognition"},
    {"key": "expenses",      "name": "Expenses",          "icon": "🧾", "desc": "Expense submission & approval"},
    {"key": "resourcing",    "name": "Resourcing",        "icon": "👥", "desc": "Staffing, utilization, capacity"},
    {"key": "catalog",       "name": "Service Catalog",   "icon": "📚", "desc": "Towers / service lines / engagement types"},
    {"key": "deliverables",  "name": "Deliverables",      "icon": "📑", "desc": "AI-generated decks, reports, docs"},
    {"key": "admin",         "name": "Admin & RBAC",      "icon": "⚙️", "desc": "Users, roles, rate cards, settings"},
]
_ALL = [m["key"] for m in MODULES]

# Role -> modules it can access. (Roles mirror engagement_360 hierarchy + firm admin.)
ROLE_ACCESS = {
    "senior_partner":     _ALL,  # sees everything, firm-wide
    "partner":            ["firm_cockpit", "engagements", "workplan", "timesheets", "billing", "finance", "expenses", "resourcing", "catalog", "deliverables"],
    "engagement_director":["firm_cockpit", "engagements", "workplan", "timesheets", "billing", "expenses", "resourcing", "catalog", "deliverables"],
    "engagement_manager": ["engagements", "workplan", "timesheets", "billing", "expenses", "resourcing", "catalog", "deliverables"],
    "senior_consultant":  ["engagements", "workplan", "timesheets", "expenses", "catalog", "deliverables"],
    "consultant":         ["engagements", "workplan", "timesheets", "expenses", "catalog", "deliverables"],
    "junior_consultant":  ["workplan", "timesheets", "expenses", "catalog"],
    "finance_admin":      ["firm_cockpit", "billing", "finance", "expenses", "timesheets", "admin"],
    "client_sponsor":     ["engagements", "deliverables"],
}


def rbac():
    return {"modules": MODULES,
            "role_access": ROLE_ACCESS,
            "roles": list(ROLE_ACCESS.keys()),
            "note": "Module access by role. Enforced in the UI today; bind to Cognito groups at deploy."}


def can_access(role, module):
    return module in ROLE_ACCESS.get(role, [])


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------
def _ensure_dir():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        return True
    except Exception:
        return False


def _read(path):
    out = []
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            out.append(json.loads(line))
                        except Exception:
                            continue
    except Exception:
        pass
    return out


def _append(path, rec):
    if not _ensure_dir():
        return False
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def _owner(o):
    return (o or "").strip() or "demo"


def _num(v, d=0):
    try:
        return float(str(v).replace(",", "").replace("₹", "").strip())
    except Exception:
        return d


def _inr(n):
    return f"₹{n:,.0f}"


# ---------------------------------------------------------------------------
# Timesheets
# ---------------------------------------------------------------------------
def add_timesheet(body):
    owner = _owner(body.get("owner"))
    rec = {
        "id": hashlib.sha1(f"ts:{owner}:{time.time()}".encode()).hexdigest()[:12],
        "owner": owner, "ts": int(time.time()),
        "engagement_id": (body.get("engagement_id") or "").strip(),
        "consultant": (body.get("consultant") or "").strip() or "—",
        "role": (body.get("role") or "consultant").strip(),
        "date": (body.get("date") or "").strip(),
        "hours": _num(body.get("hours")),
        "billable": bool(body.get("billable", True)),
        "activity": (body.get("activity") or "").strip(),
    }
    if rec["hours"] <= 0:
        return {"error": "hours must be > 0"}
    _append(_TS_PATH, rec)
    return {"ok": True, "id": rec["id"], "entry": rec}


def list_timesheets(owner, engagement_id=None):
    owner = _owner(owner)
    rows = [r for r in _read(_TS_PATH) if r.get("owner") == owner]
    if engagement_id:
        rows = [r for r in rows if r.get("engagement_id") == engagement_id]
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    bill = sum(r["hours"] for r in rows if r.get("billable"))
    nonbill = sum(r["hours"] for r in rows if not r.get("billable"))
    total = bill + nonbill
    return {"owner": owner, "count": len(rows), "entries": rows[:200],
            "billable_hours": round(bill, 1), "nonbillable_hours": round(nonbill, 1),
            "total_hours": round(total, 1),
            "utilization_pct": round(bill / total * 100, 1) if total else 0}


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------
EXPENSE_CATEGORIES = ["Travel", "Accommodation", "Meals", "Software/Tools", "Subcontractor", "Other"]


def add_expense(body):
    owner = _owner(body.get("owner"))
    rec = {
        "id": hashlib.sha1(f"ex:{owner}:{time.time()}".encode()).hexdigest()[:12],
        "owner": owner, "ts": int(time.time()),
        "engagement_id": (body.get("engagement_id") or "").strip(),
        "consultant": (body.get("consultant") or "").strip() or "—",
        "category": (body.get("category") or "Other").strip(),
        "amount": _num(body.get("amount")),
        "billable": bool(body.get("billable", True)),
        "status": "Submitted",
        "note": (body.get("note") or "").strip(),
    }
    if rec["amount"] <= 0:
        return {"error": "amount must be > 0"}
    _append(_EX_PATH, rec)
    return {"ok": True, "id": rec["id"], "expense": rec}


def set_expense_status(body):
    owner = _owner(body.get("owner"))
    eid = (body.get("id") or "").strip()
    status = (body.get("status") or "Approved").strip()
    rows = _read(_EX_PATH)
    changed = 0
    for r in rows:
        if r.get("id") == eid and r.get("owner") == owner:
            r["status"] = status
            changed += 1
    if changed and _ensure_dir():
        with open(_EX_PATH, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"ok": bool(changed), "changed": changed}


def list_expenses(owner, engagement_id=None):
    owner = _owner(owner)
    rows = [r for r in _read(_EX_PATH) if r.get("owner") == owner]
    if engagement_id:
        rows = [r for r in rows if r.get("engagement_id") == engagement_id]
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    bill = sum(r["amount"] for r in rows if r.get("billable"))
    nonbill = sum(r["amount"] for r in rows if not r.get("billable"))
    return {"owner": owner, "count": len(rows), "expenses": rows[:200], "categories": EXPENSE_CATEGORIES,
            "billable_amount": bill, "billable_label": _inr(bill),
            "nonbillable_amount": nonbill, "nonbillable_label": _inr(nonbill),
            "total_amount": bill + nonbill, "total_label": _inr(bill + nonbill),
            "pending_approval": sum(1 for r in rows if r.get("status") == "Submitted")}


# ---------------------------------------------------------------------------
# Firm Cockpit (Senior Partner)
# ---------------------------------------------------------------------------
def _fee_of(report):
    return _num(((report or {}).get("delivery") or {}).get("economics", {}).get("tm_fee"))


def _quarter(ts):
    import datetime
    d = datetime.datetime.utcfromtimestamp(ts)
    return f"{d.year}-Q{(d.month - 1)//3 + 1}"


def _cagr(series):
    """series = list of (period, value) ordered; returns period-over-period CAGR %."""
    vals = [v for _, v in series if v > 0]
    if len(vals) < 2:
        return None
    first, last, n = vals[0], vals[-1], len(vals) - 1
    try:
        return round(((last / first) ** (1 / n) - 1) * 100, 1)
    except Exception:
        return None


def cockpit(owner):
    owner = _owner(owner)
    recs = _ES.all_records(owner) if _ES else []
    n = len(recs)
    total_contracted = 0
    by_sector, by_type, by_period = {}, {}, {}
    top = []
    for r in recs:
        rep = r.get("report") or {}
        fee = _fee_of(rep)
        total_contracted += fee
        sec = r.get("sector") or rep.get("sector") or "Unknown"
        by_sector[sec] = by_sector.get(sec, 0) + fee
        et = (rep.get("engagement_type") or {}).get("name") or "Ad-hoc"
        by_type[et] = by_type.get(et, 0) + fee
        period = _quarter(r.get("ts", 0))
        by_period[period] = by_period.get(period, 0) + fee
        top.append({"id": r.get("id"), "title": r.get("title") or rep.get("title"), "sector": sec,
                    "posture": r.get("posture") or (rep.get("diagnosis") or {}).get("posture"),
                    "fee": fee, "fee_label": _inr(fee)})
    top.sort(key=lambda x: x["fee"], reverse=True)
    period_series = sorted(by_period.items())
    cagr = _cagr(period_series)

    # timesheets / expenses roll-up
    ts = list_timesheets(owner)
    ex = list_expenses(owner)
    # recognised revenue (billed actuals) ~ billable hours * blended rate proxy; if no
    # timesheets yet, fall back to contracted value as the pipeline figure.
    blended = 5000  # ₹/hr proxy; refined once role-level timesheets accrue
    recognised = round(ts["billable_hours"] * blended)
    margin_pct = round((1 - ex["billable_amount"] / recognised) * 100, 1) if recognised else None

    return {
        "owner": owner,
        "engagements": n,
        "contracted_value": total_contracted, "contracted_label": _inr(total_contracted),
        "recognised_revenue": recognised, "recognised_label": _inr(recognised),
        "avg_engagement_value": _inr(total_contracted / n) if n else "₹0",
        "revenue_by_period": [{"period": p, "value": v, "label": _inr(v)} for p, v in period_series],
        "cagr_pct": cagr,
        "by_sector": [{"sector": k, "value": v, "label": _inr(v)} for k, v in sorted(by_sector.items(), key=lambda x: x[1], reverse=True)],
        "by_type": [{"type": k, "value": v, "label": _inr(v)} for k, v in sorted(by_type.items(), key=lambda x: x[1], reverse=True)],
        "top_engagements": top[:8],
        "utilization_pct": ts["utilization_pct"],
        "billable_hours": ts["billable_hours"], "nonbillable_hours": ts["nonbillable_hours"],
        "expenses_total": ex["total_amount"], "expenses_label": ex["total_label"],
        "gross_margin_pct": margin_pct,
        "note": "Firm-wide roll-up across saved engagements. Contracted = sum of engagement T&M fees; "
                "recognised revenue accrues from billable timesheets; CAGR is period-over-period on booked fees "
                "(indicative until more history accrues).",
    }


def meta():
    return {"modules": [m["key"] for m in MODULES], "roles": list(ROLE_ACCESS.keys()),
            "expense_categories": EXPENSE_CATEGORIES,
            "endpoints": ["GET /firm/cockpit?owner=", "GET /firm/rbac", "GET|POST /firm/timesheets",
                          "GET|POST /firm/expenses", "POST /firm/expenses/status"]}


def run_firm_tests():
    cases = []
    o = "__firm_test__"
    # rbac
    rb = rbac()
    cases.append(("rbac", len(rb["modules"]) >= 8 and set(ROLE_ACCESS["senior_partner"]) == set(_ALL)
                  and not can_access("junior_consultant", "finance")))
    # timesheet billable/non-billable + utilization
    add_timesheet({"owner": o, "engagement_id": "E1", "role": "consultant", "hours": 8, "billable": True, "activity": "analysis"})
    add_timesheet({"owner": o, "engagement_id": "E1", "role": "consultant", "hours": 2, "billable": False, "activity": "internal"})
    ts = list_timesheets(o, "E1")
    cases.append(("timesheets", ts["billable_hours"] == 8 and ts["nonbillable_hours"] == 2 and ts["utilization_pct"] == 80.0))
    # expense submit + approve
    ax = add_expense({"owner": o, "engagement_id": "E1", "category": "Travel", "amount": 5000, "billable": True})
    set_expense_status({"owner": o, "id": ax["id"], "status": "Approved"})
    ex = list_expenses(o, "E1")
    cases.append(("expenses", ex["billable_amount"] >= 5000 and any(e["status"] == "Approved" for e in ex["expenses"])))
    # cockpit returns a coherent shape (works even with no engagements)
    ck = cockpit(o)
    cases.append(("cockpit", "contracted_value" in ck and "cagr_pct" in ck and ck["utilization_pct"] == 80.0))
    # cleanup timesheets/expenses for the test owner
    for path in (_TS_PATH, _EX_PATH):
        rows = [r for r in _read(path) if r.get("owner") != o]
        if _ensure_dir():
            with open(path, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    print(json.dumps(run_firm_tests(), indent=2))
