from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Query, Session

from app.core.security import get_current_user
from app.db.models import Cluster, User

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_VIEWER = "viewer"


def _ensure_enabled(user: User) -> User:
    if not getattr(user, "enabled", True):
        raise HTTPException(status_code=403, detail="账号已禁用")
    return user


def require_roles(*roles: str):
    def _dep(user: User = Depends(get_current_user)) -> User:
        _ensure_enabled(user)
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user

    return _dep


def require_write_user(user: User = Depends(get_current_user)) -> User:
    _ensure_enabled(user)
    if user.role not in (ROLE_ADMIN, ROLE_OPERATOR):
        raise HTTPException(status_code=403, detail="只读账号无权执行此操作")
    return user


def can_manage_all(user: User) -> bool:
    return user.role == ROLE_ADMIN


def filter_clusters_for_user(q: Query, user: User) -> Query:
    if can_manage_all(user):
        return q
    return q.filter(Cluster.owner_id == user.id)


def get_cluster_for_user(db: Session, cluster_id: int, user: User) -> Cluster:
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="cluster not found")
    if not can_manage_all(user) and cluster.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该集群")
    return cluster
