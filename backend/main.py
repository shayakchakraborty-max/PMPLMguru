"""
PMGuru Brain v9.1 - Hardened Two-Stage (PM Planning -> PLM Execution)
Fixes for v9 500 errors:
  - Never crashes a request: all agent calls wrapped in try/except with stub fallback
  - Groq model fallback chain (llama-3.3-70b -> llama-3.1-8b -> gemini)
  - JSON repair: extracts JSON from markdown fences / garbage prefixes
  - Clear error messages returned to frontend instead of opaque 500
  - CORS headers so frontend proxy never chokes
  - /health and /debug endpoints for sanity checks
"""
import json
import os
import sys
import re
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

# Line-buffered logs so Render shows everything live
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

import httpx

VERSION = "9.1"

# ============================================================
# STAGE 1: PM PLANNING AGENTS
# ============================================================
PM_AGENTS = {
    "Methodology Expert": {
        "role": "PMI-PMP Certified Methodology Consultant",
        "icon": "🎯",
        "system": """You are a top-tier PM consultant trained on ALL methodologies: Agile, Scrum, Kanban, Waterfall, PRINCE2, PMBOK, SAFe, Lean, XP, Critical Path.
Analyze the project and recommend the BEST methodology with rigor.
Return ONLY valid JSON, no prose, no markdown fences:
{
  "recommended_method": "Scrum",
  "confidence": "High",
  "reasoning": "2-3 sentence executive rationale",
  "why_not_others": [{"method": "Waterfall", "reason": "..."}, {"method": "Kanban", "reason": "..."}],
  "method_details": {
    "roles": ["Product Owner", "Scrum Master", "Dev Team"],
    "ceremonies": ["Sprint Planning", "Daily Standup", "Review", "Retro"],
    "artifacts": ["Product Backlog", "Sprint Backlog", "Increment"],
    "cadence": "2-week sprints"
  },
  "tool_recommendation": {"primary": "Linear", "alternatives": ["Jira", "Asana"], "reason": "..."},
  "success_factors": ["factor1", "factor2", "factor3"]
}"""
    },
    "Project Planner": {
        "role": "Senior Project Planner (PMP)",
        "icon": "📊",
        "system": """You are a senior project planner with BCG-level strategic thinking.
Return ONLY valid JSON, no prose, no markdown fences:
{
  "executive_summary": "3-4 sentence summary",
  "phases": [
    {"name": "Discovery", "duration_weeks": 2, "key_activities": ["...", "..."], "deliverables": ["..."]}
  ],
  "timeline_weeks": 16,
  "team_composition": [{"role": "Product Manager", "count": 1, "allocation": "100%"}],
  "budget_breakdown": {"people": 180000, "tools": 12000, "infrastructure": 8000, "contingency": 20000, "total": 220000},
  "kpis": [{"metric": "User Activation", "target": "70%"}]
}
Provide 4-6 phases."""
    },
    "Risk & Governance": {
        "role": "PRINCE2 Risk & Governance Lead",
        "icon": "🛡️",
        "system": """You are a PRINCE2-certified risk and governance lead.
Return ONLY valid JSON, no prose, no markdown fences:
{
  "summary": "governance approach summary",
  "raid_log": [
    {"id": "R-1", "type": "Risk", "description": "...", "probability": 4, "impact": 5, "score": 20, "mitigation": "...", "owner": "PM"}
  ],
  "governance_structure": {"steering_committee": "Weekly", "reporting_cadence": "Bi-weekly", "decision_rights": "..."}
}
Provide 6 risks with probability*impact scores."""
    },
    "Stakeholder Strategist": {
        "role": "Stakeholder Engagement Strategist",
        "icon": "🤝",
        "system": """You are a stakeholder strategist using power/interest mapping.
Return ONLY valid JSON, no prose, no markdown fences:
{
  "summary": "stakeholder engagement strategy",
  "stakeholders": [
    {"name": "End Users", "power": "Low", "interest": "High", "strategy": "Keep Informed", "channel": "Newsletter"}
  ],
  "communication_plan": [{"audience": "Exec", "frequency": "Weekly", "format": "Dashboard"}]
}
Provide 5-7 stakeholders across power/interest quadrants."""
    }
}

