from config import OPENAI_API_KEY, OPENAI_API_URL, ANTHROPIC_API_KEY, ANTHROPIC_API_URL, GOOGLE_API_KEY, GOOGLE_API_URL
from logger import log_event
import urllib.request
import urllib.error
import json

def _get_provider(model: str):
    if "claude" in model:
        return "anthropic"
    if "gemini" in model:
        return "google"
    if "gpt" in model:
        return "openai"
    else:
        return "none"

def _build_request_params(provider: str, model: str, messages: list, temperature: float, max_tokens: int):
    if provider == "anthropic":
        url = ANTHROPIC_API_URL
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        system_message = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        payload = {
            "model": model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if system_message:
            payload["system"] = system_message
        return url, headers, payload

    if provider == "google":
        url = GOOGLE_API_URL.format(model=model) + f"?key={GOOGLE_API_KEY}"
        headers = {"Content-Type": "application/json"}
        gemini_messages = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_messages.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        return url, headers, payload

    if provider == "openai":
        url = OPENAI_API_URL
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        return url, headers, payload
    
    raise ValueError(f"Unsupported provider for model: {model}")

def _parse_response(provider: str, response_body: str):
    """Parses the response from the LLM API and extracts the content."""
    result = json.loads(response_body)
    if provider == "anthropic":
        content_blocks = result.get("content", [])
        if content_blocks and "text" in content_blocks[0]:
            return result, content_blocks[0]["text"]
    elif provider == "google":
        candidates = result.get("candidates", [])
        if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
            return result, candidates[0]["content"]["parts"][0]["text"]
    elif provider == "openai": 
        choices = result.get("choices")
        if choices and len(choices) > 0:
            message = choices[0].get("message")
            if message and "content" in message:
                return result, message["content"]

    return result, None

def chat_completion(model: str, messages: list, temperature: float, max_tokens: int = 800):

    provider = _get_provider(model)
    url, headers, payload = _build_request_params(provider, model, messages, temperature, max_tokens)

    try:
        json_data_string = json.dumps(payload)
        
        data_bytes = json_data_string.encode('utf-8')

        req = urllib.request.Request(url, data=data_bytes, headers=headers)

        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode('utf-8')
            result, content = _parse_response(provider, response_body)

            log_event("LLM API call successful", {"model": model, "usage": result.get("usage", {})})
            if content:
                return content

            error_message = "API response format is unexpected or content not found."
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