from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.compose_engine import compose_engine
from app.core.deployer import create_cluster, start_job
from app.core.monitor import health_monitor
from app.core.rbac import (
    filter_clusters_for_user,
    get_cluster_for_user,
    require_write_user,
)
from app.core.registry import registry
from app.core.security import get_current_user
from app.db.models import Cluster, DeployJob, User
from app.db.session import get_db
from app.schemas import ClusterCreate, ClusterOut, HealthOut, JobOut

router = APIRouter(prefix="/clusters", tags=["clusters"])


class OverviewNode(BaseModel):
    id: str
    name: str
    status: str
    ok: bool
    dependencies: list[str]
    checks: list[dict[str, Any]] = []


class OverviewOut(BaseModel):
    cluster_id: int
    cluster_name: str
    cluster_status: str
    checked_at: str
    nodes: list[OverviewNode]
    edges: list[dict[str, str]]


def _to_out(c: Cluster) -> ClusterOut:
    return ClusterOut(
        id=c.id,
        name=c.name,
        project_name=c.project_name,
        status=c.status,
        platforms=json.loads(c.platforms_json or "[]"),
        configs=json.loads(c.config_json or "{}"),
        work_dir=c.work_dir,
        created_at=c.created_at,
    )


@router.get("", response_model=list[ClusterOut])
def list_clusters(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ClusterOut]:
    q = filter_clusters_for_user(db.query(Cluster), user).order_by(Cluster.id.desc())
    return [_to_out(c) for c in q.all()]


@router.post("", response_model=ClusterOut)
def create(
    body: ClusterCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_write_user),
) -> ClusterOut:
    try:
        cluster = create_cluster(db, body.name, body.platforms, body.configs, owner_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(cluster)


@router.get("/{cluster_id}", response_model=ClusterOut)
def get_cluster(
    cluster_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ClusterOut:
    return _to_out(get_cluster_for_user(db, cluster_id, user))


@router.post("/{cluster_id}/deploy", response_model=JobOut)
def deploy(
    cluster_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_write_user),
) -> JobOut:
    get_cluster_for_user(db, cluster_id, user)
    job_id = start_job(cluster_id, "deploy")
    job = db.get(DeployJob, job_id)
    assert job
    return JobOut.model_validate(job)


@router.post("/{cluster_id}/stop", response_model=JobOut)
def stop(
    cluster_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_write_user),
) -> JobOut:
    get_cluster_for_user(db, cluster_id, user)
    job_id = start_job(cluster_id, "stop")
    job = db.get(DeployJob, job_id)
    assert job
    return JobOut.model_validate(job)


@router.post("/{cluster_id}/restart", response_model=JobOut)
def restart(
    cluster_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_write_user),
) -> JobOut:
    get_cluster_for_user(db, cluster_id, user)
    job_id = start_job(cluster_id, "restart")
    job = db.get(DeployJob, job_id)
    assert job
    return JobOut.model_validate(job)


@router.get("/{cluster_id}/health", response_model=HealthOut)
def health(
    cluster_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HealthOut:
    cluster = get_cluster_for_user(db, cluster_id, user)
    platforms: list[str] = json.loads(cluster.platforms_json or "[]")
    configs: dict[str, Any] = json.loads(cluster.config_json or "{}")
    docker_ps = ""
    if cluster.compose_file:
        ps = compose_engine.compose_ps(
            cluster.project_name, Path(cluster.compose_file), Path(cluster.work_dir)
        )
        docker_ps = (ps.stdout or "") + "\n" + (ps.stderr or "")

    platform_health: dict[str, Any] = {}
    for pid in platforms:
        plugin = registry.get(pid)
        cfg = {**plugin.default_config(), **(configs.get(pid) or {})}
        checks = plugin.health_checks(cfg, cluster.project_name)
        platform_health[pid] = health_monitor.check_platform(checks, docker_ps=docker_ps)

    return HealthOut(
        cluster_id=cluster.id,
        cluster_status=cluster.status,
        platforms=platform_health,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{cluster_id}/overview", response_model=OverviewOut)
def overview(
    cluster_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OverviewOut:
    cluster = get_cluster_for_user(db, cluster_id, user)
    platforms: list[str] = json.loads(cluster.platforms_json or "[]")
    configs: dict[str, Any] = json.loads(cluster.config_json or "{}")
    docker_ps = ""
    if cluster.compose_file:
        ps = compose_engine.compose_ps(
            cluster.project_name, Path(cluster.compose_file), Path(cluster.work_dir)
        )
        docker_ps = (ps.stdout or "") + "\n" + (ps.stderr or "")

    nodes: list[OverviewNode] = []
    edges: list[dict[str, str]] = []
    for pid in platforms:
        plugin = registry.get(pid)
        cfg = {**plugin.default_config(), **(configs.get(pid) or {})}
        checks = plugin.health_checks(cfg, cluster.project_name)
        result = health_monitor.check_platform(checks, docker_ps=docker_ps)
        deps = [d for d in plugin.dependencies() if d in platforms]
        nodes.append(
            OverviewNode(
                id=pid,
                name=plugin.name,
                status=result["status"],
                ok=result["ok"],
                dependencies=deps,
                checks=result.get("checks", []),
            )
        )
        for dep in deps:
            edges.append({"from": dep, "to": pid})

    return OverviewOut(
        cluster_id=cluster.id,
        cluster_name=cluster.name,
        cluster_status=cluster.status,
        checked_at=datetime.now(timezone.utc).isoformat(),
        nodes=nodes,
        edges=edges,
    )
