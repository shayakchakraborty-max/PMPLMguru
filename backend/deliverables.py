"""
deliverables.py — AI deliverable generation: turn an engagement into top-firm-format
documents (board deck + executive memo) on completion.

Big-3/Big-4 decks are action-titled and MECE: every slide title states the "so-what",
the body carries the evidence. This builds that structure deterministically from the
engagement report (exec summary, findings, recommendations, roadmap, financials, risks,
KPIs, citations) and renders it as Markdown (one '---' per slide) ready to download or
paste into PowerPoint/Google Slides. A native .pptx export (python-pptx) is a deploy-time
add — the slide model here is the contract it will consume.

Deterministic, no deps. Endpoint (main.py): POST /deliverable (+ GET /deliverable/meta|tests).
"""


def _slide(n, title, body_type, content):
    return {"n": n, "title": title, "type": body_type, "content": content}


def build_deck(report):
    """A board-ready, action-titled deck model + a Markdown rendering."""
    if not report or report.get("error"):
        return {"error": "no engagement to build from"}
    title = report.get("title", "Engagement")
    sector = report.get("sector", "")
    diag = report.get("diagnosis") or {}
    et = report.get("engagement_type") or {}
    delivery = report.get("delivery") or {}
    econ = delivery.get("economics") or {}
    ws = report.get("workstreams") or []
    recs = report.get("recommendations") or []
    risks = report.get("risks") or []
    plan = report.get("action_plan") or []
    kpis = report.get("kpis") or []
    cites = report.get("citations") or []

    slides = []
    slides.append(_slide(1, f"{title} — {et.get('name','Engagement')} readout", "cover",
                         {"subtitle": f"{sector} · AI Consulting OS · confidential", "posture": diag.get("posture")}))
    slides.append(_slide(2, f"The situation demands a {diag.get('posture','focused').lower()} response", "bullets",
                         [report.get("executive_summary", "")] + ([et.get("objective")] if et.get("objective") else [])))
    slides.append(_slide(3, "We staffed an AI-led, multi-disciplinary team", "bullets",
                         [f"{a.get('advisor') or a.get('name')}" for a in (report.get("agents_engaged") or [])] or [w.get("name") for w in ws]))
    slides.append(_slide(4, "The diagnostic surfaced the issues that matter", "bullets",
                         [f"{w.get('name')}: {w.get('top_risk') or w.get('headline_reco') or w.get('context','')[:90]}" for w in ws[:6]]))
    slides.append(_slide(5, "Our recommendations, prioritised by impact", "numbered",
                         [r.get("text") for r in recs[:7]]))
    slides.append(_slide(6, "A 90-day plan turns recommendations into results", "table",
                         {"columns": ["Timeline", "Action", "Owner"],
                          "rows": [[a.get("timeline", "—"), a.get("step", ""), a.get("owner", "")] for a in plan[:8]]}))
    if econ:
        slides.append(_slide(7, "The economics: investment, fee options and value", "bullets",
                             [f"Effort: {econ.get('total_hours')} hrs over {econ.get('duration_weeks')} weeks",
                              f"Time & Materials: {econ.get('tm_fee_label')}  ·  Fixed: {econ.get('fixed_fee_label')}  ·  Retainer: {econ.get('monthly_retainer_label')}/mo",
                              f"Blended rate: {econ.get('blended_rate_label')}/hr  ·  AI leverage: {econ.get('ai_leverage_pct')}%"]))
    slides.append(_slide(8, "We will actively manage the key risks", "table",
                         {"columns": ["Risk", "Severity", "Control"],
                          "rows": [[r.get("risk", ""), r.get("severity", ""), r.get("control", "")] for r in risks[:7]]}))
    slides.append(_slide(9, "Success is measured on these KPIs", "bullets",
                         [f"{k.get('kpi')} → {k.get('target')}" for k in kpis[:8]]))
    slides.append(_slide(10, "Appendix — sources & methodology", "bullets",
                         [f"{c.get('title', c.get('key',''))}" for c in cites[:10]] + [report.get("disclaimer", "")]))

    return {"title": slides[0]["title"], "slide_count": len(slides), "slides": slides,
            "markdown": _to_markdown(title, sector, slides),
            "formats_available": ["markdown", "html-print"],
            "formats_pending": ["pptx (python-pptx at deploy)", "docx"]}


