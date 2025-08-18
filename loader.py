import os
import json
from typing import Dict, List

AGENTS_DIR = "Agents"
TOOLS_DIR = "tools"


def load_agents() -> Dict[str, dict]:
    agents = {}
    for filename in os.listdir(AGENTS_DIR):
        if filename.endswith(".json"):
            path = os.path.join(AGENTS_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
                agent_name = os.path.splitext(filename)[0]
                agents[agent_name] = config
    return agents


def discover_tools() -> List[dict]:
    tools = []
    for filename in os.listdir(TOOLS_DIR):
        if filename.endswith(".py"):
            tools.append({
                "name": os.path.splitext(filename)[0],
                "path": os.path.join(TOOLS_DIR, filename)
            })
    return tools
