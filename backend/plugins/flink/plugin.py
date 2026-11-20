from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.plugin_base import HealthCheck, PlatformPlugin, RenderResult
from app.core.template_util import render_template_dir


class FlinkPlugin(PlatformPlugin):
    id = "flink"
    name = "Apache Flink"
    version = "1.18"
    description = "Flink JobManager + TaskManager 最小集群"

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["ui_port", "task_slots"],
            "properties": {
                "image_tag": {"type": "string", "title": "镜像 Tag", "default": "1.18.1-scala_2.12-java11"},
                "ui_port": {"type": "integer", "title": "Web UI 端口", "default": 8081},
                "task_slots": {"type": "integer", "title": "Task Slots", "default": 2},
                "tm_memory": {"type": "string", "title": "TM 内存", "default": "1024m"},
            },
        }

    def default_config(self) -> dict[str, Any]:
        return {
            "image_tag": "1.18.1-scala_2.12-java11",
            "ui_port": 8081,
            "task_slots": 2,
            "tm_memory": "1024m",
        }

    def render(self, cfg: dict[str, Any], work_dir: Path) -> RenderResult:
        render_template_dir(self.id, work_dir, cfg)
        compose_file = work_dir / "docker-compose.yml"
        return RenderResult(
            compose_dir=work_dir,
            compose_file=compose_file,
            services=["flink-jobmanager", "flink-taskmanager"],
        )

    def health_checks(self, cfg: dict[str, Any], project_name: str) -> list[HealthCheck]:
        return [
            HealthCheck(
                name="flink-ui",
                kind="http",
                target=f"http://127.0.0.1:{cfg['ui_port']}",
            ),
            HealthCheck(
                name="flink-jm-container",
                kind="docker",
                target=f"{project_name}_flink-jobmanager",
            ),
        ]


plugin = FlinkPlugin()
