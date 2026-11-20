from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

from app.core.ai_base import AIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.id] = provider
        logger.info("registered AI provider %s", provider.id)

    def get(self, provider_id: str) -> AIProvider:
        if provider_id not in self._providers:
            raise KeyError(f"unknown AI provider: {provider_id}")
        return self._providers[provider_id]

    def list(self) -> list[AIProvider]:
        return list(self._providers.values())

    def discover(self, root: Path | None = None) -> None:
        base = root or settings.ai_providers_dir
        if not base.exists():
            return
        for child in sorted(base.iterdir()):
            if not child.is_dir() or child.name.startswith("_") or child.name.startswith("."):
                continue
            plugin_file = child / "provider.py"
            if not plugin_file.exists():
                continue
            try:
                mod_name = f"dpi_ai.{child.name}"
                spec = importlib.util.spec_from_file_location(mod_name, plugin_file)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                spec.loader.exec_module(module)
                provider = getattr(module, "provider", None)
                if isinstance(provider, AIProvider):
                    self.register(provider)
            except Exception as exc:  # noqa: BLE001
                logger.exception("failed to load AI provider %s: %s", child.name, exc)


ai_registry = AIRegistry()
