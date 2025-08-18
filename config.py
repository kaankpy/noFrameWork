import json
from pathlib import Path

_cfg_path = Path(__file__).parent / "config.json"
if not _cfg_path.exists():
    raise RuntimeError(f"Missing config.json at {_cfg_path}. Create it before running.")

with open(_cfg_path, "r", encoding="utf-8") as f:
    _cfg = json.load(f)

OPENAI_API_KEY = _cfg.get("OPENAI_API_KEY")
OPENAI_API_BASE = _cfg.get("OPENAI_API_BASE")
PLANNER_MODEL = _cfg.get("PLANNER_MODEL")
RESPONDER_MODEL = _cfg.get("RESPONDER_MODEL")
DEFAULT_TEMPERATURE = _cfg.get("DEFAULT_TEMPERATURE", 0.0)
MAX_RETRIES = int(_cfg.get("MAX_RETRIES", 3))
RETRY_BACKOFF_SEC = float(_cfg.get("RETRY_BACKOFF_SEC", 1.5))
LOG_FILE = _cfg.get("LOG_FILE", "agent_system.log.jsonl")
DB_PATH = _cfg.get("DB_PATH", "memory.db")