"""
PMGuru Brain v12.1 - Diagnostic Edition
Same as v12 but with LOUD error logging so we can see exactly what's failing.
Also validates API keys on startup.
"""
import json, os, sys, datetime, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
import httpx

VERSION = "12.1-diag"

# ============ STARTUP API KEY VALIDATION ============
def validate_api_keys_on_startup():
    """Check keys before accepting requests so we fail loudly on boot."""
    print("="*60, flush=True)
    print("CHECKING API KEYS ON STARTUP", flush=True)
    print("="*60, flush=True)
    
    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    # Check presence
    if not groq_key:
        print("❌ GROQ_API_KEY is MISSING from environment", flush=True)
    else:
        print(f"✓ GROQ_API_KEY present: {groq_key[:10]}... (length: {len(groq_key)})", flush=True)
        if not groq_key.startswith("gsk_"):
            print(f"⚠️  GROQ_API_KEY doesn't start with 'gsk_' - might be wrong format", flush=True)
    
    if not gemini_key:
        print("❌ GEMINI_API_KEY is MISSING from environment", flush=True)
    else:
        print(f"✓ GEMINI_API_KEY present: {gemini_key[:10]}... (length: {len(gemini_key)})", flush=True)
        if not gemini_key.startswith("AIza"):
            print(f"⚠️  GEMINI_API_KEY doesn't start with 'AIza' - might be wrong format", flush=True)
    
    # Test Groq with a tiny call
    if groq_key:
        try:
            print("Testing Groq with tiny request...", flush=True)
            r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "max_tokens": 10,
                      "messages": [{"role": "user", "content": "Say OK"}]}, timeout=15.0)
            if r.status_code == 200:
                print(f"✅ GROQ WORKS - test response: {r.json()['choices'][0]['message']['content'][:50]}", flush=True)
            else:
                print(f"❌ GROQ FAILED with status {r.status_code}: {r.text[:200]}", flush=True)
        except Exception as e:
            print(f"❌ GROQ EXCEPTION: {type(e).__name__}: {str(e)[:200]}", flush=True)
    
    # Test Gemini with a tiny call
    if gemini_key:
        try:
            print("Testing Gemini with tiny request...", flush=True)
            r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": "Say OK"}]}],
                      "generationConfig": {"maxOutputTokens": 10}}, timeout=15.0)
            if r.status_code == 200:
                text = r.json().get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")
                print(f"✅ GEMINI WORKS - test response: {text[:50]}", flush=True)
            else:
                print(f"❌ GEMINI FAILED with status {r.status_code}: {r.text[:200]}", flush=True)
        except Exception as e:
            print(f"❌ GEMINI EXCEPTION: {type(e).__name__}: {str(e)[:200]}", flush=True)
    
    print("="*60, flush=True)
    print("API KEY CHECK COMPLETE - starting server", flush=True)
    print("="*60, flush=True)

# ============ AGENT DEFINITIONS (shorter to avoid token limits) ============
METHODOLOGY_EXPERT = {
    "icon": "🎯", "role": "PMI-PMP Methodology Consultant",
    "system": """You are a senior PM consultant. Analyze the project and recommend a PM methodology.
Output ONLY valid JSON:
{
  "recommended_method": "Scrum",
  "confidence": "High",
  "reasoning": "2-3 sentence detailed rationale specific to this project",
  "layman_explanation": "3-4 sentence plain-English explanation",
  "fit_analysis": {"team_size_fit": "Why this works", "uncertainty_fit": "Why", "timeline_fit": "Why", "customer_feedback_fit": "Why"},
  "why_not_others": [{"method": "Waterfall", "simple_reason": "Plain English"}, {"method": "Kanban", "simple_reason": "Plain English"}, {"method": "PRINCE2", "simple_reason": "Plain English"}],
  "method_details": {"roles": ["Role 1", "Role 2", "Role 3"], "ceremonies": ["Ceremony 1", "Ceremony 2", "Ceremony 3"], "artifacts": ["Artifact 1", "Artifact 2"], "cadence": "2-week sprints"},
  "tool_recommendation": {"primary": "Linear", "alternatives": ["Jira", "Asana"], "reason": "Why"},
  "success_factors": ["Factor 1", "Factor 2", "Factor 3"]
}"""
}

