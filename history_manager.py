from config import MAX_HISTORY_WINDOW
import json
from logger import log_event

def summarize_conversation_history(history_turns: list):
    if not history_turns:
        return ""

    first_turn = history_turns[0]
    summary = (
        f"Conversation started with user asking: '{first_turn['user_input']}'. "
        f"Assistant's initial response was: '{first_turn['response']}'."
    )
    
    if len(history_turns) > 1:
        omitted_count = len(history_turns) - 1
        summary += f"\n... ({omitted_count} older turn(s) omitted for brevity) ..."

    log_event(
        "history_summarized", 
        {"summary": summary, "turns_summarized": len(history_turns), "method": "truncation"}
    )
    return summary

def build_context_for_planner(conversation_history: list, current_user_input: str):
    context_summary = ""
    if len(conversation_history) > MAX_HISTORY_WINDOW:
        turns_to_summarize = conversation_history[:-MAX_HISTORY_WINDOW]
        context_summary = summarize_conversation_history(turns_to_summarize)

    recent_turns = conversation_history[-MAX_HISTORY_WINDOW:]

    previously_gathered_info = {}
    for turn in recent_turns:
        plan = turn.get("plan", {})
        results = turn.get("results", {})
        if plan and results:
            tool_steps = {step["name"] for step in plan.get("steps", []) if step.get("type") == "tool"}
            for tool_name in tool_steps:
                if tool_name in results:
                    previously_gathered_info[tool_name] = results[tool_name]

    info_text = "No information has been gathered yet."
    if previously_gathered_info:
        info_text = json.dumps(previously_gathered_info, indent=2)

    recent_history_text = "\n".join(
        f"User's previous message was: '{turn['user_input']}'. Final response was: '{turn['response']}'."
        for turn in recent_turns
    )

    return f"""CONVERSATION SUMMARY:
{context_summary}

RECENT TURNS:
{recent_history_text}

PREVIOUSLY GATHERED INFORMATION:
This is a JSON object of tool names and their outputs from recent turns. If the user's current request can be answered using this information, you don't need to call the same tool again for information that is static (e.g., OS version).
{info_text}

CURRENT USER REQUEST:
{current_user_input}"""
