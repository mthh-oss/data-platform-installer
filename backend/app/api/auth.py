from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    validate_password_policy,
    verify_password,
)
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class SetupBody(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=64)


class LoginBody(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class AuthStatusOut(BaseModel):
    initialized: bool
    username: str | None = None


@router.get("/status", response_model=AuthStatusOut)
def auth_status(db: Session = Depends(get_db)) -> AuthStatusOut:
    user = db.query(User).order_by(User.id.asc()).first()
    return AuthStatusOut(initialized=user is not None, username=user.username if user else None)


@router.post("/setup", response_model=TokenOut)
def setup_admin(body: SetupBody, db: Session = Depends(get_db)) -> TokenOut:
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="主账号已初始化，请直接登录")
    errors = validate_password_policy(body.password)
    if errors:
        raise HTTPException(status_code=400, detail="；".join(errors))
    if body.username.isdigit():
        raise HTTPException(status_code=400, detail="用户名不能全是数字")
    user = User(
        username=body.username.strip(),
        password_hash=hash_password(body.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    token = create_access_token(user.username)
    return TokenOut(access_token=token, username=user.username)


@router.post("/login", response_model=TokenOut)
def login(body: LoginBody, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.username)
    return TokenOut(access_token=token, username=user.username)


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {"username": user.username, "role": user.role}