PROJECT_PLANNER = {
    "icon": "📊", "role": "Senior Project Planner",
    "system": """You are a senior project planner. Create a detailed plan specific to the project.
Output ONLY valid JSON:
{
  "executive_summary": "2-paragraph summary",
  "layman_summary": "3-sentence plain English",
  "business_context": "1-paragraph context",
  "objectives": {"primary": "Main objective", "secondary": ["Obj 1", "Obj 2", "Obj 3"]},
  "scope": {"in_scope": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"], "out_of_scope": ["Item 1", "Item 2"], "assumptions": ["A 1", "A 2"], "constraints": ["C 1", "C 2"]},
  "phases": [{"name": "Phase", "duration": "2 weeks", "what_happens": "Description", "key_deliverables": ["D 1", "D 2"], "exit_criteria": "Criteria"}],
  "timeline": {"total_duration": "16 weeks", "start": "Week 1", "end": "Week 16", "critical_path": "Path"},
  "budget_estimate": {"total": "$250K", "breakdown": {"team": "$180K", "tools": "$20K", "infra": "$30K", "contingency": "$20K"}, "rationale": "Basis"},
  "team_composition": [{"role": "Role", "count": 1, "seniority": "Senior", "responsibilities": "What", "when_needed": "Phases"}],
  "kpis": [{"metric": "Metric", "target": "Target", "why_it_matters": "Reason"}],
  "dependencies": ["Dep 1", "Dep 2"]
}
Provide 5 phases and 5 team roles."""
}

RISK_MANAGER_PM = {
    "icon": "🛡️", "role": "Risk Manager (PRINCE2)",
    "system": """You are a risk expert. Generate 10 specific risks for this project.
Output ONLY valid JSON:
{
  "executive_summary": "1-paragraph risk posture",
  "layman_summary": "3-sentence plain English",
  "risk_register": [
    {"id": "R1", "category": "Technical", "description": "Description", "simple_description": "Plain English", "probability": 4, "impact": 5, "score": 20, "mitigation": "Strategy", "simple_mitigation": "Plain English", "contingency": "Backup plan", "owner": "Owner"}
  ]
}
Provide exactly 10 risks."""
}

