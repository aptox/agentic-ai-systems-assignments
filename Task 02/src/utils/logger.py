import json
from datetime import datetime
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent
_LOGS_DIR = _SRC_DIR / "logs"


class Logger:
    def __init__(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _LOGS_DIR.mkdir(exist_ok=True)
        self.file_path = str(_LOGS_DIR / f"session_{timestamp}.json")

        self.logs = {
            "session_start": timestamp,
            "events": []
        }

    def log(self, event_type, data):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        self.logs["events"].append(entry)

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2)

        with open(str(_LOGS_DIR / "latest.json"), "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2)
