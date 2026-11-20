from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.plugin_base import HealthCheck, PlatformPlugin, RenderResult
from app.core.template_util import render_template_dir


class FlinkCDCPlugin(PlatformPlugin):
    id = "flink_cdc"
    name = "Flink CDC"
    version = "3.0"
    description = "Flink CDC 作业侧车与 SQL 骨架（依赖 flink + mysql）"

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["mysql_host", "mysql_port", "mysql_user", "mysql_password", "mysql_database"],
            "properties": {
                "flink_image_tag": {
                    "type": "string",
                    "title": "Flink 镜像 Tag",
                    "default": "1.18.1-scala_2.12-java11",
                },
                "flink_ui_port": {"type": "integer", "title": "Flink UI 端口", "default": 8081},
                "mysql_host": {"type": "string", "title": "MySQL Host", "default": "mysql"},
                "mysql_port": {"type": "integer", "title": "MySQL 端口", "default": 3306},
                "mysql_user": {"type": "string", "title": "MySQL 用户", "default": "root"},
                "mysql_password": {"type": "string", "title": "MySQL 密码", "default": "root123"},
                "mysql_database": {"type": "string", "title": "库名", "default": "demo"},
                "source_table": {"type": "string", "title": "源表", "default": "demo_table"},
            },
        }

    def default_config(self) -> dict[str, Any]:
        return {
            "flink_image_tag": "1.18.1-scala_2.12-java11",
            "flink_ui_port": 8081,
            "mysql_host": "mysql",
            "mysql_port": 3306,
            "mysql_user": "root",
            "mysql_password": "root123",
            "mysql_database": "demo",
            "source_table": "demo_table",
        }

    def dependencies(self) -> list[str]:
        return ["flink", "mysql"]

    def render(self, cfg: dict[str, Any], work_dir: Path) -> RenderResult:
        render_template_dir(self.id, work_dir, cfg)
        compose_file = work_dir / "docker-compose.yml"
        return RenderResult(
            compose_dir=work_dir,
            compose_file=compose_file,
            services=["flink-cdc-sidecar"],
        )

    def health_checks(self, cfg: dict[str, Any], project_name: str) -> list[HealthCheck]:
        return [
            HealthCheck(
                name="flink-cdc-sidecar",
                kind="docker",
                target=f"{project_name}_flink-cdc-sidecar",
            ),
            HealthCheck(
                name="flink-ui-for-cdc",
                kind="http",
                target=f"http://127.0.0.1:{cfg['flink_ui_port']}",
            ),
        ]


plugin = FlinkCDCPlugin()
