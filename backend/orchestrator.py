"""
orchestrator.py — the "Managing Partner" super-agent for the AI Consulting OS.

One free-text problem (+ optional ERP-style intake) → a full Big 3 / Big 4-style
engagement: route it, assemble a multi-disciplinary workstream team from the live
agents, run each workstream, then CURATE the best into one research-grade report
(executive summary, workstream findings, consolidated recommendations, risk
register, 90-day plan, KPIs and citations).

Deterministic core (no random / no Date) so the same engagement reproduces; an
optional Groq "managing partner" narrative is layered on best-effort by the handler.

Endpoint (wired in main.py): POST /orchestrate (+ GET /orchestrate/meta, /orchestrate/tests).
"""

try:
    import msme_agents as _M
except Exception:
    _M = None

try:
    import consulting_catalog as _C
except Exception:
    _C = None

try:
    import engagement_360 as _D
except Exception:
    _D = None

try:
    import engagement_types as _ET
except Exception:
    _ET = None


def _live(a):
    return bool(_M and _M.MSME_AGENTS.get(a, {}).get("status") == "live")


def _hash(text):
    h = 2166136261
    for ch in str(text):
        h = (h ^ ord(ch)) * 16777619 & 0xFFFFFFFF
    return format(h, "08x")


def _advisor_for(agent_key):
    if not _C:
        return None
    for a in _C.AI_ADVISORS:
        if a["agent"] == agent_key:
            return a["advisor"]
    return None


# ---------------------------------------------------------------------------
# Workstream selection — assemble the engagement team
# ---------------------------------------------------------------------------
def _detect_towers(desc):
    dl = (desc or "").lower()
    hits = []
    if _C:
        for t in _C.TOWERS:
            if any(h in dl for h in _C._TOWER_HINTS.get(t["key"], [])):
                hits.append(t)
    return hits


def select_workstreams(desc, cls, etype=None):
    """Pick the multi-disciplinary agent team for this engagement (like staffing a case).
    If a typed engagement (etype) is given, its end-to-end agent team leads, so the
    standard scope is always fully staffed; routing/sector specialists augment it."""
    agents, routed = [], None
    if etype and _ET:
        agents += _ET.live_agents(etype)
    if _C:
        routed = _C.resolve(desc)
        if routed.get("matched") and routed.get("agent"):
            agents.append(routed["agent"])
    # towers detected by distinctive terms -> their primary live agent
    for t in _detect_towers(desc):
        for a in t.get("agents", []):
            if _live(a):
                agents.append(a)
                break
    # sector / profile-driven specialists
    if cls.get("is_export"):
        agents.append("export_compliance")
    if cls.get("is_tech") or cls.get("is_startup"):
        agents.append("investor_readiness")
    if cls.get("industry") in ("manufacturing", "pharma"):
        agents.append("sop_agent")
    # cross-cutting lenses every engagement gets: finance, risk, and the CEO synthesis
    agents += ["cfo_finance", "risk_audit", "ceo_copilot"]
    # dedupe (preserve order), keep only live, cap the team size
    seen, out = set(), []
    for a in agents:
        if a in seen or not _live(a):
            continue
        seen.add(a)
        out.append(a)
    return out[:6], routed


# ---------------------------------------------------------------------------
# Curation helpers — "review all and curate the best"
# ---------------------------------------------------------------------------
_SEV_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def _dedupe(items, keyfn, cap):
    seen, out = set(), []
    for it in items:
        k = keyfn(it)
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
        if len(out) >= cap:
            break
    return out


