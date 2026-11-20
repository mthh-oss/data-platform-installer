from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.rbac import ROLE_ADMIN, require_roles
from app.core.security import hash_password, validate_password_policy
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    display_name: str = ""
    enabled: bool = True

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=64)
    role: str = "operator"
    display_name: str = ""


class UserUpdate(BaseModel):
    role: str | None = None
    display_name: str | None = None
    enabled: bool | None = None
    password: str | None = None


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN)),
) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in db.query(User).order_by(User.id.asc()).all()]


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
    user = User(
        username=body.username.strip(),
        password_hash=hash_password(body.password),
        role=body.role,
        display_name=body.display_name or body.username,
        enabled=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
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
    return UserOut.model_validate(user)
