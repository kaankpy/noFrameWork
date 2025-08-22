import json
import time
from llm_client import chat_completion
from config import PLANNER_MODEL, DEFAULT_TEMPERATURE, MAX_RETRIES, RETRY_BACKOFF_SEC
from logger import log_event


def build_planner_prompt(user_input: str, available_agents: list, available_tools: list):
    system_prompt = """You are the orchestrator agent. Your job is to decide which agents and/or tools should handle the user request, in what order, and with what parameters.
Your primary focus is the 'CURRENT USER REQUEST' section of the user's message.
Return ONLY strictly valid JSON with this shape and NO extra text, explanation, or formatting:
{
"steps": [
    {"id":"s1","type":"agent|tool","name":"...","depends_on": []},
    {"id":"s2","type":"agent|tool","name":"...","depends_on": ["s1"]},
    {"id":"s3","type":"agent|tool","name":"...","depends_on": ["s2"]},
    {"id":"s4","type":"agent|tool","name":"...","depends_on": ["s1","s2"]},
    {"id":"s5","type":"agent|tool","name":"...","depends_on": ["s4"]}
]
}
Notes:
- If the 'CURRENT USER REQUEST' is a simple greeting, question, or conversational remark (e.g., "hello", "how are you?", "thank you") that does not require any tools or information gathering, return an empty plan: `{"steps": []}`.
- You must output ONLY the JSON object as specified above, with no extra text, explanations, or formatting.
- Review the 'PREVIOUSLY GATHERED INFORMATION' section in the conversation context. If a tool was called before for a similar request and its output is unlikely to have changed (e.g., OS version), do NOT include that tool in the plan again. The previous results are available to subsequent agents.
- **Dependency Rule**: Steps can depend on each other. For example, an agent might need data from a tool, or a tool might need data from an agent. If a step requires data from another, you must create a separate step for each. The step that needs the data must list the `id` of the step that provides it in its `depends_on` array. Every `id` listed in a `depends_on` array MUST correspond to another step's `id` within the same plan.
- **Tool Parameters**: When adding a `tool` step, check its definition for required parameters. If so, add a `params` dictionary to the step. The values for these parameters should be filled if they are static or can be taken directly from the user's request. The agent descriptions may provide hints on which tools to use and what parameters they expect (`related_tools`, `expected_params`).
- **Step Order**: The `steps` array should be logically ordered. If a step `s2` depends on `s1`, then `s1` should appear before `s2` in the array.
- Keep plan concise and deterministic (i.e., always produce the same plan for the same input; avoid randomness or arbitrary choices)."""

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


    prompt = f"""This is the conversation context:
{user_input}

---
Here are the resources you can use to fulfill the CURRENT USER REQUEST:

Available agents:
{agents_text}

Available tools:
{tools_text}
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