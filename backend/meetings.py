"""
meetings.py — client / SME meeting capture + AI minutes (MoM) for the engagement.

How Big 3 / Big 4 run it: every client-site / workshop / steering meeting produces
structured minutes — summary, decisions, action items (owner + due), risks/issues and
follow-ups — that feed the engagement's registers. Here you keep a recording on (audio
stored via blob_store; AWS Transcribe at deploy) or paste notes/transcript, and the AI
turns it into formatted minutes in the firm's MoM format and rolls the actions/decisions/
risks into the Engagement 360.

analyze_meeting() is deterministic (sentence classification); the main.py handler layers
a Groq pass for sharper extraction. Same Postgres-or-JSONL seam as the rest of the ERP.

Endpoints (main.py): GET /meetings?owner=&engagement_id=, GET /meeting?owner=&id=,
POST /meetings (capture + analyze), POST /meeting/analyze (re-run AI on a transcript).
"""

import os
import re
import json
import time
import hashlib

try:
    import engagement_store as _ES
except Exception:
    _ES = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.getenv("BRAIN_DATA_DIR", "").strip() or os.path.join(_HERE, "brain_data")
_PATH = os.path.join(_DATA_DIR, "meetings.jsonl")
_USE_DB = bool(_ES and getattr(_ES, "_USE_DB", False))
_RDC = getattr(_ES, "_RDC", None) if _ES else None

MEETING_TYPES = ["Client site visit", "SME workshop", "Steering committee", "Kickoff",
                 "Working session", "Interview", "Internal"]

_DDL = """
CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY, owner TEXT NOT NULL, ts BIGINT, engagement_id TEXT, title TEXT,
    date TEXT, type TEXT, attendees JSONB, transcript TEXT, audio_key TEXT, mom JSONB, engine TEXT);
CREATE INDEX IF NOT EXISTS idx_meetings_owner ON meetings (owner, engagement_id);
"""
if _USE_DB:
    try:
        with _ES._connect() as _c, _c.cursor() as _cur:
            _cur.execute(_DDL)
            _c.commit()
        print("[meetings] Postgres backend active.", flush=True)
    except Exception as e:  # pragma: no cover
        print(f"[meetings] Postgres init failed ({e}); using JSONL.", flush=True)
        _USE_DB = False


def _owner(o):
    return (o or "").strip() or "demo"


def _as_obj(v):
    if isinstance(v, (dict, list)) or v is None:
        return v
    try:
        return json.loads(v)
    except Exception:
        return v


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
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# Deterministic MoM extraction
# ---------------------------------------------------------------------------
_DEC = ("decided", "agreed", "approved", "concluded", "finalis", "finaliz", "sign-off", "signed off", "confirmed", "will go with", "chosen", "selected")
_ACT = ("will ", "to be ", "action", "shall ", "needs to", "need to", "to do", "to send", "to share", "to prepare", "to review", "to provide", "follow up", "follow-up", "by next", "owner")
_RISK = ("risk", "issue", "concern", "blocker", "delay", "problem", "gap", "bottleneck", "shortfall", "non-compliance", "overrun", "escalat")
_FU = ("follow up", "follow-up", "next step", "revert", "circle back", "share by", "send by", "schedule", "next meeting")
_OWNER_RE = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?|finance|ops|operations|client|team|cfo|coo|ceo|hr|it|procurement)\b", re.I)
_DUE_RE = re.compile(r"\b(by\s+[A-Za-z0-9 ,/-]{3,20}|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|next\s+week|eow|eod|friday|monday|tuesday|wednesday|thursday)\b", re.I)


def _sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+|•|- ", text or "")
    return [p.strip(" -•\t") for p in parts if len(p.strip(" -•\t")) > 8]


def _due(s):
    m = _DUE_RE.search(s)
    return m.group(1).strip() if m else ""


def _owner_of(s):
    m = _OWNER_RE.search(s)
    return (m.group(1).strip().title() if m else "Unassigned")


