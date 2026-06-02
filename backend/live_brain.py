"""
live_brain.py — the AI-NATIVE CONSULTING BRAIN.

Turns a structured business intake (a FORM, not a one-liner) into a *customised*
consulting engagement. Unlike the static playbooks, every answer is shaped by the
specific inputs and is grounded on three retrieval sources, then synthesised:

  1. PLAYBOOK grounding   — the matched 13-part sector blueprint (industry_playbooks)
  2. OPEN-SOURCE search   — keyless DuckDuckGo + Wikipedia snippets (live web)
  3. MEMORY recall        — similar past engagements from a persistent learning log

  -> SYNTHESIS            — Groq LLM (llm_stack) when a key exists; ALWAYS with a
                            deterministic, input-personalised fallback so it never
                            fails and never returns the same thing for two different
                            businesses.

  -> LEARN                — every engagement is appended to the learning log, so the
                            brain evolves: future prompts recall what was seen before.

Design rule (same as the rest of the codebase): never raise, always return a
complete uniform envelope, sub-second when keyless.
"""

import os
import re
import json
import time
import hashlib
import urllib.parse

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None

try:
    import industry_playbooks as PB
except Exception:  # pragma: no cover
    PB = None

try:
    import msme_agents as M
except Exception:  # pragma: no cover
    M = None

try:
    import llm_stack as LLM
except Exception:  # pragma: no cover
    LLM = None


# ============================================================
# 1. INTAKE FORM — what we capture to personalise the engagement
# ============================================================
# Drives the frontend form. `mode` decides which fields show.
INTAKE_FIELDS = [
    {"key": "description",      "label": "Describe your business",            "type": "textarea", "ph": "e.g. 8-store grocery retail chain in Pune buying from FMCG distributors", "modes": ["startup", "existing"], "required": True},
    {"key": "business_type",    "label": "Sector (auto-detected, editable)",  "type": "playbook", "ph": "", "modes": ["startup", "existing"]},
    {"key": "specific_question","label": "Your #1 question right now",         "type": "textarea", "ph": "e.g. How do I cut working-capital lock without losing sales?", "modes": ["startup", "existing"]},
    {"key": "top_challenges",   "label": "Top challenges (one per line)",      "type": "textarea", "ph": "thin margins\nstockouts\nstaff churn", "modes": ["startup", "existing"]},
    {"key": "goals",            "label": "Goal for next 6-12 months",          "type": "text",     "ph": "e.g. double revenue, raise seed, open 3 stores", "modes": ["startup", "existing"]},
    {"key": "stage",            "label": "Stage",                              "type": "select",   "options_startup": ["idea", "pre-seed", "seed", "series-a", "early-revenue"], "options_existing": ["just-started", "growing", "established", "scaling", "turnaround"], "modes": ["startup", "existing"]},
    {"key": "turnover_cr",      "label": "Annual turnover (₹ cr)",             "type": "number",   "ph": "8", "modes": ["existing"]},
    {"key": "target_raise_cr",  "label": "Target raise (₹ cr)",                "type": "number",   "ph": "2", "modes": ["startup"]},
    {"key": "employees",        "label": "Team size",                          "type": "number",   "ph": "24", "modes": ["startup", "existing"]},
    {"key": "city_tier",        "label": "Primary market",                     "type": "select",   "options": ["Metro", "Tier-1", "Tier-2", "Tier-3", "Pan-India", "Export"], "modes": ["startup", "existing"]},
]


def intake_meta():
    """Form schema + sector list for the frontend."""
    return {
        "fields": INTAKE_FIELDS,
        "playbooks": PB.list_playbooks() if PB else [],
        "modes": [
            {"key": "startup", "label": "New / Startup", "icon": "🚀"},
            {"key": "existing", "label": "Existing Business", "icon": "🏢"},
        ],
    }


# ============================================================
# 2. OPEN-SOURCE WEB SEARCH (keyless: DuckDuckGo + Wikipedia)
# ============================================================
_UA = {"User-Agent": "Mozilla/5.0 (compatible; PMGuruBrain/1.0)"}


