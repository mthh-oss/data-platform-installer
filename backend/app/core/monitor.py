from __future__ import annotations

import logging
import socket
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.plugin_base import HealthCheck

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def probe_tcp(host: str, port: int, timeout: float) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "tcp ok"
    except OSError as exc:
        return False, str(exc)


def probe_http(url: str, timeout: float, expect_status: int) -> tuple[bool, str]:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            ok = resp.status_code == expect_status or 200 <= resp.status_code < 400
            return ok, f"http {resp.status_code}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def probe_docker_ps_running(container_name: str, ps_payload: str) -> tuple[bool, str]:
    """Best-effort: check if container name appears as running in compose ps text/json."""
    if not ps_payload:
        return False, "empty compose ps"
    # Accept both json lines and plain text
    lowered = ps_payload.lower()
    name = container_name.lower()
    if name not in lowered:
        return False, f"container {container_name} not found"
    if '"running"' in lowered or " running " in lowered or "up " in lowered:
        return True, "docker running"
    return False, "container present but not running"


def run_health_check(check: HealthCheck, docker_ps: str = "") -> dict[str, Any]:
    ok = False
    detail = ""
    if check.kind == "tcp":
        host, _, port_s = check.target.partition(":")
        ok, detail = probe_tcp(host or "127.0.0.1", int(port_s), check.timeout)
    elif check.kind == "http":
        ok, detail = probe_http(check.target, check.timeout, check.expect_status)
    elif check.kind == "docker":
        ok, detail = probe_docker_ps_running(check.target, docker_ps)
    else:
        detail = f"unknown kind {check.kind}"

    return {
        "name": check.name,
        "kind": check.kind,
        "target": check.target,
        "ok": ok,
        "detail": detail,
        "checked_at": _now_iso(),
    }


class HealthMonitor:
    def check_platform(
        self,
        checks: list[HealthCheck],
        docker_ps: str = "",
    ) -> dict[str, Any]:
        results = [run_health_check(c, docker_ps=docker_ps) for c in checks]
        overall = all(r["ok"] for r in results) if results else False
        return {
            "ok": overall,
            "status": "healthy" if overall else "unhealthy",
            "checks": results,
            "checked_at": _now_iso(),
        }


health_monitor = HealthMonitor()
