"""
PMGuru Brain v10.0 - Path A: Custom PM Tool Generator
- Stage 1: PM Planning (4 agents, same as v9)
- Stage 2: PM Tool Architect generates custom Kanban/Scrum board
- Stage 3: PLM Execution (8 agents, same as v9)
- Stage 4: Production prototype
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
        "role": "PMI-PMP Certified Methodology Consultant (BCG caliber)",
        "icon": "🎯",
        "system": """You are a top-tier PM consultant trained on ALL methodologies: Agile, Scrum, Kanban, Waterfall, PRINCE2, PMBOK, SAFe, Lean, XP, Critical Path.
Output ONLY valid JSON:
{"recommended_method": "Scrum", "confidence": "High", "reasoning": "2-3 sentence rationale",
 "why_not_others": [{"method": "Waterfall", "reason": "..."}, {"method": "Kanban", "reason": "..."}],
 "method_details": {"roles": ["..."], "ceremonies": ["..."], "artifacts": ["..."], "cadence": "..."},
 "tool_recommendation": {"primary": "Linear", "alternatives": ["Jira", "Asana"], "reason": "..."},
 "success_factors": ["...", "...", "..."]}"""
    },
    "Project Planner": {
        "role": "Senior Project Planner (PMP)",
        "icon": "📊",
        "system": """You are a senior project planner with BCG-level thinking.
Output ONLY valid JSON:
{"executive_summary": "3-sentence C-suite summary", "objectives": ["..."],
 "scope": {"in_scope": ["..."], "out_of_scope": ["..."]},
 "phases": [{"name": "Initiation", "duration": "1 week", "milestones": ["..."]}],
 "timeline": {"total_duration": "16 weeks", "start": "Week 1", "end": "Week 16"},
 "budget_estimate": {"total": "$250K", "breakdown": {"team": "$180K", "tools": "$20K", "infra": "$50K"}},
 "team_composition": [{"role": "PM", "count": 1, "seniority": "Senior"}],
 "kpis": [{"metric": "On-time delivery", "target": "95%"}]}
Provide 5 phases."""
    },
    "Risk & Governance": {
        "role": "Risk Manager + Governance Lead (PRINCE2)",
        "icon": "🛡️",
        "system": """You are a risk & governance expert.
Output ONLY valid JSON:
{"executive_summary": "2-sentence risk posture",
 "risk_register": [{"id": "R1", "category": "Technical", "description": "...", "probability": 4, "impact": 5, "score": 20, "mitigation": "...", "owner": "CTO"}],
 "governance": {"steering_committee": ["..."], "meeting_cadence": "Bi-weekly"},
 "compliance": ["GDPR", "SOC 2"]}
Provide 8 risks."""
    },
    "Stakeholder Strategist": {
        "role": "Stakeholder Strategist",
        "icon": "🤝",
        "system": """You are a stakeholder strategist.
Output ONLY valid JSON:
{"executive_summary": "...",
 "stakeholder_map": [{"name": "CEO", "power": "High", "interest": "High", "strategy": "Manage Closely", "frequency": "Weekly"}],
 "communication_plan": [{"audience": "Exec", "channel": "Email", "cadence": "Weekly", "content": "RAG status"}]}
Provide 6 stakeholders."""
    }
}

# ============ STAGE 2: PM TOOL ARCHITECT (NEW IN V10) ============
PM_TOOL_ARCHITECT = {
    "role": "Senior PM Tool Engineer (ex-Linear/Jira)",
    "icon": "🛠️",
    "system": """You are a senior PM tool engineer. Your job is to design a custom Kanban/Scrum board tailored to a specific project.
