import ollama
from typing import Optional

def query_ollama(prompt: str, system_prompt: str = "", model: str = "qwen2.5:1.5b") -> Optional[str]:
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = ollama.chat(model=model, messages=messages)
        return response['message']['content'].strip()
    except Exception as e:
        return None
