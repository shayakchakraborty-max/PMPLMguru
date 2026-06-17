"""
engagement_store.py — server-side persistence for the Engagement Digital Twin.

Dual backend behind ONE public contract (save/list/get/delete/portfolio):
  * Postgres (Aurora / Railway PG / RDS) when DATABASE_URL is set AND psycopg2 is
    installed — the production path; table auto-created on first use.
  * JSONL under BRAIN_DATA_DIR otherwise — the zero-infra fallback (works today on
    Railway without a database, and locally).

So the migration is a no-op deploy decision: set DATABASE_URL and the twin moves to
Postgres automatically; unset it and it falls back to the file store. Same API, same
owner-scoping (an anon device id today — the seam where a Cognito `sub` slots in),
same portfolio analytics. This is also the seam where pgvector RAG will live later.

Endpoints (main.py): GET /engagements, GET /engagement, GET /portfolio,
POST /engagements/delete (+ /engagements/meta, /engagements/tests).
"""

import os
import json
import time
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.getenv("BRAIN_DATA_DIR", "").strip() or os.path.join(_HERE, "brain_data")
_PATH = os.path.join(_DATA_DIR, "twin_engagements.jsonl")
_DB_URL = os.getenv("DATABASE_URL", "").strip()

# ---- optional Postgres driver (psycopg2); degrade to JSONL if absent/unreachable ----
_pg = None
_USE_DB = False
if _DB_URL:
    try:
        import psycopg2 as _pg  # type: ignore
        from psycopg2.extras import RealDictCursor as _RDC  # type: ignore
    except Exception as e:  # pragma: no cover
        print(f"[engagement_store] DATABASE_URL set but psycopg2 unavailable ({e}); using JSONL.", flush=True)
        _pg = None


def _connect():
    # Railway/Heroku-style URLs sometimes use postgres://; psycopg2 wants postgresql://
    url = _DB_URL.replace("postgres://", "postgresql://", 1) if _DB_URL.startswith("postgres://") else _DB_URL
    return _pg.connect(url, connect_timeout=5)


_DDL = """
CREATE TABLE IF NOT EXISTS engagements (
    id                TEXT PRIMARY KEY,
    owner             TEXT NOT NULL,
    ts                BIGINT NOT NULL,
    title             TEXT,
    sector            TEXT,
    posture           TEXT,
    agents            JSONB,
    advisors          JSONB,
    risk_titles       JSONB,
    n_recommendations INTEGER,
    n_risks           INTEGER,
    report            JSONB,
    deleted           BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_engagements_owner ON engagements (owner, deleted, ts DESC);
"""

if _pg:
    try:
        with _connect() as _c:
            with _c.cursor() as _cur:
                _cur.execute(_DDL)
            _c.commit()
        _USE_DB = True
        print("[engagement_store] Postgres backend active.", flush=True)
    except Exception as e:  # pragma: no cover
        print(f"[engagement_store] Postgres init failed ({e}); using JSONL.", flush=True)
        _USE_DB = False


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _ensure_dir():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        return True
    except Exception as e:  # pragma: no cover
        print(f"[engagement_store] cannot create {_DATA_DIR}: {e}", flush=True)
        return False


def _owner(o):
    o = (o or "").strip()
    return o or "demo"


def _index(report):
    """Compact, list-friendly projection of a full engagement report."""
    diag = report.get("diagnosis") or {}
    return {
        "title": report.get("title", "Engagement"),
        "sector": report.get("sector"),
        "posture": diag.get("posture"),
        "engagement_id": report.get("engagement_id"),
        "agents": [w.get("agent") for w in (report.get("workstreams") or [])],
        "advisors": [a.get("advisor") for a in (report.get("agents_engaged") or []) if a.get("advisor")],
        "risk_titles": [r.get("risk") for r in (report.get("risks") or [])][:8],
        "n_recommendations": len(report.get("recommendations") or []),
        "n_risks": len(report.get("risks") or []),
    }


def _as_obj(v):
    """psycopg2 usually returns jsonb as Python objects, but be defensive."""
    if isinstance(v, (dict, list)) or v is None:
        return v
    try:
        return json.loads(v)
    except Exception:
        return v


_POSTURE_ORDER = ["Critical", "Elevated", "Watch", "Stable"]