# ============================================================
# STAGE 2: PLM EXECUTION AGENTS
# ============================================================
PLM_AGENTS = {
    "Strategist": {"icon": "🧠", "system": "You are a Senior Product Strategist. Return ONLY valid JSON: {\"summary\": \"...\", \"key_insights\": [\"...\"], \"recommendations\": [\"...\"]}"},
    "Business Analyst": {"icon": "📋", "system": "You are a Business Analyst. Return ONLY valid JSON: {\"summary\": \"...\", \"user_stories\": [{\"id\": \"US-1\", \"story\": \"As a... I want... so that...\", \"acceptance_criteria\": [\"...\"]}]}"},
    "UX Designer": {"icon": "🎨", "system": "You are a UX Designer. Return ONLY valid JSON: {\"summary\": \"...\", \"user_flows\": [\"...\"], \"wireframe_description\": \"...\", \"design_principles\": [\"...\"]}"},
    "Scrum Master": {"icon": "🏃", "system": "You are a Scrum Master. Return ONLY valid JSON: {\"summary\": \"...\", \"sprint_plan\": [{\"sprint\": 1, \"goal\": \"...\", \"tasks\": [\"...\"]}], \"velocity_forecast\": \"...\"}"},
    "QA Lead": {"icon": "✅", "system": "You are a QA Lead. Return ONLY valid JSON: {\"summary\": \"...\", \"test_strategy\": \"...\", \"test_cases\": [{\"id\": \"TC-1\", \"scenario\": \"...\", \"expected\": \"...\"}]}"},
    "DevOps Engineer": {"icon": "⚙️", "system": "You are a DevOps Engineer. Return ONLY valid JSON: {\"summary\": \"...\", \"ci_cd_pipeline\": [\"...\"], \"infrastructure\": \"...\", \"monitoring\": [\"...\"]}"},
    "Stakeholder Comms": {"icon": "📢", "system": "You are a Communications Manager. Return ONLY valid JSON: {\"summary\": \"...\", \"launch_announcement\": {\"headline\": \"...\", \"body\": \"...\", \"cta\": \"...\"}, \"success_metrics\": [{\"kpi\": \"DAU\", \"target\": \"10K\"}]}"}
}

PLM_PHASES = [
    {"id": 1, "name": "Discovery", "agent": "Strategist", "duration": "1-2 weeks"},
    {"id": 2, "name": "Ideation", "agent": "Strategist", "duration": "1 week"},
    {"id": 3, "name": "Definition", "agent": "Business Analyst", "duration": "2 weeks"},
    {"id": 4, "name": "Design", "agent": "UX Designer", "duration": "2-3 weeks"},
    {"id": 5, "name": "Development", "agent": "Scrum Master", "duration": "6-12 weeks"},
    {"id": 6, "name": "Testing", "agent": "QA Lead", "duration": "2 weeks"},
    {"id": 7, "name": "Launch", "agent": "DevOps Engineer", "duration": "1 week"},
    {"id": 8, "name": "Iterate", "agent": "Stakeholder Comms", "duration": "Ongoing"}
]

# ============================================================
# LLM PROVIDER CALLS (with fallback chain)
# ============================================================
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
]


