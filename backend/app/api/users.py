from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.rbac import ROLE_ADMIN, require_roles
from app.core.security import get_current_user, hash_password, validate_password_policy
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    display_name: str = ""
    department: str = ""
    title: str = ""
    manager_id: int | None = None
    manager_name: str | None = None
    enabled: bool = True

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=64)
    role: str = "operator"
    display_name: str = ""
    department: str = ""
    title: str = ""
    manager_id: int | None = None


class PersonnelUpdate(BaseModel):
    display_name: str | None = None
    department: str | None = None
    title: str | None = None
    manager_id: int | None = None
    role: str | None = None
    enabled: bool | None = None
    password: str | None = None


def _to_out(u: User, by_id: dict[int, User]) -> UserOut:
    mgr = by_id.get(u.manager_id) if u.manager_id else None
    return UserOut(
        id=u.id,
        username=u.username,
        role=u.role,
        display_name=u.display_name or "",
        department=u.department or "",
        title=u.title or "",
        manager_id=u.manager_id,
        manager_name=(mgr.display_name or mgr.username) if mgr else None,
        enabled=bool(u.enabled),
    )


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[UserOut]:
    rows = db.query(User).order_by(User.id.asc()).all()
    by_id = {u.id: u for u in rows}
    return [_to_out(u, by_id) for u in rows]


@router.post("", response_model=UserOut)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN)),
) -> UserOut:
    if body.role not in ("admin", "operator", "viewer"):
        raise HTTPException(status_code=400, detail="role 必须是 admin/operator/viewer")
    errors = validate_password_policy(body.password)
    if errors:
        raise HTTPException(status_code=400, detail="；".join(errors))
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if body.manager_id:
        if not db.get(User, body.manager_id):
            raise HTTPException(status_code=400, detail="上级不存在")
    user = User(
        username=body.username.strip(),
        password_hash=hash_password(body.password),
        role=body.role,
        display_name=body.display_name or body.username,
        department=body.department or "",
        title=body.title or "",
        manager_id=body.manager_id,
        enabled=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    rows = db.query(User).all()
    return _to_out(user, {u.id: u for u in rows})


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: PersonnelUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles(ROLE_ADMIN)),
) -> UserOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.role is not None:
        if body.role not in ("admin", "operator", "viewer"):
            raise HTTPException(status_code=400, detail="非法角色")
        if user.id == current.id and body.role != "admin":
            raise HTTPException(status_code=400, detail="不能取消自己的 admin")
        user.role = body.role
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.department is not None:
        user.department = body.department
    if body.title is not None:
        user.title = body.title
    if body.manager_id is not None:
        if body.manager_id == user.id:
            raise HTTPException(status_code=400, detail="上级不能是自己")
        if body.manager_id and not db.get(User, body.manager_id):
            raise HTTPException(status_code=400, detail="上级不存在")
        user.manager_id = body.manager_id or None
    if body.enabled is not None:
        if user.id == current.id and body.enabled is False:
            raise HTTPException(status_code=400, detail="不能禁用自己")
        user.enabled = body.enabled
    if body.password:
        errors = validate_password_policy(body.password)
        if errors:
            raise HTTPException(status_code=400, detail="；".join(errors))
        user.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(user)
    rows = db.query(User).all()
    return _to_out(user, {u.id: u for u in rows})
