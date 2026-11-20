from __future__ import annotations

from typing import Any

import httpx

from app.core.ai_base import AIProvider


class DeepSeekProvider(AIProvider):
    id = "deepseek"
    name = "DeepSeek"

    def chat(self, messages: list[dict[str, str]], api_key: str, **kwargs: Any) -> str:
        if not api_key:
            raise ValueError("DeepSeek API Key 未配置")
        model = kwargs.get("model") or "deepseek-chat"
        url = kwargs.get("base_url") or "https://api.deepseek.com/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=90.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]


provider = DeepSeekProvider()
