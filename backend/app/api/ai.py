from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.ai_registry import ai_registry
from app.core.compose_engine import compose_engine
from app.core.monitor import health_monitor
from app.core.registry import registry
from app.core.security import get_current_user
from app.db.models import AppSetting, Cluster, DeployJob, User
from app.db.session import get_db

router = APIRouter(prefix="/ai", tags=["ai"])


def _get_setting(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row else default


def _set_setting(db: Session, key: str, value: str) -> None:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = value
    else:
        row = AppSetting(key=key, value=value)
        db.add(row)
    db.commit()


class AIProviderOut(BaseModel):
    id: str
    name: str


class AISettingsOut(BaseModel):
    provider: str
    has_api_key: bool
    providers: list[AIProviderOut]


class AISettingsIn(BaseModel):
    provider: str = "deepseek"
    api_key: str = ""


class DiagnoseIn(BaseModel):
    cluster_id: int | None = None
    question: str = Field(default="请根据当前集群健康与异常日志做自检，给出可能原因与处理建议")


class DiagnoseOut(BaseModel):
    provider: str
    answer: str
    context_summary: str


class ChatIn(BaseModel):
    message: str = Field(min_length=1)
    cluster_id: int | None = None
    with_context: bool = False


class ChatOut(BaseModel):
    provider: str
    answer: str



@router.get("/providers", response_model=list[AIProviderOut])
def list_providers(_: User = Depends(get_current_user)) -> list[AIProviderOut]:
    return [AIProviderOut(id=p.id, name=p.name) for p in ai_registry.list()]


@router.get("/settings", response_model=AISettingsOut)
def get_settings(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> AISettingsOut:
    provider = _get_setting(db, "ai.provider", "deepseek")
    api_key = _get_setting(db, "ai.api_key", "")
    return AISettingsOut(
        provider=provider,
        has_api_key=bool(api_key.strip()),
        providers=[AIProviderOut(id=p.id, name=p.name) for p in ai_registry.list()],
    )


@router.put("/settings", response_model=AISettingsOut)
def put_settings(
    body: AISettingsIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AISettingsOut:
    try:
        ai_registry.get(body.provider)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _set_setting(db, "ai.provider", body.provider)
    if body.api_key.strip():
        _set_setting(db, "ai.api_key", body.api_key.strip())
    provider = _get_setting(db, "ai.provider", "deepseek")
    api_key = _get_setting(db, "ai.api_key", "")
    return AISettingsOut(
        provider=provider,
        has_api_key=bool(api_key.strip()),
        providers=[AIProviderOut(id=p.id, name=p.name) for p in ai_registry.list()],
    )



def _build_context(db: Session, cluster_id: int | None) -> tuple[str, str]:
    """Return (summary, detail_text)."""
    q = db.query(Cluster).order_by(Cluster.id.desc())
    cluster = db.get(Cluster, cluster_id) if cluster_id else q.first()
    if not cluster:
        return "无集群", "当前没有集群数据。"

    platforms = json.loads(cluster.platforms_json or "[]")
    configs = json.loads(cluster.config_json or "{}")
    docker_ps = ""
    if cluster.compose_file:
        ps = compose_engine.compose_ps(
            cluster.project_name, Path(cluster.compose_file), Path(cluster.work_dir)
        )
        docker_ps = (ps.stdout or "") + "\n" + (ps.stderr or "")

    health_parts: list[str] = []
    for pid in platforms:
        plugin = registry.get(pid)
        cfg = {**plugin.default_config(), **(configs.get(pid) or {})}
        checks = plugin.health_checks(cfg, cluster.project_name)
        result = health_monitor.check_platform(checks, docker_ps=docker_ps)
        health_parts.append(f"- {pid}: {result['status']} checks={result['checks']}")

    jobs = (
        db.query(DeployJob)
        .filter(DeployJob.cluster_id == cluster.id)
        .order_by(DeployJob.id.desc())
        .limit(3)
        .all()
    )
    job_parts: list[str] = []
    for job in jobs:
        tail = (job.log_text or "")[-4000:]
        job_parts.append(
            f"### job#{job.id} status={job.status} phase={job.phase} error={job.error}\n{tail}"
        )

    summary = f"cluster={cluster.name} status={cluster.status} platforms={platforms}"
    detail = (
        f"# Cluster\n{summary}\n\n# Health\n"
        + "\n".join(health_parts)
        + "\n\n# Recent Jobs\n"
        + "\n\n".join(job_parts)
    )
    return summary, detail


@router.post("/diagnose", response_model=DiagnoseOut)
def diagnose(
    body: DiagnoseIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DiagnoseOut:
    provider_id = _get_setting(db, "ai.provider", "deepseek")
    api_key = _get_setting(db, "ai.api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="请先在 AI 设置中配置 API Key")
    try:
        provider = ai_registry.get(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    summary, detail = _build_context(db, body.cluster_id)
    messages = [
        {
            "role": "system",
            "content": (
                "你是数据平台运维助手。根据用户提供的集群健康与部署日志做自检，"
                "输出：1) 问题判断 2) 可能原因 3) 可执行处理步骤。用中文，简洁。"
            ),
        },
        {
            "role": "user",
            "content": f"{body.question}\n\n----- 上下文 -----\n{detail[:12000]}",
        },
    ]
    try:
        answer = provider.chat(messages, api_key=api_key)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI 调用失败: {exc}") from exc
    return DiagnoseOut(provider=provider_id, answer=answer, context_summary=summary)


@router.post("/chat", response_model=ChatOut)
def chat(
    body: ChatIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ChatOut:
    provider_id = _get_setting(db, "ai.provider", "deepseek")
    api_key = _get_setting(db, "ai.api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="请先在「设置」中配置 AI API Key")
    try:
        provider = ai_registry.get(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    messages = [
        {
            "role": "system",
            "content": "你是数据平台运维助手，帮助排查 Doris/Flink/MySQL/调度等问题。用中文简洁回答。",
        }
    ]
    user_content = body.message
    if body.with_context:
        _, detail = _build_context(db, body.cluster_id)
        user_content = f"{body.message}\n\n----- 集群上下文 -----\n{detail[:10000]}"
    messages.append({"role": "user", "content": user_content})
    try:
        answer = provider.chat(messages, api_key=api_key)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI 调用失败: {exc}") from exc
    return ChatOut(provider=provider_id, answer=answer)

