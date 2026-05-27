"""
Self-Correction / Refinement layer for review analysis output.

After ReviewAnalyzerAgent returns JSON, sanity_check() detects internal
contradictions (e.g. Positive sentiment with score=2). If one is found,
correct_review_async() makes a second LLM call with a targeted fix prompt
and returns the corrected JSON string.
"""

import json

from agents import Agent, Runner


# ── Contradiction rules ──────────────────────────────────────────────────────

_SENTIMENT_SCORE_RULES = {
    "Positive": (7, 10),
    "Negative": (1, 4),
    "Neutral":  (4, 6),
    "Mixed":    (3, 8),
}


def sanity_check(review_dict: dict) -> str | None:
    """
    Check for internal contradictions in a ReviewOutput dict.

    Returns a human-readable description of the contradiction if one exists,
    or None if the output is internally consistent.
    """
    sentiment = review_dict.get("overall_sentiment", "")
    score = review_dict.get("score")

    if sentiment not in _SENTIMENT_SCORE_RULES or score is None:
        return None

    low, high = _SENTIMENT_SCORE_RULES[sentiment]
    if not (low <= score <= high):
        return (
            f"overall_sentiment is '{sentiment}' but score is {score}. "
            f"Expected score in range {low}–{high} for {sentiment} sentiment."
        )

    aspects = review_dict.get("aspects", [])
    if not aspects:
        return None

    pos = sum(1 for a in aspects if a.get("sentiment") == "Positive")
    neg = sum(1 for a in aspects if a.get("sentiment") == "Negative")

    if sentiment == "Positive" and neg > pos:
        return (
            f"overall_sentiment is 'Positive' but {neg} of {len(aspects)} aspects are Negative. "
            "Consider Mixed or Negative."
        )
    if sentiment == "Negative" and pos > neg:
        return (
            f"overall_sentiment is 'Negative' but {pos} of {len(aspects)} aspects are Positive. "
            "Consider Mixed or Positive."
        )

    return None


# ── Correction agent ─────────────────────────────────────────────────────────

_CORRECTION_INSTRUCTIONS = """\
You are a JSON correction engine. You will receive:
1. An original review text.
2. A JSON analysis that contains an internal contradiction.
3. A description of the contradiction.

Your task: return ONLY a corrected, valid JSON object that fixes the contradiction \
while staying faithful to the original review. Do not add new aspects. \
Do not output any text outside the JSON object.
"""

_correction_agent = Agent(
    name="CorrectionAgent",
    instructions=_CORRECTION_INSTRUCTIONS,
)


async def correct_review_async(
    original_text: str,
    inconsistent_json: str,
    contradiction: str,
) -> str:
    """
    Make a second LLM call to fix a contradictory review JSON.

    Returns the corrected JSON string, or the original if correction fails.
    """
    prompt = (
        f"Original review:\n{original_text}\n\n"
        f"Current JSON output (contains a contradiction):\n{inconsistent_json}\n\n"
        f"Contradiction detected: {contradiction}\n\n"
        "Please fix this inconsistency. Return corrected JSON only."
    )
    try:
        result = await Runner.run(_correction_agent, input=prompt)
        corrected_text = result.final_output.strip()
        # Validate that the result is parseable JSON before returning
        json.loads(corrected_text)
        return corrected_text
    except Exception:
        # If correction fails for any reason, return the original unchanged
        return inconsistent_json
