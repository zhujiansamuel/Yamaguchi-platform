"""Task Engine - queue management and auto-assignment to available devices."""

import asyncio
import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.device.manager import device_manager
from app.models import Task, TaskStatus
from app.task.runner import execute_task

logger = logging.getLogger(__name__)


class TaskEngine:
    """Manages task queue, assigns tasks to available devices, runs them."""

    def __init__(self):
        self._running = False
        self._scheduler_task: asyncio.Task | None = None
        self._active_tasks: dict[str, asyncio.Task] = {}  # udid -> asyncio.Task

    async def start(self):
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Task engine started")

    async def stop(self):
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        # Cancel active tasks
        for task in self._active_tasks.values():
            task.cancel()
        logger.info("Task engine stopped")

    async def submit_task(
        self,
        name: str,
        script_name: str,
        script_args: dict | None = None,
        target_devices: list[str] | str = "all",
    ) -> list[int]:
        """Submit a task. If target is 'all', creates one task per connected device.
        Returns list of task IDs."""
        async with async_session() as db:
            if target_devices == "all":
                from app.models import Device, DeviceStatus
                result = await db.execute(
                    select(Device).where(Device.status != DeviceStatus.DISCONNECTED)
                )
                udids = [d.udid for d in result.scalars().all()]
            else:
                udids = target_devices if isinstance(target_devices, list) else [target_devices]

            task_ids = []
            for udid in udids:
                task = Task(
                    name=name,
                    script_name=script_name,
                    script_args=json.dumps(script_args) if script_args else None,
                    status=TaskStatus.QUEUED,
                    target_devices=udid,
                )
                db.add(task)
                await db.flush()
                task_ids.append(task.id)

            await db.commit()
            logger.info(f"Submitted {len(task_ids)} tasks: {name}")
            return task_ids

    async def _scheduler_loop(self):
        """Main scheduler: assigns queued tasks to free devices."""
        while self._running:
            try:
                await self._assign_tasks()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(1.0)

    async def _assign_tasks(self):
        async with async_session() as db:
            # Find queued tasks
            result = await db.execute(
                select(Task)
                .where(Task.status == TaskStatus.QUEUED)
                .order_by(Task.created_at)
            )
            queued_tasks = result.scalars().all()

            for task in queued_tasks:
                target_udid = task.target_devices
                # Skip if device already has an active task
                if target_udid in self._active_tasks:
                    continue

                # Check device is available
                from app.models import Device, DeviceStatus
                dev_result = await db.execute(
                    select(Device).where(
                        Device.udid == target_udid,
                        Device.status == DeviceStatus.CONNECTED,
                    )
                )
                device = dev_result.scalar_one_or_none()
                if not device:
                    continue

                # Assign and run
                task.status = TaskStatus.RUNNING
                task.device_udid = target_udid
                task.started_at = datetime.utcnow()
                await db.commit()

                await device_manager.set_device_busy(target_udid)
                self._active_tasks[target_udid] = asyncio.create_task(
                    self._run_task(task.id, target_udid)
                )

    async def _run_task(self, task_id: int, udid: str):
        """Execute a task and update its status."""
        try:
            result = await execute_task(task_id, udid)
            async with async_session() as db:
                db_result = await db.execute(select(Task).where(Task.id == task_id))
                task = db_result.scalar_one()
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.utcnow()
                await db.commit()
        except asyncio.CancelledError:
            async with async_session() as db:
                db_result = await db.execute(select(Task).where(Task.id == task_id))
                task = db_result.scalar_one()
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            async with async_session() as db:
                db_result = await db.execute(select(Task).where(Task.id == task_id))
                task = db_result.scalar_one()
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.utcnow()
                await db.commit()
        finally:
            self._active_tasks.pop(udid, None)
            await device_manager.set_device_free(udid)


# Singleton
task_engine = TaskEngine()
