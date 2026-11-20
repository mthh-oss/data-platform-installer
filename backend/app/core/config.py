from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Data Platform Installer"
    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000

    # project root = data-platform-installer/
    project_root: Path = Path(__file__).resolve().parents[3]
    backend_root: Path = Path(__file__).resolve().parents[2]
    plugins_dir: Path = backend_root / "plugins"
    templates_dir: Path = project_root / "templates"
    workspaces_dir: Path = project_root / "workspaces"
    db_url: str = f"sqlite:///{(backend_root / 'data' / 'installer.db').as_posix()}"

    health_interval_seconds: int = 15
    docker_bin: str = "docker"
    jwt_secret: str = "dpi-change-me-in-production"
    jwt_expire_hours: int = 24
    ai_providers_dir: Path = backend_root / "ai_providers"

    class Config:
        env_prefix = "DPI_"


settings = Settings()
settings.workspaces_dir.mkdir(parents=True, exist_ok=True)
(settings.backend_root / "data").mkdir(parents=True, exist_ok=True)
