from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.models import DeployJob, User
from app.db.session import get_db
from app.schemas import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(
    cluster_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[JobOut]:
    q = db.query(DeployJob).order_by(DeployJob.id.desc())
    if cluster_id is not None:
        q = q.filter(DeployJob.cluster_id == cluster_id)
    return [JobOut.model_validate(j) for j in q.limit(100).all()]


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> JobOut:
    job = db.get(DeployJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobOut.model_validate(job)


@router.get("/{job_id}/logs", response_class=PlainTextResponse)
def get_job_logs(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> str:
    job = db.get(DeployJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job.log_text or ""
