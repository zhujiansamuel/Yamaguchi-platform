"""Task Runner - executes user scripts with device context."""

import importlib.util
import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.device import connection as device_ops
from app.models import Task

logger = logging.getLogger(__name__)


class DeviceContext:
    """Provides device operations to user scripts."""

    def __init__(self, udid: str):
        self.udid = udid

    async def install_app(self, ipa_path: str) -> str:
        return await device_ops.install_app(self.udid, ipa_path)

    async def uninstall_app(self, bundle_id: str) -> str:
        return await device_ops.uninstall_app(self.udid, bundle_id)

    async def list_apps(self) -> list[dict]:
        return await device_ops.list_apps(self.udid)

    async def screenshot(self) -> bytes:
        return await device_ops.take_screenshot(self.udid)


async def execute_task(task_id: int, udid: str) -> str:
    """Load and execute a user script for a given task and device."""
    async with async_session() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one()
        script_name = task.script_name
        script_args = json.loads(task.script_args) if task.script_args else {}

    script_path = settings.scripts_dir / f"{script_name}.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    # Load the script module
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Scripts must define an async `run(ctx: DeviceContext, args: dict) -> str` function
    if not hasattr(module, "run"):
        raise AttributeError(f"Script {script_name} must define an async 'run' function")

    ctx = DeviceContext(udid)
    result = await module.run(ctx, script_args)
    return str(result) if result else "OK"
