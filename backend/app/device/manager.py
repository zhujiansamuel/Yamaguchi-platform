"""Device Manager - monitors connected devices and maintains device pool."""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.device.connection import DeviceInfo, list_connected_devices
from app.models import Device, DeviceStatus

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages the device pool, periodically polls USB for connected devices."""

    def __init__(self):
        self._running = False
        self._poll_task: asyncio.Task | None = None
        self._listeners: list[asyncio.Queue] = []

    async def start(self):
        """Start the device polling loop."""
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Device manager started")

    async def stop(self):
        """Stop the device polling loop."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        logger.info("Device manager stopped")

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to device status change events."""
        queue: asyncio.Queue = asyncio.Queue()
        self._listeners.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from device status change events."""
        self._listeners.remove(queue)

    async def _notify(self, event: dict):
        for queue in self._listeners:
            await queue.put(event)

    async def _poll_loop(self):
        """Periodically poll for connected USB devices."""
        while self._running:
            try:
                await self._sync_devices()
            except Exception as e:
                logger.error(f"Device poll error: {e}")
            await asyncio.sleep(settings.device_poll_interval)

    async def _sync_devices(self):
        """Sync connected devices with the database."""
        connected = await list_connected_devices()
        connected_udids = {d.udid for d in connected}

        async with async_session() as db:
            # Get all known devices
            result = await db.execute(select(Device))
            known_devices = {d.udid: d for d in result.scalars().all()}

            # Update or add connected devices
            for info in connected:
                if info.udid in known_devices:
                    device = known_devices[info.udid]
                    old_status = device.status
                    device.name = info.name
                    device.model = info.model
                    device.ios_version = info.ios_version
                    device.last_seen = datetime.utcnow()
                    if device.status == DeviceStatus.DISCONNECTED:
                        device.status = DeviceStatus.CONNECTED
                    if old_status != device.status:
                        await self._notify({
                            "type": "device_status",
                            "udid": device.udid,
                            "status": device.status.value,
                        })
                else:
                    device = Device(
                        udid=info.udid,
                        name=info.name,
                        model=info.model,
                        ios_version=info.ios_version,
                        status=DeviceStatus.CONNECTED,
                        last_seen=datetime.utcnow(),
                    )
                    db.add(device)
                    await self._notify({
                        "type": "device_connected",
                        "udid": info.udid,
                        "name": info.name,
                    })

            # Mark disconnected devices
            for udid, device in known_devices.items():
                if udid not in connected_udids and device.status != DeviceStatus.DISCONNECTED:
                    device.status = DeviceStatus.DISCONNECTED
                    await self._notify({
                        "type": "device_disconnected",
                        "udid": udid,
                    })

            await db.commit()

    async def get_available_device(self) -> str | None:
        """Get a UDID of an available (connected, not busy) device."""
        async with async_session() as db:
            result = await db.execute(
                select(Device).where(Device.status == DeviceStatus.CONNECTED)
            )
            device = result.scalars().first()
            return device.udid if device else None

    async def set_device_busy(self, udid: str):
        async with async_session() as db:
            result = await db.execute(select(Device).where(Device.udid == udid))
            device = result.scalar_one()
            device.status = DeviceStatus.BUSY
            await db.commit()
            await self._notify({"type": "device_status", "udid": udid, "status": "busy"})

    async def set_device_free(self, udid: str):
        async with async_session() as db:
            result = await db.execute(select(Device).where(Device.udid == udid))
            device = result.scalar_one()
            device.status = DeviceStatus.CONNECTED
            await db.commit()
            await self._notify({"type": "device_status", "udid": udid, "status": "connected"})


# Singleton
device_manager = DeviceManager()
