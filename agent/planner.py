"""
planner.py - Planning engine for VERONICA.
"""

import json
from typing import List


class AgentPlanner:
    """Creates multi-step plans using VERONICA's LLM."""

    def __init__(self, client):
        self.client = client

    def create_plan(self, goal: str) -> List[str]:
        goal = goal.strip()

        if not goal:
            return []

        prompt = f"""
You are VERONICA's task planner.

User goal:
{goal}

Break this goal into a small number of clear, safe steps.

Rules:
- Use only the tools available to VERONICA.
- Do not invent tools.
- Keep steps practical and sequential.
- Do not perform actions yourself.
- Return ONLY a JSON array of strings.

Example:
[
  "Search the web for the requested information",
  "Read the most relevant webpage",
  "Extract the important information",
  "Prepare a concise answer"
]
"""

        response = self.client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise task-planning engine."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = (response.content or "").strip()

        try:
            plan = json.loads(content)

            if isinstance(plan, list):
                return [str(step) for step in plan]

        except json.JSONDecodeError:
            pass

        # Safe fallback if the model does not return valid JSON.
        return [
            f"Understand the goal: {goal}",
            "Determine the required VERONICA tools",
            "Execute the required actions",
            "Verify the results",
            "Prepare the final response",
        ]