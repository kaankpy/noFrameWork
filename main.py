# main.py
# Projenin ana giriş noktasıdır.
# Orchestrator agent üzerinden plan oluşturma, yürütme ve cevap döndürme sürecini yönetir.

from loader import load_agents, discover_tools
from planner import plan_with_retry
from executor import execute_plan
from responder import generate_final_response
from memory import init_db, save_message
from logger import log_event


def main():
    # 1. Veritabanını başlat
    init_db()

    # 2. Kullanıcıdan girdi al
    user_input = input("User: ").strip()

    # 3. Kullanıcı mesajını kaydet
    save_message(role="user", content=user_input, meta={"source": "cli"})

    # 4. Agent ve tool bilgilerini yükle
    available_agents = load_agents()
    available_tools = discover_tools()

    # 5. Orchestrator agent bilgisini al
    orchestrator_meta = available_agents.get("orchestrator_agent", {})

    # 6. Plan oluştur
    plan = plan_with_retry(
        agent_meta=orchestrator_meta,
        user_input=user_input,
        available_agents=list(available_agents.keys()),
        available_tools=available_tools
    )

    # 7. Plan yürütme
    aggregated_results = execute_plan(plan, agents_dir="Agents")

    # 8. Final cevabı oluştur
    final_response = generate_final_response(
        orchestrator_output=plan,
        aggregated_results=aggregated_results
    )

    # 9. Asistan cevabını kaydet
    save_message(role="assistant", content=final_response, meta={"plan": plan})

    # 10. Loglama
    log_event(kind="session_complete", payload={"user_input": user_input, "response": final_response})

    # 11. Ekrana yazdır
    print("\nAssistant:", final_response)


if __name__ == "__main__":
    main()