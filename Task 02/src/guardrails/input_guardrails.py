from guardrails.llm_guardrails import classify_input


def validate_input(text: str):
    # Rule-based checks (fast)
    if not text or not text.strip():
        raise ValueError("Empty input")

    if len(text) > 500:
        raise ValueError("Input too long")

    # Simple injection patterns
    blocked_patterns = ["ignore previous instructions", "system prompt", "hack"]
    if any(p in text.lower() for p in blocked_patterns):
        raise ValueError("Prompt injection detected")

    # LLM semantic classification
    label = classify_input(text)

    if label == "MALICIOUS":
        raise ValueError("Malicious request detected")

    if label == "POLITICAL":
        raise ValueError("Political content not allowed")

    return True
