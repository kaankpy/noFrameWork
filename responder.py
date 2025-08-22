import logging
from llm_client import chat_completion
from config import RESPONDER_MODEL, DEFAULT_TEMPERATURE

def generate_final_response(orchestrator_output, aggregated_results, current_user_input):

    try:
        results_text = "\n".join([
            f"- Step {step}: {result}"
            for step, result in aggregated_results.items()
        ])

        responder = {
            "name": "responder_agent",
            "description": "The main agent that coordinates other agents and tools.",
            "system_prompt": (
                "You are the responder agent. Your job is to generate a final, user-facing response. "
                "Analyze the user's most recent message and the collected results. "
                "If the user's message is a simple conversational closing (like 'thank you', 'ok', 'bye'), "
                "respond with a polite, conversational closing (e.g., 'You're welcome!'). Do not summarize previous work in this case. "
                "Otherwise, synthesize the results into a comprehensive answer that directly addresses the user's request."
                "User may also ask follow-up questions or request additional information."
                "User may give input in different languages. Answer in the user's language."
            )
        }

        user_prompt = (
            f"User's most recent message: '{current_user_input}'\n\n"
            f"Orchestrator's plan/output:\n"
            f"{orchestrator_output}\n\n"
            f"Collected intermediate results:\n"
            f"{results_text}\n\n"
            f"Please generate the final response for the user."
        )

        messages = [
            {"role": "system", "content": responder.get("system_prompt")},
            {"role": "user", "content": user_prompt}
        ]

        response = chat_completion(
            model= RESPONDER_MODEL,
            messages=messages,
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=500
        )

        if isinstance(response, dict):
            error_message = response.get("error", "Unknown error from LLM.")
            logging.error(f"Responder agent failed: {error_message}")
            return f"An error occurred while generating the final response: {error_message}"

        final_text = response or "No response generated."
        logging.info("Final response generated successfully by responder agent.")
        return final_text

    except Exception as e:
        logging.error(f"Error in generate_final_response: {e}")
        return "An error occurred while generating the final response."