PLM_AGENTS = {
    "Initiation": {
        "id": 1, "icon": "🚀", "role": "Project Initiation Expert", "duration": "1-2 weeks",
        "system": """You are an initiation specialist. Output ONLY valid JSON:
{"summary": "1-paragraph", "layman_summary": "3 sentences", "project_charter": {"purpose": "Why", "vision_statement": "Vision", "success_criteria": ["C 1", "C 2", "C 3", "C 4"], "high_level_scope": "Scope"}, "stakeholder_identification": [{"stakeholder": "Role", "interest": "What", "influence": "High", "engagement_strategy": "How"}], "kickoff_agenda": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"], "initiation_deliverables": ["D 1", "D 2", "D 3", "D 4"], "exit_criteria": "Criteria"}
Provide 5 stakeholders."""
    },
    "Requirements": {
        "id": 2, "icon": "📋", "role": "Requirements Analyst", "duration": "2-3 weeks",
        "system": """You are a senior BA. Output ONLY valid JSON:
{"summary": "1 paragraph", "layman_summary": "3 sentences", "functional_requirements": [{"id": "FR-1", "requirement": "The system shall...", "priority": "Must", "rationale": "Why"}], "non_functional_requirements": [{"id": "NFR-1", "category": "Performance", "requirement": "Requirement", "target": "Target"}], "user_personas": [{"name": "Persona", "description": "Desc", "goals": ["G 1"], "pain_points": ["P 1"]}], "user_stories": [{"id": "US-1", "story": "As a X, I want Y, so that Z", "priority": "High", "points": 5}], "business_rules": ["R 1", "R 2"], "integration_requirements": ["I 1", "I 2"]}
Provide 6 functional, 4 NFRs, 3 personas, 6 stories."""
    },
    "Design_Development": {
        "id": 3, "icon": "🏗️", "role": "Solutions Architect", "duration": "6-10 weeks",
        "system": """You are an architect. Output ONLY valid JSON:
{"summary": "1 paragraph", "layman_summary": "3 sentences", "architecture": {"style": "Type", "rationale": "Why", "components": [{"name": "Name", "responsibility": "What", "tech": "Tech"}]}, "tech_stack": {"frontend": {"framework": "Next.js", "reason": "Why"}, "backend": {"language": "Python", "framework": "FastAPI", "reason": "Why"}, "database": {"primary": "Postgres", "reason": "Why"}, "third_party": ["S 1", "S 2"]}, "sprints": [{"number": 1, "goal": "Goal", "total_points": 25}], "estimated_velocity": 25}
Provide 5 components, 5 sprints."""
    },
    "Testing_QA": {
        "id": 4, "icon": "✅", "role": "Senior QA Lead", "duration": "2-3 weeks",
        "system": """You are a QA lead. Output ONLY valid JSON:
{"summary": "1 paragraph", "layman_summary": "3 sentences", "test_strategy": {"unit": "70%", "integration": "20%", "e2e": "10%"}, "test_cases": [{"id": "TC-1", "feature": "Feature", "steps": ["Step 1", "Step 2"], "expected_result": "Expected", "priority": "P0"}], "quality_gates": [{"gate": "Gate", "criteria": "Criteria"}], "test_environments": ["Dev", "Staging", "Prod"]}
Provide 6 test cases, 4 quality gates."""
    },
    "Deployment": {
        "id": 5, "icon": "🚢", "role": "DevOps Engineer", "duration": "1-2 weeks",
        "system": """You are a DevOps engineer. Output ONLY valid JSON:
{"summary": "1 paragraph", "layman_summary": "3 sentences", "deployment_strategy": "Strategy", "infrastructure": {"cloud_provider": "Provider", "services": [{"service": "Name", "purpose": "Purpose"}], "total_monthly_cost": "$X"}, "ci_cd_pipeline": {"platform": "GitHub Actions", "stages": [{"stage": "Stage", "what_happens": "What"}]}, "go_live_checklist": ["Item 1", "Item 2", "Item 3", "Item 4"], "rollback_strategy": "Strategy"}
Provide 5 CI/CD stages, 6 checklist items."""
    },
    "Monitoring": {
        "id": 6, "icon": "📡", "role": "SRE", "duration": "Ongoing",
        "system": """You are an SRE. Output ONLY valid JSON:
{"summary": "1 paragraph", "layman_summary": "3 sentences", "observability_stack": {"logging": {"tool": "Tool", "retention": "30 days"}, "metrics": {"tool": "Tool", "key_metrics": ["M 1", "M 2"]}, "alerting": {"tool": "Tool"}}, "slos": [{"metric": "Metric", "target": "Target", "why_it_matters": "Why"}], "key_dashboards": [{"name": "Name", "purpose": "Purpose"}], "alert_rules": [{"alert": "Alert", "condition": "When", "severity": "P0"}]}
Provide 4 SLOs, 3 dashboards, 5 alerts."""
    }
}

