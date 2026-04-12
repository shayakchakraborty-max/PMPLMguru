"""
LangGraph-style orchestrator for the 8-phase product lifecycle.
State machine: each phase = node, edges = sequential dependencies.
Memory persists across phases (each agent sees previous outputs).
Self-improvement: after each run, performance metrics are logged.
"""
from typing import Dict, List
from agents.definitions import AGENTS
from agents.router import smart_route
from memory.store import MemoryStore

# 8 product lifecycle phases — each is a node in the graph
PHASES = [
    {"id": 1, "name": "Discovery", "agent": "Strategist", "duration": "1-2 weeks", "task_type": "analysis",
     "deliverables": ["Problem statement", "User personas", "Market sizing"]},
    {"id": 2, "name": "Ideation", "agent": "Strategist", "duration": "1 week", "task_type": "creative",
     "deliverables": ["Solution concepts", "RICE-prioritized features"]},
    {"id": 3, "name": "Definition", "agent": "Business Analyst", "duration": "2 weeks", "task_type": "structured",
     "deliverables": ["User stories", "Acceptance criteria", "PRD"]},
    {"id": 4, "name": "Design", "agent": "UX Designer", "duration": "2-3 weeks", "task_type": "creative",
     "deliverables": ["User flows", "Wireframes", "Design system"]},
    {"id": 5, "name": "Development", "agent": "Scrum Master", "duration": "6-12 weeks", "task_type": "structured",
     "deliverables": ["Sprint plan", "Task breakdown", "Velocity forecast"]},
    {"id": 6, "name": "Testing", "agent": "QA Lead", "duration": "2 weeks", "task_type": "structured",
     "deliverables": ["Test strategy", "Test cases", "Quality gates"]},
    {"id": 7, "name": "Launch", "agent": "DevOps Engineer", "duration": "1 week", "task_type": "structured",
     "deliverables": ["CI/CD pipeline", "Infrastructure", "Monitoring"]},
    {"id": 8, "name": "Iterate", "agent": "Stakeholder Comms", "duration": "Ongoing", "task_type": "creative",
     "deliverables": ["Launch comms", "Status reports", "Metrics dashboard"]},
]


class WorkflowState:
    """LangGraph-style state object that flows through nodes."""
    def __init__(self, idea: str):
        self.idea = idea
        self.phases_completed: List[Dict] = []
        self.context = f"Product Idea: {idea}\n"
        self.metrics = {"start": None, "end": None, "providers_used": [], "tokens": 0}


async def execute_phase(state: WorkflowState, phase: Dict, memory: MemoryStore) -> Dict:
    """Execute a single phase node — calls the assigned agent with smart routing."""
    agent = AGENTS[phase["agent"]]
    # Pull self-improvement hints from memory (lessons from previous runs)
    lessons = memory.get_lessons(phase["agent"])
    lesson_text = f"\nLessons from previous runs: {lessons}" if lessons else ""

    system = (
        f"{agent['system_prompt']}\n"
        f"Role: {agent['role']}\n"
        f"Goal: {agent['goal']}\n"
        f"Methods: {', '.join(agent['methods'])}\n"
        f"Phase: {phase['id']} - {phase['name']}\n"
        f"Required deliverables: {', '.join(phase['deliverables'])}"
        f"{lesson_text}\n"
        f"Be concise (max 300 words). Use bullet points and clear structure."
    )
    user = f"{state.context}\n\nExecute Phase {phase['id']} ({phase['name']}). Produce: {', '.join(phase['deliverables'])}."

    result = await smart_route(system, user, task_type=phase["task_type"], max_tokens=1200)
    output = result["output"]

    state.context += f"\n\n[Phase {phase['id']} {phase['name']} by {phase['agent']}]: {output[:400]}"
    state.metrics["providers_used"].append(result["provider_used"])

    return {**phase, "output": output, "provider": result["provider_used"], "status": "✅ Complete"}


async def run_workflow(idea: str, memory: MemoryStore) -> Dict:
    """LangGraph-style orchestration: sequential execution with state passing."""
    import datetime
    state = WorkflowState(idea)
    state.metrics["start"] = datetime.datetime.utcnow().isoformat()

    for phase in PHASES:
        result = await execute_phase(state, phase, memory)
        state.phases_completed.append(result)

    state.metrics["end"] = datetime.datetime.utcnow().isoformat()
    # Self-improvement: log this run for future learning
    memory.log_run(idea, state.phases_completed, state.metrics)

    return {
        "idea": idea,
        "phases": state.phases_completed,
        "metrics": state.metrics,
        "agents_used": list(set(p["agent"] for p in state.phases_completed)),
    }
