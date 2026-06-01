"""
ReviewAnalyzerAgent — Aspect-Based Sentiment Analysis (ABSA).

Receives free-form review text and returns a strict JSON object with:
  summary, overall_sentiment, score (1-10), and per-aspect breakdowns.

Handles Israeli slang and sarcasm via prompt-level instructions.
Self-correction (sanity check + second LLM call) is applied in app.py
after the agent returns, before the result is shown to the user.
"""

from pathlib import Path

from agents import Agent

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

review_analyzer_agent = Agent(
    name="ReviewAnalyzerAgent",
    instructions=(_PROMPT_DIR / "review_analyzer_prompt.txt").read_text(encoding="utf-8"),
)
