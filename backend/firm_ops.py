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
# DB seam — reuse engagement_store's Postgres connection when DATABASE_URL is set,
# else fall back to JSONL. Keeps the whole firm ERP on one storage backend.
# ---------------------------------------------------------------------------
_USE_DB = bool(_ES and getattr(_ES, "_USE_DB", False))
_RDC = getattr(_ES, "_RDC", None) if _ES else None

_DDL = """
CREATE TABLE IF NOT EXISTS timesheets (
    id TEXT PRIMARY KEY, owner TEXT NOT NULL, ts BIGINT, engagement_id TEXT,
    consultant TEXT, role TEXT, date TEXT, hours DOUBLE PRECISION, billable BOOLEAN, activity TEXT);
CREATE INDEX IF NOT EXISTS idx_timesheets_owner ON timesheets (owner, engagement_id);
CREATE TABLE IF NOT EXISTS expenses (
    id TEXT PRIMARY KEY, owner TEXT NOT NULL, ts BIGINT, engagement_id TEXT,
    consultant TEXT, category TEXT, amount DOUBLE PRECISION, billable BOOLEAN, status TEXT, note TEXT,
    submit_role TEXT, approver_role TEXT, receipt TEXT, ocr_engine TEXT);
CREATE INDEX IF NOT EXISTS idx_expenses_owner ON expenses (owner, engagement_id);
"""

if _USE_DB:
    try:
        with _ES._connect() as _c, _c.cursor() as _cur:
            _cur.execute(_DDL)
            _c.commit()
        print("[firm_ops] Postgres backend active (timesheets, expenses).", flush=True)
    except Exception as e:  # pragma: no cover
        print(f"[firm_ops] Postgres init failed ({e}); using JSONL.", flush=True)
        _USE_DB = False


def _ts_rows(owner, eid=None):
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor(cursor_factory=_RDC) as cur:
                if eid:
                    cur.execute("SELECT * FROM timesheets WHERE owner=%s AND engagement_id=%s ORDER BY ts DESC", (owner, eid))
                else:
                    cur.execute("SELECT * FROM timesheets WHERE owner=%s ORDER BY ts DESC", (owner,))
                return [dict(r) for r in cur.fetchall()]
        except Exception as e:  # pragma: no cover
            print(f"[firm_ops] ts read failed: {e}", flush=True)
            return []
    rows = [r for r in _read(_TS_PATH) if r.get("owner") == owner and (not eid or r.get("engagement_id") == eid)]
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return rows


def _ex_rows(owner, eid=None):
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor(cursor_factory=_RDC) as cur:
                if eid:
                    cur.execute("SELECT * FROM expenses WHERE owner=%s AND engagement_id=%s ORDER BY ts DESC", (owner, eid))
                else:
                    cur.execute("SELECT * FROM expenses WHERE owner=%s ORDER BY ts DESC", (owner,))
                return [dict(r) for r in cur.fetchall()]
        except Exception as e:  # pragma: no cover
            print(f"[firm_ops] ex read failed: {e}", flush=True)
            return []
    rows = [r for r in _read(_EX_PATH) if r.get("owner") == owner and (not eid or r.get("engagement_id") == eid)]
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return rows


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
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor() as cur:
                cur.execute("""INSERT INTO timesheets (id,owner,ts,engagement_id,consultant,role,date,hours,billable,activity)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING""",
                            (rec["id"], rec["owner"], rec["ts"], rec["engagement_id"], rec["consultant"], rec["role"],
                             rec["date"], rec["hours"], rec["billable"], rec["activity"]))
                c.commit()
        except Exception as e:  # pragma: no cover
            print(f"[firm_ops] ts insert failed: {e}", flush=True)
            return {"error": "save failed"}
    else:
        _append(_TS_PATH, rec)
    return {"ok": True, "id": rec["id"], "entry": rec}


def list_timesheets(owner, engagement_id=None):
    owner = _owner(owner)
    rows = _ts_rows(owner, engagement_id)
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

# Approval hierarchy: an expense is approved by the next role UP. Everyone files & needs
# approval EXCEPT Partner / Senior Partner (top of chain → auto-approved).
APPROVAL_CHAIN = ["junior_consultant", "consultant", "senior_consultant",
                  "engagement_manager", "engagement_director", "partner", "senior_partner"]
NO_APPROVAL_ROLES = {"partner", "senior_partner"}  # "everyone except partner"


def _rank(role):
    return APPROVAL_CHAIN.index(role) if role in APPROVAL_CHAIN else 0


def _approver_for(submit_role):
    """Next level up approves; partner+ need no approval."""
    if submit_role in NO_APPROVAL_ROLES:
        return None
    i = _rank(submit_role)
    return APPROVAL_CHAIN[i + 1] if i + 1 < len(APPROVAL_CHAIN) else "senior_partner"


