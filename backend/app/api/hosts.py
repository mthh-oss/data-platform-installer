from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.rbac import ROLE_ADMIN, ROLE_OPERATOR, require_roles
from app.db.models import Host, User
from app.db.session import get_db

router = APIRouter(prefix="/hosts", tags=["hosts"])


class HostIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    ip: str = Field(min_length=3, max_length=64)
    ssh_port: int = 22
    ssh_user: str = "root"
    is_local: bool = False
    labels: str = ""
    remark: str = ""
    enabled: bool = True


class HostOut(HostIn):
    id: int

    class Config:
        from_attributes = True


@router.get("", response_model=list[HostOut])
def list_hosts(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR, "viewer")),
) -> list[HostOut]:
    return [HostOut.model_validate(h) for h in db.query(Host).order_by(Host.id.asc()).all()]


@router.post("", response_model=HostOut)
def create_host(
    body: HostIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
) -> HostOut:
    if db.query(Host).filter(Host.name == body.name).first():
        raise HTTPException(status_code=400, detail="主机名已存在")
    host = Host(**body.model_dump())
    db.add(host)
    db.commit()
    db.refresh(host)
    return HostOut.model_validate(host)


@router.put("/{host_id}", response_model=HostOut)
def update_host(
    host_id: int,
    body: HostIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
) -> HostOut:
    host = db.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")
    for k, v in body.model_dump().items():
        setattr(host, k, v)
    db.commit()
    db.refresh(host)
    return HostOut.model_validate(host)


@router.delete("/{host_id}")
def delete_host(
    host_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN)),
) -> dict:
    host = db.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")
    db.delete(host)
    db.commit()
    return {"ok": True}
