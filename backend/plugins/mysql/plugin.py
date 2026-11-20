from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.plugin_base import HealthCheck, PlatformPlugin, RenderResult
from app.core.template_util import render_template_dir


class MySQLPlugin(PlatformPlugin):
    id = "mysql"
    name = "MySQL"
    version = "8.0"
    description = "MySQL 8 单实例，开启 ROW binlog，可供 Flink CDC / DolphinScheduler 使用"

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["host_port", "root_password", "database", "user", "password"],
            "properties": {
                "image_tag": {"type": "string", "title": "镜像 Tag", "default": "8.0"},
                "host_port": {"type": "integer", "title": "宿主机端口", "default": 3306},
                "root_password": {"type": "string", "title": "Root 密码", "default": "root123"},
                "database": {"type": "string", "title": "默认库", "default": "demo"},
                "user": {"type": "string", "title": "业务用户", "default": "demo"},
                "password": {"type": "string", "title": "业务密码", "default": "demo123"},
            },
        }

    def default_config(self) -> dict[str, Any]:
        return {
            "image_tag": "8.0",
            "host_port": 3306,
            "root_password": "root123",
            "database": "demo",
            "user": "demo",
            "password": "demo123",
        }

    def render(self, cfg: dict[str, Any], work_dir: Path) -> RenderResult:
        render_template_dir(self.id, work_dir, cfg)
        compose_file = work_dir / "docker-compose.yml"
        return RenderResult(compose_dir=work_dir, compose_file=compose_file, services=["mysql"])

    def health_checks(self, cfg: dict[str, Any], project_name: str) -> list[HealthCheck]:
        return [
            HealthCheck(name="mysql-tcp", kind="tcp", target=f"127.0.0.1:{cfg['host_port']}"),
            HealthCheck(
                name="mysql-container",
                kind="docker",
                target=f"{project_name}_mysql",
            ),
        ]


plugin = MySQLPlugin()
