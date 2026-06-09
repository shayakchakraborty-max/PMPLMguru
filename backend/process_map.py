"""
process_map.py — "Process & Value-Stream Copilot" for the MSME Consulting OS.

Deterministic, no external deps. This is the consulting-firm copilot the user asked
for: feed a business description (or a playbook key / business_type) and it auto-fills,
exactly like a Big-firm engagement team would:

  * an ENGAGEMENT TEAM (Partner -> Director -> Manager -> Sr Consultant -> Consultants),
    each with a mandate, the artifacts they own, and a contextual copilot note;
  * a PROCESS MAP — the end-to-end value chain rendered as SCOR-style swimlanes
    (Plan / Source / Make / Deliver / Service) with sub-steps, owning role, systems,
    and bottleneck flags;
  * a VALUE-STREAM MAP in the exact blueprint format
    (Step | Cycle time | Waiting time | First-pass yield | Main waste | AI action)
    with computed totals: total lead time, value-add time, process-cycle-efficiency,
    rolled throughput yield;
  * a bottleneck -> AI-action plan, and a headline summary.

Source data is reused from industry_playbooks (value_chain, core_processes,
operational_bottlenecks, ai_automation_opportunities) and msme_agents (classifier).
Numbers are derived deterministically from a stable text hash so the same business
always yields the same map (no Date.now / random) — they are illustrative planning
figures, clearly labelled as such, not measured client data.

Endpoint (wired in main.py): POST /process  (also GET /process/meta, /process/tests).
The main.py handler may add an optional Groq narrative ("partner_brief"); the core
here is always deterministic and never raises hard.
"""

try:
    import industry_playbooks as _PB
except Exception:
    _PB = None

try:
    import msme_agents as _M
except Exception:
    _M = None


# ----------------------------------------------------------------------------
# Deterministic pseudo-numbers (stable per text; no random, no Date)
# ----------------------------------------------------------------------------
def _seed(text):
    h = 2166136261
    for ch in str(text):
        h = (h ^ ord(ch)) * 16777619 & 0xFFFFFFFF
    return h


def _band(text, lo, hi, salt="", nd=2):
    """Stable value in [lo, hi] from the hash of text+salt."""
    frac = (_seed(str(text) + salt) % 10000) / 10000.0
    return round(lo + frac * (hi - lo), nd)


# ----------------------------------------------------------------------------
# Engagement team — the consulting-firm hierarchy (the "copilot personas")
# ----------------------------------------------------------------------------
def engagement_team(name, cls, bottlenecks, vsm):
    top_bn = (bottlenecks[0]["bottleneck"] if bottlenecks else "operational variance")
    pce = vsm["totals"]["process_cycle_efficiency_pct"]
    lead = vsm["totals"]["total_lead_time_days"]
    waste = vsm["totals"]["top_waste"]
    sector = (cls or {}).get("industry", "business").replace("_", " ")
    return [
        {
            "role": "Engagement Partner", "level": 1, "avatar": "🤝",
            "title": "Owns the relationship & the result",
            "mandate": "Owns the client relationship, the value-at-stake thesis and the quality bar. "
                       "Signs off on final recommendations and is accountable for delivered impact.",
            "owns": ["Value-at-stake & ROI sign-off", "Final recommendations", "Steering-committee narrative"],
            "maps_to": "Blueprint agent: Engagement Director (problem ownership + quality bar)",
            "copilot_note": f"For this {sector} business the prize is clear: process-cycle efficiency is only "
                            f"{pce}% against a ~{lead:.0f}-day order-to-cash lead time, so most of the cash is "
                            f"trapped in waiting, not working. I'd anchor the engagement on releasing that.",
        },
        {
            "role": "Engagement Director", "level": 2, "avatar": "🧭",
            "title": "Designs the engagement & the future state",
            "mandate": "Designs the engagement, owns the to-be process architecture and the value-stream thesis, "
                       "and arbitrates trade-offs across workstreams.",
            "owns": ["Future-state process design", "Value-stream thesis", "Workstream arbitration"],
            "maps_to": "Blueprint agent: Operations & Lean lead",
            "copilot_note": f"The current-state map shows the constraint sits at '{top_bn}'. The future-state design "
                            f"should attack that first — everything downstream inherits its variance.",
        },
        {
            "role": "Engagement Manager", "level": 3, "avatar": "📋",
            "title": "Runs the workstreams day-to-day",
            "mandate": "Runs the workstreams, owns the bottleneck-to-solution plan, the 90-day roadmap and the "
                       "weekly benefit tracking.",
            "owns": ["Bottleneck → solution plan", "90-day roadmap", "Weekly benefit tracking"],
            "maps_to": "Blueprint agent: PMO & execution",
            "copilot_note": f"I've sequenced {len(bottlenecks)} bottleneck(s) into the roadmap. The top "
                            f"'{waste}' waste is the fastest lever — owner-assigned and trackable from week one.",
        },
        {
            "role": "Senior Consultant", "level": 4, "avatar": "📊",
            "title": "Builds the value-stream map & diagnostics",
            "mandate": "Builds the value-stream map, quantifies waste and waiting, and runs the financial and "
                       "operational diagnostics that prove the opportunity.",
            "owns": ["Value-stream map", "Waste & waiting quantification", "Diagnostic models"],
            "maps_to": "Blueprint agent: Finance & working-capital lead",
            "copilot_note": f"Quantified: ~{vsm['totals']['wait_time_days']:.1f} days of the lead time is pure "
                            f"waiting vs ~{vsm['totals']['value_add_time_days']:.1f} days of value-add work. "
                            f"That gap is the business case.",
        },
        {
            "role": "Consultants", "level": 5, "avatar": "🛠️",
            "title": "Map the processes & build the artifacts",
            "mandate": "Gather data, map the sub-processes and swimlanes, build the SOPs and dashboards, and keep "
                       "the evidence base clean and source-linked.",
            "owns": ["Process & swimlane mapping", "SOP drafts", "Data & KPI collection"],
            "maps_to": "Blueprint agents: Research/benchmark + Deliverable architect",
            "copilot_note": "Each stage below is mapped with sub-steps, an owning role and the systems it touches — "
                            "ready to validate on a site walk-through and turn into SOPs.",
        },
    ]


