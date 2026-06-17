"""
engagement_360.py — the delivery layer: staffed team, AI-supported workplan, hours,
billing and the Engagement 360 view.

The orchestrator produces the *analysis* (workstreams, recommendations, risks). This
module turns that into how a real firm *runs* the engagement:
  * a staffed TEAM across the consulting hierarchy (Senior Partner → Junior Consultant
    + SME, QA/Risk reviewer, and client-side parties), each paired with an AI advisor;
  * an AI-supported WORKPLAN — phased tasks, each owned by a role AND backed by a
    specific AI agent that does the heavy lifting (with an honest AI-automation % and a
    human sign-off where it matters);
  * HOURS by role + BILLING (master-data rate card, T&M vs fixed-fee options, blended
    rate, margin);
  * everything assembled so each person sees *their* task list with AI support, and the
    partner gets the full Engagement 360.

Deterministic (stable per-text estimates, no random/Date). India-MSME-advisory rate card
(₹), clearly indicative. Used by orchestrator.orchestrate() to add report["delivery"].
"""

# ---------------------------------------------------------------------------
# MASTER DATA — consulting hierarchy + ₹ rate card (indicative India MSME advisory)
# ---------------------------------------------------------------------------
ROLES = [
    {"key": "senior_partner",    "title": "Senior Partner",       "level": 1, "rate": 25000, "billable": True,
     "mandate": "Owns the client relationship and the result; signs off on the final recommendations.", "ai_advisor": "AI Managing Partner"},
    {"key": "partner",           "title": "Partner",              "level": 2, "rate": 18000, "billable": True,
     "mandate": "Quality bar, executive narrative, challenge sessions and value assurance.", "ai_advisor": "AI Engagement Partner"},
    {"key": "engagement_director","title": "Engagement Director",  "level": 3, "rate": 12000, "billable": True,
     "mandate": "Designs the engagement and the future state; arbitrates across workstreams.", "ai_advisor": "AI Strategy Consultant"},
    {"key": "engagement_manager","title": "Engagement Manager",   "level": 4, "rate": 8000,  "billable": True,
     "mandate": "Runs the engagement day-to-day; owns the workplan, PMO and weekly tracking.", "ai_advisor": "AI PMO Consultant"},
    {"key": "senior_consultant", "title": "Senior Consultant",    "level": 5, "rate": 5000,  "billable": True,
     "mandate": "Leads a workstream: diagnosis, models and recommendations.", "ai_advisor": "AI Research Analyst"},
    {"key": "consultant",        "title": "Consultant",           "level": 6, "rate": 3000,  "billable": True,
     "mandate": "Executes the analysis, builds models and drafts deliverables.", "ai_advisor": "AI Benchmarking Analyst"},
    {"key": "junior_consultant", "title": "Junior Consultant",    "level": 7, "rate": 1800,  "billable": True,
     "mandate": "Gathers data, runs research and supports the workstreams.", "ai_advisor": "AI Research Analyst"},
    {"key": "sme",               "title": "Subject-Matter Expert", "level": 4, "rate": 10000, "billable": True,
     "mandate": "Deep domain expertise on the lead practice for this engagement.", "ai_advisor": "AI Domain Specialist"},
    {"key": "qa_risk",           "title": "Quality & Risk Reviewer", "level": 4, "rate": 9000, "billable": True,
     "mandate": "Independent quality gate: groundedness, citations, risk and compliance.", "ai_advisor": "AI QA & Citation Verifier"},
    # Client-side / other parties (non-billable; appear in the stakeholder view)
    {"key": "client_sponsor",    "title": "Client Sponsor",       "level": 0, "rate": 0, "billable": False,
     "mandate": "Executive owner on the client side; approves scope, decisions and benefits.", "ai_advisor": "AI Executive Briefing"},
    {"key": "client_spoc",       "title": "Client SPOC",          "level": 0, "rate": 0, "billable": False,
     "mandate": "Single point of contact; coordinates data, access and reviews.", "ai_advisor": None},
]
_ROLE = {r["key"]: r for r in ROLES}

