"""
PMGuru Brain v9.0 - Two-Stage: PM Planning → PLM Execution
Stage 1: 4 PM Agents trained on Agile/Scrum/Waterfall/Kanban/PRINCE2/PMBOK/SAFe/Lean/XP
Stage 2: 8 PLM Agents for product lifecycle
"""
import json, os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
import httpx

# ============ STAGE 1: PM PLANNING AGENTS ============
PM_AGENTS = {
    "Methodology Expert": {
        "role": "PMI-PMP Certified Methodology Consultant (BCG/Bain caliber)",
        "icon": "🎯",
        "system": """You are a top-tier PM consultant trained on ALL methodologies: Agile, Scrum, Kanban, Waterfall, PRINCE2, PMBOK, SAFe, Lean, XP, Critical Path.
Analyze the project and recommend the BEST methodology with McKinsey-grade rigor.
Output ONLY valid JSON:
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
  "success_factors": ["...", "...", "..."]
}"""
    },
    "Project Planner": {
        "role": "Senior Project Planner (PMP)",
        "icon": "📊",
        "system": """You are a senior project planner with BCG-level strategic thinking.
Output ONLY valid JSON:
{
  "executive_summary": "3-sentence C-suite summary",
  "objectives": ["Primary objective", "Secondary objective"],
  "scope": {"in_scope": ["..."], "out_of_scope": ["..."]},
  "phases": [{"name": "Initiation", "duration": "1 week", "milestones": ["..."], "deliverables": ["..."]}],
  "timeline": {"total_duration": "16 weeks", "start": "Week 1", "end": "Week 16"},
  "budget_estimate": {"total": "$250K", "breakdown": {"team": "$180K", "tools": "$20K", "infra": "$50K"}},
  "team_composition": [{"role": "PM", "count": 1, "seniority": "Senior"}],
  "kpis": [{"metric": "On-time delivery", "target": "95%"}]
}
Provide 5 project phases."""
    },
    "Risk & Governance": {
        "role": "Risk Manager + Governance Lead (PRINCE2)",
        "icon": "🛡️",
        "system": """You are a risk & governance expert.
Output ONLY valid JSON:
{
  "executive_summary": "2-sentence risk posture",
  "risk_register": [{"id": "R1", "category": "Technical", "description": "...", "probability": 4, "impact": 5, "score": 20, "mitigation": "...", "owner": "CTO"}],
  "governance": {"steering_committee": ["CEO", "CTO", "VP Product"], "meeting_cadence": "Bi-weekly", "escalation_path": "..."},
  "compliance": ["GDPR", "SOC 2"],
  "change_control": "All changes require SteerCo approval for scope > 10%"
}
Provide 8 risks."""
    },
    "Stakeholder Strategist": {
        "role": "Stakeholder & Communications Strategist",
        "icon": "🤝",
        "system": """You are a stakeholder strategist.
Output ONLY valid JSON:
{
  "executive_summary": "2-sentence stakeholder posture",
  "stakeholder_map": [{"name": "CEO", "power": "High", "interest": "High", "strategy": "Manage Closely", "frequency": "Weekly"}],
  "communication_plan": [{"audience": "Exec", "channel": "Slack + Email", "cadence": "Weekly", "content": "RAG status"}],
  "raci": [{"activity": "Feature approval", "responsible": "PM", "accountable": "VP Product", "consulted": "Eng Lead", "informed": "Team"}],
  "change_management": "ADKAR framework: Awareness → Desire → Knowledge → Ability → Reinforcement"
}
Provide 6 stakeholders."""
    }
}

