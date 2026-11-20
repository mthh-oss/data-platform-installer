from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.compose_engine import compose_engine
from app.core.config import settings
from app.core.registry import registry
from app.db.models import Cluster, DeployJob
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-")
    return s[:48] or "cluster"


def _append_log(db: Session, job: DeployJob, line: str) -> None:
    job.log_text = (job.log_text or "") + line + "\n"
    db.add(job)
    db.commit()


def _set_phase(db: Session, job: DeployJob, phase: str, progress: int, message: str | None = None) -> None:
    job.phase = phase
    job.progress = max(0, min(100, progress))
    db.add(job)
    db.commit()
    if message:
        _append_log(db, job, f"[phase:{phase} {job.progress}%] {message}")


def merge_compose_files(parts: list[Path], out_file: Path) -> Path:
    import yaml

    merged: dict[str, Any] = {
        "services": {},
        "volumes": {},
        "networks": {},
    }
    for part in parts:
        data = yaml.safe_load(part.read_text(encoding="utf-8")) or {}
        for key in ("services", "volumes", "networks"):
            if key in data and isinstance(data[key], dict):
                if key == "services":
                    overlap = set(merged[key]).intersection(data[key])
                    if overlap:
                        raise ValueError(f"compose key conflict in {key}: {sorted(overlap)}")
                    merged[key].update(data[key])
                else:
                    for nk, nv in data[key].items():
                        if nk in merged[key] and merged[key][nk] != nv:
                            raise ValueError(
                                f"compose conflict in {key}.{nk}: incompatible definitions"
                            )
                        merged[key][nk] = nv
        for k, v in data.items():
            if k not in merged:
                merged[k] = v

    cleaned = {k: v for k, v in merged.items() if v}
    out_file.write_text(
        yaml.safe_dump(cleaned, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return out_file


def validate_cluster_request(platforms: list[str], configs: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    try:
        ordered = registry.topological_order(platforms)
    except (KeyError, ValueError) as exc:
        return [str(exc)]

    ports: dict[int, str] = {}
    for pid in ordered:
        plugin = registry.get(pid)
        cfg = {**plugin.default_config(), **(configs.get(pid) or {})}
        errors.extend(plugin.validate(cfg))
        for key, val in cfg.items():
            if "port" in key.lower() and isinstance(val, int):
                if val in ports:
                    errors.append(f"port conflict: {val} used by {ports[val]} and {pid}.{key}")
                else:
                    ports[val] = f"{pid}.{key}"
    return errors


def create_cluster(
    db: Session,
    name: str,
    platforms: list[str],
    configs: dict[str, Any],
    owner_id: int | None = None,
) -> Cluster:
    errors = validate_cluster_request(platforms, configs)
    if errors:
        raise ValueError("; ".join(errors))

    project = f"dpi-{_slug(name)}"
    work_dir = settings.workspaces_dir / project
    cluster = Cluster(
        name=name,
        project_name=project,
        status="created",
        owner_id=owner_id,
        platforms_json=json.dumps(platforms),
        config_json=json.dumps(configs),
        work_dir=str(work_dir),
    )
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    return cluster


def start_job(cluster_id: int, action: str = "deploy") -> int:
    db = SessionLocal()
    try:
        job = DeployJob(
            cluster_id=cluster_id,
            action=action,
            status="pending",
            phase="pending",
            progress=0,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()

    thread = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    thread.start()
    return job_id


def _run_job(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.get(DeployJob, job_id)
        if not job:
            return
        cluster = db.get(Cluster, job.cluster_id)
        if not cluster:
            job.status = "failed"
            job.phase = "failed"
            job.error = "cluster not found"
            db.commit()
            return

        job.status = "running"
        job.phase = "preparing"
        job.progress = 5
        db.commit()

        try:
            if job.action == "deploy":
                _do_deploy(db, job, cluster)
            elif job.action == "stop":
                _set_phase(db, job, "starting", 40, "stopping stack")
                _do_stop(db, job, cluster)
            elif job.action == "restart":
                _set_phase(db, job, "starting", 40, "restarting stack")
                _do_restart(db, job, cluster)
            else:
                raise ValueError(f"unknown action {job.action}")
            job.status = "succeeded"
            job.phase = "ready"
            job.progress = 100
            cluster.status = "running" if job.action != "stop" else "stopped"
            _append_log(db, job, "[phase:ready 100%] done")
        except Exception as exc:  # noqa: BLE001
            logger.exception("job %s failed", job_id)
            job.status = "failed"
            job.phase = "failed"
            job.error = str(exc)
            _append_log(db, job, f"ERROR: {exc}")
            cluster.status = "error"
        finally:
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.add(cluster)
            db.commit()
    finally:
        db.close()


def _do_deploy(db: Session, job: DeployJob, cluster: Cluster) -> None:
    platforms: list[str] = json.loads(cluster.platforms_json)
    configs: dict[str, Any] = json.loads(cluster.config_json)
    ordered = registry.topological_order(platforms)

    _set_phase(db, job, "preparing", 10, "rendering compose templates")
    work_dir = Path(cluster.work_dir)
    compose_engine.ensure_clean_dir(work_dir)
    _append_log(db, job, f"workspace: {work_dir}")
    _append_log(db, job, f"deploy order: {ordered}")

    part_files: list[Path] = []
    for idx, pid in enumerate(ordered):
        plugin = registry.get(pid)
        cfg = {**plugin.default_config(), **(configs.get(pid) or {})}
        cfg["_project"] = cluster.project_name
        cfg["_cluster_name"] = cluster.name
        plugin_dir = work_dir / pid
        result = plugin.render(cfg, plugin_dir)
        part_files.append(result.compose_file)
        progress = 10 + int((idx + 1) / max(len(ordered), 1) * 15)
        _set_phase(db, job, "preparing", progress, f"rendered {pid}")

    compose_file = work_dir / "docker-compose.yml"
    merge_compose_files(part_files, compose_file)
    cluster.compose_file = str(compose_file)
    db.add(cluster)
    db.commit()
    _append_log(db, job, f"merged compose: {compose_file}")

    avail = compose_engine.available()
    if avail.stdout:
        _append_log(db, job, avail.stdout)
    if avail.stderr:
        _append_log(db, job, avail.stderr)
    if not avail.ok:
        raise RuntimeError("Docker is not available. Install Docker and ensure `docker` is on PATH.")

    _set_phase(db, job, "downloading", 30, "pulling container images (download)")

    def on_pull_line(line: str) -> None:
        _append_log(db, job, line)
        # best-effort progress bumps while downloading
        if job.progress < 70:
            job.progress = min(70, job.progress + 1)
            db.add(job)
            db.commit()

    pull = compose_engine.compose_pull(
        cluster.project_name, compose_file, work_dir, on_line=on_pull_line
    )
    if not pull.ok:
        raise RuntimeError(f"docker compose pull failed (code={pull.returncode})")

    _set_phase(db, job, "starting", 75, "starting containers")

    def on_up_line(line: str) -> None:
        _append_log(db, job, line)
        if job.progress < 95:
            job.progress = min(95, job.progress + 1)
            db.add(job)
            db.commit()

    result = compose_engine.compose_up(
        cluster.project_name, compose_file, work_dir, on_line=on_up_line
    )
    if not result.ok:
        raise RuntimeError(f"docker compose up failed (code={result.returncode})")

    _set_phase(db, job, "starting", 95, "containers started, waiting for health probes on monitor page")


def _do_stop(db: Session, job: DeployJob, cluster: Cluster) -> None:
    compose_file = Path(cluster.compose_file)
    work_dir = Path(cluster.work_dir)
    if not compose_file.exists():
        raise FileNotFoundError("compose file missing; deploy first")
    result = compose_engine.compose_down(cluster.project_name, compose_file, work_dir)
    _append_log(db, job, result.stdout)
    if result.stderr:
        _append_log(db, job, result.stderr)
    if not result.ok:
        raise RuntimeError(f"docker compose down failed (code={result.returncode})")


def _do_restart(db: Session, job: DeployJob, cluster: Cluster) -> None:
    compose_file = Path(cluster.compose_file)
    work_dir = Path(cluster.work_dir)
    if not compose_file.exists():
        raise FileNotFoundError("compose file missing; deploy first")
    result = compose_engine.compose_restart(cluster.project_name, compose_file, work_dir)
    _append_log(db, job, result.stdout)
    if result.stderr:
        _append_log(db, job, result.stderr)
    if not result.ok:
        raise RuntimeError(f"docker compose restart failed (code={result.returncode})")
