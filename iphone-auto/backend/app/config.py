from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./device_farm.db"

    # Device polling interval (seconds)
    device_poll_interval: float = 3.0

    # Max concurrent tasks per device
    max_tasks_per_device: int = 1

    # Scripts directory
    scripts_dir: Path = Path("scripts")

    # Task result retention (days)
    task_retention_days: int = 30

    model_config = {"env_prefix": "FARM_"}


settings = Settings()
