from guardrails.llm_guardrails import validate_output_llm

def validate_output(output, route_json=None):
    # Rule checks
    if output is None:
        raise ValueError("Empty output")

    if isinstance(output, str) and len(output) > 1000:
        raise ValueError("Output too long")

    # LLM safety check
    if isinstance(output, str):
        is_safe = validate_output_llm(output)
        if not is_safe:
            raise ValueError("Unsafe output detected")

    return True