PHASES = [
    {"key": "mobilize", "name": "Mobilize", "weeks": 1},
    {"key": "diagnose", "name": "Diagnose", "weeks": 3},
    {"key": "design",   "name": "Design",   "weeks": 3},
    {"key": "validate", "name": "Validate", "weeks": 1},
    {"key": "deliver",  "name": "Deliver",  "weeks": 1},
]

FEE_MODELS = ["Time & Materials", "Fixed Fee", "Monthly Retainer", "Outcome-linked (capped)"]


# ---------------------------------------------------------------------------
# Deterministic estimate helper
# ---------------------------------------------------------------------------
def _seed(text):
    h = 2166136261
    for ch in str(text):
        h = (h ^ ord(ch)) * 16777619 & 0xFFFFFFFF
    return h


def _band(text, lo, hi, salt=""):
    return lo + (_seed(str(text) + salt) % (hi - lo + 1))


def _task(tid, title, phase, owner, ai_agent, ai_support, hours, ai_pct, deliverable, approver=None):
    return {"id": tid, "title": title, "phase": phase, "owner_role": owner, "ai_agent": ai_agent,
            "ai_support": ai_support, "est_hours": hours, "ai_automation_pct": ai_pct,
            "status": "Not started", "deliverable": deliverable, "approver_role": approver}


def _advisor_name(agent, report):
    for a in (report.get("agents_engaged") or []):
        if a.get("agent") == agent:
            return a.get("advisor") or a.get("name")
    return agent


# ---------------------------------------------------------------------------
# Build the workplan (AI-supported, role-owned tasks)
# ---------------------------------------------------------------------------
def _build_workplan(report):
    title = report.get("title", "the business")
    ws = report.get("workstreams") or []
    tasks = []
    n = 0

    def add(*a, **k):
        nonlocal n
        n += 1
        tasks.append(_task(f"T{n:02d}", *a, **k))

    # Mobilize
    add("Engagement kickoff & charter", "mobilize", "engagement_director", "ceo_copilot",
        "AI drafts the charter, scope, objectives and success metrics from the brief.",
        _band(title, 6, 10, "kick"), 45, "Engagement charter", approver="partner")
    add("Stakeholder map & data request list", "mobilize", "engagement_manager", "ceo_copilot",
        "AI generates the stakeholder map and the precise data-request checklist.",
        _band(title, 5, 9, "stk"), 65, "Stakeholder map + data request", approver="engagement_director")

    # Diagnose + Design per workstream (AI agent does the heavy lifting)
    for w in ws:
        ag = w.get("agent")
        adv = w.get("advisor") or ag
        lead = "sme" if ag in (report.get("routed_to") or {}).get("agent", "") else "senior_consultant"
        add(f"Diagnose: {w.get('name', ag)}", "diagnose", "senior_consultant", ag,
            f"{adv} runs the full diagnostic envelope (analysis, benchmarks, risks) for review.",
            _band(ag + "d", 10, 18), 75, f"{w.get('name', ag)} diagnostic", approver="engagement_manager")
        add(f"Data & analysis: {w.get('name', ag)}", "diagnose", "consultant", ag,
            f"{adv} builds the models and quantification; consultant validates inputs.",
            _band(ag + "a", 8, 16), 80, "Analysis pack", approver="senior_consultant")
        add(f"Design recommendations: {w.get('name', ag)}", "design", "senior_consultant", ag,
            f"{adv} drafts prioritised, evidence-backed recommendations + the action plan.",
            _band(ag + "r", 8, 14), 65, "Recommendation set", approver="engagement_director")

    # Cross-cutting research support
    add("Benchmarking & market evidence", "diagnose", "junior_consultant", "competitor_intel",
        "AI pulls sector benchmarks, market sizing and competitor evidence with citations.",
        _band(title, 8, 14, "bm"), 80, "Benchmark pack", approver="senior_consultant")
    add("Consolidate findings & value-at-stake", "design", "engagement_manager", "cfo_finance",
        "AI consolidates workstream findings into one value-at-stake and a 90-day plan.",
        _band(title, 8, 12, "cons"), 60, "Synthesis + value case", approver="engagement_director")

    # Validate
    add("Quality, citation & risk review", "validate", "qa_risk", "risk_audit",
        "AI QA verifier checks groundedness, citations, hallucination and compliance.",
        _band(title, 6, 10, "qa"), 55, "QA sign-off", approver="partner")
    add("Partner review & challenge session", "validate", "partner", "ceo_copilot",
        "AI prepares the challenge pack (assumptions, sensitivities, counter-arguments).",
        _band(title, 4, 7, "pr"), 25, "Reviewed recommendations", approver="senior_partner")

    # Deliver
    add("Board-ready report & executive readout", "deliver", "engagement_manager", "product_manager",
        "AI assembles the Big-4-style deck/report and the executive readout narrative.",
        _band(title, 8, 14, "rep"), 70, "Board pack + readout", approver="partner")
    add("Final sign-off & benefits plan", "deliver", "senior_partner", "ceo_copilot",
        "AI drafts the benefits-realisation plan; Senior Partner signs off the engagement.",
        _band(title, 3, 5, "sign"), 15, "Signed recommendations + benefits plan", approver=None)

    return tasks


