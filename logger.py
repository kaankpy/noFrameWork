import json
import time
from config import LOG_FILE

def log_event(kind: str, payload: dict):
    # Input:
    #   kind (str) - Log türü (ör: "planner", "executor", "responder")
    #   payload (dict) - Log detayları
    # Purpose:
    #   Olayı JSON Lines formatında log dosyasına yazar.
    # Output:
    #   None
    #pass
    entry = {
        "ts": time.time(),
        "kind": kind,
        "payload": payload
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")