from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


HealthKind = Literal["tcp", "http", "docker"]


@dataclass
class HealthCheck:
    name: str
    kind: HealthKind
    target: str  # host:port | url | container_name
    timeout: float = 3.0
    expect_status: int = 200


@dataclass
class RenderResult:
    compose_dir: Path
    compose_file: Path
    services: list[str] = field(default_factory=list)


class PlatformPlugin(ABC):
    """Contract every installable platform must implement."""

    id: str
    name: str
    version: str
    description: str = ""

    @abstractmethod
    def schema(self) -> dict[str, Any]:
        """JSON Schema used by the frontend config form."""

    @abstractmethod
    def default_config(self) -> dict[str, Any]:
        """Default values matching schema."""

    def dependencies(self) -> list[str]:
        return []

    @abstractmethod
    def render(self, cfg: dict[str, Any], work_dir: Path) -> RenderResult:
        """Render compose files into work_dir and return paths."""

    @abstractmethod
    def health_checks(self, cfg: dict[str, Any], project_name: str) -> list[HealthCheck]:
        """Return health probes for this platform instance."""

    def validate(self, cfg: dict[str, Any]) -> list[str]:
        """Return human-readable validation errors (empty = ok)."""
        errors: list[str] = []
        schema = self.schema()
        required = schema.get("required", [])
        props = schema.get("properties", {})
        for key in required:
            if key not in cfg or cfg[key] in (None, ""):
                errors.append(f"{self.id}: missing required field '{key}'")
        for key, meta in props.items():
            if key not in cfg:
                continue
            if meta.get("type") == "integer":
                try:
                    int(cfg[key])
                except (TypeError, ValueError):
                    errors.append(f"{self.id}: '{key}' must be integer")
        return errors