# ---------------------------------------------------------------------------
# Team, hours, billing
# ---------------------------------------------------------------------------
def _build_team(tasks, report):
    used = {}
    for t in tasks:
        used[t["owner_role"]] = used.get(t["owner_role"], 0) + t["est_hours"]
    team = []
    for r in ROLES:
        if not r["billable"]:
            continue
        hrs = used.get(r["key"], 0)
        if hrs == 0 and r["key"] not in ("senior_partner", "partner", "engagement_director", "engagement_manager"):
            continue  # only staff billable roles that have work (leadership always on)
        team.append({
            "role": r["title"], "role_key": r["key"], "level": r["level"], "rate_per_hour": r["rate"],
            "ai_advisor": r["ai_advisor"], "mandate": r["mandate"],
            "allocated_hours": hrs,
        })
    # client-side parties (non-billable) always shown
    for r in ROLES:
        if not r["billable"]:
            team.append({"role": r["title"], "role_key": r["key"], "level": r["level"], "rate_per_hour": 0,
                         "ai_advisor": r["ai_advisor"], "mandate": r["mandate"], "allocated_hours": 0, "client_side": True})
    team.sort(key=lambda x: (x.get("client_side", False), x["level"]))
    return team


def _inr(n):
    return f"₹{n:,.0f}"


def _build_economics(tasks):
    by_role = {}
    for t in tasks:
        rk = t["owner_role"]
        r = _ROLE.get(rk, {})
        by_role.setdefault(rk, {"role": r.get("title", rk), "hours": 0, "rate": r.get("rate", 0)})
        by_role[rk]["hours"] += t["est_hours"]
    rows = []
    total_hours = total_fee = 0
    for rk, d in by_role.items():
        cost = d["hours"] * d["rate"]
        total_hours += d["hours"]
        total_fee += cost
        rows.append({"role": d["role"], "hours": d["hours"], "rate_per_hour": d["rate"],
                     "amount": cost, "amount_label": _inr(cost)})
    rows.sort(key=lambda x: x["amount"], reverse=True)
    blended = round(total_fee / total_hours) if total_hours else 0
    fixed = round(total_fee * 0.9)            # fixed-fee = T&M less ~10% (efficiency share)
    weeks = sum(p["weeks"] for p in PHASES)
    retainer = round(total_fee / max(1, weeks) * 4.33)  # ~monthly
    ai_weighted = sum(t["est_hours"] * t["ai_automation_pct"] for t in tasks)
    ai_leverage = round(ai_weighted / total_hours) if total_hours else 0
    return {
        "rate_card": [{"role": r["title"], "rate_per_hour": r["rate"], "rate_label": _inr(r["rate"])} for r in ROLES if r["billable"]],
        "by_role": rows,
        "total_hours": total_hours,
        "duration_weeks": weeks,
        "tm_fee": total_fee, "tm_fee_label": _inr(total_fee),
        "fixed_fee": fixed, "fixed_fee_label": _inr(fixed),
        "monthly_retainer": retainer, "monthly_retainer_label": _inr(retainer),
        "blended_rate": blended, "blended_rate_label": _inr(blended),
        "fee_models": FEE_MODELS,
        "ai_leverage_pct": ai_leverage,
        "note": "Indicative ₹ rate card and AI-assisted effort estimates for Indian MSME advisory — not a quote. "
                f"AI agents do ~{ai_leverage}% of the task effort; humans review, decide and sign off.",
    }