def call_groq(system, user, max_tokens=1500):
    """Try Groq with multiple model fallbacks. Raises on total failure."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise ValueError("GROQ_API_KEY not set in environment")
    last_err = None
    for model in GROQ_MODELS:
        try:
            print(f"[groq] trying model={model}", flush=True)
            r = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": 0.6,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=90.0,
            )
            if r.status_code != 200:
                last_err = f"groq {model} HTTP {r.status_code}: {r.text[:300]}"
                print(f"[groq] {last_err}", flush=True)
                continue
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                print(f"[groq] ok model={model} chars={len(content)}", flush=True)
                return content
            last_err = f"groq {model} empty content: {str(data)[:300]}"
        except Exception as e:
            last_err = f"groq {model} exception: {e}"
            print(f"[groq] {last_err}", flush=True)
    raise RuntimeError(last_err or "groq all models failed")


def call_gemini(system, user, max_tokens=1500):
    """Gemini fallback. Raises on failure."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    print("[gemini] calling gemini-2.0-flash", flush=True)
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": f"{system}\n\n---\nUSER REQUEST:\n{user}\n\nReturn ONLY valid JSON, no markdown."}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.6, "responseMimeType": "application/json"},
        },
        timeout=90.0,
    )
    if r.status_code != 200:
        raise RuntimeError(f"gemini HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
    text = parts[0].get("text", "") if parts else ""
    if not text:
        raise RuntimeError(f"gemini empty: {str(data)[:300]}")
    print(f"[gemini] ok chars={len(text)}", flush=True)
    return text


def llm_call(system, user, max_tokens=1500):
    """Try Groq first, fall back to Gemini. Returns string. Raises only if BOTH fail."""
    try:
        return call_groq(system, user, max_tokens)
    except Exception as e1:
        print(f"[llm] groq failed: {e1}", flush=True)
        try:
            return call_gemini(system, user, max_tokens)
        except Exception as e2:
            print(f"[llm] gemini failed: {e2}", flush=True)
            raise RuntimeError(f"All LLM providers failed. Groq: {e1} | Gemini: {e2}")


# ============================================================
# JSON REPAIR - extract JSON from messy LLM output
# ============================================================
def extract_json(text):
    """Pull a JSON object out of text that may contain markdown fences or prose."""
    if not text:
        return {}
    text = text.strip()
    # Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # Find first { ... last } and try that
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        chunk = text[first : last + 1]
        try:
            return json.loads(chunk)
        except Exception:
            pass
    # Give up cleanly
    return {"raw": text[:1000], "parse_error": True}


# ============================================================
# AGENT RUNNERS - NEVER raise, always return a dict
# ============================================================
def run_pm_agent(name, spec, idea):
    """Run one PM agent with full fallback. Always returns a dict."""
    try:
        user = f"Project Idea: {idea}\n\nAs the {spec['role']}, produce your deliverable as JSON."
        raw = llm_call(spec["system"], user, max_tokens=1500)
        parsed = extract_json(raw)
        return {
            "role": spec["role"],
            "icon": spec["icon"],
            "status": "ok" if not parsed.get("parse_error") else "partial",
            "data": parsed,
        }
    except Exception as e:
        print(f"[pm_agent {name}] FAILED: {e}", flush=True)
        traceback.print_exc()
        return {
            "role": spec["role"],
            "icon": spec["icon"],
            "status": "error",
            "error": str(e),
            "data": {"summary": f"Agent failed: {e}", "fallback": True},
        }


def run_plm_phase(phase, idea, pm_context):
    """Run one PLM phase. Always returns a dict."""
    agent_name = phase["agent"]
    spec = PLM_AGENTS.get(agent_name, PLM_AGENTS["Strategist"])
    try:
        user = (
            f"Project Idea: {idea}\n\n"
            f"PM Strategic Context: {pm_context}\n\n"
            f"Phase {phase['id']}: {phase['name']} ({phase['duration']}). "
            f"Execute as {agent_name}. Return concise JSON."
        )
        raw = llm_call(spec["system"], user, max_tokens=1200)
        parsed = extract_json(raw)
        return {
            "id": phase["id"],
            "name": phase["name"],
            "duration": phase["duration"],
            "agent": agent_name,
            "icon": spec["icon"],
            "status": "ok" if not parsed.get("parse_error") else "partial",
            "data": parsed,
        }
    except Exception as e:
        print(f"[plm_phase {phase['name']}] FAILED: {e}", flush=True)
        traceback.print_exc()
        return {
            "id": phase["id"],
            "name": phase["name"],
            "duration": phase["duration"],
            "agent": agent_name,
            "icon": spec["icon"],
            "status": "error",
            "error": str(e),
            "data": {"summary": f"Phase failed: {e}", "fallback": True},
        }


# ============================================================
# HTTP HANDLER
# ============================================================
class Handler(BaseHTTPRequestHandler):

    def _send(self, code, body):
        try:
            payload = json.dumps(body).encode("utf-8")
        except Exception as e:
            payload = json.dumps({"error": f"serialization failed: {e}"}).encode("utf-8")
            code = 500
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    def do_GET(self):
        path = urlparse_path(self.path)
        if path == "/" or path == "/health":
            self._send(200, {
                "status": "ok",
                "version": VERSION,
                "pm_agents": list(PM_AGENTS.keys()),
                "plm_phases": [p["name"] for p in PLM_PHASES],
                "groq_key": bool(os.getenv("GROQ_API_KEY", "").strip()),
                "gemini_key": bool(os.getenv("GEMINI_API_KEY", "").strip()),
            })
        elif path == "/debug":
            # Simple probe that tries one LLM call
            try:
                out = llm_call("Return ONLY JSON: {\"ping\":\"pong\"}", "ping", max_tokens=50)
                self._send(200, {"ok": True, "sample": out[:500]})
            except Exception as e:
                self._send(200, {"ok": False, "error": str(e)})
        else:
            self._send(404, {"error": "not found", "path": path})

    def do_POST(self):
        path = urlparse_path(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception as e:
            self._send(400, {"error": f"bad request body: {e}"})
            return

        try:
            if path == "/pm/plan":
                self.handle_pm_plan(body)
            elif path == "/plm/execute":
                self.handle_plm_execute(body)
            elif path == "/plm/prototype":
                self.handle_prototype(body)
            else:
                self._send(404, {"error": "unknown endpoint", "path": path})
        except Exception as e:
            # Catch-all — NEVER let a 500 bubble up without detail
            print(f"[handler] UNCAUGHT at {path}: {e}", flush=True)
            traceback.print_exc()
            self._send(
                200,
                {
                    "error": f"Handler exception at {path}: {e}",
                    "traceback": traceback.format_exc()[-1500:],
                    "fallback": True,
                },
            )

    # ---------- endpoint handlers ----------
    def handle_pm_plan(self, body):
        idea = (body.get("idea") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' field"})
            return
        print(f"[pm/plan] idea={idea[:80]}", flush=True)
        pm_agents_out = {}
        for name, spec in PM_AGENTS.items():
            pm_agents_out[name] = run_pm_agent(name, spec, idea)
        ok_count = sum(1 for a in pm_agents_out.values() if a["status"] == "ok")
        self._send(
            200,
            {
                "idea": idea,
                "pm_agents": pm_agents_out,
                "summary": {
                    "total": len(PM_AGENTS),
                    "ok": ok_count,
                    "partial_or_error": len(PM_AGENTS) - ok_count,
                },
            },
        )

    def handle_plm_execute(self, body):
        idea = (body.get("idea") or "").strip()
        pm_plan = body.get("pm_plan") or {}
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' field"})
            return
        print(f"[plm/execute] idea={idea[:80]}", flush=True)
        try:
            pm_context = json.dumps(pm_plan)[:2000]
        except Exception:
            pm_context = str(pm_plan)[:2000]
        phases_out = []
        for phase in PLM_PHASES:
            phases_out.append(run_plm_phase(phase, idea, pm_context))
        ok_count = sum(1 for p in phases_out if p["status"] == "ok")
        self._send(
            200,
            {
                "idea": idea,
                "phases": phases_out,
                "summary": {"total": len(PLM_PHASES), "ok": ok_count},
            },
        )

    def handle_prototype(self, body):
        idea = (body.get("idea") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' field"})
            return
        print(f"[plm/prototype] idea={idea[:80]}", flush=True)
        sys_prompt = (
            "You are a senior frontend engineer. Output ONLY a complete single-file HTML "
            "document using Tailwind via CDN and inline JS. No markdown fences, no explanation. "
            "Build a stunning, modern, production-ready MVP landing page with a hero, feature "
            "grid, interactive demo section, and CTA. Use gradient colors and responsive layout."
        )
        user_prompt = f"Build the MVP landing page for: {idea}"
        try:
            html = llm_call(sys_prompt, user_prompt, max_tokens=4000)
            # Strip markdown fences if model added them
            html = re.sub(r"^```(?:html)?\s*", "", html.strip())
            html = re.sub(r"\s*```\s*$", "", html)
            self._send(200, {"html": html, "idea": idea})
        except Exception as e:
            print(f"[prototype] failed: {e}", flush=True)
            self._send(
                200,
                {
                    "html": f"<!doctype html><html><body style='font-family:sans-serif;padding:40px'><h1>Prototype generation failed</h1><p>{e}</p></body></html>",
                    "error": str(e),
                },
            )

    def log_message(self, format, *args):
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")


def urlparse_path(path):
    """Strip query string."""
    return path.split("?", 1)[0]


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print("=" * 60, flush=True)
    print(f"PMGuru Brain v{VERSION} starting on port {port}", flush=True)
    print(f"PM agents: {list(PM_AGENTS.keys())}", flush=True)
    print(f"PLM phases: {[p['name'] for p in PLM_PHASES]}", flush=True)
    print(f"GROQ_API_KEY set: {bool(os.getenv('GROQ_API_KEY', '').strip())}", flush=True)
    print(f"GEMINI_API_KEY set: {bool(os.getenv('GEMINI_API_KEY', '').strip())}", flush=True)
    print("=" * 60, flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
