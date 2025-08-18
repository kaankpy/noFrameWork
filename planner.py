import json
import time
from llm_client import chat_completion
from config import PLANNER_MODEL, DEFAULT_TEMPERATURE, MAX_RETRIES, RETRY_BACKOFF_SEC
from logger import log_event


def build_planner_prompt(user_input: str, available_agents: list, available_tools: list):

    orchestrator = {
        "name": "orchestrator_agent",
        "description": "The main agent that coordinates other agents and tools.",
        "system_prompt": """You are the orchestrator agent. Your job is to decide which agents and/or tools should handle the user request, in what order, and with what parameters. 
        Return ONLY strictly valid JSON with this shape and NO extra text, explanation, or formatting:
        {
        "steps": [
            {"id":"s1","type":"agent|tool","name":"...","depends_on": ["s0"]},
            {"id":"s2","type":"agent|tool","name":"...","depends_on": ["s1"]},
            {"id":"s3","type":"agent|tool","name":"...","depends_on": ["s2"]},
            {"id":"s4","type":"agent|tool","name":"...","depends_on": ["s1","s2"]},
            {"id":"s5","type":"agent|tool","name":"...","depends_on": ["s4"]}
        ]
        }
        Notes:
        - You must output ONLY the JSON object as specified above, with no extra text, explanations, or formatting before or after the JSON.

        - Agents may require results from related tools before running.
        - Use `depends_on` to specify if an agent needs outputs from tools or vice versa (e.g., an agent step can depend on tool steps or a tool step can depend on an agent step).
        - Keep plan concise and deterministic (i.e., always produce the same plan for the same input; avoid randomness or arbitrary choices)."""
    }

    system_prompt = orchestrator.get("system_prompt", "")

    agents_text = "\n".join([
    f"- {a.get('name', '')}: {a.get('description', '')} "
    f"related_tools={[t.get('name', '') for t in a.get('related_tools', [])]}"
    for a in available_agents])
    
    if not agents_text:
        agents_text = "No available agents."

    
    tools_text = "\n".join([
    f"- {t['name']}: params={t.get('params',[])} desc={t.get('description','')}"
    for t in available_tools])
    
    if not tools_text:
        tools_text = "No available tools."


    prompt = f"""

Available agents:
{agents_text}

Available tools:
{tools_text}

User request:
{user_input}

"""
    return prompt, system_prompt


def plan_with_retry(user_input: str, available_agents: list, available_tools: list):
    prompt, system_prompt = build_planner_prompt(user_input, available_agents, available_tools)
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}]
    last_exc = None
    
    for attempt in range(1, MAX_RETRIES+1):
        try:
            text = chat_completion(model=PLANNER_MODEL, messages=messages, temperature=DEFAULT_TEMPERATURE)
            plan = json.loads(text)
            if "steps" not in plan or not isinstance(plan["steps"], list):
                raise ValueError("Planner returned JSON missing 'steps' list")
            log_event("planner_ok", {"plan": plan})
            return plan
        except Exception as e:
            last_exc = e
            log_event("planner_error", {"attempt": attempt, "error": str(e)})
            time.sleep(RETRY_BACKOFF_SEC * attempt)
    raise last_exc