# ----------------------------------------------------------------------------
# Swimlane (SCOR-style) + waste classification
# ----------------------------------------------------------------------------
_LANES = [
    ("Plan", ("plan", "assort", "category", "forecast", "demand", "schedul", "design", "ideation", "r&d", "budget")),
    ("Source", ("sourc", "procure", "vendor", "supplier", "purchase", "inbound", "raw material", "import", "ingredient")),
    ("Make", ("produc", "manufactur", "assembl", "process", "build", "cook", "fabricat", "quality", "qc", "develop", "merchand")),
    ("Deliver", ("logist", "dispatch", "delivery", "distribut", "warehous", "replenish", "pos", "checkout", "billing", "invoice", "export", "outbound", "store")),
    ("Service", ("service", "support", "loyalty", "crm", "return", "claim", "after", "warranty", "collection", "reverse", "customer")),
]


def _lane_for(text):
    t = (text or "").lower()
    for lane, kws in _LANES:
        if any(k in t for k in kws):
            return lane
    return "Make"


_WASTES = [
    ("Waiting", ("wait", "delay", "approval", "idle", "queue", "lead time", "slow")),
    ("Defects", ("defect", "rework", "error", "mismatch", "reject", "quality", "damage", "expiry", "return")),
    ("Inventory", ("inventory", "stock", "dead stock", "overstock", "wip", "expiry", "ageing")),
    ("Overprocessing", ("manual", "duplicate", "re-enter", "paperwork", "rekey", "redundant")),
    ("Transportation", ("transport", "logist", "movement", "freight", "route")),
    ("Motion", ("search", "fetch", "walk", "handoff", "coordination")),
    ("Overproduction", ("overproduc", "batch", "excess", "build-ahead")),
    ("Talent", ("skill", "training", "manpower", "labour", "underutil")),
]


def _waste_for(text):
    t = (text or "").lower()
    for w, kws in _WASTES:
        if any(k in t for k in kws):
            return w
    return "Waiting"


def _short(text, n=46):
    t = (text or "").split("(")[0].strip()
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


# ----------------------------------------------------------------------------
# Bottleneck matching to a stage
# ----------------------------------------------------------------------------
_STOP = set("the a an and or of to for with in on at by from is are as per its their your our & + -".split())


def _kw(text):
    return {w for w in (text or "").lower().replace("/", " ").replace(",", " ").split() if w not in _STOP and len(w) > 3}


