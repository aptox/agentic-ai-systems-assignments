import json
import os
from pathlib import Path

_DIR = Path(__file__).resolve().parent
FILE = str(_DIR / "history.json")


def load_memory():
    if os.path.exists(FILE):
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    history = json.loads(content)
                    if isinstance(history, list):
                        return history, True
        except (json.JSONDecodeError, ValueError):
            pass  # Corrupt file — treat as fresh start
    return [], False  # does not exist or invalid


def save_memory(history):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def reset_memory():
    if os.path.exists(FILE):
        os.remove(FILE)


def history_to_messages(history):
    messages = []

    for item in history:
        messages.append({"role": "user", "content": item["user"]})
        messages.append({"role": "assistant", "content": item["bot"]})

    return messages
