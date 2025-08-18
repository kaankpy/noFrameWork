from config import OPENAI_API_KEY, OPENAI_API_BASE
from logger import log_event
import urllib.request
import urllib.error
import json

HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}

def chat_completion(model: str, messages: list, temperature: float, max_tokens: int = 800):
    url = f"{OPENAI_API_BASE}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        json_data_string = json.dumps(payload)
        
        data_bytes = json_data_string.encode('utf-8')

        req = urllib.request.Request(url, data=data_bytes, headers=HEADERS)

        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode('utf-8')
            
            result = json.loads(response_body)
            
            log_event("LLM API call successful", {"model": model, "usage": result.get("usage", {})})
            
            choices = result.get("choices")
            if choices and len(choices) > 0:
                message = choices[0].get("message")
                if message and "content" in message:
                    return message["content"]
            
            error_message = "API response format is unexpected: 'content' not found."
            log_event("LLM API call failed", {"error": error_message, "response": result})
            return {"error": error_message}
            
    except urllib.error.HTTPError as e:
        error_details = e.read().decode('utf-8')
        log_event("LLM API call failed with HTTP error", {"status_code": e.code, "error": error_details})
        return {"error": f"HTTP Error {e.code}: {error_details}"}
        
    except urllib.error.URLError as e:
        log_event("LLM API call failed with URL error", {"error": str(e.reason)})
        return {"error": str(e.reason)}
    finally:
        pass