def _best_match(stage_text, items, text_key):
    sk = _kw(stage_text)
    best, score = None, 0
    for it in items or []:
        ov = len(sk & _kw(it.get(text_key, "")))
        if ov > score:
            score, best = ov, it
    return best if score >= 1 else None


# ----------------------------------------------------------------------------
# Value-Stream Map (the blueprint table) + totals
# ----------------------------------------------------------------------------
def build_value_stream(name, stages, bottlenecks, ai_ops):
    rows = []
    for i, st in enumerate(stages):
        is_bn = bool(st.get("is_bottleneck"))
        # cycle (value-add processing) small; wait (queue/approval) larger; worse when bottlenecked
        cycle = _band(st["stage"], 0.25, 2.5, salt="c")
        wait = _band(st["stage"], 0.5, 6.0, salt="w") + (_band(st["stage"], 3.0, 9.0, salt="bw") if is_bn else 0)
        fpy = round(_band(st["stage"], 90, 99, salt="y") - (_band(st["stage"], 6, 14, salt="by") if is_bn else 0), 1)
        bn = st.get("bottleneck")
        waste = _waste_for((bn or {}).get("symptom", "") + " " + st["stage"]) if bn else _waste_for(st["stage"])
        ai = _best_match(st["stage"], ai_ops, "opportunity")
        ai_action = (ai.get("opportunity") if ai else None) or _generic_ai_action(st["lane"])
        rows.append({
            "step": _short(st["stage"], 40),
            "lane": st["lane"],
            "cycle_time_days": round(cycle, 2),
            "wait_time_days": round(wait, 2),
            "first_pass_yield_pct": fpy,
            "main_waste": waste,
            "is_bottleneck": is_bn,
            "ai_action": ai_action,
            "ai_agent": (ai or {}).get("agent"),
        })
    # totals
    va = sum(r["cycle_time_days"] for r in rows)
    wt = sum(r["wait_time_days"] for r in rows)
    lead = va + wt
    pce = round(va / lead * 100, 1) if lead else 0
    rty = 1.0
    for r in rows:
        rty *= r["first_pass_yield_pct"] / 100.0
    waste_count = {}
    for r in rows:
        waste_count[r["main_waste"]] = waste_count.get(r["main_waste"], 0) + 1
    top_waste = max(waste_count, key=waste_count.get) if waste_count else "Waiting"
    return {
        "columns": ["Step", "Cycle time (days)", "Waiting time (days)", "First-pass yield", "Main waste", "AI-generated action"],
        "rows": rows,
        "totals": {
            "value_add_time_days": round(va, 1),
            "wait_time_days": round(wt, 1),
            "total_lead_time_days": round(lead, 1),
            "process_cycle_efficiency_pct": pce,
            "rolled_throughput_yield_pct": round(rty * 100, 1),
            "top_waste": top_waste,
        },
    }


def _generic_ai_action(lane):
    return {
        "Plan": "AI demand forecast + auto-replenishment to cut guesswork and dead stock",
        "Source": "Automated 3-way match (PO vs invoice vs GRN) to plug margin leakage",
        "Make": "AI bottleneck & yield analytics with digital SOP checklists",
        "Deliver": "Auto-indent, route optimisation and GST-compliant e-invoicing",
        "Service": "Receivables ageing triggers + AI collection prioritisation",
    }.get(lane, "AI workflow automation with exception alerts")


# ----------------------------------------------------------------------------
# Process Map — value chain -> swimlane stages with sub-steps & owners
# ----------------------------------------------------------------------------
_OWNER_CYCLE = ["Consultants", "Senior Consultant", "Consultants", "Engagement Manager", "Senior Consultant"]


def build_process_map(value_chain, core_processes, bottlenecks):
    stages = []
    for i, vc in enumerate(value_chain):
        bn = _best_match(vc, bottlenecks, "bottleneck") or _best_match(vc, bottlenecks, "symptom")
        proc = _best_match(vc, core_processes, "process")
        substeps = []
        if proc:
            desc = proc.get("description", "")
            # split a process description into 2-3 crisp sub-steps
            parts = [p.strip() for p in desc.replace(";", ".").split(".") if len(p.strip()) > 12][:3]
            substeps = [_short(p, 70) for p in parts] or [_short(desc, 70)]
        if not substeps:
            substeps = [f"Execute {_short(vc, 50).lower()}", "Record, check & hand off to next stage"]
        owner = "Engagement Manager" if bn else _OWNER_CYCLE[i % len(_OWNER_CYCLE)]
        stages.append({
            "id": i,
            "stage": vc,
            "short": _short(vc, 40),
            "lane": _lane_for(vc),
            "type": "bottleneck" if bn else ("value_add" if i % 3 != 2 else "necessary"),
            "process_name": (proc or {}).get("process"),
            "substeps": substeps,
            "owner_role": owner,
            "is_bottleneck": bool(bn),
            "bottleneck": ({
                "title": bn.get("bottleneck"),
                "symptom": bn.get("symptom"),
                "impact": bn.get("impact"),
                "root_cause": bn.get("root_cause"),
            } if bn else None),
        })
    return stages


def _lane_summary(stages):
    out = []
    for lane, _ in _LANES:
        ids = [s["id"] for s in stages if s["lane"] == lane]
        if ids:
            out.append({"lane": lane, "stage_ids": ids,
                        "bottlenecks": sum(1 for s in stages if s["lane"] == lane and s["is_bottleneck"])})
    return out


# ----------------------------------------------------------------------------
# Bottleneck -> AI action plan
# ----------------------------------------------------------------------------
def action_plan(stages, ai_ops):
    plan = []
    for s in stages:
        if not s["is_bottleneck"]:
            continue
        bn = s["bottleneck"]
        ai = _best_match(s["stage"], ai_ops, "opportunity")
        plan.append({
            "stage": s["short"], "lane": s["lane"],
            "bottleneck": bn["title"], "root_cause": bn["root_cause"], "impact": bn["impact"],
            "fix": (ai.get("opportunity") if ai else _generic_ai_action(s["lane"])),
            "agent": (ai or {}).get("agent"),
            "effort": (ai or {}).get("effort", "Medium"),
            "impact_rating": (ai or {}).get("impact", "High"),
            "owner": "Engagement Manager",
        })
    return plan


# ----------------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------------
def process_map(body):
    body = body or {}
    desc = (body.get("description") or body.get("idea") or "").strip()
    key = (body.get("key") or body.get("business_type") or "").strip()

    pb, matched_key, how = (None, None, "none")
    if _PB:
        try:
            pb, matched_key, how = _PB.resolve(business_type=key or None, key=key or None, description=desc or None)
        except Exception:
            pb = None
    cls = {}
    if _M and desc:
        try:
            cls = _M.classify_business(desc)
        except Exception:
            cls = {}

    if not pb:
        # Generic fallback value chain so the copilot ALWAYS returns something useful.
        name = desc[:60] or "Your business"
        value_chain = [
            "Demand planning & order intake", "Sourcing & procurement", "Inbound & inventory",
            "Production / service delivery", "Quality check & packing", "Dispatch & distribution",
            "Billing & invoicing", "Collections & after-sales service",
        ]
        core_processes, bottlenecks, ai_ops, kpis = [], _generic_bottlenecks(), [], []
    else:
        name = pb.get("name", desc[:60] or "Your business")
        wa = pb.get("workflow_architecture", {}) or {}
        value_chain = wa.get("value_chain", []) or []
        core_processes = wa.get("core_processes", []) or []
        bottlenecks = pb.get("operational_bottlenecks", []) or []
        ai_ops = pb.get("ai_automation_opportunities", []) or []
        kpis = pb.get("kpi_structure", []) or []

    stages = build_process_map(value_chain, core_processes, bottlenecks)
    vsm = build_value_stream(name, stages, bottlenecks, ai_ops)
    team = engagement_team(name, cls, bottlenecks, vsm)
    plan = action_plan(stages, ai_ops)

    t = vsm["totals"]
    summary = {
        "headline": f"{name}: {t['total_lead_time_days']:.0f}-day order-to-cash lead time at "
                    f"{t['process_cycle_efficiency_pct']:.0f}% process-cycle efficiency.",
        "metrics": [
            {"label": "Total lead time", "value": f"{t['total_lead_time_days']:.1f}", "unit": "days", "tone": "amber"},
            {"label": "Value-add time", "value": f"{t['value_add_time_days']:.1f}", "unit": "days", "tone": "emerald"},
            {"label": "Process-cycle efficiency", "value": f"{t['process_cycle_efficiency_pct']:.0f}", "unit": "%",
             "tone": "rose" if t["process_cycle_efficiency_pct"] < 25 else "amber"},
            {"label": "Rolled throughput yield", "value": f"{t['rolled_throughput_yield_pct']:.0f}", "unit": "%",
             "tone": "rose" if t["rolled_throughput_yield_pct"] < 70 else "emerald"},
            {"label": "Bottlenecks found", "value": str(sum(1 for s in stages if s["is_bottleneck"])), "unit": "stages", "tone": "rose"},
        ],
        "biggest_waste": t["top_waste"],
    }

    return {
        "business": name,
        "matched_by": how,
        "playbook_key": matched_key,
        "tier": (pb or {}).get("tier"),
        "icon": (pb or {}).get("icon", "🏭"),
        "classification": cls,
        "engagement_team": team,
        "summary": summary,
        "process_map": {"stages": stages, "lanes": _lane_summary(stages)},
        "value_stream_map": vsm,
        "action_plan": plan,
        "kpis": kpis[:6],
        "disclaimer": "Cycle/wait times, yields and lead-time figures are deterministic, illustrative planning "
                      "estimates derived from the sector value stream — not measured client data. Validate on a "
                      "site walk-through before committing to targets.",
    }


