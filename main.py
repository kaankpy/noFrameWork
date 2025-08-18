from loader import load_agents, discover_tools
from planner import plan_with_retry
from executor import execute_plan
from responder import generate_final_response
from memory import init_db, save_message
from logger import log_event

def main():
    init_db()


    user_input = input("User: ").strip()

    save_message(role="user", content=user_input, meta={"source": "cli"})

    available_agents = load_agents()
    available_tools = discover_tools()

    agent_list = list(available_agents.values())

    plan = plan_with_retry(
        user_input=user_input,
        available_agents=agent_list,
        available_tools=available_tools
    )

    aggregated_results = execute_plan(plan, agents_dir="Agents", user_input=user_input)

    final_response = generate_final_response(
        orchestrator_output=plan,
        aggregated_results=aggregated_results
    )

    save_message(role="assistant", content=final_response, meta={"plan": plan})

    log_event(kind="session_complete", payload={"user_input": user_input, "response": final_response})

    print("\nAssistant:", final_response)


if __name__ == "__main__":
    main()