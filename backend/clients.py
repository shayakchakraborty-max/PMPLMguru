"""
clients.py — Client master data + Contract management for the consulting-firm ERP.

  * Clients — the master record (name, industry, GSTIN/PAN, contacts, billing terms,
    currency) every engagement, contract and invoice references.
  * Contracts — MSA / SOW / Engagement Letter / NDA / Retainer per client, with fee
    model, contract value, dates and signature status. Stores the engagement-letter
    text and an emails log (correspondence) so the letter mails live with the contract.
  * Billing wiring — billing_summary() rolls contracts into the firm finance view:
    signed contract value, pipeline (draft/sent), by-client and by-fee-model; each
    contract optionally links to an engagement_id so estimated vs contracted reconciles.

Same Postgres-or-JSONL seam as engagement_store (reuses its connection; tables auto-
created). Owner-scoped (Cognito-ready). Endpoints in main.py: GET/POST /clients,
GET /client, POST /client/update, GET/POST /contracts, GET /contract,
POST /contract/status, POST /contract/email, GET /billing/summary.
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
_CL_PATH = os.path.join(_DATA_DIR, "clients.jsonl")
_CT_PATH = os.path.join(_DATA_DIR, "contracts.jsonl")

_USE_DB = bool(_ES and getattr(_ES, "_USE_DB", False))
_RDC = getattr(_ES, "_RDC", None) if _ES else None

CONTRACT_TYPES = ["MSA", "SOW", "Engagement Letter", "NDA", "Retainer"]
FEE_MODELS = ["Time & Materials", "Fixed Fee", "Monthly Retainer", "Outcome-linked (capped)"]
CONTRACT_STATUS = ["Draft", "Sent", "Signed", "Active", "Closed"]

_DDL = """
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY, owner TEXT NOT NULL, ts BIGINT, name TEXT, industry TEXT, sector TEXT,
    gstin TEXT, pan TEXT, address TEXT, contacts JSONB, billing_terms TEXT, currency TEXT,
    status TEXT, notes TEXT);
CREATE INDEX IF NOT EXISTS idx_clients_owner ON clients (owner);
CREATE TABLE IF NOT EXISTS contracts (
    id TEXT PRIMARY KEY, owner TEXT NOT NULL, ts BIGINT, client_id TEXT, engagement_id TEXT,
    type TEXT, title TEXT, fee_model TEXT, contract_value DOUBLE PRECISION, currency TEXT,
    start_date TEXT, end_date TEXT, status TEXT, signed_date TEXT, letter_text TEXT,
    emails JSONB, notes TEXT);
CREATE INDEX IF NOT EXISTS idx_contracts_owner ON contracts (owner, client_id);
"""

if _USE_DB:
    try:
        with _ES._connect() as _c, _c.cursor() as _cur:
            _cur.execute(_DDL)
            _c.commit()
        print("[clients] Postgres backend active (clients, contracts).", flush=True)
    except Exception as e:  # pragma: no cover
        print(f"[clients] Postgres init failed ({e}); using JSONL.", flush=True)
        _USE_DB = False


# ---------------------------------------------------------------------------
def _owner(o):
    return (o or "").strip() or "demo"


def _num(v, d=0):
    try:
        return float(str(v).replace(",", "").replace("₹", "").strip())
    except Exception:
        return d


def _inr(n):
    return f"₹{n:,.0f}"


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
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return True


def _rewrite(path, rows):
    if not _ensure_dir():
        return False
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return True


def _as_obj(v):
    if isinstance(v, (dict, list)) or v is None:
        return v
    try:
        return json.loads(v)
    except Exception:
        return v


# ---------------------------------------------------------------------------
# CLIENTS
# ---------------------------------------------------------------------------
def add_client(body):
    owner = _owner(body.get("owner"))
    name = (body.get("name") or "").strip()
    if not name:
        return {"error": "client name required"}
    rec = {"id": hashlib.sha1(f"cl:{owner}:{name}:{time.time()}".encode()).hexdigest()[:12],
           "owner": owner, "ts": int(time.time()), "name": name,
           "industry": (body.get("industry") or "").strip(), "sector": (body.get("sector") or "").strip(),
           "gstin": (body.get("gstin") or "").strip(), "pan": (body.get("pan") or "").strip(),
           "address": (body.get("address") or "").strip(),
           "contacts": body.get("contacts") or [],
           "billing_terms": (body.get("billing_terms") or "Net 30").strip(),
           "currency": (body.get("currency") or "INR").strip(),
           "status": (body.get("status") or "Active").strip(), "notes": (body.get("notes") or "").strip()}
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor() as cur:
                cur.execute("""INSERT INTO clients (id,owner,ts,name,industry,sector,gstin,pan,address,contacts,billing_terms,currency,status,notes)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (rec["id"], owner, rec["ts"], name, rec["industry"], rec["sector"], rec["gstin"], rec["pan"],
                             rec["address"], json.dumps(rec["contacts"]), rec["billing_terms"], rec["currency"], rec["status"], rec["notes"]))
                c.commit()
        except Exception as e:  # pragma: no cover
            print(f"[clients] add failed: {e}", flush=True); return {"error": "save failed"}
    else:
        _append(_CL_PATH, rec)
    return {"ok": True, "id": rec["id"], "client": rec}


