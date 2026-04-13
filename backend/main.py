"""
PMGuru Brain v12.0 - Detailed PM Plan + 6-Phase PLM (no investor pitch)
Each agent generates rich, idea-specific content - not generic templates.
"""
import json, os, sys, datetime, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
import httpx

VERSION = "12.0"

# ============ PM PLANNING AGENTS (detailed outputs) ============
METHODOLOGY_EXPERT = {
    "icon": "🎯",
    "role": "PMI-PMP Methodology Consultant",
    "system": """You are a senior PM consultant (BCG/Bain caliber). Analyze the project DEEPLY and recommend a PM methodology with rich, specific reasoning tailored to THIS exact idea.
Output ONLY valid JSON (no markdown):
{
  "recommended_method": "Scrum",
  "confidence": "High",
  "reasoning": "2-3 paragraph detailed technical rationale citing specific aspects of THIS project",
  "layman_explanation": "3-4 sentence plain-English explanation for non-technical readers",
  "fit_analysis": {
    "team_size_fit": "Why this works for the expected team size",
    "uncertainty_fit": "Why this handles the requirement uncertainty of this project",
    "timeline_fit": "Why this delivery cadence matches the project timeline",
    "customer_feedback_fit": "Why this supports the feedback loops this project needs"
  },
  "why_not_others": [
    {"method": "Waterfall", "reason": "Specific 2-sentence reason citing this project's characteristics", "simple_reason": "Plain English version"},
    {"method": "Kanban", "reason": "Specific reason", "simple_reason": "Plain English"},
    {"method": "PRINCE2", "reason": "Specific reason", "simple_reason": "Plain English"}
  ],
  "method_details": {
    "roles": ["Product Owner - responsibilities specific to this project", "Scrum Master - role here", "Dev Team - composition for this project"],
    "ceremonies": ["Sprint Planning - how long, what gets decided", "Daily Standup - format", "Sprint Review - who attends", "Retro - focus areas"],
    "artifacts": ["Product Backlog - what it will contain for this project", "Sprint Backlog", "Increment"],
    "cadence": "2-week sprints with rationale for this duration"
  },
  "tool_recommendation": {
    "primary": "Linear",
    "alternatives": ["Jira", "Asana", "Notion"],
    "reason": "2-3 sentence reason specific to this project's needs and team"
  },
  "success_factors": [
    "Specific success factor 1 for this project",
    "Specific factor 2",
    "Specific factor 3",
    "Specific factor 4"
  ]
}"""
}

PROJECT_PLANNER = {
    "icon": "📊",
    "role": "Senior Project Planner",
    "system": """You are a senior project planner. Create a DETAILED project plan specific to THIS exact project idea.
Output ONLY valid JSON:
{
  "executive_summary": "3-paragraph summary of the project plan written for a non-technical executive sponsor - detailed, specific to the idea",
  "layman_summary": "3-sentence plain-English summary",
  "business_context": "2-paragraph explanation of the business problem and why this project solves it",
  "objectives": {
    "primary": "Specific measurable primary objective",
    "secondary": ["Specific secondary objective 1", "Specific secondary objective 2", "Specific secondary objective 3"]
  },
  "scope": {
    "in_scope": ["Specific capability 1 that WILL be built", "Capability 2", "Capability 3", "Capability 4", "Capability 5", "Capability 6"],
    "out_of_scope": ["Specific thing 1 NOT in scope", "Thing 2", "Thing 3"],
    "assumptions": ["Key assumption 1", "Assumption 2", "Assumption 3"],
    "constraints": ["Constraint 1", "Constraint 2"]
  },
  "phases": [
    {"name": "Phase 1 name", "duration": "2 weeks", "what_happens": "2-sentence explanation of this phase", "key_deliverables": ["Deliverable 1", "Deliverable 2", "Deliverable 3"], "entry_criteria": "What must be true to start", "exit_criteria": "What must be true to finish"}
  ],
  "timeline": {"total_duration": "16 weeks", "start": "Week 1", "end": "Week 16", "critical_path": "Which phases are on the critical path and why"},
  "budget_estimate": {
    "total": "$250K",
    "breakdown": {"team_salaries": "$180K", "tools_and_licenses": "$20K", "infrastructure": "$30K", "contingency": "$20K"},
    "rationale": "2-sentence explanation of how budget was estimated"
  },
  "team_composition": [
    {"role": "Specific role", "count": 1, "seniority": "Senior", "responsibilities": "What they do on this project", "when_needed": "Which phases"}
  ],
  "kpis": [
    {"metric": "Metric name", "target": "Target value", "measurement": "How measured", "why_it_matters": "Plain English reason"}
  ],
  "dependencies": ["External dependency 1", "Dependency 2", "Dependency 3"],
  "communication_plan": "Brief description of how progress gets communicated to stakeholders"
}
Provide 5 phases and 5 team roles. Be VERY specific to the project idea - no generic filler."""
}

