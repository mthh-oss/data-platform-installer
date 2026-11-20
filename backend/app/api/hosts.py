from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.host_crypto import encrypt_secret
from app.core.rbac import ROLE_ADMIN, ROLE_OPERATOR, require_roles
from app.core.ssh_probe import probe_ssh
from app.db.models import Host, User
from app.db.session import get_db

router = APIRouter(prefix="/hosts", tags=["hosts"])


class HostIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    ip: str = Field(min_length=3, max_length=64)
    ssh_port: int = 22
    ssh_user: str = Field(default="root", min_length=1, max_length=64)
    ssh_password: str = Field(default="", max_length=128)  # 明文仅写入，永不回读
    is_local: bool = False
    labels: str = ""
    remark: str = ""
    enabled: bool = True
    skip_ssh_check: bool = False  # 仅本机/调试；正式环境应校验


class HostOut(BaseModel):
    id: int
    name: str
    ip: str
    ssh_port: int = 22
    ssh_user: str = "root"
    is_local: bool = False
    labels: str = ""
    remark: str = ""
    enabled: bool = True
    agent_status: str = "unverified"
    has_password: bool = False

    class Config:
        from_attributes = True


def _to_out(host: Host) -> HostOut:
    return HostOut(
        id=host.id,
        name=host.name,
        ip=host.ip,
        ssh_port=host.ssh_port or 22,
        ssh_user=host.ssh_user or "root",
        is_local=bool(host.is_local),
        labels=host.labels or "",
        remark=host.remark or "",
        enabled=bool(host.enabled),
        agent_status=host.agent_status or "unverified",
        has_password=bool(host.ssh_password_enc),
    )


def _require_password_for_remote(body: HostIn) -> None:
    if body.is_local:
        return
    if not (body.ssh_password or "").strip():
        raise HTTPException(status_code=400, detail="远程主机必须填写 SSH 密码，否则无法纳管")


def _verify_or_raise(body: HostIn) -> str:
    """返回 agent_status。"""
    if body.is_local:
        return "verified"
    if body.skip_ssh_check:
        # 仍要求有密码落库，只是跳过探活
        return "unverified"
    ok, reason = probe_ssh(body.ip, body.ssh_port, body.ssh_user, body.ssh_password)
    if not ok:
        raise HTTPException(status_code=400, detail=reason or "SSH 校验失败")
    return "verified"


@router.get("", response_model=list[HostOut])
def list_hosts(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR, "viewer")),
) -> list[HostOut]:
    return [_to_out(h) for h in db.query(Host).order_by(Host.id.asc()).all()]


@router.get("/{host_id}", response_model=HostOut)
def get_host(
    host_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR, "viewer")),
) -> HostOut:
    host = db.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")
    return _to_out(host)


@router.post("", response_model=HostOut)
def create_host(
    body: HostIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
) -> HostOut:
    _require_password_for_remote(body)
    if db.query(Host).filter(Host.name == body.name).first():
        raise HTTPException(status_code=400, detail="主机名已存在")
    agent_status = _verify_or_raise(body)
    data = body.model_dump(exclude={"ssh_password", "skip_ssh_check"})
    host = Host(
        **data,
        ssh_password_enc=encrypt_secret(body.ssh_password) if body.ssh_password else "",
        agent_status=agent_status,
    )
    db.add(host)
    db.commit()
    db.refresh(host)
    return _to_out(host)


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

    # 未传新密码时，沿用已有密文；远程主机必须已有或新填密码
    if not body.is_local and not (body.ssh_password or "").strip() and not host.ssh_password_enc:
        raise HTTPException(status_code=400, detail="远程主机必须填写 SSH 密码")

    pwd = (body.ssh_password or "").strip()
    if pwd:
        check_body = body.model_copy(update={"ssh_password": pwd})
        agent_status = _verify_or_raise(check_body)
        host.ssh_password_enc = encrypt_secret(pwd)
        host.agent_status = agent_status
    elif body.is_local:
        host.agent_status = "verified"
    elif not body.skip_ssh_check and host.ssh_password_enc:
        # 用已存密码重探（改 IP/账号时）
        from app.core.host_crypto import decrypt_secret

        try:
            old_pwd = decrypt_secret(host.ssh_password_enc)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        ok, reason = probe_ssh(body.ip, body.ssh_port, body.ssh_user, old_pwd)
        if not ok:
            raise HTTPException(status_code=400, detail=reason or "SSH 校验失败")
        host.agent_status = "verified"

    for k, v in body.model_dump(exclude={"ssh_password", "skip_ssh_check"}).items():
        setattr(host, k, v)
    db.commit()
    db.refresh(host)
    return _to_out(host)


@router.post("/{host_id}/verify", response_model=HostOut)
def verify_host(
    host_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
) -> HostOut:
    host = db.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")
    if host.is_local:
        host.agent_status = "verified"
        db.commit()
        db.refresh(host)
        return _to_out(host)
    if not host.ssh_password_enc:
        raise HTTPException(status_code=400, detail="主机未配置 SSH 密码，请重新纳管并填写密码")
    from app.core.host_crypto import decrypt_secret

    try:
        pwd = decrypt_secret(host.ssh_password_enc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ok, reason = probe_ssh(host.ip, host.ssh_port or 22, host.ssh_user or "root", pwd)
    host.agent_status = "verified" if ok else "offline"
    db.commit()
    db.refresh(host)
    if not ok:
        raise HTTPException(status_code=400, detail=reason or "SSH 校验失败")
    return _to_out(host)


@router.delete("/{host_id}")
def delete_host(
    host_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
) -> dict:
    host = db.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")
    db.delete(host)
    db.commit()
    return {"ok": True}
