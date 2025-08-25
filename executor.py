from llm_client import chat_completion
from memory import save_message, save_tool_output
import importlib
import json
import re
import os
from graphlib import TopologicalSorter, CycleError

AGENTS_DIR = "Agents"

def execute_plan(plan: dict, agents_dir=AGENTS_DIR, user_input=""):
    
    steps = plan.get("steps", [])
    if not steps:
        return {"error": "No steps in the plan to execute."}

    try:
        steps_by_id = {step['id']: step for step in steps}
        dependency_graph = {step['id']: set(step.get('depends_on', [])) for step in steps}
        ts = TopologicalSorter(dependency_graph)

        ts.prepare()

    except KeyError as e:
        return {"error": f"Invalid plan format: {e}"}
    except CycleError as e:
        return {"error": f"Cycle detected: {e}"}

    execution_results = {"initial_request": user_input}

    while ts.is_active():
        ready_steps_group = ts.get_ready()

        for step_id in ready_steps_group:
            step = steps_by_id[step_id]
            step_type = step.get("type")
            step_name = step.get("name", "")
            raw_params = step.get("params", {})
            params = substitute_params(raw_params, execution_results)

            result = None
            if step_type == "agent":
                result = run_agent(step_name, params=params)
                save_message(role="assistant", content=result, meta={"agent": step_name, "step_id": step_id})

            elif step_type == "tool":
                result = run_tool(step_name, params)
                save_tool_output(tool_name=step_name, output=result, meta={"step_id": step_id})
            
            execution_results[step_id] = result
            
            ts.done(step_id)

    return execution_results

def substitute_params(params, results: dict):

    if isinstance(params, dict):
        return {k: substitute_params(v, results) for k, v in params.items()}
    elif isinstance(params, list):
        return [substitute_params(item, results) for item in params]
    elif isinstance(params, str):
        match = re.fullmatch(r"\{([a-zA-Z0-9_]+)\}", params)
        if match:
            step_id = match.group(1)
            return results.get(step_id, params)

        def repl(m):
            step_id = m.group(1)
            return str(results.get(step_id, m.group(0)))

        return re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, params)
    else:
        return params

def load_agent_meta(agent_name, agents_dir=AGENTS_DIR):
    
    path = os.path.join(agents_dir, f"{agent_name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_agent(agent_name: str, params: dict):
    
    agent_meta = load_agent_meta(agent_name)
    user_content = f"Execute the task with the following parameters:\n{json.dumps(params, indent=2)}"
    messages = [{"role": "user", "content": user_content}, {"role": "system", "content": agent_meta["system_prompt"]}]
    response = chat_completion(model=agent_meta["model"], messages=messages, temperature=agent_meta["temperature"])
    return response

def run_tool(tool_name, params):
    
    try:
        module = importlib.import_module(f"Tools.{tool_name}")
        func = getattr(module, tool_name)
        return func(**params)
    except Exception as e:
        return f"Tool {tool_name} error: {e}"