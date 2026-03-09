"""DNS and IPv6 configuration module for Windows.

Uses netsh commands to manage network adapter settings.
"""

import subprocess
import re


DNS_SERVER = "192.168.0.200"


def run_cmd(cmd: str) -> tuple[int, str]:
    """Run a Windows shell command and return (returncode, output)."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def get_active_adapters() -> list[str]:
    """Return a list of active (connected) network adapter names."""
    code, output = run_cmd("netsh interface show interface")
    adapters = []
    for line in output.splitlines():
        # Match lines with "Connected" status (English or Japanese locale)
        if re.search(r"\bConnected\b|接続済み|已连接", line):
            # Adapter name is the last column after multiple spaces
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 4:
                adapters.append(parts[-1])
    return adapters


def get_dns_for_adapter(adapter: str) -> str:
    """Get the current DNS server(s) for a specific adapter."""
    code, output = run_cmd(f'netsh interface ip show dns name="{adapter}"')
    dns_servers = []
    for line in output.splitlines():
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
        if match:
            dns_servers.append(match.group(1))
    if dns_servers:
        return ", ".join(dns_servers)
    if re.search(r"DHCP|dhcp|自動|自动|動的", output):
        return "DHCP (自動取得)"
    return "不明"


def get_ipv6_status(adapter: str) -> bool:
    """Check if IPv6 is enabled on a specific adapter. Returns True if enabled."""
    code, output = run_cmd(
        f'netsh interface ipv6 show interface interface="{adapter}"'
    )
    # If the command succeeds and returns interface info, IPv6 is likely enabled
    if code == 0 and re.search(r"Connected|接続済み|已连接", output):
        return True
    # Alternative check via registry / binding
    code2, output2 = run_cmd(
        'powershell -Command "'
        f"Get-NetAdapterBinding -Name '{adapter}' -ComponentID ms_tcpip6 "
        '| Select-Object -ExpandProperty Enabled"'
    )
    if "True" in output2:
        return True
    if "False" in output2:
        return False
    return True  # Default assume enabled


def set_dns(adapter: str) -> tuple[bool, str]:
    """Set DNS for the given adapter to the internal DNS server."""
    code, output = run_cmd(
        f'netsh interface ip set dns name="{adapter}" static {DNS_SERVER} primary'
    )
    if code == 0:
        return True, f"[{adapter}] DNS を {DNS_SERVER} に設定しました"
    return False, f"[{adapter}] DNS 設定失敗: {output}"


def restore_dns(adapter: str) -> tuple[bool, str]:
    """Restore DNS to DHCP (automatic) for the given adapter."""
    code, output = run_cmd(
        f'netsh interface ip set dns name="{adapter}" dhcp'
    )
    if code == 0:
        return True, f"[{adapter}] DNS を DHCP (自動取得) に戻しました"
    return False, f"[{adapter}] DNS 復元失敗: {output}"


def disable_ipv6(adapter: str) -> tuple[bool, str]:
    """Disable IPv6 on the given adapter."""
    code, output = run_cmd(
        'powershell -Command "'
        f"Disable-NetAdapterBinding -Name '{adapter}' -ComponentID ms_tcpip6"
        '"'
    )
    if code == 0:
        return True, f"[{adapter}] IPv6 を無効にしました"
    return False, f"[{adapter}] IPv6 無効化失敗: {output}"


def enable_ipv6(adapter: str) -> tuple[bool, str]:
    """Enable IPv6 on the given adapter."""
    code, output = run_cmd(
        'powershell -Command "'
        f"Enable-NetAdapterBinding -Name '{adapter}' -ComponentID ms_tcpip6"
        '"'
    )
    if code == 0:
        return True, f"[{adapter}] IPv6 を有効にしました"
    return False, f"[{adapter}] IPv6 有効化失敗: {output}"


def apply_all() -> list[str]:
    """Apply DNS + disable IPv6 on all active adapters."""
    logs = []
    adapters = get_active_adapters()
    if not adapters:
        logs.append("アクティブなネットワークアダプタが見つかりません")
        return logs
    for adapter in adapters:
        ok, msg = set_dns(adapter)
        logs.append(msg)
        ok, msg = disable_ipv6(adapter)
        logs.append(msg)
    return logs


def restore_all() -> list[str]:
    """Restore DNS to DHCP + enable IPv6 on all active adapters."""
    logs = []
    adapters = get_active_adapters()
    if not adapters:
        logs.append("アクティブなネットワークアダプタが見つかりません")
        return logs
    for adapter in adapters:
        ok, msg = restore_dns(adapter)
        logs.append(msg)
        ok, msg = enable_ipv6(adapter)
        logs.append(msg)
    return logs
