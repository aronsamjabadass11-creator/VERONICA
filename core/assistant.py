"""
assistant.py - Main VERONICA assistant orchestrator.

Coordinates conversation management, tool execution,
agent planning, LLM queries, and voice output.
"""

from typing import Optional, Callable

from config.settings import settings
from config.logging_config import logger

from core.conversation import ConversationManager
from llm.groq_client import GroqClient

from tools.registry import ToolRegistry, default_tool_registry

from voice.text_to_speech import get_tts_engine
from voice.speech_to_text import get_stt_engine

from agent.planner import AgentPlanner
from agent.executor import AgentExecutor
from agent.state import AgentState


class VeronicaAssistant:
    """The central personal AI assistant class."""

    def __init__(
        self,
        conversation_manager: Optional[ConversationManager] = None,
        groq_client: Optional[GroqClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        # ==========================================================
        # CORE SYSTEMS
        # ==========================================================

        self.conversation = (
            conversation_manager or ConversationManager()
        )

        self.client = groq_client or GroqClient()

        self.tools = (
            tool_registry or default_tool_registry
        )

        # ==========================================================
        # VOICE SYSTEMS
        # ==========================================================

        self.tts = get_tts_engine()
        self.stt = get_stt_engine()

        # ==========================================================
        # AGENT SYSTEMS
        # ==========================================================

        self.agent_planner = AgentPlanner(
            self.client
        )

        self.agent_state = AgentState()

        self.agent_executor = AgentExecutor(
            self.client,
            self.tools
        )

        logger.info(
            f"VERONICA initialized with model "
            f"'{self.client.model}'."
        )

    # ==========================================================
    # NORMAL VERONICA PROCESSING
    # ==========================================================

    def process_input(
        self,
        user_input: str,
        on_status_update: Optional[
            Callable[[str], None]
        ] = None,
    ) -> str:
        """
        Processes a single user turn:

        1. Checks for explicit memory requests.
        2. Queries Groq with tool definitions.
        3. Executes tool calls if requested.
        4. Receives and stores final response.
        5. Optionally outputs voice via TTS.
        """

        clean_input = user_input.strip()

        if not clean_input:
            return ""

        # ----------------------------------------------------------
        # Step 1: Direct memory command
        # ----------------------------------------------------------

        lower_input = clean_input.lower()

        if (
            lower_input.startswith("remember that ")
            and len(clean_input) > 14
        ):
            fact_to_remember = clean_input[14:].strip()

            self.conversation.remember(
                fact_to_remember
            )

            self.conversation.add_user_message(
                clean_input
            )

            reply = (
                "Understood. I will remember that: "
                f"{fact_to_remember}."
            )

            self.conversation.add_assistant_message(
                reply
            )

            self._speak(reply)

            return reply

        # ----------------------------------------------------------
        # Step 2: Add user message
        # ----------------------------------------------------------

        self.conversation.add_user_message(
            clean_input
        )

        messages = self.conversation.get_messages()

        if on_status_update:
            on_status_update("Thinking...")

        try:

            # ------------------------------------------------------
            # Step 3: Ask Groq
            # ------------------------------------------------------

            tool_schemas = self.tools.get_schemas()

            response_msg = self.client.chat_completion(
                messages=messages,
                tools=(
                    tool_schemas
                    if tool_schemas
                    else None
                ),
            )

            # ------------------------------------------------------
            # Step 4: Handle tool calls
            # ------------------------------------------------------

            if (
                hasattr(response_msg, "tool_calls")
                and response_msg.tool_calls
            ):

                tool_calls_data = []

                for tc in response_msg.tool_calls:

                    tool_calls_data.append(
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": (
                                    tc.function.arguments
                                ),
                            },
                        }
                    )

                self.conversation.add_raw_message(
                    {
                        "role": "assistant",
                        "content": (
                            response_msg.content or ""
                        ),
                        "tool_calls": tool_calls_data,
                    }
                )

                # --------------------------------------------------
                # Execute requested tools
                # --------------------------------------------------

                for tc in response_msg.tool_calls:

                    tool_name = tc.function.name
                    tool_args = tc.function.arguments

                    if on_status_update:
                        on_status_update(
                            f"Using tool [{tool_name}]..."
                        )

                    logger.info(
                        f"Invoking tool '{tool_name}' "
                        f"with arguments: {tool_args}"
                    )

                    tool_result = (
                        self.tools.execute_tool(
                            tool_name,
                            tool_args
                        )
                    )

                    self.conversation.add_raw_message(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tool_name,
                            "content": tool_result,
                        }
                    )

                # --------------------------------------------------
                # Final LLM response
                # --------------------------------------------------

                if on_status_update:
                    on_status_update(
                        "Synthesizing final response..."
                    )

                final_msg = (
                    self.client.chat_completion(
                        messages=(
                            self.conversation
                            .get_messages()
                        ),
                        tools=None,
                    )
                )

                final_reply = (
                    final_msg.content or ""
                )

                self.conversation.add_assistant_message(
                    final_reply
                )

                self._speak(final_reply)

                return final_reply

            # ------------------------------------------------------
            # Normal text response
            # ------------------------------------------------------

            reply = response_msg.content or ""

            self.conversation.add_assistant_message(
                reply
            )

            self._speak(reply)

            return reply

        except Exception as e:

            err_msg = (
                f"[VERONICA Error: {e}]"
            )

            logger.error(
                f"Error during assistant processing: {e}"
            )

            return err_msg

    # ==========================================================
    # AGENT SYSTEM
    # ==========================================================

    def run_agent(
        self,
        goal: str,
        on_status_update=None
    ) -> str:
        """
        Runs a multi-step VERONICA agent task.

        The agent:
        1. Creates a plan.
        2. Executes the plan.
        3. Collects the results.
        4. Sends the results to Groq.
        5. Generates the actual final answer.
        """

        goal = goal.strip()

        if not goal:
            return "I need a task to execute."

        # ----------------------------------------------------------
        # Reset agent state
        # ----------------------------------------------------------

        self.agent_state.reset(goal)

        if on_status_update:
            on_status_update(
                "Creating agent plan..."
            )

        # ----------------------------------------------------------
        # Create plan
        # ----------------------------------------------------------

        plan = self.agent_planner.create_plan(
            goal
        )

        if not plan:
            return (
                "I couldn't create a plan "
                "for that task."
            )

        self.agent_state.plan = plan

        if on_status_update:
            on_status_update(
                f"Plan created with "
                f"{len(plan)} steps."
            )

        # ----------------------------------------------------------
        # Execute plan
        # ----------------------------------------------------------

        results = (
            self.agent_executor.execute_plan(
                self.agent_state,
                status_callback=on_status_update
            )
        )

        # ----------------------------------------------------------
        # Count completed / failed steps
        # ----------------------------------------------------------

        successful = [
            item
            for item in results
            if item.get("status")
            == "completed"
        ]

        failed = [
            item
            for item in results
            if item.get("status")
            == "failed"
        ]

        # ----------------------------------------------------------
        # Prepare agent results for final LLM
        # ----------------------------------------------------------

        result_text_parts = []

        for index, item in enumerate(
            results,
            start=1
        ):

            step = item.get(
                "step",
                ""
            )

            if item.get("status") == "completed":

                result = item.get(
                    "result",
                    ""
                )

            else:

                result = item.get(
                    "error",
                    ""
                )

            result = str(result)

            # Prevent huge tool results from
            # overwhelming the final LLM request.

            if len(result) > 6000:

                result = (
                    result[:6000]
                    + "\n[Result truncated]"
                )

            result_text_parts.append(
                f"STEP {index}:\n"
                f"{step}\n\n"
                f"RESULT:\n"
                f"{result}"
            )

        collected_results = (
            "\n\n".join(
                result_text_parts
            )
        )

        # ----------------------------------------------------------
        # Generate final answer
        # ----------------------------------------------------------

        if on_status_update:
            on_status_update(
                "Synthesizing final agent answer..."
            )

        final_prompt = f"""
You are VERONICA, an intelligent personal AI assistant.

The user's original goal is:

{goal}

The VERONICA agent executed several steps and collected
the following results:

{collected_results}

Now answer the user's ORIGINAL GOAL.

IMPORTANT RULES:

1. Give the actual answer to the user's goal.
2. Use the information found by the agent.
3. Do not invent information that was not found.
4. If an official webpage was blocked, use another
   successful authoritative source from the results.
5. Do not merely say "Agent task completed".
6. Do not explain the internal agent architecture.
7. Be clear and concise.
8. Use headings, numbered lists, or tables when useful.
9. If some requested information was unavailable,
   clearly mention that limitation.
10. The final response should be useful to the user.

Return ONLY the final answer.
"""

        final_messages = [
            {
                "role": "system",
                "content": (
                    "You are VERONICA's final answer "
                    "generator. Answer the user's original "
                    "goal using the collected agent results."
                ),
            },
            {
                "role": "user",
                "content": final_prompt,
            },
        ]

        # ----------------------------------------------------------
        # Call Groq WITHOUT tools
        # ----------------------------------------------------------

        try:

            final_msg = (
                self.client.chat_completion(
                    messages=final_messages,
                    tools=None,
                )
            )

            final_answer = (
                final_msg.content
                or ""
            )

            if not final_answer.strip():

                final_answer = (
                    "The agent completed the task, "
                    "but Groq returned an empty final answer."
                )

        except Exception as e:

            logger.error(
                "Agent final-answer generation failed: "
                f"{e}"
            )

            # ------------------------------------------------------
            # Fallback answer
            # ------------------------------------------------------

            final_answer = (
                "Agent completed the task.\n\n"
                f"Steps completed: "
                f"{len(successful)}\n"
                f"Steps failed: "
                f"{len(failed)}\n\n"
                "Collected results:\n\n"
                f"{collected_results}"
            )

        # ----------------------------------------------------------
        # Speak final answer
        # ----------------------------------------------------------

        self._speak(final_answer)

        return final_answer

    # ==========================================================
    # VOICE
    # ==========================================================

    def _speak(self, text: str):
        """Helper to invoke TTS if enabled."""

        if self.tts.enabled:
            self.tts.speak(text)

    # ==========================================================
    # STATUS
    # ==========================================================

    def get_status(self) -> dict:
        """Returns the operational status of all subsystems."""

        groq_connected = (
            "CONNECTED"
            if (
                self.client
                and settings.is_api_key_set()
            )
            else "DISCONNECTED"
        )

        memory_status = (
            "READY"
            if settings.MEMORY_ENABLED
            else "DISABLED"
        )

        voice_status = (
            "ON"
            if self.tts.enabled
            else "OFF"
        )

        mic_status = (
            "READY"
            if self.stt.is_microphone_available()
            else "ERROR"
        )

        speaker_status = (
            "READY"
            if self.tts.is_speaker_available()
            else "ERROR"
        )

        return {
            "ai": "ONLINE",

            "groq": groq_connected,

            "model": self.client.model,

            "api_key_set":
                settings.is_api_key_set(),

            "memory": memory_status,

            "memory_enabled":
                settings.MEMORY_ENABLED,

            "voice": voice_status,

            "tts":
                self.tts.get_status(),

            "voice_model":
                getattr(
                    self.tts,
                    "current_voice",
                    settings.TTS_VOICE
                ),

            "speed":
                getattr(
                    self.tts,
                    "current_speed",
                    settings.TTS_SPEED
                ),

            "pitch":
                getattr(
                    self.tts,
                    "current_pitch",
                    settings.TTS_PITCH
                ),

            "microphone":
                mic_status,

            "speaker":
                speaker_status,

            "persistent_facts":
                len(
                    self.conversation
                    .persistent
                    .recall()
                ),

            "tools_registered":
                self.tools.list_tools(),
        }