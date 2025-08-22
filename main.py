from loader import load_agents, discover_tools
from planner import plan_with_retry
from executor import execute_plan
from responder import generate_final_response
from memory import init_db, save_message
from history_manager import build_context_for_planner
from logger import log_event, init_log_db

def main():
    init_db()
    init_log_db()
    available_agents = load_agents()
    available_tools = discover_tools()
    agent_list = list(available_agents.values())
    conversation_history = []

    try:
        while True:
            current_user_input = input("User: ").strip()
            if not current_user_input:
                continue

            save_message(role="user", content=current_user_input, meta={"source": "cli"})

            planner_input = build_context_for_planner(
                conversation_history=conversation_history,
                current_user_input=current_user_input
            )

            plan = plan_with_retry(
                user_input=planner_input,
                available_agents=agent_list,
                available_tools=available_tools
            )

            aggregated_results = execute_plan(plan, agents_dir="Agents", user_input=planner_input)

            final_response = generate_final_response(
                orchestrator_output=plan,
                aggregated_results=aggregated_results,
                current_user_input=current_user_input
            )

            save_message(role="assistant", content=final_response, meta={"plan": plan})
            log_event(kind="session_complete", payload={"user_input": current_user_input, "response": final_response})

            conversation_history.append({
                "user_input": current_user_input,
                "plan": plan,
                "response": final_response,
                "results": aggregated_results
            })

            print("\nAssistant:", final_response)
    except KeyboardInterrupt:
        print("\nExiting gracefully. Goodbye!")
        log_event(kind="session_end", payload={"reason": "user_interrupt"})

if __name__ == "__main__":
    main()