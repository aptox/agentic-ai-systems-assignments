from openai import OpenAI
from config import MODEL

client = OpenAI()

SAFETY_PROMPT = """
You are a strict safety classifier.

Classify the input into:
- SAFE
- MALICIOUS
- POLITICAL
- IRRELEVANT

Respond ONLY with one label.
"""

def classify_input(text: str) -> str:
    response = client.responses.create(
        model=MODEL,
        input=SAFETY_PROMPT + f"\nInput: {text}"
    )
    return response.output_text.strip()


def validate_output_llm(text: str) -> bool:
    prompt = f"""
Check if this response violates safety rules (malicious, political, unsafe).

Answer ONLY: SAFE or UNSAFE

Response: {text}
"""
    response = client.responses.create(
        model=MODEL,
        input=prompt
    )
    return "SAFE" in response.output_text