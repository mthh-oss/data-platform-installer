from fastapi import APIRouter, Depends

from app.core.registry import registry
from app.core.security import get_current_user
from app.db.models import User
from app.schemas import PluginInfo

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("", response_model=list[PluginInfo])
def list_plugins(_: User = Depends(get_current_user)) -> list[PluginInfo]:
    items: list[PluginInfo] = []
    for p in registry.list():
        items.append(
            PluginInfo(
                id=p.id,
                name=p.name,
                version=p.version,
                description=p.description,
                dependencies=p.dependencies(),
                **{"schema": p.schema()},
                default_config=p.default_config(),
            )
        )
    return items
