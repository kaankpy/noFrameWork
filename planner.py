import json
import time
from llm_client import chat_completion
from config import PLANNER_MODEL, DEFAULT_TEMPERATURE, MAX_RETRIES, RETRY_BACKOFF_SEC
from logger import log_event


def build_planner_prompt(agent_meta: dict, user_input: str, available_agents: list, available_tools: list):
    """Constructs a prompt that asks the planner (orchestrator) which agents/tools to run.
    The prompt requests STRICT JSON output with a `steps` array. Each step is either an `agent` or `tool`.
    Example step:
      {"id":"s1","type":"agent","name":"WeatherAgent","params":{"city":"Istanbul"}}
    """
    system = agent_meta.get("system_prompt", "")
    agents_text = "\n".join([f"- {a['name']}: {a.get('description','')} params={a.get('expected_params',[])}" for a in available_agents])
    tools_text = "\n".join([f"- {t['name']}: params={t.get('params',[])} desc={t.get('description','')}" for t in available_tools])

    prompt = f"""
System: {system}

Available agents:
{agents_text}

Available tools:
{tools_text}

User request:
{user_input}

Return ONLY valid JSON with this shape:
{{
  "steps": [
    {{"id":"s1","type":"agent|tool","name":"...","params":{{...}}, "depends_on": ["s0"]}}
  ]
}}

Notes:
- Use `agent` steps to call other agents. Use `tool` steps to call low-level tools.
- Provide explicit `depends_on` for steps that need outputs from previous steps.
- Keep plan concise and deterministic.
"""
    return prompt


def plan_with_retry(agent_meta: dict, user_input: str, available_agents: list, available_tools: list):
    prompt = build_planner_prompt(agent_meta, user_input, available_agents, available_tools)
    messages = [{"role": "system", "content": agent_meta.get("system_prompt", "")},
                {"role": "user", "content": prompt}]
    last_exc = None
    for attempt in range(1, MAX_RETRIES+1):
        try:
            text = chat_completion(model=PLANNER_MODEL, messages=messages, temperature=agent_meta.get("temperature", DEFAULT_TEMPERATURE))
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