def _client_rows(owner):
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor(cursor_factory=_RDC) as cur:
                cur.execute("SELECT * FROM clients WHERE owner=%s ORDER BY ts DESC", (owner,))
                return [{**dict(r), "contacts": _as_obj(r["contacts"])} for r in cur.fetchall()]
        except Exception as e:  # pragma: no cover
            print(f"[clients] read failed: {e}", flush=True); return []
    rows = [r for r in _read(_CL_PATH) if r.get("owner") == owner]
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return rows


def list_clients(owner):
    owner = _owner(owner)
    rows = _client_rows(owner)
    return {"owner": owner, "count": len(rows), "clients": rows}


def get_client(owner, cid):
    owner = _owner(owner)
    c = next((x for x in _client_rows(owner) if x.get("id") == cid), None)
    if not c:
        return {"error": "not found"}
    contracts = [x for x in _contract_rows(owner) if x.get("client_id") == cid]
    return {"client": c, "contracts": contracts, "contract_count": len(contracts)}


def update_client(body):
    owner = _owner(body.get("owner"))
    cid = (body.get("id") or "").strip()
    fields = {k: body[k] for k in ("name", "industry", "sector", "gstin", "pan", "address", "billing_terms", "currency", "status", "notes") if k in body}
    if "contacts" in body:
        fields["contacts"] = body["contacts"]
    if _USE_DB and fields:
        try:
            sets, vals = [], []
            for k, v in fields.items():
                sets.append(f"{k}=%s"); vals.append(json.dumps(v) if k == "contacts" else v)
            vals += [cid, owner]
            with _ES._connect() as c, c.cursor() as cur:
                cur.execute(f"UPDATE clients SET {', '.join(sets)} WHERE id=%s AND owner=%s", vals)
                changed = cur.rowcount; c.commit()
            return {"ok": bool(changed)}
        except Exception as e:  # pragma: no cover
            print(f"[clients] update failed: {e}", flush=True); return {"ok": False}
    rows = _read(_CL_PATH); changed = 0
    for r in rows:
        if r.get("id") == cid and r.get("owner") == owner:
            r.update(fields); changed += 1
    if changed:
        _rewrite(_CL_PATH, rows)
    return {"ok": bool(changed)}


