from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.plugin_base import HealthCheck, PlatformPlugin, RenderResult
from app.core.template_util import render_template_dir


class DolphinSchedulerPlugin(PlatformPlugin):
    id = "dolphinscheduler"
    name = "Apache DolphinScheduler"
    version = "3.2"
    description = "DolphinScheduler 精简 Compose（自带 Postgres 元库 + ZK + api/master/worker/alert）"

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["api_port", "meta_password"],
            "properties": {
                "image_tag": {"type": "string", "title": "镜像 Tag", "default": "3.2.2"},
                "api_port": {"type": "integer", "title": "API/UI 端口", "default": 12345},
                "meta_password": {
                    "type": "string",
                    "title": "元数据库密码",
                    "default": "ds123456",
                },
            },
        }

    def default_config(self) -> dict[str, Any]:
        return {
            "image_tag": "3.2.2",
            "api_port": 12345,
            "meta_password": "ds123456",
        }

    def render(self, cfg: dict[str, Any], work_dir: Path) -> RenderResult:
        render_template_dir(self.id, work_dir, cfg)

        compose_file = work_dir / "docker-compose.yml"
        return RenderResult(
            compose_dir=work_dir,
            compose_file=compose_file,
            services=["ds-api", "ds-master", "ds-worker", "ds-alert", "ds-postgresql", "ds-zookeeper"],
        )

    def health_checks(self, cfg: dict[str, Any], project_name: str) -> list[HealthCheck]:
        port = cfg["api_port"]
        return [
            HealthCheck(
                name="ds-api-http",
                kind="http",
                target=f"http://127.0.0.1:{port}/dolphinscheduler/actuator/health",
            ),

            HealthCheck(
                name="ds-api-container",
                kind="docker",
                target=f"{project_name}_ds-api",
            ),
        ]


plugin = DolphinSchedulerPlugin()
