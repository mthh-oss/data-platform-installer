from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Extension point for AI providers (DeepSeek now, others later)."""

    id: str
    name: str

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], api_key: str, **kwargs: Any) -> str:
        """Return assistant text response."""