PM_TOOL_ARCHITECT = {
    "icon": "🛠️", "role": "PM Tool Engineer",
    "system": """You are a PM tool engineer. Design a custom Kanban board. Output ONLY valid JSON:
{"board_title": "Project Board", "methodology": "Scrum", "columns": [{"id": "backlog", "name": "Backlog", "color": "#64748b"}, {"id": "sprint", "name": "Sprint", "color": "#6366f1"}, {"id": "progress", "name": "In Progress", "color": "#f59e0b"}, {"id": "review", "name": "Review", "color": "#8b5cf6"}, {"id": "done", "name": "Done", "color": "#10b981"}], "sprints": [{"number": 1, "name": "Sprint 1", "goal": "Goal"}], "team_members": [{"id": "alice", "name": "Alice", "role": "PM", "color": "#6366f1", "initials": "AL"}], "cards": [{"id": "T-1", "title": "Task", "description": "Desc", "column": "backlog", "sprint": 1, "assignee": "alice", "priority": "P0", "story_points": 3, "tags": ["tag"]}], "velocity_target": 25}
Create 12 cards and 4 team members."""
}

# ============ AI CALLS WITH LOUD LOGGING ============
def call_groq(system, user, max_tokens=2000):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY env var not set")
    try:
        r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "max_tokens": max_tokens, "response_format": {"type": "json_object"},
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=90.0)
        if r.status_code != 200:
            err = f"Groq returned {r.status_code}: {r.text[:300]}"
            print(f"  ❌ {err}", flush=True)
            raise RuntimeError(err)
        return r.json()["choices"][0]["message"]["content"]
    except httpx.TimeoutException as e:
        print(f"  ❌ Groq timeout: {str(e)[:200]}", flush=True)
        raise
    except Exception as e:
        print(f"  ❌ Groq error: {type(e).__name__}: {str(e)[:200]}", flush=True)
        raise

def call_gemini(system, user, max_tokens=2000):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY env var not set")
    try:
        r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            json={"contents": [{"parts": [{"text": f"{system}\n\n{user}\n\nReturn ONLY valid JSON."}]}],
                  "generationConfig": {"maxOutputTokens": max_tokens, "responseMimeType": "application/json"}}, timeout=90.0)
        if r.status_code != 200:
            err = f"Gemini returned {r.status_code}: {r.text[:300]}"
            print(f"  ❌ {err}", flush=True)
            raise RuntimeError(err)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"  ❌ Gemini error: {type(e).__name__}: {str(e)[:200]}", flush=True)
        raise

def smart_call(system, user, max_tokens=2000):
    try:
        output = call_groq(system, user, max_tokens)
        return {"output": output, "provider": "groq", "error": None}
    except Exception as e1:
        print(f"  ⚠️ Groq failed, trying Gemini...", flush=True)
        try:
            output = call_gemini(system, user, max_tokens)
            return {"output": output, "provider": "gemini", "error": None}
        except Exception as e2:
            err = f"Both providers failed - Groq: {str(e1)[:150]} | Gemini: {str(e2)[:150]}"
            print(f"  🔴 {err}", flush=True)
            return {"output": json.dumps({"summary": "AI providers unreachable", "error": True, "details": err[:300], "layman_summary": "The AI service could not be reached. Check API keys in Render settings."}), "provider": "none", "error": err}

def parse_json_safe(text):
    if not text: return {"summary": "Empty response", "error": True}
    try:
        text = text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result if isinstance(result, dict) else {"summary": "Invalid format", "error": True}
    except Exception as e:
        return {"summary": f"Parse error: {str(e)[:100]}", "error": True, "raw": text[:500]}

def run_agent(agent_def, user_input, max_tokens=2000):
    try:
        r = smart_call(agent_def["system"], user_input, max_tokens)
        data = parse_json_safe(r["output"])
        return {"role": agent_def["role"], "icon": agent_def["icon"], "data": data, "provider": r["provider"], "error": r["error"]}
    except Exception as e:
        print(f"  🔴 Agent crashed: {str(e)[:200]}", flush=True)
        return {"role": agent_def.get("role", "Agent"), "icon": agent_def.get("icon", "🤖"),
                "data": {"summary": f"Agent crashed: {str(e)[:100]}", "error": True},
                "provider": "none", "error": str(e)[:200]}

# ============ PM TOOL HTML (same as v12) ============
def render_pm_tool_html(board_data):
    board = board_data if isinstance(board_data, dict) and not board_data.get("error") else {
        "board_title": "Fallback Board", "methodology": "Scrum",
        "columns": [{"id": "backlog", "name": "Backlog", "color": "#64748b"}, {"id": "done", "name": "Done", "color": "#10b981"}],
        "sprints": [{"number": 1, "name": "Sprint 1", "goal": "Goal"}],
        "team_members": [{"id": "team", "name": "Team", "role": "All", "color": "#6366f1", "initials": "TM"}],
        "cards": [{"id": "T-1", "title": "Setup", "description": "Setup", "column": "backlog", "sprint": 1, "assignee": "team", "priority": "P0", "story_points": 3, "tags": ["setup"]}],
        "velocity_target": 25
    }
    board_json = json.dumps(board)
    title = board.get("board_title", "PM Board")
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>""" + title + """</title><script src="https://cdn.tailwindcss.com"></script>
<style>body{font-family:sans-serif}.card{cursor:grab}.card.dragging{opacity:0.4}.priority-P0{border-left:3px solid #ef4444}.priority-P1{border-left:3px solid #f59e0b}.priority-P2{border-left:3px solid #10b981}</style>
</head><body class="bg-gradient-to-br from-slate-900 to-indigo-950 min-h-screen text-slate-100 p-6">
<h1 class="text-2xl font-black mb-4" id="bt"></h1>
<div id="bd" class="flex gap-4 overflow-x-auto"></div>
<script>
const BD=""" + board_json + """;
document.getElementById('bt').textContent=BD.board_title||'Board';
document.getElementById('bd').innerHTML=(BD.columns||[]).map(col=>{const cs=(BD.cards||[]).filter(c=>c.column===col.id);return `<div class="flex-shrink-0 w-72 bg-slate-800/40 rounded-xl p-4"><h3 class="font-bold mb-3" style="color:${col.color}">${col.name}</h3><div class="space-y-2">${cs.map(c=>`<div class="card priority-${c.priority||'P2'} p-3 bg-slate-800 rounded-lg"><div class="text-xs text-slate-400">${c.id}</div><div class="font-semibold mt-1">${c.title}</div><div class="text-xs mt-2 opacity-70">${c.story_points||0} pts</div></div>`).join('')}</div></div>`}).join('');
</script></body></html>"""

# ============ AUTOPILOT ============
def run_autopilot(idea):
    print(f"\n{'='*60}\nAUTOPILOT START: {idea[:60]}\n{'='*60}", flush=True)
    started = datetime.datetime.now(datetime.UTC).isoformat()
    result = {"idea": idea, "started_at": started, "version": VERSION, "stages": {}}
    
    print("\n[STAGE 1] Detailed PM Planning", flush=True)
    context = f"Project Idea: {idea}"
    pm_agents_result = {}
    
    print("  Agent: Methodology Expert", flush=True)
    pm_agents_result["Methodology Expert"] = run_agent(METHODOLOGY_EXPERT, context, max_tokens=2500)
    method = pm_agents_result["Methodology Expert"]["data"].get("recommended_method", "Scrum")
    print(f"    -> Got method: {method} (provider: {pm_agents_result['Methodology Expert']['provider']})", flush=True)
    
    print(f"  Agent: Project Planner", flush=True)
    pm_agents_result["Project Planner"] = run_agent(PROJECT_PLANNER, f"{context}\nMethodology: {method}", max_tokens=3000)
    print(f"    -> Provider: {pm_agents_result['Project Planner']['provider']}", flush=True)
    
    print(f"  Agent: Risk Manager", flush=True)
    pm_agents_result["Risk Manager"] = run_agent(RISK_MANAGER_PM, context, max_tokens=2500)
    print(f"    -> Provider: {pm_agents_result['Risk Manager']['provider']}", flush=True)
    
    result["stages"]["pm_planning"] = {"pm_agents": pm_agents_result, "status": "complete"}
    
    print("\n[STAGE 2] PM Tool Architect", flush=True)
    team = pm_agents_result["Project Planner"]["data"].get("team_composition", []) if isinstance(pm_agents_result["Project Planner"]["data"], dict) else []
    tool_result = run_agent(PM_TOOL_ARCHITECT, f"Project: {idea}\nMethod: {method}\nTeam: {json.dumps(team)[:400]}\nCreate 12 cards.", max_tokens=3000)
    print(f"    -> Provider: {tool_result['provider']}", flush=True)
    board_html = render_pm_tool_html(tool_result["data"])
    result["stages"]["pm_tool"] = {"board_data": tool_result["data"], "html": board_html, "status": "complete"}
    
    print("\n[STAGE 3] 6-Phase PLM Execution", flush=True)
    plm_results = []
    plm_context = f"Idea: {idea}\nMethod: {method}"
    for phase_key, agent_def in PLM_AGENTS.items():
        print(f"  Phase {agent_def['id']}: {phase_key}", flush=True)
        r = run_agent(agent_def, f"{plm_context}\n\nExecute {phase_key} phase for this project.", max_tokens=2500)
        print(f"    -> Provider: {r['provider']}", flush=True)
        plm_results.append({
            "id": agent_def["id"], "name": phase_key.replace("_", " & "),
            "agent_icon": agent_def["icon"], "agent_role": agent_def["role"], "duration": agent_def["duration"],
            "data": r["data"], "provider": r["provider"], "error": r.get("error"),
            "status": "error" if r.get("error") else "complete"
        })
    result["stages"]["plm_execution"] = {"phases": plm_results, "status": "complete"}
    
    print("\n[STAGE 4] Prototype", flush=True)
    try:
        proto_system = "You are a frontend engineer. Output ONLY complete HTML (not JSON). Start with <!DOCTYPE html>. Include Tailwind CDN. Build a stunning SaaS landing page with gradient hero, nav, feature cards, testimonials, CTA. Use indigo/purple/pink."
        pr = smart_call(proto_system, f"Build landing for: {idea}", max_tokens=4000)
        html = pr["output"].replace("```html","").replace("```","").strip()
        if "<html" not in html.lower():
            html = f"<!DOCTYPE html><html><head><script src='https://cdn.tailwindcss.com'></script></head><body class='p-8'><h1 class='text-4xl font-bold'>{idea}</h1></body></html>"
        result["stages"]["prototype"] = {"html": html, "status": "complete"}
        print(f"    -> Provider: {pr['provider']}", flush=True)
    except Exception as e:
        print(f"    -> ERROR: {str(e)[:200]}", flush=True)
        result["stages"]["prototype"] = {"html": f"<!DOCTYPE html><html><body><h1>{idea}</h1></body></html>", "status": "error"}
    
    result["completed_at"] = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"\n{'='*60}\nAUTOPILOT COMPLETE\n{'='*60}\n", flush=True)
    return result

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
    def do_HEAD(self):
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
    def do_GET(self):
        if urlparse(self.path).path == "/health":
            self._send(200, {"status": "ok", "version": VERSION, "plm_phases": 6, "mode": "diagnostic"})
        else:
            self._send(200, {"message": f"PMGuru v{VERSION}"})
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode()) if length else {}
            if urlparse(self.path).path == "/autopilot":
                idea = body.get("idea", "").strip()
                if not idea: return self._send(400, {"error": "idea required"})
                return self._send(200, run_autopilot(idea))
            else: return self._send(404, {"error": "Not found"})
        except Exception as e:
            print(f"ERROR: {traceback.format_exc()}", flush=True)
            return self._send(500, {"error": str(e)[:500]})
    def log_message(self, fmt, *args): sys.stderr.write(f"{fmt % args}\n"); sys.stderr.flush()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print("="*60, flush=True)
    print(f"PMGuru Brain v{VERSION}", flush=True)
    print(f"Binding to 0.0.0.0:{port}", flush=True)
    print("="*60, flush=True)
    validate_api_keys_on_startup()
    print(f"✅ LISTENING on http://0.0.0.0:{port}", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
