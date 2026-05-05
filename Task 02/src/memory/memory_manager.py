import json
import os

FILE = "memory/history.json"


def load_memory():
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            history = json.load(f)
        return history, True  # exists
    return [], False  # does not exist


def save_memory(history):
    os.makedirs("memory", exist_ok=True)
    with open(FILE, "w") as f:
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