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
- **Dependency Integrity**: A step's `depends_on` array can ONLY contain IDs of other steps that are present in the same plan. Do not list an ID in `depends_on` if that step ID does not exist in the plan you are creating.
- **Step Order**: The `steps` array must be in a valid topological order. A step can only appear in the list if all the other steps it depends on (listed in its `depends_on` field) have already appeared at an earlier index in the array. For example, if an agent step requires data from a tool step to perform its task, the tool step must be listed before the agent step.
- **Step Order**: A step "si" can't depend on a step "sj" if "sj" appears later in the list than "si".
- Keep plan concise and deterministic (i.e., always produce the same plan for the same input; avoid randomness or arbitrary choices).
- Carefully read the agent descriptions and tool's descriptions to understand their capabilities, limitations and requirements.
- You can find every tool's descriptions in the 'related tools' section of each agent in the 'Available agents and their related tools:'.
- Your decision should be solely on descriptions and descriptions only.
- Don't mistake an agent for a tool or tool for an agent.
- If an agent needs a tools output to perform, It is highly likely that it is specifically defined in the agent's description. 
"""
    agents_text_parts = []
    for agent in available_agents:
        agent_info = f"- Agent: {agent.get('name', '')}\n  Description: {agent.get('description', '')}"
        related_tools = agent.get('related_tools', [])
        if related_tools:
            agent_info += "\n  Related Tools:"
            for tool in related_tools:
                agent_info += f"\n    - Name: {tool.get('name', 'N/A')}\n      Description: {tool.get('description', 'N/A')}\n      Expected Params: {tool.get('expected_params', [])}"
        agents_text_parts.append(agent_info)
    agents_text = "\n\n".join(agents_text_parts)

    if not agents_text:
        agents_text = "No available agents."

    prompt = f"""This is the conversation context:
{user_input}

---
Here are the resources you can use to fulfill the CURRENT USER REQUEST:

Available agents and their related tools:
{agents_text}

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