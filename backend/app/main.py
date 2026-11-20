from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.api import ai, auth, clusters, hosts, jobs, logs, plugins, users
from app.core.ai_registry import ai_registry
from app.core.compose_engine import compose_engine
from app.core.config import settings
from app.core.monitor import health_monitor
from app.core.registry import registry
from app.core.security import get_current_user
from app.db.models import Cluster, User
from app.db.session import SessionLocal, init_db


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("dpi")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    registry.discover()
    ai_registry.discover()
    logger.info("loaded plugins: %s", [p.id for p in registry.list()])
    logger.info("loaded AI providers: %s", [p.id for p in ai_registry.list()])
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(hosts.router, prefix=settings.api_prefix)
app.include_router(plugins.router, prefix=settings.api_prefix)
app.include_router(clusters.router, prefix=settings.api_prefix)
app.include_router(jobs.router, prefix=settings.api_prefix)
app.include_router(logs.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)


@app.get("/api/health")
def api_health() -> dict[str, Any]:
    docker = compose_engine.available()
    return {
        "status": "ok",
        "docker_ok": docker.ok,
        "plugins": [p.id for p in registry.list()],
        "ai_providers": [p.id for p in ai_registry.list()],
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics(_: User = Depends(get_current_user)) -> str:
    lines: list[str] = [
        "# HELP dpi_platform_up 1 if platform health checks all pass",
        "# TYPE dpi_platform_up gauge",
        "# HELP dpi_cluster_up 1 if cluster status is running",
        "# TYPE dpi_cluster_up gauge",
    ]
    db = SessionLocal()
    try:
        clusters_rows = db.query(Cluster).all()
        for cluster in clusters_rows:
            cluster_up = 1 if cluster.status == "running" else 0
            lines.append(
                f'dpi_cluster_up{{cluster="{cluster.name}",id="{cluster.id}"}} {cluster_up}'
            )
            platforms = json.loads(cluster.platforms_json or "[]")
            configs = json.loads(cluster.config_json or "{}")
            docker_ps = ""
            if cluster.compose_file:
                from pathlib import Path

                ps = compose_engine.compose_ps(
                    cluster.project_name, Path(cluster.compose_file), Path(cluster.work_dir)
                )
                docker_ps = (ps.stdout or "") + "\n" + (ps.stderr or "")
            for pid in platforms:
                try:
                    plugin = registry.get(pid)
                    cfg = {**plugin.default_config(), **(configs.get(pid) or {})}
                    checks = plugin.health_checks(cfg, cluster.project_name)
                    result = health_monitor.check_platform(checks, docker_ps=docker_ps)
                    up = 1 if result["ok"] else 0
                except Exception:  # noqa: BLE001
                    up = 0
                lines.append(
                    f'dpi_platform_up{{cluster="{cluster.name}",platform="{pid}"}} {up}'
                )
    finally:
        db.close()
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