def _http_get(url, params=None, timeout=8.0):
    if not httpx:
        return None
    try:
        with httpx.Client(timeout=timeout, headers=_UA, follow_redirects=True) as c:
            r = c.get(url, params=params)
            if r.status_code == 200:
                return r
    except Exception as e:
        print(f"[live_brain] GET failed {url}: {str(e)[:100]}", flush=True)
    return None


def _ddg_instant(query):
    """DuckDuckGo Instant Answer API — keyless, returns abstract + related topics."""
    out = []
    r = _http_get("https://api.duckduckgo.com/", {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"})
    if not r:
        return out
    try:
        d = r.json()
    except Exception:
        return out
    if d.get("AbstractText"):
        out.append({"title": d.get("Heading") or query, "snippet": d["AbstractText"],
                    "url": d.get("AbstractURL", ""), "source": d.get("AbstractSource") or "DuckDuckGo"})
    for t in (d.get("RelatedTopics") or [])[:6]:
        if isinstance(t, dict) and t.get("Text"):
            out.append({"title": t["Text"][:80], "snippet": t["Text"],
                        "url": (t.get("FirstURL") or ""), "source": "DuckDuckGo"})
    return out


def _ddg_html(query):
    """DuckDuckGo HTML results — best-effort scrape of titles + snippets."""
    out = []
    r = _http_get("https://html.duckduckgo.com/html/", {"q": query})
    if not r:
        return out
    html = r.text
    # result snippets live in <a class="result__snippet">...</a> and titles in result__a
    titles = re.findall(r'result__a[^>]*>(.*?)</a>', html, re.S)
    snips = re.findall(r'result__snippet[^>]*>(.*?)</a>', html, re.S)
    urls = re.findall(r'result__a"\s+href="(.*?)"', html, re.S)

    def _clean(s):
        return re.sub(r"<.*?>", "", s or "").replace("&amp;", "&").replace("&#x27;", "'").strip()
    for i in range(min(5, len(snips))):
        t = _clean(titles[i]) if i < len(titles) else query
        out.append({"title": t[:90], "snippet": _clean(snips[i])[:320],
                    "url": _clean(urls[i]) if i < len(urls) else "", "source": "Web"})
    return out


def _wikipedia(query):
    """Wikipedia search + summary — keyless, reliable grounding."""
    out = []
    r = _http_get("https://en.wikipedia.org/w/api.php",
                  {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": "2"})
    if not r:
        return out
    try:
        hits = r.json().get("query", {}).get("search", [])
    except Exception:
        return out
    for h in hits[:2]:
        title = h.get("title", "")
        s = _http_get("https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title))
        if s:
            try:
                js = s.json()
                if js.get("extract"):
                    out.append({"title": title, "snippet": js["extract"][:320],
                                "url": (js.get("content_urls", {}).get("desktop", {}) or {}).get("page", ""),
                                "source": "Wikipedia"})
            except Exception:
                pass
    return out


def web_search(query, max_results=6):
    """Aggregate keyless open-source results. Never raises; returns [] on full failure."""
    results, seen = [], set()
    for fn in (_ddg_instant, _wikipedia, _ddg_html):
        try:
            for item in fn(query):
                k = (item.get("snippet") or "")[:60]
                if k and k not in seen:
                    seen.add(k)
                    results.append(item)
        except Exception as e:
            print(f"[live_brain] search source failed: {str(e)[:80]}", flush=True)
        if len(results) >= max_results:
            break
    return results[:max_results]


# ============================================================
# 3. PERSISTENT LEARNING LOG  (the brain evolves with each prompt)
# ============================================================
# Stored as JSONL under BRAIN_DATA_DIR (mount a Railway volume there to persist
# across redeploys; falls back to a local dir otherwise).
_DATA_DIR = os.getenv("BRAIN_DATA_DIR", "").strip() or os.path.join(os.path.dirname(os.path.abspath(__file__)), "brain_data")
_LOG_PATH = os.path.join(_DATA_DIR, "engagements.jsonl")


def _ensure_dir():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        return True
    except Exception as e:  # pragma: no cover
        print(f"[live_brain] cannot create {_DATA_DIR}: {e}", flush=True)
        return False


def _read_log():
    out = []
    try:
        if os.path.exists(_LOG_PATH):
            with open(_LOG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            out.append(json.loads(line))
                        except Exception:
                            continue
    except Exception as e:  # pragma: no cover
        print(f"[live_brain] read log failed: {e}", flush=True)
    return out


def _tokens(text):
    return set(re.findall(r"[a-z]{4,}", (text or "").lower()))


def recall_similar(business_type, description, k=3):
    """Find past engagements most similar to this one (sector + keyword overlap)."""
    log = _read_log()
    if not log:
        return {"used": 0, "total_memory": 0, "notes": [], "matches": []}
    q_tokens = _tokens(description) | _tokens(business_type)
    scored = []
    for e in log:
        score = 0
        if e.get("business_type") and e.get("business_type") == business_type:
            score += 5
        overlap = len(q_tokens & set(e.get("tokens", [])))
        score += overlap
        if score > 0:
            scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [e for _, e in scored[:k]]
    notes = []
    for e in top:
        kf = e.get("key_findings") or []
        if kf:
            notes.append(f"Past {e.get('business_type','?')} engagement learned: {kf[0]}")
    return {"used": len(top), "total_memory": len(log), "notes": notes,
            "matches": [{"business_type": e.get("business_type"), "summary": e.get("summary", "")} for e in top]}


def save_engagement(intake, envelope):
    """Append this engagement so the brain learns. Best-effort; never raises."""
    if not _ensure_dir():
        return False
    desc = intake.get("description", "")
    recs = envelope.get("tailored_recommendations") or []
    key_findings = [r.get("title") for r in recs[:3] if r.get("title")]
    rid = envelope.get("engagement_id") or hashlib.sha1((desc + str(time.time())).encode()).hexdigest()[:12]
    record = {
        "id": rid,
        "ts": int(time.time()),
        "business_type": envelope.get("business_type"),
        "mode": intake.get("mode"),
        "summary": (envelope.get("diagnosis") or "")[:240],
        "key_findings": key_findings,
        "tokens": sorted(list(_tokens(desc) | _tokens(intake.get("top_challenges", "")) | _tokens(intake.get("goals", ""))))[:40],
        "engine": envelope.get("engine"),
    }
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception as e:  # pragma: no cover
        print(f"[live_brain] save failed: {e}", flush=True)
        return False


def brain_stats():
    log = _read_log()
    by_sector = {}
    for e in log:
        bt = e.get("business_type") or "unknown"
        by_sector[bt] = by_sector.get(bt, 0) + 1
    recent = sorted(log, key=lambda e: e.get("ts", 0), reverse=True)[:8]
    return {
        "total_engagements": len(log),
        "by_sector": by_sector,
        "recent": [{"business_type": e.get("business_type"), "mode": e.get("mode"),
                    "summary": e.get("summary", "")[:140], "engine": e.get("engine")} for e in recent],
        "data_dir": _DATA_DIR,
        "persisted": os.path.exists(_LOG_PATH),
    }


# ============================================================
# 4. DETERMINISTIC PERSONALISER  (always-on base, input-shaped)
# ============================================================
def _f(intake, key, default=""):
    v = intake.get(key)
    return v if v not in (None, "") else default


def _challenge_list(intake):
    raw = _f(intake, "top_challenges")
    items = [x.strip() for x in re.split(r"[\n;,]", raw) if x.strip()]
    return items


def _deterministic_engagement(intake, pb, recall):
    """Build a complete, input-personalised engagement from the playbook + form.
    This is what guarantees different businesses (and different inputs) get
    different answers even with no LLM key."""
    mode = _f(intake, "mode", "existing")
    sector = pb.get("name", "your business") if pb else "your business"
    stage = _f(intake, "stage", "growing")
    tier = _f(intake, "city_tier", "Tier-2")
    challenges = _challenge_list(intake)
    goal = _f(intake, "goals")
    size_bits = []
    if _f(intake, "turnover_cr"):
        size_bits.append(f"₹{_f(intake,'turnover_cr')} cr turnover")
    if _f(intake, "target_raise_cr"):
        size_bits.append(f"raising ₹{_f(intake,'target_raise_cr')} cr")
    if _f(intake, "employees"):
        size_bits.append(f"{_f(intake,'employees')} people")
    size_str = ", ".join(size_bits) or "early scale"

    om = (pb.get("operating_model") or {}).get("summary", "") if pb else ""
    bottlenecks = pb.get("operational_bottlenecks", []) if pb else []
    autos = pb.get("ai_automation_opportunities", []) if pb else []
    pb_risks = pb.get("risk_model", []) if pb else []
    kpis = pb.get("kpi_structure", []) if pb else []
    growth_stages = (pb.get("growth_playbook") or {}).get("stages", []) if pb else []
    pm = pb.get("pm_workflows", []) if pb else []

    # Diagnosis — explicitly references THIS business's inputs.
    diag = (
        f"You are running {'a ' + mode + '-stage' if mode=='startup' else 'an existing'} "
        f"{sector} ({size_str}; primary market {tier}; stage: {stage}). "
        + (f"The operating reality of this sector: {om} " if om else "")
        + (f"Your stated priority — \"{_f(intake,'specific_question')}\" — " if _f(intake, 'specific_question') else "")
        + ("maps directly to the structural levers below. " if _f(intake, 'specific_question') else "")
    )
    if challenges:
        diag += f"You flagged {len(challenges)} pain point(s): {', '.join(challenges[:4])}. "
        bn0 = bottlenecks[0]["bottleneck"] if bottlenecks else None
        if bn0:
            diag += f"In {sector}, these typically trace back to the sector's #1 bottleneck — {bn0}. "
    if goal:
        diag += f"Goal in scope: {goal}."

    # Recommendations — tailored: challenge-driven first, then sector bottlenecks, then mode plays.
    recs = []
    for ch in challenges[:3]:
        recs.append({"title": f"Resolve: {ch}", "priority": "High",
                     "why": f"You flagged this as a live pain point in your {sector} operation.",
                     "how": "Instrument it, set a target, assign an owner, review weekly. " +
                            ("Use the relevant AI agent below to automate the fix." if autos else "")})
    for b in bottlenecks[:3]:
        recs.append({"title": f"Pre-empt sector bottleneck: {b.get('bottleneck')}", "priority": "Medium",
                     "why": b.get("impact", ""), "how": f"Root cause is usually: {b.get('root_cause','')}. Put a control in before it bites."})
    if mode == "startup":
        recs.append({"title": "Tighten unit economics before scaling spend", "priority": "High",
                     "why": "Pre-PMF burn on unproven economics is the #1 startup killer.",
                     "how": "Prove contribution margin and CAC payback on a small cohort first; then pour fuel."})
        if _f(intake, "target_raise_cr"):
            recs.append({"title": "Build an investor-ready data room", "priority": "Medium",
                         "why": f"You're targeting ₹{_f(intake,'target_raise_cr')} cr — diligence readiness shortens the raise.",
                         "how": "Cap table, 3-statement model, metrics pack, DPIIT 80-IAC/angel-tax exemption filings."})
    else:
        recs.append({"title": "Stand up a weekly numbers cadence", "priority": "High",
                     "why": "Most MSME leakage is invisible without a weekly metric review.",
                     "how": "One dashboard: revenue, margin, cash, DSO, and your top-2 sector KPIs below."})

    quick_wins = [f"{a.get('opportunity')} (via {a.get('agent') or 'ops'})"
                  for a in autos if a.get("effort") == "Low"][:3]
    if not quick_wins:
        quick_wins = [a.get("opportunity") for a in autos[:3] if a.get("opportunity")]

    # Risk — bump severity if challenges mention cash/compliance.
    risk_text = " ".join(challenges).lower()
    risks = []
    for r in pb_risks[:4]:
        sev = r.get("severity", "Medium")
        if any(w in risk_text for w in ("cash", "gst", "compliance", "payment", "credit")) and r.get("severity") in ("Medium", "High"):
            sev = "High"
        risks.append({"risk": r.get("risk"), "severity": sev, "control": r.get("control")})

    kpi_out = [{"kpi": k.get("kpi"), "target": k.get("healthy"), "why": k.get("definition")} for k in kpis[:5]]

    # 90-day plan from PM workflows + growth stage plays.
    plays = []
    if growth_stages:
        idx = 0 if mode == "startup" or stage in ("idea", "pre-seed", "seed", "just-started") else min(1, len(growth_stages) - 1)
        plays = (growth_stages[idx] or {}).get("plays", [])
    plan = [
        {"phase": "Days 0-30 — Stabilise & measure",
         "steps": ([f"Instrument: {challenges[0]}"] if challenges else []) +
                  [(pm[0]["milestones"][0] if pm and pm[0].get("milestones") else "Stand up the core dashboard")] +
                  ["Confirm compliance calendar is current"]},
        {"phase": "Days 30-60 — Fix the binding constraint",
         "steps": [recs[0]["title"] if recs else "Address top recommendation",
                   (quick_wins[0] if quick_wins else "Automate one repetitive workflow")]},
        {"phase": "Days 60-90 — Compound",
         "steps": (plays[:2] if plays else ["Double down on what moved the needle", "Plan the next growth bet"])},
    ]

    opportunities = plays[:4] if plays else [a.get("opportunity") for a in autos[:4] if a.get("opportunity")]

    return {
        "diagnosis": diag,
        "tailored_recommendations": recs[:6],
        "quick_wins": quick_wins,
        "risks": risks,
        "kpis": kpi_out,
        "action_plan_90day": plan,
        "opportunities": opportunities,
    }


# ============================================================
# 5. LLM SYNTHESIS  (Groq via llm_stack; merges over the base)
# ============================================================
def _extract_json(text):
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(json)?", "", t).strip()
    t = re.sub(r"```$", "", t).strip()
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(t[start:end + 1])
    except Exception:
        return None


def _llm_enhance(intake, pb, web, recall, base):
    """Ask Groq to produce a richer, business-specific engagement. Returns dict or None."""
    if not LLM or not LLM.available():
        return None
    sector = pb.get("name") if pb else "the business"
    grounding = {
        "operating_model": (pb.get("operating_model") or {}).get("summary") if pb else "",
        "bottlenecks": [b.get("bottleneck") for b in (pb.get("operational_bottlenecks") or [])][:6] if pb else [],
        "kpis": [k.get("kpi") for k in (pb.get("kpi_structure") or [])][:6] if pb else [],
        "risks": [r.get("risk") for r in (pb.get("risk_model") or [])][:5] if pb else [],
        "compliance": [c.get("title") for c in (pb.get("compliance_resolved") or [])] if pb else [],
    }
    web_block = "\n".join(f"- [{w.get('source')}] {w.get('title')}: {w.get('snippet')}" for w in web[:6]) or "(no live results)"
    recall_block = "\n".join(f"- {n}" for n in recall.get("notes", [])) or "(no prior memory)"
    system = (
        "You are a blended top-tier strategy + operations consultant and a veteran Indian MSME operator. "
        "Produce a SPECIFIC, customised consulting engagement for THIS business using its exact inputs. "
        "Be concrete, India-aware, ₹-denominated. Never generic. Cite the live web sources when you use them. "
        "Return ONLY valid JSON with keys: diagnosis (string), tailored_recommendations (array of {title, priority, why, how}), "
        "quick_wins (array of strings), risks (array of {risk, severity, control}), kpis (array of {kpi, target, why}), "
        "action_plan_90day (array of {phase, steps[]}), opportunities (array of strings)."
    )
    user = (
        f"SECTOR: {sector}\nMODE: {intake.get('mode')}\n"
        f"BUSINESS: {intake.get('description','')}\n"
        f"KEY QUESTION: {intake.get('specific_question','')}\n"
        f"CHALLENGES: {intake.get('top_challenges','')}\n"
        f"GOAL: {intake.get('goals','')}\nSTAGE: {intake.get('stage','')}\n"
        f"SIZE: turnover ₹{intake.get('turnover_cr','?')}cr / raise ₹{intake.get('target_raise_cr','?')}cr / "
        f"{intake.get('employees','?')} people / market {intake.get('city_tier','?')}\n\n"
        f"SECTOR GROUNDING (use, don't just repeat):\n{json.dumps(grounding, ensure_ascii=False)}\n\n"
        f"LIVE OPEN-SOURCE SEARCH RESULTS:\n{web_block}\n\n"
        f"WHAT THE BRAIN REMEMBERS FROM SIMILAR PAST ENGAGEMENTS:\n{recall_block}\n\n"
        "Now produce the customised JSON engagement."
    )
    try:
        res = LLM.augment(system, user, max_tokens=1600)
    except Exception as e:
        print(f"[live_brain] llm augment failed: {str(e)[:120]}", flush=True)
        return None
    if not res or not res.get("text"):
        return None
    parsed = _extract_json(res["text"])
    if not isinstance(parsed, dict):
        return None
    parsed["_provider"] = res.get("provider")
    return parsed


# ============================================================
# 6. ORCHESTRATOR
# ============================================================
def consult(intake):
    """Main entry: intake (dict) -> customised engagement envelope. Never raises."""
    intake = intake or {}
    mode = intake.get("mode") or "existing"
    description = intake.get("description") or ""
    # Resolve the sector/playbook.
    key = (intake.get("business_type") or "").strip()
    pb, matched_key, how = (None, None, "none")
    if PB:
        pb, matched_key, how = PB.resolve(business_type=key or None, key=key or None, description=description or None)
    sector_name = pb.get("name") if pb else "General MSME"

    # Retrieval.
    search_q = f"{sector_name} India MSME {intake.get('specific_question') or intake.get('goals') or ''}".strip()
    web = web_search(search_q, max_results=6)
    recall = recall_similar(matched_key or key, description + " " + intake.get("top_challenges", ""))

    # Base (deterministic, always personalised) then LLM enhancement merged on top.
    base = _deterministic_engagement(intake, pb, recall)
    engine = "deterministic"
    enhanced = _llm_enhance(intake, pb, web, recall, base)
    if enhanced:
        for k in ("diagnosis", "tailored_recommendations", "quick_wins", "risks", "kpis", "action_plan_90day", "opportunities"):
            v = enhanced.get(k)
            if v:  # LLM value wins where present + non-empty
                base[k] = v
        engine = f"groq:{enhanced.get('_provider','llm')}"

    envelope = {
        "engagement_id": hashlib.sha1((description + str(time.time())).encode()).hexdigest()[:12],
        "mode": mode,
        "business_type": matched_key or key or None,
        "sector_name": sector_name,
        "matched_by": how,
        "engine": engine,
        "playbook_key": matched_key,
        **base,
        "sources": web,
        "citations": (pb.get("citations_resolved") if pb else []) or [],
        "compliance": (pb.get("compliance_resolved") if pb else []) or [],
        "recall": recall,
        "playbook_link": f"/playbooks?key={matched_key}" if matched_key else None,
    }
    # Learn.
    saved = save_engagement(intake, envelope)
    envelope["learned"] = saved
    return envelope


if __name__ == "__main__":  # quick local smoke
    out = consult({"mode": "existing", "description": "8-store grocery retail chain in Pune",
                   "top_challenges": "stockouts\nthin margins", "turnover_cr": "12", "city_tier": "Tier-2",
                   "specific_question": "how do I improve margins?"})
    print("engine:", out["engine"], "| sector:", out["sector_name"], "| recs:", len(out["tailored_recommendations"]),
          "| sources:", len(out["sources"]), "| learned:", out["learned"])