# ---------------------------------------------------------------------------
# JSONL backend
# ---------------------------------------------------------------------------
def _jsonl_read():
    out = []
    try:
        if os.path.exists(_PATH):
            with open(_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            out.append(json.loads(line))
                        except Exception:
                            continue
    except Exception as e:  # pragma: no cover
        print(f"[engagement_store] read failed: {e}", flush=True)
    return out


def _jsonl_save(owner, report, ts, sid):
    if not _ensure_dir():
        return None
    record = {"id": sid, "owner": owner, "ts": ts, **_index(report), "report": report}
    try:
        with open(_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return sid
    except Exception as e:  # pragma: no cover
        print(f"[engagement_store] save failed: {e}", flush=True)
        return None


# ---------------------------------------------------------------------------
# Public API (dispatches to Postgres or JSONL)
# ---------------------------------------------------------------------------
def save_engagement(owner, report):
    """Persist one orchestrated engagement (the digital twin). Best-effort; never raises."""
    if not report or report.get("error"):
        return None
    owner = _owner(owner)
    ts = int(time.time())
    sid = hashlib.sha1(f"{owner}:{report.get('engagement_id','')}:{ts}".encode()).hexdigest()[:12]
    if _USE_DB:
        ix = _index(report)
        try:
            with _connect() as c, c.cursor() as cur:
                cur.execute(
                    """INSERT INTO engagements
                       (id, owner, ts, title, sector, posture, agents, advisors, risk_titles, n_recommendations, n_risks, report, deleted)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE)
                       ON CONFLICT (id) DO NOTHING""",
                    (sid, owner, ts, ix["title"], ix["sector"], ix["posture"],
                     json.dumps(ix["agents"]), json.dumps(ix["advisors"]), json.dumps(ix["risk_titles"]),
                     ix["n_recommendations"], ix["n_risks"], json.dumps(report)))
                c.commit()
            return sid
        except Exception as e:  # pragma: no cover
            print(f"[engagement_store] db save failed: {e}", flush=True)
            return None
    return _jsonl_save(owner, report, ts, sid)


def list_engagements(owner, limit=50):
    owner = _owner(owner)
    if _USE_DB:
        try:
            with _connect() as c, c.cursor(cursor_factory=_RDC) as cur:
                cur.execute(
                    """SELECT id, ts, title, sector, posture, agents, n_recommendations, n_risks
                       FROM engagements WHERE owner=%s AND NOT deleted ORDER BY ts DESC LIMIT %s""",
                    (owner, limit))
                rows = cur.fetchall()
                cur.execute("SELECT COUNT(*) AS n FROM engagements WHERE owner=%s AND NOT deleted", (owner,))
                total = cur.fetchone()["n"]
            return {"owner": owner, "count": total,
                    "engagements": [{**dict(r), "agents": _as_obj(r["agents"])} for r in rows]}
        except Exception as e:  # pragma: no cover
            print(f"[engagement_store] db list failed: {e}", flush=True)
            return {"owner": owner, "count": 0, "engagements": []}
    rows = [r for r in _jsonl_read() if r.get("owner") == owner and not r.get("_deleted")]
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    out = [{k: r.get(k) for k in ("id", "ts", "title", "sector", "posture", "agents", "n_recommendations", "n_risks")} for r in rows[:limit]]
    return {"owner": owner, "count": len(rows), "engagements": out}


def get_engagement(owner, sid):
    owner = _owner(owner)
    if _USE_DB:
        try:
            with _connect() as c, c.cursor(cursor_factory=_RDC) as cur:
                cur.execute("SELECT id, ts, report FROM engagements WHERE id=%s AND owner=%s AND NOT deleted", (sid, owner))
                r = cur.fetchone()
            if r:
                return {"id": r["id"], "ts": r["ts"], "report": _as_obj(r["report"])}
            return {"error": "not found"}
        except Exception as e:  # pragma: no cover
            print(f"[engagement_store] db get failed: {e}", flush=True)
            return {"error": "lookup failed"}
    for r in _jsonl_read():
        if r.get("id") == sid and r.get("owner") == owner and not r.get("_deleted"):
            return {"id": sid, "ts": r.get("ts"), "report": r.get("report")}
    return {"error": "not found"}


def delete_engagement(owner, sid):
    owner = _owner(owner)
    if _USE_DB:
        try:
            with _connect() as c, c.cursor() as cur:
                cur.execute("UPDATE engagements SET deleted=TRUE WHERE id=%s AND owner=%s", (sid, owner))
                removed = cur.rowcount
                c.commit()
            return {"ok": True, "removed": removed}
        except Exception as e:  # pragma: no cover
            print(f"[engagement_store] db delete failed: {e}", flush=True)
            return {"ok": False}
    rows = _jsonl_read()
    kept, removed = [], 0
    for r in rows:
        if r.get("id") == sid and r.get("owner") == owner:
            removed += 1
            continue
        kept.append(r)
    if removed and _ensure_dir():
        try:
            with open(_PATH, "w", encoding="utf-8") as f:
                for r in kept:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        except Exception as e:  # pragma: no cover
            print(f"[engagement_store] delete failed: {e}", flush=True)
            return {"ok": False}
    return {"ok": True, "removed": removed}


def portfolio(owner):
    """Cross-engagement analytics across an owner's saved digital twins."""
    owner = _owner(owner)
    if _USE_DB:
        try:
            with _connect() as c, c.cursor(cursor_factory=_RDC) as cur:
                cur.execute("SELECT sector, posture, advisors, risk_titles FROM engagements WHERE owner=%s AND NOT deleted", (owner,))
                rows = [dict(r) for r in cur.fetchall()]
        except Exception as e:  # pragma: no cover
            print(f"[engagement_store] db portfolio failed: {e}", flush=True)
            rows = []
    else:
        rows = [r for r in _jsonl_read() if r.get("owner") == owner and not r.get("_deleted")]

    n = len(rows)
    posture = {p: 0 for p in _POSTURE_ORDER}
    by_sector, agent_freq, risk_freq = {}, {}, {}
    for r in rows:
        p = r.get("posture")
        if p in posture:
            posture[p] += 1
        sec = r.get("sector") or "Unknown"
        by_sector[sec] = by_sector.get(sec, 0) + 1
        for a in (_as_obj(r.get("advisors")) or []):
            agent_freq[a] = agent_freq.get(a, 0) + 1
        for rk in (_as_obj(r.get("risk_titles")) or []):
            key = (rk or "")[:60]
            if key:
                risk_freq[key] = risk_freq.get(key, 0) + 1
    top_risks = sorted(risk_freq.items(), key=lambda x: x[1], reverse=True)[:6]
    top_advisors = sorted(agent_freq.items(), key=lambda x: x[1], reverse=True)[:6]
    return {
        "owner": owner, "total_engagements": n,
        "posture_mix": posture,
        "at_risk": posture["Critical"] + posture["Elevated"],
        "by_sector": dict(sorted(by_sector.items(), key=lambda x: x[1], reverse=True)),
        "recurring_risks": [{"risk": k, "count": v} for k, v in top_risks],
        "top_advisors": [{"advisor": k, "count": v} for k, v in top_advisors],
        "backend": "postgres" if _USE_DB else "jsonl",
        "persisted": _USE_DB or os.path.exists(_PATH),
        "data_dir": None if _USE_DB else _DATA_DIR,
    }


def meta():
    return {"backend": "postgres" if _USE_DB else "jsonl",
            "db_configured": bool(_DB_URL), "driver_available": bool(_pg),
            "scope": "owner (Cognito-sub-ready)",
            "data_dir": None if _USE_DB else _DATA_DIR,
            "persisted": _USE_DB or os.path.exists(_PATH),
            "endpoints": ["GET /engagements?owner=", "GET /engagement?owner=&id=", "GET /portfolio?owner=", "POST /engagements/delete"]}


def run_store_tests():
    cases = []
    o = "__test_owner__"
    for r in list_engagements(o)["engagements"]:
        delete_engagement(o, r["id"])
    rep = {"engagement_id": "abc123", "title": "Test Co", "sector": "Retail Trade",
           "diagnosis": {"posture": "Critical"}, "workstreams": [{"agent": "cfo_finance"}],
           "agents_engaged": [{"agent": "cfo_finance", "advisor": "AI CFO Advisor"}],
           "risks": [{"risk": "Cash runway under 3 months"}], "recommendations": [{"text": "x"}]}
    sid = save_engagement(o, rep)
    cases.append(("save", bool(sid)))
    lst = list_engagements(o)
    cases.append(("list", lst["count"] >= 1 and any(e["title"] == "Test Co" for e in lst["engagements"])))
    got = get_engagement(o, sid)
    cases.append(("get", got.get("report", {}).get("title") == "Test Co"))
    pf = portfolio(o)
    cases.append(("portfolio", pf["total_engagements"] >= 1 and pf["posture_mix"]["Critical"] >= 1 and pf["at_risk"] >= 1))
    before = list_engagements(o)["count"]
    delete_engagement(o, sid)
    cases.append(("delete", list_engagements(o)["count"] == before - 1))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases),
                        "backend": "postgres" if _USE_DB else "jsonl"},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    print(json.dumps(run_store_tests(), indent=2))
