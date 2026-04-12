"""
Self-improving memory store.
After each run, agents log their performance and lessons learned.
Future runs pull these lessons into the system prompt automatically.
Backed by JSON file (or Supabase in production).
"""
import json
import os
from typing import List, Dict
from pathlib import Path

MEMORY_FILE = Path(os.getenv("MEMORY_FILE", "/tmp/pmguru_memory.json"))


class MemoryStore:
    def __init__(self):
        self.data = self._load()

    def _load(self) -> Dict:
        if MEMORY_FILE.exists():
            try:
                return json.loads(MEMORY_FILE.read_text())
            except:
                pass
        return {"runs": [], "lessons_by_agent": {}}

    def _save(self):
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text(json.dumps(self.data, indent=2))

    def log_run(self, idea: str, phases: List[Dict], metrics: Dict):
        """Log a complete run for future learning."""
        self.data["runs"].append({
            "idea": idea[:200],
            "phase_count": len(phases),
            "agents": list(set(p["agent"] for p in phases)),
            "metrics": metrics,
        })
        # Keep last 50 runs
        self.data["runs"] = self.data["runs"][-50:]
        self._save()

    def add_lesson(self, agent: str, lesson: str):
        """Add a lesson for self-improvement."""
        if agent not in self.data["lessons_by_agent"]:
            self.data["lessons_by_agent"][agent] = []
        self.data["lessons_by_agent"][agent].append(lesson)
        self.data["lessons_by_agent"][agent] = self.data["lessons_by_agent"][agent][-5:]
        self._save()

    def get_lessons(self, agent: str) -> str:
        """Retrieve recent lessons for an agent."""
        lessons = self.data["lessons_by_agent"].get(agent, [])
        return "; ".join(lessons[-3:]) if lessons else ""

    def get_stats(self) -> Dict:
        return {
            "total_runs": len(self.data["runs"]),
            "agents_with_lessons": len(self.data["lessons_by_agent"]),
            "recent_runs": self.data["runs"][-5:],
        }


# === SIMULATION RUNNER ===
async def run_simulations() -> Dict:
    """Run pre-deployment simulations on all agents to verify they work."""
    from agents.definitions import AGENTS, SIMULATIONS
    from agents.router import smart_route

    results = {}
    for agent_name, sims in SIMULATIONS.items():
        agent = AGENTS[agent_name]
        agent_results = []
        for sim in sims:
            try:
                r = await smart_route(
                    system=agent["system_prompt"],
                    user=sim["input"],
                    task_type="default",
                    max_tokens=300,
                )
                output_lower = r["output"].lower()
                passed = all(kw.lower() in output_lower for kw in sim["expects"])
                agent_results.append({
                    "input": sim["input"],
                    "passed": passed,
                    "provider": r["provider_used"],
                })
            except Exception as e:
                agent_results.append({"input": sim["input"], "passed": False, "error": str(e)[:100]})
        results[agent_name] = {
            "passed": sum(1 for r in agent_results if r.get("passed")),
            "total": len(agent_results),
            "details": agent_results,
        }
    return results
