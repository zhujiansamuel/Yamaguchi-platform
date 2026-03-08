"""Device API routes."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.device.connection import list_apps, take_screenshot
from app.models import Device

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
async def get_devices(db: AsyncSession = Depends(get_db)):
    """List all known devices."""
    result = await db.execute(select(Device))
    devices = result.scalars().all()
    return [
        {
            "udid": d.udid,
            "name": d.name,
            "model": d.model,
            "ios_version": d.ios_version,
            "status": d.status.value,
            "last_seen": d.last_seen.isoformat(),
        }
        for d in devices
    ]


@router.get("/{udid}")
async def get_device(udid: str, db: AsyncSession = Depends(get_db)):
    """Get a specific device."""
    result = await db.execute(select(Device).where(Device.udid == udid))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {
        "udid": device.udid,
        "name": device.name,
        "model": device.model,
        "ios_version": device.ios_version,
        "status": device.status.value,
        "last_seen": device.last_seen.isoformat(),
    }


@router.get("/{udid}/apps")
async def get_device_apps(udid: str):
    """List installed apps on a device."""
    try:
        apps = await list_apps(udid)
        return apps
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{udid}/screenshot")
async def get_device_screenshot(udid: str):
    """Take a screenshot of a device."""
    try:
        png_data = await take_screenshot(udid)
        return Response(content=png_data, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
