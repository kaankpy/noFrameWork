from config import OPENAI_API_KEY, OPENAI_API_BASE
from logger import log_event

HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}

def chat_completion(model: str, messages: list, temperature: float = 0.0, max_tokens: int = 800):
    # Input:
    #   model (str) - Kullanılacak LLM modeli
    #   messages (list) - Chat formatında mesaj listesi (role, content)
    #   temperature (float) - LLM yaratıcılık parametresi
    #   max_tokens (int) - Maksimum token sayısı
    # Purpose:
    #   LLM API çağrısı yaparak yanıt döner.
    # Output:
    #   dict - LLM'in cevabı (structured formatta)
    pass
