from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.core.compose_engine import compose_engine
from app.core.monitor import health_monitor
from app.core.registry import registry
from app.core.security import get_current_user
from app.db.models import Cluster, DeployJob, User
from app.db.session import get_db

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/jobs/{job_id}/download")
def download_job_logs(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    job = db.get(DeployJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    content = job.log_text or ""
    if job.error:
        content += f"\n\nERROR: {job.error}\n"
    filename = f"job-{job_id}-{job.status}.log"
    return Response(
        content=content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/clusters/{cluster_id}/abnormal/download")
def download_abnormal_logs(
    cluster_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="cluster not found")

    platforms = json.loads(cluster.platforms_json or "[]")
    configs = json.loads(cluster.config_json or "{}")
    docker_ps = ""
    if cluster.compose_file:
        ps = compose_engine.compose_ps(
            cluster.project_name, Path(cluster.compose_file), Path(cluster.work_dir)
        )
        docker_ps = (ps.stdout or "") + "\n" + (ps.stderr or "")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        summary_lines = [
            f"cluster={cluster.name}",
            f"status={cluster.status}",
            f"exported_at={datetime.now(timezone.utc).isoformat()}",
            "",
        ]
        # failed jobs
        jobs = (
            db.query(DeployJob)
            .filter(DeployJob.cluster_id == cluster.id)
            .order_by(DeployJob.id.desc())
            .limit(20)
            .all()
        )
        for job in jobs:
            if job.status == "failed" or job.phase == "failed" or job.error:
                zf.writestr(
                    f"jobs/job-{job.id}.log",
                    (job.log_text or "") + (f"\nERROR: {job.error}\n" if job.error else ""),
                )
                summary_lines.append(f"failed_job=#{job.id} phase={job.phase} error={job.error}")

        # unhealthy platform container logs
        for pid in platforms:
            plugin = registry.get(pid)
            cfg = {**plugin.default_config(), **(configs.get(pid) or {})}
            checks = plugin.health_checks(cfg, cluster.project_name)
            result = health_monitor.check_platform(checks, docker_ps=docker_ps)
            if result["ok"]:
                continue
            summary_lines.append(f"unhealthy_platform={pid} detail={result}")
            for check in result.get("checks", []):
                if check.get("kind") == "docker" and not check.get("ok"):
                    cname = check.get("target")
                    logs = compose_engine.container_logs(cname, tail=800)
                    zf.writestr(
                        f"containers/{cname}.log",
                        (logs.stdout or "") + "\n" + (logs.stderr or ""),
                    )
            # also try common container name pattern
            # already covered by docker health check targets

        zf.writestr("SUMMARY.txt", "\n".join(summary_lines) + "\n")

    buf.seek(0)
    filename = f"abnormal-logs-cluster-{cluster_id}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