RISK_MANAGER_PM = {
    "icon": "🛡️",
    "role": "Risk Manager (PRINCE2)",
    "system": """You are a risk expert. Generate 10 DEEP, specific risks for this exact project - not generic filler.
Output ONLY valid JSON:
{
  "executive_summary": "2-paragraph technical summary of the overall risk posture for this project",
  "layman_summary": "3-sentence plain-English summary of the biggest risks",
  "risk_register": [
    {
      "id": "R1",
      "category": "Technical/Business/Operational/Compliance/Market",
      "description": "Detailed technical description of the risk specific to this project - 2 sentences",
      "simple_description": "Plain English version",
      "probability": 4,
      "impact": 5,
      "score": 20,
      "mitigation": "Detailed mitigation strategy specific to this project - 2 sentences",
      "simple_mitigation": "Plain English mitigation",
      "contingency": "What we do if the mitigation fails",
      "owner": "Who owns this risk",
      "trigger_indicators": "Signs that this risk is materializing"
    }
  ],
  "governance": {
    "steering_committee": ["Specific role 1", "Role 2", "Role 3"],
    "meeting_cadence": "How often they meet",
    "escalation_path": "How issues escalate",
    "decision_authority": "Who decides what"
  }
}
Provide 10 distinct, detailed risks across different categories."""
}

# ============ 6-PHASE PLM AGENTS (each deep and specific) ============
PLM_AGENTS = {
    "Initiation": {
        "id": 1, "icon": "🚀", "role": "Project Initiation Expert", "duration": "1-2 weeks",
        "system": """You are a project initiation specialist. Generate detailed Phase 1 (Initiation) deliverables specific to THIS exact project.
Output ONLY valid JSON:
{
  "summary": "2-paragraph summary of what gets accomplished in initiation for this specific project",
  "layman_summary": "3-sentence plain English summary",
  "project_charter": {
    "purpose": "Why this project exists (specific to this idea)",
    "vision_statement": "1-sentence vision",
    "success_criteria": ["Criterion 1", "Criterion 2", "Criterion 3", "Criterion 4"],
    "high_level_scope": "What's being built in 2-3 sentences",
    "sponsor": "Role of project sponsor"
  },
  "stakeholder_identification": [
    {"stakeholder": "Specific role", "interest": "What they care about", "influence": "High/Medium/Low", "engagement_strategy": "How to work with them"}
  ],
  "initial_team": [
    {"role": "Role", "responsibilities": "What they do in initiation phase"}
  ],
  "kickoff_agenda": ["Agenda item 1", "Item 2", "Item 3", "Item 4", "Item 5"],
  "key_decisions_needed": ["Decision 1", "Decision 2", "Decision 3"],
  "initiation_deliverables": ["Deliverable 1", "Deliverable 2", "Deliverable 3", "Deliverable 4"],
  "exit_criteria": "What must be true to leave initiation phase"
}
Provide 5 stakeholders and 4 team roles. Be highly specific to the project idea."""
    },
    "Requirements": {
        "id": 2, "icon": "📋", "role": "Requirements Analyst / Business Analyst", "duration": "2-3 weeks",
        "system": """You are a senior BA. Generate DETAILED Phase 2 (Requirements Gathering) deliverables with real user stories specific to THIS project.
Output ONLY valid JSON:
{
  "summary": "2-paragraph summary of requirements gathering approach for this project",
  "layman_summary": "3-sentence plain English summary",
  "functional_requirements": [
    {"id": "FR-1", "requirement": "The system shall...", "priority": "Must", "rationale": "Why this is needed for this project"}
  ],
  "non_functional_requirements": [
    {"id": "NFR-1", "category": "Performance/Security/Usability/Scalability/Reliability", "requirement": "Specific measurable requirement", "target": "Specific target"}
  ],
  "user_personas": [
    {"name": "Persona name", "description": "Who they are (specific to this project)", "goals": ["Goal 1", "Goal 2"], "pain_points": ["Pain 1", "Pain 2"]}
  ],
  "user_stories": [
    {"id": "US-1", "story": "As a [specific user], I want [specific capability], so that [specific benefit] - tailored to this project", "priority": "High/Medium/Low", "points": 5, "acceptance_criteria": ["Given... When... Then...", "Given... When... Then..."]}
  ],
  "use_cases": [
    {"id": "UC-1", "name": "Use case name", "actor": "Who", "description": "What they do", "flow": ["Step 1", "Step 2", "Step 3"]}
  ],
  "business_rules": ["Rule 1 specific to this project", "Rule 2", "Rule 3"],
  "data_requirements": "Description of the main data entities the system needs to handle",
  "integration_requirements": ["External system 1 to integrate with", "System 2", "System 3"]
}
Provide 8 functional requirements, 6 NFRs, 3 personas, 8 user stories, 4 use cases. BE SPECIFIC TO THE PROJECT IDEA."""
    },
    "Design_Development": {
        "id": 3, "icon": "🏗️", "role": "Solutions Architect + Scrum Master", "duration": "6-10 weeks",
        "system": """You are a solutions architect and scrum master. Generate Phase 3 (Design & Development) deliverables with concrete technical decisions for THIS project.
Output ONLY valid JSON:
{
  "summary": "2-paragraph summary of design and development approach for this specific project",
  "layman_summary": "3-sentence plain English summary",
  "architecture": {
    "style": "Monolith/Microservices/Serverless - with rationale",
    "rationale": "Why this architecture fits this project",
    "components": [
      {"name": "Component name", "responsibility": "What it does", "tech": "Specific technology"}
    ],
    "data_flow": "How data flows through the system"
  },
  "tech_stack": {
    "frontend": {"framework": "e.g. Next.js 14", "reason": "Why", "ui_library": "e.g. Tailwind + shadcn"},
    "backend": {"language": "e.g. Python", "framework": "e.g. FastAPI", "reason": "Why"},
    "database": {"primary": "e.g. Postgres", "reason": "Why", "cache": "e.g. Redis"},
    "third_party": ["Service 1 for X", "Service 2 for Y", "Service 3 for Z"]
  },
  "sprints": [
    {"number": 1, "duration": "2 weeks", "goal": "Specific sprint goal", "stories_included": ["US-1", "US-2"], "total_points": 25, "key_deliverables": ["Deliverable 1", "Deliverable 2"]}
  ],
  "code_structure": {
    "description": "How the codebase is organized",
    "key_directories": ["/frontend - description", "/backend - description", "/docs - description"]
  },
  "coding_standards": ["Standard 1", "Standard 2", "Standard 3"],
  "development_practices": ["Code review on every PR", "TDD for core logic", "Practice 3"],
  "estimated_velocity": 25,
  "total_effort": "160 story points across 6 sprints"
}
Provide 6 components, 6 sprints. Be very specific to the actual project idea - real tech choices, not generic."""
    },
    "Testing_QA": {
        "id": 4, "icon": "✅", "role": "Senior QA Lead", "duration": "2-3 weeks",
        "system": """You are a senior QA lead. Generate Phase 4 (Testing & QA) deliverables with specific test cases for THIS project.
Output ONLY valid JSON:
{
  "summary": "2-paragraph testing strategy summary for this specific project",
  "layman_summary": "3-sentence plain English summary",
  "test_strategy": {
    "approach": "Test pyramid approach description",
    "unit_tests": {"percentage": "70%", "tool": "e.g. Jest/Pytest", "coverage_target": "80%"},
    "integration_tests": {"percentage": "20%", "tool": "Tool", "focus": "What to test"},
    "e2e_tests": {"percentage": "10%", "tool": "e.g. Playwright", "critical_flows": ["Flow 1", "Flow 2"]},
    "performance_tests": {"tool": "e.g. k6", "targets": ["Latency < 200ms", "Target 2"]},
    "security_tests": {"approach": "SAST + DAST", "tools": ["Tool 1", "Tool 2"]}
  },
  "test_cases": [
    {"id": "TC-1", "feature": "Specific feature being tested", "preconditions": "Setup needed", "steps": ["Step 1", "Step 2", "Step 3"], "expected_result": "What should happen", "priority": "P0/P1/P2"}
  ],
  "quality_gates": [
    {"gate": "Gate name", "criteria": "What must be met", "when": "When it's checked"}
  ],
  "bug_severity_definitions": {
    "P0_Critical": "System down / data loss",
    "P1_High": "Major feature broken",
    "P2_Medium": "Feature degraded",
    "P3_Low": "Cosmetic"
  },
  "test_environments": ["Dev - purpose", "Staging - purpose", "Production - purpose"],
  "defect_management": "How bugs are tracked, triaged, and fixed",
  "acceptance_criteria": "Overall criteria for phase 4 exit"
}
Provide 8 test cases and 5 quality gates specific to this project."""
    },
    "Deployment": {
        "id": 5, "icon": "🚢", "role": "DevOps Engineer / SRE", "duration": "1-2 weeks",
        "system": """You are a senior DevOps engineer. Generate Phase 5 (Deployment) deliverables specific to THIS project.
Output ONLY valid JSON:
{
  "summary": "2-paragraph deployment strategy summary for this specific project",
  "layman_summary": "3-sentence plain English summary",
  "deployment_strategy": "Blue-green / Canary / Rolling - with rationale for this project",
  "infrastructure": {
    "cloud_provider": "e.g. AWS/GCP/Vercel",
    "reasoning": "Why this cloud for this project",
    "services": [
      {"service": "Service name", "purpose": "What it's used for", "estimated_cost": "$X/month"}
    ],
    "total_monthly_cost": "$X"
  },
  "ci_cd_pipeline": {
    "platform": "e.g. GitHub Actions",
    "stages": [
      {"stage": "Lint", "what_happens": "What runs here", "duration": "~30s"},
      {"stage": "Unit Tests", "what_happens": "...", "duration": "~2min"},
      {"stage": "Build", "what_happens": "...", "duration": "~3min"},
      {"stage": "Deploy to Staging", "what_happens": "...", "duration": "~2min"},
      {"stage": "E2E Tests", "what_happens": "...", "duration": "~5min"},
      {"stage": "Deploy to Production", "what_happens": "Manual approval + deploy", "duration": "~3min"}
    ]
  },
  "environments": [
    {"name": "Dev", "purpose": "Purpose", "who_deploys": "Developers", "auto_deploy": true}
  ],
  "go_live_checklist": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6"],
  "rollback_strategy": "How rollback works if deployment fails",
  "secrets_management": "How secrets are stored and accessed",
  "database_migration_strategy": "How DB schema changes are handled",
  "launch_day_plan": ["Hour 0: Step 1", "Hour 1: Step 2", "Hour 2: Step 3"]
}
Be specific to the actual project idea."""
    },
    "Monitoring": {
        "id": 6, "icon": "📡", "role": "SRE / Observability Lead", "duration": "Ongoing",
        "system": """You are an SRE. Generate Phase 6 (Monitoring & Operations) deliverables for THIS project.
Output ONLY valid JSON:
{
  "summary": "2-paragraph monitoring and operations strategy for this specific project",
  "layman_summary": "3-sentence plain English summary",
  "observability_stack": {
    "logging": {"tool": "e.g. Datadog/Loki", "what_gets_logged": "What events are logged", "retention": "30 days"},
    "metrics": {"tool": "e.g. Prometheus/Datadog", "key_metrics": ["Metric 1", "Metric 2", "Metric 3"]},
    "tracing": {"tool": "e.g. OpenTelemetry", "purpose": "Request tracing across services"},
    "alerting": {"tool": "e.g. PagerDuty", "channels": ["Slack", "SMS", "Email"]}
  },
  "slos": [
    {"metric": "Availability", "target": "99.9%", "measurement": "How it's measured", "why_it_matters": "Plain English"},
    {"metric": "P95 Latency", "target": "< 500ms", "measurement": "How measured", "why_it_matters": "Plain English"}
  ],
  "key_dashboards": [
    {"name": "Dashboard name", "purpose": "What it shows", "audience": "Who uses it"}
  ],
  "alert_rules": [
    {"alert": "Alert name", "condition": "When it fires", "severity": "P0/P1/P2", "response": "What to do"}
  ],
  "incident_response": {
    "on_call_rotation": "How on-call works",
    "severity_levels": {"P0": "Definition", "P1": "Definition", "P2": "Definition"},
    "runbook_template": "How runbooks are structured",
    "post_mortem_process": "How post-mortems work"
  },
  "continuous_improvement": {
    "review_cadence": "Weekly/Monthly review of metrics",
    "iteration_process": "How learnings feed back into development",
    "user_feedback_loop": "How user feedback is captured and acted on"
  }
}
Provide 5 SLOs, 4 dashboards, 6 alert rules - all specific to this project."""
    }
}

# PM TOOL ARCHITECT (same as v11)
PM_TOOL_ARCHITECT = {
    "icon": "🛠️",
    "role": "PM Tool Engineer",
    "system": """You are a senior PM tool engineer. Design a custom Kanban/Scrum board for THIS specific project.
Output ONLY valid JSON:
{
  "board_title": "Project Name - Sprint Board",
  "methodology": "Scrum",
  "columns": [{"id": "backlog", "name": "Backlog", "color": "#64748b"}, {"id": "sprint", "name": "Sprint Backlog", "color": "#6366f1"}, {"id": "progress", "name": "In Progress", "color": "#f59e0b"}, {"id": "review", "name": "In Review", "color": "#8b5cf6"}, {"id": "done", "name": "Done", "color": "#10b981"}],
  "sprints": [{"number": 1, "name": "Sprint 1: Foundation", "goal": "Setup + core infrastructure"}],
  "team_members": [{"id": "alice", "name": "Alice", "role": "PM", "color": "#6366f1", "initials": "AL"}],
  "cards": [{"id": "T-1", "title": "Setup project repo", "description": "Create GitHub repo with initial structure", "column": "backlog", "sprint": 1, "assignee": "alice", "priority": "P0", "story_points": 3, "tags": ["setup"]}],
  "velocity_target": 25
}
Create EXACTLY 15 cards with real tasks for the actual project idea. Use 4-5 team members."""
}

# ============ AI CALLS ============
def call_groq(system, user, max_tokens=3000):
    key = os.getenv("GROQ_API_KEY")
    if not key: raise ValueError("GROQ_API_KEY not set")
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "max_tokens": max_tokens, "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=120.0)
    return r.json()["choices"][0]["message"]["content"]

def call_gemini(system, user, max_tokens=3000):
    key = os.getenv("GEMINI_API_KEY")
    if not key: raise ValueError("GEMINI_API_KEY not set")
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
        json={"contents": [{"parts": [{"text": f"{system}\n\n{user}\n\nReturn ONLY valid JSON."}]}],
              "generationConfig": {"maxOutputTokens": max_tokens, "responseMimeType": "application/json"}}, timeout=120.0)
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def smart_call(system, user, max_tokens=3000):
    try: return {"output": call_groq(system, user, max_tokens), "provider": "groq", "error": None}
    except Exception as e1:
        try: return {"output": call_gemini(system, user, max_tokens), "provider": "gemini", "error": None}
        except Exception as e2:
            return {"output": '{"summary": "Agent failed", "error": true, "layman_summary": "This agent could not complete"}', "provider": "none", "error": f"{str(e1)[:80]} | {str(e2)[:80]}"}

def parse_json_safe(text):
    if not text: return {"summary": "Empty response", "error": True}
    try:
        text = text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result if isinstance(result, dict) else {"summary": "Invalid format", "error": True}
    except Exception as e:
        return {"summary": f"Parse error: {str(e)[:100]}", "error": True, "raw": text[:500]}

def run_agent(agent_def, user_input, max_tokens=3000):
    try:
        r = smart_call(agent_def["system"], user_input, max_tokens)
        data = parse_json_safe(r["output"])
        return {"role": agent_def["role"], "icon": agent_def["icon"], "data": data, "provider": r["provider"], "error": r["error"]}
    except Exception as e:
        return {"role": agent_def.get("role", "Agent"), "icon": agent_def.get("icon", "🤖"),
                "data": {"summary": f"Agent crashed: {str(e)[:100]}", "error": True, "layman_summary": "This agent had a problem."},
                "provider": "none", "error": str(e)[:200]}

# ============ PM TOOL HTML RENDERER (compact version from v11) ============
def render_pm_tool_html(board_data):
    board = board_data if isinstance(board_data, dict) and not board_data.get("error") else {
        "board_title": "Fallback Board", "methodology": "Scrum",
        "columns": [{"id": "backlog", "name": "Backlog", "color": "#64748b"}, {"id": "done", "name": "Done", "color": "#10b981"}],
        "sprints": [{"number": 1, "name": "Sprint 1", "goal": "Core work"}],
        "team_members": [{"id": "team", "name": "Team", "role": "All", "color": "#6366f1", "initials": "TM"}],
        "cards": [{"id": "T-1", "title": "Setup", "description": "Initial setup", "column": "backlog", "sprint": 1, "assignee": "team", "priority": "P0", "story_points": 3, "tags": ["setup"]}],
        "velocity_target": 25
    }
    board_json = json.dumps(board)
    title = board.get("board_title", "PM Board")
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>""" + title + """</title><script src="https://cdn.tailwindcss.com"></script>
<style>body{font-family:-apple-system,sans-serif}.card{cursor:grab}.card.dragging{opacity:0.4}.column.drag-over{background:rgba(99,102,241,0.15)}.priority-P0{border-left:3px solid #ef4444}.priority-P1{border-left:3px solid #f59e0b}.priority-P2{border-left:3px solid #10b981}</style>
</head><body class="bg-gradient-to-br from-slate-900 to-indigo-950 min-h-screen text-slate-100">
<header class="border-b border-slate-700 bg-slate-900/50 sticky top-0 z-10"><div class="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between flex-wrap gap-3"><div><h1 class="text-2xl font-black bg-gradient-to-r from-indigo-400 to-pink-400 bg-clip-text text-transparent" id="bt"></h1><p class="text-xs text-slate-400"><span id="bm"></span> · <span id="cc"></span> tasks</p></div><div class="flex gap-3 items-center"><div class="text-right text-xs"><div class="text-slate-400">VELOCITY</div><div class="text-lg font-black text-emerald-400" id="vel">0 pts</div></div><select id="filt" class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm"><option value="">All</option></select><button onclick="rst()" class="px-3 py-2 bg-slate-800 rounded-lg text-xs">🔄</button></div></div></header>
<div class="max-w-[1600px] mx-auto p-6"><div id="tb" class="flex gap-2 mb-6 flex-wrap"></div><div id="si" class="mb-6"></div><div id="bd" class="flex gap-4 overflow-x-auto pb-4"></div></div>
<div id="mdl" class="hidden fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-6" onclick="if(event.target===this)cm()"><div class="bg-slate-800 rounded-2xl p-6 max-w-2xl w-full border border-slate-700"><div id="mc"></div><button onclick="cm()" class="mt-4 px-4 py-2 bg-slate-700 rounded-lg">Close</button></div></div>
<script>
const BD=""" + board_json + """;const SK='pmgv12_'+encodeURIComponent(BD.board_title||'b');
function ls(){try{const s=localStorage.getItem(SK);if(s)return JSON.parse(s)}catch(e){}return JSON.parse(JSON.stringify(BD))}
function ss(s){try{localStorage.setItem(SK,JSON.stringify(s))}catch(e){}}
let st=ls();function rst(){if(confirm('Reset?')){localStorage.removeItem(SK);st=JSON.parse(JSON.stringify(BD));rn()}}
function gm(id){return(st.team_members||[]).find(m=>m.id===id)||{name:id||'?',color:'#64748b',initials:'??'}}
function rn(){document.getElementById('bt').textContent=st.board_title||'Board';document.getElementById('bm').textContent=st.methodology||'Scrum';document.getElementById('cc').textContent=(st.cards||[]).length;document.getElementById('vel').textContent=(st.velocity_target||0)+' pts';
document.getElementById('tb').innerHTML=(st.team_members||[]).map(m=>`<div class="flex items-center gap-2 px-3 py-2 bg-slate-800/50 rounded-lg"><div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-black" style="background:${m.color}">${m.initials}</div><div><div class="text-xs font-bold">${m.name}</div><div class="text-[10px] text-slate-400">${m.role}</div></div></div>`).join('');
const fs=document.getElementById('filt'),cf=fs.value;fs.innerHTML='<option value="">All</option>'+(st.team_members||[]).map(m=>`<option value="${m.id}">${m.name}</option>`).join('');fs.value=cf;
if(st.sprints&&st.sprints[0]){const s=st.sprints[0];document.getElementById('si').innerHTML=`<div class="p-4 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl"><div class="text-xs opacity-80">CURRENT SPRINT</div><div class="text-lg font-black">${s.name}</div><div class="text-sm opacity-90 mt-1">${s.goal||''}</div></div>`}
const bd=document.getElementById('bd'),f=fs.value;
bd.innerHTML=(st.columns||[]).map(col=>{const cs=(st.cards||[]).filter(c=>c.column===col.id&&(!f||c.assignee===f));const pts=cs.reduce((s,c)=>s+(c.story_points||0),0);return `<div class="column flex-shrink-0 w-80 bg-slate-800/40 rounded-xl p-4 border border-slate-700" data-column="${col.id}" ondragover="event.preventDefault();this.classList.add('drag-over')" ondragleave="this.classList.remove('drag-over')" ondrop="hd(event,'${col.id}')"><div class="flex items-center justify-between mb-4"><div class="flex items-center gap-2"><div class="w-3 h-3 rounded-full" style="background:${col.color}"></div><h3 class="font-bold">${col.name}</h3><span class="text-xs text-slate-400">${cs.length}</span></div><span class="text-xs bg-slate-700 px-2 py-1 rounded">${pts} pts</span></div><div class="space-y-2">${cs.map(c=>{const m=gm(c.assignee);return `<div draggable="true" ondragstart="hds(event,'${c.id}')" ondragend="this.classList.remove('dragging')" onclick="oc('${c.id}')" class="card priority-${c.priority||'P2'} p-3 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700"><div class="text-[10px] text-slate-400 font-mono">${c.id}</div><div class="text-sm font-semibold mt-1">${c.title}</div><div class="flex items-center justify-between mt-3"><div class="flex gap-1">${(c.tags||[]).slice(0,2).map(t=>`<span class="text-[9px] bg-slate-700 px-2 py-0.5 rounded">${t}</span>`).join('')}</div><div class="flex items-center gap-2"><span class="text-xs bg-indigo-600 px-2 py-0.5 rounded font-bold">${c.story_points||0}</span><div class="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-black" style="background:${m.color}">${m.initials}</div></div></div></div>`}).join('')}</div></div>`}).join('')}
let di=null;function hds(e,id){di=id;e.target.classList.add('dragging')}function hd(e,cid){e.preventDefault();e.currentTarget.classList.remove('drag-over');if(!di)return;const c=st.cards.find(x=>x.id===di);if(c){c.column=cid;ss(st);rn()}di=null}
function oc(id){const c=st.cards.find(x=>x.id===id);if(!c)return;const m=gm(c.assignee);document.getElementById('mc').innerHTML=`<div class="text-xs text-slate-400 font-mono">${c.id}</div><h2 class="text-2xl font-black mt-1">${c.title}</h2><p class="text-slate-300 mt-3">${c.description||''}</p><div class="grid grid-cols-4 gap-3 mt-5"><div class="p-3 bg-slate-700/50 rounded-lg"><div class="text-[10px] text-slate-400">PRIORITY</div><div class="font-bold">${c.priority||'P2'}</div></div><div class="p-3 bg-slate-700/50 rounded-lg"><div class="text-[10px] text-slate-400">POINTS</div><div class="font-bold">${c.story_points||0}</div></div><div class="p-3 bg-slate-700/50 rounded-lg"><div class="text-[10px] text-slate-400">SPRINT</div><div class="font-bold">${c.sprint||'-'}</div></div><div class="p-3 bg-slate-700/50 rounded-lg"><div class="text-[10px] text-slate-400">ASSIGNEE</div><div class="font-bold">${m.name}</div></div></div>`;document.getElementById('mdl').classList.remove('hidden')}
function cm(){document.getElementById('mdl').classList.add('hidden')}
document.getElementById('filt').addEventListener('change',rn);rn();
</script></body></html>"""

# ============ THE AUTOPILOT ============
def run_autopilot(idea):
    started = datetime.datetime.utcnow().isoformat()
    result = {"idea": idea, "started_at": started, "version": VERSION, "stages": {}}
    
    # STAGE 1: PM PLANNING (3 detailed agents)
    print(f"[AUTOPILOT] Stage 1: Detailed PM Planning", flush=True)
    context = f"Project Idea: {idea}"
    pm_agents_result = {}
    
    print("[AUTOPILOT]  Running Methodology Expert...", flush=True)
    pm_agents_result["Methodology Expert"] = run_agent(METHODOLOGY_EXPERT, context, max_tokens=3000)
    
    method = pm_agents_result["Methodology Expert"]["data"].get("recommended_method", "Scrum")
    print(f"[AUTOPILOT]  Running Project Planner (method: {method})...", flush=True)
    pm_agents_result["Project Planner"] = run_agent(PROJECT_PLANNER, f"{context}\nMethodology: {method}", max_tokens=3500)
    
    print("[AUTOPILOT]  Running Risk Manager...", flush=True)
    pm_agents_result["Risk Manager"] = run_agent(RISK_MANAGER_PM, context, max_tokens=3000)
    
    result["stages"]["pm_planning"] = {"pm_agents": pm_agents_result, "status": "complete"}
    
    # STAGE 2: PM TOOL
    print("[AUTOPILOT] Stage 2: PM Tool Architect", flush=True)
    team = []
    try: team = pm_agents_result["Project Planner"]["data"].get("team_composition", [])
    except: pass
    tool_result = run_agent(PM_TOOL_ARCHITECT, f"Project: {idea}\nMethodology: {method}\nTeam: {json.dumps(team)[:400]}\nCreate 15 realistic cards.", max_tokens=3500)
    board_html = render_pm_tool_html(tool_result["data"])
    result["stages"]["pm_tool"] = {"board_data": tool_result["data"], "html": board_html, "status": "complete"}
    
    # STAGE 3: 6-PHASE PLM (each detailed)
    print("[AUTOPILOT] Stage 3: 6-Phase PLM Execution", flush=True)
    plm_results = []
    plm_context = f"Project Idea: {idea}\nMethodology: {method}"
    
    for phase_key, agent_def in PLM_AGENTS.items():
        print(f"[AUTOPILOT]  Phase {agent_def['id']}: {phase_key}", flush=True)
        r = run_agent(agent_def, f"{plm_context}\n\nExecute the {phase_key.replace('_',' & ')} phase in detail for this exact project.", max_tokens=3500)
        plm_results.append({
            "id": agent_def["id"], "name": phase_key.replace("_", " & "),
            "agent_icon": agent_def["icon"], "agent_role": agent_def["role"], "duration": agent_def["duration"],
            "data": r["data"], "provider": r["provider"], "error": r.get("error"),
            "status": "error" if r.get("error") else "complete"
        })
        summary = str(r["data"].get("layman_summary", r["data"].get("summary", "")))[:200]
        plm_context += f"\n[Phase {agent_def['id']} {phase_key}]: {summary}"
    
    result["stages"]["plm_execution"] = {"phases": plm_results, "status": "complete"}
    
    # STAGE 4: PROTOTYPE
    print("[AUTOPILOT] Stage 4: Prototype", flush=True)
    try:
        proto_system = "You are a senior frontend engineer. Output ONLY complete HTML (not JSON). Start with <!DOCTYPE html>. Include Tailwind CDN. Build a stunning SaaS landing page with gradient hero, nav, 4 feature cards, testimonials, pricing, CTA footer. Use indigo/purple/pink."
        pr = smart_call(proto_system, f"Build landing page for: {idea}", max_tokens=4000)
        html = pr["output"].replace("```html","").replace("```","").strip()
        if "<html" not in html.lower():
            html = f"<!DOCTYPE html><html><head><script src='https://cdn.tailwindcss.com'></script></head><body class='p-8'><h1 class='text-4xl font-bold'>{idea}</h1></body></html>"
        result["stages"]["prototype"] = {"html": html, "status": "complete"}
    except Exception as e:
        result["stages"]["prototype"] = {"html": f"<!DOCTYPE html><html><body><h1>{idea}</h1><p>Failed: {str(e)[:100]}</p></body></html>", "status": "error"}
    
    print("[AUTOPILOT] ALL DONE", flush=True)
    result["completed_at"] = datetime.datetime.utcnow().isoformat()
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
    def do_GET(self):
        if urlparse(self.path).path == "/health":
            self._send(200, {"status": "ok", "version": VERSION, "plm_phases": 6, "mode": "detailed_auto"})
        else: self._send(200, {"message": f"PMGuru v{VERSION}"})
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
    print("="*50, flush=True)
    print(f"PMGuru Brain v{VERSION} - Detailed Plans + 6-Phase PLM", flush=True)
    print(f"Binding to 0.0.0.0:{port}", flush=True)
    print("="*50, flush=True)
    print(f"✅ LISTENING on http://0.0.0.0:{port}", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