def synthesize(desc, cls, intake, workstreams, routed):
    """Merge the workstream envelopes into one curated Big-4 engagement report."""
    all_recs, all_risks, all_actions, all_kpis, all_cites = [], [], [], [], []
    ws_cards = []
    for ws in workstreams:
        env = ws.get("output", {}) or {}
        akey = ws.get("agent")
        aname = ws.get("name", akey)
        advisor = _advisor_for(akey)
        for r in (env.get("recommendations") or []):
            all_recs.append({"text": r, "source_agent": akey, "advisor": advisor})
        for rk in (env.get("risks") or []):
            all_risks.append({**({k: rk.get(k) for k in ("risk", "severity", "control", "owner")}), "source_agent": akey})
        for ac in (env.get("action_plan") or []):
            all_actions.append({**ac, "source_agent": akey})
        for kp in (env.get("kpis_to_monitor") or []):
            all_kpis.append({**kp, "source_agent": akey})
        for c in (env.get("citations") or []):
            all_cites.append(c)
        ws_cards.append({
            "agent": akey, "name": aname, "advisor": advisor,
            "context": env.get("business_context", ""),
            "headline_reco": (env.get("recommendations") or [None])[0],
            "top_risk": next((r.get("risk") for r in (env.get("risks") or []) if r.get("severity") in ("Critical", "High")), None),
            "kpis": [k.get("kpi") for k in (env.get("kpis_to_monitor") or [])][:3],
        })

    # curate
    all_risks.sort(key=lambda r: _SEV_RANK.get(r.get("severity"), 4))
    risks = _dedupe(all_risks, lambda r: (r.get("risk") or "")[:50].lower(), 8)
    recs = _dedupe(all_recs, lambda r: (r.get("text") or "")[:50].lower(), 9)
    actions = _dedupe(all_actions, lambda a: (a.get("step") or "")[:50].lower(), 10)
    kpis = _dedupe(all_kpis, lambda k: (k.get("kpi") or "").lower(), 10)
    cites = _dedupe(all_cites, lambda c: c.get("key", c.get("title", "")), 16)

    crit = sum(1 for r in risks if r.get("severity") == "Critical")
    high = sum(1 for r in risks if r.get("severity") == "High")
    posture = "Critical" if crit else ("Elevated" if high >= 2 else ("Watch" if (high or risks) else "Stable"))
    sector_name = (cls.get("industry") or "business").replace("_", " ").title()

    title = (intake.get("company") or desc[:48] or "MSME Engagement").strip()
    routed_to = None
    if routed and routed.get("matched"):
        routed_to = {"tower": routed["tower"]["name"], "icon": routed["tower"].get("icon"),
                     "service_line": routed.get("service_line"), "advisor": routed["tower"].get("ai_advisor")}

    exec_summary = (
        f"This engagement reviews a {cls.get('size','small')} {sector_name} business across "
        f"{len(workstreams)} workstreams. The risk posture is {posture.lower()} "
        f"({crit} critical, {high} high). The priority is to {('stabilise and de-risk' if posture in ('Critical','Elevated') else 'consolidate and scale')}: "
        f"{(recs[0]['text'] if recs else 'act on the prioritised recommendations below')}"
    )

    return {
        "engagement_id": _hash(desc + str(sorted(intake.items()))),
        "title": title,
        "sector": sector_name,
        "classification": cls,
        "business_context": desc.strip()[:400],
        "routed_to": routed_to,
        "agents_engaged": [{"agent": w.get("agent"), "name": w.get("name"), "advisor": _advisor_for(w.get("agent"))} for w in workstreams],
        "diagnosis": {"posture": posture, "critical_risks": crit, "high_risks": high,
                      "headline": f"{title}: {posture} risk posture across {len(workstreams)} workstreams."},
        "executive_summary": exec_summary,
        "workstreams": ws_cards,
        "recommendations": recs,
        "risks": risks,
        "action_plan": actions,
        "kpis": kpis,
        "citations": cites,
        "disclaimer": "AI-generated, research-grade engagement: deterministic specialist analyses curated into one "
                      "report, India-aware. Validate figures and statutory positions with your CA/CS before acting.",
    }


