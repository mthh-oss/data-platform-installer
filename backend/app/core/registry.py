from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

from app.core.config import settings
from app.core.plugin_base import PlatformPlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PlatformPlugin] = {}

    def discover(self, plugins_dir: Path | None = None) -> None:
        root = plugins_dir or settings.plugins_dir
        if not root.exists():
            logger.warning("plugins dir missing: %s", root)
            return

        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith(".") or child.name.startswith("__"):
                continue
            # example stays loadable only when renamed / explicitly enabled
            if child.name.startswith("_"):
                logger.info("skip example/disabled plugin dir: %s", child.name)
                continue
            plugin_file = child / "plugin.py"
            if not plugin_file.exists():
                logger.warning("no plugin.py in %s", child)
                continue
            try:
                plugin = self._load_plugin(plugin_file, child.name)
                self.register(plugin)
            except Exception as exc:  # noqa: BLE001
                logger.exception("failed to load plugin %s: %s", child.name, exc)

    def _load_plugin(self, path: Path, module_name: str) -> PlatformPlugin:
        mod_name = f"dpi_plugins.{module_name}"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
        plugin = getattr(module, "plugin", None)
        if plugin is None:
            raise AttributeError(f"{path} must export `plugin`")
        if not isinstance(plugin, PlatformPlugin):
            raise TypeError(f"{path} plugin is not PlatformPlugin")
        return plugin

    def register(self, plugin: PlatformPlugin) -> None:
        if plugin.id in self._plugins:
            logger.warning("overwriting plugin %s", plugin.id)
        self._plugins[plugin.id] = plugin
        logger.info("registered plugin %s (%s)", plugin.id, plugin.name)

    def get(self, plugin_id: str) -> PlatformPlugin:
        if plugin_id not in self._plugins:
            raise KeyError(f"unknown plugin: {plugin_id}")
        return self._plugins[plugin_id]

    def list(self) -> list[PlatformPlugin]:
        return list(self._plugins.values())

    def topological_order(self, selected: list[str]) -> list[str]:
        """Order selected plugin ids by dependencies (Kahn)."""
        selected_set = set(selected)
        indegree = {pid: 0 for pid in selected}
        edges: dict[str, list[str]] = {pid: [] for pid in selected}

        for pid in selected:
            plugin = self.get(pid)
            for dep in plugin.dependencies():
                if dep not in selected_set:
                    raise ValueError(
                        f"plugin '{pid}' requires '{dep}' but it was not selected"
                    )
                edges[dep].append(pid)
                indegree[pid] += 1

        queue = [pid for pid, deg in indegree.items() if deg == 0]
        ordered: list[str] = []
        while queue:
            queue.sort()
            cur = queue.pop(0)
            ordered.append(cur)
            for nxt in edges[cur]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        if len(ordered) != len(selected):
            raise ValueError("circular plugin dependency detected")
        return ordered


registry = PluginRegistry()
