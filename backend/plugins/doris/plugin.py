from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.plugin_base import HealthCheck, PlatformPlugin, RenderResult
from app.core.template_util import render_template_dir
from app.db.session import SessionLocal
from app.db.models import Host


class DorisPlugin(PlatformPlugin):
    id = "doris"
    name = "Apache Doris"
    version = "2.1"
    description = "Doris FE/BE：可从主机库存选择机器，节点间通过 IP 互通"

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["http_port", "query_port", "fe_host_ids", "be_host_ids"],
            "properties": {
                "image_tag": {"type": "string", "title": "镜像 Tag", "default": "2.1.7"},
                "http_port": {"type": "integer", "title": "FE HTTP 起始端口", "default": 8030},
                "query_port": {"type": "integer", "title": "FE Query 起始端口", "default": 9030},
                "edit_log_port": {"type": "integer", "title": "FE EditLog 端口", "default": 9010},
                "be_web_port": {"type": "integer", "title": "BE Web 起始端口", "default": 8040},
                "fe_host_ids": {
                    "type": "array",
                    "title": "FE 机器（可多选）",
                    "items": {"type": "integer"},
                    "x-ui": "host-multi",
                    "x-host-label": "fe",
                },
                "be_host_ids": {
                    "type": "array",
                    "title": "BE 机器（可多选）",
                    "items": {"type": "integer"},
                    "x-ui": "host-multi",
                    "x-host-label": "be",
                },
            },
        }

    def default_config(self) -> dict[str, Any]:
        return {
            "image_tag": "2.1.7",
            "http_port": 8030,
            "query_port": 9030,
            "edit_log_port": 9010,
            "be_web_port": 8040,
            "fe_host_ids": [],
            "be_host_ids": [],
        }

    def validate(self, cfg: dict[str, Any]) -> list[str]:
        errors = super().validate(cfg)
        fe_ids = cfg.get("fe_host_ids") or []
        be_ids = cfg.get("be_host_ids") or []
        if not fe_ids:
            errors.append("doris: 请至少选择 1 台 FE 机器")
        if not be_ids:
            errors.append("doris: 请至少选择 1 台 BE 机器")
        return errors

    def _load_hosts(self, ids: list[int]) -> list[Host]:
        if not ids:
            return []
        db = SessionLocal()
        try:
            rows = db.query(Host).filter(Host.id.in_(ids), Host.enabled.is_(True)).all()
            by_id = {h.id: h for h in rows}
            missing = [i for i in ids if i not in by_id]
            if missing:
                raise ValueError(f"主机不存在或已禁用: {missing}")
            return [by_id[i] for i in ids]
        finally:
            db.close()

    def render(self, cfg: dict[str, Any], work_dir: Path) -> RenderResult:
        fe_hosts = self._load_hosts([int(x) for x in (cfg.get("fe_host_ids") or [])])
        be_hosts = self._load_hosts([int(x) for x in (cfg.get("be_host_ids") or [])])

        edit_log_port = int(cfg.get("edit_log_port") or 9010)
        http_port = int(cfg.get("http_port") or 8030)
        query_port = int(cfg.get("query_port") or 9030)
        be_web_port = int(cfg.get("be_web_port") or 8040)

        fe_nodes = []
        fe_server_parts = []
        for idx, h in enumerate(fe_hosts, start=1):
            fe_nodes.append(
                {
                    "id": idx,
                    "fe_id": idx,
                    "host_id": h.id,
                    "ip": h.ip,
                    "name": h.name,
                    "http_port": http_port + (idx - 1),
                    "query_port": query_port + (idx - 1),
                }
            )
            # FE 互通：使用各机器 IP + edit_log_port
            fe_server_parts.append(f"fe{idx}:{h.ip}:{edit_log_port}")

        be_nodes = []
        for idx, h in enumerate(be_hosts, start=1):
            be_nodes.append(
                {
                    "id": idx,
                    "host_id": h.id,
                    "ip": h.ip,
                    "name": h.name,
                    "web_port": be_web_port + (idx - 1),
                }
            )

        render_cfg = {
            **cfg,
            "fe_nodes": fe_nodes,
            "be_nodes": be_nodes,
            "fe_servers": ",".join(fe_server_parts),
        }
        render_template_dir(self.id, work_dir, render_cfg)

        # placement plan for ops / multi-host
        plan = {
            "fe": [{"host_id": n["host_id"], "host": n["name"], "ip": n["ip"], "service": f"doris-fe-{n['id']}"} for n in fe_nodes],
            "be": [{"host_id": n["host_id"], "host": n["name"], "ip": n["ip"], "service": f"doris-be-{n['id']}"} for n in be_nodes],
            "fe_servers": render_cfg["fe_servers"],
            "note": "同一 Docker 主机可直接 compose up；跨主机请按 placement 在对应机器拉起服务并保证 IP 互通。",
        }
        (work_dir / "placement.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        compose_file = work_dir / "docker-compose.yml"
        services = [f"doris-fe-{n['id']}" for n in fe_nodes] + [f"doris-be-{n['id']}" for n in be_nodes]
        return RenderResult(compose_dir=work_dir, compose_file=compose_file, services=services)

    def health_checks(self, cfg: dict[str, Any], project_name: str) -> list[HealthCheck]:
        # probe first FE ports on control plane / localhost mapping
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
