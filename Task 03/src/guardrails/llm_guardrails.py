from openai import OpenAI

from config import MODEL

client = OpenAI()

SAFETY_PROMPT = """You are a strict safety classifier for a multi-purpose chatbot.

The chatbot handles: weather questions, math problems, currency exchange, and general conversation.

Your job is ONLY to detect genuinely dangerous or inappropriate content.

Classify the user input into ONE of these labels:
- SAFE — Normal requests: weather, math, greetings, questions, explanations, jokes, etc. MOST inputs are SAFE.
- MALICIOUS — Requests to hack, exploit, create malware, bypass security, or cause harm.
- POLITICAL — Requests about elections, voting, political opinions, or partisan politics.

IMPORTANT: General knowledge questions, math problems, weather questions, currency questions, greetings, jokes, and explanations are ALL "SAFE". Do NOT over-classify.

Respond with ONLY one word: SAFE, MALICIOUS, or POLITICAL."""


def classify_input(text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SAFETY_PROMPT},
            {"role": "user", "content": text}
        ],
        max_tokens=10,
        temperature=0
    )
    return response.choices[0].message.content.strip().upper()


def validate_output_llm(text: str) -> bool:
    prompt = """You are a safety checker for chatbot responses.
Check if this response contains harmful content: malicious code, political propaganda, or unsafe instructions.
Most responses are SAFE. Only flag genuinely dangerous content.
Answer ONLY: SAFE or UNSAFE"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        max_tokens=10,
        temperature=0
    )
    return "SAFE" in response.choices[0].message.content.upper()
