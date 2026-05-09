"""
ClassifierAgent — produces SDK-native structured output (Part B).

Uses output_type=RouteOutput to force the LLM to return a validated
Pydantic object with {intent, parameters, confidence} before the
RouterAgent performs the actual handoff.
"""

from pathlib import Path

from agents import Agent
from agents.agent_output import AgentOutputSchema

from bot_agents.schemas import RouteOutput

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

classifier_agent = Agent(
    name="ClassifierAgent",
    instructions=(_PROMPT_DIR / "classifier_prompt.txt").read_text(encoding="utf-8"),
    output_type=AgentOutputSchema(RouteOutput, strict_json_schema=False),
)
