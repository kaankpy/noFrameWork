import json
import time
from config import LOG_FILE

def log_event(kind: str, payload: dict):
    entry = {
        "ts": time.time(),
        "kind": kind,
        "payload": payload
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")