Output ONLY valid JSON matching this schema:
{
  "board_title": "Project name - Sprint Board",
  "methodology": "Scrum",
  "columns": [{"id": "backlog", "name": "Backlog", "color": "#64748b", "wip_limit": null}],
  "sprints": [{"number": 1, "name": "Sprint 1: Foundation", "goal": "...", "start_date": "Week 1", "end_date": "Week 2"}],
  "team_members": [{"id": "alice", "name": "Alice", "role": "PM", "color": "#6366f1", "initials": "AL"}],
  "cards": [
    {"id": "T-1", "title": "Setup project repo", "description": "...", "column": "backlog", "sprint": 1, "assignee": "alice", "priority": "P0", "story_points": 3, "tags": ["setup", "devops"]}
  ],
  "velocity_target": 25,
  "custom_fields": [{"name": "Business Value", "type": "number"}]
}
For Scrum: columns should be Backlog, Sprint Backlog, In Progress, In Review, Done.
For Kanban: columns based on the actual workflow of the project.
Create 15-20 real cards with specific tasks for the actual project idea.
Team size should match the project's team composition (4-6 members).
Each card should have meaningful titles, descriptions, realistic story points (1, 2, 3, 5, 8, 13), and varied priorities."""
}

# ============ STAGE 3: PLM AGENTS (same as v9) ============
PLM_AGENTS = {
    "Strategist": {"role": "Product Strategist", "icon": "🎯", "system": """Output ONLY valid JSON:
{"summary": "...", "vision": "...", "target_users": ["..."], "market_size": {"tam": "$X B", "sam": "$X B", "som": "$X M"}, "okrs": [{"objective": "...", "key_results": ["..."]}], "top_features": [{"name": "...", "rice_score": 85, "priority": "P0"}]}"""},
    "Business Analyst": {"role": "Business Analyst", "icon": "📋", "system": """Output ONLY valid JSON:
{"summary": "...", "user_stories": [{"id": "US-1", "story": "As a X, I want Y, so that Z", "priority": "High", "points": 5, "acceptance_criteria": ["Given...When...Then..."]}], "nfrs": ["..."]}
Provide 6 stories."""},
    "UX Designer": {"role": "UX Designer", "icon": "🎨", "system": """Output ONLY valid JSON:
{"summary": "...", "user_flows": [{"name": "...", "steps": ["..."]}], "wireframes": [{"screen": "...", "elements": ["..."]}], "design_system": {"primary_color": "#6366f1", "font": "Inter"}}"""},
    "Scrum Master": {"role": "Scrum Master", "icon": "🏃", "system": """Output ONLY valid JSON:
{"summary": "...", "sprints": [{"number": 1, "goal": "...", "tasks": [{"title": "...", "points": 5}], "total_points": 25}], "velocity_forecast": 28}
Provide 4 sprints."""},
    "QA Lead": {"role": "QA Lead", "icon": "✅", "system": """Output ONLY valid JSON:
{"summary": "...", "test_strategy": {"unit": "70%", "integration": "20%", "e2e": "10%"}, "test_cases": [{"id": "TC-1", "feature": "...", "expected": "..."}], "quality_gates": ["..."]}"""},
    "DevOps Engineer": {"role": "DevOps Engineer", "icon": "🚀", "system": """Output ONLY valid JSON:
{"summary": "...", "ci_cd_pipeline": ["Lint", "Test", "Build", "Deploy"], "infrastructure": {"cloud": "AWS"}, "slos": [{"metric": "Uptime", "target": "99.9%"}]}"""},
    "Risk Manager": {"role": "Risk Officer", "icon": "⚠️", "system": """Output ONLY valid JSON:
{"summary": "...", "raid_log": [{"id": "R-1", "description": "...", "probability": 4, "impact": 5, "score": 20, "mitigation": "..."}]}
Provide 6 risks."""},
    "Stakeholder Comms": {"role": "Comms Manager", "icon": "📢", "system": """Output ONLY valid JSON:
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

# ============ AI CALLS ============
def call_groq(system, user, max_tokens=2500):
    key = os.getenv("GROQ_API_KEY")
    if not key: raise ValueError("GROQ_API_KEY not set")
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "max_tokens": max_tokens, "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=120.0)
    return r.json()["choices"][0]["message"]["content"]

def call_gemini(system, user, max_tokens=2500):
    key = os.getenv("GEMINI_API_KEY")
    if not key: raise ValueError("GEMINI_API_KEY not set")
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
        json={"contents": [{"parts": [{"text": f"{system}\n\n{user}\n\nReturn ONLY valid JSON."}]}],
              "generationConfig": {"maxOutputTokens": max_tokens, "responseMimeType": "application/json"}}, timeout=120.0)
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def smart_call(system, user, max_tokens=2500):
    try: return {"output": call_groq(system, user, max_tokens), "provider": "groq"}
    except Exception as e1:
        try: return {"output": call_gemini(system, user, max_tokens), "provider": "gemini"}
        except Exception as e2: return {"output": json.dumps({"summary": "AI error", "error": True}), "provider": "none"}

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
        r = smart_call(agent["system"], context)
        parsed = parse_json(r["output"])
        results[name] = {"role": agent["role"], "icon": agent["icon"], "data": parsed}
        if isinstance(parsed, dict):
            context += f"\n[{name}]: {str(parsed.get('executive_summary', parsed.get('reasoning', '')))[:200]}"
    return {"idea": idea, "stage": "pm_planning", "pm_agents": results, "generated_at": __import__("datetime").datetime.utcnow().isoformat()}

