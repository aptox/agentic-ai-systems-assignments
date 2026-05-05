import json
import os
from datetime import datetime

class Logger:
    def __init__(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = f"logs/session_{timestamp}.json"
        os.makedirs("logs", exist_ok=True)

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
        with open(self.file_path, "w") as f:
            json.dump(self.logs, f, indent=2)

        with open("logs/latest.json", "w") as f:
            json.dump(self.logs, f, indent=2)