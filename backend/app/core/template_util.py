from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.core.config import settings


def render_template_dir(plugin_id: str, dest: Path, context: dict[str, Any]) -> Path:
    """Render all files under templates/<plugin_id> into dest using Jinja2."""
    src = settings.templates_dir / plugin_id
    if not src.exists():
        raise FileNotFoundError(f"template dir not found: {src}")

    env = Environment(
        loader=FileSystemLoader(str(src)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    dest.mkdir(parents=True, exist_ok=True)

    for path in src.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(src)
        # support *.j2 suffix
        out_name = rel.name[:-3] if rel.name.endswith(".j2") else rel.name
        out_path = dest / rel.parent / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".j2" or path.name.endswith(".yml.j2") or path.name.endswith(".yaml.j2"):
            template = env.get_template(str(rel).replace("\\", "/"))
            out_path.write_text(template.render(**context), encoding="utf-8")
        else:
            out_path.write_bytes(path.read_bytes())
    return dest