# ============ STAGE 2: PM TOOL GENERATION (NEW) ============
def generate_pm_tool(idea, pm_plan):
    """PM Tool Architect generates structured board data."""
    method = "Scrum"
    team = []
    try:
        method = pm_plan["pm_agents"]["Methodology Expert"]["data"]["recommended_method"]
        team = pm_plan["pm_agents"]["Project Planner"]["data"].get("team_composition", [])
    except: pass
    
    user = f"Project: {idea}\nMethodology: {method}\nTeam: {json.dumps(team)[:400]}\n\nDesign a complete custom PM board tailored to this project with 15-20 realistic cards."
    r = smart_call(PM_TOOL_ARCHITECT["system"], user, max_tokens=3500)
    board_data = parse_json(r["output"])
    
    # Generate the actual HTML PM tool from the structured board data
    html = render_pm_tool_html(idea, method, board_data)
    return {"board_data": board_data, "html": html, "provider": r["provider"]}

def render_pm_tool_html(idea, method, board):
    """Render a complete self-contained Kanban board HTML from structured data."""
    board_json = json.dumps(board)
    title = board.get("board_title", f"{idea[:40]} Board")
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>""" + title + """</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; }
.card { cursor: grab; transition: all 0.2s; }
.card:active { cursor: grabbing; }
.card.dragging { opacity: 0.4; transform: rotate(3deg); }
.column.drag-over { background: rgba(99, 102, 241, 0.1); }
.priority-P0 { border-left: 3px solid #ef4444; }
.priority-P1 { border-left: 3px solid #f59e0b; }
.priority-P2 { border-left: 3px solid #10b981; }
@keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.card { animation: slideIn 0.3s ease-out; }
</style>
</head>
<body class="bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 min-h-screen text-slate-100">

<header class="border-b border-slate-700 bg-slate-900/50 backdrop-blur sticky top-0 z-10">
  <div class="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-black bg-gradient-to-r from-indigo-400 to-pink-400 bg-clip-text text-transparent" id="board-title">Loading...</h1>
      <p class="text-xs text-slate-400 mt-1"><span id="board-method"></span> · Generated by PMGuru · <span id="card-count"></span> tasks</p>
    </div>
    <div class="flex gap-3 items-center">
      <div class="text-right text-xs">
        <div class="text-slate-400">VELOCITY TARGET</div>
        <div class="text-lg font-black text-emerald-400" id="velocity">0 pts</div>
      </div>
      <select id="filter-assignee" class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm">
        <option value="">All Members</option>
      </select>
      <button onclick="resetBoard()" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs">🔄 Reset</button>
    </div>
  </div>
</header>

<div class="max-w-[1600px] mx-auto p-6">
  <div id="team-bar" class="flex gap-2 mb-6 flex-wrap"></div>
  <div id="sprint-info" class="mb-6"></div>
  <div id="board" class="flex gap-4 overflow-x-auto pb-4"></div>
</div>

<div id="card-modal" class="hidden fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-6" onclick="if(event.target===this)closeModal()">
  <div class="bg-slate-800 rounded-2xl p-6 max-w-2xl w-full border border-slate-700">
    <div id="modal-content"></div>
    <button onclick="closeModal()" class="mt-4 px-4 py-2 bg-slate-700 rounded-lg">Close</button>
  </div>
</div>

<script>
const BOARD_DATA = """ + board_json + """;
const STORAGE_KEY = 'pmguru_board_' + encodeURIComponent(BOARD_DATA.board_title || 'board');

function loadState() {
  try { const s = localStorage.getItem(STORAGE_KEY); if (s) return JSON.parse(s); } catch(e) {}
  return JSON.parse(JSON.stringify(BOARD_DATA));
}
function saveState(state) { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch(e) {} }
let state = loadState();

function resetBoard() {
  if (confirm('Reset all changes?')) {
    localStorage.removeItem(STORAGE_KEY);
    state = JSON.parse(JSON.stringify(BOARD_DATA));
    render();
  }
}

function getMember(id) { return (state.team_members || []).find(m => m.id === id) || {name: id, color: '#64748b', initials: '??'}; }

function render() {
  document.getElementById('board-title').textContent = state.board_title || 'PM Board';
  document.getElementById('board-method').textContent = state.methodology || 'Scrum';
  document.getElementById('card-count').textContent = (state.cards || []).length;
  document.getElementById('velocity').textContent = (state.velocity_target || 0) + ' pts';

  const teamBar = document.getElementById('team-bar');
  teamBar.innerHTML = (state.team_members || []).map(m => 
    `<div class="flex items-center gap-2 px-3 py-2 bg-slate-800/50 rounded-lg border border-slate-700">
      <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-black" style="background:${m.color}">${m.initials}</div>
      <div><div class="text-xs font-bold">${m.name}</div><div class="text-[10px] text-slate-400">${m.role}</div></div>
    </div>`).join('');

  const filterSelect = document.getElementById('filter-assignee');
  const currentFilter = filterSelect.value;
  filterSelect.innerHTML = '<option value="">All Members</option>' + (state.team_members || []).map(m => `<option value="${m.id}">${m.name}</option>`).join('');
  filterSelect.value = currentFilter;

  if (state.sprints && state.sprints[0]) {
    const s = state.sprints[0];
    document.getElementById('sprint-info').innerHTML = 
      `<div class="p-4 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl">
        <div class="text-xs opacity-80">CURRENT SPRINT</div>
        <div class="text-lg font-black">${s.name}</div>
        <div class="text-sm opacity-90 mt-1">${s.goal}</div>
      </div>`;
  }

  const board = document.getElementById('board');
  const filter = filterSelect.value;
  board.innerHTML = (state.columns || []).map(col => {
    const cards = (state.cards || []).filter(c => c.column === col.id && (!filter || c.assignee === filter));
    const points = cards.reduce((sum, c) => sum + (c.story_points || 0), 0);
    return `
      <div class="column flex-shrink-0 w-80 bg-slate-800/40 rounded-xl p-4 border border-slate-700" 
           data-column="${col.id}" 
           ondragover="event.preventDefault(); this.classList.add('drag-over');" 
           ondragleave="this.classList.remove('drag-over');" 
           ondrop="handleDrop(event, '${col.id}')">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 rounded-full" style="background:${col.color}"></div>
            <h3 class="font-bold">${col.name}</h3>
            <span class="text-xs text-slate-400">${cards.length}</span>
          </div>
          <span class="text-xs bg-slate-700 px-2 py-1 rounded">${points} pts</span>
        </div>
        <div class="space-y-2">
          ${cards.map(c => {
            const m = getMember(c.assignee);
            return `<div draggable="true" ondragstart="handleDragStart(event, '${c.id}')" ondragend="this.classList.remove('dragging')" 
                        onclick="openCard('${c.id}')"
                        class="card priority-${c.priority || 'P2'} p-3 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700">
              <div class="text-[10px] text-slate-400 font-mono">${c.id}</div>
              <div class="text-sm font-semibold mt-1">${c.title}</div>
              <div class="flex items-center justify-between mt-3">
                <div class="flex gap-1">
                  ${(c.tags || []).slice(0, 2).map(t => `<span class="text-[9px] bg-slate-700 px-2 py-0.5 rounded">${t}</span>`).join('')}
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs bg-indigo-600 px-2 py-0.5 rounded font-bold">${c.story_points || 0}</span>
                  <div class="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-black" style="background:${m.color}" title="${m.name}">${m.initials}</div>
                </div>
              </div>
            </div>`;
          }).join('')}
        </div>
      </div>`;
  }).join('');
}

let draggedId = null;
function handleDragStart(e, id) {
  draggedId = id;
  e.target.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
}
function handleDrop(e, columnId) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  if (!draggedId) return;
  const card = state.cards.find(c => c.id === draggedId);
  if (card) { card.column = columnId; saveState(state); render(); }
  draggedId = null;
}

function openCard(id) {
  const c = state.cards.find(x => x.id === id);
  if (!c) return;
  const m = getMember(c.assignee);
  document.getElementById('modal-content').innerHTML = `
    <div class="text-xs text-slate-400 font-mono">${c.id}</div>
    <h2 class="text-2xl font-black mt-1">${c.title}</h2>
    <p class="text-slate-300 mt-3">${c.description || 'No description'}</p>
    <div class="grid grid-cols-4 gap-3 mt-5">
      <div class="p-3 bg-slate-700/50 rounded-lg"><div class="text-[10px] text-slate-400">PRIORITY</div><div class="font-bold">${c.priority || 'P2'}</div></div>
      <div class="p-3 bg-slate-700/50 rounded-lg"><div class="text-[10px] text-slate-400">POINTS</div><div class="font-bold">${c.story_points || 0}</div></div>
      <div class="p-3 bg-slate-700/50 rounded-lg"><div class="text-[10px] text-slate-400">SPRINT</div><div class="font-bold">${c.sprint || '-'}</div></div>
      <div class="p-3 bg-slate-700/50 rounded-lg"><div class="text-[10px] text-slate-400">ASSIGNEE</div><div class="font-bold">${m.name}</div></div>
    </div>
    ${c.tags && c.tags.length ? `<div class="mt-4 flex gap-2 flex-wrap">${c.tags.map(t => `<span class="text-xs bg-indigo-900/50 px-3 py-1 rounded-full">${t}</span>`).join('')}</div>` : ''}
  `;
  document.getElementById('card-modal').classList.remove('hidden');
}
function closeModal() { document.getElementById('card-modal').classList.add('hidden'); }

document.getElementById('filter-assignee').addEventListener('change', render);
render();
</script>
</body>
</html>"""
    return html

# ============ STAGE 3: PLM EXECUTION ============
def run_plm_execution(idea, pm_plan=None):
    results = []
    context = f"Project Idea: {idea}"
    if pm_plan: context += f"\n\nApproved PM Plan: {json.dumps(pm_plan)[:600]}"
    for phase in PLM_PHASES:
        agent = PLM_AGENTS[phase["agent"]]
        r = smart_call(agent["system"], f"{context}\n\nExecute Phase {phase['id']} ({phase['name']}).")
        parsed = parse_json(r["output"])
        results.append({**phase, "agent_icon": agent["icon"], "agent_role": agent["role"], "data": parsed, "status": "✅"})
        if isinstance(parsed, dict):
            context += f"\n[{phase['name']}]: {str(parsed.get('summary',''))[:150]}"
    return {"idea": idea, "stage": "plm_execution", "phases": results}

def generate_prototype(idea, phases):
    system = "You are a frontend engineer. Output ONLY complete single-file HTML with Tailwind CDN. Build a stunning SaaS landing page with gradient hero, sticky nav, 4 feature cards, testimonials, pricing, CTA footer."
    r = smart_call(system, f"Build for: {idea}", max_tokens=4000)
    html = r["output"].replace("```html","").replace("```","").strip()
    if "<html" not in html.lower():
        html = f"<!DOCTYPE html><html><head><script src='https://cdn.tailwindcss.com'></script></head><body>{html}</body></html>"
    return {"html": html, "provider": r["provider"]}

# ============ HTTP SERVER ============
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
        if path == "/health": self._send(200, {"status": "ok", "version": "10.0", "pm_agents": len(PM_AGENTS), "plm_agents": len(PLM_AGENTS), "features": ["pm_planning", "pm_tool_generator", "plm_execution", "prototype"]})
        else: self._send(200, {"message": "PMGuru Brain v10.0 - Path A"})
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode()) if length else {}
            path = urlparse(self.path).path
            if path == "/pm/plan": self._send(200, run_pm_planning(body.get("idea","")))
            elif path == "/pm/tool": self._send(200, generate_pm_tool(body.get("idea",""), body.get("pm_plan", {})))
            elif path == "/plm/execute": self._send(200, run_plm_execution(body.get("idea",""), body.get("pm_plan")))
            elif path == "/plm/prototype": self._send(200, generate_prototype(body.get("idea",""), body.get("phases",[])))
            else: self._send(404, {"error": "Not found"})
        except Exception as e: self._send(500, {"error": str(e)})
    def log_message(self, fmt, *args): sys.stderr.write(f"{fmt % args}\n"); sys.stderr.flush()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print("="*50, flush=True)
    print("PMGuru Brain v10.0 - Path A: Custom PM Tool Generator", flush=True)
    print(f"Loaded {len(PM_AGENTS)} PM agents + 1 PM Tool Architect + {len(PLM_AGENTS)} PLM agents", flush=True)
    print(f"Binding to 0.0.0.0:{port}", flush=True)
    print("="*50, flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
    print(f"✅ LISTENING on http://0.0.0.0:{port}", flush=True)