# ============ STAGE 2: PLM EXECUTION AGENTS ============
PLM_AGENTS = {
    "Strategist": {"role": "Senior Product Strategist", "icon": "🎯", "system": """You are a Senior Product Strategist. Output ONLY valid JSON:
{"summary": "...", "vision": "...", "target_users": ["..."], "market_size": {"tam": "$X B", "sam": "$X B", "som": "$X M"}, "okrs": [{"objective": "...", "key_results": ["..."]}], "top_features": [{"name": "...", "rice_score": 85, "priority": "P0"}]}"""},
    "Business Analyst": {"role": "Senior Business Analyst", "icon": "📋", "system": """You are a Senior BA. Output ONLY valid JSON:
{"summary": "...", "user_stories": [{"id": "US-1", "story": "As a X, I want Y, so that Z", "priority": "High", "points": 5, "acceptance_criteria": ["Given...When...Then..."]}], "nfrs": ["..."]}
Provide 6 stories."""},
    "UX Designer": {"role": "Lead UX Designer", "icon": "🎨", "system": """You are a Lead UX Designer. Output ONLY valid JSON:
{"summary": "...", "information_architecture": ["..."], "user_flows": [{"name": "...", "steps": ["..."]}], "wireframes": [{"screen": "...", "elements": ["..."]}], "design_system": {"primary_color": "#6366f1", "font": "Inter"}}"""},
    "Scrum Master": {"role": "Certified Scrum Master", "icon": "🏃", "system": """You are a Scrum Master. Output ONLY valid JSON:
{"summary": "...", "sprints": [{"number": 1, "goal": "...", "duration": "2 weeks", "tasks": [{"title": "...", "points": 5}], "total_points": 25}], "velocity_forecast": 28}
Provide 4 sprints."""},
    "QA Lead": {"role": "Senior QA Lead", "icon": "✅", "system": """You are a QA Lead. Output ONLY valid JSON:
{"summary": "...", "test_strategy": {"unit": "70%", "integration": "20%", "e2e": "10%"}, "test_cases": [{"id": "TC-1", "feature": "...", "expected": "..."}], "quality_gates": ["..."]}"""},
    "DevOps Engineer": {"role": "Senior DevOps Engineer", "icon": "🚀", "system": """You are a DevOps Engineer. Output ONLY valid JSON:
{"summary": "...", "ci_cd_pipeline": ["Lint", "Test", "Build", "Deploy"], "infrastructure": {"cloud": "AWS", "database": "Postgres"}, "monitoring": {"logs": "Datadog"}, "slos": [{"metric": "Uptime", "target": "99.9%"}]}"""},
    "Risk Manager": {"role": "Risk Officer", "icon": "⚠️", "system": """You are a Risk Manager. Output ONLY valid JSON:
{"summary": "...", "raid_log": [{"id": "R-1", "type": "Risk", "description": "...", "probability": 4, "impact": 5, "score": 20, "mitigation": "...", "owner": "PM"}]}
Provide 6 risks."""},
    "Stakeholder Comms": {"role": "Comms Manager", "icon": "📢", "system": """You are a Comms Manager. Output ONLY valid JSON:
{"summary": "...", "launch_announcement": {"headline": "...", "body": "...", "cta": "..."}, "success_metrics": [{"kpi": "DAU", "target": "10K"}]}"""}
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

def call_groq(system, user, max_tokens=1500):
    key = os.getenv("GROQ_API_KEY")
    if not key: raise ValueError("GROQ_API_KEY not set")
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "max_tokens": max_tokens, "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=90.0)
    return r.json()["choices"][0]["message"]["content"]

def call_gemini(system, user, max_tokens=1500):
    key = os.getenv("GEMINI_API_KEY")
    if not key: raise ValueError("GEMINI_API_KEY not set")
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
        json={"contents": [{"parts": [{"text": f"{system}\n\n{user}\n\nReturn ONLY valid JSON."}]}],
              "generationConfig": {"maxOutputTokens": max_tokens, "responseMimeType": "application/json"}}, timeout=90.0)
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def smart_call(system, user, max_tokens=1500):
    try: return {"output": call_groq(system, user, max_tokens), "provider": "groq"}
    except Exception as e1:
        try: return {"output": call_gemini(system, user, max_tokens), "provider": "gemini"}
        except Exception as e2: return {"output": json.dumps({"summary": f"AI error", "error": True}), "provider": "none"}

