"""Custom plugin example.

How to enable:
1. Copy this folder to `backend/plugins/my_platform/` (name must NOT start with `_`)
2. Copy `templates/_example_custom/` to `templates/my_platform/`
3. Change `id` / `name` below and template folder name to match
4. Restart the control plane — it will appear in GET /api/plugins
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.plugin_base import HealthCheck, PlatformPlugin, RenderResult
from app.core.template_util import render_template_dir


class ExampleCustomPlugin(PlatformPlugin):
    id = "example_custom"
    name = "Example Custom Platform"
    version = "0.1.0"
    description = "扩展样例：Nginx 单容器（默认不加载，目录名以 _ 开头）"

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["host_port"],
            "properties": {
                "image_tag": {"type": "string", "title": "镜像 Tag", "default": "1.27-alpine"},
                "host_port": {"type": "integer", "title": "宿主机端口", "default": 18080},
            },
        }

    def default_config(self) -> dict[str, Any]:
        return {"image_tag": "1.27-alpine", "host_port": 18080}

    def render(self, cfg: dict[str, Any], work_dir: Path) -> RenderResult:
        # template dir name follows plugin id; for the example folder use _example_custom
        template_id = "example_custom"
        # when still under _example_custom, render from that template path
        from app.core.config import settings

        src = settings.templates_dir / "_example_custom"
        if src.exists() and not (settings.templates_dir / template_id).exists():
            # temporary alias: render using _example_custom templates
            from jinja2 import Environment, FileSystemLoader, StrictUndefined

            env = Environment(
                loader=FileSystemLoader(str(src)),
                undefined=StrictUndefined,
                keep_trailing_newline=True,
            )
            work_dir.mkdir(parents=True, exist_ok=True)
            for path in src.rglob("*"):
                if path.is_dir():
                    continue
                rel = path.relative_to(src)
                out_name = rel.name[:-3] if rel.name.endswith(".j2") else rel.name
                out_path = work_dir / rel.parent / out_name
                out_path.parent.mkdir(parents=True, exist_ok=True)
                if rel.name.endswith(".j2"):
                    tpl = env.get_template(str(rel).replace("\\", "/"))
                    out_path.write_text(tpl.render(**cfg), encoding="utf-8")
                else:
                    out_path.write_bytes(path.read_bytes())
        else:
            render_template_dir(template_id, work_dir, cfg)
        compose_file = work_dir / "docker-compose.yml"
        return RenderResult(compose_dir=work_dir, compose_file=compose_file, services=["example-nginx"])

    def health_checks(self, cfg: dict[str, Any], project_name: str) -> list[HealthCheck]:
        return [
            HealthCheck(
                name="example-http",
                kind="http",
                target=f"http://127.0.0.1:{cfg['host_port']}",
            )
        ]


plugin = ExampleCustomPlugin()
