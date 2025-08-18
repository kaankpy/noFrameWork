import logging
from llm_client import chat_completion
from config import RESPONDER_MODEL, DEFAULT_TEMPERATURE, MAX_RETRIES, RETRY_BACKOFF_SEC

def generate_final_response(orchestrator_output, aggregated_results):

    try:
        results_text = "\n".join([
            f"- Step {step}: {result}"
            for step, result in aggregated_results.items()
        ])

        responder = {
            "name": "responder_agent",
            "description": "The main agent that coordinates other agents and tools.",
            "system_prompt": "You are the responder agent. Your job is to generate a final response for the user based on the outputs of other agents and tools."
        }

        user_prompt = (
            f"The orchestrator produced the following plan/output:\n"
            f"{orchestrator_output}\n\n"
            f"The following intermediate results were collected:\n"
            f"{results_text}\n\n"
            f"Please generate a clear and helpful final response for the user."
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
