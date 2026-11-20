from fastapi import APIRouter

from app.core.registry import registry
from app.schemas import PluginInfo

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("", response_model=list[PluginInfo])
def list_plugins() -> list[PluginInfo]:
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
