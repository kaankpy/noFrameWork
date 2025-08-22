import os
import json
import importlib.util
from typing import Dict, List

AGENTS_DIR = "Agents"
TOOLS_DIR = "Tools"


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
    if not os.path.isdir(TOOLS_DIR):
        return tools

    for filename in os.listdir(TOOLS_DIR):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = os.path.splitext(filename)[0]
            module_path = os.path.join(TOOLS_DIR, filename)
            try:
                spec = importlib.util.spec_from_file_location(f"Tools.{module_name}", module_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "get_info") and callable(getattr(module, "get_info")):
                        tool_info = module.get_info()
                        tools.append(tool_info)
            except Exception as e:
                print(f"Warning: Could not load or inspect tool '{filename}'. Error: {e}")

    return tools
