"""
PMGuru Brain Server — FastAPI backend
Endpoints:
  POST /pipeline/plan       — Step 1: generate plan from idea (for user approval)
  POST /pipeline/execute    — Step 2: execute full 8-phase lifecycle after approval
  POST /pipeline/prototype  — Generate working HTML prototype
  GET  /simulations         — Run pre-deployment simulations
  GET  /memory/stats        — View self-improvement memory stats
  GET  /health              — Health check
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.definitions import AGENTS
from agents.router import smart_route
from graph.workflow import run_workflow, PHASES
from memory.store import MemoryStore, run_simulations

app = FastAPI(title="PMGuru Brain", version="7.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
memory = MemoryStore()


class IdeaIn(BaseModel):
    idea: str


class PrototypeIn(BaseModel):
    idea: str
    phases: list


@app.get("/health")
def health():
    return {"status": "ok", "version": "7.0", "agents": len(AGENTS), "phases": len(PHASES)}


@app.post("/pipeline/plan")
async def generate_plan(body: IdeaIn):
    """Step 1: Strategist generates initial plan for user approval."""
    strategist = AGENTS["Strategist"]
    system = (
        f"{strategist['system_prompt']}\n"
        "You are creating an INITIAL PROJECT PLAN for user approval. "
        "Output: 1) Vision (1 line) 2) Target users 3) Top 5 features 4) Recommended methodology "
        "5) Estimated timeline 6) Team composition. Be concise (max 400 words)."
    )
    result = await smart_route(system, body.idea, task_type="analysis")
    return {
        "idea": body.idea,
        "plan": result["output"],
        "provider": result["provider_used"],
        "phases_preview": [{"id": p["id"], "name": p["name"], "agent": p["agent"], "duration": p["duration"]} for p in PHASES],
        "agents_preview": list(AGENTS.keys()),
    }


@app.post("/pipeline/execute")
async def execute_pipeline(body: IdeaIn):
    """Step 2: After approval, run full 8-phase lifecycle through all agents."""
    result = await run_workflow(body.idea, memory)
    return result


@app.post("/pipeline/prototype")
async def generate_prototype(body: PrototypeIn):
    """Generate a working HTML prototype based on phase outputs."""
    context = "\n".join([f"{p['name']}: {p.get('output', '')[:200]}" for p in body.phases])
    system = (
        "You are a senior frontend engineer. Output ONLY a complete single-file HTML prototype "
        "with Tailwind CDN, inline JS. No markdown, no explanations. "
        "Build a stunning working MVP UI with: hero section, navigation, 3-4 feature cards, "
        "interactive button, gradient colors (indigo/purple/pink), modern design."
    )
    user = f"Build a prototype for: {body.idea}\n\nFeatures from analysis:\n{context}"
    result = await smart_route(system, user, task_type="code", max_tokens=2500)
    html = result["output"].replace("```html", "").replace("```", "").strip()
    return {"html": html, "provider": result["provider_used"]}


@app.get("/simulations")
async def simulations():
    """Run pre-deployment simulations on all agents."""
    return await run_simulations()


@app.get("/memory/stats")
def memory_stats():
    """View self-improvement memory."""
    return memory.get_stats()


@app.get("/agents")
def list_agents():
    """List all agents with their roles and methods."""
    return {name: {"role": a["role"], "goal": a["goal"], "methods": a["methods"], "phases": a["phases"]} for name, a in AGENTS.items()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(__import__("os").getenv("PORT", "8000")))