# ---------------------------------------------------------------------------
# Public: build the delivery layer + role task lists
# ---------------------------------------------------------------------------
def build_delivery(report):
    """Attach team + AI-supported workplan + hours + billing to an orchestrated report."""
    if not report or report.get("error"):
        return None
    tasks = _build_workplan(report)
    team = _build_team(tasks, report)
    econ = _build_economics(tasks)
    phases = []
    for p in PHASES:
        pt = [t for t in tasks if t["phase"] == p["key"]]
        phases.append({"key": p["key"], "name": p["name"], "weeks": p["weeks"],
                       "task_ids": [t["id"] for t in pt], "hours": sum(t["est_hours"] for t in pt)})
    # role -> their task list (so each person sees "my tasks" with AI support)
    by_role_tasks = {}
    for t in tasks:
        by_role_tasks.setdefault(t["owner_role"], []).append(t["id"])
    return {
        "team": team,
        "phases": phases,
        "workplan": tasks,
        "task_count": len(tasks),
        "by_role_tasks": by_role_tasks,
        "economics": econ,
        "roles": [{"key": r["key"], "title": r["title"], "level": r["level"], "billable": r["billable"]} for r in ROLES],
        "ai_leverage_pct": econ["ai_leverage_pct"],
    }


def role_tasks(report, role_key):
    """The task list + AI support for one role (the 'when they open the UI' view)."""
    delivery = report.get("delivery") or build_delivery(report)
    tasks = [t for t in (delivery.get("workplan") or []) if t["owner_role"] == role_key]
    r = _ROLE.get(role_key, {})
    return {"role": r.get("title", role_key), "role_key": role_key, "mandate": r.get("mandate"),
            "ai_advisor": r.get("ai_advisor"), "task_count": len(tasks), "tasks": tasks}


def meta():
    return {"roles": [{"key": r["key"], "title": r["title"], "rate_per_hour": r["rate"], "billable": r["billable"]} for r in ROLES],
            "phases": [p["name"] for p in PHASES], "fee_models": FEE_MODELS,
            "what": "Delivery layer: staffed team + AI-supported workplan + hours + billing + Engagement 360."}


def run_360_tests():
    cases = []
    rep = {
        "title": "Test MSME", "sector": "Retail Trade",
        "agents_engaged": [{"agent": "cfo_finance", "advisor": "AI CFO Advisor"}, {"agent": "inventory_agent", "advisor": "AI Supply Chain Advisor"}],
        "workstreams": [{"agent": "cfo_finance", "name": "CFO", "advisor": "AI CFO Advisor"},
                        {"agent": "inventory_agent", "name": "Inventory", "advisor": "AI Supply Chain Advisor"}],
        "routed_to": {"agent": "inventory_agent"},
    }
    d = build_delivery(rep)
    cases.append(("workplan", d["task_count"] >= 10 and all(t["owner_role"] and t["ai_agent"] for t in d["workplan"])))
    cases.append(("phases_cover", {p["key"] for p in d["phases"]} == {"mobilize", "diagnose", "design", "validate", "deliver"}))
    cases.append(("team_hierarchy", any(m["role_key"] == "senior_partner" for m in d["team"]) and any(m.get("client_side") for m in d["team"])))
    e = d["economics"]
    cases.append(("billing", e["total_hours"] > 0 and e["tm_fee"] > 0 and e["blended_rate"] > 0 and 0 < e["ai_leverage_pct"] <= 100))
    rt = role_tasks({**rep, "delivery": d}, "senior_consultant")
    cases.append(("role_tasks", rt["task_count"] >= 1 and all(t["owner_role"] == "senior_consultant" for t in rt["tasks"])))
    # determinism
    cases.append(("deterministic", build_delivery(rep)["economics"]["tm_fee"] == e["tm_fee"]))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    import json
    print(json.dumps(run_360_tests(), indent=2))
