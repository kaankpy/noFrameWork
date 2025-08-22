from llm_client import chat_completion
from memory import save_message, save_tool_output
import importlib

AGENTS_DIR = "Agents"

def execute_plan(plan: dict, agents_dir=AGENTS_DIR, user_input=""):

    aggregated_results = {"initial_request": user_input}
    
    for step in plan.get("steps", []):

        if step.get("type") == "agent":
            agent_name = step.get("name", "")
            response = run_agent(agent_name, aggregated_results=str(aggregated_results))
            aggregated_results[agent_name] = response
            save_message(role="assistant", content=response, meta={"agent": agent_name})

        elif step.get("type") == "tool":
            tool_name = step.get("name", "")
            params = step.get("params", {})
            response = run_tool(tool_name, params)
            aggregated_results[tool_name] = response
            save_tool_output(tool_name, response)

    return aggregated_results


def load_agent_meta(agent_name, AGENTS_DIR = "Agents"):
    import os, json
    path = os.path.join(AGENTS_DIR, f"{agent_name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_agent(agent_name, aggregated_results):
    agent_meta = load_agent_meta(agent_name)
    messages = [{"role": "user", "content": aggregated_results}, {"role": "system", "content": agent_meta["system_prompt"]}]
    response = chat_completion(model=agent_meta["model"], messages=messages, temperature=agent_meta["temperature"])
    return response

def run_tool(tool_name, params):
    try:
        module = importlib.import_module(f"Tools.{tool_name}")
        func = getattr(module, tool_name)
        return func(**params)
    except Exception as e:
        return f"Tool {tool_name} error: {e}"
