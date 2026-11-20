from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.plugin_base import HealthCheck, PlatformPlugin, RenderResult
from app.core.template_util import render_template_dir


class DorisPlugin(PlatformPlugin):
    id = "doris"
    name = "Apache Doris"
    version = "2.1"
    description = "Doris FE + BE 演示级 Compose（单 FE / 单 BE）"

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["http_port", "query_port"],
            "properties": {
                "image_tag": {"type": "string", "title": "镜像 Tag", "default": "2.1.7"},
                "http_port": {"type": "integer", "title": "FE HTTP 端口", "default": 8030},
                "query_port": {"type": "integer", "title": "FE Query 端口", "default": 9030},
                "edit_log_port": {"type": "integer", "title": "FE EditLog 端口", "default": 9010},
                "be_web_port": {"type": "integer", "title": "BE Web 端口", "default": 8040},
            },
        }

    def default_config(self) -> dict[str, Any]:
        return {
            "image_tag": "2.1.7",
            "http_port": 8030,
            "query_port": 9030,
            "edit_log_port": 9010,
            "be_web_port": 8040,
        }

    def render(self, cfg: dict[str, Any], work_dir: Path) -> RenderResult:
        render_template_dir(self.id, work_dir, cfg)
        compose_file = work_dir / "docker-compose.yml"
        return RenderResult(
            compose_dir=work_dir,
            compose_file=compose_file,
            services=["doris-fe", "doris-be"],
        )

    def health_checks(self, cfg: dict[str, Any], project_name: str) -> list[HealthCheck]:
        return [
            HealthCheck(
                name="doris-fe-http",
                kind="http",
                target=f"http://127.0.0.1:{cfg['http_port']}/api/bootstrap",
            ),
            HealthCheck(
                name="doris-query-tcp",
                kind="tcp",
                target=f"127.0.0.1:{cfg['query_port']}",
            ),
        ]


plugin = DorisPlugin()
