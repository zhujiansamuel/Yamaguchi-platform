"""Task API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Task, TaskStatus
from app.task.engine import task_engine

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    name: str
    script_name: str
    script_args: dict | None = None
    target_devices: list[str] | str = "all"


@router.post("")
async def create_task(body: TaskCreate):
    """Submit a new task."""
    task_ids = await task_engine.submit_task(
        name=body.name,
        script_name=body.script_name,
        script_args=body.script_args,
        target_devices=body.target_devices,
    )
    return {"task_ids": task_ids, "count": len(task_ids)}


@router.get("")
async def list_tasks(
    status: TaskStatus | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List tasks, optionally filtered by status."""
    query = select(Task).order_by(Task.created_at.desc()).limit(limit)
    if status:
        query = query.where(Task.status == status)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "script_name": t.script_name,
            "status": t.status.value,
            "device_udid": t.device_udid,
            "result": t.result,
            "error": t.error,
            "created_at": t.created_at.isoformat(),
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]


@router.get("/{task_id}")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "name": task.name,
        "script_name": task.script_name,
        "script_args": task.script_args,
        "status": task.status.value,
        "device_udid": task.device_udid,
        "target_devices": task.target_devices,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