# ---------------------------------------------------------------------------
# Orchestrate
# ---------------------------------------------------------------------------
def orchestrate(body):
    body = body or {}
    desc = (body.get("description") or body.get("idea") or body.get("query") or "").strip()
    intake = body.get("intake") or {}
    # fold loose top-level profile fields into intake (ERP-style form data)
    for k in ("company", "turnover_cr", "headcount", "city_tier", "sector", "business_type", "top_challenges"):
        if body.get(k) not in (None, "") and k not in intake:
            intake[k] = body.get(k)
    if not desc:
        # compose a description from the intake if only the form was filled
        bits = [intake.get("company"), intake.get("business_type") or intake.get("sector"), intake.get("top_challenges")]
        desc = " — ".join([str(b) for b in bits if b]).strip()
    if not desc:
        return {"error": "Describe the business / situation to run an engagement."}
    if not _M:
        return {"error": "msme_agents not loaded"}

    cls = {}
    try:
        cls = _M.classify_business(desc)
    except Exception:
        cls = {"industry": "services", "size": "small", "is_export": False, "is_tech": False, "is_startup": False}

    etype = _ET.get(body.get("engagement_type")) if (_ET and body.get("engagement_type")) else None
    team, routed = select_workstreams(desc, cls, etype)
    scenario = {"description": desc, "data": intake}
    workstreams = []
    for a in team:
        try:
            res = _M.run_agent(a, scenario)
            if res.get("output"):
                workstreams.append(res)
        except Exception:
            continue
    if not workstreams:
        return {"error": "No workstream could be run for this engagement."}
    report = synthesize(desc, cls, intake, workstreams, routed)
    if etype:
        report["engagement_type"] = {k: etype[k] for k in ("key", "name", "tower", "icon", "objective",
                                                            "duration_weeks", "deliverables", "kpis", "value_levers")}
    # Delivery layer: staffed team + AI-supported workplan + hours + billing (Engagement 360).
    if _D:
        try:
            report["delivery"] = _D.build_delivery(report)
        except Exception:
            report["delivery"] = None
    return report


def meta():
    return {
        "what": "Managing-Partner super-agent: one problem -> a multi-workstream, curated Big-4-style engagement.",
        "cross_cutting": ["cfo_finance", "risk_audit", "ceo_copilot"],
        "max_workstreams": 6,
        "endpoints": ["POST /orchestrate", "GET /orchestrate/meta", "GET /orchestrate/tests"],
    }


def run_orchestrator_tests():
    cases = []
    out = orchestrate({"description": "FMCG wholesaler with Rs.10 cr revenue and Rs.2 cr stuck in receivables, cash crunch before GST payment", "intake": {"turnover_cr": 10}})
    cases.append(("cash_engagement", "engagement_id" in out and len(out.get("workstreams", [])) >= 3
                  and len(out.get("recommendations", [])) >= 3 and len(out.get("risks", [])) >= 3
                  and any(w["agent"] in ("o2c_expert", "cfo_finance") for w in out.get("workstreams", []))))
    # determinism
    a = orchestrate({"description": "textile garment exporter in Surat facing margin pressure"})
    b = orchestrate({"description": "textile garment exporter in Surat facing margin pressure"})
    cases.append(("deterministic", a.get("engagement_id") == b.get("engagement_id") and a.get("risks") == b.get("risks")))
    # workstreams carry advisors + curated citations present
    cases.append(("curated", bool(a.get("citations")) and all("advisor" in w for w in a.get("workstreams", []))
                  and a.get("diagnosis", {}).get("posture") in ("Critical", "Elevated", "Watch", "Stable")))
    # different problems -> different teams
    o2 = orchestrate({"description": "founder-led firm at 60 staff, everything routes through the owner, need org design and OKRs"})
    t1 = {w["agent"] for w in a.get("workstreams", [])}
    t2 = {w["agent"] for w in o2.get("workstreams", [])}
    cases.append(("distinct_teams", t1 != t2 and ("org_change" in t2 or "ceo_copilot" in t2)))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    import json
    print(json.dumps(run_orchestrator_tests(), indent=2))
