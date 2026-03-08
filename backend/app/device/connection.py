"""pymobiledevice3 wrapper for iOS device communication."""

import asyncio
import logging
from dataclasses import dataclass
from functools import partial

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.services.screenshot import ScreenshotService
from pymobiledevice3.usbmux import list_devices

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    udid: str
    name: str
    model: str
    ios_version: str


def _list_usb_devices() -> list[DeviceInfo]:
    """List all USB-connected iOS devices (sync, runs in thread)."""
    devices = []
    for mux_device in list_devices():
        try:
            lockdown = create_using_usbmux(serial=mux_device.serial)
            info = DeviceInfo(
                udid=lockdown.udid,
                name=lockdown.display_name,
                model=lockdown.product_type,
                ios_version=lockdown.product_version,
            )
            devices.append(info)
        except Exception as e:
            logger.warning(f"Failed to connect to device {mux_device.serial}: {e}")
    return devices


async def list_connected_devices() -> list[DeviceInfo]:
    """List all USB-connected iOS devices (async)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _list_usb_devices)


def _get_lockdown(udid: str):
    return create_using_usbmux(serial=udid)


async def install_app(udid: str, ipa_path: str) -> str:
    """Install an IPA file on a device."""
    loop = asyncio.get_event_loop()

    def _install():
        lockdown = _get_lockdown(udid)
        service = InstallationProxyService(lockdown=lockdown)
        service.install_from_local(ipa_path)
        return f"Installed {ipa_path} on {udid}"

    return await loop.run_in_executor(None, _install)


async def uninstall_app(udid: str, bundle_id: str) -> str:
    """Uninstall an app from a device."""
    loop = asyncio.get_event_loop()

    def _uninstall():
        lockdown = _get_lockdown(udid)
        service = InstallationProxyService(lockdown=lockdown)
        service.uninstall(bundle_id)
        return f"Uninstalled {bundle_id} from {udid}"

    return await loop.run_in_executor(None, _uninstall)


async def list_apps(udid: str) -> list[dict]:
    """List installed apps on a device."""
    loop = asyncio.get_event_loop()

    def _list():
        lockdown = _get_lockdown(udid)
        service = InstallationProxyService(lockdown=lockdown)
        return service.get_apps(app_types=["User"])

    return await loop.run_in_executor(None, _list)


async def take_screenshot(udid: str) -> bytes:
    """Take a screenshot of a device, returns PNG bytes."""
    loop = asyncio.get_event_loop()

    def _screenshot():
        lockdown = _get_lockdown(udid)
        service = ScreenshotService(lockdown=lockdown)
        return service.take_screenshot()

    return await loop.run_in_executor(None, _screenshot)
