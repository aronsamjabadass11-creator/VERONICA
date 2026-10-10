from agent.planner import AgentPlanner
from agent.state import AgentState
from agent.executor import AgentExecutor
from llm.groq_client import GroqClient
from tools.registry import default_tool_registry


client = GroqClient()

planner = AgentPlanner(client)

state = AgentState()

import sys

if len(sys.argv) > 1:
    goal = " ".join(sys.argv[1:])
else:
    goal = "Search the web for the official Raspberry Pi 4 Model B specifications and summarize them."

print("\nVERONICA AGENT")
print("=" * 50)
print(f"Goal: {goal}\n")

state.reset(goal)

print("Creating plan...\n")

plan = planner.create_plan(goal)

state.plan = plan

for number, step in enumerate(plan, start=1):
    print(f"{number}. {step}")

print("\nExecuting plan...\n")

executor = AgentExecutor(
    client,
    default_tool_registry
)

results = executor.execute_plan(
    state,
    status_callback=lambda msg: print(f"[AGENT] {msg}")
)

print("\n")
print("=" * 50)
print("AGENT RESULTS")
print("=" * 50)

for item in results:
    print(f"\nSTEP: {item['step']}")
    print(f"STATUS: {item['status']}")

    if "result" in item:
        result = str(item["result"])

        # Don't flood the terminal with huge webpage results.
        if len(result) > 1500:
            result = result[:1500] + "\n...[truncated]"

        print(f"RESULT:\n{result}")

    if "error" in item:
        print(f"ERROR: {item['error']}")

print("\nAgent finished.")
print(f"Completed steps: {len(state.completed_steps)}")
print(f"Failed steps: {len(state.failed_steps)}")