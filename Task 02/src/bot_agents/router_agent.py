from pathlib import Path

from agents import Agent, handoff

from bot_agents.chat_agent import chat_agent
from bot_agents.exchange_agent import exchange_agent
from bot_agents.math_agent import math_agent
from bot_agents.weather_agent import weather_agent

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

router_agent = Agent(
    name="RouterAgent",
    instructions=(_PROMPT_DIR / "router_prompt.txt").read_text(encoding="utf-8"),

    handoffs=[
        handoff(weather_agent),
        handoff(math_agent),
        handoff(exchange_agent),
        handoff(chat_agent),
    ]
)