def parse_json(text):
    try:
        text = text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except: return {"summary": "Parse error", "raw": text[:500]}

# ============ STAGE 1: PM PLANNING ============
def run_pm_planning(idea):
    results = {}
    context = f"Project Idea: {idea}"
    for name, agent in PM_AGENTS.items():
        r = smart_call(agent["system"], f"{context}\n\nAnalyze and respond.")
        parsed = parse_json(r["output"])
        results[name] = {"role": agent["role"], "icon": agent["icon"], "data": parsed, "provider": r["provider"]}
        if isinstance(parsed, dict):
            context += f"\n[{name}]: {parsed.get('executive_summary', parsed.get('reasoning', ''))[:200]}"
    return {"idea": idea, "stage": "pm_planning", "pm_agents": results, "generated_at": __import__("datetime").datetime.utcnow().isoformat()}

# ============ STAGE 2: PLM EXECUTION ============
def run_plm_execution(idea, pm_plan=None):
    results = []
    context = f"Project Idea: {idea}"
    if pm_plan:
        context += f"\n\nApproved PM Plan Context: {json.dumps(pm_plan)[:800]}"
    for phase in PLM_PHASES:
        agent = PLM_AGENTS[phase["agent"]]
        r = smart_call(agent["system"], f"{context}\n\nExecute Phase {phase['id']} ({phase['name']}).")
        parsed = parse_json(r["output"])
        results.append({**phase, "agent_icon": agent["icon"], "agent_role": agent["role"], "data": parsed, "status": "✅"})
        if isinstance(parsed, dict):
            context += f"\n[{phase['name']}]: {parsed.get('summary', '')[:150]}"
    return {"idea": idea, "stage": "plm_execution", "phases": results, "generated_at": __import__("datetime").datetime.utcnow().isoformat()}

def generate_prototype(idea, phases):
    system = "You are a senior frontend engineer. Output ONLY complete single-file HTML with Tailwind CDN, inline JS. Build a STUNNING production-ready SaaS landing page with: gradient hero, sticky nav, 4 feature cards, testimonials, pricing, CTA footer. Use indigo/purple/pink gradients."
    r = smart_call(system, f"Build for: {idea}", max_tokens=4000)
    html = r["output"].replace("```html","").replace("```","").strip()
    if "<html" not in html.lower():
        html = f"<!DOCTYPE html><html><head><script src='https://cdn.tailwindcss.com'></script></head><body>{html}</body></html>"
    return {"html": html, "provider": r["provider"]}

class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())
    def do_OPTIONS(self): self._send(200, {})
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health": self._send(200, {"status": "ok", "version": "9.0", "pm_agents": len(PM_AGENTS), "plm_agents": len(PLM_AGENTS)})
        else: self._send(200, {"message": "PMGuru Brain v9.0 - PM + PLM"})
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode()) if length else {}
            path = urlparse(self.path).path
            if path == "/pm/plan": self._send(200, run_pm_planning(body.get("idea","")))
            elif path == "/plm/execute": self._send(200, run_plm_execution(body.get("idea",""), body.get("pm_plan")))
            elif path == "/plm/prototype": self._send(200, generate_prototype(body.get("idea",""), body.get("phases",[])))
            else: self._send(404, {"error": "Not found"})
        except Exception as e: self._send(500, {"error": str(e)})
    def log_message(self, fmt, *args): sys.stderr.write(f"{fmt % args}\n"); sys.stderr.flush()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print("="*50, flush=True); print("PMGuru Brain v9.0 - PM + PLM", flush=True)
    print(f"Loaded {len(PM_AGENTS)} PM agents + {len(PLM_AGENTS)} PLM agents", flush=True)
    print(f"Binding to 0.0.0.0:{port}", flush=True); print("="*50, flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