def analyze_meeting(transcript, attendees=None, title="", date=""):
    """Turn raw notes / transcript into Big-firm minutes (deterministic)."""
    sents = _sentences(transcript)
    decisions, actions, risks, follow_ups, key_points = [], [], [], [], []
    for s in sents:
        sl = s.lower()
        if any(k in sl for k in _DEC):
            decisions.append(s)
        if any(k in sl for k in _ACT):
            actions.append({"action": s, "owner": _owner_of(s), "due": _due(s)})
        if any(k in sl for k in _RISK):
            risks.append(s)
        if any(k in sl for k in _FU):
            follow_ups.append(s)
    # key points: top sentences not already captured
    captured = set(decisions) | {a["action"] for a in actions} | set(risks)
    key_points = [s for s in sents if s not in captured][:6]
    summary = " ".join(sents[:2])[:400] if sents else "No discussion captured."
    return {
        "title": title or "Meeting", "date": date, "attendees": attendees or [],
        "summary": summary,
        "key_points": key_points,
        "decisions": decisions[:8],
        "action_items": actions[:12],
        "risks_issues": risks[:8],
        "follow_ups": follow_ups[:6],
        "counts": {"decisions": len(decisions), "actions": len(actions), "risks": len(risks)},
    }


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def add_meeting(body):
    owner = _owner(body.get("owner"))
    transcript = (body.get("transcript") or body.get("notes") or "").strip()
    title = (body.get("title") or "Meeting").strip()
    date = (body.get("date") or "").strip()
    attendees = body.get("attendees") or []
    if isinstance(attendees, str):
        attendees = [a.strip() for a in attendees.split(",") if a.strip()]
    mom = body.get("mom") or (analyze_meeting(transcript, attendees, title, date) if transcript else {})
    rec = {"id": hashlib.sha1(f"mt:{owner}:{time.time()}".encode()).hexdigest()[:12],
           "owner": owner, "ts": int(time.time()), "engagement_id": (body.get("engagement_id") or "").strip(),
           "title": title, "date": date, "type": (body.get("type") or "Client site visit").strip(),
           "attendees": attendees, "transcript": transcript, "audio_key": (body.get("audio_key") or "").strip(),
           "mom": mom, "engine": (body.get("engine") or "deterministic").strip()}
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor() as cur:
                cur.execute("""INSERT INTO meetings (id,owner,ts,engagement_id,title,date,type,attendees,transcript,audio_key,mom,engine)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (rec["id"], owner, rec["ts"], rec["engagement_id"], rec["title"], rec["date"], rec["type"],
                             json.dumps(rec["attendees"]), rec["transcript"], rec["audio_key"], json.dumps(rec["mom"]), rec["engine"]))
                c.commit()
        except Exception as e:  # pragma: no cover
            print(f"[meetings] add failed: {e}", flush=True); return {"error": "save failed"}
    else:
        try:
            os.makedirs(_DATA_DIR, exist_ok=True)
            with open(_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            return {"error": "save failed"}
    return {"ok": True, "id": rec["id"], "meeting": rec}


def _rows(owner, engagement_id=None):
    if _USE_DB:
        try:
            with _ES._connect() as c, c.cursor(cursor_factory=_RDC) as cur:
                if engagement_id:
                    cur.execute("SELECT * FROM meetings WHERE owner=%s AND engagement_id=%s ORDER BY ts DESC", (owner, engagement_id))
                else:
                    cur.execute("SELECT * FROM meetings WHERE owner=%s ORDER BY ts DESC", (owner,))
                return [{**dict(r), "attendees": _as_obj(r["attendees"]), "mom": _as_obj(r["mom"])} for r in cur.fetchall()]
        except Exception as e:  # pragma: no cover
            print(f"[meetings] read failed: {e}", flush=True); return []
    rows = [r for r in _read() if r.get("owner") == owner and (not engagement_id or r.get("engagement_id") == engagement_id)]
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return rows


def list_meetings(owner, engagement_id=None):
    owner = _owner(owner)
    rows = _rows(owner, engagement_id)
    # roll up registers across meetings (for Engagement 360)
    actions, decisions, risks = [], [], []
    for m in rows:
        mom = m.get("mom") or {}
        for a in (mom.get("action_items") or []):
            actions.append({**a, "meeting": m.get("title"), "date": m.get("date")})
        decisions += [{"decision": d, "meeting": m.get("title")} for d in (mom.get("decisions") or [])]
        risks += [{"risk": r, "meeting": m.get("title")} for r in (mom.get("risks_issues") or [])]
    return {"owner": owner, "count": len(rows), "meetings": rows, "types": MEETING_TYPES,
            "registers": {"action_items": actions[:30], "decisions": decisions[:20], "risks_issues": risks[:20]}}


def get_meeting(owner, mid):
    owner = _owner(owner)
    m = next((x for x in _rows(owner) if x.get("id") == mid), None)
    return {"meeting": m} if m else {"error": "not found"}


# ---------------------------------------------------------------------------
# MS 365 meeting planning + scheduling (AI proposes, human approves, auto-schedule)
# ---------------------------------------------------------------------------
import datetime


def _next_slots(n=3):
    """Next n business days at 10:00 and 15:00 (ISO), as proposed slots."""
    slots, d, added = [], datetime.date.today(), 0
    while len(slots) < n and added < 14:
        d = d + datetime.timedelta(days=1)
        added += 1
        if d.weekday() >= 5:  # skip weekends
            continue
        for hr in (10, 15):
            slots.append(f"{d.isoformat()}T{hr:02d}:00:00")
            if len(slots) >= n:
                break
    return slots


def propose_meeting(body):
    """AI drafts a meeting plan (agenda, attendees, slots) for human review — step 1
    of the human-in-the-loop flow. Deterministic; the handler may Groq-polish the agenda."""
    purpose = (body.get("purpose") or body.get("topic") or "engagement working session").strip()
    etype = (body.get("engagement_type") or "").strip()
    attendees = body.get("attendees") or []
    if isinstance(attendees, str):
        attendees = [a.strip() for a in attendees.split(",") if a.strip()]
    agenda = [
        f"Objectives & desired outcomes — {purpose}",
        "Current-state walkthrough with the SME / process owner",
        "Key data & evidence review",
        "Findings, risks and open questions",
        "Decisions required & action items (owners, dates)",
        "Next steps & follow-up cadence",
    ]
    return {"ok": True, "status": "proposed", "title": (body.get("title") or f"{etype or 'Engagement'}: {purpose}")[:120],
            "purpose": purpose, "type": (body.get("type") or "Working session"),
            "attendees": attendees, "duration_min": int(body.get("duration_min") or 60),
            "agenda": agenda, "proposed_slots": _next_slots(3),
            "note": "Review/edit, then schedule — sends a Teams invite via MS 365 when connected."}


def schedule_meeting(body):
    """Step 2: create the calendar invite. Uses Microsoft Graph when MS365_TOKEN is set
    (Teams online meeting), else returns a draft invite. Also stores the meeting record."""
    owner = _owner(body.get("owner"))
    slot = (body.get("slot") or "").strip()
    title = (body.get("title") or "Engagement meeting").strip()
    attendees = body.get("attendees") or []
    if isinstance(attendees, str):
        attendees = [a.strip() for a in attendees.split(",") if a.strip()]
    duration = int(body.get("duration_min") or 60)
    agenda = body.get("agenda") or []
    token = os.getenv("MS365_TOKEN", "").strip()
    backend, invite, join_url = "draft", None, None
    if token and slot:
        try:
            import httpx
            end = (datetime.datetime.fromisoformat(slot) + datetime.timedelta(minutes=duration)).isoformat()
            payload = {
                "subject": title,
                "body": {"contentType": "HTML", "content": "<br>".join(["<b>Agenda</b>"] + [f"• {a}" for a in agenda])},
                "start": {"dateTime": slot, "timeZone": os.getenv("MS365_TZ", "Asia/Kolkata")},
                "end": {"dateTime": end, "timeZone": os.getenv("MS365_TZ", "Asia/Kolkata")},
                "attendees": [{"emailAddress": {"address": a}, "type": "required"} for a in attendees if "@" in a],
                "isOnlineMeeting": True, "onlineMeetingProvider": "teamsForBusiness",
            }
            r = httpx.post("https://graph.microsoft.com/v1.0/me/events",
                           headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                           json=payload, timeout=15)
            if r.status_code in (200, 201):
                ev = r.json()
                backend = "msgraph"
                join_url = (ev.get("onlineMeeting") or {}).get("joinUrl")
                invite = {"id": ev.get("id"), "webLink": ev.get("webLink"), "join_url": join_url}
            else:
                invite = {"error": f"Graph {r.status_code}", "detail": r.text[:200]}
        except Exception as e:  # pragma: no cover
            invite = {"error": str(e)[:160]}
    if backend != "msgraph":
        invite = {"draft": True, "title": title, "when": slot, "duration_min": duration, "attendees": attendees,
                  "note": "MS 365 not connected — connect at deploy (MS365_TOKEN) to auto-send a Teams invite."}
    # store the scheduled meeting (agenda as the pre-meeting MoM; notes captured later)
    rec = add_meeting({"owner": owner, "engagement_id": body.get("engagement_id"), "title": title,
                       "type": body.get("type") or "Working session", "attendees": attendees,
                       "transcript": "", "engine": "scheduled",
                       "mom": {"title": title, "date": slot, "attendees": attendees, "summary": "Scheduled — agenda set; minutes to follow.",
                               "key_points": agenda, "decisions": [], "action_items": [], "risks_issues": [], "follow_ups": [],
                               "scheduled": True, "slot": slot, "join_url": join_url}})
    return {"ok": True, "backend": backend, "invite": invite, "slot": slot, "meeting_id": rec.get("id")}


def meta():
    return {"types": MEETING_TYPES, "backend": "postgres" if _USE_DB else "jsonl",
            "transcription": "AWS Transcribe at deploy; paste transcript/notes now",
            "scheduling": "MS 365 / Microsoft Graph (Teams) when MS365_TOKEN set; draft otherwise",
            "endpoints": ["GET /meetings?owner=&engagement_id=", "GET /meeting", "POST /meetings",
                          "POST /meeting/analyze", "POST /meeting/propose", "POST /meeting/schedule"]}


def run_meeting_tests():
    cases = []
    o = "__mtg_test__"
    tx = ("Client site visit with CFO and Ops SME. "
          "We agreed to migrate to the new ERP by Q3. "
          "Finance team will share the AR ageing by next week. "
          "Key risk: receivables are delayed and cash runway is a concern. "
          "Ravi to prepare the cost model by 30/06. "
          "Follow up: schedule the next steering meeting.")
    mom = analyze_meeting(tx, ["CFO", "Ops SME"], "Discovery — Acme", "2026-06-18")
    cases.append(("analyze", len(mom["decisions"]) >= 1 and len(mom["action_items"]) >= 2
                  and len(mom["risks_issues"]) >= 1 and mom["action_items"][0]["owner"]))
    add = add_meeting({"owner": o, "engagement_id": "E1", "title": "Discovery", "type": "Client site visit",
                       "attendees": "CFO, Ops SME", "transcript": tx})
    cases.append(("add", add.get("ok") and add["meeting"]["mom"]["counts"]["actions"] >= 2))
    lst = list_meetings(o, "E1")
    cases.append(("list_registers", lst["count"] >= 1 and len(lst["registers"]["action_items"]) >= 2))
    g = get_meeting(o, add["id"])
    cases.append(("get", g.get("meeting", {}).get("title") == "Discovery"))
    pr = propose_meeting({"purpose": "O2C diagnostic", "engagement_type": "Order-to-Cash", "attendees": "cfo@x.com"})
    cases.append(("propose", pr.get("ok") and len(pr["agenda"]) >= 4 and len(pr["proposed_slots"]) == 3))
    sc = schedule_meeting({"owner": o, "engagement_id": "E1", "title": "O2C kickoff", "slot": pr["proposed_slots"][0], "agenda": pr["agenda"], "attendees": ["cfo@x.com"]})
    cases.append(("schedule", sc.get("ok") and sc.get("backend") in ("draft", "msgraph") and sc.get("meeting_id")))
    # cleanup
    if not _USE_DB:
        rows = [r for r in _read() if r.get("owner") != o]
        try:
            os.makedirs(_DATA_DIR, exist_ok=True)
            with open(_PATH, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        except Exception:
            pass
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    print(json.dumps(run_meeting_tests(), indent=2))