# ---------------------------------------------------------------------------
# CONTRACTS (+ engagement-letter emails)
# ---------------------------------------------------------------------------
def add_contract(body):
    owner = _owner(body.get("owner"))
    rec = {"id": hashlib.sha1(f"ct:{owner}:{time.time()}".encode()).hexdigest()[:12],
           "owner": owner, "ts": int(time.time()),
           "client_id": (body.get("client_id") or "").strip(),
           "engagement_id": (body.get("engagement_id") or "").strip(),
           "type": (body.get("type") or "SOW").strip(),
           "title": (body.get("title") or "").strip() or (body.get("type") or "SOW"),
           "fee_model": (body.get("fee_model") or "Time & Materials").strip(),
           "contract_value": _num(body.get("contract_value")),
           "currency": (body.get("currency") or "INR").strip(),
           "start_date": (body.get("start_date") or "").strip(), "end_date": (body.get("end_date") or "").strip(),
           "status": (body.get("status") or "Draft").strip(), "signed_date": (body.get("signed_date") or "").strip(),
           "letter_text": (body.get("letter_text") or "").strip(),
           "emails": body.get("emails") or [], "notes": (body.get("notes") or "").strip()}
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor() as cur:
                cur.execute("""INSERT INTO contracts (id,owner,ts,client_id,engagement_id,type,title,fee_model,contract_value,currency,start_date,end_date,status,signed_date,letter_text,emails,notes)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (rec["id"], owner, rec["ts"], rec["client_id"], rec["engagement_id"], rec["type"], rec["title"],
                             rec["fee_model"], rec["contract_value"], rec["currency"], rec["start_date"], rec["end_date"],
                             rec["status"], rec["signed_date"], rec["letter_text"], json.dumps(rec["emails"]), rec["notes"]))
                c.commit()
        except Exception as e:  # pragma: no cover
            print(f"[clients] contract add failed: {e}", flush=True); return {"error": "save failed"}
    else:
        _append(_CT_PATH, rec)
    return {"ok": True, "id": rec["id"], "contract": rec}


def _contract_rows(owner, client_id=None):
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor(cursor_factory=_RDC) as cur:
                if client_id:
                    cur.execute("SELECT * FROM contracts WHERE owner=%s AND client_id=%s ORDER BY ts DESC", (owner, client_id))
                else:
                    cur.execute("SELECT * FROM contracts WHERE owner=%s ORDER BY ts DESC", (owner,))
                return [{**dict(r), "emails": _as_obj(r["emails"])} for r in cur.fetchall()]
        except Exception as e:  # pragma: no cover
            print(f"[clients] contract read failed: {e}", flush=True); return []
    rows = [r for r in _read(_CT_PATH) if r.get("owner") == owner and (not client_id or r.get("client_id") == client_id)]
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return rows


def list_contracts(owner, client_id=None):
    owner = _owner(owner)
    rows = _contract_rows(owner, client_id)
    names = {c["id"]: c.get("name") for c in _client_rows(owner)}
    for r in rows:
        r["client_name"] = names.get(r.get("client_id"), "—")
        r["value_label"] = _inr(r.get("contract_value") or 0)
    return {"owner": owner, "count": len(rows), "contracts": rows,
            "types": CONTRACT_TYPES, "fee_models": FEE_MODELS, "statuses": CONTRACT_STATUS}


def get_contract(owner, ctid):
    owner = _owner(owner)
    c = next((x for x in _contract_rows(owner) if x.get("id") == ctid), None)
    return {"contract": c} if c else {"error": "not found"}


def set_contract_status(body):
    owner = _owner(body.get("owner"))
    ctid = (body.get("id") or "").strip()
    status = (body.get("status") or "Signed").strip()
    signed = (body.get("signed_date") or "").strip()
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor() as cur:
                cur.execute("UPDATE contracts SET status=%s, signed_date=COALESCE(NULLIF(%s,''), signed_date) WHERE id=%s AND owner=%s", (status, signed, ctid, owner))
                changed = cur.rowcount; c.commit()
            return {"ok": bool(changed)}
        except Exception as e:  # pragma: no cover
            return {"ok": False}
    rows = _read(_CT_PATH); changed = 0
    for r in rows:
        if r.get("id") == ctid and r.get("owner") == owner:
            r["status"] = status
            if signed:
                r["signed_date"] = signed
            changed += 1
    if changed:
        _rewrite(_CT_PATH, rows)
    return {"ok": bool(changed)}


def add_email(body):
    """Store an engagement-letter / contract email against the contract."""
    owner = _owner(body.get("owner"))
    ctid = (body.get("id") or body.get("contract_id") or "").strip()
    email = {"from": (body.get("from") or "").strip(), "to": (body.get("to") or "").strip(),
             "subject": (body.get("subject") or "").strip(), "body": (body.get("body") or "").strip(),
             "date": (body.get("date") or "").strip(), "ts": int(time.time())}
    if not email["subject"] and not email["body"]:
        return {"error": "email subject or body required"}
    rows = _contract_rows(owner)
    target = next((r for r in rows if r.get("id") == ctid), None)
    if not target:
        return {"error": "contract not found"}
    emails = (_as_obj(target.get("emails")) or []) + [email]
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor() as cur:
                cur.execute("UPDATE contracts SET emails=%s WHERE id=%s AND owner=%s", (json.dumps(emails), ctid, owner))
                c.commit()
            return {"ok": True, "email_count": len(emails)}
        except Exception as e:  # pragma: no cover
            return {"ok": False}
    allrows = _read(_CT_PATH)
    for r in allrows:
        if r.get("id") == ctid and r.get("owner") == owner:
            r["emails"] = emails
    _rewrite(_CT_PATH, allrows)
    return {"ok": True, "email_count": len(emails)}


# ---------------------------------------------------------------------------
# BILLING WIRING — contracts roll into the firm finance view
# ---------------------------------------------------------------------------
_SIGNED = {"Signed", "Active", "Closed"}


def billing_summary(owner):
    owner = _owner(owner)
    contracts = _contract_rows(owner)
    clients = {c["id"]: c.get("name") for c in _client_rows(owner)}
    signed_value = sum(c.get("contract_value") or 0 for c in contracts if c.get("status") in _SIGNED)
    pipeline_value = sum(c.get("contract_value") or 0 for c in contracts if c.get("status") in ("Draft", "Sent"))
    by_client, by_fee, by_status = {}, {}, {}
    for c in contracts:
        v = c.get("contract_value") or 0
        cn = clients.get(c.get("client_id"), "—")
        by_client[cn] = by_client.get(cn, 0) + v
        by_fee[c.get("fee_model", "—")] = by_fee.get(c.get("fee_model", "—"), 0) + v
        by_status[c.get("status", "Draft")] = by_status.get(c.get("status", "Draft"), 0) + 1
    return {
        "owner": owner, "contracts": len(contracts), "clients": len(clients),
        "signed_contract_value": signed_value, "signed_label": _inr(signed_value),
        "pipeline_value": pipeline_value, "pipeline_label": _inr(pipeline_value),
        "by_client": [{"client": k, "value": v, "label": _inr(v)} for k, v in sorted(by_client.items(), key=lambda x: x[1], reverse=True)],
        "by_fee_model": [{"fee_model": k, "value": v, "label": _inr(v)} for k, v in sorted(by_fee.items(), key=lambda x: x[1], reverse=True)],
        "by_status": by_status,
        "linked_engagements": sum(1 for c in contracts if c.get("engagement_id")),
    }


def meta():
    return {"contract_types": CONTRACT_TYPES, "fee_models": FEE_MODELS, "statuses": CONTRACT_STATUS,
            "backend": "postgres" if _USE_DB else "jsonl",
            "endpoints": ["GET/POST /clients", "GET /client", "POST /client/update", "GET/POST /contracts",
                          "GET /contract", "POST /contract/status", "POST /contract/email", "GET /billing/summary"]}


def run_clients_tests():
    cases = []
    o = "__cl_test__"
    # cleanup
    for r in _read(_CL_PATH):
        pass
    cl = add_client({"owner": o, "name": "Acme Mfg", "industry": "Manufacturing", "gstin": "27ABCDE1234F1Z5",
                     "contacts": [{"name": "R. Rao", "role": "CFO", "email": "rao@acme.in"}], "billing_terms": "Net 45"})
    cases.append(("add_client", cl.get("ok") and cl["client"]["billing_terms"] == "Net 45"))
    lc = list_clients(o)
    cases.append(("list_clients", lc["count"] >= 1 and any(c["name"] == "Acme Mfg" for c in lc["clients"])))
    ct = add_contract({"owner": o, "client_id": cl["id"], "type": "Engagement Letter", "fee_model": "Fixed Fee",
                       "contract_value": 1500000, "engagement_id": "E1", "letter_text": "Dear client, we are pleased..."})
    cases.append(("add_contract", ct.get("ok") and ct["contract"]["contract_value"] == 1500000))
    em = add_email({"owner": o, "id": ct["id"], "subject": "Engagement Letter — Acme", "body": "Please find attached...", "from": "partner@firm.in", "to": "rao@acme.in"})
    cases.append(("store_email", em.get("ok") and em["email_count"] == 1))
    set_contract_status({"owner": o, "id": ct["id"], "status": "Signed", "signed_date": "2026-06-18"})
    bs = billing_summary(o)
    cases.append(("billing_wired", bs["signed_contract_value"] == 1500000 and bs["linked_engagements"] >= 1
                  and any(x["client"] == "Acme Mfg" for x in bs["by_client"])))
    gc = get_client(o, cl["id"])
    cases.append(("client_360", gc["contract_count"] >= 1))
    # cleanup test rows
    for path in (_CL_PATH, _CT_PATH):
        _rewrite(path, [r for r in _read(path) if r.get("owner") != o])
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    print(json.dumps(run_clients_tests(), indent=2))