def _to_markdown(title, sector, slides):
    out = [f"# {title}", f"_{sector} · AI Consulting OS · confidential_", ""]
    for s in slides:
        out.append("---")
        out.append(f"## {s['n']}. {s['title']}")
        c = s["content"]
        if s["type"] in ("bullets", "numbered"):
            for i, b in enumerate([x for x in (c or []) if x]):
                out.append(f"{i+1}. {b}" if s["type"] == "numbered" else f"- {b}")
        elif s["type"] == "table":
            cols = c.get("columns", [])
            out.append("| " + " | ".join(cols) + " |")
            out.append("| " + " | ".join("---" for _ in cols) + " |")
            for row in c.get("rows", []):
                out.append("| " + " | ".join(str(x).replace("|", "/") for x in row) + " |")
        elif s["type"] == "cover":
            out.append(f"_{c.get('subtitle','')}_")
            if c.get("posture"):
                out.append(f"**Risk posture: {c['posture']}**")
        out.append("")
    return "\n".join(out)


def build_memo(report):
    """A one-page executive memo (markdown)."""
    if not report or report.get("error"):
        return {"error": "no engagement"}
    recs = report.get("recommendations") or []
    md = [f"# Executive memo — {report.get('title','Engagement')}", "",
          f"**Sector:** {report.get('sector','')}  ·  **Posture:** {(report.get('diagnosis') or {}).get('posture','')}", "",
          "## Bottom line", report.get("executive_summary", ""), "",
          "## What we recommend"]
    md += [f"{i+1}. {r.get('text')}" for i, r in enumerate(recs[:5])]
    md += ["", "## First 90 days"]
    md += [f"- [{a.get('timeline','—')}] {a.get('step','')} ({a.get('owner','')})" for a in (report.get("action_plan") or [])[:6]]
    md += ["", f"_{report.get('disclaimer','')}_"]
    return {"markdown": "\n".join(md)}


def generate(body):
    report = (body or {}).get("report") or {}
    kind = (body or {}).get("kind", "deck")
    if kind == "memo":
        return {"kind": "memo", **build_memo(report)}
    return {"kind": "deck", **build_deck(report)}


def meta():
    return {"kinds": ["deck", "memo"], "deck_slides": 10,
            "formats": ["markdown", "html-print"], "pending": ["pptx", "docx"],
            "endpoints": ["POST /deliverable", "GET /deliverable/meta", "GET /deliverable/tests"]}


def run_deliverable_tests():
    rep = {
        "title": "Test Co", "sector": "Retail Trade", "engagement_type": {"name": "Working Capital Optimization", "objective": "Release cash"},
        "diagnosis": {"posture": "Critical"}, "executive_summary": "Cash is trapped across the cycle.",
        "agents_engaged": [{"advisor": "AI CFO Advisor"}], "workstreams": [{"name": "CFO", "top_risk": "Runway < 3 months"}],
        "recommendations": [{"text": "Collect the oldest 20% of invoices"}],
        "action_plan": [{"timeline": "Week 1", "step": "AR ageing", "owner": "AR lead"}],
        "risks": [{"risk": "Cash runway", "severity": "Critical", "control": "13-week cashflow"}],
        "kpis": [{"kpi": "DSO", "target": "< 45 days"}], "citations": [{"title": "Sec 43B(h)"}],
        "delivery": {"economics": {"total_hours": 200, "duration_weeks": 8, "tm_fee_label": "₹12,00,000",
                                   "fixed_fee_label": "₹10,80,000", "monthly_retainer_label": "₹6,00,000",
                                   "blended_rate_label": "₹6,000", "ai_leverage_pct": 70}},
        "disclaimer": "AI-generated.",
    }
    cases = []
    d = build_deck(rep)
    cases.append(("deck", d["slide_count"] == 10 and "## 1." in d["markdown"] and "Working Capital" in d["title"]))
    cases.append(("deck_tables", "| Timeline | Action | Owner |" in d["markdown"] and "| Risk | Severity | Control |" in d["markdown"]))
    m = build_memo(rep)
    cases.append(("memo", "Executive memo" in m["markdown"] and "Collect the oldest" in m["markdown"]))
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases)},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    import json
    print(json.dumps(run_deliverable_tests(), indent=2))
