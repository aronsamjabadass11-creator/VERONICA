"""
executor.py - Executes VERONICA agent plans using registered tools.
"""

import json
from agent.state import AgentState


class AgentExecutor:
    """Executes agent steps using VERONICA's registered tools."""

    def __init__(self, client, tools):
        self.client = client
        self.tools = tools

    def execute_plan(self, state: AgentState, status_callback=None):
        results = []

        while state.has_next_step():

            step = state.next_step()

            if status_callback:
                status_callback(f"Agent step: {step}")

            try:
                result = self._execute_step(
                    step,
                    state.goal,
                    results,
                    status_callback
                )

                results.append({
                    "step": step,
                    "result": result,
                    "status": "completed",
                })

                state.mark_completed()

            except Exception as e:

                results.append({
                    "step": step,
                    "error": str(e),
                    "status": "failed",
                })

                state.mark_failed()

                if status_callback:
                    status_callback(
                        f"Agent step failed: {step}"
                    )

        return results

    def _execute_step(
        self,
        step,
        goal,
        previous_results=None,
        status_callback=None
    ):
        """
        Execute one agent step.
        """

        previous_results = previous_results or []

        tool_schemas = self.tools.get_schemas()

        # ---------------------------------------------------------
        # Build compact context
        # ---------------------------------------------------------

        context_parts = []

        for item in previous_results[-3:]:

            result = item.get("result", "")

            if not result:
                continue

            result = str(result)

            if len(result) > 5000:
                result = (
                    result[:5000]
                    + "\n[previous result truncated]"
                )

            context_parts.append(
                f"STEP: {item.get('step', '')}\n"
                f"RESULT:\n{result}"
            )

        previous_context = "\n\n".join(context_parts)

        # ---------------------------------------------------------
        # Agent instructions
        # ---------------------------------------------------------

        system_prompt = """
You are VERONICA's execution engine.

Your job is to complete ONE current agent step.

IMPORTANT RULES:

1. Use an available tool when the step requires one.
2. Never invent a tool.
3. Prefer the most appropriate tool.
4. If previous results already contain the required information,
   use them instead of unnecessarily repeating the request.
5. If a webpage is blocked, use another available source.
6. Prefer authoritative sources and official documentation.
7. Keep tool requests focused.
8. Do not dump huge webpages into the conversation.
9. Never claim an action succeeded unless the tool actually succeeded.
"""

        user_prompt = (
            f"OVERALL GOAL:\n{goal}\n\n"
            f"CURRENT STEP:\n{step}\n\n"
            f"PREVIOUS RESULTS:\n"
            f"{previous_context if previous_context else '(none)'}"
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        # ---------------------------------------------------------
        # Ask Groq what to do
        # ---------------------------------------------------------

        response = self.client.chat_completion(
            messages=messages,
            tools=tool_schemas if tool_schemas else None,
        )

        tool_calls = getattr(response, "tool_calls", None)

        # ---------------------------------------------------------
        # No tool required
        # ---------------------------------------------------------

        if not tool_calls:
            return response.content or "Step completed."

        tool_results = []

        # ---------------------------------------------------------
        # Execute selected tools
        # ---------------------------------------------------------

        for tool_call in tool_calls:

            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            if status_callback:
                status_callback(
                    f"Using tool [{tool_name}]..."
                )

            tool = self.tools.get_tool(tool_name)

            if not tool:
                tool_results.append(
                    f"Unknown tool: {tool_name}"
                )
                continue

            if isinstance(arguments, str):

                try:
                    arguments = json.loads(arguments)

                except json.JSONDecodeError:
                    arguments = {}

            if not isinstance(arguments, dict):
                arguments = {}

            result = self.tools.execute_tool(
                tool_name,
                arguments
            )

            result = str(result)

            if len(result) > 18000:
                result = (
                    result[:18000]
                    + "\n[Tool result truncated by VERONICA]"
                )

            tool_results.append(
                f"{tool_name}:\n{result}"
            )

        # ---------------------------------------------------------
        # Return tool results
        # ---------------------------------------------------------

        return "\n\n".join(tool_results)

    # =============================================================
    # FINAL AGENT ANSWER
    # =============================================================

    def synthesize_final_answer(
        self,
        state: AgentState,
        results,
    ):
        """
        Convert all completed agent-step results into one
        concise final answer for the user.
        """

        result_parts = []

        for item in results:

            if item.get("status") != "completed":
                continue

            result = item.get("result", "")

            if not result:
                continue

            result_parts.append(
                f"STEP:\n{item.get('step', '')}\n\n"
                f"RESULT:\n{result}"
            )

        collected_results = "\n\n---\n\n".join(result_parts)

        if len(collected_results) > 30000:
            collected_results = (
                collected_results[:30000]
                + "\n[agent results truncated]"
            )

        messages = [
            {
                "role": "system",
                "content": """
You are VERONICA's final answer generator.

The agent has completed its planned steps.

Create the final answer for the user.

Rules:
1. Answer the original goal directly.
2. Use only information supported by the completed agent results.
3. Do not mention internal agent steps unless useful.
4. Do not mention tool names.
5. Do not invent missing information.
6. Keep the answer clear and easy to read.
7. Use bullets or a table when helpful.
8. If the task asks for a summary, provide the summary directly.
""",
            },
            {
                "role": "user",
                "content": (
                    f"ORIGINAL GOAL:\n{state.goal}\n\n"
                    f"COMPLETED AGENT RESULTS:\n"
                    f"{collected_results}"
                ),
            },
        ]

        response = self.client.chat_completion(
            messages=messages,
            tools=None,
        )

        return response.content or "Unable to generate final answer."