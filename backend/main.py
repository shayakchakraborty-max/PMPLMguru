"""
PMGuru Brain - Pure Python standard library version.
NO FastAPI, NO pydantic, NO Rust compilation.
Works on ANY Python version (3.10, 3.11, 3.12, 3.13, 3.14).
Only uses: http.server (built-in) + httpx (pure Python wheel).
"""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import httpx

# ============ AGENTS ============
AGENTS = {
    "Strategist": {"role": "Senior Product Strategist", "system": "You are a senior product strategist. Output: Vision, 3 OKRs, target persona, top 5 features prioritized by RICE. Be concise (max 300 words)."},
    "Business Analyst": {"role": "Senior Business Analyst", "system": "You are a senior BA. Output: 8 user stories (As a X, I want Y, so that Z) with Given/When/Then acceptance criteria. Max 300 words."},
    "UX Designer": {"role": "Lead UX Designer", "system": "You are a lead UX designer. Output: Information architecture, 5 user flows, wireframe descriptions, design tokens (colors, typography). Max 300 words."},
    "Scrum Master": {"role": "Certified Scrum Master", "system": "You are a Scrum Master. Output: 4-sprint plan with task breakdown, story points, ceremonies, velocity forecast. Max 300 words."},
    "QA Lead": {"role": "Senior QA Lead", "system": "You are a senior QA lead. Output: Test strategy (unit/integration/e2e), test cases for top features, automation framework, quality gates. Max 300 words."},
    "DevOps Engineer": {"role": "Senior DevOps Engineer", "system": "You are a DevOps engineer. Output: CI/CD pipeline stages, infrastructure plan, monitoring stack, rollback strategy, SLOs. Max 300 words."},
    "Risk Manager": {"role": "Risk & Compliance Officer", "system": "You are a risk manager. Output: RAID log with top 8 risks, P×I scores (1-5 each), mitigations, owners. Max 300 words."},
    "Stakeholder Comms": {"role": "Communications Manager", "system": "You are a launch manager. Output: Launch announcement, weekly status template (RAG), stakeholder map, success metrics. Max 300 words."},
}

PHASES = [
    {"id": 1, "name": "Discovery", "agent": "Strategist", "duration": "1-2 weeks", "deliverables": ["Problem statement", "User personas", "Market sizing"]},
    {"id": 2, "name": "Ideation", "agent": "Strategist", "duration": "1 week", "deliverables": ["Solution concepts", "RICE-prioritized features"]},
    {"id": 3, "name": "Definition", "agent": "Business Analyst", "duration": "2 weeks", "deliverables": ["User stories", "Acceptance criteria", "PRD"]},
    {"id": 4, "name": "Design", "agent": "UX Designer", "duration": "2-3 weeks", "deliverables": ["User flows", "Wireframes", "Design system"]},
    {"id": 5, "name": "Development", "agent": "Scrum Master", "duration": "6-12 weeks", "deliverables": ["Sprint plan", "Tasks", "Velocity forecast"]},
    {"id": 6, "name": "Testing", "agent": "QA Lead", "duration": "2 weeks", "deliverables": ["Test strategy", "Test cases", "Quality gates"]},
    {"id": 7, "name": "Launch", "agent": "DevOps Engineer", "duration": "1 week", "deliverables": ["CI/CD", "Infrastructure", "Monitoring"]},
    {"id": 8, "name": "Iterate", "agent": "Stakeholder Comms", "duration": "Ongoing", "deliverables": ["Launch comms", "Status reports", "Metrics"]},
]

# ============ AI ROUTER (Groq + Gemini fallback) ============
def call_groq(system, user, max_tokens=1000):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY not set")
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "max_tokens": max_tokens,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        timeout=60.0,
    )
    return r.json()["choices"][0]["message"]["content"]

def call_gemini(system, user, max_tokens=1000):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
        json={"contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
              "generationConfig": {"maxOutputTokens": max_tokens}},
        timeout=60.0,
    )
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def smart_call(system, user, max_tokens=1000):
    """Try Groq first, fall back to Gemini."""
    try:
        return {"output": call_groq(system, user, max_tokens), "provider": "groq"}
    except Exception as e1:
        try:
            return {"output": call_gemini(system, user, max_tokens), "provider": "gemini"}
        except Exception as e2:
            return {"output": f"Both AI providers failed. Groq: {str(e1)[:100]} | Gemini: {str(e2)[:100]}", "provider": "none"}

# ============ PIPELINE ============
def run_pipeline(idea):
    """Execute all 8 phases sequentially with state passing."""
    results = []
    context = f"Product Idea: {idea}\n"
    for phase in PHASES:
        agent = AGENTS[phase["agent"]]
        system = f"{agent['system']}\nPhase {phase['id']}: {phase['name']}. Deliverables: {', '.join(phase['deliverables'])}."
        user = f"{context}\n\nExecute Phase {phase['id']} ({phase['name']})."
        result = smart_call(system, user)
        results.append({**phase, "output": result["output"], "provider": result["provider"], "status": "✅ Complete"})
        context += f"\n[Phase {phase['id']} {phase['name']}]: {result['output'][:300]}"
    return {"idea": idea, "phases": results, "agents_used": list(set(p["agent"] for p in results))}

def generate_plan(idea):
    """Strategist creates initial plan for approval."""
    system = AGENTS["Strategist"]["system"] + " You are creating an INITIAL PROJECT PLAN. Include: vision, target users, top 5 features, methodology, timeline, team."
    result = smart_call(system, idea, max_tokens=800)
    return {"idea": idea, "plan": result["output"], "provider": result["provider"],
            "phases_preview": [{"id": p["id"], "name": p["name"], "agent": p["agent"], "duration": p["duration"]} for p in PHASES],
            "agents_preview": list(AGENTS.keys())}

def generate_prototype(idea, phases):
    """Generate working HTML prototype."""
    context = "\n".join([f"{p['name']}: {p.get('output', '')[:200]}" for p in phases])
    system = "You are a frontend engineer. Output ONLY a complete single-file HTML prototype with Tailwind CDN, inline JS. No markdown fences, no explanations. Build a stunning MVP UI with hero, navigation, 3-4 feature cards, gradient colors (indigo/purple/pink)."
    user = f"Build prototype for: {idea}\n\nFeatures:\n{context}"
    result = smart_call(system, user, max_tokens=2500)
    html = result["output"].replace("```html", "").replace("```", "").strip()
    return {"html": html, "provider": result["provider"]}

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

    def do_OPTIONS(self):
        self._send(200, {})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, {"status": "ok", "version": "7.1", "agents": len(AGENTS), "phases": len(PHASES)})
        elif path == "/agents":
            self._send(200, {name: {"role": a["role"]} for name, a in AGENTS.items()})
        elif path == "/":
            self._send(200, {"message": "PMGuru Brain v7.1", "endpoints": ["/health", "/agents", "/pipeline/plan (POST)", "/pipeline/execute (POST)", "/pipeline/prototype (POST)"]})
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode()) if length else {}
            path = urlparse(self.path).path
            if path == "/pipeline/plan":
                self._send(200, generate_plan(body.get("idea", "")))
            elif path == "/pipeline/execute":
                self._send(200, run_pipeline(body.get("idea", "")))
            elif path == "/pipeline/prototype":
                self._send(200, generate_prototype(body.get("idea", ""), body.get("phases", [])))
            else:
                self._send(404, {"error": "Not found"})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, format, *args):
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"PMGuru Brain v7.1 starting on port {port}", flush=True)
    print(f"Loaded {len(AGENTS)} agents and {len(PHASES)} phases", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
