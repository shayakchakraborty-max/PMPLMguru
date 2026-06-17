"""
engagement_store.py — server-side persistence for the Engagement Digital Twin.

Today the Super-Agent (/engage) keeps engagements only in browser localStorage.
This makes the twin a real, server-persisted entity: every orchestrated engagement
is saved, scoped by `owner` (an anonymous device id today — the exact seam where a
Cognito `sub` slots in later), and exposed as a portfolio with cross-engagement
analytics (posture mix, by-sector, recurring risks, agents engaged).

Storage reuses the repo's JSONL-under-BRAIN_DATA_DIR pattern (same as doc_store /
live_brain). It is intentionally swappable for Aurora/Postgres later — the public
functions (save/list/get/delete/portfolio) are the contract; only the _read/_write
internals change. NOTE: BRAIN_DATA_DIR is ephemeral on Railway unless a volume is
mounted there (set BRAIN_DATA_DIR=/data).

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


def _ensure_dir():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        return True
    except Exception as e:  # pragma: no cover
        print(f"[engagement_store] cannot create {_DATA_DIR}: {e}", flush=True)
        return False


def _read():
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


def save_engagement(owner, report):
    """Persist one orchestrated engagement (the digital twin). Best-effort; never raises."""
    if not report or report.get("error") or not _ensure_dir():
        return None
    owner = _owner(owner)
    ts = int(time.time())
    sid = hashlib.sha1(f"{owner}:{report.get('engagement_id','')}:{ts}".encode()).hexdigest()[:12]
    record = {"id": sid, "owner": owner, "ts": ts, **_index(report), "report": report}
    try:
        with open(_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return sid
    except Exception as e:  # pragma: no cover
        print(f"[engagement_store] save failed: {e}", flush=True)
        return None


def list_engagements(owner, limit=50):
    owner = _owner(owner)
    rows = [r for r in _read() if r.get("owner") == owner and not r.get("_deleted")]
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    out = []
    for r in rows[:limit]:
        out.append({k: r.get(k) for k in ("id", "ts", "title", "sector", "posture", "agents", "n_recommendations", "n_risks")})
    return {"owner": owner, "count": len(rows), "engagements": out}


def get_engagement(owner, sid):
    owner = _owner(owner)
    for r in _read():
        if r.get("id") == sid and r.get("owner") == owner and not r.get("_deleted"):
            return {"id": sid, "ts": r.get("ts"), "report": r.get("report")}
    return {"error": "not found"}


def delete_engagement(owner, sid):
    owner = _owner(owner)
    rows = _read()
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


_POSTURE_ORDER = ["Critical", "Elevated", "Watch", "Stable"]


def portfolio(owner):
    """Cross-engagement analytics across an owner's saved digital twins."""
    owner = _owner(owner)
    rows = [r for r in _read() if r.get("owner") == owner and not r.get("_deleted")]
    n = len(rows)
    posture = {p: 0 for p in _POSTURE_ORDER}
    by_sector, agent_freq, risk_freq = {}, {}, {}
    for r in rows:
        p = r.get("posture")
        if p in posture:
            posture[p] += 1
        sec = r.get("sector") or "Unknown"
        by_sector[sec] = by_sector.get(sec, 0) + 1
        for a in (r.get("advisors") or []):
            agent_freq[a] = agent_freq.get(a, 0) + 1
        for rk in (r.get("risk_titles") or []):
            key = (rk or "")[:60]
            if key:
                risk_freq[key] = risk_freq.get(key, 0) + 1
    top_risks = sorted(risk_freq.items(), key=lambda x: x[1], reverse=True)[:6]
    top_advisors = sorted(agent_freq.items(), key=lambda x: x[1], reverse=True)[:6]
    at_risk = posture["Critical"] + posture["Elevated"]
    return {
        "owner": owner, "total_engagements": n,
        "posture_mix": posture,
        "at_risk": at_risk,
        "by_sector": dict(sorted(by_sector.items(), key=lambda x: x[1], reverse=True)),
        "recurring_risks": [{"risk": k, "count": v} for k, v in top_risks],
        "top_advisors": [{"advisor": k, "count": v} for k, v in top_advisors],
        "persisted": os.path.exists(_PATH),
        "data_dir": _DATA_DIR,
    }


def meta():
    return {"storage": "jsonl (swappable for Aurora/Postgres)", "scope": "owner (Cognito-sub-ready)",
            "data_dir": _DATA_DIR, "persisted": os.path.exists(_PATH),
            "endpoints": ["GET /engagements?owner=", "GET /engagement?owner=&id=", "GET /portfolio?owner=", "POST /engagements/delete"]}


def run_store_tests():
    cases = []
    o = "__test_owner__"
    # clean any prior test rows
    delete_all = [r for r in _read() if r.get("owner") == o]
    for r in delete_all:
        delete_engagement(o, r.get("id"))
    rep = {"engagement_id": "abc123", "title": "Test Co", "sector": "Retail Trade",
           "diagnosis": {"posture": "Critical"}, "workstreams": [{"agent": "cfo_finance"}],
           "agents_engaged": [{"agent": "cfo_finance", "advisor": "AI CFO Advisor"}],
           "risks": [{"risk": "Cash runway under 3 months"}], "recommendations": [{"text": "x"}]}
    sid = save_engagement(o, rep)
    cases.append(("save", bool(sid)))
    lst = list_engagements(o)
    cases.append(("list", lst["count"] >= 1 and lst["engagements"][0]["title"] == "Test Co"))
    got = get_engagement(o, sid)
    cases.append(("get", got.get("report", {}).get("title") == "Test Co"))
    pf = portfolio(o)
    cases.append(("portfolio", pf["total_engagements"] >= 1 and pf["posture_mix"]["Critical"] >= 1 and pf["at_risk"] >= 1))
    d = delete_engagement(o, sid)
    cases.append(("delete", d.get("ok") and list_engagements(o)["count"] == lst["count"] - 1))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    print(json.dumps(run_store_tests(), indent=2))
