from pathlib import Path

from agents import Agent

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

chat_agent = Agent(
    name="ChatAgent",
    instructions=(_PROMPT_DIR / "chat_prompt.txt").read_text(encoding="utf-8"),
)
