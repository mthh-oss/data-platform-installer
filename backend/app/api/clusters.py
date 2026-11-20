from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.compose_engine import compose_engine
from app.core.deployer import create_cluster, start_job
from app.core.monitor import health_monitor
from app.core.registry import registry
from app.db.models import Cluster, DeployJob
from app.db.session import get_db
from app.schemas import ClusterCreate, ClusterOut, HealthOut, JobOut

router = APIRouter(prefix="/clusters", tags=["clusters"])


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
def list_clusters(db: Session = Depends(get_db)) -> list[ClusterOut]:
    rows = db.query(Cluster).order_by(Cluster.id.desc()).all()
    return [_to_out(c) for c in rows]


@router.post("", response_model=ClusterOut)
def create(body: ClusterCreate, db: Session = Depends(get_db)) -> ClusterOut:
    try:
        cluster = create_cluster(db, body.name, body.platforms, body.configs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(cluster)


@router.get("/{cluster_id}", response_model=ClusterOut)
def get_cluster(cluster_id: int, db: Session = Depends(get_db)) -> ClusterOut:
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="cluster not found")
    return _to_out(cluster)


@router.post("/{cluster_id}/deploy", response_model=JobOut)
def deploy(cluster_id: int, db: Session = Depends(get_db)) -> JobOut:
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="cluster not found")
    job_id = start_job(cluster_id, "deploy")
    job = db.get(DeployJob, job_id)
    assert job
    return JobOut.model_validate(job)


@router.post("/{cluster_id}/stop", response_model=JobOut)
def stop(cluster_id: int, db: Session = Depends(get_db)) -> JobOut:
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="cluster not found")
    job_id = start_job(cluster_id, "stop")
    job = db.get(DeployJob, job_id)
    assert job
    return JobOut.model_validate(job)


@router.post("/{cluster_id}/restart", response_model=JobOut)
def restart(cluster_id: int, db: Session = Depends(get_db)) -> JobOut:
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="cluster not found")
    job_id = start_job(cluster_id, "restart")
    job = db.get(DeployJob, job_id)
    assert job
    return JobOut.model_validate(job)


@router.get("/{cluster_id}/health", response_model=HealthOut)
def health(cluster_id: int, db: Session = Depends(get_db)) -> HealthOut:
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="cluster not found")

    platforms: list[str] = json.loads(cluster.platforms_json or "[]")
    configs: dict[str, Any] = json.loads(cluster.config_json or "{}")
    docker_ps = ""
    if cluster.compose_file:
        from pathlib import Path

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

    from datetime import datetime, timezone

    return HealthOut(
        cluster_id=cluster.id,
        cluster_status=cluster.status,
        platforms=platform_health,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )
