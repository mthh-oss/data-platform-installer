from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PluginInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    id: str
    name: str
    version: str
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)
    config_schema: dict[str, Any] = Field(alias="schema")
    default_config: dict[str, Any]




class ClusterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    platforms: list[str] = Field(min_length=1)
    configs: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ClusterOut(BaseModel):
    id: int
    name: str
    project_name: str
    status: str
    platforms: list[str]
    configs: dict[str, Any]
    work_dir: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    id: int
    cluster_id: int
    action: str
    status: str
    log_text: str = ""
    error: str = ""
    created_at: datetime | None = None
    finished_at: datetime | None = None

    class Config:
        from_attributes = True


class HealthOut(BaseModel):
    cluster_id: int
    cluster_status: str
    platforms: dict[str, Any]
    checked_at: str