def _generic_bottlenecks():
    return [
        {"bottleneck": "Receivables stretching beyond terms",
         "symptom": "Invoices ageing past 60 days; cash tied up in debtors",
         "impact": "Working-capital crunch and stalled growth",
         "root_cause": "No ageing discipline, weak credit control and manual follow-ups"},
        {"bottleneck": "Stockouts alongside dead stock",
         "symptom": "Fast movers out of stock while slow SKUs pile up",
         "impact": "Lost sales plus capital trapped in dead inventory",
         "root_cause": "Reorder points set on gut feel, not demand velocity"},
    ]


# ----------------------------------------------------------------------------
# Meta + self-test
# ----------------------------------------------------------------------------
def meta():
    types = []
    if _PB:
        try:
            types = [{"key": p.get("key"), "name": p.get("name"), "icon": p.get("icon"), "tier": p.get("tier")}
                     for p in _PB.PLAYBOOKS]
        except Exception:
            types = []
    return {
        "business_types": types,
        "lanes": [l for l, _ in _LANES],
        "vsm_columns": ["Step", "Cycle time", "Waiting time", "First-pass yield", "Main waste", "AI-generated action"],
        "team_roles": ["Engagement Partner", "Engagement Director", "Engagement Manager", "Senior Consultant", "Consultants"],
        "endpoints": ["POST /process", "GET /process/meta", "GET /process/tests"],
    }


def run_process_tests():
    cases = []
    # 1. matched playbook -> full map
    out = process_map({"description": "8-store kirana grocery retail chain in Pune"})
    cases.append(("matched_full", out.get("matched_by") in ("matched", "key")
                  and len(out["process_map"]["stages"]) >= 5
                  and len(out["value_stream_map"]["rows"]) == len(out["process_map"]["stages"])
                  and len(out["engagement_team"]) == 5))
    # 2. determinism — same input twice -> identical lead time
    a = process_map({"description": "textile garment exporter in Surat"})["value_stream_map"]["totals"]
    b = process_map({"description": "textile garment exporter in Surat"})["value_stream_map"]["totals"]
    cases.append(("deterministic", a == b))
    # 3. totals coherent (PCE between 0-100, lead = va + wait)
    t = out["value_stream_map"]["totals"]
    cases.append(("totals_coherent", 0 <= t["process_cycle_efficiency_pct"] <= 100
                  and abs(t["total_lead_time_days"] - (t["value_add_time_days"] + t["wait_time_days"])) < 0.2))
    # 4. generic fallback for an unknown business still returns a usable map
    g = process_map({"description": "zxqw nonsense unmatched business 12345"})
    cases.append(("fallback", len(g["process_map"]["stages"]) >= 5 and len(g["engagement_team"]) == 5))
    # 5. every team role present
    roles = {m["role"] for m in out["engagement_team"]}
    cases.append(("team_roles", roles == {"Engagement Partner", "Engagement Director", "Engagement Manager",
                                          "Senior Consultant", "Consultants"}))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    import json
    print(json.dumps(run_process_tests(), indent=2))
