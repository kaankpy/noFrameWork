import json
import time
from llm_client import chat_completion
from config import PLANNER_MODEL, DEFAULT_TEMPERATURE, MAX_RETRIES, RETRY_BACKOFF_SEC
from logger import log_event


def build_planner_prompt(user_input: str, available_agents: list, available_tools: list):
    system_prompt = """You are a master planner AI. Your job is to create a step-by-step plan to fulfill the user's request using a set of available agents and tools.
You must respond with ONLY a valid JSON object. Do not include any other text, explanations, or markdown formatting.

Your output JSON must have this structure:
{
  "steps": [
    {
      "id": "s1",
      "type": "tool",
      "name": "tool_name",
      "params": { "param_name": "value" }
    },
    {
      "id": "s2",
      "type": "agent",
      "name": "agent_name",
      "params": { "input_data": "{s1}" },
      "depends_on": ["s1"]
    }
  ]
}

**PLANNING RULES:**
1.  **Simple Conversation**: For simple greetings or conversational remarks (e.g., "hello", "thank you"), return an empty plan: `{"steps": []}`.
2.  **Data Flow with Placeholders**: To use the output of one step as an input for another, use a placeholder in the `params` value. The format is `{source_step_id}`. The executor will replace this with the actual result.
3.  **Dependencies (`depends_on`)**: If a step's `params` use a placeholder like `{step_A}`, you MUST add `"step_A"` to that step's `depends_on` array.
4.  **Parameters (`params`)**:
    - For `tool` steps, provide the parameters specified in the tool's `Expected Params`.
    - For `agent` steps, construct a `params` object that provides the necessary context for the agent to perform its task. This can include static text or placeholders from other steps.
5.  **Step `id`**: Use simple, sequential, and unique IDs for each step, like `"s1"`, `"s2"`, `"s3"`, etc. This makes creating dependencies easier.
6.  **Execution Order**: The order of steps in the `steps` array does NOT matter. The `executor` will determine the correct order from the `depends_on` field. Focus only on defining the dependencies correctly.
7.  **Resource Analysis**: Carefully analyze the provided agent and tool descriptions to create the most logical and efficient plan.
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