def can_approve(approver_role, required_role):
    """An approver can sign off if their rank is >= the required approver rank."""
    if not required_role:
        return False
    return _rank(approver_role) >= _rank(required_role)


# ---------------------------------------------------------------------------
# OCR — receipt parsing (AWS Textract at deploy; deterministic text parser now)
# ---------------------------------------------------------------------------
import re as _re

_CAT_KW = {
    "Travel": ["uber", "ola", "flight", "air", "indigo", "taxi", "cab", "train", "irctc", "fuel", "petrol", "toll"],
    "Accommodation": ["hotel", "oyo", "stay", "resort", "lodge", "room", "marriott", "taj"],
    "Meals": ["restaurant", "cafe", "food", "swiggy", "zomato", "meal", "lunch", "dinner", "coffee"],
    "Software/Tools": ["aws", "saas", "subscription", "software", "license", "google", "microsoft", "zoom"],
}


def _textract(image_b64):
    """Best-effort AWS Textract OCR; returns plain text or None. Guarded (boto3 optional)."""
    try:
        import base64
        import boto3  # type: ignore
        region = os.getenv("AWS_REGION", "").strip() or None
        client = boto3.client("textract", region_name=region)
        resp = client.detect_document_text(Document={"Bytes": base64.b64decode(image_b64)})
        lines = [b["Text"] for b in resp.get("Blocks", []) if b.get("BlockType") == "LINE"]
        return "\n".join(lines)
    except Exception as e:  # pragma: no cover
        print(f"[firm_ops] textract unavailable: {str(e)[:120]}", flush=True)
        return None


def ocr_receipt(body):
    """Extract amount / date / merchant / category from a receipt.
    Accepts image_base64 (-> Textract at deploy) or pre-extracted text. Always returns a
    best-effort parse so the user can confirm/edit before submitting."""
    body = body or {}
    text = (body.get("text") or "").strip()
    engine = "text"
    if not text and body.get("image_base64"):
        ocr = _textract(body["image_base64"])
        if ocr:
            text, engine = ocr, "textract"
        else:
            return {"ok": False, "engine": "none", "needs_provider": True,
                    "note": "Receipt stored; automatic OCR (AWS Textract) is enabled at deploy. Enter the amount manually for now."}
    if not text:
        return {"ok": False, "error": "Provide a receipt image or its text."}
    # amount: largest currency-like number
    amounts = []
    for m in _re.findall(r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*\.?[0-9]{0,2})", text, flags=_re.I):
        try:
            amounts.append(float(m.replace(",", "")))
        except Exception:
            pass
    if not amounts:
        for m in _re.findall(r"\b([0-9][0-9,]{2,}\.?[0-9]{0,2})\b", text):
            try:
                amounts.append(float(m.replace(",", "")))
            except Exception:
                pass
    amount = max(amounts) if amounts else None
    # date
    dm = _re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", text)
    date = dm.group(1) if dm else ""
    # merchant: first meaningful line
    merchant = next((ln.strip() for ln in text.splitlines() if len(ln.strip()) > 2), "")[:60]
    # category
    tl = text.lower()
    category = next((c for c, kws in _CAT_KW.items() if any(k in tl for k in kws)), "Other")
    return {"ok": True, "engine": engine, "amount": amount, "date": date,
            "merchant": merchant, "category": category, "raw_text": text[:1000]}


def add_expense(body):
    owner = _owner(body.get("owner"))
    submit_role = (body.get("role") or "consultant").strip()
    approver_role = _approver_for(submit_role)
    rec = {
        "id": hashlib.sha1(f"ex:{owner}:{time.time()}".encode()).hexdigest()[:12],
        "owner": owner, "ts": int(time.time()),
        "engagement_id": (body.get("engagement_id") or "").strip(),
        "consultant": (body.get("consultant") or "").strip() or "—",
        "category": (body.get("category") or "Other").strip(),
        "amount": _num(body.get("amount")),
        "billable": bool(body.get("billable", True)),
        "submit_role": submit_role,
        "approver_role": approver_role or "",
        # everyone needs approval EXCEPT partner / senior partner (auto-approved)
        "status": "Approved" if approver_role is None else "Submitted",
        "note": (body.get("note") or "").strip(),
        "receipt": (body.get("receipt") or "")[:200],   # receipt filename / ref (image stored client-side / S3 at deploy)
        "ocr_engine": (body.get("ocr_engine") or "").strip(),
    }
    if rec["amount"] <= 0:
        return {"error": "amount must be > 0"}
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor() as cur:
                cur.execute("""INSERT INTO expenses (id,owner,ts,engagement_id,consultant,category,amount,billable,status,note,submit_role,approver_role,receipt,ocr_engine)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING""",
                            (rec["id"], rec["owner"], rec["ts"], rec["engagement_id"], rec["consultant"],
                             rec["category"], rec["amount"], rec["billable"], rec["status"], rec["note"],
                             rec["submit_role"], rec["approver_role"], rec["receipt"], rec["ocr_engine"]))
                c.commit()
        except Exception as e:  # pragma: no cover
            print(f"[firm_ops] ex insert failed: {e}", flush=True)
            return {"error": "save failed"}
    else:
        _append(_EX_PATH, rec)
    return {"ok": True, "id": rec["id"], "expense": rec}


