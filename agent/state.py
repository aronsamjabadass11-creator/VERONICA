"""
state.py - Runtime state and shared context for VERONICA's agent.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class AgentState:
    goal: str = ""
    plan: List[str] = field(default_factory=list)
    current_step: int = 0

    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)

    # Stores the output of every completed tool/agent step.
    step_results: List[Dict[str, str]] = field(default_factory=list)

    # Shared context that can be passed to later steps.
    context: str = ""

    def reset(self, goal: str):
        self.goal = goal
        self.plan = []
        self.current_step = 0
        self.completed_steps = []
        self.failed_steps = []
        self.step_results = []
        self.context = ""

    def has_next_step(self) -> bool:
        return self.current_step < len(self.plan)

    def next_step(self) -> str:
        if not self.has_next_step():
            return ""

        return self.plan[self.current_step]

    def add_result(self, step: str, result: str):
        self.step_results.append({
            "step": step,
            "result": result,
        })

        self._rebuild_context()

    def _rebuild_context(self):
        """
        Builds a compact shared context from previous steps.
        """

        parts = []

        for item in self.step_results:
            step = item.get("step", "")
            result = item.get("result", "")

            if not result:
                continue

            parts.append(
                f"STEP: {step}\n"
                f"RESULT:\n{result}"
            )

        context = "\n\n".join(parts)

        # Prevent context from growing indefinitely.
        self.context = context[-12000:]

    def mark_completed(self):
        if self.has_next_step():
            self.completed_steps.append(
                self.plan[self.current_step]
            )
            self.current_step += 1

    def mark_failed(self):
        if self.has_next_step():
            self.failed_steps.append(
                self.plan[self.current_step]
            )
            self.current_step += 1