def set_expense_status(body):
    owner = _owner(body.get("owner"))
    eid = (body.get("id") or "").strip()
    status = (body.get("status") or "Approved").strip()
    approver_role = (body.get("approver_role") or "").strip()
    # Authorisation: the approver's rank must be >= the expense's required approver rank.
    if approver_role:
        target = next((e for e in _ex_rows(owner) if e.get("id") == eid), None)
        if target and target.get("approver_role") and not can_approve(approver_role, target.get("approver_role")):
            return {"ok": False, "error": f"{approver_role.replace('_',' ')} is not authorised to approve this expense (needs {target['approver_role'].replace('_',' ')} or above)."}
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor() as cur:
                cur.execute("UPDATE expenses SET status=%s WHERE id=%s AND owner=%s", (status, eid, owner))
                changed = cur.rowcount
                c.commit()
            return {"ok": bool(changed), "changed": changed}
        except Exception as e:  # pragma: no cover
            print(f"[firm_ops] ex status failed: {e}", flush=True)
            return {"ok": False}
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
    rows = _ex_rows(owner, engagement_id)
    bill = sum(r["amount"] for r in rows if r.get("billable"))
    nonbill = sum(r["amount"] for r in rows if not r.get("billable"))
    return {"owner": owner, "count": len(rows), "expenses": rows[:200], "categories": EXPENSE_CATEGORIES,
            "billable_amount": bill, "billable_label": _inr(bill),
            "nonbillable_amount": nonbill, "nonbillable_label": _inr(nonbill),
            "total_amount": bill + nonbill, "total_label": _inr(bill + nonbill),
            "pending_approval": sum(1 for r in rows if r.get("status") == "Submitted")}


def approvals(owner, role):
    """Expenses awaiting approval that this role is authorised to sign off (hierarchy)."""
    owner = _owner(owner)
    role = (role or "").strip()
    queue = [e for e in _ex_rows(owner)
             if e.get("status") == "Submitted" and can_approve(role, e.get("approver_role"))]
    return {"owner": owner, "role": role, "count": len(queue), "queue": queue,
            "can_approve": role not in ("junior_consultant",) and bool(role)}


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
            "backend": "postgres" if _USE_DB else "jsonl",
            "approval_chain": APPROVAL_CHAIN, "no_approval_roles": list(NO_APPROVAL_ROLES),
            "ocr": "AWS Textract at deploy; deterministic text parser now",
            "endpoints": ["GET /firm/cockpit?owner=", "GET /firm/rbac", "GET|POST /firm/timesheets",
                          "GET|POST /firm/expenses", "POST /firm/expenses/status", "POST /firm/expenses/ocr",
                          "GET /firm/approvals?owner=&role="]}


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
    # approval workflow: consultant expense needs senior_consultant+; jr can't approve; partner auto-approved
    ce = add_expense({"owner": o, "role": "consultant", "category": "Travel", "amount": 1200, "billable": True})
    deny = set_expense_status({"owner": o, "id": ce["id"], "status": "Approved", "approver_role": "junior_consultant"})
    allow = set_expense_status({"owner": o, "id": ce["id"], "status": "Approved", "approver_role": "engagement_manager"})
    pe = add_expense({"owner": o, "role": "partner", "category": "Meals", "amount": 800})
    cases.append(("approval_workflow", ce["expense"]["approver_role"] == "senior_consultant"
                  and deny.get("ok") is False and allow.get("ok") is True
                  and pe["expense"]["status"] == "Approved"))
    aq = approvals(o, "engagement_director")
    cases.append(("approvals_queue", "queue" in aq and isinstance(aq["count"], int)))
    # OCR text parser extracts amount + category
    oc = ocr_receipt({"text": "UBER INDIA\nTrip fare\nDate 14/06/2026\nTotal ₹1,250.00"})
    cases.append(("ocr", oc.get("ok") and oc.get("amount") == 1250.0 and oc.get("category") == "Travel"))
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
